"""Registration and state tracking for scheduled jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.jobs.cron import IntervalSchedule


@dataclass(slots=True)
class ScheduledJob:
    """Definition and runtime state for a recurring job."""

    name: str
    task_name: str
    payload: dict[str, Any]
    schedule: IntervalSchedule
    enabled: bool = True
    next_run_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_run_at: datetime | None = None
    dispatch_count: int = 0

    def mark_dispatched(self, occurred_at: datetime) -> None:
        """Record a dispatch and calculate the next run."""

        self.last_run_at = occurred_at
        self.dispatch_count += 1
        self.next_run_at = self.schedule.next_after(occurred_at)


class JobNotFoundError(KeyError):
    """Raised when a scheduled job does not exist."""


class JobRegistry:
    """In-memory registry of scheduled jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}

    def register(self, job: ScheduledJob) -> None:
        """Register or replace a job by name."""

        self._jobs[job.name] = job

    def get(self, name: str) -> ScheduledJob:
        """Return a registered job."""

        try:
            return self._jobs[name]
        except KeyError as exc:
            raise JobNotFoundError(name) from exc

    def list_jobs(self) -> list[ScheduledJob]:
        """Return jobs sorted by name."""

        return sorted(self._jobs.values(), key=lambda job: job.name)

    def due(self, now: datetime) -> list[ScheduledJob]:
        """Return enabled jobs whose next run time has arrived."""

        return [
            job
            for job in self.list_jobs()
            if job.enabled and job.next_run_at <= now
        ]

    def remove(self, name: str) -> None:
        """Remove a registered job."""

        if name not in self._jobs:
            raise JobNotFoundError(name)
        del self._jobs[name]
