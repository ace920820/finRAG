# Phase 20: Evidence Compression And Context Builder - Research

**Researched:** 2026-05-21
**Phase:** 20 - Evidence Compression And Context Builder

## Research Goal

Plan a deterministic context builder that turns reranked evidence into compact generation input while preserving citations, table facts, and current SSE/API behavior.

## Current System Shape

### Generation Path

- `/api/query` performs:
  - query analysis
  - retrieval
  - rerank
  - `evidence = rerank_result.top5`
  - `AnswerGenerator().generate(request.query, intent, evidence)`
  - `build_citations(evidence)`
- `QueryWorkflow.run()` has a similar non-streaming orchestration path.
- `AnswerGenerator.generate()` calls `build_generation_prompt(query, intent, evidence)` and falls back to `build_mock_answer(query, intent, evidence)`.
- `build_generation_prompt()` currently serializes each reranked item directly into prompt lines.

### Evidence Shape

- `RerankResultItem` includes:
  - ranking/score fields
  - `title`, `doc_type`, `company`, `date`, `page`
  - `content`
  - `citation_id`
  - arbitrary `metadata`
- Table facts are carried in `metadata` with fields such as `chunk_type=table_fact`, `metric`, `raw_value`, `value`, `unit`, `currency`, `period_label`, `source_pdf_name`, `table_id`, and `page_num`.
- `build_citations()` reads `citation_id`, source/title/page, and metadata from the same evidence objects used by generation.

### Phase 19 Trace

- Phase 19 added cascade trace fields but did not alter generation input.
- The evidence pack should be separate from cascade trace. Trace explains pipeline execution; evidence pack is generation context.

## Recommended Implementation Path

### 1. Add Context Builder Module

Create `backend/app/core/agent/context_builder.py`.

Recommended minimal objects:

```python
class EvidencePackItem(BaseModel):
    citation_id: int
    chunk_id: str
    title: str
    doc_type: DocType
    company: str
    date: str
    page: int | None = None
    source: str | None = None
    section: str | None = None
    content: str
    compact_content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    preserved_fields: dict[str, Any] = Field(default_factory=dict)

class EvidencePack(BaseModel):
    items: list[EvidencePackItem] = Field(default_factory=list)
    original_count: int
    compressed_count: int
    dropped_duplicate_count: int = 0
```

The models can live in `schemas.py` if API-visible, or in `context_builder.py` if internal. Prefer schema models only if the plan decides to expose evidence-pack data later.

### 2. Deterministic Compression Rules

Rules should be simple and testable:

- Deduplicate exact chunk IDs first.
- For table facts, dedupe by:
  - `source_pdf_name/source`
  - `table_id`
  - `metric`
  - `period_label`
  - `raw_value`
- For text chunks, dedupe by:
  - `title`
  - `page`
  - normalized first N chars of content
- Compact content by:
  - keeping full table-fact value/unit/period/source representation;
  - truncating text content to a bounded number of characters with stable suffix;
  - preserving metadata untouched.

No network calls or model calls should be used.

### 3. Generation Integration

Low-risk integration:

- Build an `EvidencePack` after rerank.
- Convert pack items back to `RerankResultItem`-compatible evidence for current prompt/generator, or update prompt builder to accept pack items.
- Prefer minimal public change:
  - `AnswerGenerator.generate(query, intent, evidence, evidence_pack=None)`
  - if `evidence_pack` is provided, prompt uses `evidence_pack.items`;
  - otherwise current behavior remains.
- `build_mock_answer()` can use pack items or compatible evidence sequence.

The API path can become:

```python
evidence_pack = build_evidence_pack(rerank_result.top5)
evidence = evidence_pack.to_rerank_items() or evidence_pack.items
answer_text = AnswerGenerator().generate(request.query, intent, evidence, evidence_pack=evidence_pack)
done.citations = build_citations(evidence_pack.items)
```

However, to avoid wider refactor, keep `build_citations()` accepting any item with the existing citation/source fields.

### 4. Observability

Phase 20 does not require new SSE events.

Possible additive fields if needed:

- `RerankCompleteEvent.evidence_pack_summary`
- or no API exposure, relying on tests for context builder behavior.

Recommendation: keep API surface minimal. Do not expose full evidence pack unless tests or frontend need it.

## Testing Strategy

Add focused tests:

- `backend/tests/test_context_builder.py`
  - table facts preserve raw value, unit, currency, period, table ID, page/source metadata.
  - duplicate table facts collapse deterministically.
  - text evidence compacts long content and keeps citation/source metadata.
  - citation IDs remain stable for retained evidence.
- `backend/tests/test_query_api.py`
  - NVIDIA table-fact query still returns answer with `57,006` and citation metadata.
  - SSE event order remains unchanged.
  - `done.citations` still contains table metadata.
- `backend/tests/test_agent_workflow.py`
  - workflow uses compact evidence pack if `QueryWorkflow` remains a supported path.

Verification:

```bash
cd backend && pytest tests/test_context_builder.py tests/test_query_api.py tests/test_agent_workflow.py -q
cd backend && pytest -q
```

## Risks And Mitigations

- **Losing table fact fields:** explicitly preserve table metadata in `preserved_fields` and metadata.
- **Citation drift:** keep citation IDs from rerank items and build citations from retained pack items.
- **Over-compression:** cap text length but do not alter table fact values.
- **Prompt incompatibility:** keep `AnswerGenerator.generate()` backward compatible.
- **Scope creep:** do not add iterative retrieval or hierarchy-aware drill-down.

## Recommendation

Implement as one executable plan:

1. Add `context_builder.py` and model/tests.
2. Integrate evidence pack into prompt/generator and query workflow with backward compatibility.
3. Add end-to-end regressions for table facts, citation preservation, and unchanged SSE order.

## RESEARCH COMPLETE
