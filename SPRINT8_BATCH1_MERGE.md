# Sprint 8 Batch 1 merge steps

This batch adds reusable production infrastructure only. It does not yet persist
audit events or expose system routes; those arrive in Batch 2.

## 1. Register middleware and exception handlers

Edit `backend/app/main.py`.

Add:

```python
from app.core.errors import register_exception_handlers
from app.core.middleware import register_middleware
from app.core.observability import configure_logging
```

After creating the FastAPI app, call:

```python
configure_logging()
register_middleware(app)
register_exception_handlers(app)
```

Call each function only once.

## 2. Rate-limit integration

Do not wire rate limiting into routes yet unless the route already provides the
authenticated user ID. Batch 2 will integrate the correct dependencies.

## 3. Important limitation

`InMemoryRateLimiter` is safe only for a single running application process.
Use Redis or another shared store before scaling to multiple instances.

## 4. Check

Run:

```powershell
pytest
git status
```

Do not commit secrets or raw CV content to logs.
