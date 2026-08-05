from fastapi import FastAPI

from app.core.production import configure_production_app


def test_production_bootstrap_registers_middleware_and_handlers() -> None:
    app = FastAPI()
    configure_production_app(app)

    middleware_names = {item.cls.__name__ for item in app.user_middleware}

    assert "RequestContextMiddleware" in middleware_names
    assert "SecurityHeadersMiddleware" in middleware_names
    assert Exception in app.exception_handlers
