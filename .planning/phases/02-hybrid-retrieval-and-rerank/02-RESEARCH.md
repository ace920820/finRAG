# Phase 2: Hybrid Retrieval And Rerank - Research

**Researched:** 2026-05-13  
**Domain:** Retrieval indexing, BM25/vector hybrid search, provider-configured embeddings/rerank, local index persistence  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Do not use local embedding, rerank, or text-generation models.
- Use Alibaba Cloud Bailian / DashScope-compatible API providers for all model-backed services.
- Embedding model, rerank model, and text model must all be configurable from the backend config layer.
- Text generation provider for later phases should default to Qwen Plus via Alibaba Cloud Bailian.
- The project should include a `.env` template/example with blanks for required provider values.
- Actual secrets must not be committed.
- Use a dual-track embedding path: deterministic/mock embedding by default for tests and local no-key execution; real API available via explicit config.
- Use a dual-track rerank path: deterministic/mock reranker by default for tests; real API available via explicit config.
- Rerank provider failure must fall back to fused Top 5 candidates.
- Support both local index persistence and fixture-time rebuilding.
- Use RRF as the primary fusion strategy with configurable `k=60`.
- Add a development/debug retrieval endpoint such as `/api/debug/retrieval`.
- Do not implement LLM answer generation in Phase 2.
- Do not build frontend UI or depend on live provider calls for automated tests.

### the agent's Discretion
- Exact class/protocol names for embedding and rerank providers.
- Exact index file names and serialization format.
- Whether to use `faiss-cpu` if installable, with a deterministic fallback if local installation is unavailable.
- Tokenization details for BM25 as long as Chinese retrieval works for demo fixtures.

### Deferred Ideas (OUT OF SCOPE)
- Full `POST /api/query` SSE workflow.
- LLM answer generation with Qwen Plus.
- Intent classification and prompt templates.
- Frontend retrieval visualization UI.
- Weighted-score fusion alternative.
- Production-grade vector database or large-corpus operations.
</user_constraints>

<research_summary>
## Summary

The safe Phase 2 design is a provider-abstraction layer around three model-backed capabilities: embeddings, rerank, and later text generation. Alibaba Cloud Bailian supports OpenAI-compatible calls for chat and embeddings through `https://dashscope.aliyuncs.com/compatible-mode/v1`, while rerank is exposed through the DashScope rerank endpoint. That means the backend can centralize configuration for base URL, API key, and model names while keeping tests deterministic through mock providers.

For retrieval, the phase should build a small but real hybrid stack: BM25 for lexical recall, FAISS for vector recall, and RRF for fusion. The demo corpus from Phase 1 is already enough to validate the retrieval path, persistence, and frontend-observable payloads. The lowest-risk implementation is deterministic mocks for tests, optional live Bailian providers for smoke testing, and local index files that can be rebuilt from processed fixtures.

**Primary recommendation:** Keep provider seams explicit and config-driven, build a local persistent retrieval index from the existing fixture corpus, and make all automated tests pass with mock providers only.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai | current compatible | OpenAI-compatible calls to Bailian for embeddings and later Qwen Plus text | Official OpenAI-compatible path supported by Bailian. |
| httpx | current compatible | Direct HTTP calls for rerank endpoint and provider fallback | Lightweight and already present in the backend. |
| faiss-cpu | current compatible | Local vector index | Common lightweight local vector search engine for demo-scale corpora. |
| rank_bm25 | current compatible | BM25 keyword retrieval | Simple, proven lexical retrieval for Chinese text demos. |
| jieba | current compatible | Chinese tokenization for BM25 | Standard lightweight Chinese segmentation. |
| numpy | current compatible | Numeric array support for embeddings/index operations | Common dependency for vector processing and FAISS integration. |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| pydantic-settings | Config management | Already in use; expand for provider and model settings. |
| pytest | Automated tests | Unit and integration tests for retrieval, fusion, rerank fallback, and debug endpoint. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FAISS local index | Vector database | More operational complexity and unnecessary for demo scope. |
| Weighted fusion | RRF | Weighted fusion is less canonical for this demo and adds tuning complexity. |
| Local models | Bailian APIs | Local models would violate the user's integration and config goals. |

**Installation:**
```bash
pip install openai httpx faiss-cpu rank_bm25 jieba numpy
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
backend/app/
├── core/
│   ├── config.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── embeddings.py
│   │   ├── rerank.py
│   │   └── text.py
│   └── retrieval/
│       ├── bm25_store.py
│       ├── hybrid.py
│       ├── index_store.py
│       ├── vector_store.py
│       └── service.py
├── api/
│   └── debug.py
└── data/
    └── index/
```

### Pattern 1: Provider abstraction with mock/live split
**What:** A provider protocol plus deterministic mock implementation and a Bailian-backed implementation selected by config.  
**When to use:** Embeddings, rerank, and later text generation.  
**Why:** Tests stay deterministic, but the demo can still smoke-test real APIs.

### Pattern 2: Local persistent retrieval index
**What:** Build index artifacts from processed fixtures and reload them on startup when present.  
**When to use:** Demo-scale retrieval that should be fast and reproducible.  
**Why:** It avoids rebuilding on every boot and makes the debug endpoint useful.

### Pattern 3: Separate stage outputs
**What:** Keep BM25, vector, fused, and reranked lists distinct.  
**When to use:** Any retrieval observability or future frontend visualization.  
**Why:** The frontend needs to show the retrieval story, not only the final answer.

