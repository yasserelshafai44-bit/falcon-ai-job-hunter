from app.services.job_metrics import JobMetrics


class PipelineMonitor:
    def __init__(self) -> None:
        self.metrics = JobMetrics()

    def started(self) -> None:
        self.metrics.record("started")

    def completed(self) -> None:
        self.metrics.record("completed")

    def failed(self) -> None:
        self.metrics.record("failed")

    def snapshot(self) -> dict[str, int]:
        return self.metrics.snapshot()