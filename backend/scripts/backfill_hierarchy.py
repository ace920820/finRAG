from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

DEFAULT_PROCESSED_DIR = BACKEND_DIR / "app" / "data" / "processed"
DEFAULT_INDEX_DIR = BACKEND_DIR / "app" / "data" / "index"
TEXT_PARENT_PAGE_SPAN = 5
SECTION_SUMMARY_CHAR_LIMIT = 700


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill hierarchy metadata without re-embedding existing chunks.")
    parser.add_argument("--processed-dir", type=Path, default=Path(os.environ.get("FINRAG_PROCESSED_DATA_DIR", DEFAULT_PROCESSED_DIR)))
    parser.add_argument("--index-dir", type=Path, default=Path(os.environ.get("FINRAG_INDEX_DIR", DEFAULT_INDEX_DIR)))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from app.core.config import get_settings
    from app.core.ingestion.fixture_loader import _processed_dir
    from app.core.providers.embeddings import build_embedding_provider
    from app.core.retrieval.bm25_store import BM25Store
    from app.core.retrieval.hybrid import clear_default_retriever_cache
    from app.core.retrieval.vector_store import VectorStore
    from app.models.schemas import Chunk

    os.environ["FINRAG_PROCESSED_DATA_DIR"] = str(args.processed_dir.resolve())
    os.environ["FINRAG_INDEX_DIR"] = str(args.index_dir.resolve())
    get_settings.cache_clear()
    _processed_dir.cache_clear()

    chunks_path = args.processed_dir / "chunks.json"
    vector_path = args.index_dir / "vector_index.json"
    bm25_path = args.index_dir / "bm25_index.json"
    chunks_payload = _read_json(chunks_path)
    vector_payload = _read_json(vector_path)
    bm25_payload = _read_json(bm25_path)
    chunks = [Chunk(**item) for item in chunks_payload]
    index_chunks = [Chunk(**item) for item in vector_payload.get("chunks", [])]
    vectors = list(vector_payload.get("vectors", []))
    if len(index_chunks) != len(vectors):
        raise SystemExit("vector index chunks/vectors length mismatch")
    if [chunk.chunk_id for chunk in chunks] != [chunk.chunk_id for chunk in index_chunks[:len(chunks)]]:
        raise SystemExit("processed chunks must match vector index prefix before backfill")

    existing_extra_chunks = index_chunks[len(chunks):]
    updated_chunks, new_parent_chunks = backfill_chunks(chunks, existing_extra_chunks=existing_extra_chunks)
    updated_index_chunks = updated_chunks + existing_extra_chunks + new_parent_chunks
    if args.dry_run:
        _print_summary(chunks, updated_index_chunks, existing_extra_chunks, new_parent_chunks, vector_payload.get("provenance") or {})
        return 0

    provider = build_embedding_provider()
    parent_vectors = provider.embed_texts([chunk.content for chunk in new_parent_chunks]) if new_parent_chunks else []
    if new_parent_chunks:
        expected_dimension = len(vectors[0]) if vectors else len(parent_vectors[0])
        if any(len(vector) != expected_dimension for vector in parent_vectors):
            raise SystemExit("new parent vector dimension mismatch")
    next_vectors = vectors + parent_vectors
    vector_store = VectorStore(updated_index_chunks, next_vectors, provenance=vector_payload.get("provenance") or {})
    bm25_store = BM25Store.from_chunks(updated_index_chunks)

    _write_json(chunks_path, [chunk.model_dump() for chunk in updated_index_chunks])
    vector_store.save(args.index_dir)
    _write_json(bm25_path, {
        "chunks": [chunk.model_dump() for chunk in bm25_store.chunks],
        "tokenized": bm25_store._tokenized,
    })
    clear_default_retriever_cache()
    _print_summary(chunks, updated_index_chunks, existing_extra_chunks, new_parent_chunks, vector_store.provenance)
    return 0


