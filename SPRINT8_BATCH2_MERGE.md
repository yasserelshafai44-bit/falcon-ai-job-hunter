# Sprint 8 Batch 2 merge steps

This batch adds persisted audit events and system health/readiness endpoints.

## Important correction

Authentication already exists from Sprint 3. This batch does **not** duplicate
JWT, password hashing, login, or protected-route logic.

## 1. Register the system router

Edit `backend/app/api/router.py`.

Add:

```python
from app.api.routes.system import router as system_router
```

Then add:

```python
api_router.include_router(system_router)
```

## 2. Export the audit model

Edit `backend/app/models/__init__.py`.

Add:

```python
from app.models.audit_event import AuditEvent
```

Add `AuditEvent` to `__all__`.

## 3. Apply Sprint 8 Batch 1 integration

If you have not already done so, edit `backend/app/main.py` and register:

```python
from app.core.errors import register_exception_handlers
from app.core.middleware import register_middleware
from app.core.observability import configure_logging
```

Then, after app creation:

```python
configure_logging()
register_middleware(app)
register_exception_handlers(app)
```

## 4. Apply migration and run tests

```powershell
cd backend
alembic upgrade head
cd ..
pytest
```

## 5. Future wiring

Use `record_audit_event(...)` in sensitive routes in a later integration pass.
Do not store raw CV text, passwords, tokens, or generated document contents in
audit metadata.
