# Phase 4 Baseline Review — Integration & Demo Hardening

Read-only baseline regression review of the frontend integration layer.

## Scope

PLAN: `.planning/phases/04-integration-and-demo-hardening/04-01-PLAN.md`

Re-validate that:

- Vite `/api` proxy still targets the local backend.
- `finrag.ts` mappers still cover Phase 3 SSE event names.
- `streamQuery` SSE parser still handles split frames and full event set.
- No UI redesign sneaked in during later phases.

## Files Audited

- `frontend/vite.config.ts`
- `frontend/src/api/finrag.ts`
- `frontend/src/types.ts`
- `frontend/package.json`

## Verification Run

- `npm run lint` (= `tsc --noEmit`) → **clean, 0 errors**.
- `npm run build` → **success**, single bundle 674 kB (gzip 207 kB). Build-size warning is a Vite warning, not an error.
- Visual diff of `finrag.ts` against PLAN: all 8 SSE event handlers present (`onQueryRewrite`, `onIntentDetected`, `onRetrievalComplete`, `onRerankComplete`, `onAnswerChunk`, `onDone`, `onError`, `onPing`).
- `DOC_TYPE_MAP` confirmed: `financial_report → 财报`, `research_report → 研报`, `news → 新闻`.

## Findings

### Blocker

None.

### Important

None.

### Nice-to-have

- **[Nice-to-have] Bundle size warning**
  - `dist/assets/index-*.js` 674 kB pre-gzip. Vite hints at code-splitting (`react-markdown`, `motion`, `@google/genai` are heavy). Cosmetic for demo, worth a once-over after Phase 16 if you add more pages.

- **[Nice-to-have] `vite.config.ts` still defines `process.env.GEMINI_API_KEY`**
  - File: `frontend/vite.config.ts:10-12`. Not used by FinRAG flow (we proxy `/api` to backend). Likely leftover from the AI Studio scaffold. Removing it would reduce confusion when reading config.

- **[Nice-to-have] `mapRetrievalResults` hardcodes `isHigh: item.score >= 0.85`**
  - File: `frontend/src/api/finrag.ts:172`. The threshold makes sense for normalized rerank/relevance scores, but RRF-fused scores in `fused_top20` are typically `0.01–0.05` (small reciprocal-rank sums). So `isHigh` will almost never trigger for fused results. Cosmetic UI flag, not a correctness bug.

- **[Nice-to-have] `mapRerankResults` uses `String(item.citation_id)` for `Document.id`**
  - This is intentional per PLAN to align with `DoneEvent.citations` keys, just worth noting that Phase 16 must keep citation IDs string-stable when table evidence is added.

## Phase 15/16 Risk Notes

- `BackendRerankResultItem` does not yet carry `chunk_type` or table-specific fields. When Phase 16 surfaces table citations, the frontend mapper here needs to be extended (additive — no breaking change expected).
- `Document.contentSnippet` and `formatSource()` will need a table-aware variant if you want the retrieval sidebar to render tables distinctly. Out of scope for v1.0 baseline.

## Recommended Follow-up

1. No code changes recommended for v1.0 baseline.
2. Drop the unused `GEMINI_API_KEY` define from `vite.config.ts` whenever you next touch frontend config. **(Nice-to-have, optional.)**
3. Re-visit the bundle-size warning post Phase 16.
