from __future__ import annotations

from typing import Optional, Sequence

from app.core.agent.context_builder import EvidencePack
from app.models.events import IntentDetectedEvent
from app.models.schemas import RerankResultItem


_SYSTEM_RULES = """你是 FinRAG 金融研究 Agent。只依据给定资料回答。
若资料中没有相关信息，明确写“资料中未提及”，不要编造。
表格事实冲突时，优先使用明确匹配问题期间、原表指标名含单位、且来自年度主要会计数据/合并报表的证据；保留原表单位，换算时必须同时给出原始数值。
输出 Markdown，并在关键结论后使用给定 citation_id 的引用标记。"""

_NO_EVIDENCE_RULES = """你是 FinRAG 金融研究 Agent。当前本地资料没有检索到可引用证据。
可以基于通用金融知识给出简短回答，但必须明确标注“未基于本地资料，不能作为引用结论”。
不要添加 citation 标记。"""


def build_generation_prompt(query: str, intent: IntentDetectedEvent, evidence: Sequence[RerankResultItem], evidence_pack: Optional[EvidencePack] = None) -> str:
    evidence_lines = []
    prompt_items = evidence_pack.items if evidence_pack is not None else evidence
    for item in prompt_items:
        table_bits = []
        if item.metadata:
            for key in ("chunk_type", "table_id", "metric", "period_label", "raw_value", "unit", "currency"):
                if item.metadata.get(key) not in (None, ""):
                    table_bits.append(f"{key}={item.metadata.get(key)}")
        metadata_text = " | " + " | ".join(table_bits) if table_bits else ""
        content = getattr(item, "compact_content", None) or item.content
        evidence_lines.append(
            f"[{item.citation_id}] {item.title} | {item.company} | {item.date} | "
            f"page={item.page or 'N/A'}{metadata_text} | {content}"
        )
    evidence_text = "\n".join(evidence_lines) or "无可用资料"
    rules = _SYSTEM_RULES if prompt_items else _NO_EVIDENCE_RULES
    return (
        f"{rules}\n\n"
        f"问题：{query}\n"
        f"意图：{intent.intent}\n"
        f"结构模板：{intent.template}\n\n"
        f"资料：\n{evidence_text}\n\n"
        "请给出简洁、可展示的中文 Markdown 回答。"
    )
