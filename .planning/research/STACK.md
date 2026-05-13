# Stack Research: FinRAG

**Date:** 2026-05-13  
**Context:** Greenfield interview-demo MVP with backend/integration ownership

## Recommended Stack

| Layer | Choice | Confidence | Rationale |
|-------|--------|------------|-----------|
| API | FastAPI + Uvicorn | High | Async endpoints and straightforward SSE streaming. |
| Schemas | Pydantic | High | Contract-first request, response, and SSE event models. |
| Vector index | FAISS `IndexFlatIP` | High | Simple local semantic search with normalized embeddings. |
| Keyword search | `rank_bm25` + `jieba` | High | Lightweight Chinese lexical retrieval for demo explainability. |
| Embedding | BGE-M3 compatible API | Medium | Matches requirement and avoids local model setup during demo window. |
| Rerank | bge-reranker-large compatible API | Medium | Improves evidence quality; must have fallback. |
| LLM | Provider-agnostic client for DeepSeek/Qwen/OpenAI | High | Reduces vendor lock-in and supports demo fallback. |
| PDF parsing | `pdfplumber` + PyMuPDF | Medium | Practical mix for text/table extraction with manual fallback. |
| Tests | Pytest + FastAPI TestClient/httpx | High | Enables schema, unit, and endpoint integration validation. |

## Prescriptive Notes

- Build the backend as a Python package under `backend/app` with clear module boundaries matching the requirements document.
- Keep API provider clients behind interfaces so tests can run without network calls.
- Store demo data and built indexes locally under `backend/app/data` or `backend/data`, with generated files ignored if needed.
- Use fixtures and mock providers for deterministic testing of the three demo questions.

## What Not To Use

- Avoid LangChain default chunking for the core pipeline; financial sections and tables need custom chunking.
- Avoid frontend framework decisions in backend phases; frontend UI ownership is external.
- Avoid hard-coding a single LLM provider into workflow logic.
