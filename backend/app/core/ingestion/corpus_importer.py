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
from app.core.ingestion.table_facts import TableArtifact, build_table_row_chunks, extract_table_facts
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
    facts_path: Path
    facts: list[dict]


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
    documents, chunks, facts = build_processed_records(raw_documents, defaults=defaults, target_chars=target_chars)
    if not documents:
        raise ValueError("Import produced zero documents; processed corpus was left unchanged.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    documents_path = processed_dir / "documents.json"
    chunks_path = processed_dir / "chunks.json"
    facts_path = processed_dir / "table_facts.json"
    documents_path.write_text(json.dumps([doc.model_dump() for doc in documents], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chunks_path.write_text(json.dumps([chunk.model_dump() for chunk in chunks], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    facts_path.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ImportResult(documents=documents, chunks=chunks, documents_path=documents_path, chunks_path=chunks_path, facts_path=facts_path, facts=facts)


def build_processed_records(raw_documents: list[RawDocument], defaults: ImportDefaults | None = None, target_chars: int = 900) -> tuple[list[Document], list[Chunk], list[dict]]:
    defaults = defaults or ImportDefaults()
    documents: list[Document] = []
    chunks: list[Chunk] = []
    facts: list[dict] = []
    for raw in raw_documents:
        document = _document_from_raw(raw, defaults)
        documents.append(document)
        text_chunks = chunk_text(raw.body, target_chars=target_chars)
        section_parent_ids = _section_parent_ids(document, text_chunks)
        section_children: dict[str, list[str]] = {parent_id: [] for parent_id in section_parent_ids.values()}
        child_chunks: list[Chunk] = []
        for text_chunk in text_chunks:
            chunk_hash = _hash_text(f"{document.doc_id}:{text_chunk.chunk_index}:{text_chunk.content}")[:12]
            parent_id = section_parent_ids[text_chunk.section_path]
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
                "chunk_type": "text",
                "chunk_level": "paragraph",
                "parent_id": parent_id,
                "section_title": text_chunk.section_title,
                "section_path": list(text_chunk.section_path),
                "hierarchy_path": list(text_chunk.section_path) + [text_chunk.section],
            }
            child = Chunk(
                chunk_id=f"{document.doc_id}-c{text_chunk.chunk_index:04d}-{chunk_hash}",
                doc_id=document.doc_id,
                section=text_chunk.section,
                page_num=text_chunk.page_num,
                chunk_index=text_chunk.chunk_index,
                content=text_chunk.content,
                metadata=metadata,
            )
            section_children[parent_id].append(child.chunk_id)
            child_chunks.append(child)
        chunks.extend(_section_parent_chunks(raw, document, text_chunks, section_parent_ids, section_children))
        chunks.extend(child_chunks)
        table_chunks, table_facts = _table_chunks_for_document(raw, document, len(chunks))
        chunks.extend(table_chunks)
        facts.extend(table_facts)
    return documents, chunks, facts


def _section_parent_ids(document: Document, text_chunks) -> dict[tuple[str, ...], str]:
    section_paths: list[tuple[str, ...]] = []
    for text_chunk in text_chunks:
        if text_chunk.section_path not in section_paths:
            section_paths.append(text_chunk.section_path)
    return {
        section_path: f"{document.doc_id}-s{index:04d}-{_hash_text('/'.join(section_path))[:12]}"
        for index, section_path in enumerate(section_paths)
    }


def _section_parent_chunks(
    raw: RawDocument,
    document: Document,
    text_chunks,
    section_parent_ids: dict[tuple[str, ...], str],
    section_children: dict[str, list[str]],
) -> list[Chunk]:
    parents: list[Chunk] = []
    for section_path, parent_id in section_parent_ids.items():
        children = [chunk for chunk in text_chunks if chunk.section_path == section_path]
        if not children:
            continue
        title = section_path[-1] if section_path else "Document"
        first_page = next((chunk.page_num for chunk in children if chunk.page_num is not None), None)
        content = _section_summary_content(title, children)
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
            "chunk_type": "section",
            "chunk_level": "section",
            "parent_id": None,
            "child_ids": section_children.get(parent_id, []),
            "section_title": title,
            "section_path": list(section_path),
            "hierarchy_path": list(section_path),
        }
        parents.append(Chunk(
            chunk_id=parent_id,
            doc_id=document.doc_id,
            section=" > ".join(section_path),
            page_num=first_page,
            chunk_index=-1,
            content=content,
            metadata=metadata,
        ))
    return parents


_SECTION_SUMMARY_CHAR_LIMIT = 700


def _section_summary_content(title: str, children) -> str:
    body = "\n\n".join(chunk.content for chunk in children).strip()
    if len(body) > _SECTION_SUMMARY_CHAR_LIMIT:
        body = body[:_SECTION_SUMMARY_CHAR_LIMIT].rstrip() + " …[truncated]"
    return f"Section: {title}\n\n{body}".strip()


def _table_chunks_for_document(raw: RawDocument, document: Document, start_index: int) -> tuple[list[Chunk], list[dict]]:
    table_root = _table_artifact_dir(raw)
    if table_root is None or not table_root.exists():
        return [], []
    table_chunks: list[Chunk] = []
    table_facts: list[dict] = []
    table_paths = [path for path in table_root.glob("*.json") if not path.name.startswith("._")]
    for table_index, table_path in enumerate(sorted(table_paths, key=lambda path: path.name)):
        table = _read_table_payload(table_path)
        if not table:
            continue
        artifact = TableArtifact(table=table, json_path=table_path)
        markdown = str(table.get("markdown") or "").strip()
        if not markdown:
            continue
        chunk_index = start_index + len(table_chunks)
        table_id = str(table.get("table_id") or table_path.stem)
        table_title = str(table.get("title") or table_id)
        content = _render_table_chunk_content(table)
        chunk_hash = _hash_text(f"{document.doc_id}:{table_id}:{content}")[:12]
        table_chunk_id = f"{document.doc_id}-t{table_index:04d}-{chunk_hash}"
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
            "chunk_type": "table",
            "chunk_level": "table",
            "parent_id": None,
            "child_ids": [],
            "section_title": table_title,
            "section_path": ["tables", table_title],
            "hierarchy_path": ["tables", table_title],
            "table_id": table_id,
            "table_title": table_title,
            "table_json_path": str(table_path),
            "table_csv_path": str(table.get("csv_path") or ""),
            "row_count": table.get("row_count", 0),
            "column_count": table.get("column_count", 0),
            "extraction_method": str(table.get("extraction_method") or "pdfplumber"),
        }
        table_chunk = Chunk(
            chunk_id=table_chunk_id,
            doc_id=document.doc_id,
            section=f"table:{table_id}",
            page_num=_safe_int(table.get("page_num")),
            chunk_index=chunk_index,
            content=content,
            metadata=metadata,
        )
        row_chunks = build_table_row_chunks(
            raw_frontmatter=raw.frontmatter,
            document=document,
            table_artifact=artifact,
            start_index=start_index + len(table_chunks),
            parent_chunk_id=table_chunk_id,
        )
        table_chunk.metadata["child_ids"] = [chunk.chunk_id for chunk in row_chunks]
        table_chunks.append(table_chunk)
        table_chunks.extend(row_chunks)
        table_facts.extend(extract_table_facts(raw_frontmatter=raw.frontmatter, document=document, table_artifact=artifact))
    return table_chunks, table_facts


def _table_artifact_dir(raw: RawDocument) -> Path | None:
    artifact_dir = raw.frontmatter.get("table_artifact_dir")
    if artifact_dir:
        configured = Path(artifact_dir)
        if configured.exists():
            return configured
    source_name = raw.frontmatter.get("source_pdf_name") or raw.source_name
    collection = raw.collection_name or raw.frontmatter.get("collection")
    if not source_name or not collection:
        return None
    raw_root = _raw_root_from_raw_path(raw.path)
    safe_stem = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in Path(source_name).stem.strip())
    return raw_root / "tables" / collection / safe_stem


def _raw_root_from_raw_path(path: Path) -> Path:
    parts = path.parts
    if len(parts) >= 3 and parts[-3] in {"extracted", "manual"}:
        return Path(*parts[:-3])
    return path.parent


def _read_table_payload(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _render_table_chunk_content(table: dict) -> str:
    title = str(table.get("title") or table.get("table_id") or "Table")
    page_num = table.get("page_num")
    markdown = str(table.get("markdown") or "").strip()
    return "\n\n".join([
        f"Table: {title}",
        f"Page: {page_num}" if page_num is not None else "Page: unknown",
        markdown,
    ]).strip()


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
