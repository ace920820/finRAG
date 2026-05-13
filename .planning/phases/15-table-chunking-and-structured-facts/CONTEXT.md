# Phase 15 Context — Table Chunking And Structured Facts

Source requirement: `docs/table处理.txt`.

Goal: import table artifacts as first-class table chunks and normalize core financial statement rows into a local facts store.

Key constraints:
- Preserve backward compatibility for existing text chunks and APIs.
- Prioritize financial statement tables and common metrics: revenue, gross profit, operating income, net income, EPS.
- The facts store can be JSON/SQLite-style local storage; production database is not required.
