from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.calibration_review import CalibrationReview
from app.models.discovered_job import DiscoveredJob
from app.models.user import User
from app.schemas.calibration import (
    CalibrationEvaluation,
    CalibrationReviewList,
    CalibrationReviewRead,
    CorpusBuildRequest,
    ReviewUpdate,
    ValidationSampleRequest,
)
from app.services.calibration import (
    build_corpus,
    build_validation_sample,
    evaluate_corpus,
)
from app.services.vacancy_summary import build_human_review_summary

router = APIRouter(prefix="/calibration", tags=["ranking calibration"])


@router.post("/validation-sample", response_model=CalibrationReviewList)
async def create_validation_sample(
    payload: ValidationSampleRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CalibrationReviewList:
    try:
        await build_validation_sample(
            session,
            user_id=user.id,
            candidate_analysis_id=payload.candidate_analysis_id,
            providers=payload.providers,
            corpus_version=payload.corpus_version,
            sample_size=payload.sample_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return await list_reviews(
        user=user,
        session=session,
        corpus_version=payload.corpus_version,
        labelled_only=False,
    )


def _review_response(
    review: CalibrationReview, user: User, job: DiscoveredJob | None = None
) -> CalibrationReviewRead:
    """Expose persisted review state together with its authenticated reviewer."""
    return CalibrationReviewRead(
        id=review.id,
        candidate_analysis_id=review.candidate_analysis_id,
        job_id=review.job_id,
        human_label=review.human_label,
        reviewer_notes=review.reviewer_notes,
        vacancy_snapshot=review.vacancy_snapshot,
        falcon_snapshot=review.falcon_snapshot,
        human_review_summary=build_human_review_summary(review.vacancy_snapshot, job),
        corpus_version=review.corpus_version,
        reviewed=review.human_label is not None,
        reviewer_id=user.id,
        reviewer_email=user.email,
        reviewed_at=review.reviewed_at,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post("/corpus", response_model=CalibrationReviewList)
async def create_corpus(
    payload: CorpusBuildRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CalibrationReviewList:
    try:
        await build_corpus(
            session,
            user_id=user.id,
            candidate_analysis_id=payload.candidate_analysis_id,
            providers=payload.providers,
            corpus_version=payload.corpus_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await list_reviews(
        user=user,
        session=session,
        corpus_version=payload.corpus_version,
        labelled_only=False,
    )


@router.get("/reviews", response_model=CalibrationReviewList)
async def list_reviews(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    corpus_version: str = Query(default="live-v1", max_length=32),
    labelled_only: bool = False,
) -> CalibrationReviewList:
    filters = [
        CalibrationReview.user_id == user.id,
        CalibrationReview.corpus_version == corpus_version,
    ]
    if labelled_only:
        filters.append(CalibrationReview.human_label.is_not(None))
    rows = list(
        await session.scalars(
            select(CalibrationReview)
            .where(*filters)
            .order_by(CalibrationReview.human_label.is_not(None), CalibrationReview.id)
        )
    )
    reviewed = (
        await session.scalar(
            select(func.count()).where(
                CalibrationReview.user_id == user.id,
                CalibrationReview.corpus_version == corpus_version,
                CalibrationReview.human_label.is_not(None),
            )
        )
        or 0
    )
    jobs = {
        job.id: job
        for job in await session.scalars(
            select(DiscoveredJob).where(
                DiscoveredJob.id.in_([row.job_id for row in rows])
            )
        )
    }
    return CalibrationReviewList(
        items=[_review_response(row, user, jobs.get(row.job_id)) for row in rows],
        total=len(rows),
        reviewed=reviewed,
    )


@router.put("/reviews/{review_id}", response_model=CalibrationReviewRead)
async def update_review(
    review_id: int,
    payload: ReviewUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CalibrationReviewRead:
    review = await session.scalar(
        select(CalibrationReview).where(
            CalibrationReview.id == review_id,
            CalibrationReview.user_id == user.id,
        )
    )
    if review is None:
        raise HTTPException(status_code=404, detail="Calibration review not found")
    review.human_label = payload.human_label.value
    review.reviewer_notes = payload.reviewer_notes
    review.reviewed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(review)
    job = await session.get(DiscoveredJob, review.job_id)
    return _review_response(review, user, job)


@router.get("/evaluation", response_model=CalibrationEvaluation)
async def read_evaluation(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    corpus_version: str = Query(default="live-v1", max_length=32),
) -> CalibrationEvaluation:
    return await evaluate_corpus(
        session, user_id=user.id, corpus_version=corpus_version
    )


@router.get("/export")
async def export_corpus(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    corpus_version: str = Query(default="live-v1", max_length=32),
) -> dict:
    response = await list_reviews(
        user=user,
        session=session,
        corpus_version=corpus_version,
        labelled_only=False,
    )
    return {
        "schema_version": "1.0.0",
        "corpus_version": corpus_version,
        "exported_at": datetime.now(UTC).isoformat(),
        "human_labels_are_independent": True,
        "items": [item.model_dump(mode="json") for item in response.items],
    }
