"""ATS scoring module based on keyword coverage heuristics."""
from __future__ import annotations

from typing import Any, Dict, List

from packages.job_intelligence.extractor import analyze_job_description, extract_resume_skills, keyword_names


def calculate_ats_score(resume_text: str, job_description: str) -> Dict[str, object]:
    """Compute ATS score using high-signal ranked role skills."""
    job_intelligence = analyze_job_description(job_description or "")
    job_skills = job_intelligence.get("skills", [])
    if not job_skills:
        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "notes": ["No high-signal skills were extracted from the job description."],
        }

    resume_tokens = set(keyword_names(extract_resume_skills(resume_text or "")))
    total_weight = sum(skill["score"] for skill in job_skills)
    matched_skills: List[Dict[str, Any]] = [skill for skill in job_skills if skill["name"] in resume_tokens]
    missing_skills: List[Dict[str, Any]] = [skill for skill in job_skills if skill["name"] not in resume_tokens]
    matched_weight = sum(skill["score"] for skill in matched_skills)
    score = int(round((matched_weight / total_weight) * 100)) if total_weight else 0
    role_label = job_intelligence.get("role_type", {}).get("label", "Software Engineer")

    return {
        "score": score,
        "matched_keywords": keyword_names(matched_skills),
        "missing_keywords": keyword_names(missing_skills),
        "notes": [f"Scored against the top {len(job_skills)} skills for a {role_label} role."],
    }
