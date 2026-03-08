"""Deterministic resume optimizer with planner, verifier, and scoring loop."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from packages.ai_engine.humanizer import _phrase_signature, humanize_bullet
from packages.ai_engine.planner import build_optimization_plan
from packages.ai_engine.rules import (
    build_summary,
    clean_terminal,
    clean_text,
    dedupe,
    finalize_summary,
    pick_skill_category,
    preferred_skill_order,
    skill_order_index,
)
from packages.ai_engine.scorer import score_resume
from packages.ai_engine.verifier import verify_change
from packages.job_intelligence.extractor import analyze_job_description, keyword_names
from packages.resume_formatter import build_resume_document, resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument


def optimize_resume(
    resume_text: str,
    job_description: str,
    resume_document: ResumeDocument | Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Optimize a structured resume while preserving factual resume evidence."""
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

    original_document = document.model_copy(deep=True)
    optimization_plan = build_optimization_plan(original_document, job_description or "", role_info, job_skills)

    optimized = original_document.model_copy(deep=True)
    original_score = score_resume(original_document, job_skills, original_document=original_document, role_info=role_info)
    current_score = deepcopy(original_score)
    kept_changes: List[Dict[str, Any]] = []
    rejected_changes: List[Dict[str, Any]] = []

    for planned_change in optimization_plan["planned_changes"]:
        candidate_document = optimized.model_copy(deep=True)
        applied_change = _apply_planned_change(
            candidate_document,
            optimized,
            original_document,
            planned_change,
            role_info,
            job_skill_names,
        )
        if not applied_change:
            rejected_changes.append(
                {
                    **planned_change,
                    "decision": "rejected",
                    "decision_reason": "No material improvement was available for this target.",
                }
            )
            continue

        verification = verify_change(original_document, optimized, candidate_document, applied_change, job_skills)
        if not verification["passed"]:
            rejected_changes.append(
                {
                    **applied_change,
                    "decision": "rejected",
                    "decision_reason": "; ".join(verification["reasons"]),
                    "verification": verification,
                }
            )
            continue

        candidate_score = score_resume(
            candidate_document,
            job_skills,
            original_document=original_document,
            role_info=role_info,
        )
        if candidate_score["axes"]["credibility"] < current_score["axes"]["credibility"]:
            rejected_changes.append(
                {
                    **applied_change,
                    "decision": "rejected",
                    "decision_reason": "Rejected because the change reduced credibility.",
                    "verification": verification,
                    "scores": {
                        "before": deepcopy(current_score),
                        "after": deepcopy(candidate_score),
                    },
                }
            )
            continue

        if candidate_score["total"] <= current_score["total"]:
            rejected_changes.append(
                {
                    **applied_change,
                    "decision": "rejected",
                    "decision_reason": "Rejected because the change did not improve the overall resume score.",
                    "verification": verification,
                    "scores": {
                        "before": deepcopy(current_score),
                        "after": deepcopy(candidate_score),
                    },
                }
            )
            continue

        optimized = candidate_document
        kept_changes.append(
            {
                **applied_change,
                "decision": "kept",
                "decision_reason": "Kept because the change improved score without reducing credibility.",
                "verification": verification,
                "scores": {
                    "before": deepcopy(current_score),
                    "after": deepcopy(candidate_score),
                },
            }
        )
        current_score = candidate_score

    optimized_text = resume_document_to_text(optimized)
    suggestions = _build_suggestions(kept_changes, rejected_changes, role_info)
    highlighted_keywords = [
        change["value"]
        for change in kept_changes
        if change.get("action") in {"add_skill", "add_derived_skill"}
    ][:3] or optimization_plan.get("highlighted_keywords", [])

    return {
        "optimized_text": optimized_text,
        "optimized_document": optimized.model_dump(),
        "job_description": job_description,
        "suggestions": suggestions,
        "highlighted_keywords": highlighted_keywords,
        "optimization_plan": optimization_plan["planned_changes"],
        "kept_changes": kept_changes,
        "rejected_changes": rejected_changes,
        "scores": {
            "original": original_score,
            "optimized": current_score,
        },
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
    seed_document = build_resume_document(optimized_text, role_label=role_label)
    seed_score = score_resume(seed_document, job_skills, original_document=seed_document, role_info=role_info)
    return {
        "optimized_text": optimized_text,
        "optimized_document": seed_document.model_dump(),
        "job_description": "",
        "suggestions": [
            "Created a role-aligned summary.",
            "Added a starter experience bullet so the resume is not blank.",
        ],
        "highlighted_keywords": keyword_names(job_skills)[:3],
        "optimization_plan": [],
        "kept_changes": [],
        "rejected_changes": [],
        "scores": {
            "original": seed_score,
            "optimized": seed_score,
        },
    }


def _apply_planned_change(
    candidate_document: ResumeDocument,
    current_document: ResumeDocument,
    original_document: ResumeDocument,
    change: Dict[str, Any],
    role_info: Dict[str, str],
    job_skill_names: List[str],
) -> Dict[str, Any] | None:
    action = change["action"]

    if action == "rewrite_title":
        before_value = current_document.title
        after_value = _rewrite_title_value(before_value, change.get("role_label") or role_info.get("label") or "")
        if after_value == before_value:
            return None
        candidate_document.title = after_value
        return {
            **change,
            "before_value": before_value,
            "after_value": after_value,
        }

    if action == "rewrite_summary":
        before_value = clean_text(current_document.summary or "")
        after_value = finalize_summary(
            build_summary(
                change.get("role_label") or role_info.get("label") or "Software Engineer",
                job_skill_names,
                evidence_text=resume_document_to_text(original_document),
            )
        )
        if not after_value or after_value == finalize_summary(before_value):
            return None
        candidate_document.summary = after_value
        return {
            **change,
            "before_value": finalize_summary(before_value) if before_value else "",
            "after_value": after_value,
        }

    if action in {"add_skill", "add_derived_skill"}:
        value = str(change["value"])
        existing = {item.lower() for values in candidate_document.skills.values() for item in values}
        if value.lower() in existing:
            return None
        category = pick_skill_category(
            candidate_document,
            change.get("skill_category", "architecture"),
            fallback=change.get("skill_category_label"),
        )
        candidate_document.skills.setdefault(category, [])
        before_value = list(candidate_document.skills[category])
        candidate_document.skills[category].append(value)
        candidate_document.skills[category] = dedupe(candidate_document.skills[category])[:10]
        after_value = list(candidate_document.skills[category])
        return {
            **change,
            "before_value": before_value,
            "after_value": after_value,
            "allowed_terms": [value],
        }

    if action == "reorder_skill_sections":
        if not candidate_document.skills:
            return None
        preferred = preferred_skill_order(change.get("role_label") or role_info.get("label", ""))
        before_value = list(candidate_document.skills.keys())
        indexed_items = list(enumerate(candidate_document.skills.items()))
        indexed_items.sort(key=lambda item: (skill_order_index(item[1][0], preferred), item[0]))
        reordered = {category: values for _, (category, values) in indexed_items}
        after_value = list(reordered.keys())
        if before_value == after_value:
            return None
        candidate_document.skills = reordered
        return {
            **change,
            "before_value": before_value,
            "after_value": after_value,
        }

    if action == "clean_project_details":
        project_index = int(change["target"]["project_index"])
        before_value = candidate_document.projects[project_index].details
        after_value = clean_text(before_value)
        if not after_value or after_value == before_value:
            return None
        candidate_document.projects[project_index].details = after_value
        return {
            **change,
            "before_value": before_value,
            "after_value": after_value,
        }

    if action == "clean_project_bullet":
        project_index = int(change["target"]["project_index"])
        bullet_index = int(change["target"]["bullet_index"])
        before_value = candidate_document.projects[project_index].bullets[bullet_index]
        after_value = clean_terminal(before_value)
        if after_value == before_value:
            return None
        candidate_document.projects[project_index].bullets[bullet_index] = after_value
        return {
            **change,
            "before_value": before_value,
            "after_value": after_value,
        }

    if action == "rewrite_experience_bullet":
        entry_index = int(change["target"]["entry_index"])
        bullet_index = int(change["target"]["bullet_index"])
        entry = candidate_document.experience[entry_index]
        before_value = entry.bullets[bullet_index]
        role_context = {
            value
            for values in current_document.skills.values()
            for value in values
        }
        sibling_signatures = {
            _phrase_signature(line)
            for index, line in enumerate(entry.bullets[:4])
            if index != bullet_index
        }
        after_value = humanize_bullet(entry, before_value, role_context=role_context, used_signatures=sibling_signatures)
        if clean_text(after_value) == clean_text(before_value):
            return None
        entry.bullets[bullet_index] = after_value
        return {
            **change,
            "before_value": before_value,
            "after_value": after_value,
        }

    return None


def _rewrite_title_value(current: str, role_label: str) -> str:
    role_label = (role_label or "").strip()
    if not role_label:
        return current
    current = current.strip()
    if not current:
        return role_label
    if role_label.lower() in current.lower():
        return current
    primary = current.split("|", 1)[0].strip()
    if len(primary.split()) <= 6:
        return f"{primary} | {role_label}"
    return current


def _build_suggestions(
    kept_changes: List[Dict[str, Any]],
    rejected_changes: List[Dict[str, Any]],
    role_info: Dict[str, str],
) -> List[str]:
    suggestions: List[str] = []

    if any(
        change.get("action") == "rewrite_summary" and "weakened technical or scale signals" in " ".join(
            change.get("verification", {}).get("reasons", [])
        ).lower()
        for change in rejected_changes
    ):
        suggestions.append("Kept the original summary because it carried stronger technical and scale signals.")
    elif any(change.get("action") == "rewrite_summary" for change in kept_changes):
        suggestions.append(f"Aligned the summary to {role_info.get('label', 'the target role')} language without weakening evidence.")

    added_skills = [
        change["value"]
        for change in kept_changes
        if change.get("action") in {"add_skill", "add_derived_skill"}
    ]
    if added_skills:
        suggestions.append(f"Added resume-backed keywords to skills: {', '.join(added_skills[:3])}.")

    bullet_changes = sum(1 for change in kept_changes if change.get("action") == "rewrite_experience_bullet")
    if bullet_changes:
        suggestions.append(
            f"Rewrote {bullet_changes} weaker experience bullet{'s' if bullet_changes != 1 else ''} after verification and scoring."
        )

    project_changes = sum(
        1
        for change in kept_changes
        if change.get("action") in {"clean_project_details", "clean_project_bullet"}
    )
    if project_changes:
        suggestions.append("Cleaned project content to improve PDF-safe readability.")

    if not suggestions:
        suggestions.append("Preserved the original content because no verified change improved the score.")

    return suggestions[:5]
