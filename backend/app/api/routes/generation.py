from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.providers.text_factory import get_text_generation_provider
from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.user import User
from app.schemas.generation import GenerateDocumentRequest, GeneratedDocumentRead, GeneratedDocumentType, GenerationHistoryResponse
from app.services.document_generation import GenerationInputError, generate_document, list_generation_history

router = APIRouter(tags=["document generation"])

@router.post("/resume/generate", response_model=GeneratedDocumentRead)
async def generate_resume(payload: GenerateDocumentRequest, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> GeneratedDocumentRead:
    try:
        return await generate_document(session=session, provider=get_text_generation_provider(), user_id=user.id, candidate_analysis_id=payload.candidate_analysis_id, job_id=payload.job_id, document_type=GeneratedDocumentType.RESUME, tone=payload.tone, max_words=payload.max_words)
    except GenerationInputError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.post("/cover-letter/generate", response_model=GeneratedDocumentRead)
async def generate_cover_letter(payload: GenerateDocumentRequest, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> GeneratedDocumentRead:
    try:
        return await generate_document(session=session, provider=get_text_generation_provider(), user_id=user.id, candidate_analysis_id=payload.candidate_analysis_id, job_id=payload.job_id, document_type=GeneratedDocumentType.COVER_LETTER, tone=payload.tone, max_words=payload.max_words)
    except GenerationInputError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/generation/history", response_model=GenerationHistoryResponse)
async def generation_history(user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> GenerationHistoryResponse:
    items, total = await list_generation_history(session=session, user_id=user.id)
    return GenerationHistoryResponse(items=items, total=total)
