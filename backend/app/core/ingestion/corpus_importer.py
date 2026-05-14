from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Literal

from app.core.ingestion.chunker import chunk_text
from app.core.ingestion.raw_loader import RawDocument, load_raw_documents
from app.models.schemas import Chunk, DocType, Document


DEFAULT_DOC_TYPE: DocType = "research_report"
VALID_DOC_TYPES = {"financial_report", "research_report", "news"}
COMPANY_NAME_MAP = {
    "catl": ("宁德时代", ["CATL", "300750"]),
    "moutai": ("贵州茅台", ["茅台", "600519"]),
    "nvidia": ("NVIDIA", ["NVDA"]),
    "tsmc": ("台积电", ["TSMC", "2330"]),
}
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


@dataclass(frozen=True)
class ImportDefaults:
    company: str = "未知"
    doc_type: DocType = DEFAULT_DOC_TYPE
    date: str = "unknown"
    company_aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportResult:
    documents: list[Document]
    chunks: list[Chunk]
    documents_path: Path
    chunks_path: Path


def import_corpus(
    *,
    raw_root: Path,
    processed_dir: Path,
    collection_name: str | None = None,
    source_dir: Path | None = None,
    defaults: ImportDefaults | None = None,
    target_chars: int = 900,
) -> ImportResult:
    defaults = defaults or ImportDefaults()
    raw_documents = load_raw_documents(raw_root=raw_root, collection_name=collection_name, source_dir=source_dir)
    if not raw_documents:
        raise ValueError("No raw input documents found; processed corpus was left unchanged.")
    documents, chunks = build_processed_records(raw_documents, defaults=defaults, target_chars=target_chars)
    if not documents:
        raise ValueError("Import produced zero documents; processed corpus was left unchanged.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    documents_path = processed_dir / "documents.json"
    chunks_path = processed_dir / "chunks.json"
    documents_path.write_text(json.dumps([doc.model_dump() for doc in documents], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chunks_path.write_text(json.dumps([chunk.model_dump() for chunk in chunks], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ImportResult(documents=documents, chunks=chunks, documents_path=documents_path, chunks_path=chunks_path)


def build_processed_records(raw_documents: list[RawDocument], defaults: ImportDefaults | None = None, target_chars: int = 900) -> tuple[list[Document], list[Chunk]]:
    defaults = defaults or ImportDefaults()
    documents: list[Document] = []
    chunks: list[Chunk] = []
    for raw in raw_documents:
        document = _document_from_raw(raw, defaults)
        documents.append(document)
        for text_chunk in chunk_text(raw.body, target_chars=target_chars):
            chunk_hash = _hash_text(f"{document.doc_id}:{text_chunk.chunk_index}:{text_chunk.content}")[:12]
            metadata = {
                **raw.frontmatter,
                "title": document.title,
                "source": document.source,
                "company": document.company,
                "doc_type": document.doc_type,
                "date": document.date,
                "collection": raw.collection_name or raw.frontmatter.get("collection", "default"),
                "source_path": str(raw.path),
                "source_name": raw.source_name,
            }
            chunks.append(Chunk(
                chunk_id=f"{document.doc_id}-c{text_chunk.chunk_index:04d}-{chunk_hash}",
                doc_id=document.doc_id,
                section=text_chunk.section,
                page_num=text_chunk.page_num,
                chunk_index=text_chunk.chunk_index,
                content=text_chunk.content,
                metadata=metadata,
            ))
    return documents, chunks


def _document_from_raw(raw: RawDocument, defaults: ImportDefaults) -> Document:
    frontmatter = raw.frontmatter
    content_hash = str(frontmatter.get("content_hash") or frontmatter.get("pdf_sha256") or _hash_text(raw.body))
    source_identity = str(frontmatter.get("source_pdf_path") or frontmatter.get("source_pdf_name") or raw.path.as_posix())
    doc_id = f"doc-{_hash_text(source_identity + ':' + content_hash)[:16]}"
    inferred_company, inferred_aliases = _infer_company(frontmatter, source_identity, defaults)
    doc_type = _doc_type(frontmatter.get("doc_type") or _infer_doc_type(source_identity), defaults.doc_type)
    company_aliases = _aliases(frontmatter.get("company_aliases"), tuple(inferred_aliases))
    date = str(frontmatter.get("date") or _infer_date(source_identity) or defaults.date)
    return Document(
        doc_id=doc_id,
        company=str(frontmatter.get("company") or frontmatter.get("company_name") or inferred_company),
        company_aliases=company_aliases,
        doc_type=doc_type,
        title=str(frontmatter.get("title") or raw.title),
        date=date,
        source=str(frontmatter.get("source") or frontmatter.get("source_pdf_name") or raw.source_name),
        content=raw.body,
    )


def _doc_type(value: str | None, default: DocType) -> DocType:
    if value in VALID_DOC_TYPES:
        return value  # type: ignore[return-value]
    return default


def _aliases(value: str | None, defaults: tuple[str, ...]) -> list[str]:
    if not value:
        return list(defaults)
    return [item.strip() for item in value.split(",") if item.strip()]


def _infer_company(frontmatter: dict[str, str], source_identity: str, defaults: ImportDefaults) -> tuple[str, list[str]]:
    if frontmatter.get("company") or frontmatter.get("company_name"):
        company = str(frontmatter.get("company") or frontmatter.get("company_name"))
        aliases = _aliases(frontmatter.get("company_aliases"), defaults.company_aliases)
        return company, aliases
    lowered = source_identity.lower()
    for key, (company, aliases) in COMPANY_NAME_MAP.items():
        if key in lowered:
            return company, aliases
    return defaults.company, list(defaults.company_aliases)


def _infer_doc_type(source_identity: str) -> DocType | None:
    lowered = source_identity.lower()
    if "financial_report" in lowered or "annual_report" in lowered or "quarterly_report" in lowered or "semiannual" in lowered or "10k" in lowered or "10q" in lowered:
        return "financial_report"
    if "research_report" in lowered:
        return "research_report"
    if "news" in lowered:
        return "news"
    return None


def _infer_date(source_identity: str) -> str | None:
    match = DATE_RE.search(source_identity)
    if match:
        return match.group(1)
    return None


def _hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()
