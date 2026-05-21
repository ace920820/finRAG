# Phase 17: Structured Query Understanding And Retrieval Plan - Research

**Researched:** 2026-05-21 [VERIFIED: environment date]
**Domain:** Deterministic financial query parsing, structured retrieval plan contracts, SSE compatibility [VERIFIED: .planning/ROADMAP.md]
**Confidence:** HIGH for codebase integration shape; MEDIUM for exact ontology field naming until implementation tests lock it [VERIFIED: codebase inspection]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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
- **D-12:** Matching should be implemented behind a small matcher abstraction so a simple dictionary scan can later be swapped for trie, Aho-Corasick, or FlashText-style matching without changing parser output.
- **D-13:** For Phase 17, dependency-light matching is preferred unless the planner finds an already-compatible library with low integration cost. The output contract matters more than the internal matcher algorithm.

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
- **D-22:** `dateparser` may be considered by the planner only if it adds clear value with low dependency risk; regex/rule parsing is acceptable and preferred for core financial periods.

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

### Claude's Discretion

- The exact internal matcher implementation is left to the planner, as long as the public parser output is deterministic and easy to swap later.
- The exact Pydantic field names may be adjusted to match existing style, but the semantic fields in D-28 must be represented.
- The planner may decide whether to keep ontology constants in `query_analysis.py` for Phase 17 or split them into a small `query_ontology.py` module if that reduces clutter without over-abstracting.

### Deferred Ideas (OUT OF SCOPE)

- LLM/Qwen-based query planner fallback for complex ambiguous causal questions — defer to a later milestone or a future enhancement after the rule system is stable.
- Duckling service integration — deferred due local demo/runtime complexity.
- Full trie/Aho-Corasick/FlashText dependency adoption — optional later optimization if simple deterministic matching becomes insufficient.
- Routing/filter execution based on the plan — Phase 18.
- Multi-stage retrieval trace — Phase 19.
- Evidence compression — Phase 20.
- Iterative retrieval planning — Phase 21.
- Hierarchical chunking/reindex impact — Phase 22.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QUERY-01 | Financial research queries produce a structured retrieval plan with entities, intent, task type, metrics, time range, preferred document types, and retrieval strategy. | Add typed Pydantic plan models and deterministic extractors in the existing query analysis boundary. [VERIFIED: .planning/REQUIREMENTS.md, backend/app/core/agent/query_analysis.py:50] |
| QUERY-02 | Existing query rewrite, alias expansion, sub-query generation, and intent SSE behavior remain backward compatible while exposing the richer retrieval plan. | Keep `analyze_query()` returning exactly `(QueryRewriteEvent, IntentDetectedEvent)` and attach `plan` as an optional `QueryRewriteEvent` field. [VERIFIED: backend/app/api/query.py:27-30, backend/app/core/agent/workflow.py:40, backend/app/models/events.py:8-11] |
| QUERY-03 | Query plan tests cover factual metric lookup, analytical trend/risk questions, and reasoning questions across NVIDIA, 贵州茅台, 宁德时代, and 台积电 where applicable. | Extend `backend/tests/test_query_analysis.py` and `backend/tests/test_query_api.py` with canonical field assertions for the required demo queries. [VERIFIED: backend/tests/test_query_analysis.py, backend/tests/test_query_api.py] |
</phase_requirements>

## Summary

Phase 17 should be planned as a contract-preserving parser upgrade, not as a retrieval behavior rewrite. [VERIFIED: .planning/phases/17-structured-query-understanding-and-retrieval-plan/17-CONTEXT.md] The safest implementation is to keep `analyze_query(query)` returning two objects, preserve current rewrite and intent semantics, and add a typed optional retrieval plan on `QueryRewriteEvent`. [VERIFIED: backend/app/core/agent/query_analysis.py:50-59, backend/app/api/query.py:27-30, backend/app/core/agent/workflow.py:40]

The project already has overlapping ontology assets: `query_analysis.py` contains expansion-focused entity definitions, while `table_facts.py` contains stronger company, metric, and quarter aliases used by numeric QA. [VERIFIED: backend/app/core/agent/query_analysis.py:13-39, backend/app/core/retrieval/table_facts.py:12-30] The plan should centralize or import these constants so Phase 17 does not create a third divergent alias list. [VERIFIED: .planning/phases/17-structured-query-understanding-and-retrieval-plan/17-CONTEXT.md]

