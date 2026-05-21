# Roadmap: FinRAG v1.4 Advanced RAG Retrieval Architecture

**Last updated:** 2026-05-21  
**Current status:** v1.4 initialized; ready to plan Phase 17.

## Shipped Milestones

| Milestone | Name | Status | Phases | Summary | Archive |
| --- | --- | --- | --- | --- | --- |
| v1.0 | Mock-data MVP | Shipped | 1-5 | FastAPI backend, hybrid retrieval/rerank, SSE query API, frontend integration, preview rewrite, and mock-data demo readiness. | Prior phase artifacts in `.planning/phases/01-*` through `.planning/phases/05-*` |
| v1.1 | Document Import Pipeline | Shipped | 6-7 | PDF/text-layer extraction, raw Markdown artifacts, FinRAG corpus import, deterministic chunking, and retrieval index rebuild. | `.planning/milestones/v1.1-ROADMAP.md` |
| v1.2 | Frontend Evidence Traceability & Interaction Polish | Complete | 8-10 | Real-corpus examples, document open action, retrieval panel polish, and per-turn evidence traceability. | Pending milestone archive |
| v1.3 | Knowledge Base Management | Complete | 11-16 | Single-app KB management, import/reindex APIs, table-aware extraction/chunking/facts, and table-aware numeric QA. | Pending milestone archive |

## Current Milestone

### v1.4 Advanced RAG Retrieval Architecture

Goal: Upgrade FinRAG from a direct hybrid retrieval demo into a traceable advanced financial RAG architecture with structured query understanding, knowledge routing, metadata pre-filtering, multi-stage retrieval, evidence compression, iterative retrieval, and late-stage hierarchical chunking.

| Phase | Name | Requirements | Goal | Validation |
| --- | --- | --- | --- | --- |
| 17 | Structured Query Understanding And Retrieval Plan | QUERY-01, QUERY-02, QUERY-03 | Replace ad-hoc query expansion with a structured retrieval plan while preserving existing rewrite/intent behavior. | Query plan tests cover factual metric lookup, analytical trend/risk, and reasoning questions; SSE/debug can expose plan data. |
| 18 | Knowledge Routing And Metadata Pre-filtering | ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04 | Route queries to specialized retrieval paths and shrink candidate sets with metadata filters before expensive recall. | Numeric/table, financial-report, research-report, and general fallback routes are tested; debug shows route, filters, and counts. |
| 19 | Multi-stage Retrieval Cascade Trace | CASCADE-01, CASCADE-02, CASCADE-03, CASCADE-04 | Make retrieval an explicit cascade with observable stage trace from planning/filtering through recall, fusion, rerank, and final evidence. | SSE/debug include stage traces; representative query tests verify deterministic cascade outputs and fallback metadata. |
| 20 | Evidence Compression And Context Builder | EVIDENCE-01, EVIDENCE-02, EVIDENCE-03, EVIDENCE-04 | Build compact evidence packs for generation that preserve facts, claims, citations, and table metadata while reducing context noise. | Context builder tests cover text/table evidence, dedupe, citation preservation, and table fact losslessness. |
| 21 | Agentic Iterative Retrieval Demo Mode | ITER-01, ITER-02, ITER-03, ITER-04 | Add a lightweight multi-step retrieval mode for analytical/reasoning questions with visible retrieval purposes and fallback. | Reasoning queries produce step traces; simple factual queries stay single-pass; fallback path is tested. |
| 21.1 | Frontend RAG Process Showcase For v1.4 Demo | SHOWCASE-01, SHOWCASE-02, SHOWCASE-03, SHOWCASE-04 | Add demo-oriented frontend panels and interactions that expose query planning, routing/filtering, cascade trace, evidence compression, and iterative retrieval steps before Phase 22. | Frontend type/build tests pass; representative queries visibly show intermediate RAG artifacts without breaking chat/citation flow. |
| 22 | Hierarchical Chunking And Drill-down Retrieval | HIER-01, HIER-02, HIER-03, HIER-04 | Add hierarchy metadata and optional section/table-summary to child evidence retrieval after the safer routing/cascade layers are stable. | Reimport/reindex remains deterministic; hierarchy metadata is present; drill-down retrieval is covered without breaking old chunk consumers. |

## Phase Details

### Phase 17: Structured Query Understanding And Retrieval Plan

**Purpose:** Convert query analysis from simple expansion into a structured planning layer that downstream retrieval can consume.

**Plans:** 1 plan

Plans:
- [ ] 17-01-PLAN.md — Add structured query plan contracts, shared ontology, parser builder, and API/SSE regressions.

