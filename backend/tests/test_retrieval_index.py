import subprocess
from pathlib import Path

from app.core.ingestion.fixture_loader import load_chunks
from app.core.providers.embeddings import MockEmbeddingProvider
from app.core.retrieval.bm25_store import BM25Store
from app.core.retrieval.vector_store import VectorStore


def test_bm25_and_vector_retrieval_return_hits():
    chunks = load_chunks()
    bm25 = BM25Store.from_chunks(chunks)
    vector = VectorStore.from_chunks(chunks, MockEmbeddingProvider())

    bm25_results = bm25.search('宁德时代 经营风险', top_k=5)
    vector_results = vector.search('贵州茅台 营业收入', top_k=5, embedding_provider=MockEmbeddingProvider())

    assert bm25_results
    assert vector_results
    assert any(result.chunk_id for result in bm25_results)
    assert any(result.chunk_id for result in vector_results)


def test_build_index_script_creates_artifacts():
    backend_dir = Path(__file__).resolve().parents[1]
    subprocess.run(['python3', 'scripts/build_index.py'], cwd=backend_dir, check=True)
    index_dir = backend_dir / 'app' / 'data' / 'index'
    assert (index_dir / 'bm25_index.json').exists()
    assert (index_dir / 'vector_index.json').exists()
