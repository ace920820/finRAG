# Phase 16 Context — Table-Aware Retrieval And QA Integration

Source requirement: `docs/table处理.txt`.

Goal: route financial numeric queries to table evidence/facts and expose table citation metadata to the chat/debug interfaces.

Key constraints:
- Existing text RAG and KB management flows must not regress.
- Financial table answers should cite source document/page/table metadata.
- Frontend changes should be minimal and limited to consuming table citation metadata if needed.
