# Falcon AI Job Hunter — System Architecture

**Version:** 1.0  
**Last Updated:** August 2026  
**Status:** Approved for implementation

---

## 1. Architecture Overview

Falcon AI Job Hunter follows a **modular monolith** architecture with clear internal boundaries, designed to evolve into microservices as scale demands. The system comprises a FastAPI backend, a React frontend, PostgreSQL database, Redis task queue, AI agent modules, and browser automation workers — all orchestrated via Docker Compose.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    React Frontend (SPA)                          │   │
│  │  Dashboard │ Job List │ CV Editor │ Preferences │ Analytics    │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │ HTTPS / REST API
┌─────────────────────────────▼───────────────────────────────────────────┐
│                         API Gateway Layer                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              FastAPI Application (backend/app/main.py)           │   │
│  │  Auth Middleware │ Rate Limiter │ CORS │ Request Validation      │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────┐
│                        Application Layer                                │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Auth      │  │  Job Search │  │  Matching   │  │  Document   │   │
│  │  Service    │  │  Service    │  │  Service    │  │  Service    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│  ┌──────▼────────────────▼────────────────▼────────────────▼──────┐   │
│  │                     AI Agent Layer                               │   │
│  │  CV Parser │ Job Matcher │ CV Tailor │ Cover Letter │ Research  │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│  ┌──────────────────────────▼───────────────────────────────────────┐ │
│  │              Browser Automation Worker                             │ │
│  │  Playwright │ Form Filler │ CAPTCHA Handler │ Screenshot Logger  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────────┐
│                        Infrastructure Layer                               │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │  PostgreSQL  │  │    Redis     │  │  File Store  │  │  LLM APIs  ││
│  │  (Primary DB)│  │ (Queue/Cache)│  │  (CVs/PDFs)  │  │ OpenAI/etc ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Backend (FastAPI)

### 2.1 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Runtime | Python | 3.12 |
| Framework | FastAPI | ≥ 0.115 |
| ASGI Server | Uvicorn | ≥ 0.32 |
| Validation | Pydantic v2 | ≥ 2.9 |
| Settings | pydantic-settings | ≥ 2.6 |
| ORM | SQLAlchemy 2.0 | ≥ 2.0.36 |
| DB Driver | asyncpg | ≥ 0.30 |
| Migrations | Alembic | TBD |
| Task Queue | Celery + Redis | TBD |
| HTTP Client | httpx | ≥ 0.27 |
| Testing | pytest + pytest-asyncio | ≥ 8.3 |

### 2.2 Application Structure

```
backend/app/
├── main.py                 # FastAPI app factory, middleware, lifespan
├── api/
│   ├── __init__.py
│   ├── deps.py             # Dependency injection (DB session, current user)
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py       # Aggregates all v1 routes
│   │   ├── auth.py         # /api/v1/auth/*
│   │   ├── users.py        # /api/v1/users/*
│   │   ├── profiles.py     # /api/v1/profiles/*
│   │   ├── jobs.py         # /api/v1/jobs/*
│   │   ├── applications.py # /api/v1/applications/*
│   │   ├── documents.py    # /api/v1/documents/*
│   │   └── analytics.py    # /api/v1/analytics/*
│   └── health.py           # /health, /ready
├── core/
│   ├── config.py           # Settings from environment
│   ├── security.py         # JWT, password hashing
│   └── logging.py          # Structured logging setup
├── database/
│   ├── session.py          # Async engine and session factory
│   └── base.py             # Declarative base, mixins
├── models/
│   ├── user.py             # User, UserProfile ORM models
│   ├── job.py              # JobListing, JobMatch ORM models
│   ├── application.py      # Application, ApplicationStatus ORM models
│   └── document.py         # CV, CoverLetter ORM models
├── services/
│   ├── auth_service.py
│   ├── job_search_service.py
│   ├── matching_service.py
│   ├── document_service.py
│   └── application_service.py
├── agents/
│   ├── cv_parser.py        # CV parsing agent
│   ├── job_matcher.py      # Job matching agent
│   ├── cv_tailor.py        # CV tailoring agent
│   ├── cover_letter.py     # Cover letter agent
│   └── base.py             # Base agent class with LLM client
└── utils/
    ├── pdf.py              # PDF generation/parsing utilities
    ├── text.py             # Text processing helpers
    └── retry.py            # Retry decorators for external calls
```

