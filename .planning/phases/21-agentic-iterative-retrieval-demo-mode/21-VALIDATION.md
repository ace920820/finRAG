---
phase: 21
slug: agentic-iterative-retrieval-demo-mode
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-21
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none |
| **Quick run command** | `cd backend && pytest tests/test_retrieval_planner.py tests/test_agent_workflow.py tests/test_query_api.py tests/test_debug_retrieval.py -q` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run the focused quick command for the touched test files.
- **After every plan wave:** Run `cd backend && pytest -q`.
- **Before `/gsd-verify-work`:** Full backend suite must be green.
- **Max feedback latency:** 60 seconds for focused tests.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | ITER-01, ITER-02 | T-21-trace | Step trace fields reflect actual retrieval outputs | unit | `cd backend && pytest tests/test_retrieval_planner.py -q` | W0 | pending |
| 21-01-02 | 01 | 1 | ITER-01, ITER-02 | T-21-evidence | Merged candidates are deduped before final rerank | integration | `cd backend && pytest tests/test_retrieval_planner.py tests/test_agent_workflow.py -q` | W0 | pending |
| 21-01-03 | 01 | 1 | ITER-03 | T-21-fallback | Failed iterative mode degrades to normal single-pass cascade | integration | `cd backend && pytest tests/test_agent_workflow.py tests/test_query_api.py -q` | W0 | pending |
| 21-01-04 | 01 | 1 | ITER-04 | T-21-api | API adds trace fields without new SSE event names | endpoint | `cd backend && pytest tests/test_query_api.py tests/test_debug_retrieval.py -q` | W0 | pending |
| 21-01-05 | 01 | 1 | ITER-01, ITER-02, ITER-03, ITER-04 | T-21-scope | Phase 22 hierarchy/drill-down remains absent | regression | `cd backend && pytest -q` plus `rg "parent_id|chunk_level|section_path|child relationship|drill_down|hierarchical" backend/app backend/tests` | W0 | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verify commands.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all required references through existing pytest infrastructure.
- [x] No watch-mode flags.
- [x] Feedback latency target is under 60 seconds for focused tests.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** pending
