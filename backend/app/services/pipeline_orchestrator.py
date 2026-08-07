from app.services.job_state import JobState, StateMachine


class PipelineOrchestrator:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    async def execute(self, job):
        state = JobState.PENDING

        if not StateMachine.can_transition(state, JobState.QUEUED):
            raise RuntimeError("Invalid transition to queued")
        state = JobState.QUEUED

        if not StateMachine.can_transition(state, JobState.RUNNING):
            raise RuntimeError("Invalid transition to running")
        state = JobState.RUNNING

        try:
            result = await self.pipeline.execute(job)
        except Exception:
            if StateMachine.can_transition(state, JobState.FAILED):
                state = JobState.FAILED
            raise

        if not StateMachine.can_transition(state, JobState.COMPLETED):
            raise RuntimeError("Invalid transition to completed")

        state = JobState.COMPLETED

        return {
            "state": state,
            "result": result,
        }