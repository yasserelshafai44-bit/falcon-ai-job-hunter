# Falcon AI Job Hunter — Coding Standards

**Version:** 1.0  
**Last Updated:** August 2026  
**Status:** Enforced via CI and code review

---

## 1. Purpose

This document defines the coding standards for all contributors to Falcon AI Job Hunter. Consistent standards reduce cognitive load, prevent bugs, and ensure the codebase remains maintainable as the team and feature set grow.

All code submitted via pull request must comply with these standards. Automated tooling (linters, type checkers, test runners) enforces the majority of rules in CI.

---

## 2. Python Style (PEP 8)

### 2.1 General Rules

- Follow [PEP 8](https://peps.python.org/pep-0008/) as the baseline style guide
- Line length: **100 characters** (configured in ruff)
- Indentation: **4 spaces** (no tabs)
- Blank lines: 2 between top-level definitions, 1 between methods
- Imports grouped in order: stdlib → third-party → local; separated by blank lines
- Use absolute imports within the project: `from backend.app.models.user import User`

### 2.2 Formatting Tool

All Python code is formatted with **ruff format** (Black-compatible). Run before every commit:

```bash
ruff format backend/ tests/
ruff check backend/ tests/ --fix
```

### 2.3 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | snake_case | `job_search_service.py` |
| Classes | PascalCase | `JobSearchService` |
| Functions / methods | snake_case | `search_jobs()` |
| Variables | snake_case | `match_score` |
| Constants | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE_MB` |
| Private members | leading underscore | `_parse_response()` |
| Type aliases | PascalCase | `JobListingDict` |
| Enum members | UPPER_SNAKE_CASE | `ApplicationStatus.SUBMITTED` |
| API route functions | snake_case | `get_jobs()` |
| Pydantic models | PascalCase | `JobListingCreate` |
| SQLAlchemy models | PascalCase (singular) | `JobListing` |
| Database tables | snake_case (plural) | `job_listings` |

### 2.4 Import Rules

```python
# Correct
from backend.app.models.job import JobListing
from backend.app.services.matching_service import MatchingService

# Incorrect — relative imports beyond one level
from ...models.job import JobListing

# Incorrect — wildcard imports
from backend.app.models import *
```

### 2.5 String Formatting

Prefer f-strings for interpolation. Use `.format()` or `%` only when f-strings are impractical.

```python
# Correct
message = f"Job {job.title} matched with score {score}"

# Incorrect
message = "Job {} matched with score {}".format(job.title, score)
```

---

## 3. Type Hints

### 3.1 Requirements

- **All** function signatures must include type hints for parameters and return values
- **All** class attributes must be typed
- Use `from __future__ import annotations` at the top of every module for forward references
- Run **mypy** in strict mode; zero errors required for merge

### 3.2 Standards

```python
from __future__ import annotations

from uuid import UUID

from backend.app.models.job import JobListing


async def get_jobs_for_user(
    user_id: UUID,
    *,
    min_score: int = 0,
    page: int = 1,
    per_page: int = 20,
) -> list[JobListing]:
    """Retrieve paginated job listings for a user."""
    ...
```

### 3.3 Type Hint Patterns

| Pattern | Usage |
|---------|-------|
| `UUID` | All database primary/foreign keys |
| `str \| None` | Optional strings (Python 3.12 union syntax) |
| `list[T]` | Lists (not `List[T]` from typing) |
| `dict[str, Any]` | JSON/dynamic data |
| `TypedDict` | Structured dicts passed between layers |
| `Protocol` | Structural typing for interfaces (e.g., LLM client) |
| `Enum` | Fixed sets of values (status, source, document type) |
| `Annotated` | FastAPI dependency injection and validation metadata |

### 3.4 Pydantic Models

Use Pydantic v2 models for all API request/response schemas and settings:

```python
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
```

---

## 4. Docstrings

### 4.1 Format

Use **Google-style docstrings** for all public modules, classes, functions, and methods.

```python
async def compute_match_score(
    profile: UserProfile,
    job: JobListing,
) -> MatchResult:
    """Compute a match score between a user profile and a job listing.

    Uses the Job Matcher agent to analyze skills overlap, experience
    relevance, and preference alignment.

    Args:
        profile: The user's parsed CV profile.
        job: The job listing to match against.

    Returns:
        A MatchResult containing the score (0-100) and explanation.

    Raises:
        AgentExecutionError: If the LLM call fails after retries.
        ValidationError: If profile or job data is incomplete.
    """
```

### 4.2 When Docstrings Are Required

| Element | Docstring Required | Notes |
|---------|-------------------|-------|
| Public modules | Yes | One-line module purpose at top |
| Public classes | Yes | Class purpose + attribute descriptions |
| Public functions/methods | Yes | Args, Returns, Raises |
| Private methods (`_prefix`) | Only if complex | Brief description acceptable |
| Pydantic models | No | Field descriptions via `Field(description=...)` |
| Test functions | No | Test name should be descriptive |
| `__init__.py` | Only if re-exporting | Document public API surface |

### 4.3 Module-Level Docstrings

Every Python module must begin with a one-line docstring:

```python
"""Job search service — orchestrates scraping and deduplication."""
```

---

## 5. Error Handling

### 5.1 Exception Hierarchy

Define project-specific exceptions in `backend/app/core/exceptions.py`:

```python
class FalconError(Exception):
    """Base exception for all application errors."""

class NotFoundError(FalconError):
    """Resource not found."""

class AuthenticationError(FalconError):
    """Authentication failed."""

class AuthorizationError(FalconError):
    """User lacks permission for this action."""

class ValidationError(FalconError):
    """Input validation failed."""

class AgentExecutionError(FalconError):
    """AI agent failed to execute."""

class ExternalServiceError(FalconError):
    """External API or service call failed."""
```

### 5.2 Rules

1. **Never use bare `except:`** — always catch specific exceptions
2. **Never silently swallow exceptions** — log and re-raise or return an error response
3. **Use custom exceptions** at service boundaries; catch and convert to HTTP errors at the API layer
4. **Include context** in error messages (resource ID, operation name)
5. **Log exceptions** with full traceback at ERROR level before returning user-facing errors

### 5.3 API Error Handling Pattern

```python
# In route handler
@router.get("/jobs/{job_id}")
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)

