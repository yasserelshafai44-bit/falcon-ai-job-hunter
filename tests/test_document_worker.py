import pytest

from app.core.background import BackgroundTask
from app.workers.document_worker import DocumentWorker


@pytest.mark.asyncio
async def test_document_worker_executes_handler() -> None:
    async def handler(payload):
        return {"document_id": 7, "type": payload["document_type"]}

    worker = DocumentWorker(handler)
    task = BackgroundTask(
        name="document.generate",
        payload={
            "user_id": 1,
            "candidate_analysis_id": 2,
            "job_id": 3,
            "document_type": "resume",
        },
    )

    result = await worker.execute(task)

    assert result == {"document_id": 7, "type": "resume"}
    assert task.progress == 90
