# Requirements: FinRAG v1.4 Advanced RAG Retrieval Architecture

**Milestone:** v1.4 Advanced RAG Retrieval Architecture  
**Defined:** 2026-05-21  
**Last updated:** 2026-05-21 after milestone initialization

## Goal

Upgrade FinRAG from a direct hybrid retrieval demo into a traceable advanced financial RAG architecture that demonstrates structured query understanding, knowledge routing, metadata pre-filtering, multi-stage retrieval, evidence compression, and iterative retrieval reasoning.

## v1.4 Requirements

### Query Understanding

- [ ] **QUERY-01**: Financial research queries produce a structured retrieval plan with entities, intent, task type, metrics, time range, preferred document types, and retrieval strategy.
- [ ] **QUERY-02**: Existing query rewrite, alias expansion, sub-query generation, and intent SSE behavior remain backward compatible while exposing the richer retrieval plan.
- [ ] **QUERY-03**: Query plan tests cover factual metric lookup, analytical trend/risk questions, and reasoning questions across NVIDIA, 贵州茅台, 宁德时代, and 台积电 where applicable.

### Routing And Filtering

- [ ] **ROUTE-01**: Queries route to specialized retrieval strategies such as table-fact-first, financial-report section search, research-report analysis, and general hybrid fallback.
- [ ] **ROUTE-02**: Retrieval applies metadata pre-filters before expensive recall when the query plan identifies company, document type, period/date, chunk type, metric, or collection constraints.
- [ ] **ROUTE-03**: Retrieval/debug outputs expose route choice, applied filters, and candidate counts before and after filtering.
- [ ] **ROUTE-04**: Routing and filtering preserve existing table-aware numeric QA behavior and existing general text RAG behavior.

### Retrieval Cascade

- [ ] **CASCADE-01**: Retrieval is represented as a multi-stage cascade with observable stages for planning/routing, metadata filtering, coarse recall, fusion/lightweight selection, rerank, and final evidence selection.
- [ ] **CASCADE-02**: Stage trace data includes stage name, input count, output count, method/source, and any degradation or fallback reason.
- [ ] **CASCADE-03**: SSE and debug retrieval responses expose cascade trace data without breaking existing frontend consumers.
- [ ] **CASCADE-04**: Tests verify deterministic cascade output for representative factual, analytical, and table-fact queries.

### Evidence Compression

- [ ] **EVIDENCE-01**: Generation receives a compact evidence pack that preserves salient facts, numeric values, claims, source metadata, and citation IDs instead of relying only on raw top chunks.
- [ ] **EVIDENCE-02**: Evidence compression deduplicates overlapping chunks from the same source/table/metric and keeps table facts lossless for value, unit, period, and page metadata.
- [ ] **EVIDENCE-03**: Answers remain source-grounded with accurate citation metadata after context compression.
- [ ] **EVIDENCE-04**: Tests cover context builder behavior for text evidence, table facts, duplicate evidence, and citation preservation.

### Iterative Retrieval

- [ ] **ITER-01**: Analytical and reasoning queries can run a lightweight iterative retrieval demo mode that plans evidence needs before issuing multiple targeted retrieval steps.
- [ ] **ITER-02**: Each iterative retrieval step records its purpose, generated retrieval query, route, filters, and selected evidence.
- [ ] **ITER-03**: Iterative retrieval degrades to the normal single-pass cascade when planning fails, retrieval returns no useful evidence, or the query is simple factual lookup.
- [ ] **ITER-04**: SSE/debug traces expose iterative retrieval steps for demonstration without requiring frontend redesign.

### Hierarchical Chunking

- [ ] **HIER-01**: Imported chunks can carry hierarchy metadata such as chunk level, parent ID, section title, section path, and child relationship while preserving existing chunk schema compatibility.
- [ ] **HIER-02**: Retrieval can optionally perform section/table-summary recall followed by child paragraph/table-row evidence selection.
- [ ] **HIER-03**: Reimport/reindex flows remain deterministic after adding hierarchy metadata.
- [ ] **HIER-04**: Hierarchical chunking is validated after the earlier routing/cascade/compression phases are stable, because it may require corpus and index rebuilds.

## Future Requirements

### Graph Memory

- **GRAPH-01**: The system can build an entity-relation memory layer for company, supplier, segment, metric, filing, and macro-factor relationships.
- **GRAPH-02**: Reasoning queries can traverse graph relationships before or alongside vector/BM25 retrieval.

### Sparse Neural Retrieval

- **SPARSE-01**: The system can add a sparse neural retriever such as SPLADE, ColBERT, or uniCOIL behind the retrieval interface when the demo corpus and runtime constraints justify it.

### Production Scale

- **SCALE-01**: The system can support distributed indexes, async indexing jobs, durable job state, and external object storage for large corpora.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Replacing BM25/vector with a new retrieval stack | v1.4 demonstrates architecture improvements on the existing working stack first. |
| Full knowledge graph implementation | Graph memory is useful future work but too broad for this milestone. |
| Sparse neural retrieval model integration | Adds dependency/runtime complexity; routing, filtering, and cascade trace provide higher immediate demo value. |
| Production distributed indexing | The project remains a local interview/demo MVP. |
| OCR and chart extraction | Not part of the advanced retrieval architecture milestone. |
| Frontend redesign | v1.4 may expose new trace data, but visual redesign is not required. |

## Traceability

| Requirement | Phase | Status |
| --- | --- | --- |
| QUERY-01 | Phase 17 | Pending |
| QUERY-02 | Phase 17 | Pending |
| QUERY-03 | Phase 17 | Pending |
| ROUTE-01 | Phase 18 | Pending |
| ROUTE-02 | Phase 18 | Pending |
| ROUTE-03 | Phase 18 | Pending |
| ROUTE-04 | Phase 18 | Pending |
| CASCADE-01 | Phase 19 | Pending |
| CASCADE-02 | Phase 19 | Pending |
| CASCADE-03 | Phase 19 | Pending |
| CASCADE-04 | Phase 19 | Pending |
| EVIDENCE-01 | Phase 20 | Pending |
| EVIDENCE-02 | Phase 20 | Pending |
| EVIDENCE-03 | Phase 20 | Pending |
| EVIDENCE-04 | Phase 20 | Pending |
| ITER-01 | Phase 21 | Pending |
| ITER-02 | Phase 21 | Pending |
| ITER-03 | Phase 21 | Pending |
| ITER-04 | Phase 21 | Pending |
| HIER-01 | Phase 22 | Pending |
| HIER-02 | Phase 22 | Pending |
| HIER-03 | Phase 22 | Pending |
| HIER-04 | Phase 22 | Pending |

**Coverage:**
- v1.4 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

## Source Notes

- User-provided advanced RAG architecture notes from 2026-05-21.
- Existing FinRAG v1.3 codebase: query analysis, hybrid retrieval, rerank service, table facts, SSE workflow, KB management, and table-aware QA.
