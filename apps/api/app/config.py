from __future__ import annotations

import os
from dataclasses import dataclass, field


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
    cors_origins: list[str] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", _parse_origins(os.getenv("CORS_ORIGINS")))


settings = Settings()
