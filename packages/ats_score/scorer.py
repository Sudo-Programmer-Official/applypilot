"""ATS scoring module based on keyword coverage heuristics."""
from __future__ import annotations

from typing import Dict, List

from packages.keyword_engine.extractor import extract_keywords


def calculate_ats_score(resume_text: str, job_description: str) -> Dict[str, object]:
    """Compute a simple ATS score using keyword overlap."""
    jd_keywords: List[str] = extract_keywords(job_description or "")
    if not jd_keywords:
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "notes": ["No job description provided; ATS score unavailable."],
        }

    resume_tokens = set(extract_keywords(resume_text or ""))

    matched = sorted([kw for kw in jd_keywords if kw in resume_tokens])
    missing = sorted([kw for kw in jd_keywords if kw not in resume_tokens])

    total = len(jd_keywords)
    score = int(round((len(matched) / total) * 100)) if total else 0

    return {
        "score": score,
        "matched_keywords": matched,  # type: List[str]
        "missing_keywords": missing,  # type: List[str]
        "notes": ["Keyword coverage heuristic; refine with weighting later."],
    }
