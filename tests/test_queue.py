from app.queue.queue import TaskQueue


def test_queue_is_fifo() -> None:
    queue = TaskQueue()

    queue.enqueue("first")
    queue.enqueue("second")

    assert queue.size() == 2
    assert queue.dequeue() == "first"
    assert queue.dequeue() == "second"
    assert queue.dequeue() is None
    assert queue.is_empty() is True
