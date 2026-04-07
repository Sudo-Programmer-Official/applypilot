from __future__ import annotations

from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field


class PortfolioBootstrapRequest(BaseModel):
    username: str | None = None
    parsed_resume_id: int | None = Field(default=None, ge=1)


class PortfolioProfileUpdateRequest(BaseModel):
    profile_id: int | None = Field(default=None, ge=1)
    username: str = Field(min_length=2, max_length=40)
    display_name: str = Field(min_length=1, max_length=120)
    headline: str = Field(default="", max_length=180)
    summary: str = Field(default="", max_length=2000)
    location: str = Field(default="", max_length=120)
    primary_role: str = Field(default="", max_length=120)
    contact_email: str = Field(default="", max_length=180)
    hiring_status: Literal["open", "selective", "closed"] = "open"
    hero_statement: str = Field(default="", max_length=240)


class ActivityProofInput(BaseModel):
    claim: str = Field(default="", max_length=240)
    evidence: str = Field(default="", max_length=1000)
    metric_label: str = Field(default="", max_length=120)
    metric_before: str = Field(default="", max_length=120)
    metric_after: str = Field(default="", max_length=120)
    links: List[str] = Field(default_factory=list)


class PortfolioActivityCreateRequest(BaseModel):
    profile_id: int | None = Field(default=None, ge=1)
    project_id: int | None = Field(default=None, ge=1)
    event_type: str = Field(default="manual_log", max_length=60)
    title: str = Field(min_length=3, max_length=140)
    detail: str = Field(default="", max_length=1000)
    impact: str = Field(default="", max_length=240)
    happened_on: date | None = None
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    proof: ActivityProofInput | None = None


class PortfolioMetricsResponse(BaseModel):
    impact_score: int = 0
    project_count: int = 0
    activity_count: int = 0
    proof_count: int = 0
    recent_activity_count: int = 0
    tech_diversity: int = 0
    resume_versions: int = 0


class PortfolioProjectResponse(BaseModel):
    id: int
    slug: str
    title: str
    summary: str = ""
    impact_statement: str = ""
    source: str
    tech_stack: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)
    proof_points: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    featured: bool = False
    sort_order: int = 0


class PortfolioActivityResponse(BaseModel):
    id: int
    project_id: int | None = None
    event_type: str
    title: str
    detail: str = ""
    impact: str = ""
    source: str
    happened_on: str | None = None
    tags: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    visibility: str = "public"
    proof: dict = Field(default_factory=dict)
    created_at: str | None = None


class PortfolioProofCardResponse(BaseModel):
    id: int
    project_id: int | None = None
    project_title: str | None = None
    title: str
    claim: str
    evidence: str = ""
    metric_label: str = ""
    metric_before: str = ""
    metric_after: str = ""
    source: str
    links: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: str | None = None


class PortfolioProfileResponse(BaseModel):
    id: int
    username: str
    display_name: str
    headline: str = ""
    summary: str = ""
    location: str = ""
    primary_role: str = ""
    contact_email: str = ""
    hiring_status: str = "open"
    hero_statement: str = ""
    resume_snapshot: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    email: str = ""
    photo_url: str = ""
    created_at: str | None = None
    updated_at: str | None = None


class PortfolioOverviewResponse(BaseModel):
    profile: PortfolioProfileResponse
    metrics: PortfolioMetricsResponse
    projects: List[PortfolioProjectResponse] = Field(default_factory=list)
    activity: List[PortfolioActivityResponse] = Field(default_factory=list)
    proof_cards: List[PortfolioProofCardResponse] = Field(default_factory=list)


class PublicPortfolioProfileResponse(BaseModel):
    display_name: str
    headline: str = ""
    summary: str = ""
    location: str = ""
    primary_role: str = ""
    hero_statement: str = ""


class PublicPortfolioOverviewResponse(BaseModel):
    profile: PublicPortfolioProfileResponse
    metrics: PortfolioMetricsResponse
    projects: List[PortfolioProjectResponse] = Field(default_factory=list)
    activity: List[PortfolioActivityResponse] = Field(default_factory=list)
    proof_cards: List[PortfolioProofCardResponse] = Field(default_factory=list)
