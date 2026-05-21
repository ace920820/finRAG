# Phase 22: Hierarchical Chunking And Drill-down Retrieval - Research

**Researched:** 2026-05-21  
**Domain:** Backend RAG ingestion metadata, hybrid retrieval cascade, deterministic tests  
**Confidence:** HIGH

## Summary

Phase 22 should add hierarchy as additive `Chunk.metadata` fields, not as new required top-level schema fields. `Chunk`, `RetrievalResultItem`, `RerankResultItem`, `CitationMetadata`, and KB chunk summaries already carry arbitrary `metadata: dict[str, Any]`, so additive hierarchy keys preserve existing consumers and APIs. [VERIFIED: backend/app/models/schemas.py]

The implementation should keep the current local retrieval stack and add a small hierarchy layer around existing chunk import and retrieval. Text import currently emits flat `chunk-N` text chunks, table import emits one `chunk_type="table"` chunk plus `chunk_type="table_row"` children, and retrieval already records a cascade trace with `query_plan`, `coarse_recall`, `metadata_filter`, and `fusion`. [VERIFIED: backend/app/core/ingestion/chunker.py] [VERIFIED: backend/app/core/ingestion/corpus_importer.py] [VERIFIED: backend/app/core/ingestion/table_facts.py] [VERIFIED: backend/app/core/retrieval/hybrid.py]

**Primary recommendation:** Use deterministic parent section/table summary chunks plus child paragraph/table-row metadata, then add optional drill-down inside `HybridRetriever.retrieve()` as an extra cascade stage that expands recalled parents to indexed children before fusion/rerank. [VERIFIED: codebase grep]

## Project Constraints (from AGENTS.md)

- FinRAG is a financial-domain RAG Agent MVP for interview demonstration, not a general chatbot. [VERIFIED: AGENTS.md]
- Answers must remain grounded in retrieved source chunks with precise citation markers and visible retrieval process. [VERIFIED: AGENTS.md]
- Backend stack is FastAPI, Pydantic, FAISS-style local vector retrieval, `rank_bm25` + `jieba`, provider-agnostic embeddings/rerank/LLM, and pytest. [VERIFIED: AGENTS.md]
- Build backend code under `backend/app` with clear module boundaries. [VERIFIED: AGENTS.md]
- Keep provider clients behind interfaces so tests run without network calls. [VERIFIED: AGENTS.md]
- Store demo data and built indexes locally under `backend/app/data` or `backend/data`; generated files may be ignored. [VERIFIED: AGENTS.md]
- Avoid LangChain default chunking for the core pipeline because financial sections and tables need custom chunking. [VERIFIED: AGENTS.md]
- Avoid frontend framework decisions in backend phases. [VERIFIED: AGENTS.md]
- Avoid hard-coding a single LLM provider into workflow logic. [VERIFIED: AGENTS.md]
- Apply `karpathy-guidelines`: think before coding, simplicity first, surgical changes, goal-driven execution, and targeted validation. [VERIFIED: /Users/jamiezhao/.codex/skills/karpathy-guidelines/SKILL.md]
- Do not make direct repo edits outside a GSD workflow unless explicitly asked; this research artifact is the requested GSD planning output. [VERIFIED: AGENTS.md]

## User Constraints

No Phase 22 CONTEXT.md exists, so there are no locked decisions from `/gsd-discuss-phase`. [VERIFIED: `gsd-tools init phase-op 22`]

