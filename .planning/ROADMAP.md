# Roadmap: FinRAG v1.3 Knowledge Base Management

**Last updated:** 2026-05-13  
**Current status:** Phase 14 table-aware extraction complete; Phase 15 table chunking/facts pending.

## Shipped Milestones

| Milestone | Name | Status | Phases | Summary | Archive |
| --- | --- | --- | --- | --- | --- |
| v1.0 | Mock-data MVP | Shipped | 1-5 | FastAPI backend, hybrid retrieval/rerank, SSE query API, React integration, preview rewrite, and mock-data demo readiness. | Prior phase artifacts in `.planning/phases/01-*` through `.planning/phases/05-*` |
| v1.1 | Document Import Pipeline | Shipped | 6-7 | PDF/text-layer extraction, raw Markdown artifacts, FinRAG corpus import, deterministic chunking, and retrieval index rebuild. | `.planning/milestones/v1.1-ROADMAP.md` |
| v1.2 | Frontend Evidence Traceability & Interaction Polish | Complete | 8-10 | Real-corpus examples, document open action, retrieval panel polish, and per-turn evidence traceability. | Pending milestone archive |

## Current Milestone

### v1.3 Knowledge Base Management

Goal: Add a lightweight knowledge base management page and backend API surface for document import, indexing, and maintenance while keeping FinRAG as one frontend app.

| Phase | Name | Requirements | Goal | Validation |
| --- | --- | --- | --- | --- |
| 11 | Single-App Management Page Integration | REQ-v1.3-001, REQ-v1.3-007, REQ-v1.3-008 | Merge the external knowledge base manager React page into `frontend/` and add a chat-header entry without running a second frontend app. | ✓ Complete |
| 12 | KB Backend API Foundation | REQ-v1.3-002, REQ-v1.3-003, REQ-v1.3-007, REQ-v1.3-008 | Implement `/api/kb/overview`, `/api/kb/documents`, and `/api/kb/documents/{doc_id}` over the existing processed corpus and chunk data. | ✓ Complete |
| 13 | KB Import, Reindex, and Frontend联调 | REQ-v1.3-004, REQ-v1.3-005, REQ-v1.3-006, REQ-v1.3-007, REQ-v1.3-008 | Implement upload/import/job/reindex/maintenance APIs and wire the management page to real backend endpoints. | ✓ Complete |
| 14 | Table-Aware PDF Extraction | REQ-v1.3-009, REQ-v1.3-010 | Extend PDF/raw extraction to emit structured table artifacts, table manifests, and table-aware raw metadata alongside existing text extraction. | Complete |
| 15 | Table Chunking And Structured Facts | REQ-v1.3-010, REQ-v1.3-012 | Add `text`/`table`/`table_row`/`table_summary` chunk types and normalize core financial statement metrics into a local structured facts store. | Pending |
| 16 | Table-Aware Retrieval And QA Integration | REQ-v1.3-011, REQ-v1.3-013, REQ-v1.3-007, REQ-v1.3-008 | Route numeric/metric questions through table-aware retrieval/facts, expose table evidence in citations/debug APIs, and verify financial table answers. | Pending |

## Phase Details

### Phase 11 — Single-App Management Page Integration

**Purpose:** Consolidate the externally built management frontend into the existing FinRAG Vite app.

**Likely files:**
- `frontend/src/App.tsx`
- `frontend/src/components/Header.tsx`
- `frontend/src/pages/KnowledgeBaseManager.tsx`
- `frontend/src/pages/knowledgeBaseTypes.ts`

**Success criteria:**
- Existing chat screen has a “知识库管理” button in the header.
- Clicking it opens the manager page inside the same frontend runtime.
- The manager page has a “返回对话” path back to the chat screen.
- No second frontend dev server is required.

### Phase 12 — KB Backend API Foundation

**Purpose:** Provide read-only KB management APIs first, using the existing corpus outputs.

