<!-- GSD:project-start source:PROJECT.md -->
## Project

**Project: FinRAG 金融智能研究 Agent**

FinRAG is a financial-domain RAG Agent MVP for interview demonstration. It is not a general chatbot. It demonstrates the complete chain of multi-source financial data governance, hybrid retrieval, reranking, agent analysis, source-grounded generation, and SSE-based streaming delivery.

The system is built for financial researchers and investment-advisory analysts who need structured, cited answers from heterogeneous financial documents.

**Core Value:** Users can ask financial research questions and receive structured Markdown analysis that is grounded in retrieved source chunks, includes precise citation markers, and exposes the retrieval process for demonstration and trust.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
