from __future__ import annotations

from typing import Optional

from app.core.agent.context_builder import EvidencePack
from app.models.schemas import RetrievalCascadeStage


def rerank_trace(
    input_count: int,
    output_count: int,
    degraded: bool,
    fallback_reason: Optional[str],
    evidence_pack: Optional[EvidencePack] = None,
) -> list[RetrievalCascadeStage]:
    final_input_count = evidence_pack.original_count if evidence_pack is not None else output_count
    final_output_count = evidence_pack.compressed_count if evidence_pack is not None else output_count
    final_metadata = {}
    if evidence_pack is not None:
        final_metadata = {
            "original_count": evidence_pack.original_count,
            "compressed_count": evidence_pack.compressed_count,
            "dropped_duplicate_count": evidence_pack.dropped_duplicate_count,
        }
    return [
        RetrievalCascadeStage(
            name="rerank",
            method="rerank_service",
            input_count=input_count,
            output_count=output_count,
            kind="filter",
            degraded=degraded,
            fallback_reason=fallback_reason,
        ),
        RetrievalCascadeStage(
            name="final_evidence",
            method="evidence_pack_compression",
            input_count=final_input_count,
            output_count=final_output_count,
            kind="filter",
            degraded=degraded,
            fallback_reason=fallback_reason,
            metadata=final_metadata,
        ),
    ]
