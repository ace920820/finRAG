from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from html import escape

from app.core.ingestion.fixture_loader import chunk_counts_by_doc_id, load_documents
from app.core.ingestion.normalizer import document_list_item_from_document
from app.models.schemas import DocumentListResponse

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    documents = load_documents()
    counts = chunk_counts_by_doc_id()
    items = [document_list_item_from_document(document, counts.get(document.doc_id, 0)) for document in documents]
    return DocumentListResponse(total=len(items), documents=items)


@router.get("/documents/{doc_id}/view", response_class=HTMLResponse)
def view_document(doc_id: str) -> HTMLResponse:
    document = next((item for item in load_documents() if item.doc_id == doc_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    title = escape(document.title)
    meta = escape(f"{document.company} · {document.date} · {document.source}")
    content = escape(document.content or "暂无正文内容")
    html = f"""
    <!doctype html>
    <html lang="zh-CN">
      <head>
        <meta charset="utf-8" />
        <title>{title}</title>
        <style>
          body {{ margin: 0; background: #f8fafc; color: #1e293b; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
          main {{ max-width: 980px; margin: 0 auto; padding: 32px 24px; }}
          h1 {{ font-size: 24px; line-height: 1.35; margin: 0 0 8px; }}
          .meta {{ color: #64748b; font-size: 13px; margin-bottom: 24px; }}
          pre {{ white-space: pre-wrap; word-break: break-word; background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; line-height: 1.7; font-size: 14px; }}
        </style>
      </head>
      <body><main><h1>{title}</h1><div class="meta">{meta}</div><pre>{content}</pre></main></body>
    </html>
    """
    return HTMLResponse(html)
