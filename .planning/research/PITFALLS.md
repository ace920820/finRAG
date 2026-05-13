# Pitfalls Research: FinRAG

**Date:** 2026-05-13

## Common Pitfalls

| Pitfall | Warning Sign | Prevention | Phase |
|---------|--------------|------------|-------|
| Citation drift | Answer citations do not map to actual chunks | Generate citation map from reranked chunks and test done payload | Phase 3 |
| PDF extraction instability | Factual query fails or numbers mismatch | Curated JSON fallback for critical demo figures | Phase 1 |
| SSE contract ambiguity | Frontend needs ad-hoc parsing fixes | Define event Pydantic models before implementation | Phase 1 |
| API provider outage | Demo stalls during embedding/rerank/LLM calls | Mock/demo fallback providers and graceful degraded events | Phases 2-3 |
| Overbuilding frontend | Backend timeline slips | Treat frontend as external integration target | All phases |
| Retrieval opacity | UI cannot show BM25/vector/rerank differences | Preserve separate result lists in `retrieval_complete` | Phase 2 |
| Generic chatbot output | Analysis lacks financial structure | Intent-specific prompt templates and tests | Phase 3 |

## Prevention Strategy

- Favor deterministic demo paths first, then provider-backed paths.
- Lock API contracts with tests before importing frontend code.
- Keep fallback behavior explicit in event payloads so the demo can explain degradation.
