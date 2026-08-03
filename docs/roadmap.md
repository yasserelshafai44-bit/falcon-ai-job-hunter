# Falcon AI Job Hunter — Development Roadmap

**Version:** 1.0  
**Last Updated:** August 2026  
**Status:** Active

---

## Overview

This roadmap defines 12 milestones that take Falcon AI Job Hunter from project scaffold to production deployment. Each milestone produces a working, testable increment. Milestones are sequential — each builds on the previous — but some tasks within a milestone can be parallelized.

**Estimated total timeline:** 6–8 months (solo developer) | 3–4 months (team of 2–3)

---

## Milestone Summary

| # | Milestone | Duration | Key Deliverable |
|---|-----------|----------|-----------------|
| M1 | Foundation | 1 week | Running FastAPI app with config, logging, health checks |
| M2 | Backend API | 2 weeks | Auth endpoints, user management, API structure |
| M3 | Database | 1.5 weeks | PostgreSQL schema, models, migrations, CRUD |
| M4 | AI CV Parser | 2 weeks | CV upload, AI parsing, structured profile |
| M5 | Job Search Engine | 2.5 weeks | Multi-source scraping, deduplication, scheduling |
| M6 | Browser Automation | 3 weeks | Playwright-based application submission |
| M7 | AI Matching | 2 weeks | Job–profile scoring with explanations |
| M8 | CV Tailoring | 1.5 weeks | Job-specific CV generation with diff view |
| M9 | Cover Letter Generator | 1 week | Personalized cover letter generation |
| M10 | Dashboard | 3 weeks | React frontend with full user workflow |
| M11 | Analytics | 1.5 weeks | Funnel metrics, response rates, trends |
| M12 | Deployment | 1.5 weeks | Production Docker, CI/CD, monitoring |

---

## Milestone 1: Foundation

**Duration:** 1 week  
**Goal:** Establish the core backend infrastructure so all subsequent milestones have a stable base.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M1-01 | Implement `core/config.py` | P0 | Pydantic Settings loading from `.env`; all config fields typed |
| M1-02 | Implement `core/logging.py` | P0 | Structured JSON logging; configurable log level |
| M1-03 | Implement `main.py` | P0 | FastAPI app factory, CORS middleware, lifespan handler |
| M1-04 | Add health endpoints | P0 | `GET /health` (liveness), `GET /ready` (readiness) |
| M1-05 | Configure ruff + mypy | P0 | Linting and type checking; add to CI workflow |
| M1-06 | Set up pytest infrastructure | P0 | `conftest.py` with test client fixture, async test support |
| M1-07 | Verify Docker Compose stack | P1 | Backend starts via `docker compose up`; connects to PostgreSQL and Redis |
| M1-08 | Add Alembic migration setup | P1 | Initialize Alembic; configure for async SQLAlchemy |
| M1-09 | Create GitHub Actions CI | P1 | Workflow: lint → type check → test on push/PR |

### Deliverables

- [ ] FastAPI app running on `http://localhost:8000`
- [ ] Swagger UI accessible at `/docs`
- [ ] Health endpoints returning 200
- [ ] CI pipeline passing on `main`
- [ ] Docker Compose brings up backend + db + redis

### Definition of Done

- `docker compose up --build` starts all services without errors
- `pytest` runs (even if zero tests initially) without configuration errors
- `ruff check` and `mypy` pass on all existing code
- README updated with verified setup instructions

---

## Milestone 2: Backend API

**Duration:** 2 weeks  
**Goal:** Implement authentication and core API structure with versioned routing.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M2-01 | Implement `core/security.py` | P0 | bcrypt password hashing, JWT creation/validation |
| M2-02 | Create auth API routes | P0 | Register, login, refresh, logout endpoints |
| M2-03 | Implement auth dependency injection | P0 | `get_current_user` FastAPI dependency |
| M2-04 | Create API v1 router structure | P0 | `api/v1/router.py` aggregating sub-routers |
| M2-05 | Implement user endpoints | P0 | `GET/PUT /api/v1/users/me` |
| M2-06 | Add rate limiting middleware | P1 | Token bucket on auth endpoints (5/min/IP) |
| M2-07 | Implement global error handlers | P0 | Consistent JSON error responses for all exception types |
| M2-08 | Add request ID middleware | P1 | Inject `X-Request-ID` header for tracing |
| M2-09 | Write auth integration tests | P0 | Register, login, token refresh, unauthorized access |
| M2-10 | Document API in OpenAPI | P1 | All endpoints have descriptions, request/response schemas |

