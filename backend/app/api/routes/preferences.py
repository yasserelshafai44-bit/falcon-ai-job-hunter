from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.discovered_job import DiscoveredJob
from app.models.job_match import JobMatch
from app.models.job_preference import JobPreference
from app.models.user import User
from app.schemas.preferences import JobPreferenceResponse, JobPreferenceUpsert
from app.services.location_fit import assess_location

router = APIRouter(prefix="/preferences", tags=["job preferences"])


@router.get("", response_model=JobPreferenceResponse)
async def get_preferences(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobPreference:
    preferences = await session.scalar(
        select(JobPreference).where(JobPreference.user_id == user.id)
    )
    if preferences is None:
        raise HTTPException(status_code=404, detail="Job preferences not found")
    return preferences


@router.put("", response_model=JobPreferenceResponse)
async def upsert_preferences(
    payload: JobPreferenceUpsert,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobPreference:
    preferences = await session.scalar(
        select(JobPreference).where(JobPreference.user_id == user.id)
    )
    values = payload.model_dump(exclude_unset=preferences is not None)
    if preferences is None:
        preferences = JobPreference(user_id=user.id, **values)
        session.add(preferences)
    else:
        for key, value in values.items():
            setattr(preferences, key, value)
    await session.flush()
    context = JobPreferenceResponse.model_validate(preferences).model_dump()
    rows = await session.execute(
        select(JobMatch, DiscoveredJob)
        .join(DiscoveredJob, DiscoveredJob.id == JobMatch.job_id)
        .where(JobMatch.user_id == user.id)
    )
    for match, job in rows:
        _, status, reason = assess_location(
            context, job.location, remote=job.remote, workplace_type=job.workplace_type
        )
        match.evidence = [
            e for e in match.evidence if e.get("dimension") != "location"
        ] + [
            {
                "dimension": "location",
                "contribution": 0,
                "max_score": 0,
                "status": status,
                "explanation": reason,
                "sources": [],
            }
        ]
    await session.commit()
    await session.refresh(preferences)
    return preferences
