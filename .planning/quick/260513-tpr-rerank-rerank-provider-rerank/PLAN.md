# Quick Task 260513-tpr: Fix Bailian Rerank Provider

## Goal
Find why rerank is degraded, fix the provider call, and verify live rerank returns real relevance scores instead of fallback fusion scores.

## Assumptions
- Keep `.env` secrets local and uncommitted.
- Prefer official DashScope/Bailian API documentation for endpoint and payload shape.
- Preserve mock-provider tests and deterministic fallback behavior.

## Tasks
1. Confirm current degraded failure and provider configuration.
2. Check official rerank API endpoint/payload.
3. Patch `BailianRerankProvider` and response parsing.
4. Add/adjust tests with mocked HTTP response.
5. Validate live debug retrieval no longer degrades.
