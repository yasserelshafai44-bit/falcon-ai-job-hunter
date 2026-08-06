"""Worker for resume and cover-letter generation tasks."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.background import BackgroundTask
from app.workers.base_worker import BaseWorker, WorkerExecutionError

DocumentHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class DocumentWorker(BaseWorker):
    """Execute document-generation jobs through an injected handler."""

    task_name = "document.generate"

    def __init__(self, handler: DocumentHandler) -> None:
        self._handler = handler

    async def execute(self, task: BackgroundTask) -> dict[str, Any]:
        required = {"user_id", "candidate_analysis_id", "job_id", "document_type"}
        missing = sorted(required.difference(task.payload))
        if missing:
            raise WorkerExecutionError(
                f"Missing document task fields: {', '.join(missing)}"
            )

        await self.report_progress(task, 10)
        result = await self._handler(task.payload)
        await self.report_progress(task, 90)
        return result
