from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class ResumeEducationItem(BaseModel):
    school: str = ""
    degree: str = ""
    date: str = ""
    details: List[str] = Field(default_factory=list)


class ResumeExperienceItem(BaseModel):
    role: str = ""
    company: str = ""
    date: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: List[str] = Field(default_factory=list)


class ResumeProjectItem(BaseModel):
    name: str = ""
    details: str = ""
    bullets: List[str] = Field(default_factory=list)


class ResumeLayoutBlock(BaseModel):
    text: str = ""
    page: int = 1
    order: int = 0
    x0: float = 0.0
    x1: float = 0.0
    top: float = 0.0
    bottom: float = 0.0
    font_size: float = 0.0
    is_bold: bool = False
    style_name: str = ""
    source: str = ""


class ResumeDocument(BaseModel):
    name: str = ""
    title: str = ""
    contact_items: List[str] = Field(default_factory=list)
    summary: str = ""
    education: List[ResumeEducationItem] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    experience: List[ResumeExperienceItem] = Field(default_factory=list)
    projects: List[ResumeProjectItem] = Field(default_factory=list)
