"""Worker for outbound email tasks."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.background import BackgroundTask
from app.workers.base_worker import BaseWorker, WorkerExecutionError

EmailHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class EmailWorker(BaseWorker):
    """Execute email jobs through an injected delivery handler."""

    task_name = "email.send"

    def __init__(self, handler: EmailHandler) -> None:
        self._handler = handler

    async def execute(self, task: BackgroundTask) -> dict[str, Any]:
        required = {"recipient", "subject", "body"}
        missing = sorted(required.difference(task.payload))
        if missing:
            raise WorkerExecutionError(
                f"Missing email task fields: {', '.join(missing)}"
            )

        await self.report_progress(task, 20)
        result = await self._handler(task.payload)
        await self.report_progress(task, 90)
        return result
