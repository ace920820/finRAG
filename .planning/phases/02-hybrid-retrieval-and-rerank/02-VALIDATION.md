# Phase 2: Hybrid Retrieval And Rerank - Validation Strategy

**Created:** 2026-05-13  
**Status:** Ready for execution

## Validation Architecture

Phase 2 must prove that retrieval and rerank work deterministically on the existing fixture corpus, while live Bailian API support remains optional and explicitly configured.

## Required Checks

- `python -m compileall backend/app/core/providers backend/app/core/retrieval backend/scripts`
- `cd backend && python -m pytest`
- `cd backend && python scripts/build_index.py`
- `cd backend && python -m pytest tests/test_retrieval_service.py tests/test_debug_retrieval.py`

## Acceptance Gates

- Backend can build or load a local retrieval index from processed fixture data.
- BM25 and vector retrieval both return deterministic stage outputs for the demo corpus.
- RRF fusion returns stable top-k candidates with metadata.
- Rerank returns Top 5 payloads and falls back to fused Top 5 when the provider is mocked to fail.
- `/api/debug/retrieval` exposes retrieval-stage outputs without requiring the full `POST /api/query` SSE flow.
- Provider configuration supports Bailian base URL, API key, embedding model, rerank model, and text model through config and `.env` placeholders.

---

*Phase: 02-hybrid-retrieval-and-rerank*  
*Validation strategy created: 2026-05-13*
