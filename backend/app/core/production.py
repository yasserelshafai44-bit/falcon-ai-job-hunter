from __future__ import annotations

import logging
from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.core.middleware import register_middleware
from app.core.observability import configure_logging


def configure_production_app(
    app: FastAPI,
    *,
    log_level: int = logging.INFO,
) -> FastAPI:
    """Apply Falcon production safeguards to a FastAPI application.

    Call this once, immediately after creating the FastAPI app.
    """
    configure_logging(log_level)
    register_middleware(app)
    register_exception_handlers(app)
    return app
