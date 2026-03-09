from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResumeEditTarget(BaseModel):
    section: Literal["experience"]
    entry_index: int = Field(ge=0)
    bullet_index: int = Field(ge=0)


class ResumeEditRequest(BaseModel):
    original_document: dict
    current_document: dict
    instruction: str = Field(min_length=1)
    target: ResumeEditTarget
    job_description: str | None = None
    parsed_resume_id: int | None = Field(default=None, ge=1)
    parent_version_id: int | None = Field(default=None, ge=1)
