from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import build_embedding_provider
from app.core.retrieval.bm25_store import BM25Store
from app.core.retrieval.vector_store import VectorStore


@dataclass
class RetrievalIndexStore:
    bm25_store: BM25Store
    vector_store: VectorStore

    @classmethod
    def load_or_build(cls) -> "RetrievalIndexStore":
        settings = get_settings()
        index_dir = settings.index_dir
        index_dir.mkdir(parents=True, exist_ok=True)
        bm25_path = index_dir / "bm25_index.json"
        vector_path = index_dir / "vector_index.json"
        chunks = load_chunks()
        embedding_provider = build_embedding_provider()
        bm25_store = BM25Store.from_chunks(chunks)
        if vector_path.exists():
            vector_store = VectorStore.load(index_dir)
            if vector_store is None:
                vector_store = VectorStore.from_chunks(chunks, embedding_provider)
        else:
            vector_store = VectorStore.from_chunks(chunks, embedding_provider)
        if not bm25_path.exists():
            cls._save_bm25(index_dir, bm25_store)
        return cls(bm25_store=bm25_store, vector_store=vector_store)

    @staticmethod
    def _save_bm25(index_dir: Path, store: BM25Store) -> None:
        import json

        payload = {
            "chunks": [chunk.model_dump() for chunk in store.chunks],
            "tokenized": store._tokenized,
        }
        (index_dir / "bm25_index.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def save(self) -> None:
        settings = get_settings()
        settings.index_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store.save(settings.index_dir)
        self._save_bm25(settings.index_dir, self.bm25_store)