**Primary recommendation:** Add a small `query_ontology.py` plus typed plan models in `schemas.py`, build the plan inside `analyze_query()`, expose it through `QueryRewriteEvent.plan`, and avoid changing `retrieval_query()` consumption until Phase 18. [VERIFIED: backend/app/core/agent/workflow.py:101-103, .planning/ROADMAP.md]

## Project Constraints (from AGENTS.md)

- FinRAG is a financial-domain RAG Agent MVP for interview demonstration, not a general chatbot. [VERIFIED: AGENTS.md]
- Answers must remain structured, source-grounded, and citation-oriented. [VERIFIED: AGENTS.md]
- Backend package code belongs under `backend/app` with clear module boundaries. [VERIFIED: AGENTS.md]
- Provider clients must remain behind interfaces so deterministic tests do not require network calls. [VERIFIED: AGENTS.md, backend/tests/conftest.py]
- Demo data and built indexes should stay local under backend data paths with generated files ignored as needed. [VERIFIED: AGENTS.md]
- Tests should use fixtures and mock providers for deterministic demo-question validation. [VERIFIED: AGENTS.md, backend/tests/conftest.py]
- Do not use LangChain default chunking for this project’s core pipeline. [VERIFIED: AGENTS.md]
- Do not hard-code a single LLM provider into workflow logic. [VERIFIED: AGENTS.md]
- All coding and phase execution must apply `karpathy-guidelines`: simple, surgical, goal-driven, and verified. [VERIFIED: AGENTS.md, /Users/jamiezhao/.codex/skills/karpathy-guidelines/SKILL.md]
- Direct repo edits should be made through GSD workflow entry points unless explicitly bypassed. [VERIFIED: AGENTS.md]
- No project-local skills were found under `.claude/skills` or `.agents/skills`. [VERIFIED: filesystem scan]
- `CLAUDE.md` was not present in the project root during research. [VERIFIED: filesystem scan]

## Standard Stack

### Core
| Library / Module | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `re` / string normalization | Python 3.9.6 runtime | Regex financial-period parsing, alias matching, punctuation cleanup | Existing table fact retrieval already uses regex and deterministic string matching successfully. [VERIFIED: python3 --version, backend/app/core/retrieval/table_facts.py:55-63] |
| Pydantic | 2.12.5 installed; requirement `>=2.6,<3.0` | Typed retrieval plan and SSE payload models | Existing API/event contracts are Pydantic models. [VERIFIED: importlib.metadata, backend/requirements.txt, backend/app/models/events.py:8-31, backend/app/models/schemas.py:48-80] |
| Existing `QueryIntent` | `Literal["factual", "analytical", "reasoning"]` | Backward-compatible public intent surface | Current generator and tests consume these values. [VERIFIED: backend/app/models/schemas.py:6-8, backend/app/core/agent/generator.py, backend/tests/test_query_analysis.py] |
| Existing `DocType` | `Literal["financial_report", "research_report", "news"]` | Preferred document type values inside the plan | Existing retrieval result schemas use this exact doc type set. [VERIFIED: backend/app/models/schemas.py:6, backend/app/models/schemas.py:53-63] |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `backend/app/core/retrieval/table_facts.py` constants | In-repo module | Reuse `COMPANY_ALIASES`, `METRIC_ALIASES`, and `QUARTER_ALIASES` | Use as the source data for entity, metric, and quarter ontology to preserve numeric QA compatibility. [VERIFIED: backend/app/core/retrieval/table_facts.py:12-30] |
| Pytest | 8.4.2 installed; requirement `>=8.0,<9.0` | Parser, SSE, workflow regression tests | Existing backend tests use pytest and mock providers. [VERIFIED: importlib.metadata, backend/requirements.txt, backend/tests/conftest.py] |
| FastAPI TestClient / httpx | FastAPI 0.128.8, httpx 0.28.1 installed | SSE endpoint compatibility tests | Existing query endpoint tests use `TestClient`. [VERIFIED: importlib.metadata, backend/tests/test_query_api.py] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Simple dictionary scan | Trie / Aho-Corasick / FlashText-style matcher | Deferred because current demo ontology is small and the user locked dependency-light matching as acceptable. [VERIFIED: 17-CONTEXT.md] |
| Regex/rule financial period parser | `dateparser` | Not needed for the required fiscal quarter patterns and adds dependency risk for little Phase 17 value. [VERIFIED: 17-CONTEXT.md, backend/requirements.txt] |
| In-process rules | Duckling service | Explicitly out of scope because Phase 17 must not add a heavy service dependency. [VERIFIED: 17-CONTEXT.md] |
| Rule parser | LLM query planner | Explicitly out of scope for Phase 17. [VERIFIED: 17-CONTEXT.md] |

