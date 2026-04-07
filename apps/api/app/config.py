from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULT_JOB_CACHE_PATH = str(Path(__file__).resolve().parents[1] / "data" / "job_cache.db")


def _parse_origins(raw_value: str | None) -> list[str]:
    if not raw_value:
        return [
            "http://localhost:5173",
            "https://tryapplypilot.com",
            "https://www.tryapplypilot.com",
        ]
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    api_title: str = os.getenv("API_TITLE", "ApplyPilot API")
    environment: str = os.getenv("ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    max_file_bytes: int = int(os.getenv("MAX_FILE_BYTES", str(5 * 1024 * 1024)))
    database_url: str | None = os.getenv("DATABASE_URL") or None
    firebase_project_id: str | None = os.getenv("FIREBASE_PROJECT_ID") or None
    firebase_service_account_path: str | None = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH") or None
    firebase_service_account_json: str | None = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or None
    job_import_timeout_seconds: int = int(os.getenv("JOB_IMPORT_TIMEOUT_SECONDS", "6"))
    job_cache_ttl_hours: int = int(os.getenv("JOB_CACHE_TTL_HOURS", "168"))
    job_cache_path: str = os.getenv("JOB_CACHE_PATH", _DEFAULT_JOB_CACHE_PATH)
    cors_origins: list[str] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", _parse_origins(os.getenv("CORS_ORIGINS")))


settings = Settings()
