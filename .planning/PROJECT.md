# Project: FinRAG 金融智能研究 Agent

**Initialized:** 2026-05-13  
**Milestone:** Interview-demo MVP  
**Target delivery window:** 2 days  
**Primary owner focus:** Backend development, backend testing, API contract stability, and frontend-backend integration

## What This Is

FinRAG is a financial-domain RAG Agent MVP for interview demonstration. It is not a general chatbot. It demonstrates the complete chain of multi-source financial data governance, hybrid retrieval, reranking, agent analysis, source-grounded generation, and SSE-based streaming delivery.

The system is built for financial researchers and investment-advisory analysts who need structured, cited answers from heterogeneous financial documents.

## Core Value

Users can ask financial research questions and receive structured Markdown analysis that is grounded in retrieved source chunks, includes precise citation markers, and exposes the retrieval process for demonstration and trust.

## Demo Scenarios

1. Factual query: “贵州茅台 2023 年营业收入是多少？同比增长率？”
2. Analytical query: “宁德时代近期有哪些潜在经营风险？”
3. Reasoning query: “美联储加息对 A 股新能源板块可能产生什么影响？”

These three cases drive the MVP. Every backend decision should preserve demo reliability for these scenarios.

## Users

- Financial researchers who need fact extraction and evidence-backed analysis.
- Investment-advisory analysts who need multi-dimensional risk and market-impact reasoning.
- Interview evaluators who need to see end-to-end RAG architecture and traceability, not just a polished chat UI.

## Scope Boundary

The frontend team owns React UI implementation, interaction design, and visual polish. This project initializes planning for the backend system and integration layer. When the React project is imported later, the work here should support contract validation, SSE integration, and end-to-end testing rather than redesigning frontend screens.

## Architecture

```text
[React Frontend]
    ↓ POST /api/query (SSE)
[FastAPI Backend]
    ↓
[Query Rewrite] → alias expansion, optional sub-question split
    ↓
[Hybrid Retrieval]
    ├── FAISS vector retrieval Top 20
    └── BM25 keyword retrieval Top 20
    ↓ RRF fusion
[Rerank] → bge-reranker-large Top 5
    ↓
[Agent Workflow]
    ├── intent classification: factual / analytical / reasoning
    └── structured prompt selection
    ↓
[LLM Generation + Citations]
    ↓ SSE events
[Frontend Rendering]
```

## Technical Decisions

| Area | Decision | Rationale | Outcome |
|------|----------|-----------|---------|
| Backend framework | Python 3.10 + FastAPI | Fast SSE support and Python-native RAG ecosystem | Pending implementation |
| Streaming contract | `POST /api/query` with `text/event-stream` | Single integration point for frontend answer and retrieval-stage updates | Pending implementation |
| Retrieval | FAISS + BM25 + RRF | Demonstrates semantic and lexical retrieval comparison | Pending implementation |
| Rerank | bge-reranker-large API with degradation path | Better Top 5 evidence quality; can fall back to fused Top 5 | Pending implementation |
| Generation | DeepSeek / Qwen / OpenAI compatible LLM client | Flexible API provider switching for demo reliability | Pending implementation |
| Frontend ownership | External React team | Avoid duplicating UI design work; focus on backend and integration | Active constraint |
| Demo data strategy | Real or semi-real curated financial documents plus manual JSON fallback | Prevent PDF/network failures from blocking demo | Pending implementation |

## Requirements

### Validated

(None yet — project is initialized from the requirements document and still needs implementation and validation.)

### Active

- [ ] Backend exposes `GET /api/documents` for imported document metadata.
- [ ] Backend exposes `POST /api/query` as an SSE stream with stable event names and JSON payloads.
- [ ] Data pipeline normalizes PDFs/news into Document and Chunk schemas.
- [ ] Demo dataset includes Guizhou Moutai, CATL, at least one research report, and related news.
- [ ] Hybrid retrieval returns BM25, vector, and fused candidate lists for frontend visualization.
- [ ] Rerank produces Top 5 cited chunks and gracefully degrades when the rerank API is unavailable.
- [ ] Query rewrite expands company aliases and optionally splits complex questions.
- [ ] Agent workflow classifies query intent and selects a structured output template.
- [ ] LLM generation streams Markdown chunks and enforces source-grounded citation behavior.
- [ ] Done event returns latency, token usage, and citation metadata.
- [ ] Backend includes tests for schemas, retrieval fusion, SSE event formatting, and demo-case workflows.
- [ ] Frontend-backend integration validates the imported React client against the API contract.

### Out of Scope

- Full frontend UI design and layout implementation — owned by another team.
- User authentication and account management — not needed for interview demo MVP.
- Production deployment, observability, and multi-tenant operations — beyond two-day demo scope.
- Real-time incremental indexing — mentionable in architecture/P2, not required for MVP.
- Knowledge graph multi-hop reasoning — useful future direction, not required for MVP.
- Large-scale 100k+ document corpus ingestion — local FAISS design should allow it, but demo uses curated data.

## Integration Contract

### Required Endpoints

- `POST /api/query`: SSE stream for query lifecycle events.
- `GET /api/documents`: returns demo document list.
- `POST /api/preview-rewrite`: optional P1 endpoint for query rewrite preview.

### Required SSE Events

- `query_rewrite`
- `retrieval_complete`
- `rerank_complete`
- `intent_detected` (optional but planned)
- `answer_chunk`
- `done`
- `error`
- `ping` heartbeat every 15 seconds

## Success Definition

The project is successful when the backend can run locally at `http://localhost:8000`, the three demo questions produce stable streamed responses with citations, and the imported React frontend can render the full query lifecycle without API-contract changes.

## Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM or embedding API rate limit | Demo failure | Provider abstraction plus cached/demo fallback outputs |
| PDF table parsing instability | Incorrect factual answers | Manually curated JSON fallback for critical financial numbers |
| Rerank API outage | Lower evidence quality | Fall back to fused Top 5 with event metadata explaining degradation |
| SSE contract drift | Frontend integration delay | Define Pydantic event models and contract tests early |
| Frontend arrives late | Reduced integration time | Provide mock SSE examples and executable API smoke tests upfront |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? → Move to Out of Scope with reason.
2. Requirements validated? → Move to Validated with phase reference.
3. New requirements emerged? → Add to Active.
4. Decisions to log? → Add to Key Decisions.
5. “What This Is” still accurate? → Update if drifted.

**After each milestone**:
1. Full review of all sections.
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state.

---
*Last updated: 2026-05-13 after initialization*
