# Phase 2: Hybrid Retrieval And Rerank - Context

**Gathered:** 2026-05-13  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the retrieval and rerank foundation for FinRAG. It should build BM25 keyword retrieval, vector retrieval, hybrid fusion, index persistence/loading, rerank Top 5, and frontend-observable payloads for later `retrieval_complete` and `rerank_complete` SSE events.

This phase does **not** implement the full `POST /api/query` SSE workflow, LLM answer generation, intent classification, or frontend UI. It prepares retrieval/rerank services and testable payloads that Phase 3 will orchestrate.

</domain>

<decisions>
## Implementation Decisions

### Model Provider Strategy
- **D-01:** Do not use local embedding, rerank, or text-generation models.
- **D-02:** Use Alibaba Cloud Bailian / DashScope-compatible API providers for all model-backed services.
- **D-03:** Embedding model, rerank model, and text model must all be configurable from the backend config layer.
- **D-04:** Text generation provider for later phases should default to Qwen Plus via Alibaba Cloud Bailian, but Phase 2 should only add config/provider seams as needed for retrieval/rerank.
- **D-05:** The project should include a `.env` template/example with blanks for required provider values such as base URL, API key, embedding model, rerank model, and text model.
- **D-06:** Actual secrets must not be committed. Use `.env.example` or documented blank `.env` placeholders, and keep real `.env` local-only.

### Embedding Strategy
- **D-07:** Use a dual-track embedding path: deterministic/mock embedding by default for tests and local no-key execution; Alibaba Cloud Bailian embedding API available via explicit config.
- **D-08:** Tests must not require API keys or network calls.
- **D-09:** The vector retrieval implementation should be compatible with real API embeddings later, but fixture/demo tests can use deterministic embeddings.

### Rerank Strategy
- **D-10:** Use a dual-track rerank path: deterministic/mock reranker by default for tests; Alibaba Cloud Bailian rerank API available via explicit config.
- **D-11:** Rerank provider failure must fall back to fused Top 5 candidates and preserve a clear degradation signal for later event payloads.
- **D-12:** Rerank output must include `chunk_id`, `rank`, score, title, doc metadata, full content, and `citation_id`.

### Index Persistence
- **D-13:** Support both local index persistence and fixture-time rebuilding.
- **D-14:** Default behavior should try to load local built indexes when available, and rebuild from fixture chunks when missing.
- **D-15:** `scripts/build_index.py` should evolve from fixture-only validation into a real local index build script.

### Hybrid Fusion
- **D-16:** Use RRF as the primary fusion strategy with configurable `k=60`.
- **D-17:** Weighted score fusion can remain out of scope unless needed later; do not add complexity in Phase 2.
- **D-18:** Keep BM25, vector, and fused result lists separate in service outputs so the frontend can visualize retrieval stages later.

### Debug Interface
- **D-19:** Add a development/debug endpoint such as `/api/debug/retrieval` to inspect retrieval and rerank results before the full SSE workflow exists.
- **D-20:** Treat the debug endpoint as internal/dev-only contract, not the long-term frontend production API.
- **D-21:** The formal frontend path remains Phase 3 `POST /api/query` SSE; Phase 2 debug endpoint exists to speed backend validation and later frontend联调.

### Scope Control
- **D-22:** Do not implement LLM answer generation in Phase 2, even though Qwen Plus config should be prepared.
- **D-23:** Do not build frontend UI or visual components in Phase 2.
- **D-24:** Do not depend on live provider calls for automated tests.

### the agent's Discretion
- The agent may choose exact class/protocol names for embedding and rerank providers.
- The agent may choose exact index file names and serialization format, as long as it is local, deterministic, and documented.
- The agent may choose whether to use `faiss-cpu` if installable, with a deterministic fallback if local installation is unavailable.
- The agent may choose tokenization details for BM25 as long as Chinese text retrieval works for demo fixtures.

</decisions>

<specifics>
## Specific Ideas

