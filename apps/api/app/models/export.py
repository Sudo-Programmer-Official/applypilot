from __future__ import annotations

from pydantic import BaseModel


class ResumeDownloadRequest(BaseModel):
    resume_text: str
    file_name: str | None = None
    role_label: str | None = None
    use_optimized: bool = True
