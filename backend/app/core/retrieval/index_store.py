from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.ingestion.fixture_loader import load_active_chunks
from app.core.providers.embeddings import build_embedding_provider
from app.core.retrieval.bm25_store import BM25Store
from app.core.retrieval.vector_store import VectorStore


logger = logging.getLogger(__name__)


@dataclass
class RetrievalIndexStore:
    bm25_store: BM25Store
    vector_store: VectorStore

    @classmethod
    def load_or_build(cls, force_rebuild: bool = False) -> "RetrievalIndexStore":
        settings = get_settings()
        index_dir = settings.resolved_index_dir
        index_dir.mkdir(parents=True, exist_ok=True)
        bm25_path = index_dir / "bm25_index.json"
        vector_path = index_dir / "vector_index.json"
        chunks = None
        bm25_store = cls._load_bm25(index_dir) if bm25_path.exists() and not force_rebuild else None
        if bm25_store is None:
            chunks = load_active_chunks()
            bm25_store = BM25Store.from_chunks(chunks)
        if vector_path.exists() and not force_rebuild:
            vector_store = VectorStore.load(index_dir)
            if vector_store is None:
                chunks = chunks or load_active_chunks()
                embedding_provider = build_embedding_provider()
                vector_store = VectorStore.from_chunks(chunks, embedding_provider)
            else:
                _warn_if_vector_dimension_mismatch(vector_store)
        else:
            chunks = chunks or load_active_chunks()
            embedding_provider = build_embedding_provider()
            vector_store = VectorStore.from_chunks(chunks, embedding_provider)
        if force_rebuild or not bm25_path.exists():
            cls._save_bm25(index_dir, bm25_store)
        return cls(bm25_store=bm25_store, vector_store=vector_store)

    @staticmethod
    def _load_bm25(index_dir: Path) -> Optional[BM25Store]:
        import json

        path = index_dir / "bm25_index.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return BM25Store.from_index_payload(payload.get("chunks", []), payload.get("tokenized", []))

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
        index_dir = settings.resolved_index_dir
        index_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store.save(index_dir)
        self._save_bm25(index_dir, self.bm25_store)


def _warn_if_vector_dimension_mismatch(vector_store: VectorStore) -> None:
    # 21.1 修复后不再自动重建以避免线上卡死。这里只在加载时记录维度信息，
    # 不调用 embed_texts 探测（启动路径需保持零远程调用，由查询时的失败日志兜底）。
    if not vector_store.dimension:
        return
    settings = get_settings()
    provider = getattr(settings, "embedding_provider", "unknown")
    model = getattr(settings, "embedding_model", "unknown")
    logger.info(
        "vector index loaded: dimension=%d provider=%s model=%s (if dimension mismatches provider, "
        "vector retrieval will degrade until /api/kb/reindex is triggered)",
        vector_store.dimension,
        provider,
        model,
    )