- User explicitly wants Alibaba Cloud Bailian API configuration centralized in backend config.
- `.env`/environment template should leave blanks for user-filled values, including:
  - `FINRAG_MODEL_BASE_URL`
  - `FINRAG_MODEL_API_KEY`
  - `FINRAG_EMBEDDING_MODEL`
  - `FINRAG_RERANK_MODEL`
  - `FINRAG_TEXT_MODEL`
- Recommended defaults can be documented, but real credentials must remain blank.
- Existing Phase 1 fixture chunks should be enough to validate BM25, vector retrieval, RRF fusion, and rerank fallback without external APIs.

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project And Scope
- `.planning/PROJECT.md` — Overall product context and backend/integration priority.
- `.planning/ROADMAP.md` — Phase 2 goal, requirements, and success criteria.
- `.planning/REQUIREMENTS.md` — RETR/API requirements mapped to Phase 2.
- `.planning/STATE.md` — Current project state and completed Phase 1 status.

### Prior Phase
- `.planning/phases/01-backend-foundation-and-demo-data/01-CONTEXT.md` — Fixture-first, provider-mock-first, backend/frontend boundary decisions.
- `.planning/phases/01-backend-foundation-and-demo-data/01-RESEARCH.md` — Backend foundation research and validation constraints.
- `.planning/phases/01-backend-foundation-and-demo-data/01-01-SUMMARY.md` — Backend foundation implementation summary.
- `.planning/phases/01-backend-foundation-and-demo-data/01-02-SUMMARY.md` — Fixture data and documents API implementation summary.
- `.planning/phases/01-backend-foundation-and-demo-data/01-03-SUMMARY.md` — Tests and README implementation summary.

### Source Requirements
- `FinRAG_需求文档.md` — Original retrieval, rerank, API, and frontend visualization requirements.

### Existing Code
- `backend/app/models/schemas.py` — Existing retrieval/rerank/citation payload schemas.
- `backend/app/models/events.py` — Existing future SSE payload models.
- `backend/app/core/ingestion/fixture_loader.py` — Existing processed fixture loading.
- `backend/app/data/processed/chunks.json` — Current fixture chunks for index building.
- `backend/scripts/build_index.py` — Existing fixture-only build script to extend.
- `backend/tests/` — Existing pytest pattern and no-network validation style.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/schemas.py`: already defines `RetrievalResultItem`, `RerankResultItem`, and `CitationMetadata`.
- `backend/app/models/events.py`: already defines `RetrievalCompleteEvent` and `RerankCompleteEvent` payload models.
- `backend/app/core/ingestion/fixture_loader.py`: loads fixture documents/chunks and should feed retrieval index building.
- `backend/scripts/build_index.py`: currently validates fixtures; Phase 2 should evolve it into actual BM25/vector index construction.
- `backend/tests/conftest.py`: provides FastAPI TestClient pattern for new debug endpoint tests.

### Established Patterns
- Tests run with `python3 -m pytest` from `backend/` and must not require external APIs.
- Backend uses Python 3.9-compatible type syntax because local `python3` is Python 3.9.6.
- Config uses `FINRAG_` env prefix and `pydantic-settings`.
- Fixture data is stored in `backend/app/data/processed`.

### Integration Points
- Retrieval services should connect to existing `Chunk` models loaded from fixture data.
- Debug endpoint should return structures compatible with future `RetrievalCompleteEvent` and `RerankCompleteEvent`.
- Phase 3 will orchestrate these services into `POST /api/query` SSE.

</code_context>

<deferred>
## Deferred Ideas

- Full `POST /api/query` SSE workflow — Phase 3.
- LLM answer generation with Qwen Plus — Phase 3.
- Intent classification and prompt templates — Phase 3.
- Frontend retrieval visualization UI — external frontend team / Phase 4 integration.
- Weighted-score fusion alternative — defer unless RRF proves insufficient.
- Production-grade vector database or large-corpus operations — out of MVP scope.

</deferred>

---

*Phase: 02-hybrid-retrieval-and-rerank*  
*Context gathered: 2026-05-13*
