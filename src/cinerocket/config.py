from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: SecretStr | None = None
    openrouter_models: list[str] = Field(
        default_factory=lambda: [
            "nvidia/nemotron-3.5-lightning:free",
            "google/gemma-4-26b-a4b-it:free",
            "z-ai/glm-5.2:free",
            "openrouter/free",
        ]
    )
    google_api_key: SecretStr | None = None
    gemini_model: str = "gemini-flash-latest"

    database_path: Path = Path("data/cinerocket.db")
    app_db_path: Path = Path("data/app.db")
    index_dir: Path = Path("data/index")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_cache_dir: Path = Path("data/models")
    embedding_batch_size: int = 256
    semantic_search_limit: int = Field(default=30, ge=1, le=100)
    excluded_tables: Annotated[frozenset[str], NoDecode] = frozenset({"alembic_version"})

    max_rows: int = Field(default=200, ge=1)
    preview_rows: int = Field(default=20, ge=1)
    query_timeout_seconds: float = Field(default=45.0, gt=0)
    max_question_length: int = Field(default=1000, ge=10)

    agent_request_limit: int = Field(default=8, ge=1)
    agent_retries: int = Field(default=3, ge=0)
    history_max_turns: int = Field(default=6, ge=1)
    cache_ttl_seconds: int = Field(default=86_400, ge=0)

    api_url: str = "http://localhost:8000"
    log_level: str = "INFO"

    @field_validator("excluded_tables", mode="before")
    @classmethod
    def _split_tables(cls, value: object) -> object:
        if isinstance(value, str):
            return frozenset(name.strip() for name in value.split(",") if name.strip())
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
