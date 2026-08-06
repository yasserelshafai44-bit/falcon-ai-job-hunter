"""Framework-agnostic in-memory background task queue."""

from __future__ import annotations

import asyncio
from collections import deque

from app.core.background import BackgroundTask, TaskStatus


class TaskNotFoundError(KeyError):
    """Raised when a requested task does not exist."""


class InMemoryTaskQueue:
    """Concurrency-safe FIFO task queue for one application process."""

    def __init__(self) -> None:
        self._tasks: dict[str, BackgroundTask] = {}
        self._pending: deque[str] = deque()
        self._condition = asyncio.Condition()

    async def enqueue(
        self,
        *,
        name: str,
        payload: dict[str, object],
    ) -> BackgroundTask:
        """Create and enqueue a task."""

        task = BackgroundTask(name=name, payload=dict(payload))

        async with self._condition:
            self._tasks[task.id] = task
            self._pending.append(task.id)
            self._condition.notify()

        return task

    async def dequeue(self) -> BackgroundTask:
        """Wait for and return the next non-cancelled task."""

        async with self._condition:
            while True:
                while not self._pending:
                    await self._condition.wait()

                task_id = self._pending.popleft()
                task = self._tasks[task_id]

                if task.status is TaskStatus.CANCELLED:
                    continue

                return task

    async def get(self, task_id: str) -> BackgroundTask:
        """Return a task by ID."""

        task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def list_tasks(self) -> list[BackgroundTask]:
        """Return tasks ordered by creation time."""

        return sorted(self._tasks.values(), key=lambda task: task.created_at)

    async def cancel(self, task_id: str) -> BackgroundTask:
        """Request task cancellation."""

        task = await self.get(task_id)
        task.request_cancellation()
        return task

    async def requeue(self, task_id: str) -> BackgroundTask:
        """Return a failed or running task to the queue."""

        task = await self.get(task_id)
        task.status = TaskStatus.QUEUED
        task.error = None

        async with self._condition:
            self._pending.append(task.id)
            self._condition.notify()

        return task

    async def clear(self) -> None:
        """Remove all queued and tracked tasks."""

        async with self._condition:
            self._tasks.clear()
            self._pending.clear()
