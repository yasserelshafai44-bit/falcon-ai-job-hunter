from app.services.pipeline_monitor import PipelineMonitor


def test_pipeline_monitor_tracks_execution():
    monitor = PipelineMonitor()

    monitor.started()
    monitor.completed()
    monitor.failed()

    assert monitor.snapshot() == {
        "started": 1,
        "completed": 1,
        "failed": 1,
    }