---
quick_id: 260521-wvm
slug: upgrade-interview-guide-with-v1-4-backen
date: 2026-05-21
type: docs
files:
  - docs/FinRAG_面试讲解指南.md
  - .planning/quick/260521-wvm-upgrade-interview-guide-with-v1-4-backen/PLAN.md
  - .planning/quick/260521-wvm-upgrade-interview-guide-with-v1-4-backen/SUMMARY.md
  - .planning/STATE.md
---

# Quick Plan: Upgrade Interview Guide With v1.4 Content

## Goal

Upgrade `docs/FinRAG_面试讲解指南.md` into a comprehensive interview guide that reflects Phase 17-22 backend upgrades, Phase 21.1 frontend showcase behavior, and the two new reference docs under `docs/`.

## Inputs

- `docs/FinRAG_v1.4_工业级RAG升级讲解.md`
- `docs/前端新功能介绍.md`
- `.planning/phases/finrag-21.1-frontend-rag-process-showcase-for-v1-4-demo/21.1-01-SUMMARY.md`
- Existing `docs/FinRAG_面试讲解指南.md`

## Tasks

1. Reframe the one-sentence and 1-2 minute pitch around the v1.4 industrial RAG architecture.
2. Add the Phase 17-22 architecture story: query plan, routing/filtering, cascade trace, evidence compression, iterative retrieval, hierarchy drill-down.
3. Add frontend showcase guidance for Query Plan, Route & Filters, Cascade, Iterative Steps, and Hierarchy & Drill-down.
4. Keep honest boundaries: live provider vs mock fallback, JSON vector store vs future FAISS/vector DB, hierarchy metadata may require reimport/reindex for old corpus.
5. Add demo script, common follow-up answers, limitations, and next-step roadmap.

## Verification

- Read the final document for structure and current-state accuracy.
- Grep for core v1.4 terms to ensure the new guide covers the intended features.