### 2.3 Key Design Decisions

- **Async-first:** All database and HTTP operations use `async/await` for concurrency
- **Dependency injection:** FastAPI `Depends()` for DB sessions, auth, and service instances
- **Versioned API:** All routes under `/api/v1/` for future backward compatibility
- **Service layer:** Business logic lives in `services/`, not in route handlers
- **Agent isolation:** AI agents are independent modules with a common base class and LLM client abstraction

### 2.4 Middleware Stack

```
Request → CORS → Rate Limiter → Auth (JWT) → Route Handler → Response
```

| Middleware | Purpose |
|-----------|---------|
| CORS | Allow frontend origin; configurable via settings |
| Rate Limiter | Token bucket per IP/user; stricter on auth endpoints |
| Auth | Extract and validate JWT from Authorization header |
| Request ID | Inject `X-Request-ID` for distributed tracing |
| Error Handler | Catch exceptions; return consistent JSON error responses |

---

## 3. Frontend

### 3.1 Technology Stack (Planned)

| Component | Technology |
|-----------|-----------|
| Framework | React 18+ with TypeScript |
| Build Tool | Vite |
| State Management | TanStack Query (server state) + Zustand (client state) |
| Routing | React Router v6 |
| UI Components | shadcn/ui + Tailwind CSS |
| Forms | React Hook Form + Zod validation |
| HTTP Client | Axios or fetch wrapper with interceptors |
| Charts | Recharts (analytics dashboard) |

### 3.2 Page Structure

```
frontend/src/
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Dashboard.tsx          # Overview, pipeline summary
│   ├── Jobs.tsx               # Job listings with match scores
│   ├── JobDetail.tsx          # Single job + generate materials
│   ├── Profile.tsx            # CV upload, parsed profile edit
│   ├── Preferences.tsx        # Job search preferences
│   ├── Applications.tsx       # Application pipeline (kanban/list)
│   ├── Documents.tsx          # CV/cover letter management
│   └── Analytics.tsx          # Funnel, response rates, trends
├── components/
│   ├── layout/                # Header, Sidebar, Footer
│   ├── jobs/                  # JobCard, MatchScore, JobFilters
│   ├── documents/             # CVEditor, CoverLetterEditor, DiffView
│   └── common/                # Button, Modal, Toast, Loading
├── hooks/                     # useAuth, useJobs, useApplications
├── services/                  # API client functions
├── types/                     # TypeScript interfaces matching API schemas
└── utils/                     # Formatters, constants
```

### 3.3 Frontend–Backend Communication

- All API calls go through a centralized API client with JWT token injection
- Token refresh handled transparently via Axios interceptors
- TanStack Query manages caching, refetching, and optimistic updates
- WebSocket connection (future) for real-time automation status updates

---

## 4. Database

