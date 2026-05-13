# Phase 1: Backend Foundation And Demo Data - Research

**Researched:** 2026-05-13  
**Domain:** FastAPI backend foundation, Pydantic contracts, deterministic financial-demo fixtures  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use fixture-first demo data for Phase 1; handwritten JSON/fixture content must stabilize the three demo questions before PDF parsing is robust.
- Include curated fallback data for critical financial facts, especially Guizhou Moutai 2023 revenue/growth and CATL risk material.
- PDF parsing may be scaffolded, but Phase 1 success must not depend on perfect PDF extraction.
- Use a standard `backend/` structure with `backend/app`, `backend/scripts`, and `backend/tests`.
- Keep a clean backend/frontend boundary because React frontend code will be imported later by another team.
- Mock provider behavior first; Phase 1 tests must run without network calls, API keys, embedding, rerank, or LLM services.
- Define frontend-facing Pydantic models early, including future SSE event payloads.
- Implement `GET /api/documents` in Phase 1.
- Do not build frontend UI, full retrieval/rerank/generation, authentication, deployment, or production observability.

### the agent's Discretion
- Exact Python packaging tool and dependency file format.
- Exact fixture filenames and backend-local data folder layout.
- Whether to include a minimal `/health` endpoint for smoke tests.
- Exact config class names, environment variable prefixes, and test fixture organization.

### Deferred Ideas (OUT OF SCOPE)
- Full hybrid retrieval implementation.
- Rerank provider integration.
- `POST /api/query` SSE lifecycle workflow implementation.
- Query rewrite preview endpoint.
- Frontend UI implementation and visual polish.
- Numeric consistency checks and recency weighting.
</user_constraints>

<research_summary>
## Summary

Phase 1 should establish a contract-first FastAPI backend that later retrieval, rerank, and SSE workflow phases can extend without changing frontend-facing schemas. The safest approach for the two-day demo timeline is to build deterministic data and schema seams before integrating external model APIs or fragile PDF parsing.

The backend should use a simple Python package under `backend/app`, Pydantic models for all API and future SSE payloads, JSON fixture data for documents/chunks/demo cases, and pytest coverage for importability, configuration, schema serialization, and `GET /api/documents`.

**Primary recommendation:** Build a minimal runnable FastAPI backend with fixture-backed document metadata, stable Pydantic contracts, seed/build scripts, and no external service dependency.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | current compatible | HTTP API and OpenAPI schema generation | Simple async API layer and natural Pydantic integration. |
| Uvicorn | current compatible | Local ASGI server | Standard FastAPI development runner. |
| Pydantic / pydantic-settings | current compatible | Data and config models | Keeps contracts explicit and serializable. |
| Pytest | current compatible | Automated tests | Lightweight and standard for Python backend projects. |
| httpx or FastAPI TestClient | current compatible | Endpoint tests | Enables local API tests without real network dependencies. |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| python-dotenv | Local env loading | Optional for demo developer convenience. |
| PyMuPDF/pdfplumber | PDF parsing scaffold | Only scaffold or isolate in Phase 1; do not make success depend on PDF quality. |

### Recommended Installation Shape

