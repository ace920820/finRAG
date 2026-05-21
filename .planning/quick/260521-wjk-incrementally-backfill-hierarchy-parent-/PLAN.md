# Quick Task 260521-wjk — Incremental hierarchy backfill

Goal: Add usable hierarchy parent-child metadata to the existing processed/index corpus without recomputing embeddings for existing chunks.

Plan:
1. Add a deterministic backfill script that reads processed chunks and current vector index, annotates existing text/table_row chunks with hierarchy metadata, creates section/table parent chunks where missing, embeds only new parent chunks, and rewrites processed/vector/BM25 indexes atomically enough for local demo use.
2. Add focused tests on a tiny sandbox corpus proving existing vectors are preserved and only parent vectors are appended.
3. Run the script against the live corpus, then verify parent_id/child_ids/section_path counts and hierarchy drill-down traces.

Success criteria:
- Existing vector count is preserved as prefix; new parent vectors are appended.
- Current corpus gains parent_id/child_ids/section_path metadata.
- vector_index provenance remains silicon / BAAI/bge-m3 / dimension 1024.
- Query SSE returns hierarchy_drill_down when eligible.
