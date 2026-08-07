import pytest

from app.services.failure_recovery import FailureRecovery
from app.services.job_state import JobState


class SuccessPipeline:
    async def execute(self, job):
        return {"job": job}


class FailingPipeline:
    async def execute(self, job):
        raise RuntimeError("failure")


@pytest.mark.asyncio
async def test_failure_recovery_success():
    recovery = FailureRecovery(max_retries=3)

    result = await recovery.recover({"id": 1}, SuccessPipeline())

    assert result["state"] == JobState.COMPLETED
    assert result["attempts"] == 1


@pytest.mark.asyncio
async def test_failure_recovery_failure():
    recovery = FailureRecovery(max_retries=2)

    result = await recovery.recover({"id": 1}, FailingPipeline())

    assert result["state"] == JobState.FAILED
    assert result["attempts"] == 2