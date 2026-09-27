from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_status_event import ApplicationStatusEvent
from app.models.application_workflow import ApplicationWorkflow
from app.models.candidate_analysis import CandidateAnalysis
from app.models.discovered_job import DiscoveredJob
from app.models.generated_document import GeneratedDocument
from app.models.job_match import JobMatch
from app.schemas.application_workflow import (
    ApplicationReview,
    ApplicationWorkflowRead,
    ApplicationWorkflowStatus,
    ReviewDocument,
    ReviewJob,
    ReviewMatch,
)
from app.services.application_routing import application_route


class ApplicationWorkflowError(ValueError):
    """Raised when an application workflow action is invalid."""


_ALLOWED_TRANSITIONS: dict[
    ApplicationWorkflowStatus, set[ApplicationWorkflowStatus]
] = {
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

    inactive_statuses = {
        ApplicationWorkflowStatus.REJECTED.value,
        ApplicationWorkflowStatus.WITHDRAWN.value,
    }
    existing = await session.scalar(
        select(ApplicationWorkflow)
        .where(
            ApplicationWorkflow.user_id == user_id,
            ApplicationWorkflow.job_id == match.job_id,
            ApplicationWorkflow.status.not_in(inactive_statuses),
        )
        .order_by(ApplicationWorkflow.created_at.desc())
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
    await session.flush()
    _add_status_event(session, record, None, record.status, "created")
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
    record = await _get_record(
        session=session, user_id=user_id, workflow_id=workflow_id
    )

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

    previous = record.status
    record.resume_document_id = resume_document_id
    record.cover_letter_document_id = cover_letter_document_id
    record.status = ApplicationWorkflowStatus.MATERIALS_READY.value
    record.reviewed_at = None
    _add_status_event(session, record, previous, record.status, "materials_attached")

    await session.commit()
    await session.refresh(record)
    return _read(record)


async def request_approval(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
) -> ApplicationWorkflowRead:
    record = await _get_record(
        session=session, user_id=user_id, workflow_id=workflow_id
    )
    if record.resume_document_id is None:
        raise ApplicationWorkflowError("A resume must be attached before approval")
    await _require_reviewable_materials(session, record)
    if record.reviewed_at is None:
        raise ApplicationWorkflowError(
            "Review the resume and cover letter before requesting approval"
        )
    previous = record.status
    _transition(record, ApplicationWorkflowStatus.AWAITING_APPROVAL)
    _add_status_event(session, record, previous, record.status, "approval_requested")
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def mark_reviewed(
    *, session: AsyncSession, user_id: int, workflow_id: int
) -> ApplicationWorkflowRead:
    record = await _get_record(
        session=session, user_id=user_id, workflow_id=workflow_id
    )
    if (
        ApplicationWorkflowStatus(record.status)
        is not ApplicationWorkflowStatus.MATERIALS_READY
    ):
        raise ApplicationWorkflowError(
            "Only prepared application materials can be marked reviewed"
        )
    if record.resume_document_id is None or record.cover_letter_document_id is None:
        raise ApplicationWorkflowError(
            "Both resume and cover letter are required before review"
        )
    await _require_reviewable_materials(session, record)
    record.reviewed_at = datetime.now(UTC)
    _add_status_event(session, record, record.status, record.status, "reviewed")
    await session.commit()
    await session.refresh(record)
    return _read(record)


def _review_document(record: GeneratedDocument, source_text: str) -> ReviewDocument:
    source_lines = {
        " ".join(line.casefold().split())
        for line in source_text.splitlines()
        if line.strip()
    }
    changes = [
        f"Generated draft line: {line.strip()}"
        for line in record.content.splitlines()
        if line.strip() and " ".join(line.casefold().split()) not in source_lines
    ][:100]
    return ReviewDocument(
        id=record.id,
        document_type=record.document_type,
        content=record.content,
        status=record.status,
        metadata=record.metadata_json,
        updated_at=record.updated_at,
        change_summary=changes,
    )


def _review_match(record: JobMatch) -> ReviewMatch:
    """Normalize persisted scoring detail for one non-duplicative review stream."""
    structured = list(record.evidence or [])
    explanations = {
        str(item.get("explanation") or "").strip()
        for item in structured
        if item.get("explanation")
    }
    strengths = [item for item in record.strengths if item not in explanations]
    gaps = list(dict.fromkeys(record.gaps))
    positive_evidence: list[dict] = []
    uncertainty = [
        item for item in dict.fromkeys(record.uncertainty) if item not in gaps
    ]
    seen_dimensions: set[str] = set()
    seen_explanations: set[str] = set()
    for item in structured:
        dimension = str(item.get("dimension") or "")
        explanation = str(item.get("explanation") or "").strip()
        identity = explanation.casefold()
        if dimension in seen_dimensions or (identity and identity in seen_explanations):
            continue
        seen_dimensions.add(dimension)
        if identity:
            seen_explanations.add(identity)
        contribution = float(item.get("contribution") or 0)
        preference_unknown = dimension == "salary" and "not stated" in identity
        if contribution <= 0 or preference_unknown:
            if (
                explanation
                and explanation not in gaps
                and explanation not in uncertainty
            ):
                uncertainty.append(explanation)
        else:
            positive_evidence.append(item)

    return ReviewMatch(
        id=record.id,
        overall_score=record.overall_score,
        recommendation=record.recommendation,
        strengths=strengths,
        gaps=gaps,
        mandatory_failures=list(dict.fromkeys(record.mandatory_failures)),
        evidence=positive_evidence,
        uncertainty=list(dict.fromkeys(uncertainty)),
    )


async def get_application_review(
    *, session: AsyncSession, user_id: int, workflow_id: int
) -> ApplicationReview:
    workflow = await session.scalar(
        select(ApplicationWorkflow).where(
            ApplicationWorkflow.id == workflow_id,
            ApplicationWorkflow.user_id == user_id,
        )
    )
    if workflow is None:
        raise ApplicationWorkflowError("Application workflow not found")
    match = await session.scalar(
        select(JobMatch).where(
            JobMatch.id == workflow.job_match_id,
            JobMatch.user_id == user_id,
        )
    )
    job = await session.get(DiscoveredJob, workflow.job_id)
    analysis = (
        await session.scalar(
            select(CandidateAnalysis).where(
                CandidateAnalysis.id == match.candidate_analysis_id,
                CandidateAnalysis.user_id == user_id,
            )
        )
        if match is not None
        else None
    )
    resume = (
        await session.get(GeneratedDocument, workflow.resume_document_id)
        if workflow.resume_document_id is not None
        else None
    )
    cover = (
        await session.get(GeneratedDocument, workflow.cover_letter_document_id)
        if workflow.cover_letter_document_id is not None
        else None
    )
    if match is None or job is None or analysis is None:
        raise ApplicationWorkflowError("Application review data is incomplete")
    if resume is None or resume.user_id != user_id:
        raise ApplicationWorkflowError("Tailored resume is missing")
    if cover is None or cover.user_id != user_id:
        raise ApplicationWorkflowError("Cover letter is missing")

    questions_status, questions_note = employer_question_state(job)
    return ApplicationReview(
        application_route=application_route(job),
        employer_questions_status=questions_status,
        employer_questions_note=questions_note,
        workflow=_read(workflow),
        job=ReviewJob(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
        ),
        match=_review_match(match),
        original_cv_evidence=analysis.analysis_data,
        original_cv_text=analysis.extracted_text,
        resume=_review_document(resume, analysis.extracted_text),
        cover_letter=_review_document(cover, analysis.extracted_text),
        unanswered_employer_questions=list(
            dict.fromkeys(
                question
                for source in (job.source_records or [])
                if isinstance(source, dict)
                for question in (source.get("application_questions") or [])
                if isinstance(question, str) and question.strip()
            )
        ),
        status_history=list(
            await session.scalars(
                select(ApplicationStatusEvent)
                .where(
                    ApplicationStatusEvent.workflow_id == workflow.id,
                    ApplicationStatusEvent.user_id == user_id,
                )
                .order_by(ApplicationStatusEvent.created_at, ApplicationStatusEvent.id)
            )
        ),
    )


def employer_question_state(job: DiscoveredJob) -> tuple[str, str]:
    sources = [s for s in (job.source_records or []) if isinstance(s, dict)]
    if any(
        isinstance(q, str) and q.strip()
        for source in sources
        for q in (source.get("application_questions") or [])
    ):
        return "retrieved", (
            "Known employer questions require answers on the employer site."
        )
    if any(s.get("application_questions_status") == "none_required" for s in sources):
        return "none_required", (
            "The employer source confirms no employer questions are required."
        )
    if urlsplit(job.url).hostname == "jobs.smartrecruiters.com":
        return "requires_employer_site", (
            "Employer questions require review on employer site. Falcon's existing "
            "integration retrieves public vacancies, not application forms or answers. "
            "Questions, login and consent requirements have not been checked. "
            "You can approve the saved materials now; review and answer any questions "
            "on the official form before explicitly submitting there."
        )
    if any(s.get("application_questions_status") == "unavailable" for s in sources):
        return "unavailable", (
            "Employer questions cannot currently be retrieved automatically. "
            "Review the employer site."
        )
    return "unknown", (
        "Employer questions: not yet checked. "
        "Review the official employer form before submission."
    )


async def approve_workflow(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
    notes: str | None,
) -> ApplicationWorkflowRead:
    record = await _get_record(
        session=session, user_id=user_id, workflow_id=workflow_id
    )
    previous = record.status
    if record.reviewed_at is None:
        raise ApplicationWorkflowError("Review both current drafts before approval")
    await _require_reviewable_materials(session, record)
    _transition(record, ApplicationWorkflowStatus.APPROVED)
    _add_status_event(session, record, previous, record.status, "approved")
    record.approval_notes = notes
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def approve_reviewed_materials(*, session, user_id, workflow_id):
    record = await _get_record(
        session=session, user_id=user_id, workflow_id=workflow_id
    )
    if record.status not in {"materials_ready", "awaiting_approval"}:
        raise ApplicationWorkflowError("Only prepared materials can be approved")
    await _require_reviewable_materials(session, record)
    job = await session.get(DiscoveredJob, record.job_id)
    previous = record.status
    record.reviewed_at = datetime.now(UTC)
    record.status = "approved"
    record.application_method = application_route(job)["method"]
    record.approval_notes = (
        "Owner explicitly reviewed and approved these materials; "
        "no external submission authorised."
    )
    _add_status_event(session, record, previous, record.status, "materials_approved")
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
    await _get_record(session=session, user_id=user_id, workflow_id=workflow_id)
    raise ApplicationWorkflowError(
        "Employer/ATS submission confirmation is not integrated. "
        "Continue to the employer; Falcon will keep this application approved, "
        "not submitted."
    )


async def set_outcome(
    *,
    session: AsyncSession,
    user_id: int,
    workflow_id: int,
    target: ApplicationWorkflowStatus,
) -> ApplicationWorkflowRead:
    if target not in {
        ApplicationWorkflowStatus.REJECTED,
        ApplicationWorkflowStatus.INTERVIEW,
        ApplicationWorkflowStatus.OFFER,
        ApplicationWorkflowStatus.WITHDRAWN,
    }:
        raise ApplicationWorkflowError("Use the dedicated review and approval actions")
    record = await _get_record(
        session=session, user_id=user_id, workflow_id=workflow_id
    )
    previous = record.status
    _transition(record, target)
    _add_status_event(session, record, previous, record.status, "status_changed")
    await session.commit()
    await session.refresh(record)
    return _read(record)


async def list_workflows(
    *,
    session: AsyncSession,
    user_id: int,
) -> tuple[list[ApplicationWorkflowRead], int]:
    total = (
        await session.scalar(
            select(func.count())
            .select_from(ApplicationWorkflow)
            .where(ApplicationWorkflow.user_id == user_id)
        )
        or 0
    )
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
        select(ApplicationWorkflow)
        .where(
            ApplicationWorkflow.id == workflow_id,
            ApplicationWorkflow.user_id == user_id,
        )
        .with_for_update()
    )
    if record is None:
        raise ApplicationWorkflowError("Application workflow not found")
    return record


async def _require_reviewable_materials(
    session: AsyncSession, workflow: ApplicationWorkflow
) -> None:
    match = await session.get(JobMatch, workflow.job_match_id)
    for document_id, kind in (
        (workflow.resume_document_id, "resume"),
        (workflow.cover_letter_document_id, "cover_letter"),
    ):
        document = (
            await session.get(GeneratedDocument, document_id) if document_id else None
        )
        if (
            match is None
            or document is None
            or match.user_id != workflow.user_id
            or match.job_id != workflow.job_id
            or document.user_id != workflow.user_id
            or document.job_id != workflow.job_id
            or document.candidate_analysis_id != match.candidate_analysis_id
            or document.document_type != kind
            or not document.content.strip()
        ):
            raise ApplicationWorkflowError(
                "Both drafts must belong to this application's CV and vacancy"
            )
        if any(
            phrase in document.content.casefold()
            for phrase in (
                "evidence-based operations leader tailored to the target role",
                "verified achievement included from candidate evidence",
            )
        ):
            raise ApplicationWorkflowError(
                "Regenerate the placeholder drafts before review"
            )


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


def _add_status_event(
    session: AsyncSession,
    record: ApplicationWorkflow,
    from_status: str | None,
    to_status: str,
    event_type: str,
) -> None:
    session.add(
        ApplicationStatusEvent(
            workflow_id=record.id,
            user_id=record.user_id,
            from_status=from_status,
            to_status=to_status,
            event_type=event_type,
        )
    )
