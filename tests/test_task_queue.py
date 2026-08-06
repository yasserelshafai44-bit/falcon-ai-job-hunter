"""Tests for the in-memory task queue."""

import pytest

from app.core.background import TaskStatus
from app.core.task_queue import InMemoryTaskQueue, TaskNotFoundError


@pytest.mark.asyncio
async def test_queue_enqueues_and_dequeues_fifo() -> None:
    queue = InMemoryTaskQueue()

    first = await queue.enqueue(name="first", payload={"index": 1})
    second = await queue.enqueue(name="second", payload={"index": 2})

    assert (await queue.dequeue()).id == first.id
    assert (await queue.dequeue()).id == second.id


@pytest.mark.asyncio
async def test_cancelled_queued_task_is_skipped() -> None:
    queue = InMemoryTaskQueue()

    cancelled = await queue.enqueue(name="cancelled", payload={})
    active = await queue.enqueue(name="active", payload={})
    await queue.cancel(cancelled.id)

    dequeued = await queue.dequeue()

    assert cancelled.status is TaskStatus.CANCELLED
    assert dequeued.id == active.id


@pytest.mark.asyncio
async def test_queue_raises_for_unknown_task() -> None:
    queue = InMemoryTaskQueue()

    with pytest.raises(TaskNotFoundError):
        await queue.get("missing")
