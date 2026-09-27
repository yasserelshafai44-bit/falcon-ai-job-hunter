"""Authorised local dry run; never approves or submits the real application."""

import asyncio
import json
from io import BytesIO
from pathlib import Path

import httpx
from app.commands.verify_application_21_approval import fingerprint
from app.core.security import create_access_token
from app.database.session import AsyncSessionLocal
from app.models.application_workflow import ApplicationWorkflow
from app.models.generated_document import GeneratedDocument
from docx import Document


async def main():
    before = await fingerprint()
    async with AsyncSessionLocal() as session:
        workflow = await session.get(ApplicationWorkflow, 21)
        assert workflow and workflow.status == "approved" and not workflow.submitted_at
        resume = await session.get(GeneratedDocument, workflow.resume_document_id)
        headers = {
            "Authorization": f"Bearer {create_access_token(str(workflow.user_id))}"
        }
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000", headers=headers, timeout=30
    ) as client:
        profile_response = await client.get("/api/v1/application-assistant/profile")
        assert profile_response.status_code == 200, profile_response.text
        profile = profile_response.json()
        file = await client.get(
            "/api/v1/application-assistant/applications/21/resume.docx"
        )
        assert file.status_code == 200, file.text
        doc = Document(BytesIO(file.content))
        expected = [
            line.strip().removeprefix("- ").removeprefix("• ")
            for line in resume.content.splitlines()
            if line.strip()
        ]
        assert [p.text for p in doc.paragraphs] == expected
        Path("/tmp/Falcon-application-21-resume.docx").write_bytes(file.content)
        response = await client.post(
            "/api/v1/application-assistant/applications/21/prepare"
        )
        assert response.status_code == 200, response.text
        view = response.json()
        assert view["dry_run"] is True
        assert view["state"] == "blocked", (
            "A connected live route needs separate inspection"
        )
        session_url = f"/api/v1/application-assistant/sessions/{view['id']}"
        denied = await client.post(
            session_url + "/final-approve",
            json={
                "snapshot_digest": view["snapshot_digest"],
                "explicit_final_approval": True,
            },
        )
        assert denied.status_code == 409, denied.text
        denied = await client.post(
            session_url + "/submit-dry-run",
            json={"snapshot_digest": view["snapshot_digest"]},
        )
        assert denied.status_code == 409, denied.text
        for path in (
            "/api/v1/health",
            "/api/v1/ready",
            "/app",
            "/assets/application-assistant.js",
        ):
            assert (await client.get(path)).status_code == 200, path
    after = await fingerprint()
    new_tables = {"candidate_application_profiles", "application_assistant_sessions"}
    assert all(
        after[table] == rows
        for table, rows in before.items()
        if table not in new_tables
    )
    for table in new_tables:
        assert set(before[table]).issubset(set(after[table]))
    result = {
        "application": 21,
        "status": "BLOCKED",
        "profile": profile,
        "assistant": view,
        "tailored_cv_downloadable": True,
        "cv_text_preserved": True,
        "docx_visual_qa": "pending",
        "final_gate_rejects_unresolved": True,
        "all_existing_data_preserved": True,
        "external_submission_performed": False,
    }
    Path("/tmp/application-21-automation.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in {"profile", "assistant"}}
        )
    )
    print(
        json.dumps(
            {
                "work_records": len(profile["work_history"]),
                "education_records": len(profile["education"]),
                "blocker": view["blocker"],
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
