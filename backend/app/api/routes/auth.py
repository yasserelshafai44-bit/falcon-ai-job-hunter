from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db_session
from app.models.user import User
from app.schemas.auth import (
    LocalPasswordResetRequest,
    LocalPasswordResetResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> TokenResponse:
    existing = await session.scalar(
        select(User).where(User.email == payload.email.lower())
    )
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=payload.email.lower(), password_hash=hash_password(payload.password)
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post(
    "/local-reset-password",
    response_model=LocalPasswordResetResponse,
    include_in_schema=False,
)
async def local_reset_password(
    payload: LocalPasswordResetRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LocalPasswordResetResponse:
    """Reset an existing password only in non-production local environments."""
    if settings.app_env != "development" or not settings.local_password_reset_enabled:
        raise HTTPException(status_code=404, detail="Not found")

    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found")

    user.password_hash = hash_password(payload.new_password)
    await session.commit()
    return LocalPasswordResetResponse(
        message="Password reset. Sign in with your new password."
    )


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
