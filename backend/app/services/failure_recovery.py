from app.services.job_state import JobState


class FailureRecovery:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def recover(self, job, pipeline):
        attempts = 0

        while attempts < self.max_retries:
            attempts += 1
            try:
                result = await pipeline.execute(job)
                return {
                    "state": JobState.COMPLETED,
                    "attempts": attempts,
                    "result": result,
                }
            except Exception:
                if attempts >= self.max_retries:
                    return {
                        "state": JobState.FAILED,
                        "attempts": attempts,
                    }

        return {
            "state": JobState.FAILED,
            "attempts": attempts,
        }