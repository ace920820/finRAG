import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import create_app


@pytest.fixture(autouse=True)
def _force_mock_providers(monkeypatch):
    monkeypatch.setenv("FINRAG_EMBEDDING_PROVIDER", "mock")
    monkeypatch.setenv("FINRAG_RERANK_PROVIDER", "mock")
    monkeypatch.setenv("FINRAG_TEXT_PROVIDER", "mock")
    monkeypatch.setenv("FINRAG_MODEL_API_KEY", "")
    monkeypatch.setenv("FINRAG_EMBEDDING_API_KEY", "")
    monkeypatch.setenv("FINRAG_RERANK_API_KEY", "")
    monkeypatch.setenv("FINRAG_LLM_API_KEY", "")
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)
