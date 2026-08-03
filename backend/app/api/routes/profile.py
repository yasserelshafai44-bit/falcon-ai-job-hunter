from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.session import get_db_session
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate import CandidateResponse, CandidateUpsert

router = APIRouter(prefix="/profile", tags=["candidate profile"])


@router.get("", response_model=CandidateResponse)
async def get_profile(user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> Candidate:
    profile = await session.scalar(select(Candidate).where(Candidate.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return profile


@router.put("", response_model=CandidateResponse)
async def upsert_profile(payload: CandidateUpsert, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> Candidate:
    profile = await session.scalar(select(Candidate).where(Candidate.user_id == user.id))
    values = payload.model_dump()
    if profile is None:
        profile = Candidate(user_id=user.id, **values)
        session.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
    await session.commit()
    await session.refresh(profile)
    return profile
