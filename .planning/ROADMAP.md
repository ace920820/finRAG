# Roadmap: FinRAG v1.1 Document Import Pipeline

**Created:** 2026-05-13  
**Granularity:** Coarse  
**Primary emphasis:** Real document ingestion, PDF extraction reuse, deterministic chunking, and index rebuild.

## Prior Milestone

v1.0 delivered the mock-data FinRAG MVP: FastAPI backend, hybrid retrieval/rerank, SSE query API, React integration, and preview rewrite. The user has passed smoke testing with mock data.

## Overview

| Phase | Name | Goal | Requirements | UI Hint | Status |
|-------|------|------|--------------|---------|--------|
| 6 | PDF Extraction Adapter | Adapt the provided `pdf2md` project so FinRAG can extract text-layer PDFs into traceable Markdown/raw artifacts. | PDF-01..05 | no | Complete |
| 7 | FinRAG Corpus Import And Index Build | Convert extracted Markdown/text into FinRAG documents/chunks, rebuild indexes, and document the ingestion workflow. | ING-01..08, PIPE-01..04 | no | Complete |

## Phase Details

### Phase 6: PDF Extraction Adapter

**Status:** Complete — implemented in `pdf2md` with `--profile finrag`, validated by `cd pdf2md && python3 -m pytest` on 2026-05-13.

**Goal:** Reuse and adapt `pdf2md` for FinRAG source PDFs without Elite Daily-specific assumptions blocking generic financial documents.

**Requirements:** PDF-01, PDF-02, PDF-03, PDF-04, PDF-05

**Success Criteria:**
1. `pdf2md` can process a FinRAG raw PDF directory or single PDF into Markdown/raw outputs.
2. Outputs preserve source path/name, title, extraction status, page count, hashes, and failure records.
3. Re-runs skip unchanged files unless forced.
4. Failed PDFs are recorded without aborting the batch.
5. The output location can target a FinRAG-owned data directory.

**Notes:** Follow `pdf2md/AGENTS.md` for files under `pdf2md/`. Do not introduce OCR in this phase.

### Phase 7: FinRAG Corpus Import And Index Build

**Status:** Complete — importer, CLI, index rebuild, docs, and integration tests implemented on 2026-05-13.

**Goal:** Add a FinRAG-side import pipeline that turns extracted Markdown/text into `documents.json`, `chunks.json`, and rebuilt retrieval indexes.

**Requirements:** ING-01, ING-02, ING-03, ING-04, ING-05, ING-06, ING-07, ING-08, PIPE-01, PIPE-02, PIPE-03, PIPE-04

**Success Criteria:**
1. Raw document locations and import commands are documented.
2. Import script creates schema-compatible `documents.json` and `chunks.json` from Markdown/text inputs.
3. Chunking is deterministic and preserves title/source/date/company/doc type metadata when available.
4. Import can rebuild BM25/vector indexes and the existing query flow retrieves imported chunks.
5. Existing demo fixtures remain usable for tests/fallback.
6. Tests cover sample import, JSON shape validation, and index build integration.

## Dependency Map

- Phase 6 provides text-layer extraction artifacts for PDFs.
- Phase 7 depends on Phase 6 outputs but should also support manually supplied Markdown/text.
- Existing v1.0 query and frontend flows depend only on generated `processed` data and rebuilt indexes, so they should continue to work after import.

## Coverage Validation

- v1.1 requirements mapped: 17 / 17
- Unmapped v1.1 requirements: 0
- Frontend redesign intentionally excluded; imported documents should flow through existing `GET /api/documents`.

---
*Last updated: 2026-05-13 after starting document import pipeline milestone*
