
from app.services.execution_events import EventStore, ExecutionEvent


def test_event_store_publishes_and_returns_events():
    store = EventStore()
    event = ExecutionEvent(
        event="started",
        job_id="job-1",
        details={"source": "test"},
    )

    store.publish(event)

    events = store.all()

    assert len(events) == 1
    assert events[0].event == "started"
    assert events[0].job_id == "job-1"