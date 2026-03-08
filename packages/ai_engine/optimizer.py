"""Deterministic resume optimizer with structured humanization."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from packages.ai_engine.humanizer import humanize_experience_bullets
from packages.job_intelligence.extractor import analyze_job_description, extract_resume_skills_from_document, keyword_names
from packages.resume_formatter import build_resume_document, resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument

_CATEGORY_HINTS = {
    "language": "Languages",
    "framework": "Frameworks",
    "tool": "Cloud & Infrastructure",
    "cloud": "Cloud & Infrastructure",
    "methodology": "Cloud & Infrastructure",
    "architecture": "Backend & Distributed Systems",
    "database": "Databases",
    "data": "Data Engineering",
    "ml": "AI & Machine Learning",
}

_SUMMARY_FOCUS = {
    "backend engineer": "scalable backend systems, cloud infrastructure, and service reliability",
    "data engineer": "data pipelines, distributed processing, and production reliability",
    "ml engineer": "applied machine learning systems, evaluation rigor, and production delivery",
    "frontend engineer": "product-facing interfaces, performance, and cross-functional delivery",
    "devops engineer": "platform reliability, cloud infrastructure, and deployment automation",
}

_BACKEND_SKILL_ORDER = [
    "Languages",
    "Backend & Distributed Systems",
    "Databases",
    "Cloud & Infrastructure",
    "Systems Engineering",
    "Core CS",
    "Frameworks",
    "AI & Machine Learning",
    "Data Engineering",
    "Technical Skills",
]

_GENERIC_SKILL_ORDER = [
    "Languages",
    "Frameworks",
    "Backend & Distributed Systems",
    "Databases",
    "Cloud & Infrastructure",
    "Systems Engineering",
    "Core CS",
    "Data Engineering",
    "AI & Machine Learning",
    "Technical Skills",
]

_SUMMARY_GENERIC_PATTERNS = (
    "experienced in scalable",
    "service reliability",
    "measurable impact",
    "production reliability",
)


def optimize_resume(
    resume_text: str,
    job_description: str,
    resume_document: ResumeDocument | Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Optimize a structured resume while preserving role and bullet structure."""
    job_intelligence = analyze_job_description(job_description or "", limit=10)
    role_info = job_intelligence.get("role_type", {"id": "general_software", "label": "Software Engineer"})
    job_skills = job_intelligence.get("skills", [])
    job_skill_names = keyword_names(job_skills)

    if isinstance(resume_document, ResumeDocument):
        document = resume_document.model_copy(deep=True)
    elif isinstance(resume_document, dict) and resume_document:
        document = ResumeDocument.model_validate(resume_document)
    else:
        document = build_resume_document(resume_text or "", role_label=role_info.get("label"))

    if not document.name and not document.experience and not document.projects:
        return _seed_resume(job_skills, role_info)

    existing_skills = {skill.lower() for skill in keyword_names(extract_resume_skills_from_document(document.model_dump()))}
    missing_skills = [skill for skill in job_skills if skill["name"].lower() not in existing_skills]

    optimized = document.model_copy(deep=True)
    _rewrite_title(optimized, role_info)
    summary_action = _rewrite_summary(optimized, role_info, job_skill_names)
    added_skills = _add_missing_skills(optimized, missing_skills[:2])
    _reorder_skill_sections(optimized, role_info)
    bullet_changes = humanize_experience_bullets(optimized)
    project_changes = _rewrite_projects(optimized)

    optimized_text = resume_document_to_text(optimized)
    suggestions = _build_suggestions(added_skills, bullet_changes, project_changes, role_info, summary_action)

    return {
        "optimized_text": optimized_text,
        "optimized_document": optimized.model_dump(),
        "job_description": job_description,
        "suggestions": suggestions,
        "highlighted_keywords": [skill["name"] for skill in missing_skills[:3]],
    }


def _seed_resume(job_skills: List[Dict[str, Any]], role_info: Dict[str, str]) -> Dict[str, Any]:
    focus = ", ".join(keyword_names(job_skills)[:3]) or "target role requirements"
    role_label = role_info.get("label") or "Software Engineer"
    optimized_text = "\n".join(
        [
            "Candidate",
            role_label,
            "",
            f"{role_label} focused on {focus} with measurable product impact.",
            "",
            "Experience",
            "- Delivered backend systems aligned to the target role.",
        ]
    )
    return {
        "optimized_text": optimized_text,
        "optimized_document": build_resume_document(optimized_text, role_label=role_label).model_dump(),
        "job_description": "",
        "suggestions": [
            "Created a role-aligned summary.",
            "Added a starter experience bullet so the resume is not blank.",
        ],
        "highlighted_keywords": keyword_names(job_skills)[:3],
    }


def _rewrite_title(document: ResumeDocument, role_info: Dict[str, str]) -> None:
    role_label = (role_info.get("label") or "").strip()
    if not role_label:
        return
    current = document.title.strip()
    if not current:
        document.title = role_label
        return
    if role_label.lower() in current.lower():
        return
    primary = current.split("|", 1)[0].strip()
    if len(primary.split()) <= 6:
        document.title = f"{primary} | {role_label}"


