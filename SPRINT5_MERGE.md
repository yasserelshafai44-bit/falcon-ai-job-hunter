# Sprint 5 merge steps

After copying this overlay into the existing repository:

## 1. backend/app/api/router.py

Add:

```python
from app.api.routes.jobs import router as jobs_router
```

Then register it:

```python
api_router.include_router(jobs_router)
```

## 2. backend/app/models/__init__.py

Add:

```python
from app.models.discovered_job import DiscoveredJob
```

Add `DiscoveredJob` to `__all__`.

## 3. Run tests

```powershell
pip install -r requirements.txt
pytest
```

## 4. Run migration

```powershell
cd backend
alembic upgrade head
```

## Important

LinkedIn, Indeed, and Bayt are placeholders only. They do not scrape those websites.
Remote OK is the only working provider in this sprint.