### Anti-Patterns to Avoid
- **Hard-coding provider endpoints or model names:** makes later switching and `.env` management painful.
- **Using only final top-k results:** hides the retrieval process from later SSE/frontend stages.
- **Testing live APIs in pytest:** makes CI and local development fragile.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Embeddings | Custom embedding math | Bailian/OpenAI-compatible embedding API or deterministic mock | Real models improve relevance; mocks keep tests stable. |
| Text rerank | Heuristic keyword-only reranker | Bailian rerank API or deterministic mock | Rerank quality matters for demo credibility. |
| Vector search | Linear scan over all chunks | FAISS | Even a demo corpus benefits from a standard local index. |
| Chinese tokenization | Naive whitespace splitting | `jieba` | Chinese retrieval needs segmentation to avoid poor BM25 recall. |

**Key insight:** Retrieval quality and demo stability come from clean provider seams and reusable local indexes, not from clever one-off scoring code.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Provider config leaks into business logic
**What goes wrong:** Retrieval service starts instantiating API clients directly.  
**Why it happens:** Config is spread across route handlers and utility functions.  
**How to avoid:** Centralize provider/client creation in `core/providers` and inject them into retrieval services.  
**Warning signs:** Retrieval tests require env vars or network access.

### Pitfall 2: Rerank failure breaks the query flow
**What goes wrong:** A rerank API outage prevents retrieval results from being returned at all.  
**Why it happens:** The code assumes the rerank provider always succeeds.  
**How to avoid:** Fall back to fused Top 5 and mark the degradation explicitly.  
**Warning signs:** Debug endpoint or test fails when rerank is mocked to throw.

### Pitfall 3: Index state becomes non-deterministic
**What goes wrong:** Local index artifacts differ across runs or are rebuilt inconsistently.  
**Why it happens:** Fixture data and serialization rules are not fixed.  
**How to avoid:** Build indexes from canonical processed fixtures and validate deterministic outputs in tests.  
**Warning signs:** Same chunk corpus yields different top-k ordering or scores in tests.

### Pitfall 4: Retrieval outputs are not frontend-friendly
**What goes wrong:** Only final scores are returned, with no chunk metadata.  
**Why it happens:** The service is built as an internal search utility rather than an integration surface.  
**How to avoid:** Keep `bm25_results`, `vector_results`, `fused_top20`, and rerank payloads separate and metadata-rich.  
**Warning signs:** Debug response lacks page/source/title or citation IDs.
</common_pitfalls>

<validation_architecture>
## Validation Architecture

Phase 2 validation should prove retrieval/rerank works locally with no live provider requirement.

### Required Validation Dimensions
- Provider seam validation: mock providers can be instantiated without API keys.
- Retrieval validation: BM25 and vector search return deterministic results on the fixture corpus.
- Fusion validation: RRF produces stable ordering from BM25/vector candidates.
- Rerank validation: rerank returns Top 5 payloads and falls back cleanly when mocked to fail.
- Debug validation: `/api/debug/retrieval` returns retrieval stage outputs compatible with later SSE payloads.
- Optional live smoke validation: documented manual command can hit Bailian-compatible APIs when env vars are present.

### Validation Commands
- `python -m compileall backend/app/core/providers backend/app/core/retrieval backend/scripts`
- `cd backend && python -m pytest`
- `cd backend && python scripts/build_index.py`
- `cd backend && python -m pytest tests/test_retrieval_service.py tests/test_debug_retrieval.py`
</validation_architecture>

<open_questions>
## Open Questions

1. **Best local retrieval fallback when FAISS is unavailable**
   - What we know: `faiss-cpu` is the preferred demo-scale local index.
   - Recommendation: keep a deterministic in-memory fallback so tests can still pass if FAISS installation is problematic.

2. **How much live API smoke testing should be documented**
   - What we know: the user wants API-based embedding/rerank/text configs centralized.
   - Recommendation: document manual smoke commands and env vars, but keep pytest fully offline.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- https://help.aliyun.com/document_detail/2579562.html — Bailian OpenAI-compatible base URL guidance.
- https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-responses — Qwen Plus-family OpenAI-compatible chat usage and base URL.
- https://help.aliyun.com/zh/model-studio/developer-reference/embedding-interfaces-compatible-with-openai — OpenAI-compatible embeddings via `text-embedding-v4` and base URL.
- https://help.aliyun.com/zh/model-studio/rerank — `qwen3-rerank` rerank endpoint and API shape.
- https://help.aliyun.com/zh/model-studio/text-rerank-api — Rerank API reference and HTTP endpoint.

### Secondary (MEDIUM confidence)
- `.planning/phases/01-backend-foundation-and-demo-data/01-RESEARCH.md` — Phase 1 validated backend/test constraints.
- `.planning/phases/02-hybrid-retrieval-and-rerank/02-CONTEXT.md` — User decisions for Phase 2 provider/config strategy.

### Tertiary (LOW confidence - needs validation)
- None.
</sources>

<metadata>
## Metadata

**Research scope:** provider config, embeddings, rerank, BM25/vector hybrid retrieval, local index persistence, debug endpoint.

**Confidence breakdown:**
- Standard stack: HIGH - supported by official Bailian docs and common retrieval practice.
- Architecture: HIGH - directly aligned with Phase 2 scope and Phase 3 handoff.
- Pitfalls: HIGH - derived from demo integration risks and provider fallback needs.
- Code examples: MEDIUM - implementation will still need repository-specific adaptation.

**Research date:** 2026-05-13  
**Valid until:** 2026-06-12
</metadata>

---

*Phase: 02-hybrid-retrieval-and-rerank*  
*Research completed: 2026-05-13*  
*Ready for planning: yes*