def _rewrite_summary(document: ResumeDocument, role_info: Dict[str, str], job_skill_names: List[str]) -> str:
    original_summary = _clean_text(document.summary or "")
    role_label = (role_info.get("label") or document.title or "Software Engineer").split("|", 1)[0].strip()
    generated_summary = _build_summary(role_label, job_skill_names)

    if original_summary and _summary_score(original_summary) >= _summary_score(generated_summary):
        document.summary = _finalize_summary(original_summary)
        return "preserved"

    document.summary = generated_summary
    return "rewritten" if original_summary else "created"


def _add_missing_skills(document: ResumeDocument, missing_skills: List[Dict[str, Any]]) -> List[str]:
    added: List[str] = []
    for skill in missing_skills:
        name = skill["name"]
        if any(name == existing for values in document.skills.values() for existing in values):
            continue
        category = _pick_skill_category(document, skill.get("category", "architecture"))
        document.skills.setdefault(category, [])
        document.skills[category].append(name)
        document.skills[category] = _dedupe(document.skills[category])[:10]
        added.append(name)
    return added


def _pick_skill_category(document: ResumeDocument, category: str) -> str:
    preferred = _CATEGORY_HINTS.get(category, "Technical Skills")
    preferred_lower = preferred.lower()
    for existing in document.skills:
        lowered = existing.lower()
        if preferred_lower in lowered:
            return existing
        if category == "language" and "language" in lowered:
            return existing
        if category in {"cloud", "tool", "methodology"} and ("cloud" in lowered or "infra" in lowered):
            return existing
        if category == "database" and "database" in lowered:
            return existing
        if category == "architecture" and ("backend" in lowered or "system" in lowered):
            return existing
    return preferred


def _reorder_skill_sections(document: ResumeDocument, role_info: Dict[str, str]) -> None:
    if not document.skills:
        return

    role_lower = (role_info.get("label") or "").lower()
    preferred_order = _BACKEND_SKILL_ORDER if any(
        token in role_lower for token in ("backend", "distributed", "platform", "devops")
    ) else _GENERIC_SKILL_ORDER

    indexed_items = list(enumerate(document.skills.items()))
    indexed_items.sort(key=lambda item: (_skill_order_index(item[1][0], preferred_order), item[0]))
    document.skills = {category: values for _, (category, values) in indexed_items}


def _rewrite_projects(document: ResumeDocument) -> int:
    changes = 0
    for entry in document.projects:
        cleaned_details = _clean_text(entry.details)
        if cleaned_details != entry.details:
            entry.details = cleaned_details
            changes += 1
        cleaned_bullets = []
        for bullet in entry.bullets[:3]:
            updated = _clean_terminal(bullet)
            cleaned_bullets.append(updated)
            if updated != bullet:
                changes += 1
        entry.bullets = cleaned_bullets
    return changes


def _build_suggestions(
    added_skills: List[str],
    bullet_changes: int,
    project_changes: int,
    role_info: Dict[str, str],
    summary_action: str,
) -> List[str]:
    if summary_action == "preserved":
        suggestions = ["Kept the original summary because it was already stronger than the generated rewrite."]
    elif summary_action == "created":
        suggestions = [f"Created a role-aligned summary for {role_info.get('label', 'the target role')}."]
    else:
        suggestions = [f"Aligned the summary to {role_info.get('label', 'the target role')} language."]
    if added_skills:
        suggestions.append(f"Added missing role keywords to skills: {', '.join(added_skills[:2])}.")
    if bullet_changes:
        suggestions.append(f"Humanized {bullet_changes} experience bullet{'s' if bullet_changes != 1 else ''} with cleaner technical phrasing.")
    if project_changes:
        suggestions.append("Cleaned project descriptions to preserve readability in the final PDF.")
    return suggestions[:4]


def _build_summary(role_label: str, job_skill_names: List[str]) -> str:
    focus = _SUMMARY_FOCUS.get(role_label.lower(), "scalable systems, measurable impact, and production reliability")
    lead_skills = ", ".join(job_skill_names[:3])
    if lead_skills:
        return f"{role_label} building {focus} across {lead_skills}."
    return f"{role_label} building {focus}."


def _summary_score(summary: str) -> int:
    lowered = summary.lower()
    metrics = len(re.findall(r"\b\d+(?:\.\d+)?\s?(?:%|m\+|k\+|records?|workers?|hours?)\b", lowered))
    technical_signals = len(re.findall(
        r"\b(?:distributed|fault-tolerant|scalable|concurrency|cloud|backend|lambda|rds|microservices|systems?)\b",
        lowered,
    ))
    generic_hits = sum(1 for pattern in _SUMMARY_GENERIC_PATTERNS if pattern in lowered)
    sentence_length_bonus = 1 if 10 <= len(summary.split()) <= 24 else 0
    return metrics * 3 + technical_signals + sentence_length_bonus - generic_hits


def _finalize_summary(summary: str) -> str:
    cleaned = _clean_text(summary).rstrip(".")
    return f"{cleaned}."


def _skill_order_index(category: str, preferred_order: List[str]) -> Tuple[int, str]:
    normalized = category.lower()
    for index, preferred in enumerate(preferred_order):
        preferred_lower = preferred.lower()
        if normalized == preferred_lower:
            return index, normalized
        if preferred_lower in normalized or normalized in preferred_lower:
            return index, normalized
    return len(preferred_order), normalized


def _clean_terminal(text: str) -> str:
    cleaned = _clean_text(text).rstrip(".")
    return f"{cleaned}."


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered
