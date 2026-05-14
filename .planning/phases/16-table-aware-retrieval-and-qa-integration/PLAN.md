# Phase 16 Plan — Table-Aware Retrieval And QA Integration

**Status:** Complete  
**Milestone:** v1.3 Table-Aware RAG  
**Depends on:** Phase 15 — Table Chunking And Structured Facts  
**Requirements:** REQ-v1.3-011, REQ-v1.3-013, REQ-v1.3-007, REQ-v1.3-008  
**Source:** `docs/table处理.txt`

## Goal

Make financial numeric questions reliably retrieve, rank, cite, and answer from structured table evidence.

Phase 16 should use Phase 15 outputs — `chunk_type=table`, `chunk_type=table_row`, and `backend/app/data/processed/table_facts.json` — to answer demo-critical financial table questions such as:

- “英伟达2026年第三季度的总营收是多少？”
- “贵州茅台 2024 年前三季度营业收入是多少？”
- One TSMC revenue / net income table question where extracted facts are available.

This phase should stay backend-focused. Frontend work is limited to additive metadata compatibility if the existing UI needs to display table citations without breaking.

## Current Baseline

Phase 15 rebuilt the 40-PDF corpus with:

- Documents: 40
- Text chunks: 9303
- Table chunks: 4128
- Table-row chunks: 660
- Structured facts: 1558
- Facts path: `backend/app/data/processed/table_facts.json`

Current retrieval has partial table awareness through table chunks and heuristic boosts in:

- `backend/app/core/retrieval/hybrid.py`
- `backend/app/core/retrieval/rerank_service.py`

But the system still lacks a first-class facts lookup path, table-aware citation metadata, and deterministic answer support for numeric table questions.

## Scope

### In Scope

- Add a lightweight table facts loader/query helper over `table_facts.json`.
- Detect financial numeric/metric queries for table-aware routing.
- Use structured facts to supplement or prioritize retrieval evidence.
- Ensure `table_row` / `table` chunks are strongly ranked for matching company, metric, period, and source document.
- Add table metadata to retrieval/rerank/citation objects in a backward-compatible way.
- Make mock answer generation produce concise numeric answers when a high-confidence table fact is present.
- Keep public API shape additive and compatible with existing clients.
- Add regression tests for NVIDIA, Moutai, and one TSMC table-backed query where data supports it.

### Out Of Scope

- No LLM-based table extraction or summarization.
- No new database; continue using local JSON facts for MVP.
- No OCR/chart interpretation.
- No broad frontend redesign.
- No general spreadsheet agent or SQL engine.
- No live model API dependency in tests.

## Design Principles

- Prefer deterministic facts for numeric answers, then table-row chunks, then full table chunks, then ordinary text chunks.
- Keep table-aware logic small and explicit; do not replace the existing RAG pipeline.
- Preserve existing text RAG behavior for non-numeric and non-table questions.
- Expose evidence traceability rather than hiding heuristics.
- Use conservative matching: if company/metric/period confidence is weak, fall back to normal retrieval instead of inventing numbers.

## Data Contracts

### Citation Metadata Additions

Extend `CitationMetadata` additively with optional fields:

```json
{
  "chunk_type": "table_row",
  "table_id": "tbl-a1b4...",
  "metric": "revenue",
  "metric_label": "Revenue",
  "period_label": "Three Months Ended Oct 26 2025",
  "raw_value": "57,006",
  "value": 57006,
  "unit": "USD millions",
  "currency": "USD"
}
```

Existing fields must remain unchanged:

- `chunk_id`
- `title`
- `doc_type`
- `company`
- `date`
- `page`
- `source`
- `section`

### Retrieval / Rerank Item Metadata

Add optional metadata fields to `RetrievalResultItem` and `RerankResultItem`, or a single optional `metadata: dict[str, Any]`, so table citation fields can flow from chunks to the final `done` event.

Preferred minimal option:

```python
metadata: dict[str, Any] = Field(default_factory=dict)
```

This avoids adding many optional schema fields and keeps frontend compatibility additive.

### Table Fact Match Shape