**Installation:**
```bash
# No new package should be required for Phase 17.
```

**Version verification:** Python package versions were verified locally with `importlib.metadata`; no npm packages are part of this backend phase. [VERIFIED: local command]

## Architecture Patterns

### Recommended Project Structure
```text
backend/app/
├── core/agent/query_analysis.py      # public analyze_query(), classify_intent(), detect_entities()
├── core/agent/query_ontology.py      # small shared ontology constants and matcher helpers
├── core/retrieval/table_facts.py     # imports/reuses ontology constants for numeric QA
├── models/schemas.py                 # RetrievalPlan and nested plan model contracts
└── models/events.py                  # QueryRewriteEvent gains optional plan
```

This structure keeps the public query analysis entry point stable while removing duplicate entity/metric aliases between query analysis and table-fact retrieval. [VERIFIED: backend/app/core/agent/query_analysis.py:50, backend/app/core/retrieval/table_facts.py:12-30]

### Pattern 1: Add Typed Plan Models Without Replacing Existing Events
**What:** Add Pydantic models such as `QueryEntity`, `QueryMetric`, `QueryTimeRange`, and `RetrievalPlan`, then add `plan: Optional[RetrievalPlan] = None` to `QueryRewriteEvent`. [VERIFIED: backend/app/models/events.py:8-11, backend/app/models/schemas.py:1-8]
**When to use:** Use this in Phase 17 because SSE already emits `query_rewrite` first and tests assert that order. [VERIFIED: backend/app/api/query.py:29-30, backend/tests/test_query_api.py:38]
**Example:**
```python
# Source: existing Pydantic schema style in backend/app/models/schemas.py and events.py
RetrievalStrategy = Literal[
    "table_fact_first",
    "financial_report_first",
    "research_report_analysis",
    "general_hybrid",
]

class RetrievalPlan(BaseModel):
    original_query: str
    normalized_query: str
    intent: QueryIntent
    task_type: QueryTaskType
    entities: list[QueryEntity] = Field(default_factory=list)
    metrics: list[QueryMetric] = Field(default_factory=list)
    time_range: Optional[QueryTimeRange] = None
    preferred_doc_types: list[DocType] = Field(default_factory=list)
    retrieval_strategy: RetrievalStrategy = "general_hybrid"
    filters: dict[str, Any] = Field(default_factory=dict)
    signals: list[str] = Field(default_factory=list)
```

### Pattern 2: Keep `analyze_query()` as the Compatibility Boundary
**What:** `analyze_query()` should still return `(QueryRewriteEvent, IntentDetectedEvent)` and should build `rewrite.plan` internally. [VERIFIED: backend/app/core/agent/query_analysis.py:50-59]
**When to use:** Use this because both `/api/query` and `QueryWorkflow.run()` unpack two values. [VERIFIED: backend/app/api/query.py:27, backend/app/core/agent/workflow.py:40]
**Example:**
```python
# Source: backend/app/core/agent/query_analysis.py existing public function
def analyze_query(query: str) -> tuple[QueryRewriteEvent, IntentDetectedEvent]:
    original = query.strip()
    normalized = normalize_query(original)
    expanded = _expand_terms(original)
    intent = classify_intent(original)
    plan = build_retrieval_plan(original_query=original, normalized_query=normalized, intent=intent)
    rewrite = QueryRewriteEvent(
        original=original,
        expanded=expanded,
        sub_queries=_build_sub_queries(original, intent, expanded),
        plan=plan,
    )
    return rewrite, IntentDetectedEvent(intent=intent, template=_template_for_intent(intent))
```

