from __future__ import annotations

from typing import Optional, Union

from app.core.config import get_settings

try:
    import httpx
except Exception:  # pragma: no cover - httpx is expected to exist
    httpx = None


class MockTextProvider:
    def generate_text(self, prompt: str, **kwargs) -> str:
        evidence = kwargs.get("evidence") or []
        intent = kwargs.get("intent", "analytical")
        query = kwargs.get("query", "")
        if not evidence:
            return f"### 回答\n\n当前本地资料中未检索到可引用证据，无法给出带引用的结论。\n\n### 查询\n\n{query}"
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
        self.timeout_seconds = settings.provider_timeout_seconds
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
        response = httpx.post(f"{self.base_url.rstrip('/')}/chat/completions", json=payload, headers=headers, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return data.get("output_text", data.get("text", ""))


def build_text_provider() -> Union[MockTextProvider, BailianTextProvider]:
    settings = get_settings()
    if settings.text_provider == "bailian":
        return BailianTextProvider()
    return MockTextProvider()
