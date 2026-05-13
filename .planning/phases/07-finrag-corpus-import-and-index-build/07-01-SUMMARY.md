---
phase: 07-finrag-corpus-import-and-index-build
plan: 01
subsystem: corpus-import-core
tags: [ingestion, chunking, processed-json]
key-files:
  - backend/app/core/ingestion/raw_loader.py
  - backend/app/core/ingestion/chunker.py
  - backend/app/core/ingestion/corpus_importer.py
  - backend/tests/test_corpus_import.py
metrics:
  tests: 4 passed
---

# Plan 07-01 Summary: Corpus Import Core

## Completed

- Added raw `.md`/`.txt` discovery and parsing for Phase 6 Markdown and manual supplements.
- Added frontmatter parsing and `## Extracted Text` body extraction.
- Added deterministic page-aware chunking.
- Added schema-compatible `Document` and `Chunk` generation with deterministic IDs.
- Added processed JSON writing for `documents.json` and `chunks.json`.
- Added unit tests for parsing, discovery, chunking, deterministic import, and schema validation.

## Deviations

- Kept chunking intentionally simple and deterministic rather than adding semantic splitting.

## Self-Check

PASSED — `cd backend && python3 -m pytest tests/test_corpus_import.py`.