Additional user constraints from the research request:
- Plan Phase 22 before returning to Phase 21.1. [VERIFIED: user prompt]
- Do not implement Phase 21.1 frontend showcase here. [VERIFIED: user prompt]
- Focus Phase 22 on backend hierarchical chunking and optional drill-down retrieval. [VERIFIED: user prompt]
- Preserve existing chunk consumers and KB/document APIs. [VERIFIED: user prompt]
- Keep deterministic tests and no live model/API dependency. [VERIFIED: user prompt]
- Existing dirty code changes are present; do not touch source files during research. [VERIFIED: `git status --short`]
- Write only `.planning/phases/22-hierarchical-chunking-and-drill-down-retrieval/22-RESEARCH.md`. [VERIFIED: user prompt]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HIER-01 | Imported chunks can carry hierarchy metadata such as chunk level, parent ID, section title, section path, and child relationship while preserving existing chunk schema compatibility. | Use additive `Chunk.metadata` keys because schema already accepts arbitrary metadata and persisted index JSON round-trips chunks. [VERIFIED: backend/app/models/schemas.py] [VERIFIED: backend/app/core/retrieval/index_store.py] |
| HIER-02 | Retrieval can optionally perform section/table-summary recall followed by child paragraph/table-row evidence selection. | Add a retrieval helper that maps recalled parent IDs to children using `bm25_store.chunks`, then append a `hierarchy_drill_down` cascade stage before fusion/rerank. [VERIFIED: backend/app/core/retrieval/hybrid.py] |
| HIER-03 | Reimport/reindex flows remain deterministic after adding hierarchy metadata. | Import tests already compare repeated `documents.json` and `chunks.json`; extend them to assert stable parent IDs, section paths, and child IDs. [VERIFIED: backend/tests/test_corpus_import.py] |
| HIER-04 | Hierarchical chunking is validated after earlier routing/cascade/compression phases are stable because it may require corpus and index rebuilds. | Phase 21 summary states plan/route/cascade/evidence/iterative layers are complete, and no hierarchy fields currently exist. [VERIFIED: .planning/phases/21-agentic-iterative-retrieval-demo-mode/21-01-SUMMARY.md] |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.9.6 installed | Backend runtime | Existing backend and tests run under `python3`; no new runtime needed. [VERIFIED: `python3 --version`] |
| Pydantic | installed 2.12.5, latest 2.13.4 | Schema compatibility and metadata payloads | Existing models use Pydantic v2 `BaseModel` and `Field(default_factory=...)`; no schema migration needed. [VERIFIED: pip index] [VERIFIED: backend/app/models/schemas.py] |
| rank_bm25 | installed/latest 0.2.2 | Keyword recall over chunk content | Existing `BM25Store` indexes `Chunk.content` and preserves chunk metadata in results. [VERIFIED: pip index] [VERIFIED: backend/app/core/retrieval/bm25_store.py] |
| jieba | installed/latest 0.42.1 | Chinese tokenization for BM25 | Existing BM25 tokenization uses `jieba.lcut`, so hierarchy should not alter tokenization. [VERIFIED: pip index] [VERIFIED: backend/app/core/retrieval/bm25_store.py] |
| numpy | installed/latest 2.0.2 | Local vector normalization/scoring | Existing `VectorStore` embeds chunk content and serializes chunks/vectors to JSON. [VERIFIED: pip index] [VERIFIED: backend/app/core/retrieval/vector_store.py] |
| pytest | installed/latest 8.4.2 | Deterministic validation | Existing backend suite uses pytest and passed as Phase 21 baseline with 111 tests. [VERIFIED: pip index] [VERIFIED: Phase 21 summary] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI | installed/latest 0.128.8 | Existing API surface | Phase 22 should not need API route changes unless tests reveal metadata serialization gaps. [VERIFIED: pip index] [VERIFIED: backend/app/models/events.py] |
| httpx | installed/latest 0.28.1 | API tests | Use only if KB/query API regression tests need HTTP-level compatibility checks. [VERIFIED: pip index] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Add metadata to current custom chunker/retriever | LangChain `ParentDocumentRetriever` | LangChain supports parent-child retrieval patterns, but AGENTS.md explicitly says avoid LangChain default chunking for this core pipeline. [CITED: https://python.langchain.com/docs/how_to/parent_document_retriever/] [VERIFIED: AGENTS.md] |
| Add small drill-down helper in `HybridRetriever` | LlamaIndex recursive retriever | Recursive retrieval is a known pattern, but adopting a new framework would be broader than the phase goal and duplicate existing BM25/vector/cascade code. [ASSUMED] |
| Store hierarchy in a separate graph/index | Dedicated graph memory | Graph memory is explicitly future work, out of scope for v1.4 Phase 22. [VERIFIED: .planning/REQUIREMENTS.md] |

**Installation:**
```bash
# No new packages recommended for Phase 22.
cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_hybrid_retrieval.py -q
```

**Version verification:** Current versions were checked with `python3 -m pip index versions ...` on 2026-05-21. [VERIFIED: pip index]

## Architecture Patterns

### Recommended Project Structure

```text
backend/app/core/ingestion/
├── chunker.py          # section-aware text chunk metadata extraction
├── corpus_importer.py  # deterministic parent/child chunk record assembly
└── table_facts.py      # table-row child metadata aligned to table parent IDs

backend/app/core/retrieval/
├── filters.py          # optional hierarchy-aware chunk_type/chunk_level filters
└── hybrid.py           # optional parent recall -> child drill-down stage

backend/tests/
├── test_corpus_import.py
├── test_import_pipeline_integration.py
└── test_hybrid_retrieval.py
```

### Pattern 1: Additive Metadata, Stable Schema

**What:** Keep `Chunk` unchanged and add hierarchy fields under `metadata`: `chunk_type`, `chunk_level`, `parent_id`, `child_ids`, `section_title`, `section_path`, `hierarchy_path`, and for tables `table_id`/`row_index` linkage. [VERIFIED: backend/app/models/schemas.py]

**When to use:** Use this for HIER-01 because all current consumers already pass metadata through retrieval, rerank, evidence packing, citations, KB chunk summaries, and persisted index JSON. [VERIFIED: backend/app/models/schemas.py] [VERIFIED: backend/app/core/agent/context_builder.py] [VERIFIED: backend/app/core/retrieval/index_store.py]

**Example:**
```python
metadata.update({
    "chunk_type": "text",
    "chunk_level": "paragraph",
    "parent_id": section_id,
    "section_title": text_chunk.section_title,
    "section_path": text_chunk.section_path,
})
```

### Pattern 2: Deterministic Parent IDs

**What:** Parent IDs should be derived from stable document identity plus normalized section/table identity, not from mutable list position alone. Existing document IDs and chunk hashes are deterministic because they use content/source hashes. [VERIFIED: backend/app/core/ingestion/corpus_importer.py]

**When to use:** Use stable IDs for section parent chunks and table summary parent chunks so repeated import/reindex produces identical JSON. [VERIFIED: backend/tests/test_corpus_import.py]

**Example:**
```python
section_id = f"{document.doc_id}-s{section_index:04d}-{_hash_text(section_path_key)[:12]}"
```

### Pattern 3: Parent Recall Then Child Expansion

**What:** Retrieve normal BM25/vector/supplemental candidates, identify recalled parent chunks, then expand to child chunks already present in the same in-memory stores before fusion/rerank. [VERIFIED: backend/app/core/retrieval/hybrid.py]

**When to use:** Enable for strategies that benefit from section context, such as `financial_report_first`, `research_report_analysis`, analytical, trend, risk, comparison, and reasoning tasks. Keep factual `table_fact_first` behavior conservative to avoid breaking numeric QA. [VERIFIED: backend/app/core/retrieval/filters.py] [VERIFIED: backend/tests/test_hybrid_retrieval.py]

**Example:**
```python
children = self._hierarchy_child_hits(parent_hits, query, top_k=limit)
supplemental_hits.extend(children)
cascade_trace.append(RetrievalCascadeStage(
    name="hierarchy_drill_down",
    method="parent_child_metadata",
    input_count=len(parent_hits),
    output_count=len(children),
))
```

### Pattern 4: Preserve Existing Trace Semantics

**What:** Add a new optional trace stage only if schema allows it, or encode drill-down counts inside existing `fusion`/`coarse_recall` metadata if changing the Literal is too invasive. Current `RetrievalCascadeStageName` is a closed Literal and does not include `hierarchy_drill_down`. [VERIFIED: backend/app/models/schemas.py]

**When to use:** Prefer extending the Literal with `"hierarchy_drill_down"` only if tests cover SSE/debug serialization; otherwise include `hierarchy_drill_down_count` under existing stage metadata. [VERIFIED: backend/app/models/events.py]

### Anti-Patterns to Avoid

- **Required top-level hierarchy fields on `Chunk`:** This risks breaking old processed/index JSON that lacks the fields. Use optional metadata instead. [VERIFIED: backend/app/models/schemas.py]
- **Replacing chunking with LangChain/LlamaIndex:** This violates the project’s custom financial chunking constraint and is unnecessary for the demo MVP. [VERIFIED: AGENTS.md]
- **Rebuilding retrieval around a separate hierarchy index:** The existing stores already keep full chunk objects in memory, so a dictionary parent-child map is enough. [VERIFIED: backend/app/core/retrieval/bm25_store.py] [VERIFIED: backend/app/core/retrieval/vector_store.py]
- **Applying drill-down to all queries unconditionally:** Table-fact numeric QA already has strict period and metric handling; broad expansion can pollute rerank candidates. [VERIFIED: backend/app/core/retrieval/hybrid.py] [VERIFIED: backend/tests/test_hybrid_retrieval.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full document parser | A new Markdown/PDF AST parser | Existing `raw_loader`, page marker parsing, and simple heading detection in `chunker.py` | The phase only needs section paths from extracted Markdown/text, not a universal parser. [VERIFIED: backend/app/core/ingestion/chunker.py] |
| New vector database/index | Separate parent-child vector DB | Existing `BM25Store`, `VectorStore`, and JSON index store | Current stores already serialize chunks and metadata; new storage increases rebuild risk. [VERIFIED: backend/app/core/retrieval/index_store.py] |
| LLM summarization for section parents | Live summary generation | Deterministic extractive section/table summary content | Tests must not depend on live model/API calls. [VERIFIED: user prompt] |
| New reranker | Custom child scoring model | Existing fusion/rerank path plus lightweight content overlap scoring for child selection | Current pipeline already reranks final candidates and supports fallback. [VERIFIED: backend/app/core/agent/workflow.py] |

**Key insight:** Hierarchy is a metadata and candidate-selection upgrade for this MVP, not a new retrieval platform. [VERIFIED: project constraints]

## Common Pitfalls

### Pitfall 1: Breaking Old Chunk Consumers

**What goes wrong:** Adding required fields to `Chunk` or changing `section` semantics breaks existing processed data, KB chunk summaries, citations, and index reload. [VERIFIED: backend/app/models/schemas.py]
**Why it happens:** Existing APIs assume stable top-level chunk fields and flexible metadata. [VERIFIED: backend/app/models/schemas.py]
**How to avoid:** Keep hierarchy under metadata and leave `chunk_id`, `doc_id`, `section`, `page_num`, `chunk_index`, and `content` behavior compatible. [VERIFIED: backend/app/models/schemas.py]
**Warning signs:** `Chunk(**item)` fails for old JSON or KB/document tests fail.

### Pitfall 2: Non-Deterministic Parent/Child IDs

**What goes wrong:** Reimport produces different `chunks.json` even when raw inputs are unchanged. [VERIFIED: backend/tests/test_corpus_import.py]
**Why it happens:** IDs derived from unordered dictionaries, filesystem glob without sorting, or mutable global chunk positions can drift. [VERIFIED: backend/app/core/ingestion/corpus_importer.py]
**How to avoid:** Sort source/table paths, normalize section paths, and hash stable document/section/table identity. [VERIFIED: backend/app/core/ingestion/corpus_importer.py]
**Warning signs:** Repeated import JSON equality test fails.

### Pitfall 3: Table Parent/Row Child Mismatch

**What goes wrong:** Table row chunks cannot be traced back to their table summary parent, or row children get unrelated parent IDs. [VERIFIED: backend/app/core/ingestion/table_facts.py]
**Why it happens:** Table parent chunk is built in `corpus_importer.py`, but row chunks are built in `table_facts.py`; both need the same deterministic table parent ID. [VERIFIED: backend/app/core/ingestion/corpus_importer.py] [VERIFIED: backend/app/core/ingestion/table_facts.py]
**How to avoid:** Pass or recompute the table parent ID from `document.doc_id` + `table_id`, then set `parent_id` on every row chunk. [VERIFIED: codebase inspection]
**Warning signs:** Table chunk exists but no `table_row` has `metadata.parent_id == table_chunk.chunk_id`.

### Pitfall 4: Candidate Pollution During Drill-down

**What goes wrong:** Recalled parent sections expand to too many children and bury precise table facts or high-relevance chunks. [ASSUMED]
**Why it happens:** Parent-child expansion changes candidate distribution before rerank. [ASSUMED]
**How to avoid:** Cap children per parent, dedupe by chunk ID, and only enable drill-down for appropriate plan strategies/task types. [VERIFIED: backend/app/core/agent/workflow.py]
**Warning signs:** NVIDIA revenue tests stop ranking `table_fact` or income statement evidence near the top.

### Pitfall 5: Closed Cascade Stage Literal

**What goes wrong:** Adding `"hierarchy_drill_down"` trace data fails Pydantic validation. [VERIFIED: backend/app/models/schemas.py]
**Why it happens:** `RetrievalCascadeStageName` is a `Literal` without that value. [VERIFIED: backend/app/models/schemas.py]
**How to avoid:** Update the Literal and tests together, or keep drill-down data inside an existing stage’s metadata. [VERIFIED: backend/app/models/schemas.py]
**Warning signs:** Query/debug API tests fail during event serialization.

## Code Examples

Verified patterns from current codebase:

### Current Metadata-Preserving Chunk Import

```python
chunks.append(Chunk(
    chunk_id=f"{document.doc_id}-c{text_chunk.chunk_index:04d}-{chunk_hash}",
    doc_id=document.doc_id,
    section=text_chunk.section,
    page_num=text_chunk.page_num,
    chunk_index=text_chunk.chunk_index,
    content=text_chunk.content,
    metadata=metadata,
))
```

Source: `backend/app/core/ingestion/corpus_importer.py`. [VERIFIED: backend/app/core/ingestion/corpus_importer.py]

### Current Retrieval Metadata Pass-through

```python
return RetrievalResultItem(
    chunk_id=payload["chunk_id"],
    title=payload["title"],
    doc_type=payload["doc_type"],
    company=payload["company"],
    date=payload["date"],
    page=payload["page"],
    preview=payload["preview"],
    score=float(payload.get("score", getattr(hit, "score", 0.0))),
    content=payload.get("content", payload["preview"]),
    metadata=dict(payload.get("metadata", {})),
)
```

Source: `backend/app/core/retrieval/hybrid.py`. [VERIFIED: backend/app/core/retrieval/hybrid.py]

### Current Deterministic Import Test Pattern

```python
first_chunks_json = first.chunks_path.read_text(encoding="utf-8")
second = import_corpus(...)
assert first_chunks_json == second.chunks_path.read_text(encoding="utf-8")
```

Source: `backend/tests/test_corpus_import.py`. [VERIFIED: backend/tests/test_corpus_import.py]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat chunks only | Parent-child or small-to-large retrieval is a common RAG pattern where smaller child chunks improve matching and parent/section context improves evidence completeness. | Current RAG practice; verified in official LangChain ParentDocumentRetriever docs on 2026-05-21. | FinRAG can implement the pattern locally without adopting LangChain. [CITED: https://python.langchain.com/docs/how_to/parent_document_retriever/] |
| Single-stage retrieval lists | Multi-stage RAG pipelines include preprocessing, alignment, chunking, indexes, and hierarchical indexes. | Current Azure advanced RAG guidance checked 2026-05-21. | Phase 22 fits naturally as a hierarchical index/candidate expansion step after v1.4 cascade layers. [CITED: https://learn.microsoft.com/en-us/azure/developer/ai/advanced-retrieval-augmented-generation] |
| Live/generated summaries for every parent | Deterministic extractive parent content for testable MVP | Project-specific constraint, 2026-05-21. | Avoid live model calls and keep index rebuild reproducible. [VERIFIED: user prompt] |

**Deprecated/outdated:**
- LangChain default chunking for FinRAG core pipeline: explicitly disallowed by project stack notes. [VERIFIED: AGENTS.md]
- Production distributed indexing for this phase: explicitly out of scope for v1.4. [VERIFIED: .planning/REQUIREMENTS.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LlamaIndex recursive retrieval is a known parent-child/recursive retrieval pattern, but not worth adopting for this phase. | Alternatives Considered | Low; planner should not depend on LlamaIndex details because recommendation is local implementation. |
| A2 | Broad parent expansion can pollute precise table-fact retrieval. | Common Pitfalls | Medium; tests should validate numeric QA behavior after drill-down is added. |

## Open Questions

1. **Should Phase 22 emit explicit section parent chunks for all text sections, or only metadata parents without separate retrievable chunks?**
   - What we know: Requirement HIER-02 says retrieval can recall section/table-summary evidence first, implying parent chunks should be retrievable. [VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: How much section summary content is enough for useful parent recall without bloating indexes.
   - Recommendation: Build deterministic extractive parent chunks from heading + first child previews, capped by character count.

2. **Should drill-down be exposed in SSE/debug as a new cascade stage name?**
   - What we know: Current cascade stage names are closed Literals. [VERIFIED: backend/app/models/schemas.py]
   - What's unclear: Whether frontend Phase 21.1 will expect stage names to be fixed.
   - Recommendation: Add `"hierarchy_drill_down"` only with backend tests; otherwise keep metadata under existing `fusion` stage for compatibility.

3. **Should existing processed corpus/index be rebuilt during Phase 22 execution?**
   - What we know: HIER-04 says hierarchy may require corpus and index rebuilds. [VERIFIED: .planning/REQUIREMENTS.md]
   - What's unclear: Whether the planner should include a committed data artifact rebuild or only code/test support.
   - Recommendation: Plan code and deterministic tests first; include a manual or explicit rebuild task only if project convention currently commits processed/index data.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Backend tests/import scripts | yes | 3.9.6 | none |
| pytest | Validation | yes | 8.4.2 | none |
| pip | Version checks/package availability | yes | 21.2.4 | none |
| FastAPI | Existing API contracts | yes | 0.128.8 installed | none needed |
| Pydantic | Existing schemas | yes | 2.12.5 installed | none |
| rank_bm25 | BM25 retrieval | yes | 0.2.2 installed/latest | none |
| jieba | Chinese tokenization | yes | 0.42.1 installed/latest | none |
| numpy | Vector retrieval | yes | 2.0.2 installed/latest | none |
| Live embedding/rerank APIs | Not required for tests | not required | n/a | `MockEmbeddingProvider` |

**Missing dependencies with no fallback:**
- None for Phase 22 planning/execution. [VERIFIED: environment audit]

**Missing dependencies with fallback:**
- Live model/API access is intentionally not required; tests should use `MockEmbeddingProvider`. [VERIFIED: backend/tests/test_hybrid_retrieval.py]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 [VERIFIED: `python3 -m pytest --version`] |
| Config file | none detected under `backend`; tests run by module invocation [VERIFIED: `rg --files backend`] |
| Quick run command | `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_hybrid_retrieval.py -q` |
| Full suite command | `cd backend && python3 -m pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| HIER-01 | Imported text/table chunks carry `chunk_level`, `parent_id`, `section_title`, `section_path`, and child relationship metadata without schema breakage | unit/integration | `cd backend && python3 -m pytest tests/test_corpus_import.py -q` | yes |
| HIER-02 | Retrieval can recall parent section/table chunks and drill down to paragraph/table-row children | unit | `cd backend && python3 -m pytest tests/test_hybrid_retrieval.py -q` | yes |
| HIER-03 | Repeated import/reindex produces identical hierarchy metadata and index reload preserves it | integration | `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_retrieval_index.py -q` | yes |
| HIER-04 | Existing table-fact, query API, KB/document API, and full backend behavior remain green | regression | `cd backend && python3 -m pytest -q` | yes |

### Sampling Rate

- **Per task commit:** `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_hybrid_retrieval.py -q`
- **Per wave merge:** `cd backend && python3 -m pytest tests/test_corpus_import.py tests/test_import_pipeline_integration.py tests/test_hybrid_retrieval.py tests/test_table_facts.py tests/test_query_api.py tests/test_kb_api.py -q`
- **Phase gate:** `cd backend && python3 -m pytest -q`

### Wave 0 Gaps

- [ ] Extend `backend/tests/test_corpus_import.py` with deterministic text hierarchy assertions for section parent/child metadata. [VERIFIED: backend/tests/test_corpus_import.py]
- [ ] Extend `backend/tests/test_corpus_import.py` or `backend/tests/test_table_facts.py` with table parent -> table_row child linkage assertions. [VERIFIED: backend/tests/test_table_facts.py]
- [ ] Extend `backend/tests/test_hybrid_retrieval.py` with optional drill-down retrieval coverage and table-fact regression. [VERIFIED: backend/tests/test_hybrid_retrieval.py]
- [ ] Extend `backend/tests/test_retrieval_index.py` if persisted index JSON needs explicit hierarchy round-trip coverage. [VERIFIED: backend/app/core/retrieval/index_store.py]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Phase 22 does not add auth surfaces. [VERIFIED: phase scope] |
| V3 Session Management | no | Phase 22 does not alter sessions. [VERIFIED: phase scope] |
| V4 Access Control | limited | Preserve existing KB/document API behavior; do not expose new file paths beyond existing metadata. [VERIFIED: backend/app/models/schemas.py] |
| V5 Input Validation | yes | Keep Pydantic schemas backward-compatible and validate metadata through deterministic tests. [VERIFIED: backend/app/models/schemas.py] |
| V6 Cryptography | no | Phase 22 does not add cryptography. [VERIFIED: phase scope] |

### Known Threat Patterns for Backend RAG Metadata

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Metadata/path leakage via citations or KB chunk responses | Information Disclosure | Do not add new absolute paths beyond existing `source_path`, `table_json_path`, and `table_csv_path`; prefer IDs/titles for hierarchy display. [VERIFIED: backend/app/core/ingestion/corpus_importer.py] |
| Prompt/context pollution from expanded children | Tampering | Keep drill-down bounded, deterministic, and reranked through existing evidence pipeline. [VERIFIED: backend/app/core/agent/workflow.py] |
| Denial of service by unbounded parent-child expansion | Denial of Service | Cap children per parent and top-k expansion; reuse in-memory chunk lists. [ASSUMED] |

## Sources

### Primary (HIGH confidence)

- `AGENTS.md` - project stack, workflow, and coding constraints.
- `/Users/jamiezhao/.codex/skills/karpathy-guidelines/SKILL.md` - simplicity, surgical changes, validation behavior.
- `.planning/STATE.md` - current milestone state and active constraints.
- `.planning/ROADMAP.md` - Phase 22 scope, likely files, success criteria.
- `.planning/REQUIREMENTS.md` - HIER-01 through HIER-04 and out-of-scope items.
- `.planning/phases/21-agentic-iterative-retrieval-demo-mode/21-01-SUMMARY.md` - upstream retrieval pipeline state.
- `backend/app/core/ingestion/chunker.py` - current flat text chunking.
- `backend/app/core/ingestion/corpus_importer.py` - deterministic processed chunk import and table chunk creation.
- `backend/app/core/ingestion/table_facts.py` - table row chunks and facts.
- `backend/app/core/retrieval/hybrid.py` - current hybrid retrieval cascade, supplemental hits, table facts.
- `backend/app/core/retrieval/filters.py` - current metadata filters and strategy chunk types.
- `backend/app/models/schemas.py` - schema compatibility and cascade stage Literal.
- `backend/app/core/retrieval/index_store.py`, `bm25_store.py`, `vector_store.py` - index serialization and metadata pass-through.
- `backend/tests/test_corpus_import.py`, `backend/tests/test_hybrid_retrieval.py` - existing deterministic validation patterns.
- `python3 -m pip index versions ...` - package versions for FastAPI, Pydantic, pytest, rank_bm25, jieba, numpy, httpx.

### Secondary (MEDIUM confidence)

- https://python.langchain.com/docs/how_to/parent_document_retriever/ - verified parent-child retrieval concept; not recommended as a dependency.
- https://learn.microsoft.com/en-us/azure/developer/ai/advanced-retrieval-augmented-generation - verified advanced RAG guidance mentions chunking and hierarchical indexes.

### Tertiary (LOW confidence)

- LlamaIndex recursive retrieval as a comparable pattern; not used for planning-critical implementation. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from project requirements, installed packages, and code imports.
- Architecture: HIGH - based on direct code inspection of ingestion, retrieval, schemas, and tests.
- Pitfalls: MEDIUM - compatibility/determinism pitfalls are verified; candidate pollution risk is an informed assumption requiring tests.

**Research date:** 2026-05-21  
**Valid until:** 2026-06-20 for project-specific code findings; 2026-05-28 for package version currency.
