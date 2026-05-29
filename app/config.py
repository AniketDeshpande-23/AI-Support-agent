"""
app/config.py — Settings and LLM/embeddings factory.

Supports two providers, selected via LLM_PROVIDER env var:
  - "ollama"  (default) — local Ollama server
  - "openai"            — OpenAI API
"""

import logging
import sys
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Provider toggle
    LLM_PROVIDER: Literal["ollama", "openai"] = "ollama"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

    # App
    DB_PATH: str = "support_logs.db"
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT: str = "10/minute"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# ── LLM / Embeddings factories ────────────────────────────────────────────────

def get_llm():
    """Return the configured LLM instance (lazy, not cached here — cache in agent.py)."""
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        logger.info(f"LLM provider: OpenAI | model: {settings.OPENAI_MODEL}")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY,
        )

    from langchain_ollama import OllamaLLM
    logger.info(f"LLM provider: Ollama | model: {settings.OLLAMA_MODEL}")
    return OllamaLLM(
        model=settings.OLLAMA_MODEL,
        temperature=0.2,
        base_url=settings.OLLAMA_BASE_URL,
        num_predict=400,
    )


def get_embeddings():
    """Return the configured embeddings instance."""
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        logger.info(f"Embeddings provider: OpenAI | model: {settings.OPENAI_EMBED_MODEL}")
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBED_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    from langchain_ollama import OllamaEmbeddings
    logger.info(f"Embeddings provider: Ollama | model: {settings.OLLAMA_EMBED_MODEL}")
    return OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )
