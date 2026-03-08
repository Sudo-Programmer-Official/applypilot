from __future__ import annotations

from typing import List

from pydantic import BaseModel


class JobImportRequest(BaseModel):
    url: str


class JobImportResponse(BaseModel):
    url: str
    source: str
    title: str
    company: str
    location: str = ""
    description: str
    skills: List[str]
