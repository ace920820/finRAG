from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfileobj
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.core.config import get_settings
from app.core.ingestion.fixture_loader import _processed_dir, chunk_counts_by_doc_id, load_chunks, load_documents
from app.core.ingestion.raw_loader import discover_raw_inputs
from app.core.ingestion.corpus_importer import ImportDefaults, import_corpus
from app.core.retrieval.index_store import RetrievalIndexStore
from app.models.schemas import (
    KBChunkSummary,
    KBDocumentDetail,
    KBDocumentListItem,
    KBDocumentListResponse,
    KBOverviewResponse,
    KBImportJobResponse,
    KBImportRequest,
    KBReindexResponse,
    KBUploadResponse,
)

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])

DocumentStatus = Literal["active", "disabled", "failed"]
ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".md", ".txt"}
JOBS: dict[str, "ImportJobState"] = {}
KB_STATE_FILENAME = "kb_state.json"


@dataclass
class ImportJobState:
    job_id: str
    status: str
    total_files: int = 0
    success_count: int = 0
    fail_count: int = 0
    created_at: str = ""
    started_at: str | None = None
    finished_at: str | None = None
    error_messages: list[str] | None = None
    reindex_status: str = "not_requested"


@router.get("/overview", response_model=KBOverviewResponse)
def get_overview() -> KBOverviewResponse:
    documents = load_documents()
    chunks = load_chunks()
    processed_dir = get_settings().processed_dir
    return KBOverviewResponse(
        total_documents=len(documents),
        total_chunks=len(chunks),
        last_import_at=_file_mtime(processed_dir / "documents.json"),
        last_reindex_at=_latest_mtime(get_settings().resolved_index_dir),
        status="ready" if documents else "not_initialized",
    )


