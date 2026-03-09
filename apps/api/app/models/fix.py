from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ResumeFixRequest(BaseModel):
    original_document: dict
    current_document: dict
    job_description: str = Field(min_length=1)
    analysis: Dict[str, Any] | None = None
    missing_signals: List[str] = Field(default_factory=list)
    parsed_resume_id: int | None = Field(default=None, ge=1)
    parent_version_id: int | None = Field(default=None, ge=1)