### Pattern 3: Match on Normalized Text, Preserve Original Text
**What:** Use `original_query = query.strip()` for display, generation, and existing rewrite behavior; use normalized text for extraction. [VERIFIED: 17-CONTEXT.md, backend/app/core/agent/query_analysis.py:50-59]
**When to use:** Use this for entity, metric, and time parsing so Latin aliases can match case-insensitively without changing the user-visible query. [VERIFIED: 17-CONTEXT.md]
**Example:**
```python
def normalize_query(query: str) -> str:
    text = query.strip()
    text = text.translate(FULL_WIDTH_TRANSLATION)
    text = re.sub(r"\s+", " ", text)
    text = text.translate(PUNCTUATION_TRANSLATION)
    return text
```

### Pattern 4: Centralize Ontology, Keep Table Fact Behavior Stable
**What:** Move shared alias constants to `query_ontology.py`, then import them from both query analysis and table facts. [VERIFIED: backend/app/core/agent/query_analysis.py:13-39, backend/app/core/retrieval/table_facts.py:12-30]
**When to use:** Use this because `query_analysis.py` currently canonicalizes NVIDIA as `英伟达`, while table facts canonicalize NVIDIA as `NVIDIA`. [VERIFIED: backend/app/core/agent/query_analysis.py:24-28, backend/app/core/retrieval/table_facts.py:12-17]
**Example:**
```python
COMPANY_ALIASES = {
    "NVIDIA": ("nvidia", "英伟达", "nvda"),
    "贵州茅台": ("贵州茅台", "茅台", "600519", "moutai"),
    "宁德时代": ("宁德时代", "catl", "300750"),
    "台积电": ("台积电", "tsmc", "2330"),
}
```

