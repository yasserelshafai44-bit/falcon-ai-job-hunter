from collections import deque


class TaskQueue:
    def __init__(self):
        self._queue = deque()

    def enqueue(self, task):
        self._queue.append(task)

    def dequeue(self):
        if self.is_empty():
            return None
        return self._queue.popleft()

    def is_empty(self):
        return len(self._queue) == 0

    def size(self):
        return len(self._queue)
