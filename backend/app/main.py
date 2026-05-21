import logging
import threading
from contextlib import asynccontextmanager
from typing import AsyncIterator, Union

from fastapi import FastAPI

from app.api.debug import router as debug_router
from app.api.documents import router as documents_router
from app.api.kb import router as kb_router
from app.api.query import router as query_router
from app.api.preview_rewrite import router as preview_rewrite_router
from app.core.config import get_settings
from app.core.retrieval.hybrid import HybridRetriever


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if get_settings().preload_retriever:
        threading.Thread(target=_preload_default_retriever, name="finrag-retriever-preload", daemon=True).start()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, Union[str, bool]]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
        }

    app.include_router(documents_router)
    app.include_router(kb_router)
    app.include_router(debug_router)
    app.include_router(query_router)
    app.include_router(preview_rewrite_router)
    return app


app = create_app()


def _preload_default_retriever() -> None:
    try:
        HybridRetriever.load_default()
        logger.info("default retriever preloaded")
    except Exception:
        logger.exception("default retriever preload failed")
