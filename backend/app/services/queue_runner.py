from typing import Any


class QueueRunner:
    """Runs a single queued job through an injected worker manager."""

    def __init__(self, worker_manager):
        self.worker_manager = worker_manager

    async def run(self, job: Any):
        return await self.worker_manager.process_task(job)