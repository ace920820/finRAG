# Phase 2 Baseline Review — Hybrid Retrieval & Rerank

Read-only baseline regression review of Phase 2 in the context of the v1.3 corpus (40 PDFs / 9303 chunks) and the upcoming Phase 15/16 table-aware retrieval work.

## Scope

PLAN: `.planning/phases/02-hybrid-retrieval-and-rerank/02-01-PLAN.md`

Re-validate that:

- Config/`.env.example` still exposes mock + bailian provider switches.
- BM25 + vector + RRF + rerank top-k still match PLAN.
- Mock providers default; live providers behind explicit config.
- Rerank fallback path still works.

## Files Audited

- `backend/app/core/config.py`
- `backend/.env.example`
- `backend/app/core/providers/{base,embeddings,rerank,text}.py`
- `backend/app/core/retrieval/{bm25_store,vector_store,hybrid,rerank_service,index_store}.py`
- `backend/app/data/index/{bm25_index,vector_index}.json` (header inspection only)

## Verification Run

- `python3 -m pytest -q` → **59 passed**.
- Index header inspection:
  - `bm25_index.json`: 9303 chunks, 40 unique `doc_id`s.
  - `vector_index.json`: 9303 chunks, vector **dim = 8** (MockEmbeddingProvider).
- End-to-end `/api/query` (real `.env` with `FINRAG_EMBEDDING_PROVIDER=bailian`):
  - `vector_store.search` raised `ValueError: Query embedding dimension 1024 does not match index dimension 8`.
  - Whole `HybridRetriever.retrieve()` aborted; `bm25_results`, `vector_results`, `fused_top20` all empty in the SSE payload.

## Findings

### Blocker

- **[Blocker] vector index dimension is locked to mock (dim=8) while live config uses Bailian (dim=1024)**
  - File: `backend/app/core/retrieval/vector_store.py:68-72`, `backend/app/data/index/vector_index.json`.
  - Effect: when live providers are configured, `/api/query` returns empty retrieval and the workflow degrades for every real query. Demo path is broken for the live config.
  - Root cause: `vector_index.json` was built under `MockEmbeddingProvider` (dim=8), but `build_embedding_provider()` now returns `BailianEmbeddingProvider` (dim=1024). There is no consistency check at load time.

### Important

- **[Important] `HybridRetriever.retrieve` is all-or-nothing**
  - File: `backend/app/core/retrieval/hybrid.py:39-49`.
  - Effect: when `vector_store.search` raises, the already-computed `bm25_hits` are discarded too. PLAN expected BM25 + vector to be independently usable; current implementation surfaces zero retrieval evidence if either side fails.
  - Suggestion: wrap each branch in `try/except`, log degradation, RRF-fuse only the available side.

- **[Important] No index/provider consistency metadata**
  - File: `backend/app/core/retrieval/vector_store.py`, `index_store.py`.
  - Effect: switching `FINRAG_EMBEDDING_PROVIDER` (or rebuilding under a different model) silently mismatches the persisted vectors. There is no `embedding_model` / `provider` / `dimension` header in `vector_index.json` and no rebuild-on-mismatch hint.
  - Suggestion: write provider + dim into `vector_index.json`, validate at load, raise a clear "rebuild required" error before query time.

- **[Important] `processed/` vs `index/` data drift**
  - File: `backend/app/core/ingestion/fixture_loader.py`, `backend/app/core/retrieval/index_store.py`.
  - Effect: KB APIs read 4 docs / 7 chunks from `processed/`, retrieval reads 40 docs / 9303 chunks from `index/`. Same workspace, two truths. See milestone SUMMARY for the broader impact (carryover from v1.1 import pipeline).

### Nice-to-have

- **[Nice-to-have] `MockTextProvider` and `BailianTextProvider` live inside `providers/rerank.py`**
  - File: `backend/app/core/providers/rerank.py:69-115`, `backend/app/core/providers/text.py:1-12`.
  - Effect: `providers/text.py` only imports/dispatches; the implementations are in the rerank module. Hurts discoverability, no behavior bug.

- **[Nice-to-have] `_query_alignment_boost` contains a brittle micro-tweak for NVIDIA Q3**
  - File: `backend/app/core/retrieval/rerank_service.py:78-98`.
  - Effect: large hand-tuned boosts (`+6.0`, `+4.0`) for exact phrases ("condensed consolidated statements of income"). Works for NVIDIA demo, but will need re-tuning once Phase 16 starts routing numeric queries through table chunks. Flag for re-review after Phase 15/16.

- **[Nice-to-have] AppleDouble `._*` files on the external volume**
  - Effect: `compileall` fails with "source code string cannot contain null bytes". Cosmetic; not a code defect.

## Phase 15/16 Risk Notes

- Phase 15 will introduce `chunk_type` (`text`/`table`/`table_row`/`table_summary`). `Chunk.metadata` is already `dict[str, Any]`, so additive fields are fine. But the **vector index header gap (Important above) becomes worse** because table chunks will likely be embedded differently — without provenance metadata, a partial reindex will be undetectable.
- Phase 16 will route numeric queries through table chunks. The rerank handcrafted boosts in `rerank_service._query_alignment_boost` may compete with table-aware routing. Plan to retire or scope them once table evidence is first-class.
- `HybridRetriever._supplemental_hits` already hardcodes NVIDIA-revenue-specific markers — Phase 16 should replace this with a structured table-routing path rather than extending the keyword list.

## Recommended Follow-up

1. Rebuild `vector_index.json` against the active embedding provider, or revert `.env` to mock for demo, before any further live testing. **(Blocker)**
2. Add provider/dimension header to `vector_index.json` and validate at load. **(Important)**
3. Split BM25 and vector failure modes in `HybridRetriever.retrieve`. **(Important)**
4. Move text provider implementations to `providers/text.py`. **(Nice-to-have, do alongside Phase 16.)**
