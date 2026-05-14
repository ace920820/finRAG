---
status: resolved_pending_user_browser_verify
trigger: "Investigate issue: frontend-markdown-citation-nowrap — specific query renders Markdown/citation HTML literally and overflows horizontally"
created: 2026-05-14T00:00:00+08:00
updated: 2026-05-14T00:35:00+08:00
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: fixed by unwrapping whole-answer markdown fences before ReactMarkdown rendering and adding defensive wrapping styles
test: frontend lint/build plus focused normalization check
expecting: no type/build errors; exact fenced answer shape becomes normal Markdown before render
next_action: user browser verification for original query

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: Assistant answer should render Markdown normally, wrap lines within the chat area, and show clickable citations linked to the right-side evidence panel.
actual: For this query, visible literal citation HTML appears in text, Markdown is not correctly rendered, and long lines overflow horizontally.
errors: No explicit runtime error provided. Screenshot shows literal `<span class="cite" data-id="2">2</span>` and horizontal scrollbar.
reproduction: In frontend, click/type the example question `结合台积电先进制程与英伟达数据中心需求，AI 算力链条对两家公司业绩可能产生什么影响？`; issue reproduces 100%.
started: A previous frontend-only fix normalized some citation formats but this query still reproduces the issue.

## Eliminated
<!-- APPEND only - prevents re-investigating -->

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-05-14T00:05:00+08:00
  checked: codebase search for citation/markdown/wrapping terms
  found: citation normalization appears in frontend/src/components/ChatArea.tsx; backend emits raw HTML citation spans in app/core/agent/generator.py and app/core/providers/text.py; CSS contains overflow/white-space rules.
  implication: bug likely crosses backend raw span output and frontend Markdown/HTML rendering assumptions.
- timestamp: 2026-05-14T00:12:00+08:00
  checked: frontend/src/components/ChatArea.tsx renderer and frontend/src/App.tsx stream assembly
  found: ChatArea passes renderCitationMarkup(msg) into ReactMarkdown with rehypeRaw; renderCitationMarkup only replaces raw <span class="cite" data-id="n"> forms and bracket/sup forms when citations exist. During answer_chunk streaming citations are unavailable until done. The markdown container has break-words but not explicit overflow-wrap:anywhere or min-w-0 on ancestor flex item.
  implication: escaped HTML entity spans are not converted into badges, and flex min-width/wrapping can still allow horizontal overflow for long unbroken text.
- timestamp: 2026-05-14T00:18:00+08:00
  checked: backend reproduction for exact query through analyze_query/retrieval/rerank/AnswerGenerator
  found: generated answer is wrapped as a whole-document fenced code block starting with ```markdown and ending with ```. Inside a Markdown fence, ReactMarkdown treats headings/lists/raw citation spans as literal code and browsers preserve long lines, creating horizontal scroll.
  implication: root cause is not citation click handling itself; it is missing normalization for provider responses that incorrectly wrap Markdown output in a code fence. A frontend unwrapping guard is the minimal robust fix.

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: Provider-generated answer for this query is wrapped in a full-document ```markdown fenced code block. ReactMarkdown correctly renders fenced content as a code block, making Markdown syntax and citation span HTML appear literal and allowing long code lines to overflow horizontally.
fix: Added frontend normalization to unwrap whole-answer ```markdown/```md fences before escaped citation normalization and ReactMarkdown rendering; added defensive wrapping styles for markdown/code blocks.
verification: `npm run lint` passed; `npm run build` passed; focused Node check confirms the exact fenced Markdown shape is unwrapped before rendering.
files_changed: [frontend/src/components/ChatArea.tsx, frontend/src/index.css]