Add an internal dataclass or typed dict for matched facts, e.g. in `backend/app/core/retrieval/table_facts.py`:

```python
@dataclass(frozen=True)
class TableFactMatch:
    fact: dict[str, Any]
    score: float
    reasons: list[str]
```

This is internal only and should not be exposed as a public API contract unless needed by citations.

## Implementation Tasks

### 1. Add table fact loading and query matching

Create a small retrieval helper, e.g.:

- `backend/app/core/retrieval/table_facts.py`

Responsibilities:

- Load `backend/app/data/processed/table_facts.json` using existing settings / processed data dir conventions.
- Return an empty list if the file does not exist or is malformed.
- Detect requested company/entity from query using conservative aliases:
  - NVIDIA / 英伟达 / NVDA
  - 贵州茅台 / 茅台 / 600519
  - 台积电 / TSMC / 2330
  - 宁德时代 / CATL / 300750
- Detect metric:
  - revenue / 营收 / 收入 / 营业收入 / 总营收 → `revenue`
  - gross profit / 毛利 → `gross_profit`
  - operating income / 营业利润 → `operating_income`
  - net income / 净利润 → `net_income`
  - EPS / 每股收益 / diluted → `eps_diluted`
- Detect period hints:
  - fiscal year: 2024 / 2025 / 2026
  - quarter: Q1/Q2/Q3/Q4, 第一季度/第二季度/第三季度/第四季度, 前三季度
  - date hints from source filename / period label.
- Score matches by company, metric, source filename/date, period label, and value presence.

**Verify**

- Unit test loads facts and returns no failure for missing/malformed facts file.
- Unit test matches NVIDIA FY2026 Q3 revenue fact with value `57006`.
- Unit test rejects weak or wrong-company matches.

### 2. Inject fact-backed table evidence into retrieval

Extend `HybridRetriever.retrieve()` or a narrow wrapper inside `QueryWorkflow` to insert table fact evidence into the candidate list before reranking.

Recommended minimal approach:

- In `HybridRetriever`, after normal fusion, ask the table facts helper for top matches.
- Convert each high-confidence fact into a `RetrievalResultItem` with:
  - `chunk_id`: the related table row/table chunk when available, otherwise deterministic `fact_id`.
  - `title`, `company`, `doc_type`, `date`, `page` from fact metadata.
  - `preview` / `content`: concise fact text such as `Revenue = 57,006 USD millions, period ...`.
  - `score`: high enough to enter `fused_top20`, not enough to override exact text matches for unrelated queries.
  - `metadata`: fact/table fields.
- Deduplicate by `chunk_id` / `fact_id`.
- Only inject facts for numeric/metric queries with a recognized metric and company/period signal.

**Verify**

- NVIDIA revenue query returns a fact/table item in top fused candidates.
- Non-financial query such as “宁德时代近期有哪些潜在经营风险？” does not get synthetic fact-only evidence.
- Existing `test_hybrid_retrieval_returns_separate_stage_outputs` and RRF determinism still pass.

### 3. Make reranking table-aware without broad heuristic sprawl

Refine `RerankService._query_alignment_boost()` to prefer structured table evidence:

- Boost `metadata.chunk_type in {"table_row", "table"}` when query asks for numeric metrics.
- Boost exact `metadata.metric` match.
- Boost `metadata.period_label` / `source_pdf_name` / title matching query period.
- Avoid adding more one-off hardcoded table strings.
- Consider reducing or scoping existing revenue Markdown-table boosts if they compete with structured fact matches.

**Verify**

- NVIDIA FY2026 Q3 revenue top-5 contains structured fact/table evidence.
- Top result is from the intended NVIDIA FY2026 Q3 report.
- Existing text queries still produce reasonable non-table evidence.

### 4. Propagate table metadata to citations and debug events

Add optional `metadata` to retrieval/rerank models, or explicit optional fields if metadata dict is rejected during implementation.

Update mapping points:

- `backend/app/core/retrieval/hybrid.py` result construction.
- `backend/app/core/retrieval/rerank_service.py` `_to_rerank_item()`.
- `backend/app/core/agent/workflow.py` citation construction.
- `backend/app/api/query.py` SSE citation construction if it has a separate implementation.