### 4.1 PostgreSQL Schema (Core Entities)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    users     │────<│ user_profiles│     │  preferences │
│──────────────│     │──────────────│     │──────────────│
│ id (PK)      │     │ id (PK)      │     │ id (PK)      │
│ email        │     │ user_id (FK) │     │ user_id (FK) │
│ password_hash│     │ parsed_data  │     │ roles[]      │
│ is_active    │     │ raw_cv_path  │     │ locations[]  │
│ created_at   │     │ version      │     │ remote_ok    │
└──────┬───────┘     └──────────────┘     │ salary_min   │
       │                                   │ salary_max   │
       │                                   │ exclusions[] │
       │                                   └──────────────┘
       │
       │     ┌──────────────┐     ┌──────────────┐
       ├────<│  job_matches │>────│ job_listings │
       │     │──────────────│     │──────────────│
       │     │ id (PK)      │     │ id (PK)      │
       │     │ user_id (FK) │     │ external_id  │
       │     │ job_id (FK)  │     │ source       │
       │     │ score        │     │ title        │
       │     │ explanation  │     │ company      │
       │     │ status       │     │ location     │
       │     └──────┬───────┘     │ salary_range │
       │            │             │ description  │
       │            │             │ url          │
       │     ┌──────▼───────┐     │ posted_at    │
       │     │ applications │     │ scraped_at   │
       │     │──────────────│     └──────────────┘
       │     │ id (PK)      │
       │     │ user_id (FK) │
       │     │ job_match_id │
       │     │ status       │
       │     │ submitted_at │
       │     └──────┬───────┘
       │            │
       │     ┌──────▼───────┐
       └────<│  documents   │
             │──────────────│
             │ id (PK)      │
             │ user_id (FK) │
             │ app_id (FK)  │
             │ type (cv/cl) │
             │ content      │
             │ file_path    │
             │ is_tailored  │
             └──────────────┘
```

### 4.2 Database Conventions

- All tables use UUID primary keys (`gen_random_uuid()`)
- Timestamps: `created_at`, `updated_at` on every table (auto-managed)
- Soft deletes via `deleted_at` column where applicable
- JSONB columns for flexible structured data (parsed CV, match explanation)
- Indexes on foreign keys, frequently queried columns (email, source+external_id, user_id+status)
- Alembic for version-controlled schema migrations

### 4.3 Redis Usage

| Purpose | Key Pattern | TTL |
|---------|------------|-----|
| Task queue (Celery broker) | celery:* | — |
| Session cache | session:{user_id} | 15 min |
| Rate limiting | ratelimit:{ip}:{endpoint} | 1 min |
| Job search results cache | search:{user_id}:{hash} | 1 hour |
| LLM response cache | llm:{prompt_hash} | 24 hours |

---

## 5. AI Agents

### 5.1 Agent Architecture

Each agent follows a common pattern:

```python
class BaseAgent:
    """Base class for all AI agents."""

    def __init__(self, llm_client: LLMClient, config: AgentConfig):
        self.llm = llm_client
        self.config = config

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        prompt = self.build_prompt(input_data)
        response = await self.llm.complete(prompt, **self.config.llm_params)
        return self.parse_response(response)

    def build_prompt(self, input_data: AgentInput) -> str: ...
    def parse_response(self, raw: str) -> AgentOutput: ...
```

### 5.2 Agent Inventory

| Agent | Module | Input | Output | LLM Model |
|-------|--------|-------|--------|-----------|
| CV Parser | `agents/cv_parser.py` | Raw CV text/file | Structured profile JSON | GPT-4o / Claude |
| Job Matcher | `agents/job_matcher.py` | User profile + job listing | Score (0–100) + explanation | GPT-4o-mini |
| CV Tailor | `agents/cv_tailor.py` | Master profile + job description | Tailored CV text | GPT-4o |
| Cover Letter | `agents/cover_letter.py` | Profile + job + company info | Cover letter text | GPT-4o |
| Company Research | `agents/research.py` | Company name | Summary, recent news | GPT-4o-mini + web search |

### 5.3 LLM Client Abstraction

```
┌─────────────────────────────────┐
│         LLMClient (ABC)         │
│  complete(prompt, **kwargs)    │
│  complete_structured(prompt,   │
│    schema, **kwargs)           │
└──────────┬──────────────────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌───▼─────┐
│ OpenAI  │ │Anthropic│
│ Client  │ │ Client  │
└─────────┘ └─────────┘
```

- Provider selected via `LLM_PROVIDER` environment variable
- Structured output via Pydantic schema enforcement (JSON mode)
- Token usage tracked per request for cost monitoring
- Response caching in Redis to avoid redundant LLM calls

### 5.4 Prompt Management

- Prompts stored as Jinja2 templates in `backend/app/agents/prompts/`
- Versioned filenames: `cv_parser_v1.jinja2`, `job_matcher_v1.jinja2`
- Prompt variables validated against typed input schemas
- System prompts include safety guardrails (no fabrication, factual accuracy)

---

## 6. Browser Automation

### 6.1 Technology

| Component | Technology |
|-----------|-----------|
| Browser Engine | Playwright (Chromium) |
| Execution | Celery worker (separate container) |
| CAPTCHA | Pause + notify user; manual intervention |
| Logging | Screenshot on every step; stored in file system |

### 6.2 Automation Flow

```
User approves application
        │
        ▼