### Deliverables

- [ ] User registration and login working end-to-end
- [ ] JWT access + refresh token flow
- [ ] Protected endpoints reject unauthenticated requests
- [ ] API v1 route structure in place for all future endpoints
- [ ] Auth integration tests passing

### Definition of Done

- Can register a user, login, and access protected endpoint with JWT
- Invalid/expired tokens return 401 with clear error message
- All auth endpoints have integration tests with ≥ 90% coverage
- OpenAPI docs reflect all implemented endpoints

---

## Milestone 3: Database

**Duration:** 1.5 weeks  
**Goal:** Design and implement the PostgreSQL schema with SQLAlchemy models and Alembic migrations.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M3-01 | Implement async database session | P0 | `database/session.py` with async engine and session factory |
| M3-02 | Create base model with mixins | P0 | UUID PK, `created_at`, `updated_at` on all tables |
| M3-03 | Implement User model | P0 | `users` table: id, email, password_hash, is_active, timestamps |
| M3-04 | Implement UserProfile model | P0 | `user_profiles` table: parsed CV data (JSONB), raw file path, version |
| M3-05 | Implement Preferences model | P0 | `preferences` table: roles, locations, salary, exclusions |
| M3-06 | Implement JobListing model | P0 | `job_listings` table: source, title, company, location, description, URL |
| M3-07 | Implement JobMatch model | P0 | `job_matches` table: user_id, job_id, score, explanation, status |
| M3-08 | Implement Application model | P0 | `applications` table: user_id, job_match_id, status, submitted_at |
| M3-09 | Implement Document model | P0 | `documents` table: type, content, file_path, is_tailored |
| M3-10 | Create initial Alembic migration | P0 | Migration creating all tables with indexes |
| M3-11 | Write model unit tests | P1 | Test model creation, relationships, constraints |
| M3-12 | Connect auth to database | P0 | Registration/login persist to and read from PostgreSQL |

### Deliverables

- [ ] All core database tables created via Alembic migration
- [ ] SQLAlchemy models with proper relationships and indexes
- [ ] Auth service reading/writing to PostgreSQL (replacing any in-memory storage)
- [ ] Database session available as FastAPI dependency

### Definition of Done

- `alembic upgrade head` creates all tables successfully
- User registration persists to database; login reads from database
- All foreign key relationships enforced
- Model tests verify constraints (unique email, valid status enums)

---

## Milestone 4: AI CV Parser

**Duration:** 2 weeks  
**Goal:** Enable users to upload CVs and receive structured profile data parsed by an AI agent.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M4-01 | Implement LLM client abstraction | P0 | `BaseAgent` class + OpenAI client with retry/timeout |
| M4-02 | Create CV parser agent | P0 | `agents/cv_parser.py` with prompt template |
| M4-03 | Implement file upload endpoint | P0 | `POST /api/v1/profiles/cv` — accept PDF/DOCX/TXT (max 10 MB) |
| M4-04 | Implement text extraction utilities | P0 | `utils/pdf.py` for PDF/DOCX text extraction |
| M4-05 | Create CV parsing service | P0 | Orchestrate: upload → extract → parse → store |
| M4-06 | Implement profile CRUD endpoints | P0 | GET/PUT profile, list CV versions |
| M4-07 | Design parser prompt template | P0 | `prompts/cv_parser_v1.jinja2` with structured output schema |
| M4-08 | Add file storage | P0 | Store uploaded files in `uploads/{user_id}/` |
| M4-09 | Write agent unit tests | P0 | Mock LLM; test parsing with sample CVs |
| M4-10 | Write upload integration tests | P0 | Test file upload, parsing, profile retrieval |
| M4-11 | Handle parsing failures gracefully | P1 | Partial results, user-friendly error messages |

