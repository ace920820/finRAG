# Architecture Research: FinRAG

**Date:** 2026-05-13

## Components

| Component | Boundary | Depends On |
|-----------|----------|------------|
| FastAPI API layer | HTTP routes, SSE formatting, error mapping | Schemas, workflow |
| Schema layer | Pydantic models for docs, chunks, events, requests | None |
| Ingestion pipeline | PDF/news parsing, normalization, chunking | Schemas, local data |
| Retrieval stores | FAISS vector index and BM25 index lifecycle | Chunks, embeddings |
| Hybrid retriever | Query search across BM25/vector and RRF fusion | Retrieval stores |
| Reranker | External rerank provider and fallback logic | Hybrid retriever |
| Agent workflow | Rewrite, retrieval, rerank, intent, generation orchestration | All core services |
| Generation | Prompt templates, LLM streaming, citation mapping | Reranked chunks |
| Integration tests | Contract and demo-flow validation | API layer, mocked providers |

## Data Flow

1. `scripts/seed_data.py` creates or validates demo raw/JSON data.
2. `scripts/build_index.py` parses, normalizes, chunks, embeds, and builds FAISS/BM25 indexes.
3. `GET /api/documents` reads processed metadata.
4. `POST /api/query` emits SSE events while workflow progresses.
5. The frontend renders stages and clickable citations from event payloads.

## Suggested Build Order

1. Contract-first backend skeleton and Pydantic schemas.
2. Demo data model, seed script, and document list endpoint.
3. Chunking and index-building pipeline with deterministic fallback data.
4. BM25/vector stores and RRF fusion tests.
5. Rerank provider abstraction and fallback.
6. Agent workflow with mock generation, then real LLM client.
7. SSE contract tests and frontend integration smoke tests.
