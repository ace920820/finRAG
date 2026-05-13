# Feature Research: FinRAG

**Date:** 2026-05-13

## Table Stakes

- Curated financial document ingestion for annual reports, research reports, and news.
- Unified Document and Chunk schemas with metadata for company, date, type, source, and page.
- Hybrid retrieval with both BM25 and vector search results exposed separately.
- Reranked Top 5 chunks with scores and citation IDs.
- Structured Markdown answers with citation markers.
- SSE lifecycle events that let the frontend visualize query rewrite, retrieval, rerank, generation, completion, and errors.
- Document list API for the left sidebar.
- Demo stability for the three prescribed questions.

## Differentiators

- Retrieval process transparency: BM25, vector, and rerank comparison appears in the UI.
- Financial answer templates based on query intent: factual, analytical, reasoning.
- Citation-first generation policy and “资料中未提及” refusal behavior.
- Financial-specific rerank adjustment for time-sensitive queries.

## Anti-Features

- Generic open-domain chatbot behavior.
- Unsourced financial claims.
- Overbuilt authentication, admin, or production ops features.
- Frontend redesign work inside backend phases.

## Complexity Notes

- PDF table extraction is high risk and should have curated JSON fallback.
- SSE event shape must be stabilized before full frontend integration.
- Rerank and LLM APIs require mockable providers and outage fallbacks.
