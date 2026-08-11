from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.text_base import TextGenerationProvider
from app.schemas.generation import GeneratedDocumentType
from app.services.application_workflow import (
    attach_documents,
    create_workflow,
    request_approval,
)
from app.services.document_generation import generate_document
from app.services.matching_engine import calculate_and_persist_match


@dataclass(slots=True)
class PreparedApplication:
    job_match_id: int
    workflow_id: int
    resume_document_id: int
    cover_letter_document_id: int | None
    status: str


async def prepare_application(
    *,
    session: AsyncSession,
    provider: TextGenerationProvider,
    user_id: int,
    candidate_analysis_id: int,
    job_id: int,
    include_cover_letter: bool = True,
    tone: str = "professional",
    resume_max_words: int = 700,
    cover_letter_max_words: int = 450,
) -> PreparedApplication:
    """Build a human-reviewable application package for one discovered job.

    This deliberately stops at the approval gate. It does not submit an external
    application or bypass the user's review.
    """

    match = await calculate_and_persist_match(
        session=session,
        user_id=user_id,
        candidate_analysis_id=candidate_analysis_id,
        job_id=job_id,
    )

    workflow = await create_workflow(
        session=session,
        user_id=user_id,
        job_match_id=match.id,
    )

    resume = await generate_document(
        session=session,
        provider=provider,
        user_id=user_id,
        candidate_analysis_id=candidate_analysis_id,
        job_id=job_id,
        document_type=GeneratedDocumentType.RESUME,
        tone=tone,
        max_words=resume_max_words,
    )

    cover = None
    if include_cover_letter:
        cover = await generate_document(
            session=session,
            provider=provider,
            user_id=user_id,
            candidate_analysis_id=candidate_analysis_id,
            job_id=job_id,
            document_type=GeneratedDocumentType.COVER_LETTER,
            tone=tone,
            max_words=cover_letter_max_words,
        )

    workflow = await attach_documents(
        session=session,
        user_id=user_id,
        workflow_id=workflow.id,
        resume_document_id=resume.id,
        cover_letter_document_id=cover.id if cover is not None else None,
    )

    workflow = await request_approval(
        session=session,
        user_id=user_id,
        workflow_id=workflow.id,
    )

    return PreparedApplication(
        job_match_id=match.id,
        workflow_id=workflow.id,
        resume_document_id=resume.id,
        cover_letter_document_id=cover.id if cover is not None else None,
        status=str(workflow.status),
    )
