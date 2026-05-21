# Quick Task: Evidence Compression Context Engineering

## Goal

Show Phase 20 evidence compression effects in the RAG process inspector: raw evidence size, compact evidence size, compression ratio, and duplicate removal.

## Plan

1. Extend EvidencePack with character totals computed from packed items.
2. Include those totals in the existing final_evidence cascade metadata.
3. Add an Evidence Compression section to the frontend inspector using real snapshot trace metadata.
4. Validate with focused backend tests and frontend type check.
