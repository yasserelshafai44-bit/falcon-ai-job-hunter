import hashlib
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.application_assistant import (
    ApplicationAssistantSession,
)
from app.models.application_workflow import ApplicationWorkflow
from app.models.discovered_job import DiscoveredJob
from app.models.generated_document import GeneratedDocument
from app.services.application_profile import get_application_profile


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


async def inputs(session, user_id, workflow_id):
    workflow = await session.scalar(
        select(ApplicationWorkflow)
        .where(
            ApplicationWorkflow.id == workflow_id,
            ApplicationWorkflow.user_id == user_id,
        )
        .with_for_update()
    )
    if not workflow:
        raise ValueError("Application not found")
    if workflow.status != "approved" or not workflow.reviewed_at:
        raise ValueError("Approve the current application materials first")
    job = await session.get(DiscoveredJob, workflow.job_id)
    resume = await session.get(GeneratedDocument, workflow.resume_document_id)
    cover = await session.get(GeneratedDocument, workflow.cover_letter_document_id)
    if (
        not job
        or not resume
        or not cover
        or any(
            d.user_id != user_id or d.job_id != workflow.job_id for d in (resume, cover)
        )
    ):
        raise ValueError("Approved application materials are missing or do not match")
    profile = await get_application_profile(session, user_id)
    identity = digest(
        {
            "profile": profile,
            "resume": resume.content,
            "resume_id": resume.id,
            "cover": cover.content,
            "cover_id": cover.id,
            "job": job.id,
            "url": job.url,
            "status": workflow.status,
            "reviewed": workflow.reviewed_at,
            "approval": workflow.approval_notes,
        }
    )
    return workflow, job, resume, cover, profile, identity


async def prepare_assistant(session, user_id, workflow_id, *, local_browser=False):
    from app.services.assisted_apply import assisted_pack

    return await assisted_pack(session, user_id, workflow_id, continue_application=True)


async def refresh_local(session, user_id, session_id):
    from app.services.assisted_apply import assisted_pack

    record = await get_session(session, user_id, session_id)
    return await assisted_pack(session, user_id, record.workflow_id)


def public_session(record):
    snapshot = {
        key: value for key, value in record.snapshot.items() if key != "payload"
    }
    return {
        "id": record.id,
        "workflow_id": record.workflow_id,
        "state": record.state,
        "snapshot_digest": record.snapshot_digest,
        "final_approved_at": record.final_approved_at,
        **snapshot,
    }


async def get_session(session, user_id, session_id):
    record = await session.scalar(
        select(ApplicationAssistantSession)
        .where(
            ApplicationAssistantSession.id == session_id,
            ApplicationAssistantSession.user_id == user_id,
        )
        .with_for_update()
    )
    if not record:
        raise ValueError("Application assistant session not found")
    return record


async def final_approve(session, user_id, session_id, expected_digest, explicit):
    record = await get_session(session, user_id, session_id)
    if not explicit:
        raise ValueError("Explicit final submission approval is required")
    if record.state != "review_required" or record.snapshot.get("unresolved"):
        raise ValueError(
            "Resolve all questions and connection blockers before final approval"
        )
    if record.snapshot["configuration"].get("status") != "retrieved":
        raise ValueError("Employer application configuration has not been checked")
    *_, identity = await inputs(session, user_id, record.workflow_id)
    if (
        identity != record.input_digest
        or expected_digest != record.snapshot_digest
        or digest(record.snapshot) != expected_digest
    ):
        raise ValueError("Application changed; prepare and review it again")
    record.final_approved_at = datetime.now(UTC)
    record.state = "final_approved_dry_run"
    await session.commit()
    return public_session(record)


async def dry_run_submit(session, user_id, session_id, expected_digest):
    record = await get_session(session, user_id, session_id)
    if record.state != "final_approved_dry_run" or not record.final_approved_at:
        raise ValueError(
            "Final submission approval is required immediately before submission"
        )
    approved = record.final_approved_at.replace(tzinfo=UTC)
    if datetime.now(UTC) - approved > timedelta(minutes=5):
        raise ValueError("Final approval expired; prepare and review again")
    *_, identity = await inputs(session, user_id, record.workflow_id)
    if (
        identity != record.input_digest
        or expected_digest != record.snapshot_digest
        or digest(record.snapshot) != expected_digest
    ):
        raise ValueError("Application changed; final approval is invalid")
    # Hard development protection: there is no external POST/submit call here.
    # A caller cannot switch this session to live mode or submit #21.
    record.state = "dry_run_complete"
    await session.commit()
    return {
        **public_session(record),
        "external_submission_performed": False,
        "message": "Dry run complete. No employer submission request was sent.",
    }