Citation output should include enough metadata for the frontend/debug panel to distinguish table evidence:

- `chunk_type`
- `table_id`
- `metric`
- `period_label`
- `raw_value`
- `value`
- `unit`
- `currency`
- `source`
- `section`

**Verify**

- `/api/query` `rerank_complete.top5[*].metadata.chunk_type` is present for table/fact evidence.
- `/api/query` final `done.citations["1"]` includes table metadata when citation 1 is table-backed.
- Existing clients that ignore metadata still pass tests.

### 5. Add deterministic table-aware answer support

Improve answer generation for high-confidence fact evidence while keeping LLM/mock fallback:

- If the top evidence item has table fact metadata with `value` and `metric`, format a concise numeric conclusion before or through the existing mock provider path.
- Keep citation markers using existing `<span class="cite" data-id="...">` format.
- Include unit/currency and period label when available.
- Do not fabricate if facts are missing; fall back to current generation.

Example expected answer shape:

```markdown
### 结论

英伟达 FY2026 第三季度总营收为 57,006 USD millions。<span class="cite" data-id="1">[1]</span>

### 依据

- 来源：NVDA_nvidia_10q_FY2026Q3_2025-11-19_q4cdn.pdf，第 21 页，表格 tbl-a1b4...。<span class="cite" data-id="1">[1]</span>
```

**Verify**

- Mock provider mode returns `57,006` for NVIDIA Q3 revenue query.
- Answer includes a citation marker.
- If no matching fact exists, answer behavior remains unchanged.

### 6. Add backend regression tests

Add or extend tests:

- `backend/tests/test_table_fact_retrieval.py` for fact loading/matching.
- `backend/tests/test_hybrid_retrieval.py` for top evidence quality.
- `backend/tests/test_query_api.py` for SSE metadata and answer content.
- `backend/tests/test_rerank_service.py` if rerank scoring logic changes materially.

Minimum query coverage:

- NVIDIA FY2026 Q3 revenue: answer/retrieval contains `57,006` and table citation metadata.
- Moutai revenue or net profit query backed by a fact from `table_facts.json`.
- One TSMC table query backed by available extracted facts, chosen after inspecting current facts.
- A non-table risk query remains non-fact-only and passes existing expectations.

**Verify**

Run targeted tests:

```bash
python3 -m pytest \
  backend/tests/test_table_facts.py \
  backend/tests/test_table_fact_retrieval.py \
  backend/tests/test_hybrid_retrieval.py \
  backend/tests/test_query_api.py \
  backend/tests/test_rerank_service.py
```

Run API/data regressions:

```bash
python3 -m pytest \
  backend/tests/test_documents_api.py \
  backend/tests/test_kb_api.py \
  backend/tests/test_kb_import_api.py \
  backend/tests/test_import_pipeline_integration.py
```

## Likely Files

Backend code:

- `backend/app/core/retrieval/table_facts.py` (new)
- `backend/app/core/retrieval/hybrid.py`
- `backend/app/core/retrieval/rerank_service.py`
- `backend/app/core/agent/generator.py`
- `backend/app/core/agent/prompts.py` if prompt formatting needs table evidence guidance
- `backend/app/core/agent/workflow.py`
- `backend/app/api/query.py`
- `backend/app/models/schemas.py`
- `backend/app/models/events.py` only if event schemas need explicit metadata typing

Backend tests:

- `backend/tests/test_table_fact_retrieval.py` (new)
- `backend/tests/test_hybrid_retrieval.py`
- `backend/tests/test_query_api.py`
- `backend/tests/test_rerank_service.py`
- Existing KB/document/import tests as regressions

Frontend code:

- No required frontend implementation.
- If metadata is already rendered generically, do nothing.
- If TypeScript types reject additive table citation fields, update only the minimal type definitions.

## Verification Commands

Confirm current facts include demo targets:

