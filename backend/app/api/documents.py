from fastapi import APIRouter

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
