"""Background task domain models and retry policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskStatus(StrEnum):
    """Supported task lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Deterministic retry configuration for background tasks."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    multiplier: float = 2.0
    max_delay_seconds: float = 30.0

    def delay_for_attempt(self, attempt: int) -> float:
        """Return the delay before the given retry attempt.

        Args:
            attempt: One-based retry attempt number.

        Returns:
            Delay in seconds, capped by ``max_delay_seconds``.

        Raises:
            ValueError: If ``attempt`` is less than one.
        """

        if attempt < 1:
            raise ValueError("attempt must be at least 1")

        delay = self.base_delay_seconds * (self.multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)


@dataclass(slots=True)
class BackgroundTask:
    """Mutable in-memory representation of a background task."""

    name: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.QUEUED
    progress: int = 0
    attempts: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    cancellation_requested: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def mark_running(self) -> None:
        """Mark the task as running and increment its attempt count."""

        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(UTC)
        self.attempts += 1
        self.error = None

    def update_progress(self, progress: int) -> None:
        """Set task progress between zero and one hundred."""

        self.progress = max(0, min(100, progress))

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        """Mark the task as completed."""

        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.result = result or {}
        self.error = None
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        """Mark the task as failed."""

        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(UTC)

    def request_cancellation(self) -> None:
        """Request cancellation for the task."""

        self.cancellation_requested = True
        if self.status is TaskStatus.QUEUED:
            self.mark_cancelled()

    def mark_cancelled(self) -> None:
        """Mark the task as cancelled."""

        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(UTC)

    @property
    def is_terminal(self) -> bool:
        """Return whether the task has reached a terminal state."""

        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
