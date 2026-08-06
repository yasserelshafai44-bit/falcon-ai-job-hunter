"""Tests for background task domain models."""

import pytest

from app.core.background import BackgroundTask, RetryPolicy, TaskStatus


def test_retry_policy_is_deterministic_and_capped() -> None:
    policy = RetryPolicy(
        max_attempts=4,
        base_delay_seconds=2,
        multiplier=2,
        max_delay_seconds=5,
    )

    assert policy.delay_for_attempt(1) == 2
    assert policy.delay_for_attempt(2) == 4
    assert policy.delay_for_attempt(3) == 5

    with pytest.raises(ValueError):
        policy.delay_for_attempt(0)


def test_background_task_tracks_lifecycle() -> None:
    task = BackgroundTask(name="example", payload={"value": 1})

    assert task.status is TaskStatus.QUEUED
    assert task.progress == 0

    task.mark_running()
    task.update_progress(45)
    task.mark_completed({"ok": True})

    assert task.status is TaskStatus.COMPLETED
    assert task.progress == 100
    assert task.result == {"ok": True}
    assert task.attempts == 1
    assert task.is_terminal is True


def test_queued_task_can_be_cancelled() -> None:
    task = BackgroundTask(name="example", payload={})

    task.request_cancellation()

    assert task.status is TaskStatus.CANCELLED
    assert task.cancellation_requested is True
