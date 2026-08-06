"""Deterministic scheduled-job polling."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.background import BackgroundTask
from app.jobs.dispatcher import JobDispatcher
from app.jobs.job_registry import JobRegistry


class Scheduler:
    """Find due jobs and dispatch them."""

    def __init__(
        self,
        *,
        registry: JobRegistry,
        dispatcher: JobDispatcher,
    ) -> None:
        self.registry = registry
        self.dispatcher = dispatcher

    async def tick(
        self,
        now: datetime | None = None,
    ) -> list[BackgroundTask]:
        """Dispatch each due job once and return created tasks."""

        current = now or datetime.now(UTC)
        tasks: list[BackgroundTask] = []

        for job in self.registry.due(current):
            tasks.append(
                await self.dispatcher.dispatch(job, occurred_at=current)
            )

        return tasks
