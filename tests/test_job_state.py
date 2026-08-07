from app.services.job_state import JobState, StateMachine


def test_valid_transitions():
    assert StateMachine.can_transition(JobState.PENDING, JobState.QUEUED)
    assert StateMachine.can_transition(JobState.QUEUED, JobState.RUNNING)
    assert StateMachine.can_transition(JobState.RUNNING, JobState.COMPLETED)


def test_invalid_transition():
    assert not StateMachine.can_transition(JobState.PENDING, JobState.COMPLETED)