**Likely files:**
- `backend/app/api/kb.py`
- `backend/app/main.py`
- `backend/app/models/schemas.py`
- `backend/app/core/ingestion/fixture_loader.py`
- `backend/tests/test_kb_api.py`

**Success criteria:**
- Overview returns total documents/chunks and status.
- Document list supports basic search/filter parameters.
- Document detail returns metadata and representative chunk summaries.
- Existing `/api/documents` remains unchanged.

### Phase 13 — KB Import, Reindex, and Frontend联调

**Purpose:** Complete the management write flows and replace mock frontend data with real API calls.

**Likely files:**
- `backend/app/api/kb.py`
- `backend/app/core/ingestion/corpus_importer.py`
- `backend/app/core/retrieval/index_store.py`
- `frontend/src/api/kb.ts`
- `frontend/src/pages/KnowledgeBaseManager.tsx`
- `backend/tests/test_kb_import_api.py`

**Success criteria:**
- File upload accepts PDF/MD/TXT and saves to raw/manual collection paths.
- Import creates a trackable job and can optionally rebuild indexes.
- Job polling returns success/failure counts and errors.
- Reindex and single-document maintenance actions are wired to UI actions.
- Existing chat/query demo still works after management operations.


### Phase 14 — Table-Aware PDF Extraction

**Purpose:** Stop treating all PDF table content as plain text by extracting table objects during the raw PDF processing stage.

**Likely files:**
- `pdf2md/src/elite_daily_pdf_to_md/extraction.py`
- `pdf2md/src/elite_daily_pdf_to_md/finrag.py`
- `pdf2md/src/elite_daily_pdf_to_md/output.py`
- `backend/app/data/raw/tables/` generated artifacts
- `pdf2md/tests/test_finrag_adapter.py`

**Success criteria:**
- FinRAG PDF extraction emits Markdown text exactly as before plus table JSON/CSV/manifest artifacts.
- Each table artifact preserves page, inferred title/caption when possible, headers, rows, Markdown table rendering, row/column counts, and source PDF metadata.
- Extraction remains idempotent and degrades to text-only when table extraction fails.
- The existing 40-PDF corpus can be reprocessed without reducing current document/chunk availability.

### Phase 15 — Table Chunking And Structured Facts

**Purpose:** Import table artifacts into backend corpus/index data as first-class evidence instead of plain text only.

**Likely files:**
- `backend/app/models/schemas.py`
- `backend/app/core/ingestion/corpus_importer.py`
- `backend/app/core/ingestion/chunker.py`
- `backend/app/core/ingestion/raw_loader.py`
- `backend/tests/test_corpus_import.py`
- `backend/tests/test_import_pipeline_integration.py`

**Success criteria:**
- Chunks support `chunk_type` values: `text`, `table`, `table_row`, `table_summary`.
- Table chunk metadata includes table id/title, page, statement type, unit/currency, row/column counts, company/ticker/doc/report-period/source PDF.
- Financial statement rows such as revenue, gross profit, operating income, net income, EPS are normalized into a local structured facts JSON store.
- Existing text chunks and document APIs remain backward compatible.

### Phase 16 — Table-Aware Retrieval And QA Integration

**Purpose:** Make financial numeric questions retrieve and cite structured table evidence reliably.

**Likely files:**
- `backend/app/core/retrieval/hybrid.py`
- `backend/app/core/retrieval/rerank_service.py`
- `backend/app/core/agent/workflow.py`
- `backend/app/models/events.py`
- `backend/tests/test_hybrid_retrieval.py`
- `backend/tests/test_query_api.py`
- `frontend/src/types.ts` only if table citation metadata needs a type update.

**Success criteria:**
- Queries like “英伟达2026年第三季度的总营收是多少？” prioritize table evidence and can return deterministic table facts.
- Debug retrieval and query SSE expose enough metadata to show table citations distinctly.
- Existing text RAG, KB management APIs, and frontend build remain green.
- Tests cover at least NVIDIA revenue, Moutai revenue/net profit, and one TSMC financial table query.

## Next Action

Plan or execute Phase 15 for table chunking and structured facts.
