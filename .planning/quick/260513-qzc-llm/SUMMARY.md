# Quick Task 260513-qzc Summary

## Completed
- Fixed relative `FINRAG_INDEX_DIR=backend/app/data/index` resolution so the backend loads the existing index from the project backend root instead of creating `backend/backend/...`.
- Loaded cached BM25 tokenization from `bm25_index.json` instead of rebuilding it on each query startup.
- Made `/api/query` emit `query_rewrite` and `intent_detected` before slow retrieval/rerank/generation work.
- Added provider timeout configuration and stage-level backend logs.
- Added NVIDIA/NVDA query aliases and factual intent handling for `营收`.
- Added entity/topic supplemental retrieval so English NVIDIA revenue chunks surface for Chinese revenue questions.
- Allowed no-evidence generation to reach the text provider with a clear no-local-evidence prompt instead of returning nothing early.

## Validation
- `cd backend && python3 -m pytest tests/test_query_api.py tests/test_debug_retrieval.py tests/test_provider_config.py tests/test_query_analysis.py tests/test_hybrid_retrieval.py` → 13 passed.
- Live smoke: `POST /api/query` with `英伟达最近营收的信息是？` streamed query events, NVIDIA retrieval/rerank evidence, answer chunks, and done in ~5.5s.
