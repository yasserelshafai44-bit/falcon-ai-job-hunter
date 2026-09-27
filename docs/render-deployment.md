# Render deployment

Use the repository root, Python runtime, Frankfurt, main, and the Free web plan.
`render.yaml` supplies the full service configuration and references the existing
`falcon-ai-job-hunter-db` in the same workspace without creating or modifying it.
A manually created service does not automatically apply render.yaml; import/sync
the Blueprint to apply these settings.

Build: `pip install -r requirements.txt`

Start: `bash scripts/render-start.sh`

The start script validates production settings, runs all Alembic migrations, and
only then starts one Uvicorn worker on Render's PORT. Failed migrations prevent
startup. No paid pre-deploy command or persistent disk is required.

## Complete environment configuration

| Variable | Production value / purpose |
| --- | --- |
| DATABASE_URL | Existing Render internal PostgreSQL connection string; Blueprint reference supplies it securely |
| JWT_SECRET_KEY | Render `generateValue: true`; stable secret, never commit it |
| APP_ENV | production |
| DEBUG | false |
| LOCAL_PASSWORD_RESET_ENABLED | false |
| ACCESS_TOKEN_MINUTES | 30 |
| LOG_LEVEL | INFO |
| CV_STORAGE_PATH | /tmp/falcon-cvs (temporary storage) |
| PYTHONPATH | backend; start script also sets an absolute path |
| PYTHON_VERSION | 3.12.8, controls Render Python runtime |
| PORT | Supplied by Render, do not manually override |

Other application settings have working defaults and need no environment entry:
APP_NAME (`Falcon AI Job Hunter`), API_V1_PREFIX (`/api/v1`), JWT_ALGORITHM (`HS256`),
MAX_CV_SIZE_MB (`10`), REMOTEOK_API_URL (`https://remoteok.com/api`),
REMOTEOK_TIMEOUT_SECONDS (`20`), REAL_JOB_REFRESH_MINUTES (`60`).
SMARTRECRUITERS_APPLICATION_TOKEN and SMARTRECRUITERS_APPLICATION_COMPANY are
optional existing integration settings and are not needed to boot or use the
ordinary application. No OpenAI key, Redis URL, SMTP credentials, separate
frontend URL, or geocoding key is required by current settings/provider selection.
Local password reset is deliberately unavailable in production.

JWT secrets must come from a cryptographically secure generator. The Blueprint
uses Render's generator. An equivalent local generator is Python's
`secrets.token_urlsafe(48)` (48 random bytes); transfer directly to a secret store
without printing, logging, or committing the result. Never regenerate on boot.

## Storage and verification

Free Render CV uploads are ephemeral: original files disappear after restart or
redeploy. The UI and production logs disclose this. Existing extracted analysis
and metadata remain in PostgreSQL; users must retain originals and re-upload
when necessary. A failed local write returns HTTP 503. No persistent disk is
assumed or provisioned. Existing local CV files and databases are not deployed.

Frontend: `/app`, with same-origin `/assets/*` and `/api/v1/*`.
Production `/api/v1/health` verifies database connectivity and the migration table;
`/api/v1/ready` checks database/provider readiness. Public verification must wait
until Render has deployed the pushed commit; local checks are not proof of a
successful Render deployment.

References: https://render.com/docs/blueprint-spec and https://render.com/docs/free
