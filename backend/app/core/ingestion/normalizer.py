from __future__ import annotations

from typing import Any, Dict, List

from app.models.schemas import Chunk, Document, DocumentListItem


def normalize_document(raw: Dict[str, Any]) -> Document:
    return Document(
        doc_id=raw["doc_id"],
        company=raw["company"],
        company_aliases=list(raw.get("company_aliases", [])),
        doc_type=raw["doc_type"],
        title=raw["title"],
        date=raw["date"],
        source=raw["source"],
        content=raw.get("content", ""),
    )


def normalize_chunk(raw: Dict[str, Any]) -> Chunk:
    return Chunk(
        chunk_id=raw["chunk_id"],
        doc_id=raw["doc_id"],
        section=raw.get("section", ""),
        page_num=raw.get("page_num"),
        chunk_index=raw.get("chunk_index", 0),
        content=raw.get("content", ""),
        embedding=list(raw.get("embedding", [])),
        metadata=dict(raw.get("metadata", {})),
    )


def document_list_item_from_document(document: Document, chunk_count: int) -> DocumentListItem:
    return DocumentListItem(
        doc_id=document.doc_id,
        title=document.title,
        doc_type=document.doc_type,
        company=document.company,
        date=document.date,
        chunk_count=chunk_count,
        source=document.source,
    )
