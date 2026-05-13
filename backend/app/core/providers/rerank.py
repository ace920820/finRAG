from __future__ import annotations

import hashlib
from typing import List, Sequence, Optional, Union

from app.core.config import get_settings
from app.core.providers.base import ProviderResult

try:
    import httpx
except Exception:  # pragma: no cover - httpx is expected to exist
    httpx = None


class MockRerankProvider:
    def rerank(self, query: str, documents: Sequence[str]) -> List[ProviderResult]:
        scored: List[ProviderResult] = []
        query_tokens = set(query.replace(" ", ""))
        for index, document in enumerate(documents):
            token_overlap = len(query_tokens.intersection(set(document)))
            digest = hashlib.sha256((query + "||" + document).encode("utf-8")).digest()
            stable = int.from_bytes(digest[:4], "big") % 1000 / 1000.0
            score = round(0.5 * token_overlap + 0.5 * stable, 6)
            scored.append(ProviderResult(score=score, metadata={"index": index}))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored


class BailianRerankProvider:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.model_base_url
        self.api_key = api_key if api_key is not None else settings.model_api_key
        self.model = model or settings.rerank_model
        if not self.api_key:
            raise ValueError("Bailian rerank provider requires FINRAG_MODEL_API_KEY")
        if httpx is None:
            raise RuntimeError("httpx package unavailable for Bailian rerank provider")

    def rerank(self, query: str, documents: Sequence[str]) -> List[ProviderResult]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "query": query, "documents": list(documents)}
        response = httpx.post(f"{self.base_url.rstrip('/')}/rerank", json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        results: List[ProviderResult] = []
        for item in data.get("output", data.get("results", [])):
            results.append(ProviderResult(score=float(item.get("relevance_score", item.get("score", 0.0))), metadata=item))
        return results


class MockTextProvider:
    def generate_text(self, prompt: str, **kwargs) -> str:
        evidence = kwargs.get("evidence") or []
        intent = kwargs.get("intent", "analytical")
        query = kwargs.get("query", "")
        if not evidence:
            return "资料中未提及。"
        first = evidence[0]
        cite = f'<span class="cite" data-id="{first.citation_id}">[{first.citation_id}]</span>'
        if intent == "factual":
            return f"### 结论\n\n{first.content}{cite}"
        bullets = "\n".join(
            f"- {item.content}<span class=\"cite\" data-id=\"{item.citation_id}\">[{item.citation_id}]</span>"
            for item in evidence[:3]
        )
        return f"### 分析摘要\n\n{bullets}\n\n### 回答范围\n\n以上回答针对：{query}"


class BailianTextProvider:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.model_base_url
        self.api_key = api_key if api_key is not None else settings.model_api_key
        self.model = model or settings.text_model
        if not self.api_key:
            raise ValueError("Bailian text provider requires FINRAG_MODEL_API_KEY")
        if httpx is None:
            raise RuntimeError("httpx package unavailable for Bailian text provider")

    def generate_text(self, prompt: str, **kwargs) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是严谨的金融研究助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        response = httpx.post(f"{self.base_url.rstrip('/')}/chat/completions", json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return data.get("output_text", data.get("text", ""))


def build_rerank_provider() -> Union[MockRerankProvider, BailianRerankProvider]:
    settings = get_settings()
    if settings.rerank_provider == "bailian":
        return BailianRerankProvider()
    return MockRerankProvider()
