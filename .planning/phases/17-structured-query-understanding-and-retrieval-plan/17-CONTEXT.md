# Phase 17: Structured Query Understanding And Retrieval Plan - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 17 delivers deterministic structured query understanding for FinRAG. It converts a raw financial research query into a normalized retrieval plan containing entities, metrics, time range, task type, preferred document types, retrieval strategy, and backward-compatible rewrite/intent fields.

This phase does not implement routing/filtering execution, multi-stage retrieval tracing, evidence compression, iterative retrieval, graph memory, or LLM-based query planning. Those are later v1.4 phases.

</domain>

<decisions>
## Implementation Decisions

### Core Interpretation

- **D-01:** Query Understanding is treated as a structured mapping problem, not a deep semantic understanding problem.
- **D-02:** Phase 17 must use a rule + dictionary + ontology + parser approach. No model training and no LLM call are allowed in the primary parser.
- **D-03:** The parser should be deterministic, low-latency, explainable, and easy to debug from tests and SSE/debug payloads.
- **D-04:** Future LLM query planning is allowed only as a later fallback for complex ambiguous causal questions, not as part of Phase 17.

### Normalization

- **D-05:** Add an explicit query normalization step before extraction.
- **D-06:** Normalization should include `strip()`, lowercase comparison for Latin tokens, whitespace cleanup, common full-width to half-width conversion, and punctuation normalization.
- **D-07:** Traditional-to-simplified Chinese conversion is desirable, but Phase 17 should avoid adding a heavy dependency solely for this unless the planner finds a lightweight, deterministic option. A small local mapping for known finance aliases is acceptable.
- **D-08:** The original user query must be preserved for display and generation; normalized text is used for matching and planning.

### Entity Extraction

- **D-09:** Entity extraction is dictionary-driven. Existing company aliases should be promoted into a canonical entity ontology.
- **D-10:** The initial ontology must cover existing demo entities: `NVIDIA`, `贵州茅台`, `宁德时代`, `台积电`, plus existing macro/domain entries where still useful.
- **D-11:** Aliases such as `英伟达`, `NVDA`, `nvidia` must normalize to `NVIDIA`; `茅台`, `600519`, `贵州茅台` normalize to `贵州茅台`; `CATL`, `300750`, `宁德时代` normalize to `宁德时代`; `TSMC`, `2330`, `台积电` normalize to `台积电`.
- **D-12:** Matching should be implemented behind a small matcher abstraction so the parser output is independent of whether the backend is FlashText, trie/Aho-Corasick, or a deterministic fallback matcher.
- **D-13:** Because FinRAG is an industrial RAG capability demo, Phase 17 should use a local, lightweight industrial matcher where feasible. Prefer `flashtext-i18n` as the default keyword matcher because it preserves FlashText-style high-performance dictionary extraction while addressing CJK/Unicode boundary issues. Keep a stdlib fallback matcher for deterministic tests and environments where the dependency is unavailable.
- **D-13A:** Do not hand-roll a complex trie/Aho-Corasick implementation in Phase 17. If future scale requires it, add a separate backend behind the same matcher interface, such as `pyahocorasick`, after benchmark evidence justifies the extra dependency.

### Metric Ontology

- **D-14:** Metric extraction is ontology matching. User-facing aliases map to canonical metric fields.
- **D-15:** Initial metric ontology must include at least `revenue`, `gross_profit`, `gross_margin`, `operating_income`, `net_income`, `eps_diluted`, and YoY/change intent markers.
- **D-16:** Existing aliases in `backend/app/core/retrieval/table_facts.py` should be reused or centralized to avoid divergent metric definitions.
- **D-17:** Metric extraction should support multiple matches when a query asks for comparison or causal analysis involving more than one metric.

### Time Parser

