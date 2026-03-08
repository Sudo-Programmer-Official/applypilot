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
    bullets: List[str] = Field(default_factory=list)


class ResumeProjectItem(BaseModel):
    name: str = ""
    details: str = ""
    bullets: List[str] = Field(default_factory=list)


class ResumeDocument(BaseModel):
    name: str = ""
    title: str = ""
    contact_items: List[str] = Field(default_factory=list)
    summary: str = ""
    education: List[ResumeEducationItem] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    experience: List[ResumeExperienceItem] = Field(default_factory=list)
    projects: List[ResumeProjectItem] = Field(default_factory=list)
