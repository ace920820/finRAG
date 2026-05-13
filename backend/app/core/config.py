from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal["mock", "bailian"]


class Settings(BaseSettings):
    app_name: str = "FinRAG API"
    environment: str = "local"
    demo_mode: bool = True
    data_dir: Path = Field(default=Path(__file__).resolve().parents[1] / "data")
    processed_data_dir: Optional[Path] = None
    index_dir: Path = Field(default=Path(__file__).resolve().parents[1] / "data" / "index")

    model_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    rerank_base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
    model_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-v4"
    rerank_model: str = "qwen3-rerank"
    text_model: str = "qwen-plus"
    embedding_provider: ProviderName = "mock"
    rerank_provider: ProviderName = "mock"
    text_provider: ProviderName = "mock"

    embedding_api_key: Optional[str] = None
    rerank_api_key: Optional[str] = None
    llm_api_key: Optional[str] = None

    retrieval_top_k: int = 20
    rerank_top_k: int = 5
    rrf_k: int = 60
    provider_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FINRAG_",
        extra="ignore",
    )

    @field_validator("model_api_key", "embedding_api_key", "rerank_api_key", "llm_api_key", mode="before")
    @classmethod
    def blank_secret_to_none(cls, value):
        if value == "":
            return None
        return value

    @property
    def processed_dir(self) -> Path:
        path = self.processed_data_dir or self.data_dir / "processed"
        return self._resolve_path(path)

    @property
    def resolved_index_dir(self) -> Path:
        return self._resolve_path(self.index_dir)

    @staticmethod
    def _resolve_path(path: Path) -> Path:
        if path.is_absolute():
            return path
        backend_root = Path(__file__).resolve().parents[2]
        if path.parts and path.parts[0] == backend_root.name:
            return backend_root.parent / path
        return backend_root / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
