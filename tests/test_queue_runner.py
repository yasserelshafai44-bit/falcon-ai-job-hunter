import pytest

from app.services.queue_runner import QueueRunner


class FakeWorkerManager:
    async def process_task(self, job):
        return {"processed": True, "job": job}


@pytest.mark.asyncio
async def test_queue_runner_uses_worker_manager():
    runner = QueueRunner(FakeWorkerManager())

    result = await runner.run({"id": 1})

    assert result == {
        "processed": True,
        "job": {"id": 1},
    }