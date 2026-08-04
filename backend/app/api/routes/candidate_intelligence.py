from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.session import get_db_session
from app.models.candidate_analysis import CandidateAnalysis
from app.models.cv_document import CVDocument
from app.models.user import User
from app.schemas.candidate_intelligence import (
    CandidateAnalysisResponse,
    CandidateIntelligenceData,
)
from app.services.candidate_intelligence import analyze_candidate_text
from app.services.cv_text_extractor import CVTextExtractionError, extract_cv_text

router = APIRouter(prefix="/candidate-intelligence", tags=["candidate intelligence"])


def _response(record: CandidateAnalysis) -> CandidateAnalysisResponse:
    return CandidateAnalysisResponse(
        id=record.id,
        cv_document_id=record.cv_document_id,
        analysis=CandidateIntelligenceData.model_validate(record.analysis_data),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "/cvs/{cv_document_id}/analyze",
    response_model=CandidateAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_cv(
    cv_document_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CandidateAnalysisResponse:
    document = await session.scalar(
        select(CVDocument).where(
            CVDocument.id == cv_document_id,
            CVDocument.user_id == user.id,
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="CV document not found")

    path = get_settings().cv_storage_path / document.stored_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored CV file not found")

    try:
        text = extract_cv_text(Path(path))
    except CVTextExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    analysis = analyze_candidate_text(text)
    record = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.cv_document_id == document.id
        )
    )
    if record is None:
        record = CandidateAnalysis(
            cv_document_id=document.id,
            user_id=user.id,
            extracted_text=text,
            analysis_data=analysis.model_dump(),
        )
        session.add(record)
    else:
        record.extracted_text = text
        record.analysis_data = analysis.model_dump()

    await session.commit()
    await session.refresh(record)
    return _response(record)


@router.get(
    "/cvs/{cv_document_id}",
    response_model=CandidateAnalysisResponse,
)
async def get_cv_analysis(
    cv_document_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CandidateAnalysisResponse:
    record = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.cv_document_id == cv_document_id,
            CandidateAnalysis.user_id == user.id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Candidate analysis not found")
    return _response(record)
