from __future__ import annotations

from typing import Sequence

from app.models.events import IntentDetectedEvent
from app.models.schemas import RerankResultItem


_SYSTEM_RULES = """你是 FinRAG 金融研究 Agent。只依据给定资料回答。
若资料中没有相关信息，明确写“资料中未提及”，不要编造。
输出 Markdown，并在关键结论后使用给定 citation_id 的引用标记。"""

_NO_EVIDENCE_RULES = """你是 FinRAG 金融研究 Agent。当前本地资料没有检索到可引用证据。
可以基于通用金融知识给出简短回答，但必须明确标注“未基于本地资料，不能作为引用结论”。
不要添加 citation 标记。"""


def build_generation_prompt(query: str, intent: IntentDetectedEvent, evidence: Sequence[RerankResultItem]) -> str:
    evidence_lines = []
    for item in evidence:
        evidence_lines.append(
            f"[{item.citation_id}] {item.title} | {item.company} | {item.date} | "
            f"page={item.page or 'N/A'} | {item.content}"
        )
    evidence_text = "\n".join(evidence_lines) or "无可用资料"
    rules = _SYSTEM_RULES if evidence else _NO_EVIDENCE_RULES
    return (
        f"{rules}\n\n"
        f"问题：{query}\n"
        f"意图：{intent.intent}\n"
        f"结构模板：{intent.template}\n\n"
        f"资料：\n{evidence_text}\n\n"
        "请给出简洁、可展示的中文 Markdown 回答。"
    )