### Anti-Patterns to Avoid
- **Changing `analyze_query()` arity:** This would break existing direct callers that unpack two return values. [VERIFIED: backend/app/api/query.py:27, backend/app/core/agent/workflow.py:40]
- **Adding a new SSE event before `retrieval_complete`:** Current tests assert the first four event names exactly. [VERIFIED: backend/tests/test_query_api.py:38]
- **Routing retrieval in Phase 17:** Phase 18 owns route/filter execution, so Phase 17 should only expose `retrieval_strategy` and `filters` as plan data. [VERIFIED: .planning/ROADMAP.md]
- **Duplicating metric aliases:** Divergent metric aliases would risk breaking `is_table_metric_query()` and table fact lookup. [VERIFIED: backend/app/core/retrieval/table_facts.py:162-169, backend/app/core/retrieval/hybrid.py:168-172]
- **Adding LLM/date service dependencies:** Phase 17 explicitly forbids LLM planning and Duckling service use. [VERIFIED: 17-CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API/event contracts | Loose nested dictionaries | Pydantic models in `schemas.py` and optional event field in `events.py` | Existing contracts use Pydantic and tests serialize event models. [VERIFIED: backend/app/models/events.py, backend/app/models/schemas.py, backend/tests/test_sse_formatter.py] |
| Large-scale NLP understanding | LLM call, embedding classifier, training pipeline | Rule + dictionary + ontology + regex parser | Phase 17 explicitly requires deterministic no-LLM parsing. [VERIFIED: 17-CONTEXT.md] |
| Generic date understanding | Duckling service or broad date NLP | Small financial-period regex parser | Required expressions are years, quarters, fiscal quarter strings, latest/recent, and recent-year ranges. [VERIFIED: 17-CONTEXT.md] |
| New alias taxonomy | Separate constants in every module | Shared ontology constants | Existing code already has two alias sources with NVIDIA canonical mismatch. [VERIFIED: backend/app/core/agent/query_analysis.py:24-28, backend/app/core/retrieval/table_facts.py:12-17] |

**Key insight:** The hard part in Phase 17 is not parsing complexity; it is preserving contracts while making enough structured state available for Phase 18. [VERIFIED: .planning/ROADMAP.md, backend/tests/test_query_api.py]

## Common Pitfalls

### Pitfall 1: Breaking SSE Event Order
**What goes wrong:** Adding a separate `query_plan` event before retrieval can fail tests and frontend assumptions. [VERIFIED: backend/tests/test_query_api.py:38]
**Why it happens:** Current endpoint yields `query_rewrite`, `intent_detected`, `retrieval_complete`, and `rerank_complete` in that order. [VERIFIED: backend/app/api/query.py:29-65]
**How to avoid:** Put plan data inside `query_rewrite.plan` for Phase 17. [VERIFIED: 17-CONTEXT.md D-35]
**Warning signs:** `test_query_endpoint_streams_expected_events` fails on `event_names[:4]`. [VERIFIED: backend/tests/test_query_api.py:38]

### Pitfall 2: Changing Retrieval Query Text Too Early
**What goes wrong:** Existing table-aware numeric QA may stop finding facts if rewrite expansion or retrieval query assembly changes. [VERIFIED: backend/app/core/agent/workflow.py:101-103, backend/app/core/retrieval/hybrid.py:168-172]
**Why it happens:** Retrieval still consumes a string made from `rewrite.original`, `rewrite.expanded`, and `rewrite.sub_queries`. [VERIFIED: backend/app/core/agent/workflow.py:101-103]
**How to avoid:** Preserve current `_expand_terms()` and `_build_sub_queries()` outputs unless a new focused regression proves a specific correction is needed. [VERIFIED: 17-CONTEXT.md D-36]
**Warning signs:** NVIDIA revenue endpoint or table fact retrieval tests fail. [VERIFIED: backend/tests/test_query_api.py:101-151, backend/tests/test_table_fact_retrieval.py]

### Pitfall 3: Alias Drift Between Plan and Table Facts
**What goes wrong:** The plan can say `英伟达` while table facts expect `NVIDIA`, causing Phase 18 filters to miss table facts. [VERIFIED: backend/app/core/agent/query_analysis.py:24-28, backend/app/core/retrieval/table_facts.py:12-17]
**Why it happens:** Current query analysis and table facts maintain separate entity constants. [VERIFIED: backend/app/core/agent/query_analysis.py:13-39, backend/app/core/retrieval/table_facts.py:12-17]
**How to avoid:** Use table fact canonical company values as the initial shared ontology canonical names. [VERIFIED: backend/app/core/retrieval/table_facts.py:12-17, 17-CONTEXT.md D-11]
**Warning signs:** Parser tests pass for expansions but plan `filters.company` differs from table fact `company`. [VERIFIED: backend/app/core/retrieval/table_facts.py:83-90]

### Pitfall 4: Intent and Task Type Collapsing Into One Field
**What goes wrong:** Replacing `QueryIntent` with detailed task types breaks prompt/template behavior and public contracts. [VERIFIED: backend/app/models/schemas.py:7, backend/app/core/agent/query_analysis.py:101-107]
**Why it happens:** Detailed plan task type is new, but `QueryIntent` is already consumed by generation. [VERIFIED: backend/app/core/agent/generator.py]
**How to avoid:** Keep `intent` as `factual` / `analytical` / `reasoning`; add `task_type` inside `RetrievalPlan`. [VERIFIED: 17-CONTEXT.md D-23-D-25]
**Warning signs:** Existing intent tests or generator prompt tests fail. [VERIFIED: backend/tests/test_query_analysis.py, backend/tests/test_agent_workflow.py]

## Code Examples

Verified patterns from project sources:

### Current Analyze Query Contract
```python
# Source: backend/app/core/agent/query_analysis.py:50-59
def analyze_query(query: str) -> tuple[QueryRewriteEvent, IntentDetectedEvent]:
    normalized_query = query.strip()
    expanded = _expand_terms(normalized_query)
    intent = classify_intent(normalized_query)
    rewrite = QueryRewriteEvent(
        original=normalized_query,
        expanded=expanded,
        sub_queries=_build_sub_queries(normalized_query, intent, expanded),
    )
    return rewrite, IntentDetectedEvent(intent=intent, template=_template_for_intent(intent))
```

### Current SSE Emission Contract
```python
# Source: backend/app/api/query.py:27-30
rewrite, intent = analyze_query(request.query)
yield format_sse_event("query_rewrite", rewrite)
yield format_sse_event("intent_detected", intent)
```

### Current Retrieval Query Assembly
```python
# Source: backend/app/core/agent/workflow.py:101-103
def retrieval_query(rewrite: QueryRewriteEvent) -> str:
    parts = [rewrite.original] + rewrite.expanded[:8] + rewrite.sub_queries[:2]
    return " ".join(part for part in parts if part)
```

### Existing Financial Alias Source
```python
# Source: backend/app/core/retrieval/table_facts.py:12-30
COMPANY_ALIASES = {
    "NVIDIA": ("nvidia", "英伟达", "nvda"),
    "贵州茅台": ("贵州茅台", "茅台", "600519", "moutai"),
    "宁德时代": ("宁德时代", "catl", "300750"),
    "台积电": ("台积电", "tsmc", "2330"),
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Query expansion-only analysis | Typed structured retrieval plan attached to existing rewrite event | Phase 17 planned for v1.4 | Enables Phase 18 routing without breaking current string retrieval. [VERIFIED: .planning/ROADMAP.md] |
| Separate entity aliases in query analysis and table facts | Shared ontology constants imported by both modules | Phase 17 planned | Prevents canonical company and metric drift. [VERIFIED: backend/app/core/agent/query_analysis.py:13-39, backend/app/core/retrieval/table_facts.py:12-30] |
| One public intent field | Public `QueryIntent` plus internal plan `task_type` | Phase 17 planned | Preserves old prompt/SSE behavior while adding retrieval-specific detail. [VERIFIED: 17-CONTEXT.md D-23-D-25] |

**Deprecated/outdated:**
- LLM-based query planning is out of scope for Phase 17. [VERIFIED: 17-CONTEXT.md]
- Duckling service integration is out of scope for Phase 17. [VERIFIED: 17-CONTEXT.md]
- Full trie/Aho-Corasick/FlashText dependency adoption is deferred unless future ontology scale requires it. [VERIFIED: 17-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The planner can choose exact Pydantic field names as long as D-28 semantics are represented. [ASSUMED] | Architecture Patterns | Low; CONTEXT.md explicitly allows field-name adjustment, but tests must lock final names. |

## Open Questions

1. **Should `QueryRewriteEvent.plan` be omitted when `None` or serialized as `null`?** [VERIFIED: backend/app/models/events.py]
   - What we know: Existing event formatter serializes Pydantic payloads and tests only assert current fields, not absence of extras. [VERIFIED: backend/tests/test_sse_formatter.py, backend/tests/test_query_api.py]
   - What's unclear: Frontend tolerance for extra optional `plan` field was not inspected in this research pass. [ASSUMED]
   - Recommendation: Add `plan` always for query rewrite after Phase 17 and keep old fields unchanged. [VERIFIED: 17-CONTEXT.md D-35]

2. **Should ontology constants live in `core/agent` or `core/retrieval`?** [VERIFIED: backend/app/core/agent/query_analysis.py, backend/app/core/retrieval/table_facts.py]
   - What we know: Both agent analysis and table fact retrieval need the constants. [VERIFIED: backend/app/core/agent/query_analysis.py:13-39, backend/app/core/retrieval/table_facts.py:12-30]
   - What's unclear: The project has no established shared ontology module yet. [VERIFIED: filesystem/code scan]
   - Recommendation: Put `query_ontology.py` under `backend/app/core/agent` for Phase 17, and import from `table_facts.py`; this is small and avoids broad package reshaping. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend parser and tests | ✓ | 3.9.6 | None needed. [VERIFIED: local command] |
| Pydantic | Plan/event schemas | ✓ | 2.12.5 | None needed; already installed. [VERIFIED: local command] |
| Pytest | Validation | ✓ | 8.4.2 | None needed. [VERIFIED: local command] |
| FastAPI | SSE query endpoint tests | ✓ | 0.128.8 | None needed. [VERIFIED: local command] |
| httpx | FastAPI TestClient dependency | ✓ | 0.28.1 | None needed. [VERIFIED: local command] |
| New NLP/date/parser dependency | Not required | N/A | N/A | Use stdlib rules. [VERIFIED: 17-CONTEXT.md, backend/requirements.txt] |

**Missing dependencies with no fallback:**
- None. [VERIFIED: local command]

**Missing dependencies with fallback:**
- None. [VERIFIED: local command]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 [VERIFIED: local command] |
| Config file | none detected under `backend`; `backend/tests/conftest.py` sets import path and mock providers. [VERIFIED: filesystem scan, backend/tests/conftest.py] |
| Quick run command | `cd backend && pytest tests/test_query_analysis.py tests/test_query_api.py tests/test_preview_rewrite.py -q` [VERIFIED: existing test files] |
| Full suite command | `cd backend && pytest -q` [VERIFIED: existing test suite] |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QUERY-01 | Plan contains canonical entities, metrics, time range, task type, doc types, strategy, filters, and signals. | unit | `cd backend && pytest tests/test_query_analysis.py -q` | ✅ |
| QUERY-02 | Existing rewrite/intent/SSE order remains compatible while `query_rewrite.plan` is exposed. | integration | `cd backend && pytest tests/test_query_api.py tests/test_sse_formatter.py -q` | ✅ |
| QUERY-02 | Preview rewrite endpoint and `detect_entities()` remain compatible. | integration/unit | `cd backend && pytest tests/test_preview_rewrite.py -q` | ✅ |
| QUERY-03 | Demo queries cover NVIDIA metric lookup, Moutai trend/causal analysis, CATL risk, and TSMC financial report or metric lookup. | unit/integration | `cd backend && pytest tests/test_query_analysis.py tests/test_query_api.py -q` | ✅ existing files; new cases required |
| QUERY-03 | Table-aware numeric QA still returns table fact metadata for NVIDIA revenue. | integration | `cd backend && pytest tests/test_query_api.py::test_query_endpoint_returns_table_fact_metadata_for_nvidia_revenue -q` | ✅ |

### Sampling Rate
- **Per task commit:** `cd backend && pytest tests/test_query_analysis.py tests/test_query_api.py tests/test_preview_rewrite.py -q` [VERIFIED: existing test files]
- **Per wave merge:** `cd backend && pytest -q` [VERIFIED: existing test suite]
- **Phase gate:** Full suite green before `/gsd-verify-work`. [VERIFIED: .planning/config.json workflow.nyquist_validation=true]

### Wave 0 Gaps
- [ ] `backend/tests/test_query_analysis.py` needs structured plan assertions for all four required demo entities. [VERIFIED: backend/tests/test_query_analysis.py]
- [ ] `backend/tests/test_query_api.py` needs an assertion that `query_rewrite` includes plan data without changing first-four event order. [VERIFIED: backend/tests/test_query_api.py:38-45]
- [ ] `backend/tests/test_schemas.py` or existing event tests need coverage for optional `QueryRewriteEvent.plan` serialization. [VERIFIED: backend/tests/test_schemas.py, backend/tests/test_sse_formatter.py]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Phase 17 does not add authentication behavior. [VERIFIED: .planning/ROADMAP.md] |
| V3 Session Management | no | Phase 17 does not change session state. [VERIFIED: backend/app/models/schemas.py:48-50, .planning/ROADMAP.md] |
| V4 Access Control | no | Phase 17 does not add protected resources or authorization decisions. [VERIFIED: .planning/ROADMAP.md] |
| V5 Input Validation | yes | Keep `QueryRequest.query` Pydantic validation and add deterministic parser handling for arbitrary strings. [VERIFIED: backend/app/models/schemas.py:48-50, backend/tests/test_query_api.py:153-156] |
| V6 Cryptography | no | Phase 17 does not add cryptographic behavior. [VERIFIED: .planning/ROADMAP.md] |

### Known Threat Patterns for Deterministic Query Parsing

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Parser crash on malformed Unicode or punctuation | Denial of Service | Normalize defensively and keep parser pure/no network side effects. [VERIFIED: 17-CONTEXT.md D-05-D-08] |
| Prompt/retrieval query injection through structured plan fields | Tampering | Treat plan fields as extracted metadata only; do not execute plan filters until Phase 18. [VERIFIED: .planning/ROADMAP.md] |
| Sensitive provider leakage during tests | Information Disclosure | Continue mock provider fixtures and do not add network calls. [VERIFIED: backend/tests/conftest.py, AGENTS.md] |

## Recommended Plan Split

1. **Schema contract task:** Add `RetrievalPlan` and nested models/types in `schemas.py`; add optional `plan` to `QueryRewriteEvent`. [VERIFIED: backend/app/models/schemas.py, backend/app/models/events.py]
2. **Ontology/normalization task:** Create small shared ontology helpers for companies, metrics, quarters, and term matching; update table facts to import shared constants without changing behavior. [VERIFIED: backend/app/core/retrieval/table_facts.py:12-30]
3. **Parser task:** Implement normalization, entity extraction, metric extraction, time parsing, task type, strategy/doc-type selection, filters, and signals in `query_analysis.py`. [VERIFIED: backend/app/core/agent/query_analysis.py]
4. **Compatibility wiring task:** Keep `/api/query`, `QueryWorkflow`, `retrieval_query()`, preview rewrite, and generation behavior unchanged except for optional plan serialization. [VERIFIED: backend/app/api/query.py, backend/app/core/agent/workflow.py, backend/app/api/preview_rewrite.py]
5. **Validation task:** Add parser canonical-field tests, SSE plan exposure tests, preview rewrite regression, and table fact numeric QA regression. [VERIFIED: backend/tests/test_query_analysis.py, backend/tests/test_query_api.py, backend/tests/test_preview_rewrite.py]

## Sources

### Primary (HIGH confidence)
- `.planning/phases/17-structured-query-understanding-and-retrieval-plan/17-CONTEXT.md` - locked decisions, deferred scope, and compatibility requirements. [VERIFIED: file read]
- `.planning/REQUIREMENTS.md` - QUERY-01, QUERY-02, QUERY-03 definitions. [VERIFIED: file read]
- `.planning/ROADMAP.md` - Phase 17 boundary and future phase split. [VERIFIED: file read]
- `.planning/STATE.md` - active constraints and milestone history. [VERIFIED: file read]
- `AGENTS.md` - project stack, constraints, and required `karpathy-guidelines` skill. [VERIFIED: file read]
- `backend/app/core/agent/query_analysis.py` - current public parser and rewrite behavior. [VERIFIED: code inspection]
- `backend/app/core/retrieval/table_facts.py` - existing company/metric/quarter aliases and numeric QA parser behavior. [VERIFIED: code inspection]
- `backend/app/api/query.py` - SSE event order and direct `analyze_query()` use. [VERIFIED: code inspection]
- `backend/app/core/agent/workflow.py` - workflow `analyze_query()` and retrieval query use. [VERIFIED: code inspection]
- `backend/app/models/events.py` and `backend/app/models/schemas.py` - current Pydantic contract locations. [VERIFIED: code inspection]
- `backend/tests/test_query_analysis.py`, `backend/tests/test_query_api.py`, `backend/tests/test_preview_rewrite.py` - regression surfaces. [VERIFIED: code inspection]

### Secondary (MEDIUM confidence)
- Local installed package versions from `importlib.metadata`. [VERIFIED: local command]

### Tertiary (LOW confidence)
- None. [VERIFIED: research log]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependency is needed and current installed versions were verified locally. [VERIFIED: backend/requirements.txt, local command]
- Architecture: HIGH - integration points are small and directly verified in code. [VERIFIED: backend/app/core/agent/query_analysis.py, backend/app/api/query.py, backend/app/core/agent/workflow.py]
- Pitfalls: HIGH - compatibility risks map directly to existing tests and code paths. [VERIFIED: backend/tests/test_query_api.py, backend/tests/test_query_analysis.py]
- Exact final Pydantic field names: MEDIUM - CONTEXT.md permits planner discretion, and tests should lock the final names. [VERIFIED: 17-CONTEXT.md]

**Research date:** 2026-05-21 [VERIFIED: environment date]
**Valid until:** 2026-06-20 for codebase-local conclusions; re-check package versions if dependency choices change. [ASSUMED]
