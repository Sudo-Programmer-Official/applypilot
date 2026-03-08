"""Backward-compatible wrapper around the job intelligence extractor."""
from __future__ import annotations

from typing import Iterable, List, Dict, Any

from packages.job_intelligence.extractor import (
    analyze_job_description,
    extract_resume_skills,
    get_role_template_skills,
    keyword_names,
)


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    del min_length
    return keyword_names(analyze_job_description(text).get("skills", []))


def keyword_names_from_items(items: Iterable[Dict[str, Any]]) -> List[str]:
    return keyword_names(items)


__all__ = [
    "analyze_job_description",
    "extract_keywords",
    "extract_resume_skills",
    "get_role_template_skills",
    "keyword_names",
    "keyword_names_from_items",
]
