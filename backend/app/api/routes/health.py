from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.session import get_db_session
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HealthResponse:
    """Return service health and environment information."""

    if settings.app_env == "production":
        try:
            await session.execute(text("SELECT 1 FROM alembic_version LIMIT 1"))
        except Exception:
            raise HTTPException(
                status_code=503, detail="Database is unavailable"
            ) from None
    return HealthResponse(
        service=settings.app_name,
        environment=settings.app_env,
    )
