from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.user import User
from app.schemas.job_matching import (
    JobMatchList,
    JobMatchRead,
    RecalculateMatchesRequest,
    RecalculateMatchesResponse,
    ScoreJobRequest,
)
from app.services.matching_engine import (
    MatchingInputError,
    calculate_and_persist_match,
    get_match,
    list_matches,
)

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/jobs/{job_id}/score", response_model=JobMatchRead)
async def score_job(
    job_id: int,
    payload: ScoreJobRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobMatchRead:
    try:
        return await calculate_and_persist_match(
            session=session,
            user_id=user.id,
            candidate_analysis_id=payload.candidate_analysis_id,
            job_id=job_id,
        )
    except MatchingInputError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=JobMatchList)
async def read_matches(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobMatchList:
    items, total = await list_matches(session=session, user_id=user.id)
    return JobMatchList(items=items, total=total)


@router.get("/{match_id}", response_model=JobMatchRead)
async def read_match(
    match_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobMatchRead:
    item = await get_match(session=session, user_id=user.id, match_id=match_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return item


@router.post("/recalculate", response_model=RecalculateMatchesResponse)
async def recalculate_matches(
    payload: RecalculateMatchesRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecalculateMatchesResponse:
    updated = 0
    failed: list[int] = []
    for job_id in payload.job_ids:
        try:
            await calculate_and_persist_match(
                session=session,
                user_id=user.id,
                candidate_analysis_id=payload.candidate_analysis_id,
                job_id=job_id,
            )
            updated += 1
        except MatchingInputError:
            failed.append(job_id)
    return RecalculateMatchesResponse(updated=updated, failed_job_ids=failed)
