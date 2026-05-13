from typing import Union

from fastapi import FastAPI

from app.api.debug import router as debug_router
from app.api.documents import router as documents_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, Union[str, bool]]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
        }

    app.include_router(documents_router)
    app.include_router(debug_router)
    return app


app = create_app()
