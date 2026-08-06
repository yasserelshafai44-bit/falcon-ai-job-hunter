from datetime import UTC, datetime, timedelta

import pytest

from app.core.task_queue import InMemoryTaskQueue
from app.jobs.cron import IntervalSchedule
from app.jobs.dispatcher import JobDispatcher
from app.jobs.job_registry import JobRegistry, ScheduledJob
from app.jobs.scheduler import Scheduler


@pytest.mark.asyncio
async def test_scheduler_dispatches_only_due_jobs() -> None:
    now = datetime.now(UTC)
    registry = JobRegistry()
    registry.register(
        ScheduledJob(
            name="due",
            task_name="jobs.sync",
            payload={},
            schedule=IntervalSchedule(seconds=60),
            next_run_at=now - timedelta(seconds=1),
        )
    )
    registry.register(
        ScheduledJob(
            name="later",
            task_name="jobs.sync",
            payload={},
            schedule=IntervalSchedule(seconds=60),
            next_run_at=now + timedelta(seconds=30),
        )
    )

    scheduler = Scheduler(
        registry=registry,
        dispatcher=JobDispatcher(InMemoryTaskQueue()),
    )

    tasks = await scheduler.tick(now)

    assert len(tasks) == 1
    assert tasks[0].payload["scheduled_job_name"] == "due"
