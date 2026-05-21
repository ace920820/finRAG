from __future__ import annotations

from typing import Optional

from app.models.schemas import RetrievalCascadeStage


def rerank_trace(input_count: int, output_count: int, degraded: bool, fallback_reason: Optional[str]) -> list[RetrievalCascadeStage]:
    return [
        RetrievalCascadeStage(
            name="rerank",
            method="rerank_service",
            input_count=input_count,
            output_count=output_count,
            degraded=degraded,
            fallback_reason=fallback_reason,
        ),
        RetrievalCascadeStage(
            name="final_evidence",
            method="top_evidence_selection",
            input_count=output_count,
            output_count=output_count,
            degraded=degraded,
            fallback_reason=fallback_reason,
        ),
    ]
