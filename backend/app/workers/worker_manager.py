"""Worker registration, dispatch, retries, and cancellation."""

from __future__ import annotations

import asyncio
import logging

from app.core.background import BackgroundTask, RetryPolicy, TaskStatus
from app.core.task_queue import InMemoryTaskQueue
from app.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class WorkerNotRegisteredError(LookupError):
    """Raised when no worker is registered for a task name."""


class WorkerManager:
    """Dispatch queued tasks to registered workers."""

    def __init__(
        self,
        *,
        queue: InMemoryTaskQueue,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.queue = queue
        self.retry_policy = retry_policy or RetryPolicy()
        self._workers: dict[str, BaseWorker] = {}
        self._shutdown_requested = False

    def register(self, worker: BaseWorker) -> None:
        """Register or replace a worker for its task name."""

        self._workers[worker.task_name] = worker

    def get_worker(self, task_name: str) -> BaseWorker:
        """Return the worker registered for a task name."""

        worker = self._workers.get(task_name)
        if worker is None:
            raise WorkerNotRegisteredError(task_name)
        return worker

    async def process_task(self, task: BackgroundTask) -> BackgroundTask:
        """Execute one task and apply deterministic retry behavior."""

        if task.cancellation_requested:
            task.mark_cancelled()
            return task

        worker = self.get_worker(task.name)
        task.mark_running()

        try:
            result = await worker.execute(task)
        except Exception as exc:
            if task.cancellation_requested:
                task.mark_cancelled()
                return task

            task.mark_failed(str(exc))
            logger.exception(
                "Background task failed",
                extra={"task_id": task.id, "task_name": task.name},
            )

            if task.attempts < self.retry_policy.max_attempts:
                retry_number = task.attempts
                delay = self.retry_policy.delay_for_attempt(retry_number)
                await asyncio.sleep(delay)
                await self.queue.requeue(task.id)
            return task

        task.mark_completed(result)
        return task

    async def process_next(self) -> BackgroundTask:
        """Wait for and process the next queued task."""

        task = await self.queue.dequeue()
        return await self.process_task(task)

    async def run(self) -> None:
        """Continuously process tasks until shutdown is requested."""

        self._shutdown_requested = False
        while not self._shutdown_requested:
            await self.process_next()

    def request_shutdown(self) -> None:
        """Request a graceful stop after the active task finishes."""

        self._shutdown_requested = True

    async def cancel(self, task_id: str) -> BackgroundTask:
        """Request cancellation for a queued or active task."""

        return await self.queue.cancel(task_id)