# Global exception handler in main.py
@app.exception_handler(FalconError)
async def falcon_error_handler(request: Request, exc: FalconError):
    logger.error("Application error", exc_info=exc, extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": str(exc)}},
    )
```

### 5.4 External Service Calls

Always wrap external calls (LLM APIs, job boards, email) with retry logic and timeout:

```python
@retry(max_attempts=3, backoff=2.0, exceptions=(ExternalServiceError,))
async def call_llm(prompt: str, timeout: float = 30.0) -> str:
    try:
        response = await llm_client.complete(prompt, timeout=timeout)
        return response
    except TimeoutError:
        raise ExternalServiceError(f"LLM call timed out after {timeout}s")
    except Exception as exc:
        raise ExternalServiceError(f"LLM call failed: {exc}") from exc
```

---

## 6. Logging

### 6.1 Configuration

- Use Python's built-in `logging` module with structured JSON output in production
- Configure in `backend/app/core/logging.py`
- Log level controlled via `LOG_LEVEL` environment variable (default: `INFO`)

### 6.2 Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info (prompt contents, SQL queries) — dev only |
| INFO | Normal operations (request handled, job search completed, user registered) |
| WARNING | Unexpected but handled situations (retry succeeded, stale job listing) |
| ERROR | Failures requiring attention (LLM call failed, DB connection lost) |
| CRITICAL | System-level failures (cannot start, data corruption) |

### 6.3 Structured Logging Format

```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Job search completed",
    extra={
        "user_id": str(user_id),
        "jobs_found": 42,
        "source": "linkedin",
        "duration_ms": 3200,
    },
)
```

Production output (JSON):
```json
{
  "timestamp": "2026-08-03T12:00:00Z",
  "level": "INFO",
  "logger": "backend.app.services.job_search_service",
  "message": "Job search completed",
  "user_id": "abc-123",
  "jobs_found": 42,
  "source": "linkedin",
  "duration_ms": 3200
}
```

### 6.4 Rules

- **Never log secrets** — passwords, tokens, API keys, or full CV content
- **Never log PII at DEBUG in production** — mask email addresses and phone numbers
- **Always include `request_id`** in API-related log entries for tracing
- **Use module-level loggers:** `logger = logging.getLogger(__name__)`
- **Do not use `print()`** anywhere in backend code

---

## 7. Testing Requirements

### 7.1 Test Structure

```
tests/
├── conftest.py              # Shared fixtures (DB, client, test user)
├── unit/
│   ├── test_cv_parser.py
│   ├── test_job_matcher.py
│   ├── test_matching_service.py
│   └── test_auth_service.py
├── integration/
│   ├── test_auth_api.py
│   ├── test_jobs_api.py
│   └── test_documents_api.py
└── e2e/
    └── test_application_flow.py
