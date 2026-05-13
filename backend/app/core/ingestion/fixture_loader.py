from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List

from app.core.config import get_settings
from app.models.schemas import Chunk, Document
from app.core.ingestion.normalizer import normalize_chunk, normalize_document


@lru_cache
def _processed_dir() -> Path:
    return get_settings().processed_dir


def _load_json(filename: str):
    path = _processed_dir() / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_documents() -> List[Document]:
    return [normalize_document(item) for item in _load_json("documents.json")]


def load_chunks() -> List[Chunk]:
    return [normalize_chunk(item) for item in _load_json("chunks.json")]


def load_demo_cases():
    return _load_json("demo_cases.json")


def chunk_counts_by_doc_id() -> dict[str, int]:
    counts: dict[str, int] = {}
    for chunk in load_chunks():
        counts[chunk.doc_id] = counts.get(chunk.doc_id, 0) + 1
    return counts
