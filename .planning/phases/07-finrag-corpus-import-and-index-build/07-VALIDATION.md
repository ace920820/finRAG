# Phase 7 Validation Checklist

**Created:** 2026-05-13  
**Updated:** 2026-05-13  
**Status:** Passed

## Goal-Backward Validation

Phase 7 is complete because a developer can add raw Markdown/text, run a documented import/index command sequence, and have existing FinRAG APIs/query retrieval operate on the imported corpus without frontend redesign.

## Evidence

- `backend/app/data/raw/` is documented as the canonical raw input location.
- `backend/scripts/import_corpus.py` converts Phase 6 Markdown and manual Markdown/text into schema-compatible `documents.json` and `chunks.json`.
- Generated document and chunk IDs are deterministic across repeated imports with unchanged content.
- Metadata preservation covers title, source, date, company, doc type, page marker, collection, source path/name, and original frontmatter.
- `backend/scripts/build_index.py` supports explicit processed/index paths and writes BM25/vector indexes.
- Existing fixture/demo path remains available through `backend/scripts/seed_data.py`.
- Integration tests prove `GET /api/documents` and hybrid retrieval work against imported corpus data.
- Tests use mock/local providers; no Alibaba Bailian API key is required.

## Validation Commands Run

```bash
cd backend && python3 -m pytest tests/test_corpus_import.py
# 4 passed
```

```bash
cd backend && python3 -m pytest tests/test_import_pipeline_integration.py
# 2 passed
```

```bash
cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_import_pipeline_integration.py tests/test_retrieval_index.py tests/test_documents_api.py tests/test_hybrid_retrieval.py
# 11 passed
```

Full backend validation:

```bash
cd backend && python3 -m pytest
# 35 passed
```

## Output Contract

Raw inputs:

- `backend/app/data/raw/extracted/<collection-name>/*.md`
- `backend/app/data/raw/manual/<collection-name>/*.{md,txt}`

Generated outputs:

- `backend/app/data/processed/documents.json`
- `backend/app/data/processed/chunks.json`
- `backend/app/data/index/bm25_index.json`
- `backend/app/data/index/vector_index.json`

## Out Of Scope Checks

- OCR was not added.
- Frontend UI was not redesigned.
- No production ingestion service was added.
- Tests do not require live model credentials.
