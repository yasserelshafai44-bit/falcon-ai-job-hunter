import pytest

from app.core.background import BackgroundTask
from app.workers.email_worker import EmailWorker


@pytest.mark.asyncio
async def test_email_worker_executes_handler() -> None:
    async def handler(payload):
        return {"message_id": "abc", "recipient": payload["recipient"]}

    worker = EmailWorker(handler)
    task = BackgroundTask(
        name="email.send",
        payload={
            "recipient": "user@example.com",
            "subject": "Hello",
            "body": "Body",
        },
    )

    result = await worker.execute(task)

    assert result["message_id"] == "abc"
    assert task.progress == 90