@router.get("/documents", response_model=KBDocumentListResponse)
def list_kb_documents(
    q: Optional[str] = Query(default=None),
    company: Optional[str] = Query(default=None),
    doc_type: Optional[str] = Query(default=None),
    status: Optional[DocumentStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> KBDocumentListResponse:
    counts = chunk_counts_by_doc_id()
    items = [_document_item(document, counts.get(document.doc_id, 0)) for document in load_documents()]
    filtered = _filter_documents(items, q=q, company=company, doc_type=doc_type, status=status)
    start = (page - 1) * page_size
    end = start + page_size
    return KBDocumentListResponse(total=len(filtered), documents=filtered[start:end])


@router.get("/documents/{doc_id}", response_model=KBDocumentDetail)
def get_kb_document(doc_id: str) -> KBDocumentDetail:
    document = next((item for item in load_documents() if item.doc_id == doc_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = [chunk for chunk in load_chunks() if chunk.doc_id == doc_id]
    first_chunk = chunks[0] if chunks else None
    source_path = ""
    collection_name = "default"
    if first_chunk:
        source_path = str(first_chunk.metadata.get("source_path") or "")
        collection_name = str(first_chunk.metadata.get("collection") or "default")
    status, error_message = _load_document_state(doc_id)
    return KBDocumentDetail(
        doc_id=document.doc_id,
        title=document.title,
        company=document.company,
        doc_type=document.doc_type,
        date=document.date,
        source=document.source,
        source_path=source_path,
        chunk_count=len(chunks),
        status=status,
        collection_name=collection_name,
        error_message=error_message,
        chunks=[
            KBChunkSummary(
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                section=chunk.section,
                page_num=chunk.page_num,
                content=chunk.content[:500],
                metadata=chunk.metadata,
            )
            for chunk in chunks[:20]
        ],
    )


@router.post("/upload", response_model=KBUploadResponse)
def upload_files(
    files: list[UploadFile] = File(...),
    collection_name: str = Form("default"),
) -> KBUploadResponse:
    target_dir = get_settings().data_dir / "raw" / "manual" / _safe_name(collection_name)
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []
    for upload in files:
        filename = Path(upload.filename or "uploaded.txt").name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_UPLOAD_SUFFIXES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")
        target_path = target_dir / filename
        with target_path.open("wb") as output:
            copyfileobj(upload.file, output)
        saved_paths.append(str(target_path))
    return KBUploadResponse(uploaded=len(saved_paths), saved_paths=saved_paths)


@router.post("/import", response_model=KBImportJobResponse)
def start_import(request: KBImportRequest) -> KBImportJobResponse:
    job = _new_job()
    JOBS[job.job_id] = job
    job.status = "running"
    job.started_at = _now()
    try:
        source_dir = Path(request.source_dir) if request.source_dir else None
        raw_root = get_settings().data_dir / "raw"
        processed_dir = Path(request.processed_dir) if request.processed_dir else get_settings().processed_dir
        _validate_request_paths(raw_root=raw_root, processed_dir=processed_dir, source_dir=source_dir)
        readable_inputs = discover_raw_inputs(raw_root=raw_root, collection_name=request.collection_name, source_dir=source_dir)
        if not readable_inputs:
            raise ValueError("No importable Markdown/TXT/PDF files found.")
        import_dir = processed_dir / ".tmp_import" / job.job_id
        result = import_corpus(
            raw_root=raw_root,
            source_dir=source_dir,
            collection_name=request.collection_name,
            processed_dir=import_dir,
            defaults=ImportDefaults(
                company=request.default_company,
                doc_type=request.default_doc_type,
                date=request.default_date,
            ),
        )
        _merge_processed_records(processed_dir, result.documents_path, result.chunks_path)
        _write_state(processed_dir, request.collection_name, result.documents)
        job.total_files = len(result.documents)
        job.success_count = len(result.documents)
        job.fail_count = 0
        _processed_dir.cache_clear()
        if request.rebuild_index:
            _rebuild_index()
            job.reindex_status = "completed"
        job.status = "completed"
    except Exception as exc:  # pragma: no cover - exercised through API failure payloads
        job.status = "failed"
        job.fail_count = 1
        job.error_messages = [str(exc)]
        if request.rebuild_index:
            job.reindex_status = "failed"
    finally:
        job.finished_at = _now()
    return _job_response(job)


@router.get("/import-jobs/{job_id}", response_model=KBImportJobResponse)
def get_import_job(job_id: str) -> KBImportJobResponse:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return _job_response(job)


@router.post("/reindex", response_model=KBReindexResponse)
def reindex() -> KBReindexResponse:
    _rebuild_index()
    return KBReindexResponse(status="completed")


@router.post("/documents/{doc_id}/reimport", response_model=KBImportJobResponse)
def reimport_document(doc_id: str) -> KBImportJobResponse:
    document = next((item for item in load_documents() if item.doc_id == doc_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    job = _new_job()
    job.status = "completed"
    job.started_at = job.created_at
    job.finished_at = _now()
    job.total_files = 1
    job.success_count = 1
    job.reindex_status = "not_requested"
    JOBS[job.job_id] = job
    _update_document_state(document.doc_id, status="active", error_message=None)
    return _job_response(job)


@router.delete("/documents/{doc_id}")
def disable_document(doc_id: str) -> dict[str, str]:
    if not any(item.doc_id == doc_id for item in load_documents()):
        raise HTTPException(status_code=404, detail="Document not found")
    _update_document_state(doc_id, status="disabled", error_message=None)
    return {"doc_id": doc_id, "status": "disabled"}


def _document_item(document, chunk_count: int) -> KBDocumentListItem:
    source_path = ""
    collection_name = "default"
    for chunk in load_chunks():
        if chunk.doc_id == document.doc_id:
            source_path = str(chunk.metadata.get("source_path") or "")
            collection_name = str(chunk.metadata.get("collection") or "default")
            break
    status, error_message = _load_document_state(document.doc_id)
    return KBDocumentListItem(
        doc_id=document.doc_id,
        title=document.title,
        company=document.company,
        doc_type=document.doc_type,
        date=document.date,
        source=document.source,
        source_path=source_path,
        chunk_count=chunk_count,
        status=status,
        collection_name=collection_name,
        error_message=error_message,
    )


def _filter_documents(
    items: list[KBDocumentListItem],
    *,
    q: Optional[str],
    company: Optional[str],
    doc_type: Optional[str],
    status: Optional[DocumentStatus],
) -> list[KBDocumentListItem]:
    result = items
    if q:
        query = q.lower()
        result = [item for item in result if query in item.title.lower() or query in item.company.lower() or query in (item.source or "").lower()]
    if company:
        result = [item for item in result if item.company == company]
    if doc_type:
        result = [item for item in result if item.doc_type == doc_type]
    if status:
        result = [item for item in result if item.status == status]
    return result


def _file_mtime(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _latest_mtime(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    files = [item for item in path.rglob("*") if item.is_file()]
    if not files:
        return None
    return datetime.fromtimestamp(max(item.stat().st_mtime for item in files), tz=timezone.utc).isoformat()


def _new_job() -> ImportJobState:
    return ImportJobState(job_id=f"job-{uuid4().hex[:12]}", status="pending", created_at=_now(), error_messages=[])


def _job_response(job: ImportJobState) -> KBImportJobResponse:
    payload = asdict(job)
    payload["error_messages"] = payload.get("error_messages") or []
    return KBImportJobResponse(**payload)


def _rebuild_index() -> None:
    _processed_dir.cache_clear()
    index_store = RetrievalIndexStore.load_or_build(force_rebuild=True)
    index_store.save()


def _safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value.strip())
    return cleaned or "default"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _merge_processed_records(processed_dir: Path, imported_documents_path: Path, imported_chunks_path: Path) -> None:
    import json

    existing_documents_path = processed_dir / "documents.json"
    existing_chunks_path = processed_dir / "chunks.json"
    imported_documents = json.loads(imported_documents_path.read_text(encoding="utf-8"))
    imported_chunks = json.loads(imported_chunks_path.read_text(encoding="utf-8"))
    if not imported_documents:
        raise ValueError("Import produced zero documents; existing knowledge base was left unchanged.")
    existing_documents = _read_json_list(existing_documents_path)
    existing_chunks = _read_json_list(existing_chunks_path)
    merged_documents = {item["doc_id"]: item for item in existing_documents}
    for item in imported_documents:
        merged_documents[item["doc_id"]] = item
    imported_doc_ids = {item["doc_id"] for item in imported_documents}
    merged_chunks = [item for item in existing_chunks if item.get("doc_id") not in imported_doc_ids]
    merged_chunks.extend(imported_chunks)
    existing_documents_path.write_text(json.dumps(list(merged_documents.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    existing_chunks_path.write_text(json.dumps(merged_chunks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_state(processed_dir: Path, collection_name: str, documents) -> None:
    import json

    state_path = processed_dir / KB_STATE_FILENAME
    state = _read_state(state_path)
    for document in documents:
        state[document.doc_id] = {
            "status": "active",
            "error_message": None,
            "collection_name": collection_name,
        }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_document_state(doc_id: str, *, status: str, error_message: Optional[str]) -> None:
    import json

    settings = get_settings()
    processed_dir = settings.processed_dir
    processed_dir.mkdir(parents=True, exist_ok=True)
    state_path = processed_dir / KB_STATE_FILENAME
    state = _read_state(state_path)
    current = state.get(doc_id, {})
    state[doc_id] = {
        **current,
        "status": status,
        "error_message": error_message,
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_state(path: Path) -> dict[str, dict]:
    import json

    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_document_state(doc_id: str) -> tuple[str, Optional[str]]:
    state = _read_state(get_settings().processed_dir / KB_STATE_FILENAME)
    entry = state.get(doc_id, {})
    return str(entry.get("status") or "active"), entry.get("error_message")


def _validate_request_paths(*, raw_root: Path, processed_dir: Path, source_dir: Optional[Path]) -> None:
    resolved_raw = raw_root.resolve()
    resolved_processed = processed_dir.resolve()
    resolved_root = get_settings().data_dir.resolve()
    try:
        resolved_processed.relative_to(resolved_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="processed_dir must stay under the configured data directory") from exc
    if source_dir is not None:
        try:
            source_dir.resolve().relative_to(resolved_raw)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="source_dir must stay under backend/app/data/raw") from exc


def _read_json_list(path: Path) -> list[dict]:
    import json

    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []
