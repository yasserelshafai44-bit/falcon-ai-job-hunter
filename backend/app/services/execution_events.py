from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutionEvent:
    event: str
    job_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict | None = None


class EventStore:
    def __init__(self) -> None:
        self._events: list[ExecutionEvent] = []

    def publish(self, event: ExecutionEvent) -> None:
        self._events.append(event)

    def all(self) -> list[ExecutionEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()