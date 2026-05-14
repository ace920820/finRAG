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
    score_source = "mock"

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


class SiliconRerankProvider:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = (base_url or settings.silicon_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.model_api_key_silicon
        self.model = model or settings.rerank_model
        self.timeout_seconds = settings.provider_timeout_seconds
        self.top_k = settings.rerank_top_k
        if not self.api_key:
            raise ValueError("SiliconFlow rerank provider requires FINRAG_MODEL_API_KEY_SILICON")
        if httpx is None:
            raise RuntimeError("httpx package unavailable for SiliconFlow rerank provider")

    def rerank(self, query: str, documents: Sequence[str]) -> List[ProviderResult]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "query": query, "documents": list(documents), "top_n": self.top_k}
        response = httpx.post(f"{self.base_url}/rerank", json=payload, headers=headers, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        raw_results = data.get("results") or data.get("data") or data.get("output", {}).get("results", [])
        results: List[ProviderResult] = []
        for rank, item in enumerate(raw_results):
            metadata = dict(item)
            metadata.setdefault("index", item.get("index", rank))
            score = item.get("relevance_score", item.get("score", item.get("rerank_score", 0.0)))
            results.append(ProviderResult(score=float(score), metadata=metadata))
        return results


class BailianRerankProvider:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.rerank_base_url
        self.api_key = api_key if api_key is not None else settings.model_api_key
        self.model = model or settings.rerank_model
        self.timeout_seconds = settings.provider_timeout_seconds
        self.top_k = settings.rerank_top_k
        if not self.api_key:
            raise ValueError("Bailian rerank provider requires FINRAG_MODEL_API_KEY")
        if httpx is None:
            raise RuntimeError("httpx package unavailable for Bailian rerank provider")

    def rerank(self, query: str, documents: Sequence[str]) -> List[ProviderResult]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = self._build_payload(query, documents)
        response = httpx.post(self.base_url, json=payload, headers=headers, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        results: List[ProviderResult] = []
        output = data.get("output", data)
        raw_results = output.get("results", output if isinstance(output, list) else data.get("results", []))
        for rank, item in enumerate(raw_results):
            metadata = dict(item)
            metadata.setdefault("index", item.get("index", rank))
            results.append(ProviderResult(score=float(item.get("relevance_score", item.get("score", 0.0))), metadata=metadata))
        return results

    def _build_payload(self, query: str, documents: Sequence[str]) -> dict:
        if "/compatible-api/" in self.base_url or self.base_url.rstrip("/").endswith("/reranks"):
            return {"model": self.model, "query": query, "documents": list(documents), "top_n": self.top_k}
        return {
            "model": self.model,
            "input": {"query": query, "documents": list(documents)},
            "parameters": {"return_documents": False, "top_n": self.top_k},
        }


def build_rerank_provider() -> Union[MockRerankProvider, BailianRerankProvider, SiliconRerankProvider]:
    settings = get_settings()
    if settings.rerank_provider == "silicon":
        return SiliconRerankProvider()
    if settings.rerank_provider == "bailian":
        return BailianRerankProvider()
    return MockRerankProvider()