**Likely files:**
- `backend/app/core/agent/query_analysis.py`
- `backend/app/models/schemas.py`
- `backend/app/models/events.py`
- `backend/app/core/agent/workflow.py`
- `backend/tests/test_query_analysis.py`
- `backend/tests/test_query_api.py`

**Success criteria:**
- A query plan captures entities, intent, task type, metrics, time range, preferred document types, and retrieval strategy.
- Existing query rewrite, alias expansion, intent detection, and SSE events remain backward compatible.
- Tests cover NVIDIA revenue lookup, Moutai/CATL analytical questions, and at least one reasoning query.
- The plan is simple and rule-based enough to stay deterministic under mock tests.

### Phase 18: Knowledge Routing And Metadata Pre-filtering

**Purpose:** Avoid searching the full corpus when the query plan can narrow the search space first.

**Likely files:**
- `backend/app/core/retrieval/router.py`
- `backend/app/core/retrieval/filters.py`
- `backend/app/core/retrieval/hybrid.py`
- `backend/app/core/retrieval/bm25_store.py`
- `backend/app/core/retrieval/vector_store.py`
- `backend/app/api/debug.py`
- `backend/tests/test_hybrid_retrieval.py`
- `backend/tests/test_debug_retrieval.py`

**Success criteria:**
- Queries route to table-fact-first, financial-report section, research-report analysis, or general hybrid fallback.
- Metadata pre-filters can use company, doc_type, date/period, chunk_type, metric, and collection.
- Debug/retrieval outputs show route choice, filters, candidate counts before/after filtering, and fallback reasons when filters are too narrow.
- Existing table-aware numeric QA and general text RAG behavior remain green.

### Phase 19: Multi-stage Retrieval Cascade Trace

**Purpose:** Turn retrieval into an inspectable cascade rather than a single fused top-k list.

**Likely files:**
- `backend/app/core/retrieval/hybrid.py`
- `backend/app/core/retrieval/rerank_service.py`
- `backend/app/models/events.py`
- `backend/app/models/schemas.py`
- `backend/app/core/agent/workflow.py`
- `frontend/src/types.ts` only if frontend typing needs the new optional trace fields
- `backend/tests/test_hybrid_retrieval.py`
- `backend/tests/test_query_api.py`

**Success criteria:**
- Retrieval records stages for query plan/route, metadata filter, coarse recall, fusion/lightweight selection, rerank, and final evidence.
- Each stage records name, input count, output count, method/source, and degradation/fallback metadata.
- SSE and debug retrieval expose stage traces without breaking existing frontend consumers.
- Tests verify deterministic cascade traces for factual, analytical, and table-fact queries.

### Phase 20: Evidence Compression And Context Builder

**Purpose:** Reduce context pollution by feeding generation a compact, source-grounded evidence pack.

**Likely files:**
- `backend/app/core/agent/context_builder.py`
- `backend/app/core/agent/generator.py`
- `backend/app/core/agent/prompts.py`
- `backend/app/core/agent/workflow.py`
- `backend/tests/test_agent_workflow.py`
- `backend/tests/test_query_api.py`

**Success criteria:**
- Generation uses an evidence pack containing salient facts, numeric values, claims, citation IDs, and source metadata.
- Duplicate or overlapping evidence from the same source/table/metric is compressed.
- Table facts preserve value, unit, currency, period, page, and source without lossy summarization.
- Existing citation metadata remains accurate in `done` events.

### Phase 21: Agentic Iterative Retrieval Demo Mode

**Purpose:** Demonstrate retrieval as a reasoning process for complex financial analysis questions.

**Likely files:**
- `backend/app/core/agent/retrieval_planner.py`
- `backend/app/core/agent/workflow.py`
- `backend/app/core/agent/query_analysis.py`
- `backend/app/models/events.py`
- `backend/tests/test_agent_workflow.py`
- `backend/tests/test_query_api.py`

**Success criteria:**
- Analytical/reasoning queries can create 2-3 retrieval steps with explicit purpose, generated retrieval query, route, filters, and selected evidence.
- Simple factual lookups keep the single-pass cascade path.
- Iterative retrieval falls back gracefully when planning or evidence collection fails.
- SSE/debug traces expose iterative steps for demo explanation without requiring frontend redesign.

### Phase 21.1: Frontend RAG Process Showcase For v1.4 Demo (INSERTED)

**Purpose:** Make the v1.4 advanced RAG architecture visible in the chat UI for interview/demo use, including the Phase 22 hierarchy/drill-down trace when present.

