from app.core.retrieval.bm25_store import BM25Store
from app.core.retrieval.hybrid import HybridRetriever, clear_default_retriever_cache
from app.core.retrieval.vector_store import VectorStore


class FakeIndexStore:
    def __init__(self):
        self.bm25_store = BM25Store.from_chunks([])
        self.vector_store = VectorStore([], [])


def test_default_retriever_is_cached(monkeypatch):
    calls = []

    def fake_load_or_build():
        calls.append("load")
        return FakeIndexStore()

    monkeypatch.setattr("app.core.retrieval.hybrid.RetrievalIndexStore.load_or_build", fake_load_or_build)
    clear_default_retriever_cache()

    first = HybridRetriever.load_default()
    second = HybridRetriever.load_default()

    assert first is second
    assert calls == ["load"]


def test_default_retriever_cache_can_be_cleared(monkeypatch):
    calls = []

    def fake_load_or_build():
        calls.append("load")
        return FakeIndexStore()

    monkeypatch.setattr("app.core.retrieval.hybrid.RetrievalIndexStore.load_or_build", fake_load_or_build)
    clear_default_retriever_cache()

    first = HybridRetriever.load_default()
    clear_default_retriever_cache()
    second = HybridRetriever.load_default()

    assert first is not second
    assert calls == ["load", "load"]
