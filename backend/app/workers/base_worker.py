"""Base abstractions for background workers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.background import BackgroundTask


class WorkerExecutionError(RuntimeError):
    """Raised when a worker cannot process a task payload."""


class BaseWorker(ABC):
    """Base class for a task-specific worker."""

    task_name: str

    def accepts(self, task: BackgroundTask) -> bool:
        """Return whether this worker can execute the task."""

        return task.name == self.task_name

    @abstractmethod
    async def execute(self, task: BackgroundTask) -> dict[str, Any]:
        """Execute a task and return a serializable result."""

        raise NotImplementedError

    async def report_progress(
        self,
        task: BackgroundTask,
        progress: int,
    ) -> None:
        """Update task progress while respecting cancellation."""

        if task.cancellation_requested:
            task.mark_cancelled()
            raise WorkerExecutionError("Task cancellation requested")

        task.update_progress(progress)