```

### 7.2 Coverage Requirements

| Scope | Minimum Coverage |
|-------|-----------------|
| Services | 90% |
| Agents | 85% |
| API routes | 80% |
| Models / schemas | 70% |
| **Overall backend** | **80%** |

Coverage measured via `pytest-cov`. CI fails if overall coverage drops below 80%.

### 7.3 Test Naming Convention

```python
def test_<function>_<scenario>_<expected_outcome>():
    ...
```

Examples:
```python
def test_compute_match_score_with_matching_skills_returns_high_score():
    ...

def test_register_with_duplicate_email_returns_409():
    ...

def test_cv_parser_with_pdf_returns_structured_profile():
    ...
```

### 7.4 Test Patterns

**Unit tests** — mock external dependencies:
```python
@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=LLMClient)
    client.complete.return_value = '{"score": 85, "explanation": "Strong match"}'
    return client

async def test_job_matcher_returns_score(mock_llm_client):
    agent = JobMatcherAgent(llm_client=mock_llm_client)
    result = await agent.execute(profile=sample_profile, job=sample_job)
    assert result.score == 85
```

**Integration tests** — use test database:
```python
async def test_create_job_listing(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/v1/jobs/search", headers=auth_headers)
    assert response.status_code == 202
```

### 7.5 Test Rules

1. Every service method must have at least one unit test
2. Every API endpoint must have at least one integration test (happy path + error case)
3. Tests must be independent — no shared mutable state between tests
4. Use fixtures for common setup; never rely on test execution order
5. Mock all external services (LLM APIs, job boards, email) in unit tests
6. Integration tests use a dedicated test database (never production)
7. No `@pytest.mark.skip` without a linked issue/ticket explaining why

---

## 8. Git Workflow

### 8.1 Branch Strategy

```
main          ← production-ready code
  └── develop ← integration branch (optional, for larger teams)
       ├── feature/m2-auth-api
       ├── feature/m4-cv-parser
       └── fix/job-dedup-logic
```

For solo/small team development, feature branches merge directly into `main` via pull request.

### 8.2 Branch Naming

```
feature/<milestone>-<short-description>   # New features
fix/<short-description>                   # Bug fixes
docs/<short-description>                  # Documentation only
refactor/<short-description>              # Code refactoring
test/<short-description>                  # Test additions/fixes
```

Examples:
- `feature/m2-auth-api`
- `feature/m5-linkedin-scraper`
- `fix/match-score-overflow`
- `docs/api-endpoint-spec`

### 8.3 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code refactoring (no behavior change) |
| `test` | Adding or updating tests |
| `chore` | Build, CI, dependency updates |
| `perf` | Performance improvement |

Examples:
```
feat(auth): add JWT refresh token endpoint
fix(jobs): deduplicate listings across LinkedIn and Indeed
test(matching): add unit tests for score calculation edge cases
docs(architecture): add browser automation flow diagram
```

### 8.4 Pull Request Process

1. Create feature branch from `main`
2. Implement changes following all coding standards
3. Run locally: `ruff format`, `ruff check`, `mypy`, `pytest`
4. Push branch and open PR with:
   - Clear title (conventional commit format)
   - Description: what changed, why, how to test
   - Link to relevant milestone/issue
5. CI must pass (lint, type check, tests, coverage)
6. Self-review or peer review before merge
7. Squash merge into `main`

### 8.5 What Not to Commit

- `.env` files (secrets)
- `__pycache__/`, `.venv/`, `*.pyc`
- IDE settings (`.idea/`, `.vscode/` — except shared extensions.json)
- Generated files (coverage reports, build artifacts)
- Large binary files (use Git LFS if necessary)

---

## 9. Naming Conventions (Cross-Cutting)

### 9.1 API Endpoints

- Plural nouns for resources: `/jobs`, `/applications`, `/documents`
- Nested for sub-resources: `/jobs/{id}/matches`
- Actions as sub-paths: `/applications/{id}/submit`
- Lowercase with hyphens: `/cover-letter` (not `/coverLetter` or `/cover_letter`)

### 9.2 Database

| Element | Convention | Example |
|---------|-----------|---------|
| Tables | snake_case, plural | `job_listings` |
| Columns | snake_case | `match_score`, `created_at` |
| Foreign keys | `{table_singular}_id` | `user_id`, `job_listing_id` |
| Indexes | `ix_{table}_{column}` | `ix_job_listings_source` |
| Constraints | `{type}_{table}_{column}` | `uq_users_email` |
| Enums (DB) | snake_case type name | `application_status` |

### 9.3 Environment Variables

- UPPER_SNAKE_CASE
- Grouped by prefix: `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY`
- Defined in `core/config.py` via pydantic-settings

### 9.4 Files and Directories

- Python modules: `snake_case.py`
- Test files: `test_<module_name>.py`
- Prompt templates: `<agent_name>_v<version>.jinja2`
- Docker files: `Dockerfile.<service>`
- Scripts: `snake_case.sh` or `snake_case.py`

---

## 10. Security Practices

### 10.1 Input Validation

- All API inputs validated through Pydantic models — never trust raw request data
- File uploads: validate MIME type, size limit (10 MB), and scan for malicious content
- SQL injection prevented by SQLAlchemy parameterized queries — never use raw SQL with string interpolation
- XSS prevented by returning JSON (not HTML) and sanitizing any user-generated content displayed in frontend

### 10.2 Authentication & Authorization

- Passwords hashed with bcrypt (cost ≥ 12) — never store plain text
- JWT tokens signed with HS256 and a 256-bit secret
- Access tokens expire in 15 minutes; refresh tokens in 7 days
- Every authenticated endpoint verifies token and extracts `user_id`
- Authorization checks: users can only access their own resources (enforce at service layer)

### 10.3 Secrets Management

- All secrets in environment variables — never hardcoded
- `.env` file gitignored; `.env.example` contains placeholder values only
- LLM API keys, database passwords, and JWT secrets rotated periodically
- Docker secrets or cloud secret manager for production

### 10.4 Data Protection

- CV files stored with user-scoped paths: `uploads/{user_id}/{filename}`
- Generated documents accessible only by owning user
- Audit log for all application submissions
- Data retention policy: user data deleted within 30 days of account deletion request

### 10.5 Dependency Security

- Pin dependency versions in `requirements.txt`
- Run `pip audit` or `safety check` in CI
- Review dependency updates before merging Dependabot PRs
- No dependencies with known critical CVEs

---

## 11. Performance Guidelines

### 11.1 Database

- Use async SQLAlchemy sessions for all DB operations
- Index all foreign keys and frequently filtered columns
- Paginate all list endpoints (default 20, max 100)
- Use `selectinload` or `joinedload` to avoid N+1 queries
- Cache expensive read queries in Redis (job search results, match scores)

### 11.2 API

- Response time target: p95 < 200 ms for read endpoints
- Use background tasks (Celery) for long-running operations (CV parsing, job search, document generation)
- Return `202 Accepted` with task ID for async operations; client polls for result
- Compress responses with gzip for payloads > 1 KB

### 11.3 AI / LLM Calls

- Cache LLM responses in Redis keyed by prompt hash (24-hour TTL)
- Use cheaper models (GPT-4o-mini) for matching; reserve GPT-4o for document generation
- Set token limits on all LLM calls to control cost
- Batch matching requests where possible
- Track token usage per user for quota enforcement

### 11.4 File Handling

- Stream large file uploads — do not load entire file into memory
- Generate PDFs asynchronously via background task
- Store files on disk (dev) or S3-compatible storage (production)

### 11.5 General

- Profile before optimizing — use `py-spy` or logging timestamps to identify bottlenecks
- Avoid premature optimization; optimize hot paths identified by metrics
- Load test critical endpoints before milestone completion (locust or k6)

---

## Appendix A: Tooling Configuration

### ruff (pyproject.toml or ruff.toml)

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM", "TCH"]

[tool.ruff.lint.isort]
known-first-party = ["backend"]
```

### mypy

```toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
```

### pytest

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=backend --cov-report=term-missing --cov-fail-under=80"
```

## Appendix B: Code Review Checklist

- [ ] Follows PEP 8 and passes ruff lint + format
- [ ] All functions have type hints; mypy passes
- [ ] Public functions have Google-style docstrings
- [ ] Error handling uses custom exceptions; no bare except
- [ ] No secrets, PII, or debug print statements
- [ ] Tests added/updated; coverage maintained
- [ ] API changes documented in docstrings and reflected in OpenAPI
- [ ] Database changes include Alembic migration
- [ ] No unnecessary dependencies added
- [ ] Performance-sensitive paths considered (N+1, caching, async)
