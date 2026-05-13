from __future__ import annotations

from typing import Sequence

from app.models.events import IntentDetectedEvent
from app.models.schemas import RerankResultItem


_SYSTEM_RULES = """你是 FinRAG 金融研究 Agent。只依据给定资料回答。
若资料中没有相关信息，明确写“资料中未提及”，不要编造。
输出 Markdown，并在关键结论后使用给定 citation_id 的引用标记。"""


def build_generation_prompt(query: str, intent: IntentDetectedEvent, evidence: Sequence[RerankResultItem]) -> str:
    evidence_lines = []
    for item in evidence:
        evidence_lines.append(
            f"[{item.citation_id}] {item.title} | {item.company} | {item.date} | "
            f"page={item.page or 'N/A'} | {item.content}"
        )
    evidence_text = "\n".join(evidence_lines) or "无可用资料"
    return (
        f"{_SYSTEM_RULES}\n\n"
        f"问题：{query}\n"
        f"意图：{intent.intent}\n"
        f"结构模板：{intent.template}\n\n"
        f"资料：\n{evidence_text}\n\n"
        "请给出简洁、可展示的中文 Markdown 回答。"
    )