**Goal:** Add frontend display and interaction surfaces for the key intermediate artifacts produced by Phases 17-22: structured query plan, route/filter metadata, cascade trace, evidence selection/compression signals, iterative retrieval steps, and hierarchy/drill-down metadata.
**Requirements**: SHOWCASE-01, SHOWCASE-02, SHOWCASE-03, SHOWCASE-04
**Depends on:** Phase 22
**Plans:** 1 plan

**Likely files:**
- `frontend/src/api/finrag.ts`
- `frontend/src/types.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/SidebarRight.tsx`
- `frontend/src/components/ChatArea.tsx`
- `frontend/src/components/*Trace*.tsx` or focused new display components if needed

**Success criteria:**
- The UI displays query understanding fields such as intent, task type, entities, metrics, retrieval strategy, expansions, and sub-queries.
- The retrieval panel shows route choice, applied metadata filters, cascade stages, input/output counts, degradation/fallback status, and final evidence selection.
- Iterative analytical/reasoning queries show each retrieval step's purpose, generated query, route/filter metadata, and selected evidence summaries.
- Hierarchy/drill-down UI shows real `hierarchy_drill_down`, `chunk_level`, `parent_id`, `child_ids`, and `section_path` data when backend payloads contain it.
- Existing chat streaming, citation clicking, KB navigation, and simple factual/table QA flows remain usable.
- The design is demo-oriented and information-rich rather than production-minimal; it should make intermediate processing legible during a walkthrough.

Plans:
- [ ] 21.1-01-PLAN.md — Add frontend RAG process inspector for Phase 17-22 traces, including hierarchy/drill-down display.

### Phase 22: Hierarchical Chunking And Drill-down Retrieval

**Purpose:** Add multi-scale retrieval after the safer architecture layers are in place.
**Requirements**: HIER-01, HIER-02, HIER-03, HIER-04
**Depends on:** Phase 21
**Plans:** 1 plan

**Likely files:**
- `backend/app/core/ingestion/chunker.py`
- `backend/app/core/ingestion/corpus_importer.py`
- `backend/app/core/ingestion/table_facts.py`
- `backend/app/core/retrieval/hybrid.py`
- `backend/app/core/retrieval/filters.py`
- `backend/tests/test_corpus_import.py`
- `backend/tests/test_import_pipeline_integration.py`
- `backend/tests/test_hybrid_retrieval.py`

**Success criteria:**
- Chunks can carry `chunk_level`, `parent_id`, `section_title`, `section_path`, and child relationship metadata.
- Retrieval can optionally recall section/table-summary evidence first, then drill down to paragraph/table-row children.
- Corpus import and index rebuild remain deterministic.
- Existing chunk consumers and KB/document APIs remain backward compatible.

Plans:
- [x] 22-01-PLAN.md — Add deterministic hierarchy metadata, table parent-child linkage, and bounded drill-down retrieval.

## Requirement Coverage

| Requirement | Phase | Status |
| --- | --- | --- |
| QUERY-01 | Phase 17 | Pending |
| QUERY-02 | Phase 17 | Pending |
| QUERY-03 | Phase 17 | Pending |
| ROUTE-01 | Phase 18 | Pending |
| ROUTE-02 | Phase 18 | Pending |
| ROUTE-03 | Phase 18 | Pending |
| ROUTE-04 | Phase 18 | Pending |
| CASCADE-01 | Phase 19 | Pending |
| CASCADE-02 | Phase 19 | Pending |
| CASCADE-03 | Phase 19 | Pending |
| CASCADE-04 | Phase 19 | Pending |
| EVIDENCE-01 | Phase 20 | Pending |
| EVIDENCE-02 | Phase 20 | Pending |
| EVIDENCE-03 | Phase 20 | Pending |
| EVIDENCE-04 | Phase 20 | Pending |
| ITER-01 | Phase 21 | Pending |
| ITER-02 | Phase 21 | Pending |
| ITER-03 | Phase 21 | Pending |
| ITER-04 | Phase 21 | Pending |
| SHOWCASE-01 | Phase 21.1 | Pending |
| SHOWCASE-02 | Phase 21.1 | Pending |
| SHOWCASE-03 | Phase 21.1 | Pending |
| SHOWCASE-04 | Phase 21.1 | Pending |
| HIER-01 | Phase 22 | Complete |
| HIER-02 | Phase 22 | Complete |
| HIER-03 | Phase 22 | Complete |
| HIER-04 | Phase 22 | Complete |

**Coverage:** 27 requirements mapped to 7 phases; unmapped requirements: 0.

## Next Action

Execute Phase 21.1 frontend showcase, using Phase 22 hierarchy metadata and drill-down trace in the demo UI.
