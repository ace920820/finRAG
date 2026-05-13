from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, List, Sequence

import jieba
from rank_bm25 import BM25Okapi

from app.models.schemas import Chunk


@dataclass(frozen=True)
class BM25Result:
    chunk_id: str
    score: float
    title: str
    doc_type: str
    company: str
    date: str
    page: Optional[int]
    preview: str
    content: str
    metadata: Dict[str, object]


class BM25Store:
    def __init__(self, chunks: Sequence[Chunk]):
        self.chunks = list(chunks)
        self._tokenized = [self._tokenize(chunk.content) for chunk in self.chunks]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None

    @classmethod
    def from_chunks(cls, chunks: Sequence[Chunk]) -> "BM25Store":
        return cls(chunks)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        tokens = [token.strip() for token in jieba.lcut(text, cut_all=False)]
        return [token for token in tokens if token]

    def search(self, query: str, top_k: int = 20) -> List[BM25Result]:
        if not self.chunks or self._bm25 is None:
            return []
        scores = self._bm25.get_scores(self._tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        results: List[BM25Result] = []
        for index, score in ranked:
            chunk = self.chunks[index]
            results.append(self._to_result(chunk, float(score)))
        return results

    @staticmethod
    def _to_result(chunk: Chunk, score: float) -> BM25Result:
        metadata = dict(chunk.metadata)
        title = str(metadata.get("source", metadata.get("title", chunk.chunk_id)))
        return BM25Result(
            chunk_id=chunk.chunk_id,
            score=score,
            title=title,
            doc_type=str(metadata.get("doc_type", "news")),
            company=str(metadata.get("company", metadata.get("company_name", ""))),
            date=str(metadata.get("date", "")),
            page=chunk.page_num,
            preview=chunk.content[:120],
            content=chunk.content,
            metadata=metadata,
        )
