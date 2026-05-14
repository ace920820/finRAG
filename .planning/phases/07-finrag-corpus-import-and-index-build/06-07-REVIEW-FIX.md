# Phase 6–7 Review Fix Summary

Fix date: 2026-05-14
Source review: `.planning/phases/07-finrag-corpus-import-and-index-build/06-07-REVIEW.md`

## Fixed

- Added empty-import protection so `import_corpus()` fails before touching `documents.json` or `chunks.json` when no raw inputs are discovered.
- Added safe collection-name validation in backend raw discovery to reject path traversal values like `../outside`.
- Stopped broad raw discovery from recursively scanning the entire `raw_root`; it now scans only `extracted/` and `manual/` when no collection/source is specified.
- Excluded `_meta` paths from raw input discovery so generated manifest Markdown is not imported as a document.
- Updated `build_index.py` to set env vars and clear settings caches instead of mutating an already-created settings object.
- Added regression tests for empty import preservation, unsafe collection names, and `_meta` manifest exclusion.

## Local Ignored Helper Updates

- The ignored local `pdf2md/` helper copy was also updated and tested for unsafe FinRAG collection names.
- Because root `.gitignore` ignores `pdf2md/`, those helper-copy edits are not part of normal git status unless force-added intentionally.

## Tests

- `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_import_pipeline_integration.py tests/test_retrieval_index.py`
- `cd pdf2md && python3 -m pytest tests/test_finrag_adapter.py tests/test_config.py`

## Notes

- Backend tests pass with existing PyMuPDF/SWIG deprecation warnings.