### Deliverables

- [ ] CV upload endpoint accepting PDF, DOCX, TXT
- [ ] AI agent parsing CV into structured JSON profile
- [ ] Profile stored in database and retrievable via API
- [ ] CV version history maintained
- [ ] User can manually edit parsed fields

### Definition of Done

- Upload a sample CV → receive structured profile within 30 seconds
- Parsed profile includes: name, email, skills, experience, education
- Profile editable via PUT endpoint
- Agent unit tests cover happy path and malformed input
- Integration test covers full upload-to-profile flow

---

## Milestone 5: Job Search Engine

**Duration:** 2.5 weeks  
**Goal:** Automatically discover job listings from multiple sources based on user preferences.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M5-01 | Design job search service architecture | P0 | Service + scraper plugins per job board |
| M5-02 | Implement LinkedIn scraper | P0 | Search by keywords, location, filters; extract listing data |
| M5-03 | Implement Indeed scraper | P0 | Search API or HTML scraping with rate limiting |
| M5-04 | Implement job deduplication logic | P0 | Fuzzy match on title + company across sources |
| M5-05 | Create job listing CRUD service | P0 | Store, retrieve, mark stale listings |
| M5-06 | Implement job API endpoints | P0 | `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `POST /api/v1/jobs/search` |
| M5-07 | Set up Celery + Redis task queue | P0 | Background job search tasks |
| M5-08 | Implement Celery Beat scheduler | P0 | Daily scheduled search per active user |
| M5-09 | Add search result caching | P1 | Redis cache for recent search results (1-hour TTL) |
| M5-10 | Respect rate limits and robots.txt | P0 | Configurable delays; honor crawl restrictions |
| M5-11 | Write scraper unit tests | P0 | Mock HTTP responses; test parsing and dedup |
| M5-12 | Write search integration tests | P0 | Trigger search → verify listings stored |

### Deliverables

- [ ] LinkedIn and Indeed job scraping working
- [ ] Jobs stored in database with deduplication
- [ ] Scheduled daily search per user preferences
- [ ] Manual search trigger via API
- [ ] Job listing API with pagination and filtering

### Definition of Done

- Scheduled search discovers ≥ 10 relevant jobs per user per run
- Duplicate jobs across sources correctly merged
- Job listings accessible via API with pagination
- Scraper handles HTTP errors and malformed pages without crashing
- Rate limiting prevents IP blocking

---

## Milestone 6: Browser Automation

**Duration:** 3 weeks  
**Goal:** Automate job application form filling and submission using Playwright.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M6-01 | Set up Playwright in worker container | P0 | Dockerfile.worker with Chromium dependencies |
| M6-02 | Design automation framework | P0 | Base automation class with step logging and screenshots |
| M6-03 | Implement LinkedIn Easy Apply automation | P0 | Navigate, fill fields, upload documents, submit |
| M6-04 | Implement Indeed Quick Apply automation | P0 | Form detection and filling |
| M6-05 | Implement CAPTCHA detection and pause | P0 | Detect CAPTCHA → pause task → notify user |
| M6-06 | Create application submission flow | P0 | User approval → queue task → automate → update status |
| M6-07 | Implement application API endpoints | P0 | CRUD + `POST /applications/{id}/submit` |
| M6-08 | Add screenshot logging | P0 | Capture screenshot at every step; store on failure |
| M6-09 | Implement safety controls | P0 | Max 10 submissions/day; explicit approval required |
| M6-10 | Add human-like behavior | P1 | Randomized delays, realistic typing speed |
| M6-11 | Write automation unit tests | P0 | Mock Playwright; test form detection and filling logic |
| M6-12 | Write end-to-end automation test | P1 | Test full flow against a mock application page |

### Deliverables

- [ ] LinkedIn Easy Apply automation working
- [ ] Indeed Quick Apply automation working
- [ ] Application submission with user approval flow
- [ ] CAPTCHA detection pauses and notifies user
- [ ] Full audit trail with screenshots

### Definition of Done

- User can approve an application and automation submits it on LinkedIn
- Failed automations capture screenshot and set status to "requires manual action"
- Safety controls prevent runaway submissions
- Automation worker runs in separate Docker container
- All automation actions logged with timestamps

---

## Milestone 7: AI Matching

**Duration:** 2 weeks  
**Goal:** Score every discovered job against the user's profile and provide actionable match explanations.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M7-01 | Implement job matcher agent | P0 | `agents/job_matcher.py` with scoring prompt |
| M7-02 | Design matching prompt template | P0 | `prompts/job_matcher_v1.jinja2` — skills, experience, preferences |
| M7-03 | Implement matching service | P0 | Batch match new jobs against user profile |
| M7-04 | Create match score storage | P0 | Store score + explanation in `job_matches` table |
| M7-05 | Integrate matching into search pipeline | P0 | Auto-match after job discovery |
| M7-06 | Add match score to job API responses | P0 | Include score and explanation in job listing/detail |
| M7-07 | Implement match threshold filtering | P1 | User-configurable minimum score for notifications |
| M7-08 | Cache match results | P1 | Redis cache keyed by profile hash + job ID |
| M7-09 | Write matcher agent unit tests | P0 | Test scoring logic with known profile/job pairs |
| M7-10 | Write matching service tests | P0 | Test batch matching, threshold filtering |
| M7-11 | Validate match quality | P1 | Manual review of 20 sample matches for accuracy |

### Deliverables

- [ ] Match score (0–100) computed for every job–user pair
- [ ] Human-readable match explanation generated
- [ ] Jobs sortable/filterable by match score in API
- [ ] Matching runs automatically after job discovery

### Definition of Done

- Every discovered job has a match score within 10 seconds
- Match explanation includes skills overlap, experience fit, and preference alignment
- Jobs with score ≥ 70 correctly identify strong matches (validated manually)
- Matching integrated into daily search pipeline

---

## Milestone 8: CV Tailoring

**Duration:** 1.5 weeks  
**Goal:** Generate job-specific CV variants that emphasize relevant experience while preserving factual accuracy.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M8-01 | Implement CV tailor agent | P0 | `agents/cv_tailor.py` with tailoring prompt |
| M8-02 | Design tailoring prompt template | P0 | `prompts/cv_tailor_v1.jinja2` — emphasize relevant skills/experience |
| M8-03 | Implement document service | P0 | Generate, store, retrieve tailored CVs |
| M8-04 | Create tailoring API endpoint | P0 | `POST /api/v1/documents/cv/tailor` with job_id |
| M8-05 | Implement diff generation | P1 | Compute diff between master CV and tailored version |
| M8-06 | Add PDF export | P0 | `GET /api/v1/documents/{id}/pdf` — generate PDF from tailored CV |
| M8-07 | Add factual accuracy guardrails | P0 | Prompt constraints: no fabricated experience or skills |
| M8-08 | Write tailor agent unit tests | P0 | Verify tailoring emphasizes relevant content |
| M8-09 | Write document service tests | P0 | Test generation, storage, retrieval, PDF export |

### Deliverables

- [ ] Tailored CV generated per job in < 60 seconds
- [ ] Diff view showing changes from master CV
- [ ] PDF export of tailored CV
- [ ] No fabricated content in generated CVs

### Definition of Done

- Generate tailored CV for a job → relevant skills/experience highlighted
- Diff accurately shows what changed vs. master profile
- PDF download works and is properly formatted
- Agent tests verify no hallucinated experience

---

## Milestone 9: Cover Letter Generator

**Duration:** 1 week  
**Goal:** Generate personalized cover letters for each job application.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M9-01 | Implement cover letter agent | P0 | `agents/cover_letter.py` with generation prompt |
| M9-02 | Design cover letter prompt template | P0 | `prompts/cover_letter_v1.jinja2` — company, role, profile |
| M9-03 | Create cover letter API endpoint | P0 | `POST /api/v1/documents/cover-letter` with job_id |
| M9-04 | Add tone customization | P1 | Professional, conversational, concise options |
| M9-05 | Implement cover letter editing | P0 | User can edit generated letter before saving |
| M9-06 | Add PDF export for cover letters | P0 | Download cover letter as PDF |
| M9-07 | Write cover letter agent tests | P0 | Test generation quality, length, tone variants |

### Deliverables

- [ ] Cover letter generated per job in < 60 seconds
- [ ] Letter incorporates company name, role requirements, and user profile
- [ ] User can edit and re-generate
- [ ] PDF export available

### Definition of Done

- Cover letter is 250–400 words, personalized, and grammatically correct
- Letter references specific job requirements and user qualifications
- Edit and re-generate workflow functional
- PDF export produces clean, professional document

---

## Milestone 10: Dashboard

**Duration:** 3 weeks  
**Goal:** Build the React frontend providing a complete user workflow from onboarding to application tracking.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M10-01 | Initialize React + TypeScript + Vite project | P0 | Frontend scaffold with routing and API client |
| M10-02 | Implement auth pages | P0 | Login, register, token management |
| M10-03 | Build layout components | P0 | Header, sidebar navigation, responsive layout |
| M10-04 | Build profile/onboarding page | P0 | CV upload, parsed profile review/edit |
| M10-05 | Build preferences page | P0 | Job preference form (roles, location, salary, exclusions) |
| M10-06 | Build jobs list page | P0 | Job cards with match scores, sorting, filtering |
| M10-07 | Build job detail page | P0 | Full job info, match explanation, action buttons |
| M10-08 | Build document editor | P0 | CV tailoring view with diff; cover letter editor |
| M10-09 | Build applications pipeline | P0 | Kanban/list view of application statuses |
| M10-10 | Build dashboard overview | P0 | Summary cards: active jobs, pending apps, recent matches |
| M10-11 | Add Dockerfile.frontend | P0 | Multi-stage build: Node build → nginx serve |
| M10-12 | Integrate frontend into docker-compose | P0 | Frontend service on port 3000 |
| M10-13 | Write component tests | P1 | Key components tested with React Testing Library |
| M10-14 | Responsive design | P1 | Functional on desktop (1280px+) and tablet (768px+) |

### Deliverables

- [ ] Complete frontend application with all core pages
- [ ] User can complete full workflow: register → upload CV → set preferences → browse jobs → generate materials → track applications
- [ ] Frontend served via Docker alongside backend
- [ ] Responsive layout on desktop and tablet

### Definition of Done

- Full user workflow completable through the UI without API tools
- Frontend communicates with backend API exclusively (no direct DB access)
- All pages load in < 2 seconds
- Frontend container builds and serves via docker-compose

---

## Milestone 11: Analytics

**Duration:** 1.5 weeks  
**Goal:** Provide users with actionable insights into their job search performance.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M11-01 | Design analytics data model | P0 | Aggregate queries on applications, matches, submissions |
| M11-02 | Implement funnel metrics endpoint | P0 | `GET /api/v1/analytics/funnel` — discovered → submitted → responded |
| M11-03 | Implement response rate endpoint | P0 | `GET /api/v1/analytics/response-rates` — by board, role, score band |
| M11-04 | Implement time-to-application metric | P1 | Average time from discovery to submission |
| M11-05 | Build analytics dashboard page | P0 | Funnel chart, response rate breakdown, trend lines |
| M11-06 | Add date range filtering | P1 | Filter analytics by week/month/custom range |
| M11-07 | Write analytics service tests | P0 | Test metric calculations with known data sets |
| M11-08 | Write analytics API tests | P0 | Test endpoints with various date ranges and filters |

### Deliverables

- [ ] Application funnel visualization (discovered → matched → applied → responded)
- [ ] Response rate breakdown by job board and match score
- [ ] Trend charts showing weekly/monthly activity
- [ ] Analytics page in frontend dashboard

### Definition of Done

- Funnel metrics accurately reflect application pipeline data
- Response rates calculated correctly across dimensions
- Analytics page renders charts within 2 seconds
- Date range filtering works correctly

---

## Milestone 12: Deployment

**Duration:** 1.5 weeks  
**Goal:** Deploy Falcon AI Job Hunter to a production environment with CI/CD, monitoring, and operational readiness.

### Tasks

| ID | Task | Priority | Details |
|----|------|----------|---------|
| M12-01 | Create production Docker Compose | P0 | `docker-compose.prod.yml` with resource limits, no dev volumes |
| M12-02 | Set up CI/CD pipeline | P0 | GitHub Actions: test → build → deploy on merge to main |
| M12-03 | Configure production environment | P0 | Secret management, environment-specific configs |
| M12-04 | Set up PostgreSQL backups | P0 | Daily automated backups with 30-day retention |
| M12-05 | Configure HTTPS / reverse proxy | P0 | nginx or Caddy with Let's Encrypt TLS |
| M12-06 | Add application monitoring | P0 | Health check endpoints monitored; alert on failure |
| M12-07 | Set up log aggregation | P1 | Centralized logging (Docker logs → file or cloud service) |
| M12-08 | Create deployment runbook | P0 | Step-by-step deploy, rollback, and disaster recovery docs |
| M12-09 | Load test critical endpoints | P1 | Verify 100 concurrent users with acceptable response times |
| M12-10 | Security audit | P0 | Review auth, input validation, secret handling, OWASP checks |
| M12-11 | Create staging environment | P1 | Mirror of production for pre-release testing |
| M12-12 | Write operational scripts | P1 | `scripts/deploy.sh`, `scripts/backup_db.sh`, `scripts/health_check.sh` |

### Deliverables

- [ ] Production environment running and accessible via HTTPS
- [ ] CI/CD pipeline deploys on merge to main
- [ ] Automated database backups
- [ ] Monitoring and alerting for service health
- [ ] Deployment and rollback runbook

### Definition of Done

- Application accessible at production URL via HTTPS
- Push to `main` triggers automated test → build → deploy
- Database backup verified restorable
- Health check alerts fire on service failure
- Load test passes with p95 < 200 ms for read endpoints at 100 concurrent users
- Security audit findings addressed or documented

---

## Dependency Graph

```
M1 Foundation
 └── M2 Backend API
      └── M3 Database
           ├── M4 AI CV Parser
           │    └── M7 AI Matching
           │         ├── M8 CV Tailoring
           │         │    └── M10 Dashboard
           │         │         └── M11 Analytics
           │         │              └── M12 Deployment
           │         └── M9 Cover Letter Generator
           └── M5 Job Search Engine
                ├── M7 AI Matching (also depends on M4)
                └── M6 Browser Automation
                     └── M10 Dashboard (also depends on M8, M9)
