from collections import Counter


class JobMetrics:
    def __init__(self) -> None:
        self._counter = Counter()

    def record(self, event: str) -> None:
        self._counter[event] += 1

    def get(self, event: str) -> int:
        return self._counter[event]

    def snapshot(self) -> dict[str, int]:
        return dict(self._counter)

    def reset(self) -> None:
        self._counter.clear()