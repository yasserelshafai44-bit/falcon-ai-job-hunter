from datetime import UTC, datetime

import pytest

from app.core.task_queue import InMemoryTaskQueue
from app.jobs.cron import IntervalSchedule
from app.jobs.dispatcher import JobDispatcher
from app.jobs.job_registry import ScheduledJob


@pytest.mark.asyncio
async def test_dispatcher_enqueues_and_updates_job() -> None:
    queue = InMemoryTaskQueue()
    dispatcher = JobDispatcher(queue)
    now = datetime.now(UTC)
    job = ScheduledJob(
        name="daily-match",
        task_name="matching.calculate",
        payload={"user_id": 1},
        schedule=IntervalSchedule(seconds=60),
        next_run_at=now,
    )

    task = await dispatcher.dispatch(job, occurred_at=now)

    assert task.name == "matching.calculate"
    assert task.payload["scheduled_job_name"] == "daily-match"
    assert job.dispatch_count == 1
    assert job.next_run_at > now
