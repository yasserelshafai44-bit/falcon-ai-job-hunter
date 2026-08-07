from typing import Any


class ExecutionPipeline:
    """Coordinates execution of a queued job."""

    def __init__(self, queue_runner):
        self.queue_runner = queue_runner

    async def execute(self, job: Any):
        return await self.queue_runner.run(job)