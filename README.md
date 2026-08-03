# Falcon AI Job Hunter — Sprint 2 Backend Foundation

This package adds the first working backend foundation for Falcon.

## Included

- FastAPI application
- Environment-based configuration
- Structured JSON logging
- Async SQLAlchemy setup
- PostgreSQL Docker service
- Alembic migration configuration
- Candidate, Job, and Application models
- Health-check and root endpoints
- Async API tests

## Run with Docker

```bash
copy .env.example .env
docker compose up --build
```

Open:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## Run tests locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH="backend"
pytest
```

## Create the first migration

```bash
docker compose run --rm api alembic revision --autogenerate -m "create initial tables"
docker compose run --rm api alembic upgrade head
```
