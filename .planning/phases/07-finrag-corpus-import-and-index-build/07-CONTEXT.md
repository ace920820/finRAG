# Phase 7 Context: FinRAG Corpus Import And Index Build

**Created:** 2026-05-13  
**Status:** Ready for planning

## Phase Goal

Add a FinRAG-side local import pipeline that converts Phase 6 raw Markdown/text artifacts into existing backend `Document` and `Chunk` schemas, writes deterministic `documents.json` and `chunks.json`, rebuilds retrieval indexes, and keeps the existing frontend/backend query flow stable.

## Locked Decisions

- Import pipeline lives in the backend/FinRAG project, not inside `pdf2md`.
- Canonical raw data location for this milestone is `backend/app/data/raw/`.
- Generated processed data continues to use `backend/app/data/processed/documents.json` and `backend/app/data/processed/chunks.json` so existing APIs and retrieval code keep working.
- Existing demo fixture path must remain available as fallback and for deterministic tests.
- Phase 7 should support both Phase 6 Markdown output and manually supplied `.md` / `.txt` files.
- Index rebuild should use the existing retrieval index mechanism where possible instead of introducing a new index format.
- No frontend redesign or API contract redesign; frontend should see imported documents through existing `GET /api/documents`.
- Provider credentials are not required for tests; mock embedding path must remain usable.

## Requirements Covered

- `ING-01`: document raw data location.
- `ING-02`: convert Markdown/text into `documents.json` and `chunks.json` using existing schemas.
- `ING-03`: preserve title/source/date/company/doc type metadata when available.
- `ING-04`: deterministic document/chunk IDs across unchanged imports.
- `ING-05`: support PDF-derived Markdown and manual Markdown/text.
- `ING-06`: rebuild retrieval indexes after import.
- `ING-07`: keep demo fixture fallback and deterministic tests.
- `ING-08`: tests for sample import and JSON shape.
- `PIPE-01`: documented extraction → import → index build command sequence.
- `PIPE-02`: docs explain how to add PDFs and rebuild corpus.
- `PIPE-03`: imported documents flow through existing `GET /api/documents`.
- `PIPE-04`: query flow retrieves imported chunks after index rebuild.

## Canonical References

- `backend/app/models/schemas.py` — existing `Document` and `Chunk` schema contracts.
- `backend/app/core/ingestion/fixture_loader.py` — current processed JSON loading path.
- `backend/app/core/ingestion/normalizer.py` — normalization into Pydantic models.
- `backend/scripts/build_index.py` — existing retrieval index build script.
- `backend/app/core/retrieval/index_store.py` — load/build/save index implementation.
- `backend/app/core/retrieval/bm25_store.py` — BM25 payload expectations.
- `backend/app/core/retrieval/vector_store.py` — vector index payload expectations.
- `backend/app/api/documents.py` — document library API that must remain stable.
- `pdf2md/README.md` — Phase 6 FinRAG raw output contract.
- `.planning/phases/06-pdf-extraction-adapter/06-VALIDATION.md` — raw Markdown/manifest contract for Phase 7.

## Existing Data Shape

Current backend reads:

- `backend/app/data/processed/documents.json`
- `backend/app/data/processed/chunks.json`
- `backend/app/data/processed/demo_cases.json`
- `backend/app/data/index/bm25_index.json`
- `backend/app/data/index/vector_index.json`

`Document` requires `doc_id`, `company`, `company_aliases`, `doc_type`, `title`, `date`, `source`, `content`.

`Chunk` requires `chunk_id`, `doc_id`, `section`, optional `page_num`, `chunk_index`, `content`, optional `embedding`, and `metadata`.

## Implementation Assumptions

- If metadata is missing, importer should use safe defaults: company `未知`, doc_type `research_report`, date `unknown`, source from file path/name.
- Metadata can come from YAML frontmatter, simple filename heuristics, or optional CLI/default flags.
- Deterministic IDs should derive from stable source identity and content hashes, not timestamps.
- Chunking can be simple paragraph/length based for v1.1; avoid semantic splitting complexity until real corpus quality demands it.
- Rebuild index can invalidate old index files by overwriting them from newly generated chunks.

## Out Of Scope

- OCR and PDF extraction changes.
- Frontend UI redesign.
- Production ingestion UI or background jobs.
- Advanced financial table reconstruction.
- Incremental vector updates.