def backfill_chunks(chunks: list[Any], existing_extra_chunks: list[Any] | None = None) -> tuple[list[Any], list[Any]]:
    from app.models.schemas import Chunk

    existing_extra_chunks = existing_extra_chunks or []
    existing_ids = {chunk.chunk_id for chunk in chunks}
    existing_ids.update(chunk.chunk_id for chunk in existing_extra_chunks)
    updated = [chunk.model_copy(deep=True) for chunk in chunks]
    by_id = {chunk.chunk_id: chunk for chunk in updated}
    new_parents: list[Chunk] = []

    text_groups: dict[tuple[str, int], list[Chunk]] = defaultdict(list)
    for chunk in updated:
        metadata = chunk.metadata
        chunk_type = metadata.get("chunk_type")
        if chunk_type not in (None, "", "text"):
            continue
        group_key = (chunk.doc_id, _page_bucket(chunk.page_num))
        text_groups[group_key].append(chunk)

    for (doc_id, bucket), children in sorted(text_groups.items(), key=lambda item: (item[0][0], item[0][1])):
        children.sort(key=lambda chunk: (chunk.page_num or 0, chunk.chunk_index))
        parent_id = _parent_id(doc_id, f"text:{bucket}")
        if parent_id in existing_ids:
            continue
        section_title = _text_section_title(children)
        section_path = [_source_label(children[0]), section_title]
        child_ids = [child.chunk_id for child in children]
        for child in children:
            metadata = dict(child.metadata)
            metadata.update({
                "chunk_type": "text",
                "chunk_level": "paragraph",
                "parent_id": parent_id,
                "section_title": section_title,
                "section_path": section_path,
                "hierarchy_path": section_path + [child.section],
            })
            by_id[child.chunk_id] = child.model_copy(update={"metadata": metadata})
        first = children[0]
        parent_metadata = {
            **first.metadata,
            "chunk_type": "section",
            "chunk_level": "section",
            "parent_id": None,
            "child_ids": child_ids,
            "section_title": section_title,
            "section_path": section_path,
            "hierarchy_path": section_path,
        }
        new_parents.append(Chunk(
            chunk_id=parent_id,
            doc_id=doc_id,
            section=" > ".join(section_path),
            page_num=children[0].page_num,
            chunk_index=-1,
            content=_section_summary_content(section_title, children),
            metadata=parent_metadata,
        ))

    table_groups: dict[tuple[str, str], dict[str, list[Chunk] | Chunk | None]] = defaultdict(lambda: {"parents": [], "rows": []})
    for chunk in updated:
        metadata = chunk.metadata
        chunk_type = metadata.get("chunk_type")
        if chunk_type not in {"table", "table_row"}:
            continue
        key = (chunk.doc_id, _table_key(chunk))
        table_groups[key]["parents"].append(chunk)  # type: ignore[union-attr]
        if chunk_type == "table_row":
            table_groups[key]["rows"].append(chunk)  # type: ignore[union-attr]

    for (_doc_id, _table_key_value), group in table_groups.items():
        parents = [chunk for chunk in group["parents"] if chunk.metadata.get("chunk_type") == "table"]  # type: ignore[index]
        rows = [chunk for chunk in group["rows"]]  # type: ignore[index]
        if not parents:
            continue
        parent = sorted(parents, key=lambda chunk: chunk.chunk_index)[0]
        table_title = str(parent.metadata.get("table_title") or parent.metadata.get("section_title") or parent.section)
        section_path = ["tables", table_title]
        row_ids = [row.chunk_id for row in sorted(rows, key=lambda chunk: chunk.chunk_index)]
        parent_metadata = dict(parent.metadata)
        parent_metadata.update({
            "chunk_level": "table",
            "parent_id": None,
            "child_ids": row_ids,
            "section_title": table_title,
            "section_path": section_path,
            "hierarchy_path": section_path,
        })
        by_id[parent.chunk_id] = parent.model_copy(update={"metadata": parent_metadata})
        for row in rows:
            row_metadata = dict(row.metadata)
            row_metadata.update({
                "chunk_level": "table_row",
                "parent_id": parent.chunk_id,
                "section_title": table_title,
                "section_path": section_path,
                "hierarchy_path": section_path + [row.section],
            })
            by_id[row.chunk_id] = row.model_copy(update={"metadata": row_metadata})

    return [by_id[chunk.chunk_id] for chunk in updated], new_parents


def _page_bucket(page_num: int | None) -> int:
    page = max(1, int(page_num or 1))
    return (page - 1) // TEXT_PARENT_PAGE_SPAN


def _text_section_title(children: list[Any]) -> str:
    pages = [child.page_num for child in children if child.page_num is not None]
    if not pages:
        return "Document section"
    return f"Pages {min(pages)}-{max(pages)}"


def _source_label(chunk: Any) -> str:
    metadata = chunk.metadata
    return str(metadata.get("source") or metadata.get("source_pdf_name") or metadata.get("title") or chunk.doc_id)


def _section_summary_content(title: str, children: list[Any]) -> str:
    body = "\n\n".join(child.content for child in children).strip()
    if len(body) > SECTION_SUMMARY_CHAR_LIMIT:
        body = body[:SECTION_SUMMARY_CHAR_LIMIT].rstrip() + " ...[truncated]"
    return f"Section: {title}\n\n{body}".strip()


def _table_key(chunk: Any) -> str:
    metadata = chunk.metadata
    for key in ("table_id", "table_title", "section_title", "source", "source_pdf_name"):
        value = metadata.get(key)
        if value:
            return str(value)
    return chunk.section


def _parent_id(doc_id: str, seed: str) -> str:
    return f"{doc_id}-sbf-{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _print_summary(
    original_chunks: list[Any],
    updated_chunks: list[Any],
    existing_extra_chunks: list[Any],
    new_parents: list[Any],
    provenance: dict[str, Any],
) -> None:
    parent_links = sum(1 for chunk in updated_chunks if chunk.metadata.get("parent_id"))
    parents = sum(1 for chunk in updated_chunks + new_parents if chunk.metadata.get("child_ids"))
    print(f"processed_chunks={len(updated_chunks)}")
    print(f"existing_extra_chunks={len(existing_extra_chunks)}")
    print(f"new_parent_chunks={len(new_parents)}")
    print(f"parent_links={parent_links}")
    print(f"parents_with_children={parents}")
    print(f"existing_chunks_preserved={len(original_chunks)}")
    print(f"vector_provenance={provenance}")


if __name__ == "__main__":
    raise SystemExit(main())
