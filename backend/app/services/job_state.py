from enum import Enum


class JobState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class StateMachine:
    _transitions = {
        JobState.PENDING: {
            JobState.QUEUED,
            JobState.CANCELLED,
        },
        JobState.QUEUED: {
            JobState.RUNNING,
            JobState.CANCELLED,
        },
        JobState.RUNNING: {
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.RETRYING,
        },
        JobState.RETRYING: {
            JobState.QUEUED,
            JobState.FAILED,
        },
        JobState.FAILED: set(),
        JobState.COMPLETED: set(),
        JobState.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, current: JobState, new: JobState) -> bool:
        return new in cls._transitions[current]