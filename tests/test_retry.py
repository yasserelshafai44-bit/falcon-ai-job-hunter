import pytest

from app.queue.retry import RetryPolicy


def test_retry_policy_limits_attempts_and_delay() -> None:
    policy = RetryPolicy(
        max_attempts=3,
        base_delay_seconds=2,
        multiplier=2,
        max_delay_seconds=5,
    )

    assert policy.should_retry(1) is True
    assert policy.should_retry(2) is True
    assert policy.should_retry(3) is False

    assert policy.delay_for_attempt(1) == 2
    assert policy.delay_for_attempt(2) == 4
    assert policy.delay_for_attempt(3) == 5


def test_retry_policy_rejects_invalid_attempt() -> None:
    policy = RetryPolicy()

    with pytest.raises(ValueError):
        policy.delay_for_attempt(0)
