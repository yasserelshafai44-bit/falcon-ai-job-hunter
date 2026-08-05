# Falcon AI Job Hunter — Production Deployment

## Required safeguards

- HTTPS must terminate at a trusted reverse proxy or load balancer.
- Production secrets must come from a secret manager or deployment environment.
- Never commit `.env`, API keys, database passwords, tokens, or user documents.
- PostgreSQL backups must be automated and restore-tested.
- Apply Alembic migrations before starting a new release.
- Run one process only while using the in-memory rate limiter.
- Replace the in-memory limiter with Redis before horizontal scaling.

## Release sequence

1. Build an immutable container image.
2. Run the automated test suite.
3. Back up the production database.
4. Apply migrations with `alembic upgrade head`.
5. Deploy the new image.
6. Verify `/health`.
7. Verify `/ready`.
8. Check structured logs for errors.
9. Roll back the image if readiness remains degraded.

## Startup

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

## Reverse proxy expectations

The proxy should:

- enforce HTTPS
- set `X-Forwarded-For`
- set `X-Forwarded-Proto`
- reject oversized request bodies
- apply request timeouts
- preserve `X-Request-ID` where present

Only trust forwarded headers from known proxies.

## Health checks

- Liveness: `GET /health`
- Readiness: `GET /ready`

Do not route production traffic to instances reporting a degraded readiness state.

## Logs

- Write structured logs to stdout.
- Do not log authorization headers, passwords, tokens, CV text, or generated documents.
- Define retention and access controls.
- Alert on elevated 5xx errors, provider failures, and repeated readiness failures.

## Backups

- Perform encrypted PostgreSQL backups.
- Store backups separately from the primary database.
- Test restores on a schedule.
- Document recovery-point and recovery-time objectives.

## Rollback

Application rollback:

1. Restore the previous image.
2. Confirm `/health` and `/ready`.
3. Review migration compatibility.

Database rollback should be exceptional. Prefer forward-fix migrations because destructive
downgrades can lose user data.
