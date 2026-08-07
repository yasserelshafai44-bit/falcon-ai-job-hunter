from app.services.execution_events import EventStore, ExecutionEvent
from app.services.execution_report import ExecutionReport
from app.services.job_metrics import JobMetrics


def test_execution_report_combines_metrics_and_events():
    events = EventStore()
    metrics = JobMetrics()

    metrics.record("started")
    metrics.record("completed")

    events.publish(
        ExecutionEvent(
            event="completed",
            job_id="job-1",
            details={"result": "ok"},
        )
    )

    report = ExecutionReport(events, metrics).build()

    assert report["metrics"] == {
        "started": 1,
        "completed": 1,
    }
    assert len(report["events"]) == 1
    assert report["events"][0]["job_id"] == "job-1"