```

### Critical Path

```
M1 → M2 → M3 → M4 → M5 → M7 → M8 → M10 → M11 → M12
```

M6 (Browser Automation) and M9 (Cover Letter) can be developed in parallel with M8 once M7 is complete.

---

## Risk Register

| Risk | Impact | Mitigation | Milestone |
|------|--------|------------|-----------|
| Job board HTML changes break scrapers | High | Abstract scraper interface; monitor and alert on zero-result searches | M5 |
| LLM API costs exceed budget | Medium | Cache responses; use cheaper models for matching; set per-user quotas | M4, M7 |
| Browser automation blocked by CAPTCHAs | High | Pause-and-notify pattern; manual fallback always available | M6 |
| Job board ToS prohibits automation | High | User acknowledgment during onboarding; manual apply always available | M6 |
| Match score accuracy insufficient | Medium | Manual validation set; user feedback loop to improve prompts | M7 |
| Frontend complexity delays MVP | Medium | Build pages incrementally; API-first ensures backend is usable without UI | M10 |

---

## Success Criteria (Full Platform)

The Falcon AI Job Hunter platform is complete when:

1. A user can register, upload a CV, and set job preferences entirely through the UI
2. The system discovers relevant jobs daily from 2+ sources without manual intervention
3. Every job displays an accurate match score with explanation
4. The user can generate tailored CVs and cover letters for any matched job
5. The user can approve and auto-submit applications on LinkedIn and Indeed
6. The dashboard provides a clear view of the application pipeline
7. Analytics show funnel metrics and response rates
8. The platform runs in production with CI/CD, monitoring, and backups
9. All backend code has ≥ 80% test coverage
10. API response times meet NFR targets (p95 < 200 ms)
