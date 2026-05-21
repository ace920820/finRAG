# Phase 18: Knowledge Routing And Metadata Pre-filtering - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 18 consumes the structured retrieval plan produced in Phase 17 and uses it to route queries into specialized retrieval paths and apply metadata pre-filters before expensive recall.

This phase does not add cascade stage tracing, evidence compression, iterative retrieval, or hierarchical drill-down. Those remain later v1.4 phases.

</domain>

<decisions>
## Implementation Decisions

### Routing Strategy

- **R-01:** Route selection should be deterministic and rule-based, consuming `RetrievalPlan` from Phase 17.
- **R-02:** `table_fact_first` is the primary route for metric or numeric queries when the plan has both a company and a metric.
- **R-03:** `financial_report_first` is the preferred route for company filing / report lookup questions that have a company and time clue but no clear table-fact lookup.
- **R-04:** `research_report_analysis` is the preferred route for risk, causal, trend, comparison, and industry-analysis questions where narrative evidence is likely needed.
- **R-05:** `general_hybrid` remains the fallback when the plan is sparse, ambiguous, or cannot be mapped confidently to a specialized route.

### Metadata Pre-filtering

- **R-06:** Apply metadata pre-filters before expensive recall when the plan supplies usable constraints.
- **R-07:** Filter priority should be conservative and stable: `collection` first when explicit, then `company`, `doc_type`, `chunk_type`, `metric`, and finally `date/period`.
- **R-08:** Pre-filters should be strong by default, but if they over-constrain the candidate set, the retriever should automatically relax them and continue with a fallback path rather than returning an empty result too early.
- **R-09:** Relaxation behavior must be observable in debug output through a fallback reason or relaxed-filter note.

### Table-Fact Priority

- **R-10:** Numeric metric queries with a matched company and metric should strongly prefer table facts before broader hybrid recall.
- **R-11:** Table-fact prioritization must preserve existing table-aware numeric QA behavior from Phase 16.
- **R-12:** Filtering and routing must not regress general text RAG behavior when the query is not a numeric/table-fact query.

### Debug And API Surface

- **R-13:** Routing and filter observability should be exposed in `/api/debug/retrieval` first.
- **R-14:** The normal `/api/query` SSE contract should remain unchanged in Phase 18 except for consuming the plan internally.
- **R-15:** Debug output should include route choice, applied filters, candidate counts before and after filtering, and any relaxation/fallback reason.
- **R-16:** Candidate counts and route metadata are sufficient for Phase 18; full multi-stage cascade trace remains Phase 19.

### Compatibility

- **R-17:** `HybridRetriever.retrieve(query: str)` compatibility must be preserved for existing callers.
- **R-18:** The retriever may accept an optional `RetrievalPlan`, but string-only usage must continue to work.
- **R-19:** Existing SSE event order and existing table-aware QA tests must remain green.

</decisions>

<specifics>
## Specifics

- Phase 17 already provides `RetrievalPlan` with entities, metrics, time range, retrieval strategy, filters, and signals.
- Phase 17 tests already prove that structured plan data can be attached to `query_rewrite` without changing the event order.
- The retrieval stack already has strong table-fact support in `HybridRetriever._table_fact_hits()` and `query_table_facts()`, so Phase 18 should reuse that path instead of inventing a second numeric QA mechanism.
- `/api/debug/retrieval` already returns retrieval and rerank sections, making it the best place to surface routing and filtering metadata first.

</specifics>

<deferred>
## Deferred Ideas

- Cascade stage tracing with per-stage counts and fallback metadata — Phase 19.
- Evidence compression and compact evidence packs — Phase 20.
- Iterative retrieval planning — Phase 21.
- Hierarchical chunking and drill-down retrieval — Phase 22.

</deferred>

---

*Phase: 18-knowledge-routing-and-metadata-pre-filtering*
*Context gathered: 2026-05-21*

