# Roadmap: FinRAG

**Last updated:** 2026-05-13  
**Current status:** v1.1 Document Import Pipeline shipped.

## Shipped Milestones

| Milestone | Name | Status | Phases | Summary | Archive |
| --- | --- | --- | --- | --- | --- |
| v1.0 | Mock-data MVP | Shipped | 1-5 | FastAPI backend, hybrid retrieval/rerank, SSE query API, React integration, preview rewrite, and mock-data demo readiness. | Prior phase artifacts in `.planning/phases/01-*` through `.planning/phases/05-*` |
| v1.1 | Document Import Pipeline | Shipped | 6-7 | PDF/text-layer extraction, raw Markdown artifacts, FinRAG corpus import, deterministic chunking, and retrieval index rebuild. | `.planning/milestones/v1.1-ROADMAP.md` |

## Current Capabilities

- Backend can run locally and serve existing query/document APIs.
- Corpus data can be generated from source PDFs using `pdf2md --profile finrag`.
- Raw Markdown/text can be imported into `documents.json` and `chunks.json`.
- BM25/vector indexes can be rebuilt from imported chunks.
- Frontend document list and query flow continue using existing API contracts.

## Next Milestone Candidates

- Real-provider UAT with Alibaba Bailian text, embedding, and rerank models.
- Corpus quality improvements: metadata manifests, table cleanup, and document-type heuristics.
- Production data artifact strategy for large processed/index files.
- Frontend/backend polish after real React integration feedback.
- Optional OCR milestone if scanned PDFs become required.

## Archive Index

- v1.1 roadmap archive: `.planning/milestones/v1.1-ROADMAP.md`
- v1.1 requirements archive: `.planning/milestones/v1.1-REQUIREMENTS.md`
