# Roadmap: FinRAG

**Created:** 2026-05-13  
**Granularity:** Coarse  
**Primary emphasis:** Backend implementation, automated tests, and frontend-backend integration

## Overview

| Phase | Name | Goal | Requirements | UI Hint | Status |
|-------|------|------|--------------|---------|--------|
| 1 | Backend Foundation And Demo Data | Establish runnable FastAPI backend, schemas, document endpoint, and deterministic demo data pipeline. | BACK-01..04, DATA-01..05, API-01 | no | Pending |
| 2 | Hybrid Retrieval And Rerank | Build BM25/vector retrieval, RRF fusion, rerank Top 5, and degradation path. | RETR-01..06, API-04, API-05 | no | Pending |
| 3 | Agent Workflow And SSE Query API | Orchestrate rewrite, retrieval, rerank, intent, LLM streaming, citations, errors, and heartbeat events. | AGNT-01..06, API-02, API-03, API-06..09 | no | Complete |
| 4 | Integration And Demo Hardening | Validate imported React frontend against contract and stabilize three demo scenarios with fallbacks. | INTG-01..08 | yes | Pending |
| 5 | P1 Enhancements | Add optional rewrite preview and polish financial-specific quality improvements as time allows. | API-10, selected v2 quality items | partial | Pending |

## Phase Details

### Phase 1: Backend Foundation And Demo Data

**Goal:** Create the backend skeleton and deterministic data foundation needed by all later phases.

**Requirements:** BACK-01, BACK-02, BACK-03, BACK-04, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, API-01

**Success Criteria:**
1. `backend` FastAPI app starts locally and exposes health/document endpoints.
2. Pydantic schemas cover all document, chunk, API, and SSE payload contracts.
3. Seed/build scripts can create processed demo data for the three target questions.
4. Unit tests pass without external API keys.
5. Critical financial facts have a curated fallback path independent of PDF parsing quality.

**Notes:** This phase should not build frontend UI. It may include OpenAPI/schema examples for the frontend team.

### Phase 2: Hybrid Retrieval And Rerank

**Goal:** Make evidence retrieval observable, testable, and suitable for frontend visualization.

**Requirements:** RETR-01, RETR-02, RETR-03, RETR-04, RETR-05, RETR-06, API-04, API-05

**Success Criteria:**
1. BM25 and vector stores can be built from demo chunks and queried independently.
2. Hybrid retrieval returns separate BM25, vector, and fused candidate arrays.
3. RRF scoring is deterministic and covered by unit tests.
4. Rerank returns Top 5 chunk payloads with ranks, scores, content, metadata, and citation IDs.
5. Rerank provider failure returns a documented fallback Top 5 instead of breaking the query flow.

### Phase 3: Agent Workflow And SSE Query API

**Goal:** Deliver the central `POST /api/query` streaming workflow and source-grounded generated answers.

**Requirements:** AGNT-01, AGNT-02, AGNT-03, AGNT-04, AGNT-05, AGNT-06, API-02, API-03, API-06, API-07, API-08, API-09

**Success Criteria:**
1. Query workflow emits SSE events in the frontend contract order.
2. Query rewrite expands company aliases and can split complex reasoning queries.
3. Intent classification selects factual, analytical, or reasoning prompt templates.
4. Generated Markdown includes citation markers that map to `done.citations` metadata.
5. Error and heartbeat behavior is testable and frontend-friendly.
6. Backend SSE fixtures/examples mirror the imported frontend's current `Message` stage flow and `SidebarRight` retrieval panels.
7. Answer citation markup can be adapted into the frontend's clickable citation span behavior.

**Frontend integration prep:** Read `.planning/frontend-integration-readiness.md` before planning or implementing this phase. Phase 3 should stabilize backend SSE payloads so Phase 4 can replace frontend mocks with adapters instead of redesigning UI.

### Phase 4: Integration And Demo Hardening

**Goal:** Ensure the imported React app can integrate without contract churn and the demo survives provider/network failures.

**Requirements:** INTG-01, INTG-02, INTG-03, INTG-04, INTG-05, INTG-06, INTG-07, INTG-08

**Success Criteria:**
1. Contract tests cover `GET /api/documents` and all SSE event payload shapes.
2. Imported React frontend can run against local backend via `/api` proxy.
3. Three demo questions complete end-to-end with visible retrieval and citation data.
4. Demo mode can use cached/mock provider responses when external APIs are unavailable.
5. Integration issues are fixed at API boundaries without taking over frontend design work.
6. Frontend mock flow in `frontend/src/App.tsx` is replaced by a backend API/SSE adapter while preserving existing component layout and state shapes.
7. `GET /api/documents` populates the left document library, and `retrieval_complete`/`rerank_complete` populate the right retrieval panels.
8. Citation IDs from backend `rerank_complete`/`done.citations` drive the existing clickable citation highlight behavior.

**Frontend integration prep:** Use `.planning/frontend-integration-readiness.md` as the canonical adapter checklist for this phase.

### Phase 5: P1 Enhancements

**Goal:** Add high-value extras only after the MVP path is stable.

**Requirements:** API-10 plus selected QUAL-01, QUAL-02, QUAL-03, QUAL-04 if time permits

**Success Criteria:**
1. Optional `POST /api/preview-rewrite` returns detected entities and expanded terms.
2. Recency weighting and numeric consistency checks are added only if they do not destabilize demo flow.
3. Enhancement tests are isolated so the core MVP remains reliable.

## Dependency Map

- Phase 1 blocks all later phases.
- Phase 2 depends on Phase 1 data and schemas.
- Phase 3 depends on Phase 2 retrieval/rerank services.
- Phase 4 depends on stable Phase 3 API contracts and can start with mocks once Phase 1 schemas exist.
- Phase 5 depends on successful Phase 4 demo hardening.

## Coverage Validation

- v1 requirements mapped: 35 / 35
- Unmapped v1 requirements: 0
- Frontend UI design intentionally excluded from phase goals except integration validation.

---
*Last updated: 2026-05-13 after frontend import integration prep*
