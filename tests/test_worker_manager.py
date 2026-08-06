import pytest

from app.core.background import RetryPolicy, TaskStatus
from app.core.task_queue import InMemoryTaskQueue
from app.workers.document_worker import DocumentWorker
from app.workers.worker_manager import WorkerManager


@pytest.mark.asyncio
async def test_worker_manager_completes_registered_task() -> None:
    async def handler(payload):
        return {"job_id": payload["job_id"]}

    queue = InMemoryTaskQueue()
    manager = WorkerManager(
        queue=queue,
        retry_policy=RetryPolicy(
            max_attempts=1,
            base_delay_seconds=0,
        ),
    )
    manager.register(DocumentWorker(handler))

    task = await queue.enqueue(
        name="document.generate",
        payload={
            "user_id": 1,
            "candidate_analysis_id": 2,
            "job_id": 3,
            "document_type": "resume",
        },
    )

    processed = await manager.process_next()

    assert processed.id == task.id
    assert processed.status is TaskStatus.COMPLETED
    assert processed.result == {"job_id": 3}
