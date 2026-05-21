from __future__ import annotations

from typing import Optional, Sequence

from app.core.agent.context_builder import EvidencePack
from app.core.agent.prompts import build_generation_prompt
from app.core.providers.text import build_text_provider
from app.models.events import IntentDetectedEvent
from app.models.schemas import RerankResultItem


class AnswerGenerator:
    def __init__(self, text_provider=None):
        self.text_provider = text_provider or build_text_provider()

    def generate(self, query: str, intent: IntentDetectedEvent, evidence: Sequence[RerankResultItem], evidence_pack: Optional[EvidencePack] = None) -> str:
        prompt = build_generation_prompt(query, intent, evidence, evidence_pack=evidence_pack)
        generation_evidence = evidence_pack.items if evidence_pack is not None else evidence
        try:
            answer = self.text_provider.generate_text(prompt, query=query, intent=intent.intent, evidence=generation_evidence)
        except TypeError:
            answer = self.text_provider.generate_text(prompt)
        except Exception:
            answer = ""
        if not answer.strip():
            return build_mock_answer(query, intent, generation_evidence)
        return answer.strip()


def build_mock_answer(query: str, intent: IntentDetectedEvent, evidence: Sequence[RerankResultItem]) -> str:
    if not evidence:
        return "资料中未提及。"
    first = evidence[0]
    citation = _citation(first.citation_id)
    if intent.intent == "factual":
        return (
            f"### 结论\n\n"
            f"根据资料，{first.content}{citation}\n\n"
            f"### 依据\n\n- 来源：{first.title}，公司：{first.company}。{citation}"
        )
    if intent.intent == "reasoning":
        bullets = "\n".join(
            f"- {item.content}{_citation(item.citation_id)}" for item in evidence[:3]
        )
        return f"### 推理分析\n\n围绕“{query}”，资料显示：\n\n{bullets}\n\n### 边界\n\n未覆盖的信息按“资料中未提及”处理。"
    bullets = "\n".join(
        f"- {item.content}{_citation(item.citation_id)}" for item in evidence[:3]
    )
    return f"### 分析摘要\n\n{bullets}\n\n### 风险提示\n\n以上结论仅基于当前检索资料。"


def _citation(citation_id: int) -> str:
    return f'<span class="cite" data-id="{citation_id}">[{citation_id}]</span>'
