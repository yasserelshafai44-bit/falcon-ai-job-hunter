from app.queue.priority import Priority, sort_by_priority


def test_priority_sort_orders_highest_first() -> None:
    tasks = [
        {"id": 1, "priority": Priority.LOW},
        {"id": 2, "priority": Priority.CRITICAL},
        {"id": 3, "priority": Priority.NORMAL},
        {"id": 4, "priority": Priority.HIGH},
    ]

    ordered = sort_by_priority(tasks)

    assert [task["id"] for task in ordered] == [2, 4, 3, 1]
