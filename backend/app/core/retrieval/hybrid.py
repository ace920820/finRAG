from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from app.core.config import get_settings
from app.core.providers.embeddings import build_embedding_provider
from app.core.retrieval.bm25_store import BM25Result, BM25Store
from app.core.retrieval.index_store import RetrievalIndexStore
from app.core.retrieval.table_facts import is_table_fact_period_compatible, is_table_metric_query, query_table_facts
from app.core.retrieval.vector_store import VectorResult, VectorStore
from app.models.schemas import RetrievalResultItem


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HybridRetrievalResult:
    bm25_results: List[RetrievalResultItem]
    vector_results: List[RetrievalResultItem]
    fused_top20: List[RetrievalResultItem]
    bm25_error: Optional[str] = None
    vector_error: Optional[str] = None


class HybridRetriever:
    def __init__(self, bm25_store: BM25Store, vector_store: VectorStore, rrf_k: int = 60):
        self.bm25_store = bm25_store
        self.vector_store = vector_store
        self.rrf_k = rrf_k
        self.settings = get_settings()

    @classmethod
    def from_chunks(cls, chunks, embedding_provider=None) -> "HybridRetriever":
        bm25_store = BM25Store.from_chunks(chunks)
        vector_store = VectorStore.from_chunks(chunks, embedding_provider or build_embedding_provider())
        return cls(bm25_store=bm25_store, vector_store=vector_store, rrf_k=get_settings().rrf_k)

    @classmethod
    def load_default(cls) -> "HybridRetriever":
        index_store = RetrievalIndexStore.load_or_build()
        return cls(index_store.bm25_store, index_store.vector_store, rrf_k=get_settings().rrf_k)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> HybridRetrievalResult:
        limit = top_k or self.settings.retrieval_top_k
        bm25_hits: List[BM25Result] = []
        vector_hits: List[VectorResult] = []
        bm25_error: Optional[str] = None
        vector_error: Optional[str] = None
        try:
            bm25_hits = self.bm25_store.search(query, top_k=limit)
        except Exception as exc:
            bm25_error = str(exc)
            logger.exception("bm25 search failed")
        try:
            vector_hits = self.vector_store.search(query, top_k=limit)
        except Exception as exc:
            vector_error = str(exc)
            logger.exception("vector search failed")
        try:
            supplemental_hits = self._supplemental_hits(query, top_k=limit)
            supplemental_hits.extend(self._table_fact_hits(query, top_k=limit))
        except Exception:
            logger.exception("supplemental hits failed")
            supplemental_hits = []
        fused_hits = self._rrf_fuse(query, bm25_hits, vector_hits, supplemental_hits, top_k=limit)
        return HybridRetrievalResult(
            bm25_results=[self._to_result(hit, rank + 1) for rank, hit in enumerate(bm25_hits)],
            vector_results=[self._to_result(hit, rank + 1) for rank, hit in enumerate(vector_hits)],
            fused_top20=[self._to_result(hit, rank + 1) for rank, hit in enumerate(fused_hits)],
            bm25_error=bm25_error,
            vector_error=vector_error,
        )

    def _rrf_fuse(
        self,
        query: str,
        bm25_hits: Sequence[BM25Result],
        vector_hits: Sequence[VectorResult],
        supplemental_hits: Sequence[BM25Result],
        top_k: int,
    ) -> List[dict]:
        scores: Dict[str, float] = {}
        payloads: Dict[str, dict] = {}
        for rank, hit in enumerate(bm25_hits, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank)
            payloads[hit.chunk_id] = self._hit_to_payload(hit)
        for rank, hit in enumerate(vector_hits, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank)
            payloads[hit.chunk_id] = self._hit_to_payload(hit)
        for rank, hit in enumerate(supplemental_hits, start=1):
            if getattr(hit, "metadata", {}).get("chunk_type") == "table_fact" and not is_table_fact_period_compatible(query, getattr(hit, "metadata", {})):
                continue
            if getattr(hit, "metadata", {}).get("chunk_type") == "table_fact" and "strict_period_match" in getattr(hit, "metadata", {}).get("fact_reasons", []):
                supplemental_score = 0.55 + min(0.35, float(getattr(hit, "score", 0.0)) * 0.03) + 1.0 / (self.rrf_k + rank)
            else:
                supplemental_score = 0.08 + min(0.25, float(getattr(hit, "score", 0.0)) * 0.03) + 1.0 / (self.rrf_k + rank)
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + supplemental_score
            payloads[hit.chunk_id] = self._hit_to_payload(hit)
        boosts = self._entity_boost_terms(query)
        topical_terms = self._topical_boost_terms(query)
        if boosts:
            for chunk_id, payload in payloads.items():
                haystack = " ".join(
                    str(payload.get(field, "")) for field in ("title", "company", "preview", "content")
                ).lower()
                if any(term in haystack for term in boosts):
                    scores[chunk_id] = scores.get(chunk_id, 0.0) + 0.03
                matched_topics = sum(1 for term in topical_terms if term in haystack)
                if matched_topics:
                    scores[chunk_id] = scores.get(chunk_id, 0.0) + min(0.08, matched_topics * 0.02)
        ranked_ids = sorted(scores.keys(), key=lambda chunk_id: scores[chunk_id], reverse=True)[:top_k]
        fused: List[dict] = []
        for chunk_id in ranked_ids:
            payload = dict(payloads[chunk_id])
            payload["score"] = round(scores[chunk_id], 6)
            fused.append(payload)
        return fused

    def _supplemental_hits(self, query: str, top_k: int) -> List[BM25Result]:
        entity_terms = self._entity_boost_terms(query)
        topical_terms = self._topical_boost_terms(query)
        if not entity_terms or not topical_terms:
            return []
        scored: List[tuple[float, BM25Result]] = []
        for chunk in self.bm25_store.chunks:
            hit = BM25Store._to_result(chunk, 0.0)
            haystack = " ".join([hit.title, hit.company, hit.preview, hit.content]).lower()
            if not any(term in haystack for term in entity_terms):
                continue
            topic_matches = sum(1 for term in topical_terms if term in haystack)
            if not topic_matches:
                continue
            score = float(topic_matches)
            if "fy2026q3" in hit.title.lower() or "2025-11" in hit.date:
                score += 2.0
            elif "fy2026q2" in hit.title.lower() or "2025-08" in hit.date:
                score += 1.0
            if any(marker in query.lower() for marker in ("第三季度", "三季度", "q3")) and "fy2026q3" in hit.title.lower():
                score += 2.0
            if any(marker in query.lower() for marker in ("总营收", "营收", "收入", "revenue")) and "condensed consolidated statements of income" in haystack and "three months ended" in haystack and "revenue" in haystack:
                score += 4.0
            if self._is_revenue_table_hit(query, hit, haystack):
                score += 6.0
            scored.append((score, hit))
        ranked = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
        results: List[BM25Result] = []
        for score, hit in ranked:
            results.append(
                BM25Result(
                    chunk_id=hit.chunk_id,
                    score=score,
                    title=hit.title,
                    doc_type=hit.doc_type,
                    company=hit.company,
                    date=hit.date,
                    page=hit.page,
                    preview=hit.preview,
                    content=hit.content,
                    metadata=hit.metadata,
                )
            )
        return results

    def _table_fact_hits(self, query: str, top_k: int) -> List[BM25Result]:
        if not is_table_metric_query(query):
            return []
        results: List[BM25Result] = []
        for match in query_table_facts(query, top_k=top_k):
            fact = match.fact
            metadata = {
                **fact,
                "chunk_type": "table_fact",
                "fact_score": match.score,
                "fact_reasons": match.reasons,
                "source": fact.get("source_pdf_name", ""),
                "section": f"table:{fact.get('table_id', '')}",
            }
            raw_value = str(fact.get("raw_value") or fact.get("value") or "")
            unit = str(fact.get("unit") or "").strip()
            currency = str(fact.get("currency") or "").strip()
            metric_label = str(fact.get("metric_label") or fact.get("metric") or "metric")
            period_label = str(fact.get("period_label") or "").strip()
            content = " | ".join(
                part
                for part in (
                    f"Table fact: {metric_label} = {raw_value}",
                    f"period: {period_label}" if period_label else "",
                    f"unit: {unit}" if unit else "",
                    f"currency: {currency}" if currency else "",
                    f"table: {fact.get('table_id', '')}",
                    f"source: {fact.get('source_pdf_name', '')}",
                )
                if part
            )
            results.append(
                BM25Result(
                    chunk_id=str(fact.get("fact_id") or f"fact-{fact.get('table_id', '')}"),
                    score=match.score,
                    title=str(fact.get("source_pdf_name") or fact.get("table_id") or "table fact"),
                    doc_type=str(fact.get("doc_type") or "financial_report"),
                    company=str(fact.get("company") or ""),
                    date=_date_from_source(str(fact.get("source_pdf_name") or "")),
                    page=fact.get("page_num") if isinstance(fact.get("page_num"), int) else None,
                    preview=content[:120],
                    content=content,
                    metadata=metadata,
                )
            )
        return results


    @staticmethod
    def _is_revenue_table_hit(query: str, hit: BM25Result, haystack: str) -> bool:
        query_lower = query.lower()
        if not any(marker in query_lower for marker in ("总营收", "营收", "收入", "revenue")):
            return False
        if hit.metadata.get("chunk_type") != "table":
            return False
        return "|" in hit.content and "revenue" in haystack

    @staticmethod
    def _entity_boost_terms(query: str) -> List[str]:
        lowered = query.lower()
        terms: List[str] = []
        if any(marker in lowered for marker in ("英伟达", "nvidia", "nvda")):
            terms.extend(["nvidia", "nvda", "英伟达"])
        if any(marker in lowered for marker in ("宁德时代", "catl", "300750")):
            terms.extend(["宁德时代", "catl", "300750"])
        if any(marker in lowered for marker in ("贵州茅台", "茅台", "600519")):
            terms.extend(["贵州茅台", "茅台", "600519"])
        return terms

    @staticmethod
    def _topical_boost_terms(query: str) -> List[str]:
        lowered = query.lower()
        terms: List[str] = []
        if any(marker in lowered for marker in ("收入", "营收", "revenue")):
            terms.extend(["收入", "营收", "revenue", "net revenue", "total revenue"])
        if "data center" in lowered or "数据中心" in lowered:
            terms.extend(["data center", "数据中心"])
        return terms

    @staticmethod
    def _hit_to_payload(hit) -> dict:
        if isinstance(hit, dict):
            payload = dict(hit)
        else:
            payload = {
                "chunk_id": hit.chunk_id,
                "title": hit.title,
                "doc_type": hit.doc_type,
                "company": hit.company,
                "date": hit.date,
                "page": hit.page,
                "preview": hit.preview,
                "content": hit.content,
                "metadata": hit.metadata,
            }
        payload.setdefault("score", getattr(hit, "score", 0.0))
        return payload

    @staticmethod
    def _to_result(hit, rank: int) -> RetrievalResultItem:
        payload = HybridRetriever._hit_to_payload(hit)
        return RetrievalResultItem(
            chunk_id=payload["chunk_id"],
            title=payload["title"],
            doc_type=payload["doc_type"],
            company=payload["company"],
            date=payload["date"],
            page=payload["page"],
            preview=payload["preview"],
            score=float(payload.get("score", getattr(hit, "score", 0.0))),
            content=payload.get("content", payload["preview"]),
            metadata=dict(payload.get("metadata", {})),
        )


def _date_from_source(source_name: str) -> str:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", source_name)
    return match.group(1) if match else "unknown"
