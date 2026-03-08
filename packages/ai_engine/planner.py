"""Structured planning stage for deterministic resume optimization."""
from __future__ import annotations

from typing import Any, Dict, List

from packages.ai_engine.rules import bullet_strength_score, clean_terminal, clean_text, document_skill_names
from packages.job_intelligence.extractor import keyword_names
from packages.resume_formatter import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument

_DERIVED_SKILL_RULES = (
    {
        "name": "AI Systems",
        "category": "AI & Machine Learning",
        "job_terms": ("ai", "llm", "machine learning", "automation", "model"),
        "evidence_terms": ("llm", "large language model", "ai-powered", "ai-generated", "semantic similarity"),
        "reason": "Resume already describes AI or LLM-backed systems.",
    },
    {
        "name": "Evaluation Pipelines",
        "category": "AI & Machine Learning",
        "job_terms": ("evaluation", "llm", "ai", "model", "benchmark"),
        "evidence_terms": ("evaluation pipeline", "benchmark", "manual scoring", "ai-generated outputs"),
        "reason": "Resume already references benchmarking or evaluating AI-generated outputs.",
    },
    {
        "name": "Automation Pipelines",
        "category": "AI & Machine Learning",
        "job_terms": ("automation", "pipeline", "workflow", "llm", "ai"),
        "evidence_terms": ("automation", "pipeline", "workflow", "orchestration"),
        "reason": "Resume already mentions automation or orchestration workflows.",
    },
    {
        "name": "Semantic Similarity",
        "category": "AI & Machine Learning",
        "job_terms": ("semantic", "llm", "ai", "retrieval", "nlp"),
        "evidence_terms": ("semantic similarity",),
        "reason": "Resume already references semantic similarity techniques.",
    },
)


def build_optimization_plan(
    document: ResumeDocument,
    job_description: str,
    role_info: Dict[str, str],
    job_skills: List[Dict[str, Any]],
) -> Dict[str, Any]:
    role_label = (role_info.get("label") or document.title or "Software Engineer").split("|", 1)[0].strip()
    document_text = resume_document_to_text(document)
    resume_skill_names = {skill.lower() for skill in document_skill_names(document)}
    skill_values = {value.lower() for values in document.skills.values() for value in values}
    job_skill_names = keyword_names(job_skills)
    job_text = clean_text(job_description).lower()

    planned_changes: List[Dict[str, Any]] = []

    if role_label:
        planned_changes.append(
            {
                "id": "title:align-role",
                "action": "rewrite_title",
                "type": "title",
                "target_section": "title",
                "priority": 5,
                "reason": f"Align the resume title to the detected {role_label} role language.",
                "role_label": role_label,
            }
        )

    planned_changes.append(
        {
            "id": "summary:optimize",
            "action": "rewrite_summary",
            "type": "summary",
            "target_section": "summary",
            "priority": 10,
            "reason": "Improve the summary only if role alignment can be increased without weakening technical evidence.",
            "role_label": role_label,
        }
    )

    for skill in job_skills:
        name = skill["name"]
        if name.lower() in skill_values:
            continue
        if name.lower() not in resume_skill_names:
            continue
        planned_changes.append(
            {
                "id": f"skills:add:{name.lower()}",
                "action": "add_skill",
                "type": "skills",
                "target_section": "skills",
                "priority": 20,
                "value": name,
                "skill_category": skill.get("category", "architecture"),
                "reason": f"Add {name} to the skills section because the job description emphasizes it and the resume already supports it.",
                "evidence": [f"Resume already references {name} outside the skills section."],
                "job_relevant": True,
            }
        )

    for rule in _DERIVED_SKILL_RULES:
        if rule["name"].lower() in skill_values:
            continue
        if not _matches_terms(document_text, rule["evidence_terms"]):
            continue
        if not _matches_terms(job_text, rule["job_terms"]) and "ml" not in role_label.lower() and "ai" not in role_label.lower():
            continue
        planned_changes.append(
            {
                "id": f"skills:enrich:{rule['name'].lower().replace(' ', '-')}",
                "action": "add_derived_skill",
                "type": "skills",
                "target_section": "skills",
                "priority": 22,
                "value": rule["name"],
                "skill_category": "ml",
                "skill_category_label": rule["category"],
                "reason": rule["reason"],
                "evidence": [f"Matched resume evidence for {rule['name']}."],
                "job_relevant": True,
            }
        )

    if document.skills:
        planned_changes.append(
            {
                "id": "skills:reorder",
                "action": "reorder_skill_sections",
                "type": "skills",
                "target_section": "skills",
                "priority": 30,
                "reason": "Reorder skill sections to match recruiter scan order for the target role.",
                "role_label": role_label,
            }
        )

    for project_index, entry in enumerate(document.projects):
        cleaned_details = clean_text(entry.details)
        if cleaned_details and cleaned_details != entry.details:
            planned_changes.append(
                {
                    "id": f"project:{project_index}:details",
                    "action": "clean_project_details",
                    "type": "project",
                    "target_section": "projects",
                    "priority": 40,
                    "target": {"project_index": project_index},
                    "reason": "Clean project details for more reliable PDF rendering and scan readability.",
                }
            )
        for bullet_index, bullet in enumerate(entry.bullets[:3]):
            cleaned_bullet = clean_terminal(bullet)
            if cleaned_bullet != bullet:
                planned_changes.append(
                    {
                        "id": f"project:{project_index}:bullet:{bullet_index}",
                        "action": "clean_project_bullet",
                        "type": "project",
                        "target_section": "projects",
                        "priority": 42,
                        "target": {"project_index": project_index, "bullet_index": bullet_index},
                        "reason": "Normalize project bullets so exported resumes remain visually consistent.",
                    }
                )

    for entry_index, entry in enumerate(document.experience):
        for bullet_index, bullet in enumerate(entry.bullets[:4]):
            strength = bullet_strength_score(bullet)
            if strength >= 7 and clean_terminal(bullet) == bullet:
                continue
            planned_changes.append(
                {
                    "id": f"experience:{entry_index}:bullet:{bullet_index}",
                    "action": "rewrite_experience_bullet",
                    "type": "experience",
                    "target_section": "experience",
                    "priority": 50,
                    "target": {
                        "entry_index": entry_index,
                        "bullet_index": bullet_index,
                        "role": entry.role,
                        "company": entry.company,
                    },
                    "reason": "Tighten weaker bullet phrasing only if the rewrite improves clarity and preserves truth.",
                    "strength_score": strength,
                }
            )

    planned_changes.sort(key=lambda item: (item["priority"], item["id"]))
    return {
        "role_label": role_label,
        "planned_changes": planned_changes,
        "highlighted_keywords": [skill["name"] for skill in job_skills[:3]],
    }


def _matches_terms(text: str, terms: tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(term in lowered for term in terms)