- **D-18:** Time parsing should focus on financial-report expressions needed by the demo rather than broad natural-language date coverage.
- **D-19:** The parser must recognize years, quarters, fiscal quarter expressions, `latest`/`最近`/`近期`, and broad ranges such as `近年`/`recent_years`.
- **D-20:** Examples: `2026年第三季度`, `2026Q3`, `FY2026 Q3`, and `2026 fiscal third quarter` should normalize to a structured year/quarter representation.
- **D-21:** Duckling should not be introduced in Phase 17 because it adds a service/runtime dependency that is too heavy for the local demo.
- **D-22:** Use a two-layer time parser: deterministic financial-period rules first for fiscal years, quarters, latest/recent/recent-years, then `dateparser` as a fallback for ordinary natural-language dates that are not financial reporting periods. Pin a Python-version-compatible range; `dateparser` 1.4.0 requires Python 3.10+, so Python 3.9-compatible environments should use the 1.2.x line.

### Intent And Task Type

- **D-23:** Existing public `QueryIntent` values should remain backward compatible: `factual`, `analytical`, and `reasoning`.
- **D-24:** Add a more specific task type inside the retrieval plan instead of replacing `QueryIntent`.
- **D-25:** Suggested task types: `metric_lookup`, `causal_analysis`, `risk_analysis`, `trend_analysis`, `comparison`, and `general_analysis`.
- **D-26:** Intent and task type should be rule-based. Example: queries containing `为什么`, `原因`, `是不是因为` map toward causal analysis; `风险`, `潜在` map toward risk analysis; `多少`, `是多少`, `营收`, `净利润` map toward metric lookup unless causal/trend markers dominate.

### Retrieval Plan Output

- **D-27:** Add a Pydantic retrieval plan model rather than passing loose dictionaries through workflow code.
- **D-28:** The plan should include original query, normalized query, canonical entities, metrics, time range, task type, preferred document types, retrieval strategy, filters, and parse signals/reasons.
- **D-29:** Suggested retrieval strategies for Phase 17 output: `table_fact_first`, `financial_report_first`, `research_report_analysis`, and `general_hybrid`.
- **D-30:** `table_fact_first` should be chosen for metric/numeric queries with an identified entity and metric.
- **D-31:** `research_report_analysis` should be chosen for risk, industry, trend, and causal analysis queries where narrative evidence is likely needed.
- **D-32:** `financial_report_first` should be chosen for company filing questions without a clear metric fact lookup.
- **D-33:** `general_hybrid` remains the fallback when the parser has low structure or cannot map enough fields.

### Backward Compatibility

- **D-34:** Existing `analyze_query(query) -> (QueryRewriteEvent, IntentDetectedEvent)` callers must keep working.
- **D-35:** `QueryRewriteEvent` may gain an optional `plan` field, or the workflow may emit a separate plan-aware event, but old frontend consumers should not break.
- **D-36:** Existing query rewrite expansion and sub-query behavior should be preserved unless a test proves the new structured plan makes an old expansion wrong.
- **D-37:** Existing table-aware numeric QA behavior must remain green after Phase 17.

### Testing And Demo Coverage

- **D-38:** Add focused parser unit tests before wiring deeper retrieval behavior.
- **D-39:** Tests must cover at least: `英伟达2026年第三季度的总营收是多少？`, `贵州茅台近年净利润变化原因`, `宁德时代近期有哪些潜在经营风险？`, and a 台积电 metric or financial-report query.
- **D-40:** Tests should assert canonical fields, not only non-empty expansions.
- **D-41:** SSE/query endpoint tests should verify that structured plan data is exposed while existing event order and current assertions remain compatible.

### the agent's Discretion

- The exact matcher interface shape is left to the planner, but it must make the FlashText/default backend replaceable without changing `build_retrieval_plan()` output.
- The exact Pydantic field names may be adjusted to match existing style, but the semantic fields in D-28 must be represented.
- The planner may decide whether to keep ontology constants in `query_analysis.py` for Phase 17 or split them into a small `query_ontology.py` module if that reduces clutter without over-abstracting.

</decisions>

<specifics>
## Specific Ideas

