from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic
from typing import Deque

from fastapi import HTTPException, Request, status


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    requests: int
    window_seconds: int


class InMemoryRateLimiter:
    """Single-process limiter suitable for development and one-instance deployments.

    Replace with Redis before running multiple application instances.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, *, key: str, rule: RateLimitRule) -> int:
        now = monotonic()
        cutoff = now - rule.window_seconds

        async with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= rule.requests:
                retry_after = max(1, int(rule.window_seconds - (now - bucket[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)
            return max(0, rule.requests - len(bucket))


rate_limiter = InMemoryRateLimiter()

PUBLIC_RULE = RateLimitRule(requests=120, window_seconds=60)
AUTHENTICATED_RULE = RateLimitRule(requests=240, window_seconds=60)
AI_GENERATION_RULE = RateLimitRule(requests=10, window_seconds=60)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def enforce_public_rate_limit(request: Request) -> None:
    await rate_limiter.check(
        key=f"public:{client_ip(request)}",
        rule=PUBLIC_RULE,
    )


async def enforce_authenticated_rate_limit(
    request: Request,
    user_id: int,
) -> None:
    await rate_limiter.check(
        key=f"user:{user_id}",
        rule=AUTHENTICATED_RULE,
    )


async def enforce_ai_generation_rate_limit(
    request: Request,
    user_id: int,
) -> None:
    await rate_limiter.check(
        key=f"ai:{user_id}",
        rule=AI_GENERATION_RULE,
    )
