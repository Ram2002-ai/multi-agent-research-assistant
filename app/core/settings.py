"""Environment-driven application settings.

The project intentionally has useful local defaults. Production deployments can
switch to PostgreSQL, stricter authentication, and a different vector backend
without changing application code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _origins() -> list[str]:
    value = os.getenv("CORS_ORIGINS", "http://localhost:4173,http://127.0.0.1:4173")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ResearchOS")
    environment: str = os.getenv("APP_ENV", "development")
    debug: bool = _bool("DEBUG", False)
    root_dir: Path = ROOT_DIR
    data_dir: Path = field(default_factory=lambda: ROOT_DIR / "data")
    output_dir: Path = field(default_factory=lambda: ROOT_DIR / "outputs")
    log_dir: Path = field(default_factory=lambda: ROOT_DIR / "logs")
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(ROOT_DIR / 'data' / 'research_platform.db').as_posix()}",
    )
    jwt_secret: str = os.getenv(
        "JWT_SECRET", "development-only-change-me-32-bytes"
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))
    auth_required: bool = _bool("AUTH_REQUIRED", False)
    cors_origins: list[str] = field(default_factory=_origins)
    default_model: str = os.getenv(
        "DEFAULT_LLM", "openrouter/meta-llama/llama-3.3-70b-instruct"
    )
    fallback_model: str = os.getenv("FALLBACK_LLM", "")
    max_retries: int = int(os.getenv("RETRY_COUNT", "2"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "300"))
    source_limit: int = int(os.getenv("NUMBER_OF_SOURCES", "10"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    vector_backend: str = os.getenv("VECTOR_DB", "local")

    def prepare_directories(self) -> None:
        for path in (self.data_dir, self.output_dir, self.log_dir):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def validate_production(self) -> None:
        if self.is_production and self.jwt_secret == "development-only-change-me-32-bytes":
            raise RuntimeError("JWT_SECRET must be changed in production")


settings = Settings()
