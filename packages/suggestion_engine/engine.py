"""Parse external suggestions and apply them to a structured resume document."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from packages.job_intelligence.extractor import extract_resume_skills
from packages.shared_types.resume_document import ResumeDocument

_ORDINAL_MAP = {
    "first": 0,
    "second": 1,
    "third": 2,
    "fourth": 3,
    "fifth": 4,
}

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

_WEAK_OPENINGS = {
    "worked on": "Built",
    "responsible for": "Owned",
    "helped": "Supported",
    "used": "Applied",
    "built": "Architected",
    "developed": "Engineered",
}


def apply_suggestions_to_document(document: ResumeDocument, suggestions_text: str) -> Dict[str, Any]:
    updated = document.model_copy(deep=True)
    actions = _parse_suggestions(suggestions_text, document)
    applied_changes: List[str] = []
    unresolved: List[str] = []
    added_skill_names: List[str] = []
    bullet_improvements: Dict[str, int] = {}

    for action in actions:
        action_type = action["type"]
        if action_type == "add_skill":
            skill = action["skill"]
            category = _add_skill(updated, skill["name"], skill["category"])
            if category:
                added_skill_names.append(skill["name"])
                applied_changes.append(f"Added {skill['name']} to {category}.")
            continue

        if action_type == "rewrite_summary":
            _rewrite_summary(updated, added_skill_names, action["instruction"])
            applied_changes.append("Strengthened the summary for clearer role positioning.")
            continue

        if action_type == "enhance_experience":
            count, target_label = _enhance_experience(updated, action)
            if count:
                bucket = target_label or "resume experience"
                bullet_improvements[bucket] = bullet_improvements.get(bucket, 0) + count
            else:
                unresolved.append(action["instruction"])
            continue

        if action_type == "general_improvement":
            if _apply_general_improvement(updated, action["instruction"], added_skill_names):
                applied_changes.append(f"Applied: {action['instruction']}")
            else:
                unresolved.append(action["instruction"])

    if not applied_changes and suggestions_text.strip():
        _rewrite_summary(updated, added_skill_names, suggestions_text)
        count, target_label = _enhance_experience(
            updated,
            {"instruction": suggestions_text, "entry_index": None, "bullet_index": None},
        )
        if updated.summary:
            applied_changes.append("Strengthened the summary for clearer role positioning.")
        if count:
            bucket = target_label or "resume experience"
            bullet_improvements[bucket] = bullet_improvements.get(bucket, 0) + count

    for target_label, count in bullet_improvements.items():
        suffix = f" in {target_label}" if target_label != "resume experience" else ""
        applied_changes.append(f"Improved {count} experience bullet{'s' if count != 1 else ''}{suffix}.")

    requested_skills = _requested_skills(actions)
    updated_resume_skills = {skill["name"] for skill in extract_resume_skills(_document_skill_source(updated))}
    remaining_skills = [skill for skill in requested_skills if skill["name"] not in updated_resume_skills]

    return {
        "document": updated,
        "applied_changes": _dedupe(applied_changes)[:6],
        "unresolved_suggestions": _dedupe(unresolved)[:4],
        "requested_skills": requested_skills,
        "remaining_skills": remaining_skills,
    }


def _parse_suggestions(suggestions_text: str, document: ResumeDocument) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []

    for raw_line in suggestions_text.splitlines():
        instruction = _clean_instruction(raw_line)
        if not instruction:
            continue

        lower = instruction.lower()
        suggestion_skills = extract_resume_skills(instruction)
        summary_related = any(marker in lower for marker in ("summary", "profile", "headline"))
        experience_related = any(
            marker in lower for marker in ("bullet", "experience", "internship", "quantify", "metric", "impact", "scale")
        )
        handled = False

        if suggestion_skills and _mentions_skill_addition(lower):
            for skill in suggestion_skills:
                actions.append({"type": "add_skill", "instruction": instruction, "skill": skill})
            handled = True

        if summary_related:
            actions.append({"type": "rewrite_summary", "instruction": instruction})
            handled = True

        if experience_related or (not summary_related and any(marker in lower for marker in ("rewrite", "improve", "strengthen"))):
            entry_index, bullet_index = _find_experience_target(document, lower)
            actions.append(
                {
                    "type": "enhance_experience",
                    "instruction": instruction,
                    "entry_index": entry_index,
                    "bullet_index": bullet_index,
                }
            )
            handled = True

        if not handled:
            actions.append({"type": "general_improvement", "instruction": instruction})

    return actions


def _clean_instruction(line: str) -> str:
    cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
    return re.sub(r"\s+", " ", cleaned)


def _mentions_skill_addition(lowered_instruction: str) -> bool:
    return any(
        marker in lowered_instruction
        for marker in ("add ", "include ", "mention ", "highlight ", "technical skill", "skill", "languages")
    )


def _find_experience_target(document: ResumeDocument, lowered_instruction: str) -> Tuple[int | None, int | None]:
    bullet_index = None
    for token, index in _ORDINAL_MAP.items():
        if f"{token} bullet" in lowered_instruction:
            bullet_index = index
            break

    for index, entry in enumerate(document.experience):
        company = entry.company.lower()
        role = entry.role.lower()
        if company and company in lowered_instruction:
            return index, bullet_index
        if role and role in lowered_instruction:
            return index, bullet_index
        if company and any(token in lowered_instruction for token in company.split()):
            return index, bullet_index

    return None, bullet_index


def _add_skill(document: ResumeDocument, skill_name: str, skill_category: str) -> str | None:
    for category, values in document.skills.items():
        if skill_name in values:
            return None

    category_name = _pick_skill_category(document, skill_category)
    document.skills.setdefault(category_name, [])
    document.skills[category_name].append(skill_name)
    document.skills[category_name] = _dedupe(document.skills[category_name])[:12]
    return category_name


def _pick_skill_category(document: ResumeDocument, skill_category: str) -> str:
    preferred = _CATEGORY_HINTS.get(skill_category, "Technical Skills")
    preferred_lower = preferred.lower()

    for category in document.skills:
        lowered = category.lower()
        if preferred_lower in lowered:
            return category
        if skill_category == "language" and "language" in lowered:
            return category
        if skill_category in {"cloud", "tool", "methodology"} and ("cloud" in lowered or "infra" in lowered):
            return category
        if skill_category == "database" and "database" in lowered:
            return category
        if skill_category == "architecture" and ("backend" in lowered or "system" in lowered):
            return category

    return preferred


def _rewrite_summary(document: ResumeDocument, added_skills: List[str], instruction: str) -> None:
    focus_skills = list(added_skills)
    for values in document.skills.values():
        for skill in values:
            if skill not in focus_skills:
                focus_skills.append(skill)

    title = _role_label_from_document(document)
    focus = ", ".join(focus_skills[:4]) if focus_skills else "scalable backend systems"
    summary = f"{title} focused on {focus}, delivering reliable systems with measurable product impact."

    if "quantify" in instruction.lower() or "metric" in instruction.lower():
        summary = f"{summary.rstrip('.')} Known for translating technical work into clear business outcomes."

    document.summary = _truncate(summary, 240)


def _role_label_from_document(document: ResumeDocument) -> str:
    title = document.title.strip()
    if not title:
        return "Software engineer"
    return title.split("|", 1)[0].strip() or title


def _enhance_experience(document: ResumeDocument, action: Dict[str, Any]) -> Tuple[int, str]:
    if not document.experience:
        return 0, ""

    target_entry = action.get("entry_index")
    target_bullet = action.get("bullet_index")
    target_entries = [target_entry] if target_entry is not None else list(range(len(document.experience)))
    improved = 0
    target_label = ""

    for entry_index in target_entries:
        if entry_index is None or entry_index >= len(document.experience):
            continue

        entry = document.experience[entry_index]
        bullet_indexes = [target_bullet] if target_bullet is not None else list(range(len(entry.bullets)))
        for bullet_index in bullet_indexes:
            if bullet_index is None or bullet_index >= len(entry.bullets):
                continue
            upgraded = _upgrade_bullet(entry.bullets[bullet_index], action["instruction"])
            if upgraded != entry.bullets[bullet_index]:
                entry.bullets[bullet_index] = upgraded
                improved += 1
                target_label = entry.company or entry.role
            if target_bullet is not None:
                break
        if improved and target_entry is not None:
            break

    if improved == 0:
        for entry in document.experience:
            for index, bullet in enumerate(entry.bullets):
                upgraded = _upgrade_bullet(bullet, action["instruction"])
                if upgraded != bullet:
                    entry.bullets[index] = upgraded
                    improved += 1
                    target_label = entry.company or entry.role
                    break
            if improved:
                break

    return improved, target_label


def _upgrade_bullet(bullet: str, instruction: str) -> str:
    original = bullet.strip().rstrip(".")
    updated = original
    lowered = updated.lower()

    for weak, strong in _WEAK_OPENINGS.items():
        if lowered.startswith(weak):
            updated = f"{strong}{updated[len(weak):]}"
            lowered = updated.lower()
            break

    suggested_skills = [skill["name"] for skill in extract_resume_skills(instruction)]
    for skill in suggested_skills[:1]:
        if skill.lower() not in lowered:
            updated = f"{updated} using {skill}"
            lowered = updated.lower()

    if any(token in instruction.lower() for token in ("quantify", "metric", "scale", "impact")) and not any(char.isdigit() for char in updated):
        updated = f"{updated} for production-scale workloads and measurable business impact"
    elif not re.search(r"(improv|reduc|increas|optim|accelerat|impact|reliab)", lowered):
        updated = f"{updated} to improve reliability and delivery speed"

    updated = updated.strip().rstrip(".")
    return _truncate(f"{updated}.", 140)


def _apply_general_improvement(document: ResumeDocument, instruction: str, added_skills: List[str]) -> bool:
    before_summary = document.summary
    _rewrite_summary(document, added_skills, instruction)
    if document.summary != before_summary:
        return True
    count, _ = _enhance_experience(document, {"instruction": instruction, "entry_index": None, "bullet_index": None})
    return count > 0


def _requested_skills(actions: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    requested: List[Dict[str, Any]] = []
    for action in actions:
        if action["type"] == "add_skill":
            requested.append(action["skill"])
    return _dedupe_skills(requested)


def _document_skill_source(document: ResumeDocument) -> str:
    parts: List[str] = []
    for values in document.skills.values():
        parts.extend(values)
    for entry in document.experience:
        parts.extend(entry.bullets)
    return "\n".join(parts)


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


def _dedupe_skills(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    ordered: List[Dict[str, Any]] = []
    for item in items:
        key = item["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def _truncate(value: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if len(cleaned) <= limit:
        return cleaned
    clipped = cleaned[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:-")
    return f"{clipped}..."
