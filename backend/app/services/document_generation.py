from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.providers.text_base import TextGenerationProvider
from app.models.candidate_analysis import CandidateAnalysis
from app.models.discovered_job import DiscoveredJob
from app.models.generated_document import GeneratedDocument
from app.schemas.generation import GeneratedDocumentRead, GeneratedDocumentType
from app.services.prompt_builder import PROMPT_VERSION, build_cover_letter_prompt, build_resume_prompt

class GenerationInputError(ValueError):
    pass

async def generate_document(*, session: AsyncSession, provider: TextGenerationProvider, user_id: int, candidate_analysis_id: int, job_id: int, document_type: GeneratedDocumentType, tone: str, max_words: int) -> GeneratedDocumentRead:
    analysis = await session.scalar(select(CandidateAnalysis).where(CandidateAnalysis.id == candidate_analysis_id, CandidateAnalysis.user_id == user_id))
    if analysis is None:
        raise GenerationInputError("Candidate analysis not found")
    job = await session.get(DiscoveredJob, job_id)
    if job is None:
        raise GenerationInputError("Job not found")

    builder = build_resume_prompt if document_type is GeneratedDocumentType.RESUME else build_cover_letter_prompt
    system_prompt, user_prompt = builder(
        candidate_analysis=analysis.analysis_data,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        tone=tone,
        max_words=max_words,
    )
    content = (await provider.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)).strip()
    if not content:
        raise GenerationInputError("Generation provider returned empty content")

    record = GeneratedDocument(
        user_id=user_id,
        candidate_analysis_id=candidate_analysis_id,
        job_id=job_id,
        document_type=document_type.value,
        provider=provider.name,
        prompt_version=PROMPT_VERSION,
        content=content,
        metadata_json={"tone": tone, "max_words": max_words, "job_title": job.title, "company": job.company},
        status="draft",
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return GeneratedDocumentRead.model_validate(record)

async def list_generation_history(*, session: AsyncSession, user_id: int) -> tuple[list[GeneratedDocumentRead], int]:
    total = await session.scalar(select(func.count()).select_from(GeneratedDocument).where(GeneratedDocument.user_id == user_id)) or 0
    rows = await session.scalars(select(GeneratedDocument).where(GeneratedDocument.user_id == user_id).order_by(GeneratedDocument.created_at.desc()))
    return [GeneratedDocumentRead.model_validate(row) for row in rows], total
