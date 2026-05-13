# Project: FinRAG 金融智能研究 Agent

**Initialized:** 2026-05-13  
**Current shipped milestone:** v1.1 Document Import Pipeline  
**Last updated:** 2026-05-13 after v1.1 milestone completion

## Current State

FinRAG is a local financial-domain RAG Agent demo with a FastAPI backend, React frontend integration, and a repeatable document import pipeline.

Shipped capabilities:

- v1.0 mock-data MVP: backend schemas, fixture data, hybrid retrieval, rerank/generation provider abstraction, SSE query API, frontend integration, and preview rewrite.
- v1.1 document import pipeline: generic PDF extraction through `pdf2md --profile finrag`, raw Markdown artifacts, backend import into `documents.json`/`chunks.json`, deterministic chunking, and BM25/vector index rebuild.
- Real-corpus import has been smoke tested with 40 PDFs across 宁德时代、贵州茅台、NVIDIA、台积电, producing 40 documents and 9303 chunks.

## Core Value

Users can ask financial research questions and receive structured, source-grounded Markdown analysis while the system exposes retrieval and citation evidence for demo trust.

## Current Architecture

```text
PDF/text sources
    ↓ pdf2md --profile finrag
backend/app/data/raw/
    ↓ backend/scripts/import_corpus.py
backend/app/data/processed/documents.json + chunks.json
    ↓ backend/scripts/build_index.py
backend/app/data/index/bm25_index.json + vector_index.json
    ↓ existing FastAPI APIs
React frontend / SSE query workflow
```

## Validated Requirements

- ✓ Mock-data MVP and frontend/backend integration — v1.0.
- ✓ PDF extraction adapter with traceable raw Markdown outputs — v1.1.
- ✓ Markdown/text import into existing FinRAG document/chunk schemas — v1.1.
- ✓ Deterministic chunk IDs/document IDs and index rebuild — v1.1.
- ✓ Existing document API/query flow works with imported corpus contracts — v1.1.

## Active Constraints

- Frontend design remains owned externally; backend work should preserve API contracts and focus on integration/testing.
- `.env` and provider API keys must remain local and uncommitted.
- Tests should stay deterministic and default to mock providers unless explicitly doing live-provider UAT.
- OCR is out of scope unless a future milestone explicitly requires scanned-PDF support.

## Next Milestone Goals

Potential next work:

1. Run real-provider UAT using Alibaba Bailian text, embedding, and rerank models.
2. Improve corpus metadata quality with explicit metadata manifests and better title/company/doc-type normalization.
3. Decide how to manage large generated corpus/index artifacts in git or external storage.
4. Harden frontend/backend integration using the newly imported real corpus.
5. Add OCR only if scanned source PDFs become a requirement.

<details>
<summary>Archived project context before v1.1 completion</summary>

# Project: FinRAG 金融智能研究 Agent

**Initialized:** 2026-05-13  
**Milestone:** v1.1 Document Import Pipeline
**Target delivery window:** Local ingestion pipeline iteration
**Primary owner focus:** Document ingestion, PDF extraction adaptation, chunk generation, index rebuild, and backend validation

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
| Backend framework | Python 3.10 + FastAPI | Fast SSE support and Python-native RAG ecosystem | Implemented in v1.0 |
| Streaming contract | `POST /api/query` with `text/event-stream` | Single integration point for frontend answer and retrieval-stage updates | Implemented in v1.0 |
| Retrieval | BM25 + vector + RRF | Demonstrates semantic and lexical retrieval comparison | Implemented in v1.0; v1.1 will feed real imported chunks |
| Rerank | Bailian-compatible rerank API with degradation path | Better Top 5 evidence quality; can fall back to fused Top 5 | Implemented in v1.0 |
| Generation | Qwen Plus / OpenAI-compatible provider client | Flexible API provider switching for demo reliability | Implemented in v1.0 with mock fallback |
| Frontend ownership | External React team | Avoid duplicating UI design work; focus on backend and integration | Active constraint |
| Data strategy | Fixture fallback plus v1.1 import pipeline | Prevent PDF/network failures while enabling real corpus ingestion | v1.1 active focus |

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


## Required Coding Skill

All coding, code review, refactoring, debugging, and phase execution work in this project must apply the `karpathy-guidelines` skill.

Practical requirements:
- Think before coding: surface assumptions and unclear tradeoffs before implementation.
- Simplicity first: implement the minimum code that satisfies the current phase goal.
- Surgical changes: touch only files required by the active GSD plan or explicit user request.
- Goal-driven execution: define verifiable success criteria and run targeted validation.
- Avoid speculative abstractions, broad refactors, or frontend redesign work unless explicitly requested.



## Current State

- v1.0 mock-data MVP is complete and passed user smoke testing with mock data.
- Backend, frontend integration, query SSE, and preview rewrite are implemented.
- The main known gap is replacing hand-maintained fixture JSON with a real document import pipeline.

## Current Milestone: v1.1 Document Import Pipeline

Goal: adapt the provided `pdf2md/` project and add FinRAG-side import tooling so real PDFs/Markdown can become `documents.json`, `chunks.json`, and rebuilt retrieval indexes.

Planned phases:
1. Phase 6 — PDF Extraction Adapter.
2. Phase 7 — FinRAG Corpus Import And Index Build.

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

</details>
