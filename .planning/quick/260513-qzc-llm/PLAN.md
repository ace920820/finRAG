# Quick Task 260513-qzc: Fix NVIDIA query hang/no response

## Goal
Fix the backend query path so NVIDIA revenue questions do not hang silently and return either grounded evidence-based output or a clear degraded fallback. Add enough logging to identify whether retrieval, rerank, or generation is blocking.

## Assumptions
- Keep provider architecture unchanged.
- Do not expose API keys or secrets in logs.
- Prefer short network timeouts and graceful fallback over blocking the SSE response.
- Retrieval should still work with existing local indexes.

## Tasks
1. Reproduce and isolate the blocking provider call.
2. Add bounded provider timeouts and graceful fallback.
3. Add stage-level backend logs for query workflow.
4. Make SSE emit early stage events before slow work.
5. Validate NVIDIA query returns timely events.
