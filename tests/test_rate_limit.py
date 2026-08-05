import pytest
from fastapi import HTTPException

from app.core.rate_limit import InMemoryRateLimiter, RateLimitRule


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter()
    rule = RateLimitRule(requests=2, window_seconds=60)

    await limiter.check(key="test", rule=rule)
    await limiter.check(key="test", rule=rule)

    with pytest.raises(HTTPException) as exc_info:
        await limiter.check(key="test", rule=rule)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers
    assert "Retry-After" in exc_info.value.headers
