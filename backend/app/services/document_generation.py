import json
from hashlib import sha256

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.text_base import TextGenerationProvider
from app.models.application_status_event import ApplicationStatusEvent
from app.models.application_workflow import ApplicationWorkflow
from app.models.candidate_analysis import CandidateAnalysis
from app.models.discovered_job import DiscoveredJob
from app.models.generated_document import GeneratedDocument
from app.schemas.generation import GeneratedDocumentRead, GeneratedDocumentType
from app.services.candidate_context import enrich_analysis_with_profile
from app.services.grounded_materials import MaterialEvidenceError, validate_material
from app.services.prompt_builder import (
    PROMPT_VERSION,
    build_cover_letter_prompt,
    build_resume_prompt,
)


class GenerationInputError(ValueError):
    pass


async def generate_document(
    *,
    session: AsyncSession,
    provider: TextGenerationProvider,
    user_id: int,
    candidate_analysis_id: int,
    job_id: int,
    document_type: GeneratedDocumentType,
    tone: str,
    max_words: int,
    commit: bool = True,
) -> GeneratedDocumentRead:
    analysis = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.id == candidate_analysis_id,
            CandidateAnalysis.user_id == user_id,
        )
    )
    if analysis is None:
        raise GenerationInputError("Candidate analysis not found")
    job = await session.get(DiscoveredJob, job_id)
    if job is None:
        raise GenerationInputError("Job not found")

    builder = (
        build_resume_prompt
        if document_type is GeneratedDocumentType.RESUME
        else build_cover_letter_prompt
    )
    candidate_context = await enrich_analysis_with_profile(
        session, user_id, analysis.analysis_data
    )
    candidate_context["source_text"] = analysis.extracted_text
    system_prompt, user_prompt = builder(
        candidate_analysis=candidate_context,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        job_requirements=job.requirements,
        tone=tone,
        max_words=max_words,
    )
    try:
        content = (
            await provider.generate_text(
                system_prompt=system_prompt, user_prompt=user_prompt
            )
        ).strip()
        validate_material(content, json.loads(user_prompt))
    except MaterialEvidenceError as exc:
        raise GenerationInputError(str(exc)) from exc
    if not content:
        raise GenerationInputError("Generation provider returned empty content")
    if any(
        phrase in content.casefold()
        for phrase in (
            "evidence-based operations leader tailored to the target role",
            "verified achievement included from candidate evidence",
        )
    ):
        raise GenerationInputError("Placeholder application content was rejected")

    record = GeneratedDocument(
        user_id=user_id,
        candidate_analysis_id=candidate_analysis_id,
        job_id=job_id,
        document_type=document_type.value,
        provider=provider.name,
        prompt_version=PROMPT_VERSION,
        content=content,
        metadata_json={
            "tone": tone,
            "max_words": max_words,
            "job_title": job.title,
            "company": job.company,
            "cv_document_id": analysis.cv_document_id,
            "cv_source_sha256": sha256(analysis.extracted_text.encode()).hexdigest(),
            "generation_input_sha256": sha256(user_prompt.encode()).hexdigest(),
            "generation_method": provider.name,
            "quality_version": PROMPT_VERSION,
        },
        status="draft",
    )
    session.add(record)
    if commit:
        await session.commit()
    else:
        await session.flush()
    await session.refresh(record)
    return GeneratedDocumentRead.model_validate(record)


async def list_generation_history(
    *, session: AsyncSession, user_id: int
) -> tuple[list[GeneratedDocumentRead], int]:
    total = (
        await session.scalar(
            select(func.count())
            .select_from(GeneratedDocument)
            .where(GeneratedDocument.user_id == user_id)
        )
        or 0
    )
    rows = await session.scalars(
        select(GeneratedDocument)
        .where(GeneratedDocument.user_id == user_id)
        .order_by(GeneratedDocument.created_at.desc())
    )
    return [GeneratedDocumentRead.model_validate(row) for row in rows], total


async def update_generated_document(
    *, session: AsyncSession, user_id: int, document_id: int, content: str
) -> GeneratedDocumentRead:
    record = await session.scalar(
        select(GeneratedDocument).where(
            GeneratedDocument.id == document_id,
            GeneratedDocument.user_id == user_id,
        )
    )
    if record is None:
        raise GenerationInputError("Generated document not found")
    if record.status != "draft":
        raise GenerationInputError("Only draft documents can be revised")

    workflows = list(
        await session.scalars(
            select(ApplicationWorkflow)
            .where(
                ApplicationWorkflow.user_id == user_id,
                or_(
                    ApplicationWorkflow.resume_document_id == document_id,
                    ApplicationWorkflow.cover_letter_document_id == document_id,
                ),
            )
            .with_for_update()
        )
    )
    editable_statuses = {"materials_ready", "awaiting_approval"}
    if any(workflow.status not in editable_statuses for workflow in workflows):
        raise GenerationInputError(
            "Documents cannot be revised after application approval"
        )
    if not content.strip():
        raise GenerationInputError("Draft content cannot be blank")
    revisions = list(record.metadata_json.get("revisions", []))
    revisions.append(
        {"content": record.content, "updated_at": record.updated_at.isoformat()}
    )
    record.content = content.strip()
    record.metadata_json = {
        **record.metadata_json,
        "user_revised": True,
        "revisions": revisions,
    }
    for workflow in workflows:
        session.add(
            ApplicationStatusEvent(
                workflow_id=workflow.id,
                user_id=user_id,
                from_status=workflow.status,
                to_status="materials_ready",
                event_type="materials_revised",
            )
        )
        workflow.reviewed_at = None
        workflow.status = "materials_ready"
    await session.commit()
    await session.refresh(record)
    return GeneratedDocumentRead.model_validate(record)
