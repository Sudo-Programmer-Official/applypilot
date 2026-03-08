"""Application readiness scoring for job-fit diagnostics."""
from __future__ import annotations

from typing import Any, Dict, List

from packages.job_intelligence.extractor import (
    analyze_job_description,
    extract_resume_skills,
    get_role_template_skills,
    keyword_names,
)

_SECTION_MARKERS = ("experience", "projects", "skills", "technical skills", "summary")
_ACTION_VERBS = (
    "built",
    "designed",
    "improved",
    "implemented",
    "led",
    "developed",
    "owned",
    "optimized",
    "delivered",
    "created",
    "launched",
    "scaled",
)


def _lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _score_skill_match(resume_skill_names: set[str], role_skills: List[str]) -> int:
    if not role_skills:
        return 0
    matched = len([skill for skill in role_skills if skill in resume_skill_names])
    return int(round((matched / len(role_skills)) * 100))


def _score_keyword_coverage(resume_skill_names: set[str], jd_skills: List[Dict[str, Any]]) -> int:
    if not jd_skills:
        return 0
    total_weight = sum(skill["score"] for skill in jd_skills)
    matched_weight = sum(skill["score"] for skill in jd_skills if skill["name"] in resume_skill_names)
    return int(round((matched_weight / total_weight) * 100)) if total_weight else 0


def _score_experience_strength(resume_lines: List[str]) -> int:
    if not resume_lines:
        return 0
    section_hits = sum(1 for line in resume_lines if any(marker in line.lower() for marker in _SECTION_MARKERS))
    action_hits = sum(1 for line in resume_lines if line.split() and line.split()[0].lower().strip("-") in _ACTION_VERBS)
    bullet_like = sum(1 for line in resume_lines if line.startswith("-") or line.startswith("*"))
    score = 25
    score += min(section_hits, 3) * 15
    score += min(action_hits, 5) * 8
    score += min(bullet_like, 5) * 4
    return min(score, 100)


def _score_impact_metrics(resume_lines: List[str]) -> int:
    if not resume_lines:
        return 0
    impact_lines = sum(1 for line in resume_lines if any(char.isdigit() for char in line))
    action_lines = max(sum(1 for line in resume_lines if len(line.split()) >= 4), 1)
    return min(int(round((impact_lines / action_lines) * 100)), 100)


def _top_issues(skill_match: int, experience_strength: int, impact_metrics: int, keyword_coverage: int, missing_skills: List[str]) -> List[str]:
    issues: List[str] = []
    if missing_skills:
        issues.append(f"Add missing core skills: {', '.join(missing_skills[:3])}.")
    if impact_metrics < 70:
        issues.append("Add measurable metrics to more experience bullets.")
    if experience_strength < 70:
        issues.append("Strengthen the experience section with clearer action-first bullets.")
    if keyword_coverage < 70:
        issues.append("Mirror the job description language more closely in the summary and skills sections.")
    if skill_match < 70:
        issues.append("Align the resume with the core role template before applying.")
    return issues[:4]


def calculate_application_readiness(resume_text: str, job_description: str) -> Dict[str, Any]:
    jd_report = analyze_job_description(job_description or "")
    role_type = jd_report.get("role_type", {"id": "general_software", "label": "Software Engineer"})
    jd_skills = jd_report.get("skills", [])
    resume_skills = extract_resume_skills(resume_text or "")
    resume_skill_names = set(keyword_names(resume_skills))
    jd_skill_names = keyword_names(jd_skills)
    role_template_skills = [
        skill for skill in get_role_template_skills(role_type.get("id", "general_software")) if skill in jd_skill_names
    ][:8]

    skill_match = _score_skill_match(resume_skill_names, role_template_skills or keyword_names(jd_skills))
    keyword_coverage = _score_keyword_coverage(resume_skill_names, jd_skills)
    resume_lines = _lines(resume_text or "")
    experience_strength = _score_experience_strength(resume_lines)
    impact_metrics = _score_impact_metrics(resume_lines)
    readiness = int(round(
        skill_match * 0.35
        + experience_strength * 0.25
        + impact_metrics * 0.20
        + keyword_coverage * 0.20
    ))
    missing_skill_names = [skill["name"] for skill in jd_skills if skill["name"] not in resume_skill_names]

    return {
        "score": readiness,
        "role_type": role_type,
        "breakdown": {
            "skill_match": skill_match,
            "experience_strength": experience_strength,
            "impact_metrics": impact_metrics,
            "keyword_coverage": keyword_coverage,
        },
        "top_issues": _top_issues(
            skill_match,
            experience_strength,
            impact_metrics,
            keyword_coverage,
            missing_skill_names,
        ),
    }
