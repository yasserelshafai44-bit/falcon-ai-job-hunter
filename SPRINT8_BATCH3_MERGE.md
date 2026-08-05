# Sprint 8 Batch 3 merge steps

Batch 3 completes the production-readiness layer.

## 1. Bootstrap production safeguards

Edit `backend/app/main.py`.

Add:

```python
from app.core.production import configure_production_app
```

Immediately after creating the FastAPI application, add:

```python
configure_production_app(app)
```

Do not also call `configure_logging`, `register_middleware`, or
`register_exception_handlers` individually. Use one approach only, otherwise middleware
and handlers may be registered twice.

## 2. Register system routes

Edit `backend/app/api/router.py`.

Add:

```python
from app.api.routes.system import router as system_router
```

Then add:

```python
api_router.include_router(system_router)
```

Do not register it twice if Batch 2 was already manually integrated.

## 3. Export the AuditEvent model

Edit `backend/app/models/__init__.py`.

Add:

```python
from app.models.audit_event import AuditEvent
```

Add `AuditEvent` to `__all__`.

## 4. Optional audit wiring

Use `audit_from_request(...)` after successful sensitive operations such as CV upload,
candidate analysis, job sync, matching, and document generation.

Do not record raw CV text, generated document content, passwords, or tokens.

## 5. Run checks

```powershell
pytest
cd backend
alembic upgrade head
cd ..
git status
```

## 6. Important limitation

The current rate limiter is in-memory and process-local. Do not run multiple workers or
multiple application instances until the limiter is replaced with a shared store such as
Redis.
