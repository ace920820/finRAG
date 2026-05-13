from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FINRAG_",
        extra="ignore",
    )

    @property
    def processed_dir(self) -> Path:
        return self.processed_data_dir or self.data_dir / "processed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
