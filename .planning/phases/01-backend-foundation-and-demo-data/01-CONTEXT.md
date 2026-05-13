# Phase 1: Backend Foundation And Demo Data - Context

**Gathered:** 2026-05-13  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the runnable backend foundation and deterministic demo data baseline for FinRAG. It should create the backend project structure, FastAPI entrypoint, Pydantic schemas, configuration layer, document-list API, demo data seed/build flow, and tests that run without external API keys.

This phase does **not** implement full hybrid retrieval, rerank, LLM generation, SSE query workflow, or frontend UI. Those are later phases. It may define schemas and examples those later phases will use.

</domain>

<decisions>
## Implementation Decisions

### Data Strategy
- **D-01:** Use fixture-first demo data for Phase 1. Handwritten JSON/fixture content should guarantee the three demo questions have stable source facts even before PDF parsing is robust.
- **D-02:** Include a curated fallback path for critical financial facts, especially Guizhou Moutai 2023 revenue/growth and CATL risk material.
- **D-03:** PDF parsing can be scaffolded in Phase 1, but passing Phase 1 should not depend on perfect PDF extraction.
- **D-04:** Seed/build scripts should produce processed data that downstream retrieval phases can consume without external services.

### Backend Project Structure
- **D-05:** Use a standard `backend/` structure: `backend/app`, `backend/scripts`, and `backend/tests`.
- **D-06:** Keep the repository ready for a later imported React frontend by preserving a clean backend/frontend boundary.
- **D-07:** Prefer module boundaries aligned with the source requirements document: `api`, `core/ingestion`, `core/retrieval`, `core/agent`, `core/generation`, `models`, and `data`.

### Provider And Test Strategy
- **D-08:** Mock provider behavior first. Phase 1 tests must run without network calls, API keys, embedding services, rerank services, or LLM providers.
- **D-09:** Define provider/config seams early so later phases can add real BGE-M3, bge-reranker, DeepSeek/Qwen/OpenAI clients without rewriting core workflow code.
- **D-10:** Do not enable live external calls just because environment variables are present; later live modes should be explicit.

### API Contract Foundation
- **D-11:** Define Pydantic models for all frontend-facing payloads early, including future SSE event payloads even if `POST /api/query` is not fully implemented in this phase.
- **D-12:** Implement `GET /api/documents` in Phase 1 because the frontend left sidebar depends on it and it validates the document metadata model.
- **D-13:** Include OpenAPI/schema examples or tests that the frontend team can use as contract references.

### Scope Control
- **D-14:** Do not build or redesign the frontend UI in Phase 1.
- **D-15:** Do not implement full retrieval/rerank/generation in Phase 1; only create compatible data, schemas, and seams.
- **D-16:** Do not add authentication, user accounts, editable document management, deployment, or production observability.

### the agent's Discretion
- The agent may choose the exact Python packaging tool and dependency file format, as long as it is simple for a two-day demo and supports pytest.
- The agent may choose exact fixture filenames and local data folder layout under `backend/`, as long as the structure is documented and deterministic.
- The agent may decide whether to include a minimal `/health` endpoint if useful for smoke tests.
- The agent may decide exact config class names, environment variable prefixes, and test fixture organization.

</decisions>

<specifics>
## Specific Ideas

- The three demo questions from `FinRAG_需求文档.md` are acceptance anchors and should appear in fixtures or tests as named demo cases.
- The frontend will be imported later by another team, so Phase 1 should optimize for stable contracts and easy integration rather than visual design.
- The document-list endpoint should return the fields specified in the source requirements: `doc_id`, `title`, `doc_type`, `company`, `date`, and `chunk_count`.
- Critical financial facts should be present in fixture data in a way that later citations can trace to chunk metadata.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project And Scope
- `.planning/PROJECT.md` — Project context, scope boundary, core value, frontend ownership constraint.
- `.planning/ROADMAP.md` — Phase 1 boundary, requirements mapping, success criteria.
- `.planning/REQUIREMENTS.md` — Phase 1 requirement IDs and frontend-facing API contract requirements.
- `.planning/STATE.md` — Current project memory and active constraints.

### Source Requirements
- `FinRAG_需求文档.md` — Original product/backend/frontend requirements and API contract.

### Research
- `.planning/research/STACK.md` — Recommended backend stack and what not to use.
- `.planning/research/ARCHITECTURE.md` — Component boundaries and suggested build order.
- `.planning/research/PITFALLS.md` — Phase 1 pitfalls: fixture fallback, SSE contract ambiguity, provider outage risks.
- `.planning/research/SUMMARY.md` — Initialization research synthesis.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No application code exists yet. The repository currently contains planning assets and the original requirements document.

### Established Patterns
- No runtime code patterns are established. New backend code should establish clear, minimal, testable patterns.
- Planning artifacts indicate FastAPI + Pydantic + pytest as the intended foundation.

### Integration Points
- Future React frontend integration depends on stable `/api` routes and JSON/SSE schemas.
- Phase 1 integration point is `GET /api/documents`; later phases add `POST /api/query` SSE.

</code_context>

<deferred>
## Deferred Ideas

- Full hybrid retrieval implementation — Phase 2.
- Rerank provider integration and fallback behavior — Phase 2.
- `POST /api/query` SSE lifecycle workflow — Phase 3.
- Query rewrite preview endpoint — Phase 5 unless needed earlier for frontend integration.
- Frontend UI implementation and visual polish — external frontend team; Phase 4 only validates integration.
- Numeric consistency hallucination checks and recency weighting — v2/P1 enhancements after MVP stability.

</deferred>

---

*Phase: 01-backend-foundation-and-demo-data*  
*Context gathered: 2026-05-13*