┌───────────────────┐
│  Queue Task       │  Celery: apply_to_job(application_id)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Launch Browser   │  Headless Chromium via Playwright
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Navigate to URL  │  Job application page
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Detect Form      │  Identify fields via selectors + heuristics
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Fill Fields      │  Name, email, phone, experience, etc.
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Upload Documents │  Attach tailored CV + cover letter
└────────┬──────────┘
         │
         ▼
┌───────────────────┐     ┌──────────────────┐
│  CAPTCHA?         │────>│  Pause + Notify  │
└────────┬──────────┘     │  User completes  │
         │ No             └──────────────────┘
         ▼
┌───────────────────┐
│  Submit Form      │  Click submit; verify confirmation
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Update Status    │  application.status = "submitted"
│  + Screenshot     │  Store confirmation screenshot
└───────────────────┘
```

### 6.3 Supported Platforms (Planned)

| Platform | Apply Method | Priority |
|----------|-------------|----------|
| LinkedIn | Easy Apply | P0 (MVP automation) |
| Indeed | Quick Apply | P0 |
| Greenhouse | Standard form | P1 |
| Lever | Standard form | P1 |
| Workday | Complex multi-step | P2 |

### 6.4 Safety Controls

- Automation runs only after explicit user approval (stored approval record with timestamp)
- Maximum 10 automated submissions per user per day
- Randomized delays between actions (1–3 seconds) to mimic human behavior
- User-agent rotation and proxy support (future)
- Full audit trail: screenshots, field values, timestamps

---

## 7. Docker

### 7.1 Container Architecture

```yaml
services:
  backend:       # FastAPI application
  worker:        # Celery worker (job search, AI tasks, automation)
  scheduler:     # Celery Beat (cron-like task scheduling)
  db:            # PostgreSQL 16
  redis:         # Redis 7 (broker + cache)
  frontend:      # React app (nginx serving static build)
```

### 7.2 Dockerfile Strategy

| Container | Base Image | Notes |
|-----------|-----------|-------|
| backend | python:3.12-slim | Multi-stage; non-root user |
| worker | python:3.12-slim + Playwright | Includes Chromium dependencies |
| frontend | node:20-alpine → nginx:alpine | Build stage + serve stage |
| db | postgres:16-alpine | Persistent volume |
| redis | redis:7-alpine | No persistence needed for cache |

### 7.3 Environment Configuration

- All secrets via `.env` file (never committed)
- `.env.example` documents all required variables
- Docker Compose overrides for dev (`docker-compose.override.yml`, gitignored)
- Production deployment via `docker-compose.prod.yml` with resource limits

### 7.4 Networking

```
┌──────────── docker network: falcon-net ────────────┐
│                                                     │
│  frontend:80 ──> backend:8000                      │
│  backend:8000 ──> db:5432                          │
│  backend:8000 ──> redis:6379                       │
│  worker ──> db:5432, redis:6379, external APIs    │
│                                                     │
│  Exposed ports (dev):                               │
│    frontend: 3000                                   │
│    backend:  8000                                   │
│    db:       5432                                   │
│    redis:    6379                                   │
└─────────────────────────────────────────────────────┘
```

---

## 8. Authentication

### 8.1 Flow

```
Registration:
  Client → POST /api/v1/auth/register {email, password}
       → Validate → Hash password → Store user → Return tokens

Login:
  Client → POST /api/v1/auth/login {email, password}
       → Verify hash → Issue JWT access + refresh tokens

Authenticated Request:
  Client → GET /api/v1/jobs  (Authorization: Bearer <access_token>)
       → Middleware validates JWT → Extract user_id → Route handler

