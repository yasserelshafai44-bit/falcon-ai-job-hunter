# Required merge edits

After copying this overlay into the repository, make these small edits.

## 1. backend/app/api/router.py

Add:

```python
from app.api.routes.candidate_intelligence import router as candidate_intelligence_router
```

Then add:

```python
api_router.include_router(candidate_intelligence_router)
```

## 2. backend/app/models/__init__.py

Add:

```python
from app.models.candidate_analysis import CandidateAnalysis
```

Include `"CandidateAnalysis"` in `__all__`.

## 3. requirements.txt

Add:

```text
pypdf>=5.1,<6.0
python-docx>=1.1,<2.0
```

## 4. Run

```powershell
pip install -r requirements.txt
pytest
```

For PostgreSQL:

```powershell
cd backend
alembic upgrade head
```
