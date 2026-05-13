# Phase 7 Research: FinRAG Corpus Import And Index Build

**Created:** 2026-05-13  
**Status:** Ready for planning

## Research Goal

Find the smallest safe backend pipeline that turns Phase 6 raw Markdown/text artifacts into existing FinRAG processed data and indexes without disturbing the v1.0 query/frontend flow.

## Inputs Reviewed

- `.planning/REQUIREMENTS.md` — Phase 7 `ING-*` and `PIPE-*` requirements.
- `.planning/ROADMAP.md` — Phase 7 goal and success criteria.
- `.planning/STATE.md` — Phase 6 completion and current milestone state.
- `.planning/phases/06-pdf-extraction-adapter/06-VALIDATION.md` — raw Markdown output contract.
- `pdf2md/README.md` — `--profile finrag` usage and raw directory layout.
- `backend/app/models/schemas.py` — existing document/chunk schemas.
- `backend/app/core/ingestion/fixture_loader.py` — current loader for processed JSON.
- `backend/scripts/build_index.py` — current index build entrypoint.
- `backend/app/core/retrieval/index_store.py` — retrieval index build/save behavior.
- `backend/tests/test_retrieval_index.py` and `backend/tests/test_seed_data.py` — existing validation patterns.

## Recommended Technical Approach

### 1. Add Backend Import Modules

Create small ingestion modules under `backend/app/core/ingestion/`:

- `raw_loader.py` — discovers raw `.md` and `.txt` inputs, parses frontmatter and source text.
- `chunker.py` — deterministic paragraph/length chunking with page marker awareness.
- `corpus_importer.py` — maps raw records into `Document` and `Chunk` dictionaries/Pydantic models and writes processed JSON.

Keep code pure and testable; CLI should be a thin wrapper.

### 2. Add Import CLI Script

Add `backend/scripts/import_corpus.py` with arguments such as:

- `--raw-root backend/app/data/raw`
- `--processed-dir backend/app/data/processed`
- `--collection-name research-reports` optional
- `--source-dir` optional direct Markdown/text input
- metadata defaults like `--default-company`, `--default-doc-type`, `--default-date`
- `--rebuild-index` to call/trigger index rebuild after writing processed JSON

The script should be local and deterministic, not a web API.

### 3. Keep Existing Runtime Contract

Since existing APIs and retrieval load `processed/*.json`, importing should write the same files rather than changing runtime loaders in this phase. After import and index rebuild, existing `GET /api/documents` and query flow should work unchanged.

### 4. Preserve Fixture Safety

Do not delete fixture generator or demo cases. Tests should use temporary raw/processed/index directories where possible, and existing demo data should remain usable by `scripts/seed_data.py`.

### 5. Deterministic IDs And Metadata

Generate `doc_id` from normalized source path/name plus content hash. Generate `chunk_id` from `doc_id`, chunk index, and chunk content hash. Preserve frontmatter fields in `Chunk.metadata`.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Import overwrites demo data during tests | Use temp dirs and CLI arguments in tests; keep seed script unchanged. |
| Metadata missing in raw files | Use documented defaults and preserve available source fields. |
| Chunking is too complex | Start with deterministic paragraph/length chunking and page marker extraction. |
| Index rebuild uses stale index files | Overwrite `bm25_index.json` and `vector_index.json` after import. |
| Live embeddings required | Keep mock provider/default test path; do not require Bailian credentials. |

## Suggested Plan Split

1. **Importer core and tests** — raw loader, metadata parsing, deterministic chunk/document generation, JSON writing.
2. **Index rebuild and integration tests** — import CLI, build-index support for custom dirs or settings, `GET /api/documents`/retrieval validation.
3. **Docs and milestone state** — document extraction → import → index commands, UAT, requirement/status updates.
