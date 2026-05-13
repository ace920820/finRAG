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


def load_active_chunks() -> List[Chunk]:
    disabled_doc_ids = _disabled_doc_ids()
    if not disabled_doc_ids:
        return load_chunks()
    return [chunk for chunk in load_chunks() if chunk.doc_id not in disabled_doc_ids]


def load_demo_cases():
    return _load_json("demo_cases.json")


def chunk_counts_by_doc_id() -> dict[str, int]:
    counts: dict[str, int] = {}
    for chunk in load_chunks():
        counts[chunk.doc_id] = counts.get(chunk.doc_id, 0) + 1
    return counts


def _disabled_doc_ids() -> set[str]:
    state_path = _processed_dir() / "kb_state.json"
    if not state_path.exists():
        return set()
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return set()
    return {doc_id for doc_id, state in payload.items() if isinstance(state, dict) and state.get("status") == "disabled"}