```bash
python3 - <<'PY'
import json
from pathlib import Path
facts = json.loads(Path('backend/app/data/processed/table_facts.json').read_text(encoding='utf-8'))
for company in ('NVIDIA', '贵州茅台', '台积电'):
    matches = [f for f in facts if f.get('company') == company and f.get('metric') in {'revenue', 'net_income'}]
    print(company, len(matches), matches[:2])
PY
```

Run targeted backend tests:

```bash
python3 -m pytest \
  backend/tests/test_table_facts.py \
  backend/tests/test_table_fact_retrieval.py \
  backend/tests/test_hybrid_retrieval.py \
  backend/tests/test_query_api.py \
  backend/tests/test_rerank_service.py
```

Run broader backend regression:

```bash
python3 -m pytest \
  backend/tests/test_documents_api.py \
  backend/tests/test_kb_api.py \
  backend/tests/test_kb_import_api.py \
  backend/tests/test_import_pipeline_integration.py
```

Optional full smoke with mock providers:

```bash
FINRAG_EMBEDDING_PROVIDER=mock \
FINRAG_RERANK_PROVIDER=mock \
FINRAG_TEXT_PROVIDER=mock \
python3 backend/scripts/import_corpus.py \
  --collection-name finrag-user-source-40 \
  --processed-dir "$PWD/backend/app/data/processed" \
  --index-dir "$PWD/backend/app/data/index" \
  --rebuild-index
```

## Acceptance Criteria

- Numeric financial queries can use structured facts from `table_facts.json`.
- NVIDIA FY2026 Q3 revenue query returns/cites `57,006` from table evidence.
- At least one Moutai and one TSMC financial table query are covered by tests when matching facts exist.
- `rerank_complete` and `done.citations` expose table metadata for table-backed evidence.
- Existing text RAG query tests continue to pass.
- Existing KB management and document APIs continue to pass.
- No live model APIs are required for validation.
- Public API changes are additive and backward compatible.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Fact matching returns wrong period | Require metric + company and score period/source hints; fallback to normal RAG when weak. |
| Table facts contain duplicated values | Deduplicate by fact id and prefer source/date/period matches over raw value frequency. |
| Existing heuristic boosts conflict with structured facts | Scope or reduce old one-off boosts after structured fact evidence is inserted. |
| Frontend type mismatch | Add optional metadata only; update minimal frontend types only if build/tests require it. |
| Answers overclaim units/currency | Use `raw_value`, `unit`, and `currency` only when present; otherwise state the raw value without inference. |

## Handoff After Phase 16

After execution, v1.3 should have an end-to-end table-aware RAG demo path:

1. PDF tables are extracted.
2. Table chunks and structured facts are imported.
3. Numeric financial questions retrieve table evidence.
4. Answers cite table-backed sources with traceable metadata.

If remaining work exists after Phase 16, it should be treated as polish or a new milestone, not a blocker for the MVP demo unless core NVIDIA/Moutai/TSMC table questions fail.


## Execution Summary

- Added `backend/app/core/retrieval/table_facts.py` for local structured fact loading and conservative query matching.
- Injected high-confidence table facts into hybrid retrieval as `chunk_type=table_fact` evidence.
- Propagated additive `metadata` through retrieval, rerank, and final citation payloads.
- Added deterministic mock-provider answers for table-backed numeric facts.
- Verified NVIDIA FY2026 Q3 revenue returns `57,006` with table fact citation metadata.
- Added positive facts matching coverage for NVIDIA and Moutai; current Phase 15 facts contain no TSMC facts, so TSMC positive QA remains pending better extracted table facts.
- Added tests for facts matching, retrieval ranking, SSE metadata, and table-backed answers.
- Regression tests passed for query/retrieval/rerank plus KB/document/import APIs.

## Validation Result

- `python3 -m pytest backend/tests/test_table_facts.py backend/tests/test_table_fact_retrieval.py backend/tests/test_hybrid_retrieval.py backend/tests/test_query_api.py backend/tests/test_rerank_service.py` — 14 passed.
- `python3 -m pytest backend/tests/test_documents_api.py backend/tests/test_kb_api.py backend/tests/test_kb_import_api.py backend/tests/test_import_pipeline_integration.py` — 18 passed.
