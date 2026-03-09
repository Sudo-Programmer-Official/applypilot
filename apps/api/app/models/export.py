from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ResumeDownloadRequest(BaseModel):
    resume_text: str
    document: dict | None = None
    file_name: str | None = None
    role_label: str | None = None
    use_optimized: bool = True
    layout_density: Literal["compact", "balanced", "spacious"] = "balanced"
