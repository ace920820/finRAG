---
quick_id: 260521-wvm
slug: upgrade-interview-guide-with-v1-4-backen
date: 2026-05-21
type: docs
status: complete
---

# Quick Summary: Upgrade Interview Guide With v1.4 Content

## Completed

- Rewrote `docs/FinRAG_面试讲解指南.md` around the current v1.4 architecture instead of the older basic hybrid retrieval story.
- Integrated backend Phase 17-22 content: structured query planning, routing/filtering, cascade tracing, evidence compression, iterative retrieval, and hierarchy drill-down.
- Integrated frontend Phase 21.1 content: Query Plan, Route & Filters, Cascade, Iterative Steps, Hierarchy & Drill-down, plus the no-fake-hierarchy boundary.
- Preserved interview-safe boundaries around live Bailian/Qwen provider usage, mock fallback, JSON vector store, and reimport/reindex requirements for old hierarchy metadata.
- Added demo flow, recommended prompts, common follow-up answers, key file map, verification numbers, and a closing summary script.

## Verification

- `rg "RetrievalPlan|Route & Filters|Cascade|Iterative|Hierarchy|EvidencePack|reimport|116 个测试|RagProcessInspector" docs/FinRAG_面试讲解指南.md`
  - Result: all intended v1.4 concepts are covered.

## Notes

- Did not modify the two reference documents:
  - `docs/FinRAG_v1.4_工业级RAG升级讲解.md`
  - `docs/前端新功能介绍.md`
- Existing unrelated working tree changes were left untouched.

