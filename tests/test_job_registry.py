from datetime import UTC, datetime, timedelta

import pytest

from app.jobs.cron import IntervalSchedule
from app.jobs.job_registry import JobNotFoundError, JobRegistry, ScheduledJob


def test_registry_returns_due_jobs() -> None:
    now = datetime.now(UTC)
    registry = JobRegistry()
    registry.register(
        ScheduledJob(
            name="sync-jobs",
            task_name="jobs.sync",
            payload={},
            schedule=IntervalSchedule(seconds=60),
            next_run_at=now - timedelta(seconds=1),
        )
    )

    assert [job.name for job in registry.due(now)] == ["sync-jobs"]

    with pytest.raises(JobNotFoundError):
        registry.get("missing")
