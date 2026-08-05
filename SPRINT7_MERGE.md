# Sprint 7 merge steps

## 1. Register the router

Edit `backend/app/api/router.py`.

Add:

```python
from app.api.routes.generation import router as generation_router
```

Then add:

```python
api_router.include_router(generation_router)
```

## 2. Export the model

Edit `backend/app/models/__init__.py`.

Add:

```python
from app.models.generated_document import GeneratedDocument
```

Add `GeneratedDocument` to `__all__`.

## 3. Run tests

```powershell
pytest
```

## 4. Apply migration

```powershell
cd backend
alembic upgrade head
```

Sprint 7 deliberately uses a deterministic mock provider. Do not commit real API keys.
