"""Dispatch scheduled jobs into the background task queue."""

from __future__ import annotations

from datetime import datetime

from app.core.background import BackgroundTask
from app.core.task_queue import InMemoryTaskQueue
from app.jobs.job_registry import ScheduledJob


class JobDispatcher:
    """Convert a scheduled job into a queued background task."""

    def __init__(self, queue: InMemoryTaskQueue) -> None:
        self.queue = queue

    async def dispatch(
        self,
        job: ScheduledJob,
        *,
        occurred_at: datetime,
    ) -> BackgroundTask:
        """Queue a task and update the job's execution state."""

        task = await self.queue.enqueue(
            name=job.task_name,
            payload={
                **job.payload,
                "scheduled_job_name": job.name,
                "scheduled_for": occurred_at.isoformat(),
            },
        )
        job.mark_dispatched(occurred_at)
        return task
