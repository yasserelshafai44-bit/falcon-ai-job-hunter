"""Replay #21 approval inside a rolled-back transaction; never submit externally."""

import asyncio
import json
from hashlib import sha256
from pathlib import Path

import httpx
from app.api.dependencies import get_current_user
from app.core.security import create_access_token
from app.database.session import AsyncSessionLocal, engine, get_db_session
from app.main import app
from app.models.application_workflow import ApplicationWorkflow
from app.models.user import User
from sqlalchemy import MetaData, select
from sqlalchemy.ext.asyncio import AsyncSession


async def fingerprint():
    async with engine.connect() as connection:
        metadata = MetaData()
        await connection.run_sync(metadata.reflect)
        result = {}
        for table in metadata.sorted_tables:
            rows = (await connection.execute(select(table))).mappings().all()
            result[table.name] = sorted(
                sha256(
                    json.dumps(dict(row), default=str, sort_keys=True).encode()
                ).hexdigest()
                for row in rows
            )
        return result


async def main():
    before = await fingerprint()
    async with AsyncSessionLocal() as session:
        workflow = await session.get(ApplicationWorkflow, 21)
        assert workflow and workflow.status == "approved" and not workflow.submitted_at
        owner = await session.get(User, workflow.user_id)
        saved = {c.name: getattr(workflow, c.name) for c in workflow.__table__.columns}
    reviews = {}
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as session:
                record = await session.get(ApplicationWorkflow, 21)
                record.status = "materials_ready"
                record.approval_notes = None
                await session.commit()

                async def db():
                    yield session

                app.dependency_overrides[get_db_session] = db
                app.dependency_overrides[get_current_user] = lambda: owner
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    for action, expected in (
                        ("request-approval", "awaiting_approval"),
                        ("approve", "approved"),
                    ):
                        response = await client.post(
                            f"/api/v1/application-workflows/21/{action}",
                            json={"notes": "ROLLBACK-ONLY approval workflow test"},
                        )
                        assert response.status_code == 200, response.text
                        assert response.json()["status"] == expected
                        review = await client.get(
                            "/api/v1/application-workflows/21/review"
                        )
                        assert review.status_code == 200, review.text
                        reviews[expected] = review.json()
                        assert (
                            review.json()["employer_questions_status"]
                            == "requires_employer_site"
                        )
                        assert review.json()["unanswered_employer_questions"] == []
                        assert review.json()["workflow"]["submitted_at"] is None
        finally:
            app.dependency_overrides.clear()
            await transaction.rollback()
    assert before == await fingerprint(), (
        "Database rows changed during rolled-back test"
    )
    async with AsyncSessionLocal() as session:
        workflow = await session.get(ApplicationWorkflow, 21)
        assert saved == {
            c.name: getattr(workflow, c.name) for c in workflow.__table__.columns
        }
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        for path in ("/api/v1/health", "/api/v1/ready", "/app"):
            response = await client.get(path)
            assert response.status_code == 200, (path, response.status_code)
        response = await client.get(
            "/api/v1/application-workflows/21/review",
            headers={"Authorization": f"Bearer {create_access_token(str(owner.id))}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["employer_questions_status"] == "requires_employer_site"
        assert response.json()["workflow"]["status"] == "approved"
    Path("/tmp/application-21-approval-review.json").write_text(json.dumps(reviews))
    print(
        json.dumps(
            {
                "application": 21,
                "test_status": "approved",
                "saved_status": workflow.status,
                "resume_id": workflow.resume_document_id,
                "cover_letter_id": workflow.cover_letter_document_id,
                "all_database_rows_unchanged": True,
                "external_submission": False,
                "api_frontend_health": "PASS",
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
