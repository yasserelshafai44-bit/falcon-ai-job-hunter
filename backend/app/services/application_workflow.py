from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_workflow import ApplicationWorkflow
from app.models.generated_document import GeneratedDocument
from app.models.job_match import JobMatch
from app.schemas.application_workflow import (
    ApplicationWorkflowRead,
    ApplicationWorkflowStatus,
)


class ApplicationWorkflowError(ValueError):
    """Raised when an application workflow action is invalid."""


_ALLOWED_TRANSITIONS: dict[ApplicationWorkflowStatus, set[ApplicationWorkflowStatus]] = {
    ApplicationWorkflowStatus.DRAFT: {
        ApplicationWorkflowStatus.MATERIALS_READY,
        ApplicationWorkflowStatus.WITHDRAWN,
    },
    ApplicationWorkflowStatus.MATERIALS_READY: {
        ApplicationWorkflowStatus.AWAITING_APPROVAL,
        ApplicationWorkflowStatus.WITHDRAWN,
    },
    ApplicationWorkflowStatus.AWAITING_APPROVAL: {
        ApplicationWorkflowStatus.APPROVED,
        ApplicationWorkflowStatus.WITHDRAWN,
    },
    ApplicationWorkflowStatus.APPROVED: {
        ApplicationWorkflowStatus.SUBMITTED,
        ApplicationWorkflowStatus.WITHDRAWN,
    },
    ApplicationWorkflowStatus.SUBMITTED: {
        ApplicationWorkflowStatus.REJECTED,
        ApplicationWorkflowStatus.INTERVIEW,
        ApplicationWorkflowStatus.OFFER,
        ApplicationWorkflowStatus.WITHDRAWN,
    },
    ApplicationWorkflowStatus.INTERVIEW: {
        ApplicationWorkflowStatus.REJECTED,
        ApplicationWorkflowStatus.OFFER,
        ApplicationWorkflowStatus.WITHDRAWN,
    },
    ApplicationWorkflowStatus.REJECTED: set(),
    ApplicationWorkflowStatus.OFFER: set(),
    ApplicationWorkflowStatus.WITHDRAWN: set(),
}


def can_transition(
    current: ApplicationWorkflowStatus,
    target: ApplicationWorkflowStatus,
) -> bool:
    return target in _ALLOWED_TRANSITIONS[current]


def _read(record: ApplicationWorkflow) -> ApplicationWorkflowRead:
    return ApplicationWorkflowRead.model_validate(record)


async def create_workflow(
    *,
    session: AsyncSession,
    user_id: int,
    job_match_id: int,
) -> ApplicationWorkflowRead:
    match = await session.scalar(
        select(JobMatch).where(
            JobMatch.id == job_match_id,
            JobMatch.user_id == user_id,
        )
    )
    if match is None:
        raise ApplicationWorkflowError("Job match not found")

    existing = await session.scalar(
        select(ApplicationWorkflow).where(
            ApplicationWorkflow.user_id == user_id,
            ApplicationWorkflow.job_match_id == job_match_id,
        )
    )
    if existing is not None:
        return _read(existing)

    record = ApplicationWorkflow(
        user_id=user_id,
        job_match_id=job_match_id,
        job_id=match.job_id,
        status=ApplicationWorkflowStatus.DRAFT.value,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def attach_documents(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
    resume_document_id: int,
    cover_letter_document_id: int | None,
) -> ApplicationWorkflowRead:
    record = await _get_record(session=session, user_id=user_id, workflow_id=workflow_id)

    if ApplicationWorkflowStatus(record.status) not in {
        ApplicationWorkflowStatus.DRAFT,
        ApplicationWorkflowStatus.MATERIALS_READY,
    }:
        raise ApplicationWorkflowError(
            "Documents can only be attached before approval review"
        )

    resume = await session.scalar(
        select(GeneratedDocument).where(
            GeneratedDocument.id == resume_document_id,
            GeneratedDocument.user_id == user_id,
            GeneratedDocument.job_id == record.job_id,
            GeneratedDocument.document_type == "resume",
        )
    )
    if resume is None:
        raise ApplicationWorkflowError("Valid resume document not found")

    if cover_letter_document_id is not None:
        cover = await session.scalar(
            select(GeneratedDocument).where(
                GeneratedDocument.id == cover_letter_document_id,
                GeneratedDocument.user_id == user_id,
                GeneratedDocument.job_id == record.job_id,
                GeneratedDocument.document_type == "cover_letter",
            )
        )
        if cover is None:
            raise ApplicationWorkflowError("Valid cover letter document not found")

    record.resume_document_id = resume_document_id
    record.cover_letter_document_id = cover_letter_document_id
    record.status = ApplicationWorkflowStatus.MATERIALS_READY.value

    await session.commit()
    await session.refresh(record)
    return _read(record)


async def request_approval(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
) -> ApplicationWorkflowRead:
    record = await _get_record(session=session, user_id=user_id, workflow_id=workflow_id)
    if record.resume_document_id is None:
        raise ApplicationWorkflowError("A resume must be attached before approval")
    _transition(record, ApplicationWorkflowStatus.AWAITING_APPROVAL)
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def approve_workflow(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
    notes: str | None,
) -> ApplicationWorkflowRead:
    record = await _get_record(session=session, user_id=user_id, workflow_id=workflow_id)
    _transition(record, ApplicationWorkflowStatus.APPROVED)
    record.approval_notes = notes
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def mark_submitted(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
    external_application_url: str | None,
) -> ApplicationWorkflowRead:
    record = await _get_record(session=session, user_id=user_id, workflow_id=workflow_id)
    _transition(record, ApplicationWorkflowStatus.SUBMITTED)
    record.external_application_url = external_application_url
    record.submitted_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def set_outcome(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
    target: ApplicationWorkflowStatus,
) -> ApplicationWorkflowRead:
    record = await _get_record(session=session, user_id=user_id, workflow_id=workflow_id)
    _transition(record, target)
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def list_workflows(
    *,
    session: AsyncSession,
    user_id: int,
) -> tuple[list[ApplicationWorkflowRead], int]:
    total = await session.scalar(
        select(func.count())
        .select_from(ApplicationWorkflow)
        .where(ApplicationWorkflow.user_id == user_id)
    ) or 0
    rows = await session.scalars(
        select(ApplicationWorkflow)
        .where(ApplicationWorkflow.user_id == user_id)
        .order_by(ApplicationWorkflow.updated_at.desc())
    )
    return [_read(row) for row in rows], total


async def get_workflow(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
) -> ApplicationWorkflowRead | None:
    record = await session.scalar(
        select(ApplicationWorkflow).where(
            ApplicationWorkflow.id == workflow_id,
            ApplicationWorkflow.user_id == user_id,
        )
    )
    return _read(record) if record is not None else None


async def _get_record(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
) -> ApplicationWorkflow:
    record = await session.scalar(
        select(ApplicationWorkflow).where(
            ApplicationWorkflow.id == workflow_id,
            ApplicationWorkflow.user_id == user_id,
        )
    )
    if record is None:
        raise ApplicationWorkflowError("Application workflow not found")
    return record


def _transition(
    record: ApplicationWorkflow,
    target: ApplicationWorkflowStatus,
) -> None:
    current = ApplicationWorkflowStatus(record.status)
    if not can_transition(current, target):
        raise ApplicationWorkflowError(
            f"Invalid workflow transition: {current.value} -> {target.value}"
        )
    record.status = target.value
