import pytest

from app.services.execution_pipeline import ExecutionPipeline


class FakeRunner:
    async def run(self, job):
        return {"job": job, "status": "done"}


@pytest.mark.asyncio
async def test_execution_pipeline_delegates_to_runner():
    pipeline = ExecutionPipeline(FakeRunner())

    result = await pipeline.execute({"id": 1})

    assert result == {
        "job": {"id": 1},
        "status": "done",
    }