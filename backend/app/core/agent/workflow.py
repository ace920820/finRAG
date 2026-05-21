from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from app.core.agent.context_builder import build_evidence_pack
from app.core.agent.generator import AnswerGenerator
from app.core.agent.query_analysis import analyze_query
from app.core.agent.retrieval_planner import plan_iterative_retrieval, should_use_iterative_retrieval
from app.core.retrieval.hybrid import HybridRetriever
from app.core.retrieval.rerank_service import RerankService
from app.core.retrieval.trace import rerank_trace
from app.models.events import DoneEvent, IntentDetectedEvent, QueryRewriteEvent, RerankCompleteEvent, RetrievalCompleteEvent
from app.models.schemas import (
    CitationMetadata,
    IterativeRetrievalStep,
    IterativeRetrievalTrace,
    QueryRequest,
    RetrievalCascadeStage,
    RetrievalResultItem,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryWorkflowResult:
    query_rewrite: QueryRewriteEvent
    intent_detected: IntentDetectedEvent
    retrieval_complete: RetrievalCompleteEvent
    rerank_complete: RerankCompleteEvent
    answer_text: str
    done: DoneEvent
    degraded: bool = False
    fallback_reason: Optional[str] = None


@dataclass(frozen=True)
class RetrievalPipelineResult:
    retrieval_complete: RetrievalCompleteEvent
    rerank_complete: RerankCompleteEvent
    evidence: list
    evidence_pack: object | None
    degraded: bool = False
    fallback_reason: Optional[str] = None


class QueryWorkflow:
    def __init__(self, retriever=None, rerank_service=None, generator=None):
        self.retriever = retriever or HybridRetriever.load_default()
        self.rerank_service = rerank_service or RerankService()
        self.generator = generator or AnswerGenerator()

    def run(self, request: QueryRequest) -> QueryWorkflowResult:
        started_at = time.perf_counter()
        logger.info("query workflow started")
        rewrite, intent = analyze_query(request.query)
        logger.info("query analysis complete intent=%s", intent.intent)
        retrieval = RetrievalCompleteEvent()
        rerank = RerankCompleteEvent()
        degraded = False
        fallback_reason = None
        evidence = []
        evidence_pack = None
        try:
            logger.info("retrieval started")
            pipeline = run_retrieval_pipeline(
                request.query,
                rewrite,
                retriever=self.retriever,
                rerank_service=self.rerank_service,
            )
            retrieval = pipeline.retrieval_complete
            rerank = pipeline.rerank_complete
            evidence = pipeline.evidence
            evidence_pack = pipeline.evidence_pack
            degraded = pipeline.degraded
            fallback_reason = pipeline.fallback_reason
        except Exception as exc:
            logger.exception("query retrieval/rerank failed")
            degraded = True
            fallback_reason = str(exc)
            rerank = RerankCompleteEvent(degraded=True, fallback_reason=fallback_reason, score_source="hybrid_fusion")
        logger.info("generation started evidence=%d", len(evidence))
        answer = self.generator.generate(request.query, intent, evidence, evidence_pack=evidence_pack)
        logger.info("generation complete chars=%d", len(answer))
        citations = build_citations(evidence)
        done = DoneEvent(
            latency_ms=max(1, int((time.perf_counter() - started_at) * 1000)),
            total_tokens=estimate_tokens(answer),
            citations=citations,
        )
        return QueryWorkflowResult(
            query_rewrite=rewrite,
            intent_detected=intent,
            retrieval_complete=retrieval,
            rerank_complete=rerank,
            answer_text=answer,
            done=done,
            degraded=degraded,
            fallback_reason=fallback_reason,
        )


def run_retrieval_pipeline(query: str, rewrite: QueryRewriteEvent, retriever, rerank_service) -> RetrievalPipelineResult:
    retrieval_result, iterative_trace, candidates = _retrieve_candidates(query, rewrite, retriever)
    logger.info(
        "retrieval complete bm25=%d vector=%d fused=%d candidates=%d",
        len(retrieval_result.bm25_results),
        len(retrieval_result.vector_results),
        len(retrieval_result.fused_top20),
        len(candidates),
    )
    retrieval = RetrievalCompleteEvent(
        bm25_results=retrieval_result.bm25_results,
        vector_results=retrieval_result.vector_results,
        fused_top20=retrieval_result.fused_top20,
        bm25_error=getattr(retrieval_result, "bm25_error", None),
        vector_error=getattr(retrieval_result, "vector_error", None),
        cascade_trace=list(getattr(retrieval_result, "cascade_trace", []) or []),
        iterative_trace=iterative_trace,
    )
    logger.info("rerank started candidates=%d", len(candidates))
    rerank_result = rerank_service.rerank(query, candidates)
    logger.info("rerank complete top=%d degraded=%s", len(rerank_result.top5), rerank_result.degraded)
    evidence_pack = build_evidence_pack(rerank_result.top5)
    rerank = RerankCompleteEvent(
        top5=rerank_result.top5,
        degraded=rerank_result.degraded,
        fallback_reason=rerank_result.fallback_reason,
        score_source=rerank_result.score_source,
        cascade_trace=rerank_trace(
            len(candidates),
            len(rerank_result.top5),
            rerank_result.degraded,
            rerank_result.fallback_reason,
            evidence_pack=evidence_pack,
        ),
    )
    degraded = rerank_result.degraded or bool(iterative_trace and iterative_trace.degraded)
    fallback_reason = rerank_result.fallback_reason or (iterative_trace.fallback_reason if iterative_trace and iterative_trace.degraded else None)
    return RetrievalPipelineResult(
        retrieval_complete=retrieval,
        rerank_complete=rerank,
        evidence=evidence_pack.items,
        evidence_pack=evidence_pack,
        degraded=degraded,
        fallback_reason=fallback_reason,
    )


def _retrieve_candidates(query: str, rewrite: QueryRewriteEvent, retriever):
    single_pass = _retrieve_single(retriever, retrieval_query(rewrite), rewrite.plan)
    if not should_use_iterative_retrieval(rewrite.plan):
        return single_pass, None, single_pass.fused_top20
    try:
        iterative_trace = plan_iterative_retrieval(query, rewrite.plan)
    except Exception:
        iterative_trace = IterativeRetrievalTrace(enabled=True, degraded=True, fallback_reason="iterative_planning_failed")
        return single_pass, iterative_trace, single_pass.fused_top20
    if not iterative_trace.steps:
        iterative_trace.degraded = True
        iterative_trace.fallback_reason = "iterative_planning_failed"
        return single_pass, iterative_trace, single_pass.fused_top20
    try:
        step_candidates: list[RetrievalResultItem] = []
        executed_steps: list[IterativeRetrievalStep] = []
        # 同步记录每一步实际产出的 fused_top20 长度。selected_evidence_ids 是给 UI
        # 展示的样本（截断到前 5），不能用来反映真实的合并基数；下方 per_step_metadata
        # 必须用这个真实数，否则 "step 各 5 → 合并 22" 会出现明显矛盾。
        step_raw_counts: list[int] = []
        for step in iterative_trace.steps:
            step_result = _retrieve_single(retriever, step.retrieval_query, rewrite.plan)
            evidence = _selected_evidence(step_result.fused_top20)
            executed_steps.append(
                step.model_copy(
                    update={
                        "route": getattr(step_result, "route", None),
                        "applied_filters": dict(getattr(step_result, "applied_filters", {}) or {}),
                        "selected_evidence_ids": [item.chunk_id for item in step_result.fused_top20[:5]],
                        "selected_evidence": evidence,
                        "cascade_trace": list(getattr(step_result, "cascade_trace", []) or []),
                    }
                )
            )
            step_candidates.extend(step_result.fused_top20)
            step_raw_counts.append(len(step_result.fused_top20))
        candidates = _dedupe_candidates(step_candidates)
        if not candidates:
            iterative_trace = iterative_trace.model_copy(
                update={"degraded": True, "fallback_reason": "iterative_no_evidence", "steps": executed_steps}
            )
            return single_pass, iterative_trace, single_pass.fused_top20
        iterative_trace = iterative_trace.model_copy(update={"steps": executed_steps})
        # 在 single_pass 的 cascade_trace 末尾追加 iterative_merge 阶段，
        # 让前端能看到 single_pass.fused_top20 → iterative_dedupe 的数字流转
        per_step_metadata = [
            {
                "index": step.index,
                "purpose": step.purpose,
                "candidates": raw_count,
                "evidence_sample_size": len(step.selected_evidence_ids),
            }
            for step, raw_count in zip(executed_steps, step_raw_counts)
        ]
        single_pass.cascade_trace.append(
            RetrievalCascadeStage(
                name="iterative_merge",
                method=f"{len(executed_steps)}_steps_dedupe",
                kind="augment",
                input_count=len(single_pass.fused_top20),
                output_count=len(candidates),
                metadata={
                    "per_step": per_step_metadata,
                    "deduped_total": len(candidates),
                    "raw_step_total": sum(int(s["candidates"]) for s in per_step_metadata),
                },
            )
        )
        return single_pass, iterative_trace, candidates
    except Exception:
        iterative_trace = iterative_trace.model_copy(update={"degraded": True, "fallback_reason": "iterative_step_failed"})
        return single_pass, iterative_trace, single_pass.fused_top20


def _retrieve_single(retriever, query: str, plan):
    try:
        return retriever.retrieve(query, plan=plan)
    except TypeError:
        return retriever.retrieve(query)


def _selected_evidence(items: list[RetrievalResultItem]) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for item in items[:3]:
        evidence.append(
            {
                "chunk_id": item.chunk_id,
                "title": item.title,
                "company": item.company,
                "doc_type": item.doc_type,
                "score": item.score,
                "preview": item.preview[:160],
            }
        )
    return evidence


def _dedupe_candidates(items: list[RetrievalResultItem]) -> list[RetrievalResultItem]:
    seen: set[tuple[object, ...]] = set()
    deduped: list[RetrievalResultItem] = []
    for item in items:
        key = _candidate_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _candidate_key(item: RetrievalResultItem) -> tuple[object, ...]:
    if item.chunk_id:
        return ("chunk", item.chunk_id)
    metadata = item.metadata or {}
    if metadata.get("chunk_type") == "table_fact":
        return (
            "table_fact",
            metadata.get("source_pdf_name") or metadata.get("source") or item.title,
            metadata.get("table_id"),
            metadata.get("metric"),
            metadata.get("period_label"),
            metadata.get("raw_value"),
        )
    return ("text", item.title, item.page, (item.content or item.preview)[:160])


def retrieval_query(rewrite: QueryRewriteEvent) -> str:
    parts = [rewrite.original] + rewrite.expanded[:8] + rewrite.sub_queries[:2]
    return " ".join(part for part in parts if part)


def build_citations(items) -> Dict[str, CitationMetadata]:
    citations: Dict[str, CitationMetadata] = {}
    for item in items:
        citations[str(item.citation_id)] = CitationMetadata(
            chunk_id=item.chunk_id,
            title=item.title,
            doc_type=item.doc_type,
            company=item.company,
            date=item.date,
            page=item.page,
            source=str(item.metadata.get("source") or item.metadata.get("source_pdf_name") or item.title),
            section=str(item.metadata.get("section") or item.metadata.get("table_id") or "") or None,
            metadata=dict(item.metadata),
        )
    return citations


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)
