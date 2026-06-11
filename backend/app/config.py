"""
Application configuration using pydantic-settings.
All values are loaded from environment variables (.env file).
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field

import os

print("CWD =", os.getcwd())
print("HF ENV =", os.getenv("HUGGINGFACE_API_KEY"))

class Settings(BaseSettings):
    # ── HuggingFace ──────────────────────────────────────────
    huggingface_api_key: str = Field("", alias="HUGGINGFACE_API_KEY")

    # ── LangSmith ────────────────────────────────────────────
    langchain_tracing_v2: str = Field("true", alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field("", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field("crm-intelligence", alias="LANGCHAIN_PROJECT")
    langchain_endpoint: str = Field(
        "https://api.smith.langchain.com", alias="LANGCHAIN_ENDPOINT"
    )

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(
        "sqlite:///./crm_intelligence.db", alias="DATABASE_URL"
    )

    # ── ChromaDB ─────────────────────────────────────────────
    chroma_persist_dir: str = Field("./chroma_db", alias="CHROMA_PERSIST_DIR")

    # ── LLM settings ─────────────────────────────────────────
    hf_llm_model: str = Field(
        "mistralai/Mistral-7B-Instruct-v0.3", alias="HF_LLM_MODEL"
    )
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )

    # ── App settings ──────────────────────────────────────────
    app_env: str = Field("development", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    max_agent_tool_calls: int = Field(6, alias="MAX_AGENT_TOOL_CALLS")
    rag_top_k: int = Field(3, alias="RAG_TOP_K")
    rag_min_score: float = Field(0.3, alias="RAG_MIN_SCORE")
    confidence_human_threshold: float = Field(0.70, alias="CONFIDENCE_HUMAN_THRESHOLD")
    sentiment_deterioration_count: int = Field(3, alias="SENTIMENT_DETERIORATION_COUNT")
    web_intel_cache_hours: int = Field(6, alias="WEB_INTEL_CACHE_HOURS")
    email_replay_speed: float = Field(1.0, alias="EMAIL_REPLAY_SPEED")

    # ── CORS ──────────────────────────────────────────────────
    allowed_origins: str = Field(
        "http://localhost:3000,http://127.0.0.1:3000", alias="ALLOWED_ORIGINS"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        populate_by_name = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    print("HF_LLM_MODEL from settings =", s.hf_llm_model)
    return s


def configure_langsmith(settings: Settings) -> None:
    """Set LangSmith env vars so LangChain picks them up automatically."""
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = settings.huggingface_api_key
