from app.services.execution_events import EventStore
from app.services.job_metrics import JobMetrics


class ExecutionReport:
    def __init__(self, events: EventStore, metrics: JobMetrics):
        self.events = events
        self.metrics = metrics

    def build(self) -> dict:
        return {
            "metrics": self.metrics.snapshot(),
            "events": [
                {
                    "event": event.event,
                    "job_id": event.job_id,
                    "timestamp": event.timestamp.isoformat(),
                    "details": event.details,
                }
                for event in self.events.all()
            ],
        }