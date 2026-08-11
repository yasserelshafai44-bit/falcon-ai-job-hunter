# Sprint 10 Merge

The installer can patch the router and model exports automatically.

Manual equivalent:

## backend/app/api/router.py

Add:

```python
from app.api.routes.applications import router as applications_router
```

Then:

```python
api_router.include_router(applications_router)
```

## backend/app/models/__init__.py

Add:

```python
from app.models.application_workflow import ApplicationWorkflow
```

Add `"ApplicationWorkflow"` to `__all__`.

## Test

```powershell
$env:PYTHONPATH="$PWD\backend"
python -m pytest --noconftest tests/test_application_workflow.py tests/test_application_routes.py
```

## Migration

```powershell
cd backend
alembic upgrade head
```
