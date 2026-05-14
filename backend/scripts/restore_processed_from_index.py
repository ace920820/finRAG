"""Reconstruct backend/app/data/processed/{documents,chunks}.json from the
cached BM25 index. This is a one-shot recovery tool used after the corpus
fixtures were destroyed; it is idempotent and safe to re-run.

Usage:
    python3 scripts/restore_processed_from_index.py [--dry-run]

The reconstruction:
  - reads chunk records from app/data/index/bm25_index.json
  - groups chunks by doc_id, preserves their original order
  - rebuilds Document records using metadata from the first chunk per doc
  - reads Document.content from the original markdown file at
    metadata["source_path"] when available, otherwise concatenates chunk
    content as a fallback
  - writes documents.json and chunks.json without overwriting demo_cases.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
INDEX_PATH = BACKEND_DIR / "app" / "data" / "index" / "bm25_index.json"
PROCESSED_DIR = BACKEND_DIR / "app" / "data" / "processed"


def _load_chunks() -> list[dict[str, Any]]:
    if not INDEX_PATH.exists():
        raise SystemExit(f"BM25 index not found at {INDEX_PATH}")
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    chunks = payload.get("chunks", [])
    if not chunks:
        raise SystemExit("BM25 index contains zero chunks; cannot restore.")
    return chunks


def _document_record(doc_id: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    first = chunks[0]
    metadata = first.get("metadata", {}) or {}
    source_path = metadata.get("source_path")
    content = ""
    if source_path:
        candidate = Path(source_path)
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8")
            except OSError:
                content = ""
    if not content:
        content = "\n\n".join(chunk.get("content", "") for chunk in chunks)
    company = str(metadata.get("company", "")).strip() or "未知"
    doc_type = str(metadata.get("doc_type") or "research_report")
    if doc_type not in {"financial_report", "research_report", "news"}:
        doc_type = "research_report"
    return {
        "doc_id": doc_id,
        "company": company,
        "company_aliases": [],
        "doc_type": doc_type,
        "title": str(metadata.get("title") or metadata.get("source") or doc_id),
        "date": str(metadata.get("date") or "unknown"),
        "source": str(metadata.get("source") or metadata.get("source_pdf_name") or ""),
        "content": content,
    }


def _grouped_chunks(chunks: list[dict[str, Any]]) -> "OrderedDict[str, list[dict[str, Any]]]":
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    for chunk in chunks:
        doc_id = chunk.get("doc_id")
        if not doc_id:
            continue
        groups.setdefault(doc_id, []).append(chunk)
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report counts without writing files")
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    args = parser.parse_args()

    chunks = _load_chunks()
    groups = _grouped_chunks(chunks)
    documents = [_document_record(doc_id, doc_chunks) for doc_id, doc_chunks in groups.items()]

    print(f"Reconstructed {len(documents)} documents from {len(chunks)} chunks.")
    if args.dry_run:
        for doc in documents[:5]:
            print(f"  - {doc['doc_id']} | {doc['company']} | {doc['doc_type']} | {doc['title'][:60]}")
        return 0

    args.processed_dir.mkdir(parents=True, exist_ok=True)
    documents_path = args.processed_dir / "documents.json"
    chunks_path = args.processed_dir / "chunks.json"
    documents_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    chunks_path.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {documents_path}")
    print(f"Wrote {chunks_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