Token Refresh:
  Client → POST /api/v1/auth/refresh {refresh_token}
       → Validate refresh token → Issue new access token
```

### 8.2 Token Structure

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Access Token Claims:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1234567890,
  "type": "access"
}
```

### 8.3 Security Measures

| Measure | Implementation |
|---------|---------------|
| Password hashing | bcrypt, cost factor 12 |
| Token signing | HS256 with `SECRET_KEY` (256-bit) |
| Token storage (client) | Access token in memory; refresh token in httpOnly cookie |
| Brute force protection | Rate limit: 5 login attempts/minute/IP |
| CORS | Whitelist frontend origin only |
| CSRF | SameSite cookie attribute + CSRF token for state-changing requests |

---

## 9. API Structure

### 9.1 Endpoint Map

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **Auth** | | | |
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh token |
| POST | `/api/v1/auth/logout` | Invalidate refresh token | Yes |
| **Users** | | | |
| GET | `/api/v1/users/me` | Get current user profile | Yes |
| PUT | `/api/v1/users/me` | Update user profile | Yes |
| **Profiles** | | | |
| POST | `/api/v1/profiles/cv` | Upload CV | Yes |
| GET | `/api/v1/profiles/cv` | Get parsed profile | Yes |
| PUT | `/api/v1/profiles/cv` | Update parsed profile | Yes |
| GET | `/api/v1/profiles/cv/versions` | List CV versions | Yes |
| **Preferences** | | | |
| GET | `/api/v1/preferences` | Get job preferences | Yes |
| PUT | `/api/v1/preferences` | Update preferences | Yes |
| **Jobs** | | | |
| GET | `/api/v1/jobs` | List matched jobs (paginated, filterable) | Yes |
| GET | `/api/v1/jobs/{id}` | Get job detail with match info | Yes |
| POST | `/api/v1/jobs/search` | Trigger manual job search | Yes |
| **Applications** | | | |
| GET | `/api/v1/applications` | List applications by status | Yes |
| POST | `/api/v1/applications` | Create application for a job | Yes |
| PUT | `/api/v1/applications/{id}` | Update application status | Yes |
| POST | `/api/v1/applications/{id}/submit` | Approve and submit application | Yes |
| **Documents** | | | |
| POST | `/api/v1/documents/cv/tailor` | Generate tailored CV | Yes |
| POST | `/api/v1/documents/cover-letter` | Generate cover letter | Yes |
| GET | `/api/v1/documents/{id}` | Get document content | Yes |
| GET | `/api/v1/documents/{id}/pdf` | Download document as PDF | Yes |
| **Analytics** | | | |
| GET | `/api/v1/analytics/funnel` | Application funnel metrics | Yes |
| GET | `/api/v1/analytics/response-rates` | Response rate breakdown | Yes |
| **Health** | | | |
| GET | `/health` | Liveness probe | No |
| GET | `/ready` | Readiness probe (checks DB, Redis) | No |

### 9.2 Response Format

**Success:**
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

**Error:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {"field": "email", "message": "Must be a valid email address"}
    ]
  }
}
```

### 9.3 Pagination

All list endpoints support:
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `sort_by` (field name)
- `sort_order` (`asc` | `desc`)

---

## 10. Folder Structure (Complete)

```
falcon-ai-job-hunter/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── docker-compose.yml
├── docker-compose.prod.yml          # Production overrides
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── api/
│       │   ├── deps.py
│       │   ├── health.py
│       │   └── v1/
│       │       ├── router.py
│       │       ├── auth.py
│       │       ├── users.py
│       │       ├── profiles.py
│       │       ├── jobs.py
│       │       ├── applications.py
│       │       ├── documents.py
│       │       └── analytics.py
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   └── logging.py
│       ├── database/
│       │   ├── session.py
│       │   └── base.py
│       ├── models/
│       │   ├── user.py
│       │   ├── job.py
│       │   ├── application.py
│       │   └── document.py
│       ├── services/
│       │   ├── auth_service.py
│       │   ├── job_search_service.py
│       │   ├── matching_service.py
│       │   ├── document_service.py
│       │   └── application_service.py
│       ├── agents/
│       │   ├── base.py
│       │   ├── cv_parser.py
│       │   ├── job_matcher.py
│       │   ├── cv_tailor.py
│       │   ├── cover_letter.py
│       │   ├── research.py
│       │   └── prompts/
│       │       ├── cv_parser_v1.jinja2
│       │       ├── job_matcher_v1.jinja2
│       │       ├── cv_tailor_v1.jinja2
│       │       └── cover_letter_v1.jinja2
│       └── utils/
│           ├── pdf.py
│           ├── text.py
│           └── retry.py
├── frontend/                          # React SPA (future)
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── product_requirements.md
│   ├── architecture.md
│   ├── coding_standards.md
│   └── roadmap.md
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.worker
│   └── Dockerfile.frontend
└── scripts/
    ├── init_db.sh
    ├── seed_data.py
    └── run_tests.sh
```

---

## 11. Data Flow

### 11.1 Job Discovery & Matching Flow

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Scheduler │───>│ Job Search   │───>│  PostgreSQL  │───>│  Matching    │
│ (Celery   │    │ Service      │    │  job_listings│    │  Agent       │
│  Beat)    │    │ (scrape API  │    │              │    │              │
└──────────┘    │  + HTML)     │    └──────────────┘    └──────┬───────┘
                └──────────────┘                                  │
                                                                  ▼
                                                         ┌──────────────┐
                                                         │  PostgreSQL  │
                                                         │  job_matches │
                                                         │  (score +    │
                                                         │  explanation)│
                                                         └──────┬───────┘
                                                                │
                                                                ▼
                                                         ┌──────────────┐
                                                         │  Notification│
                                                         │  (email if   │
                                                         │  score >     │
                                                         │  threshold)  │
                                                         └──────────────┘
```

### 11.2 Application Preparation Flow

```
User selects job in dashboard
        │
        ▼
POST /api/v1/documents/cv/tailor  ──>  CV Tailor Agent  ──>  Store tailored CV
        │
        ▼
POST /api/v1/documents/cover-letter  ──>  Cover Letter Agent  ──>  Store cover letter
        │
        ▼
User reviews materials in dashboard (edit if needed)
        │
        ▼
POST /api/v1/applications/{id}/submit  ──>  Queue automation task
        │
        ▼
Browser Automation Worker  ──>  Fill form  ──>  Submit  ──>  Update status
```

### 11.3 CV Upload & Parsing Flow

```
User uploads CV (PDF/DOCX)
        │
        ▼
POST /api/v1/profiles/cv
        │
        ├──> Store raw file (file system / S3)
        │
        ├──> Extract text (pdf utils / docx parser)
        │
        ├──> CV Parser Agent  ──>  Structured JSON profile
        │
        └──> Store in user_profiles table
                │
                ▼
        Return parsed profile to frontend for review/edit
```

---

## Appendix A: Technology Decision Records

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Backend framework | FastAPI | Django, Flask | Async support, auto OpenAPI docs, Pydantic integration |
| Database | PostgreSQL | MongoDB, MySQL | JSONB support, mature ecosystem, strong ACID |
| Task queue | Celery + Redis | ARQ, Dramatiq | Mature, Playwright-compatible, wide adoption |
| Browser automation | Playwright | Selenium, Puppeteer | Modern API, auto-wait, multi-browser, Python support |
| LLM provider | OpenAI (primary) | Anthropic, local models | Best structured output; abstraction allows switching |
| Frontend | React + TypeScript | Vue, Svelte | Ecosystem size, hiring pool, component libraries |
| Container orchestration | Docker Compose | Kubernetes | Sufficient for MVP scale; K8s when needed |

## Appendix B: Deployment Environments

| Environment | Purpose | Infrastructure |
|-------------|---------|---------------|
| Local | Developer machines | docker-compose.yml |
| Staging | Pre-production testing | Single VPS or cloud VM |
| Production | Live users | Cloud VM with managed PostgreSQL, CDN for frontend |