Use either `backend/requirements.txt` for speed or a lightweight `backend/pyproject.toml`. For this MVP, `requirements.txt` is acceptable and easiest for a two-day demo.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── documents.py
│   ├── core/
│   │   ├── config.py
│   │   └── ingestion/
│   │       ├── __init__.py
│   │       ├── fixture_loader.py
│   │       └── normalizer.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   └── events.py
│   └── data/
│       ├── raw/
│       └── processed/
├── scripts/
│   ├── seed_data.py
│   └── build_index.py
├── tests/
│   ├── test_documents_api.py
│   ├── test_schemas.py
│   └── test_seed_data.py
└── requirements.txt
```

### Pattern 1: Contract-first schemas
**What:** Define Pydantic models before service implementation.  
**When to use:** API responses, SSE payloads, document/chunk persistence, provider seams.  
**Why:** The frontend team can integrate against stable JSON shapes, and tests can catch drift.

### Pattern 2: Fixture-backed services
**What:** Load processed JSON data through a small repository/loader instead of hard-coding route responses.  
**When to use:** `GET /api/documents`, future retrieval fixtures, demo cases.  
**Why:** It keeps Phase 1 simple while making Phase 2 retrieval implementation plug into the same data path.

### Pattern 3: Explicit demo mode
**What:** Configuration should make demo/mock behavior explicit.  
**When to use:** Any future provider, fallback, or external dependency.  
**Why:** Tests and local demo runs stay deterministic.
</architecture_patterns>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Letting PDF parsing define the demo path
**What goes wrong:** Critical demo facts are missing or malformed due to table extraction issues.  
**How to avoid:** Use curated fixture facts and chunks first; keep PDF parsing isolated and non-blocking.

### Pitfall 2: Under-specified API payloads
**What goes wrong:** Frontend integration requires repeated backend changes because fields differ from the PRD.  
**How to avoid:** Encode the PRD fields in Pydantic models and endpoint tests immediately.

### Pitfall 3: External service dependency in tests
**What goes wrong:** CI/local tests fail without keys or network.  
**How to avoid:** Use mock provider seams and fixture data only in Phase 1 tests.

### Pitfall 4: Overbuilding Phase 1
**What goes wrong:** Time is spent on retrieval/generation before data and contracts are stable.  
**How to avoid:** Stop Phase 1 at runnable backend, schemas, fixture data, document endpoint, and tests.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 1 validation should prove the backend foundation is runnable and contract-safe without external services.

### Required Validation Dimensions
- Import validation: all backend modules import successfully.
- API validation: FastAPI app responds to `/health` and `/api/documents`.
- Schema validation: Document, Chunk, API response, and SSE event payload models serialize expected fields.
- Data validation: seed/build scripts create deterministic processed JSON with the required demo documents and chunks.
- External dependency validation: tests pass without API keys, network, embedding, rerank, or LLM calls.

### Validation Commands
- `python -m compileall backend/app backend/scripts`
- `cd backend && python -m pytest`
- `cd backend && python scripts/seed_data.py`
- `cd backend && python scripts/build_index.py --fixture-only`
</validation_architecture>

<open_questions>
## Open Questions

1. **Exact packaging choice**
   - What we know: `requirements.txt` is fastest and acceptable for the demo.
   - Recommendation: Use `backend/requirements.txt` unless implementation discovers a strong reason for `pyproject.toml`.

2. **Actual source PDFs**
   - What we know: The PRD names target reports, but files are not yet present in the repo.
   - Recommendation: Seed representative fixture records now; add real PDFs later without changing schemas.
</open_questions>

<sources>
## Sources

### Primary
- `.planning/PROJECT.md` — Project scope and backend/integration priority.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements and API contract.
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria.
- `.planning/phases/01-backend-foundation-and-demo-data/01-CONTEXT.md` — User decisions and scope boundaries.
- `FinRAG_需求文档.md` — Source PRD and backend directory/API requirements.

### Secondary
- `.planning/research/STACK.md` — Initialized stack recommendation.
- `.planning/research/ARCHITECTURE.md` — Initialized architecture recommendation.
- `.planning/research/PITFALLS.md` — Initialized risk analysis.
</sources>

<metadata>
## Metadata

**Research scope:** FastAPI scaffold, Pydantic schemas, fixture data, document API, deterministic tests.  
**Confidence breakdown:**
- Standard stack: HIGH — directly specified by PRD and common FastAPI practice.
- Architecture: HIGH — aligns with PRD module layout and Phase 1 scope.
- Pitfalls: HIGH — derived from PRD risk table and user constraints.
- Code examples: MEDIUM — implementation examples deferred to execution.

**Research date:** 2026-05-13  
**Valid until:** 2026-06-12
</metadata>

---

*Phase: 01-backend-foundation-and-demo-data*  
*Research completed: 2026-05-13*  
*Ready for planning: yes*
