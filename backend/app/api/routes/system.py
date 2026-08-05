from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import enforce_public_rate_limit
from app.database.session import get_db_session
from app.schemas.system import HealthResponse, ReadinessResponse
from app.services.readiness_service import check_readiness

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health(
    request: Request,
) -> HealthResponse:
    await enforce_public_rate_limit(request)
    return HealthResponse()


@router.get("/ready", response_model=ReadinessResponse)
async def ready(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadinessResponse:
    await enforce_public_rate_limit(request)
    return await check_readiness(session)
