from enum import IntEnum


class Priority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


def sort_by_priority(tasks):
    return sorted(
        tasks,
        key=lambda t: t.get("priority", Priority.NORMAL),
        reverse=True,
    )
