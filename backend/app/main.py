import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    logger.info("application_starting environment=%s", settings.app_env)
    settings.validate_production()
    if settings.app_env == "production":
        logger.warning(
            "CV uploads use local filesystem storage; without a persistent disk, "
            "files are lost on restart or redeploy. Users must retain originals."
        )
    yield
    logger.info("application_stopping")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    version="0.2.0",
)
register_middleware(app)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)

frontend_path = Path(__file__).resolve().parents[2] / "frontend"
if not frontend_path.is_dir():
    frontend_path = Path(__file__).resolve().parents[1] / "frontend"
if frontend_path.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_path), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    async def frontend() -> FileResponse:
        return FileResponse(
            frontend_path / "index.html",
            headers={"Cache-Control": "no-store, max-age=0"},
        )
