from __future__ import annotations

import json
from typing import Any, Iterable, List

from pydantic import BaseModel


def format_sse_event(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(_serialize(data), ensure_ascii=False)}\n\n"


def format_sse_ping() -> str:
    return "event: ping\ndata: {}\n\n"


def format_sse_error(code: str, message: str) -> str:
    return format_sse_event("error", {"code": code, "message": message})


def split_markdown_chunks(markdown: str, max_length: int = 220) -> List[str]:
    text = markdown.strip()
    if not text:
        return []
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if current and len(candidate) > max_length:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text]


def _serialize(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump()
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    return data
