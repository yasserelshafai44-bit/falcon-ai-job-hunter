from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.database.session import get_db_session
from app.models.candidate import Candidate
from app.models.candidate_analysis import CandidateAnalysis
from app.models.cv_document import CVDocument
from app.models.user import User
from app.schemas.candidate import CandidateResponse
from app.schemas.candidate_intelligence import (
    ApplyProfileSuggestionsRequest,
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

    record = await session.scalar(
        select(CandidateAnalysis).where(CandidateAnalysis.cv_document_id == document.id)
    )
    path = get_settings().cv_storage_path / document.stored_name
    if path.is_file():
        try:
            text = extract_cv_text(Path(path))
        except CVTextExtractionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    elif record is not None and record.extracted_text.strip():
        text = record.extracted_text
    else:
        raise HTTPException(status_code=404, detail="Stored CV file not found")

    analysis = analyze_candidate_text(text)
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

    await session.flush()
    candidate = await session.scalar(
        select(Candidate).where(Candidate.user_id == user.id)
    )
    if candidate is not None:
        candidate.profile_data = {
            **candidate.profile_data,
            "cv_analysis_id": record.id,
            "cv_analysis": analysis.model_dump(mode="json"),
        }

    await session.commit()
    await session.refresh(record)
    return _response(record)


@router.post("/{analysis_id}/apply-profile", response_model=CandidateResponse)
async def apply_profile_suggestions(
    analysis_id: int,
    payload: ApplyProfileSuggestionsRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Candidate:
    record = await session.scalar(
        select(CandidateAnalysis).where(
            CandidateAnalysis.id == analysis_id, CandidateAnalysis.user_id == user.id
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Candidate analysis not found")
    analysis = CandidateIntelligenceData.model_validate(record.analysis_data)
    allowed = {
        "full_name",
        "primary_location",
        "years_experience",
        "professional_summary",
        "seniority",
        "role_family",
        "skills",
        "industries",
        "leadership_scope",
        "certifications_qualifications",
    }
    selected = set(payload.fields)
    if not selected or not selected <= allowed:
        raise HTTPException(
            status_code=422, detail="Select valid CV suggestions to apply"
        )
    candidate = await session.scalar(
        select(Candidate).where(Candidate.user_id == user.id)
    )
    suggested_name = analysis.full_name.value if analysis.full_name else None
    if candidate is None:
        if "full_name" not in selected or not suggested_name:
            raise HTTPException(
                status_code=422,
                detail="A supported full name is required to create the profile",
            )
        candidate = Candidate(
            user_id=user.id,
            full_name=suggested_name,
            email=user.email,
            years_experience=0,
            profile_data={},
        )
        session.add(candidate)
    if "full_name" in selected and suggested_name:
        candidate.full_name = suggested_name
    if "primary_location" in selected and analysis.primary_location:
        candidate.location = analysis.primary_location.value
    if "years_experience" in selected and analysis.years_experience:
        candidate.years_experience = int(analysis.years_experience.value)
    enrichment = dict(candidate.profile_data.get("accepted_cv_enrichment", {}))
    for field in selected - {"full_name", "primary_location", "years_experience"}:
        value = (
            analysis.professional_summary_evidence
            if field == "professional_summary"
            else getattr(analysis, field)
        )
        if value not in (None, [], ""):
            enrichment[field] = (
                value.model_dump(mode="json")
                if hasattr(value, "model_dump")
                else [item.model_dump(mode="json") for item in value]
                if isinstance(value, list)
                else value
            )
    candidate.profile_data = {
        **candidate.profile_data,
        "cv_analysis_id": record.id,
        "accepted_cv_enrichment": enrichment,
    }
    await session.commit()
    await session.refresh(candidate)
    return candidate


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
