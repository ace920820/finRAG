# Requirements: FinRAG v1.3 Knowledge Base Management

**Milestone:** v1.3 Knowledge Base Management  
**Last updated:** 2026-05-13

## Goal

Add a lightweight knowledge base management capability to FinRAG so the demo can manage documents, trigger import/reindex operations, and integrate the externally built React management page into the existing single frontend app.

## Active Requirements

| ID | Requirement | Priority | Acceptance Criteria |
| --- | --- | --- | --- |
| REQ-v1.3-001 | Single-app knowledge base page integration | Must | The React management page from `finrag-knowledge-base-manager/` is integrated under `frontend/`; the existing app exposes a “知识库管理” entry from the chat header; switching pages does not require running a second frontend project. |
| REQ-v1.3-002 | Knowledge base overview API | Must | Backend exposes an overview endpoint returning document count, chunk count, last import/reindex timestamps, and status for direct page rendering. |
| REQ-v1.3-003 | Knowledge base document APIs | Must | Backend exposes document list/detail endpoints with search/filter-ready fields, chunk counts, status, source path, and error message fields. |
| REQ-v1.3-004 | Upload and import task APIs | Must | Backend supports uploading PDF/MD/TXT files, creating import jobs, polling job status, and preserving failure details without blocking successful files. |
| REQ-v1.3-005 | Reindex and document maintenance APIs | Must | Backend supports full reindex, single-document reimport, and soft disable/delete semantics compatible with the existing corpus/index files. |
| REQ-v1.3-006 | Frontend-backend integration | Must | The integrated management page calls real `/api/kb/*` endpoints, handles loading/error states, and falls back only where endpoints are intentionally pending during development. |
| REQ-v1.3-007 | Regression-safe existing demo | Must | Existing `GET /api/documents`, `POST /api/query`, `POST /api/preview-rewrite`, SSE streaming, and document opening flows continue to work. |
| REQ-v1.3-008 | Backend tests and integration smoke checks | Should | Targeted backend tests cover KB schemas/endpoints/job state; frontend type/build checks pass after page integration. |
| REQ-v1.3-009 | Table-aware PDF extraction | Must | PDF pipeline extracts table objects alongside text, preserving page, title/caption when available, headers, rows, Markdown representation, CSV/JSON artifacts, and a table manifest; extraction failure degrades to text-only without breaking existing import. |
| REQ-v1.3-010 | Table chunk data model | Must | Backend corpus supports `chunk_type` values for `text`, `table`, `table_row`, and `table_summary`; table chunks preserve metadata such as company, ticker, doc_type, report_period, page, table_id, table_title, statement_type, unit, currency, row_count, column_count, and source_pdf. |
| REQ-v1.3-011 | Table-aware retrieval and rerank | Must | Retrieval indexes table summaries/Markdown/row facts in addition to text chunks; numeric/metric queries such as revenue, net income, YoY, and latest quarter route table evidence into rerank/top citations. |
| REQ-v1.3-012 | Structured financial facts store | Should | Core financial statement rows are normalized into a local JSON/SQLite-style facts store with company, ticker, period, statement, metric, value, unit, currency, page, and source_pdf fields for deterministic numeric answers. |
| REQ-v1.3-013 | Table evidence API and frontend integration | Should | Query responses and debug retrieval expose table evidence metadata so the chat UI can distinguish table citations from normal text citations without redesigning the frontend. |

## Table-Aware RAG Scope

The table-aware work is based on `docs/table处理.txt`. It should preserve table structure instead of relying only on plain PDF text extraction. The implementation should remain demo-oriented: prioritize financial statement tables and clear metric queries before attempting broad OCR, chart extraction, or production-grade table understanding.

## Non-Goals

- No new visual redesign of the management page beyond minimal integration affordances.
- No multi-user permissions, approval workflow, or complex version control.
- No production-grade distributed task queue; an in-process/local job model is acceptable for the demo.
- No OCR unless explicitly added in a future milestone.
- No chart extraction in the table-aware phase set; charts can be added later.

## Source Documents

- `docs/知识库管理PRD.md`
- `docs/知识库管理接口清单.md`
- `docs/知识库管理GSD需求说明.md`
- `docs/table处理.txt`
