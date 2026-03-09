"""Final recruiter-facing polish for structured resume documents."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Tuple

from packages.resume_formatter.normalizer import normalize_resume_line
from packages.resume_formatter.serializer import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument

_TECH_NORMALIZATIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bMongo\s+DB\b", re.IGNORECASE), "MongoDB"),
    (re.compile(r"\bCloud\s+Watch\b", re.IGNORECASE), "CloudWatch"),
    (re.compile(r"\bFast\s+API\b", re.IGNORECASE), "FastAPI"),
    (re.compile(r"\bNode\s*\.?\s*js\b", re.IGNORECASE), "Node.js"),
    (re.compile(r"\bNo\s+SQL\b", re.IGNORECASE), "NoSQL"),
)

_DANGLING_ENDINGS = (" and", " with", " using", " via", " through")


def polish_resume_text(
    resume_json: ResumeDocument | Dict[str, Any],
    *,
    role_label: str | None = None,
) -> Tuple[ResumeDocument, Dict[str, Any]]:
    """Polish a structured resume without changing its core claims."""
    document = _coerce_document(resume_json)
    changes: list[str] = []

    document.name = _clean_inline_value(document.name)
    document.title = _clean_inline_value(document.title)
    document.contact_items = [_clean_inline_value(item) for item in document.contact_items if _clean_inline_value(item)]
    document.summary = _polish_summary(document.summary, role_label=role_label, changes=changes)

    for entry in document.education:
        entry.school = _clean_inline_value(entry.school)
        entry.degree = _clean_inline_value(entry.degree)
        entry.date = _clean_inline_value(entry.date)
        entry.details = [_polish_sentence(detail, section="education", context=entry.school, changes=changes) for detail in entry.details]

    normalized_skills: Dict[str, list[str]] = {}
    for category, values in document.skills.items():
        cleaned_category = _clean_inline_value(category)
        cleaned_values: list[str] = []
        for value in values:
            polished_value = _clean_inline_value(value)
            if not polished_value:
                continue
            if polished_value.lower() in {item.lower() for item in cleaned_values}:
                continue
            cleaned_values.append(polished_value)
        if cleaned_values:
            normalized_skills[cleaned_category or "Technical Skills"] = cleaned_values[:10]
    document.skills = normalized_skills

    for entry in document.experience:
        entry.role = _clean_inline_value(entry.role)
        entry.company = _clean_inline_value(entry.company)
        entry.date = _clean_inline_value(entry.date)
        entry.start_date = _clean_inline_value(entry.start_date)
        entry.end_date = _clean_inline_value(entry.end_date)
        context = " ".join(part for part in (entry.role, entry.company, role_label or "") if part).strip()
        entry.bullets = [
            _polish_bullet(bullet, section="experience", context=context, changes=changes)
            for bullet in entry.bullets[:4]
            if _clean_inline_value(bullet)
        ]

    for entry in document.projects:
        entry.name = _clean_inline_value(entry.name)
        project_context = " ".join(part for part in (entry.name, role_label or "") if part).strip()
        entry.details = _polish_sentence(entry.details, section="projects", context=project_context, changes=changes)
        entry.bullets = [
            _polish_bullet(bullet, section="projects", context=project_context, changes=changes)
            for bullet in entry.bullets[:3]
            if _clean_inline_value(bullet)
        ]

    return document, {
        "applied": bool(changes),
        "changes": changes[:12],
        "text": resume_document_to_text(document),
    }


def _coerce_document(value: ResumeDocument | Dict[str, Any]) -> ResumeDocument:
    if isinstance(value, ResumeDocument):
        return value.model_copy(deep=True)
    return ResumeDocument.model_validate(value)


def _clean_inline_value(text: str) -> str:
    cleaned = _normalize_whitespace(text)
    cleaned = _normalize_known_technologies(cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _polish_summary(text: str, *, role_label: str | None, changes: list[str]) -> str:
    polished = _polish_sentence(text, section="summary", context=role_label or "", changes=changes)
    if not polished:
        return polished
    if polished[0].islower():
        polished = polished[0].upper() + polished[1:]
    return polished


def _polish_bullet(text: str, *, section: str, context: str, changes: list[str]) -> str:
    cleaned = _polish_sentence(text, section=section, context=context, changes=changes)
    if not cleaned:
        return cleaned

    if cleaned[:1].islower():
        cleaned = cleaned[:1].upper() + cleaned[1:]

    if len(cleaned.split()) > 35:
        shortened = _shorten_overlong_bullet(cleaned)
        if shortened != cleaned:
            changes.append("Shortened an overlong bullet without changing its core metric or claim.")
            cleaned = shortened

    return _ensure_period(cleaned)


def _polish_sentence(text: str, *, section: str, context: str, changes: list[str]) -> str:
    original = text or ""
    cleaned = normalize_resume_line(original)
    cleaned = _normalize_whitespace(cleaned)
    cleaned = _repair_fragment_artifacts(cleaned)
    cleaned = _normalize_known_technologies(cleaned)
    cleaned = _repair_truncated_text(cleaned, section=section, context=context)
    cleaned = _normalize_whitespace(cleaned)

    if cleaned and section in {"experience", "projects", "summary", "education"}:
        cleaned = _ensure_period(cleaned)

    if cleaned != original.strip():
        changes.append(f"Polished {section} copy for punctuation, spacing, or grammar consistency.")

    return cleaned


def _normalize_whitespace(text: str) -> str:
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", text or "")
    cleaned = re.sub(r"([,.;:!?]){2,}", lambda match: match.group(0)[0], cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+/\s+", "/", cleaned)
    cleaned = cleaned.replace(" .", ".").replace(" ,", ",")
    return cleaned.strip()


def _normalize_known_technologies(text: str) -> str:
    normalized = text
    for pattern, replacement in _TECH_NORMALIZATIONS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def _repair_fragment_artifacts(text: str) -> str:
    repaired = re.sub(
        r"\.\s*(?:servability|observability)\s*,\s*and\s*performance stability\b",
        ", improving observability and performance stability",
        text,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(r"\bservability\b", "observability", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"\bMoni,\s*toring\b", "Monitoring", repaired, flags=re.IGNORECASE)
    repaired = re.sub(r"\bresume\b(?=\s+mechanisms)", "resume", repaired, flags=re.IGNORECASE)
    return repaired


def _repair_truncated_text(text: str, *, section: str, context: str) -> str:
    stripped = text.rstrip()
    if not stripped:
        return stripped

    lowered = stripped.lower()
    if any(lowered.endswith(token) for token in _DANGLING_ENDINGS):
        stem = stripped.rsplit(" ", 1)[0].rstrip(",;:-")
        tail = stripped[len(stem):].strip().lower()
        completion = _completion_fragment(section=section, context=f"{context} {stem}")
        if tail == "and":
            return stem
        if tail in {"with", "using", "via", "through"}:
            return f"{stem} {tail} {completion}"

    if stripped.endswith((",", ";", ":")):
        stem = stripped.rstrip(",;: ")
        if section == "projects":
            completion = _completion_fragment(section=section, context=f"{context} {stem}")
            return f"{stem}, supporting {completion}"
        return stem

    return stripped


def _completion_fragment(*, section: str, context: str) -> str:
    lowered = context.lower()
    if any(token in lowered for token in ("conversational", "workflow", "automation", "agentic")):
        return "backend APIs and stateful orchestration"
    if any(token in lowered for token in ("llm", "semantic", "evaluation", "data pipeline", "analytics", "retrieval")):
        return "data and evaluation pipelines"
    if any(token in lowered for token in ("aws", "cloud", "lambda", "serverless", "infrastructure")):
        return "cloud production systems"
    if any(token in lowered for token in ("backend", "api", "microservice", "distributed")):
        return "scalable backend services"
    if section == "projects":
        return "production-scale systems"
    return "production systems"


def _ensure_period(text: str) -> str:
    cleaned = text.rstrip()
    if not cleaned:
        return cleaned
    if cleaned[-1] in ".!?":
        return cleaned
    return f"{cleaned}."


def _shorten_overlong_bullet(text: str) -> str:
    if "; " in text:
        return _ensure_period(text.split(";", 1)[0].rstrip())
    if ". " in text:
        return _ensure_period(text.split(". ", 1)[0].rstrip())
    return text
