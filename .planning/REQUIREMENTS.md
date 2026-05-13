# Requirements: FinRAG

**Defined:** 2026-05-13  
**Core Value:** Financial users receive structured, cited, source-grounded RAG analysis through a stable backend contract that the imported React frontend can consume.

## v1 Requirements

### Backend Foundation

- [x] **BACK-01**: Backend can start a FastAPI app locally at `http://localhost:8000`.
- [x] **BACK-02**: Backend defines Pydantic models for Document, Chunk, query requests, document responses, and SSE events.
- [x] **BACK-03**: Backend centralizes configuration for API keys, provider selection, data paths, rerank fallback, and demo mode.
- [x] **BACK-04**: Backend test suite can run without external API calls by using mock providers and fixture data.

### Data Pipeline

- [x] **DATA-01**: Developer can seed at least 2 annual reports, 1 research report, and 5-10 news items for the demo corpus.
- [x] **DATA-02**: Ingestion normalizes raw financial documents into the required Document schema.
- [x] **DATA-03**: Chunking creates section-aware financial-report chunks, semantic research-report chunks, and whole-news chunks.
- [x] **DATA-04**: Chunk metadata preserves company, aliases, document type, date, source, page, and section for citations.
- [x] **DATA-05**: Critical demo facts can be loaded from curated JSON fallback data when PDF extraction is unreliable.

### Retrieval And Rerank

- [x] **RETR-01**: Backend can build and load a FAISS vector index for demo chunks.
- [x] **RETR-02**: Backend can build and load a BM25 index with Chinese tokenization.
- [x] **RETR-03**: Hybrid retrieval returns vector Top 20, BM25 Top 20, and fused Top 20 candidate lists.
- [x] **RETR-04**: Fusion uses RRF with configurable `k=60` or a documented weighted-score fallback.
- [x] **RETR-05**: Rerank returns Top 5 chunks with score, rank, full content, and citation IDs.
- [x] **RETR-06**: Rerank gracefully falls back to fused Top 5 when the rerank provider fails.

### Agent Workflow

- [x] **AGNT-01**: Query rewrite expands detected company aliases for Guizhou Moutai and CATL demo queries.
- [x] **AGNT-02**: Query rewrite can return sub-queries for complex macro-to-sector reasoning questions.
- [x] **AGNT-03**: Intent classification labels queries as `factual`, `analytical`, or `reasoning`.
- [x] **AGNT-04**: Workflow emits lifecycle events in order: query rewrite, retrieval, rerank, optional intent, answer chunks, done or error.
- [x] **AGNT-05**: Prompt templates enforce factual, analytical, and reasoning Markdown structures.
- [x] **AGNT-06**: Generation refuses unsupported claims with “资料中未提及” instead of hallucinating.

### API Contract

- [x] **API-01**: `GET /api/documents` returns total count and document metadata for the left sidebar.
- [x] **API-02**: `POST /api/query` accepts query and optional session ID and responds as `text/event-stream`.
- [x] **API-03**: SSE `query_rewrite` event includes original query, expanded terms, and sub-queries.
- [x] **API-04**: SSE `retrieval_complete` event includes BM25, vector, and fused result arrays.
- [x] **API-05**: SSE `rerank_complete` event includes Top 5 chunks with citation IDs.
- [x] **API-06**: SSE `answer_chunk` events stream Markdown text fragments.
- [x] **API-07**: SSE `done` event includes latency, token count, and citation metadata.
- [x] **API-08**: SSE `error` event includes machine-readable code and user-facing message.
- [x] **API-09**: SSE heartbeat sends `ping` at least every 15 seconds during long-running queries.
- [x] **API-10**: Optional `POST /api/preview-rewrite` returns expanded terms and detected entities.

### Integration And Demo

- [x] **INTG-01**: Imported React frontend can call backend through `/api` without contract changes.
- [x] **INTG-02**: Three demo questions complete end-to-end with streamed stage updates and final cited answers.
- [x] **INTG-03**: Contract tests verify frontend-facing response shapes and SSE event payloads.
- [x] **INTG-04**: Demo mode can run with cached or mock provider responses if external APIs fail.
- [x] **INTG-05**: Error handling supports retryable provider failures and surfaces clear frontend messages.
- [x] **INTG-06**: Frontend adapters replace mock RAG flow with backend `/api/query` SSE while preserving existing UI state shapes.
- [x] **INTG-07**: Frontend document library maps `GET /api/documents` into the existing left sidebar display.
- [x] **INTG-08**: Frontend retrieval panels map backend `retrieval_complete` and `rerank_complete` payloads into existing right sidebar cards.

## v2 Requirements

### Quality Enhancements

- **QUAL-01**: Lightweight numeric consistency check flags answer numbers not present in retrieved chunks.
- **QUAL-02**: Entity extraction stores mentioned companies in chunk metadata.
- **QUAL-03**: Time-sensitive rerank applies configurable recency decay.
- **QUAL-04**: Frontend query rewrite preview is fully enabled and debounced. *(Implemented in Phase 5)*

### Future Architecture

- **FUTR-01**: Incremental indexing updates changed documents without full rebuild.
- **FUTR-02**: Knowledge graph relations support multi-hop financial reasoning.
- **FUTR-03**: Larger corpus management supports 100k-level chunks with persistence strategy.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full React UI implementation | Owned by another team; this project handles integration and tests. |
| Authentication | Not needed for interview demo MVP. |
| Production deployment | Two-day demo scope prioritizes local reliability. |
| User-editable document library | Demo document list is read-only. |
| Real-time market data ingestion | Not required by the supplied demo questions. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BACK-01 | Phase 1 | Complete |
| BACK-02 | Phase 1 | Complete |
| BACK-03 | Phase 1 | Complete |
| BACK-04 | Phase 1 | Complete |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 1 | Complete |
| RETR-01 | Phase 2 | Complete |
| RETR-02 | Phase 2 | Complete |
| RETR-03 | Phase 2 | Complete |
| RETR-04 | Phase 2 | Complete |
| RETR-05 | Phase 2 | Complete |
| RETR-06 | Phase 2 | Complete |
| AGNT-01 | Phase 3 | Complete |
| AGNT-02 | Phase 3 | Complete |
| AGNT-03 | Phase 3 | Complete |
| AGNT-04 | Phase 3 | Complete |
| AGNT-05 | Phase 3 | Complete |
| AGNT-06 | Phase 3 | Complete |
| API-01 | Phase 1 | Complete |
| API-02 | Phase 3 | Complete |
| API-03 | Phase 3 | Complete |
| API-04 | Phase 2 | Complete |
| API-05 | Phase 2 | Complete |
| API-06 | Phase 3 | Complete |
| API-07 | Phase 3 | Complete |
| API-08 | Phase 3 | Complete |
| API-09 | Phase 3 | Complete |
| API-10 | Phase 5 | Complete |
| INTG-01 | Phase 4 | Complete |
| INTG-02 | Phase 4 | Complete |
| INTG-03 | Phase 4 | Complete |
| INTG-04 | Phase 4 | Complete |
| INTG-05 | Phase 4 | Complete |
| INTG-06 | Phase 4 | Complete |
| INTG-07 | Phase 4 | Complete |
| INTG-08 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 38 total
- Mapped to phases: 38
- Unmapped: 0

---
*Requirements defined: 2026-05-13*  
*Last updated: 2026-05-13 after phase 5 completion*
