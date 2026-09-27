from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.text_factory import get_text_generation_provider
from app.models.application_status_event import ApplicationStatusEvent
from app.models.application_workflow import ApplicationWorkflow
from app.models.generated_document import GeneratedDocument
from app.models.job_match import JobMatch
from app.schemas.application_workflow import ApplicationWorkflowRead
from app.schemas.generation import GeneratedDocumentType
from app.services.application_workflow import ApplicationWorkflowError
from app.services.document_generation import generate_document


async def regenerate_application_materials(
    *, session: AsyncSession, user_id: int, workflow_id: int
) -> ApplicationWorkflowRead:
    """Replace both draft pointers atomically; retain all original documents/history."""
    workflow = await session.scalar(
        select(ApplicationWorkflow)
        .where(
            ApplicationWorkflow.id == workflow_id,
            ApplicationWorkflow.user_id == user_id,
        )
        .with_for_update()
    )
    if workflow is None:
        raise ApplicationWorkflowError("Application workflow not found")
    if (
        workflow.status
        not in {"draft", "materials_ready", "awaiting_approval", "approved"}
        or workflow.submitted_at is not None
    ):
        raise ApplicationWorkflowError(
            "Submitted or closed applications cannot be regenerated"
        )
    match = await session.scalar(
        select(JobMatch).where(
            JobMatch.id == workflow.job_match_id,
            JobMatch.user_id == user_id,
            JobMatch.job_id == workflow.job_id,
        )
    )
    if match is None:
        raise ApplicationWorkflowError("Application candidate evidence not found")
    previous = {
        "resume_document_id": workflow.resume_document_id,
        "cover_letter_document_id": workflow.cover_letter_document_id,
        "status": workflow.status,
        "reviewed_at": (
            workflow.reviewed_at.isoformat() if workflow.reviewed_at else None
        ),
        "approval_notes": workflow.approval_notes,
    }
    provider = get_text_generation_provider()
    documents = []
    try:
        for kind, limit in (
            (GeneratedDocumentType.RESUME, 1200),
            (GeneratedDocumentType.COVER_LETTER, 350),
        ):
            document = await generate_document(
                session=session,
                provider=provider,
                user_id=user_id,
                candidate_analysis_id=match.candidate_analysis_id,
                job_id=workflow.job_id,
                document_type=kind,
                tone="professional",
                max_words=limit,
                commit=False,
            )
            record = await session.get(GeneratedDocument, document.id)
            record.metadata_json = {
                **record.metadata_json,
                "workflow_id": workflow.id,
                "replaces_application_materials": previous,
            }
            documents.append(document.id)
        workflow.resume_document_id, workflow.cover_letter_document_id = documents
        workflow.status = "materials_ready"
        workflow.reviewed_at = None
        workflow.approval_notes = None
        session.add(
            ApplicationStatusEvent(
                workflow_id=workflow.id,
                user_id=user_id,
                from_status=previous["status"],
                to_status="materials_ready",
                event_type="materials_regenerated",
            )
        )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    await session.refresh(workflow)
    return ApplicationWorkflowRead.model_validate(workflow)