- User explicitly prefers Phase 17 as pure rules + ontology + parser, not ML/LLM.
- User wants Query Understanding to produce structures like `{entity: "NVIDIA", metric: "revenue", time: "2026Q3"}`.
- User named trie, Aho-Corasick, and FlashText as industrial matching directions; Phase 17 should visibly implement the industrial matching layer with `flashtext-i18n` and keep a fallback matcher.
- User named `dateparser` and Duckling as mature parser options; Phase 17 should use `dateparser` fallback for non-financial ordinary dates but keep Duckling deferred because it adds a service dependency.
- Future Phase 2-style enhancement can use low-cost Qwen/LLM query planner for complex ambiguous causal questions, but only as a supplement to the rule system.

</specifics>

<canonical_refs>
## Canonical References

### Milestone and phase scope

- `.planning/PROJECT.md` — v1.4 milestone goal and constraints.
- `.planning/REQUIREMENTS.md` — QUERY-01, QUERY-02, QUERY-03.
- `.planning/ROADMAP.md` — Phase 17 boundary, likely files, and success criteria.

### Existing parser and retrieval rules

- `backend/app/core/agent/query_analysis.py` — Current alias expansion, intent classification, and sub-query generation.
- `backend/app/core/retrieval/table_facts.py` — Existing company aliases, metric aliases, quarter aliases, and period matching rules that should be reused or centralized.
- `backend/app/core/agent/workflow.py` — Existing caller of `analyze_query()` and construction of retrieval query.
- `backend/app/models/events.py` — Existing `QueryRewriteEvent` and `IntentDetectedEvent` SSE models.
- `backend/app/models/schemas.py` — Existing `QueryIntent`, `DocType`, query, retrieval, and citation schemas.
- `backend/tests/test_query_analysis.py` — Existing parser regression tests to expand.
- `backend/tests/test_query_api.py` — Existing SSE/query compatibility tests.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `backend/app/core/agent/query_analysis.py`: Already contains the seed shape for entity matching, expansion terms, intent classification, and sub-query generation.
- `backend/app/core/retrieval/table_facts.py`: Already contains stronger financial aliases for companies, metrics, and quarters; Phase 17 should avoid duplicating this ontology in a conflicting way.
- `backend/app/models/events.py`: `QueryRewriteEvent` is the natural event to extend with optional plan metadata if keeping the event list stable.
- `backend/app/models/schemas.py`: Pydantic models and `Literal` types are already the project pattern for API contracts.

### Established Patterns

- Tests default to deterministic mock providers and should not require live API calls.
- Existing SSE event order starts with `query_rewrite`, `intent_detected`, `retrieval_complete`, and `rerank_complete`; Phase 17 should preserve this order unless the frontend and tests are explicitly updated.
- Existing retrieval still receives a string via `retrieval_query(rewrite)`; Phase 17 can prepare structured plan data without forcing Phase 18 routing behavior early.

### Integration Points

- `analyze_query()` should remain the main entry point for query understanding in Phase 17.
- `QueryWorkflow.run()` should carry the structured plan through the workflow enough to expose it, but not yet require `HybridRetriever.retrieve()` to consume it.
- Future Phase 18 will use the retrieval plan for routing and metadata filtering, so Phase 17 should make the plan object easy to pass downstream.

</code_context>

<deferred>
## Deferred Ideas

- LLM/Qwen-based query planner fallback for complex ambiguous causal questions — defer to a later milestone or a future enhancement after the rule system is stable.
- Duckling service integration — deferred due local demo/runtime complexity.
- A dedicated `pyahocorasick` backend and benchmark/pickled automaton flow — defer until the ontology is large enough to justify a second matcher dependency.
- Routing/filter execution based on the plan — Phase 18.
- Multi-stage retrieval trace — Phase 19.
- Evidence compression — Phase 20.
- Iterative retrieval planning — Phase 21.
- Hierarchical chunking/reindex impact — Phase 22.

</deferred>

---

*Phase: 17-structured-query-understanding-and-retrieval-plan*
*Context gathered: 2026-05-21*
