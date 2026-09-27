"""Privileged local repair for application 21; never reviews, approves or submits it.

Run by falcon_finish_beta.ps1 inside the existing API container. The short-lived
owner token stays in this process and is used only for the authorised repair and
read-only API verification. Passwords and browser sessions are not changed.
"""

import argparse
import asyncio
import json
from hashlib import sha256
from pathlib import Path

import httpx
from app.core.security import create_access_token
from app.database.session import AsyncSessionLocal
from app.models.application_workflow import ApplicationWorkflow
from app.models.candidate_analysis import CandidateAnalysis
from app.models.discovered_job import DiscoveredJob
from app.models.generated_document import GeneratedDocument
from app.models.job_match import JobMatch
from app.services.candidate_context import enrich_analysis_with_profile
from app.services.grounded_materials import render_material
from app.services.prompt_builder import PROMPT_VERSION
from sqlalchemy import MetaData, select

PLACEHOLDERS = (
    "evidence-based operations leader tailored to the target role",
    "verified achievement included from candidate evidence",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def snapshot() -> dict:
    """Fingerprint every existing database row without exporting private contents."""
    async with AsyncSessionLocal() as session:
        connection = await session.connection()
        metadata = MetaData()
        await connection.run_sync(metadata.reflect)
        result = {}
        for table in metadata.sorted_tables:
            rows = (await session.execute(select(table))).mappings().all()
            entries = {}
            for row in rows:
                data = dict(row)
                identity = [data[column.name] for column in table.primary_key]
                if not identity:
                    identity = data
                key = json.dumps(identity, default=str, sort_keys=True)
                # Only the explicitly authorised workflow pointer/state changes
                # are excluded; the application identity and match remain checked.
                if table.name == "application_workflows" and data.get("id") == 21:
                    for field in (
                        "resume_document_id",
                        "cover_letter_document_id",
                        "status",
                        "reviewed_at",
                        "approval_notes",
                        "updated_at",
                    ):
                        data.pop(field, None)
                entries[key] = sha256(
                    json.dumps(data, default=str, sort_keys=True).encode()
                ).hexdigest()
            result[table.name] = entries
        return result


def verify_preserved(before: dict, after: dict) -> None:
    for table, rows in before.items():
        for key, digest in rows.items():
            require(
                after.get(table, {}).get(key) == digest,
                f"Preservation check failed for an existing row in {table}; "
                "no reset was attempted",
            )


async def finish(report_path: Path) -> None:
    async with AsyncSessionLocal() as session:
        workflow = await session.get(ApplicationWorkflow, 21)
        require(workflow is not None, "Application #21 was not found")
        job = await session.get(DiscoveredJob, workflow.job_id)
        match = await session.get(JobMatch, workflow.job_match_id)
        require(
            job is not None and match is not None,
            "Application #21 has incomplete vacancy/match data",
        )
        require(
            not job.is_demo
            and job.provider == "raising_canes_uk"
            and "area leader" in job.title.casefold()
            and "raising cane" in job.company.casefold()
            and "london" in job.location.casefold(),
            "Application #21 is not the expected Raising Cane's London vacancy; "
            "left unchanged",
        )
        require(match.user_id == workflow.user_id, "Owner/match mismatch")
        require(match.job_id == workflow.job_id, "Vacancy/match mismatch")
        analysis = await session.get(CandidateAnalysis, match.candidate_analysis_id)
        require(
            analysis is not None and analysis.user_id == workflow.user_id,
            "Owner/CV mismatch",
        )
        candidate = await enrich_analysis_with_profile(
            session, workflow.user_id, analysis.analysis_data
        )
        candidate["source_text"] = analysis.extracted_text
        require(
            bool(analysis.extracted_text.strip()), "The saved CV has no extracted text"
        )
        owner_id = workflow.user_id
        original_status = workflow.status
        originals = [
            await session.get(GeneratedDocument, document_id) if document_id else None
            for document_id in (
                workflow.resume_document_id,
                workflow.cover_letter_document_id,
            )
        ]
        repair = any(
            document is None
            or any(phrase in document.content.casefold() for phrase in PLACEHOLDERS)
            or (
                not document.metadata_json.get("user_revised")
                and (
                    document.provider != "evidence_grounded"
                    or document.prompt_version != PROMPT_VERSION
                )
            )
            for document in originals
        )
        job_data = {
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "requirements": job.requirements or [],
        }
        original_match = (match.id, match.overall_score, match.recommendation)

    before = await snapshot()
    # Administrative maintenance uses the real owner-scoped endpoints, never an
    # authentication override or a new/reset owner account.
    token = create_access_token(str(owner_id))
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000/api/v1",
        timeout=120,
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        me = await client.get("/auth/me")
        me.raise_for_status()
        require(me.json()["id"] == owner_id, "Owner authentication mismatch")
        if repair:
            require(
                original_status
                in {"draft", "materials_ready", "awaiting_approval", "approved"},
                "Application #21 is already submitted/closed; repair refused",
            )
            response = await client.post(
                "/application-workflows/21/regenerate-materials"
            )
            response.raise_for_status()
            require(
                response.json()["status"] == "materials_ready",
                "Regenerated drafts must require review",
            )
            require(
                response.json()["reviewed_at"] is None, "Prior review was not cleared"
            )
        response = await client.get("/application-workflows/21/review")
        response.raise_for_status()
        review = response.json()
        if not repair:
            require(
                review["workflow"]["status"] == original_status,
                "Existing review or approval state changed",
            )
        require(
            review["workflow"]["user_id"] == owner_id, "Review belongs to another owner"
        )
        require(
            review["workflow"]["submitted_at"] is None,
            "Application #21 has a submission timestamp",
        )
        require(
            (
                review["match"]["id"],
                review["match"]["overall_score"],
                review["match"]["recommendation"],
            )
            == original_match,
            "Application match or scoring changed",
        )
        for name, kind in (("resume", "resume"), ("cover_letter", "cover_letter")):
            document = review[name]
            content = document["content"]
            require(
                not any(phrase in content.casefold() for phrase in PLACEHOLDERS),
                "Placeholder content remains",
            )
            require(
                job_data["title"] in content and job_data["company"] in content,
                "Material is not addressed to the actual employer/role",
            )
            if not document["metadata"].get("user_revised"):
                expected = render_material(
                    {
                        "document_type": kind,
                        "candidate": candidate,
                        "job": job_data,
                        "max_words": document["metadata"]["max_words"],
                    }
                )
                require(
                    content == expected,
                    "Stored material differs from verified source-grounded output",
                )
                if kind == "resume":
                    claims = [
                        line[2:].strip()
                        for line in content.splitlines()
                        if line.startswith("- ")
                    ]
                    require(
                        5 <= len(claims) <= 8,
                        "Application #21 needs five to eight complete highlights",
                    )
        require(
            review["resume"]["content"] != review["cover_letter"]["content"],
            "Both materials are identical",
        )

    verify_preserved(before, await snapshot())
    report = {
        "status": "PASS",
        "application_id": 21,
        "repaired": repair,
        "application_state": review["workflow"]["status"],
        "data_preserved": True,
        "external_application_submitted": False,
        "employer": review["job"]["company"],
        "role": review["job"]["title"],
        "score": review["match"]["overall_score"],
        "resume": review["resume"]["content"],
        "cover_letter": review["cover_letter"]["content"],
        "table_counts_before": {name: len(rows) for name, rows in before.items()},
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("PASS: application #21 materials verified; previous data preserved.")
    print(f"PASS: owner API review; state={review['workflow']['status']}.")
    print("PASS: external submission=NO.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(finish(args.report))


if __name__ == "__main__":
    main()
