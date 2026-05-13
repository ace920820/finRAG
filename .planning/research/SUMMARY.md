# Research Summary: FinRAG

**Date:** 2026-05-13

## Key Conclusions

- The MVP should be built contract-first around the two integration endpoints: `POST /api/query` and `GET /api/documents`.
- Backend development should prioritize deterministic demo reliability over broad feature coverage.
- The highest-value differentiator is transparent retrieval plus source-grounded structured answers.
- Provider dependencies must be abstracted and mockable because embedding, rerank, and LLM APIs are demo risks.
- Frontend work should be limited to contract support and integration once the external React code arrives.

## Roadmap Implications

- Start with backend schemas, SSE event models, and demo data foundations.
- Build retrieval before generation so the frontend can visualize intermediate retrieval results early.
- Add agent templates and LLM streaming after retrieval/rerank contract is stable.
- Reserve a dedicated phase for frontend-backend integration and demo hardening.

## Open Questions For Phase Planning

- Which concrete API providers and environment variable names should be supported first?
- Where will the demo PDFs/news JSON be sourced or stored?
- Should fallback answers be static fixtures or generated from curated chunks?
