import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.readiness_service import check_readiness


class FakeResult:
    pass


class FakeSession:
    async def execute(self, statement):
        del statement
        return FakeResult()


@pytest.mark.asyncio
async def test_readiness_reports_ready_when_dependencies_work() -> None:
    result = await check_readiness(FakeSession())  # type: ignore[arg-type]

    assert result.status == "ready"
    assert any(check.name == "database" for check in result.checks)
