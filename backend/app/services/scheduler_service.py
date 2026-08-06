"""Lifecycle service for periodic scheduler polling."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.jobs.scheduler import Scheduler

SleepFunction = Callable[[float], Awaitable[None]]


class SchedulerService:
    """Run scheduler ticks at a fixed polling interval."""

    def __init__(
        self,
        *,
        scheduler: Scheduler,
        poll_interval_seconds: float = 1.0,
        sleep: SleepFunction = asyncio.sleep,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        self.scheduler = scheduler
        self.poll_interval_seconds = poll_interval_seconds
        self._sleep = sleep
        self._stop_requested = False

    async def run_once(self) -> int:
        """Perform one scheduler tick and return the dispatch count."""

        return len(await self.scheduler.tick())

    async def run(self) -> None:
        """Poll until a graceful stop is requested."""

        self._stop_requested = False
        while not self._stop_requested:
            await self.run_once()
            await self._sleep(self.poll_interval_seconds)

    def request_stop(self) -> None:
        """Request graceful service shutdown."""

        self._stop_requested = True
