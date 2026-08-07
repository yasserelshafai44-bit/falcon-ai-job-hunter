from app.services.job_metrics import JobMetrics


def test_job_metrics_records_events():
    metrics = JobMetrics()

    metrics.record("started")
    metrics.record("started")
    metrics.record("completed")

    assert metrics.get("started") == 2
    assert metrics.get("completed") == 1
    assert metrics.snapshot() == {
        "started": 2,
        "completed": 1,
    }