from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.text_factory import get_text_generation_provider
from app.schemas.system import ReadinessCheck, ReadinessResponse


async def check_readiness(session: AsyncSession) -> ReadinessResponse:
    checks: list[ReadinessCheck] = []

    try:
        await session.execute(text("SELECT 1"))
        checks.append(ReadinessCheck(name="database", status="ok"))
    except Exception:
        checks.append(
            ReadinessCheck(
                name="database",
                status="failed",
                detail="Database connectivity check failed",
            )
        )

    try:
        provider = get_text_generation_provider()
        checks.append(
            ReadinessCheck(
                name="text_generation_provider",
                status="ok",
                detail=provider.name,
            )
        )
    except Exception:
        checks.append(
            ReadinessCheck(
                name="text_generation_provider",
                status="failed",
                detail="Provider configuration is invalid",
            )
        )

    status = "ready" if all(check.status == "ok" for check in checks) else "degraded"
    return ReadinessResponse(status=status, checks=checks)
