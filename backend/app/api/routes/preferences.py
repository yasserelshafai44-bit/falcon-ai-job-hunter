from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.job_preference import JobPreference
from app.models.user import User
from app.schemas.preferences import JobPreferenceResponse, JobPreferenceUpsert

router = APIRouter(prefix="/preferences", tags=["job preferences"])


@router.get("", response_model=JobPreferenceResponse)
async def get_preferences(user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> JobPreference:
    preferences = await session.scalar(select(JobPreference).where(JobPreference.user_id == user.id))
    if preferences is None:
        raise HTTPException(status_code=404, detail="Job preferences not found")
    return preferences


@router.put("", response_model=JobPreferenceResponse)
async def upsert_preferences(payload: JobPreferenceUpsert, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> JobPreference:
    preferences = await session.scalar(select(JobPreference).where(JobPreference.user_id == user.id))
    values = payload.model_dump()
    if preferences is None:
        preferences = JobPreference(user_id=user.id, **values)
        session.add(preferences)
    else:
        for key, value in values.items():
            setattr(preferences, key, value)
    await session.commit()
    await session.refresh(preferences)
    return preferences
