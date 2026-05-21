# Phase 20: Evidence Compression And Context Builder - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 20 introduces a compact evidence pack between rerank and answer generation.

The goal is to reduce context noise while preserving source grounding, citation IDs, table-fact metadata, and enough source detail for existing answers and `done.citations` to remain accurate.

This phase does not add iterative retrieval, new retrieval routes, hierarchical chunking, or frontend redesign. It consumes the single-pass retrieval/rerank outputs and Phase 19 cascade trace as-is.

</domain>

<decisions>
## Implementation Decisions

### Evidence Pack Shape

- **E-01:** Add a dedicated context builder module rather than embedding compression inside `AnswerGenerator`.
- **E-02:** Evidence packs should be deterministic Pydantic models or dataclasses with explicit fields for citation ID, title, doc type, company, date, page, source, section, content summary, and metadata.
- **E-03:** Table facts must be lossless for `raw_value`, `value`, `unit`, `currency`, `period_label`, `metric`, `table_id`, `page_num`, and source filename/path metadata when present.
- **E-04:** Text evidence can be compacted by truncating/salience extraction, but citation ID and source metadata must not be changed.

### Deduplication And Compression

- **E-05:** Deduplicate overlapping evidence conservatively by stable source keys such as `chunk_id`, `source/table_id/metric/period_label/raw_value`, or source/title/page when available.
- **E-06:** Keep one canonical item for duplicate table facts and preserve all citation IDs only if needed for backward compatibility; otherwise keep the selected rerank citation ID.
- **E-07:** Do not summarize numeric table facts into lossy prose.
- **E-08:** Compression should be bounded and deterministic under mock tests; no LLM call should be required to build the evidence pack.

### Generation Integration

- **E-09:** `AnswerGenerator` should receive or build against the compact evidence pack while preserving the existing public `generate(query, intent, evidence)` compatibility when possible.
- **E-10:** Existing mock answer behavior should continue to cite evidence with `<span class="cite" data-id="...">`.
- **E-11:** `done.citations` must remain accurate and should still be built from the evidence selected for generation.
- **E-12:** Existing SSE event order must remain unchanged.

### Observability

- **E-13:** Phase 20 may expose evidence-pack metadata through additive debug/test-visible fields only if useful, but should not require new frontend UI.
- **E-14:** Phase 19 cascade trace should remain intact and should not be repurposed as the evidence pack.

</decisions>

<specifics>
## Specifics

- `RerankService.rerank()` returns `RerankResultItem` objects with citation IDs assigned by rank.
- `AnswerGenerator.generate(query, intent, evidence)` currently accepts a sequence of `RerankResultItem`.
- `build_generation_prompt()` currently serializes the top evidence items directly into prompt text.
- `build_citations()` in `backend/app/core/agent/workflow.py` builds `done.citations` from items with `citation_id` and metadata.
- `/api/query` currently has a direct path: rerank top5 -> `evidence` -> `AnswerGenerator.generate()` -> `done.citations`.
- Table fact metadata already appears on `RerankResultItem.metadata` for numeric QA.

</specifics>

<deferred>
## Deferred Ideas

- Agentic iterative retrieval and multi-step evidence needs — Phase 21.
- Hierarchical chunking / section-to-child drill-down — Phase 22.
- Frontend redesign for viewing evidence packs — out of scope unless later requested.

</deferred>

---

*Phase: 20-evidence-compression-and-context-builder*
*Context gathered: 2026-05-21*
