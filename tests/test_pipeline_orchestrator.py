import pytest

from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.services.job_state import JobState


class FakePipeline:
    async def execute(self, job):
        return {"id": job["id"]}


@pytest.mark.asyncio
async def test_pipeline_orchestrator_success():
    orchestrator = PipelineOrchestrator(FakePipeline())

    result = await orchestrator.execute({"id": 1})

    assert result["state"] == JobState.COMPLETED
    assert result["result"] == {"id": 1}