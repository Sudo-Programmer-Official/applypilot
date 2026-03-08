"""Build a structured resume document from plain text."""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

from packages.shared_types.resume_document import (
    ResumeDocument,
    ResumeEducationItem,
    ResumeExperienceItem,
    ResumeProjectItem,
)

_SECTION_ALIASES = {
    "education": "education",
    "technical skills": "skills",
    "skills": "skills",
    "core skills": "skills",
    "experience": "experience",
    "professional experience": "experience",
    "work experience": "experience",
    "employment": "experience",
    "projects": "projects",
    "selected projects": "projects",
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "target role alignment": "summary",
}

_BULLET_PREFIXES = ("- ", "* ", "• ", "\u2022 ")
_DATE_PATTERN = re.compile(
    r"(?P<date>("
    r"(?:[A-Za-z]{3,9}\s+\d{4}(?:\s*\(Expected\))?(?:\s*[-\u2013]\s*(?:[A-Za-z]{3,9}\s+\d{4}|Present|Current))?)"
    r"|(?:\d{4}\s*[-\u2013]\s*(?:\d{4}|Present|Current))"
    r"))$"
)


def build_resume_document(resume_text: str, role_label: str | None = None) -> ResumeDocument:
    sections = _split_sections(resume_text or "")
    name, title, contact_items, header_summary = _parse_header(sections.get("header", []), role_label)
    summary_lines = sections.get("summary", []) or ([header_summary] if header_summary else [])

    return ResumeDocument(
        name=name,
        title=title,
        contact_items=contact_items,
        summary=_truncate_text(" ".join(summary_lines).strip(), 260),
        education=_parse_education(sections.get("education", [])),
        skills=_parse_skills(sections.get("skills", [])),
        experience=_parse_experience(sections.get("experience", [])),
        projects=_parse_projects(sections.get("projects", [])),
    )


def summarize_resume_sections(document: ResumeDocument) -> List[Dict[str, int | str]]:
    return [
        {"name": "education", "items": len(document.education)},
        {"name": "skills", "items": len(document.skills)},
        {"name": "experience", "items": len(document.experience)},
        {"name": "projects", "items": len(document.projects)},
    ]


def _split_sections(resume_text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {
        "header": [],
        "summary": [],
        "education": [],
        "skills": [],
        "experience": [],
        "projects": [],
    }

    current_section = "header"
    for raw_line in (resume_text or "").replace("\uf0b7", "•").splitlines():
        line = _normalize_line(raw_line)
        if not line:
            continue

        section_key = _section_key(line)
        if section_key:
            current_section = section_key
            continue

        sections.setdefault(current_section, []).append(line)

    return sections


def _section_key(line: str) -> str | None:
    normalized = re.sub(r"[:\s]+", " ", line.strip().lower()).strip()
    return _SECTION_ALIASES.get(normalized)


def _normalize_line(line: str) -> str:
    cleaned = line.replace("\xa0", " ").strip()
    if "|" in cleaned:
        cleaned = cleaned.replace("|", " | ")
    if cleaned and " " not in cleaned and re.search(r"[a-z][A-Z]", cleaned):
        cleaned = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _parse_header(header_lines: List[str], role_label: str | None) -> Tuple[str, str, List[str], str]:
    if not header_lines:
        return "Candidate", role_label or "", [], ""

    name = _normalize_name(header_lines[0])
    title = ""
    contact_items: List[str] = []
    summary_parts: List[str] = []

    for line in header_lines[1:]:
        if not title and _looks_like_title(line):
            title = line
        elif _looks_like_contact(line):
            contact_items.extend(_split_contact_line(line))
        else:
            summary_parts.append(line)

    if not title and role_label:
        title = role_label

    return name, title, _dedupe(contact_items), " ".join(summary_parts).strip()


def _normalize_name(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value).strip()
    if collapsed.isupper():
        return collapsed.title()
    return collapsed


def _looks_like_contact(line: str) -> bool:
    lowered = line.lower()
    if "@" in line or "linkedin" in lowered or "github" in lowered or "http" in lowered:
        return True
    if re.search(r"\+?\d[\d(). -]{7,}", line):
        return True
    if "|" in line and any(token in lowered for token in ("email", "phone", "linkedin", "github", ".com")):
        return True
    return False


def _split_contact_line(line: str) -> List[str]:
    parts = [part.strip() for part in re.split(r"\s*\|\s*", line) if part.strip()]
    if len(parts) > 1:
        return parts
    return [line.strip()]


def _looks_like_title(line: str) -> bool:
    lowered = line.lower()
    if lowered.endswith("."):
        return False
    return len(line.split()) <= 14 and not _looks_like_contact(line)


def _parse_education(lines: List[str]) -> List[ResumeEducationItem]:
    entries: List[ResumeEducationItem] = []
    current: ResumeEducationItem | None = None

    for line in lines:
        bullet = _strip_bullet(line)
        if bullet and current:
            current.details.append(_truncate_text(bullet, 140))
            continue

        main, date = _split_trailing_date(line)
        school, degree = _split_once(main, ",")
        current = ResumeEducationItem(
            school=school or main,
            degree=degree,
            date=date,
        )
        entries.append(current)

    return entries


def _parse_skills(lines: List[str]) -> Dict[str, List[str]]:
    categories: Dict[str, List[str]] = {}
    for line in lines:
        cleaned = _strip_bullet(line) or line
        if ":" in cleaned:
            category, values = cleaned.split(":", 1)
            category_name = category.strip() or "Core Skills"
            skill_values = _split_skill_values(values)
        else:
            category_name = "Core Skills"
            skill_values = _split_skill_values(cleaned)

        if not skill_values:
            continue

        categories.setdefault(category_name, [])
        categories[category_name].extend(skill_values)
        categories[category_name] = _dedupe(categories[category_name])[:10]

    return categories


def _split_skill_values(values: str) -> List[str]:
    items = [item.strip(" -") for item in re.split(r",|;|\u2022", values) if item.strip(" -")]
    return [item for item in items if item]


def _parse_experience(lines: List[str]) -> List[ResumeExperienceItem]:
    entries: List[ResumeExperienceItem] = []
    current: ResumeExperienceItem | None = None

    for line in lines:
        bullet = _strip_bullet(line)
        if bullet:
            if current is None:
                current = ResumeExperienceItem(role="Experience", company="", date="", bullets=[])
                entries.append(current)
            current.bullets.append(_truncate_text(bullet, 140))
            current.bullets = current.bullets[:5]
            continue

        if current and current.bullets:
            role, company, date = _parse_role_company_date(line)
            if role or company or date:
                current = ResumeExperienceItem(role=role, company=company, date=date, bullets=[])
                entries.append(current)
                continue

        role, company, date = _parse_role_company_date(line)
        if role or company or date:
            current = ResumeExperienceItem(role=role, company=company, date=date, bullets=[])
            entries.append(current)
            continue

        if current is None:
            current = ResumeExperienceItem(role=line, company="", date="", bullets=[])
            entries.append(current)
            continue

        if current.company:
            current.company = _truncate_text(f"{current.company} {line}".strip(), 80)
        else:
            current.company = _truncate_text(line, 80)

    return [entry for entry in entries if entry.role or entry.company or entry.bullets]


def _parse_projects(lines: List[str]) -> List[ResumeProjectItem]:
    entries: List[ResumeProjectItem] = []
    current: ResumeProjectItem | None = None

    for line in lines:
        bullet = _strip_bullet(line)
        if bullet:
            if current is None:
                current = ResumeProjectItem(name="Project", details="", bullets=[])
                entries.append(current)
            current.bullets.append(_truncate_text(bullet, 140))
            current.bullets = current.bullets[:3]
            continue

        if ":" in line:
            name, details = _split_once(line, ":")
            current = ResumeProjectItem(
                name=name or "Project",
                details=_truncate_text(details, 180),
                bullets=[],
            )
            entries.append(current)
            continue

        current = ResumeProjectItem(name=line, details="", bullets=[])
        entries.append(current)

    return entries[:3]


def _parse_role_company_date(line: str) -> Tuple[str, str, str]:
    main, date = _split_trailing_date(line)
    for separator in (" - ", " – ", " -- ", " | "):
        if separator in main:
            left, right = main.split(separator, 1)
            return _truncate_text(left.strip(), 70), _truncate_text(right.strip(), 70), date
    return _truncate_text(main.strip(), 90), "", date


def _split_trailing_date(line: str) -> Tuple[str, str]:
    match = _DATE_PATTERN.search(line)
    if not match:
        return line.strip(), ""
    date = match.group("date").strip()
    main = line[: match.start()].strip(" ,-")
    return main, date


def _split_once(value: str, separator: str) -> Tuple[str, str]:
    if separator not in value:
        return value.strip(), ""
    left, right = value.split(separator, 1)
    return left.strip(), right.strip()


def _strip_bullet(line: str) -> str:
    stripped = line.strip()
    for prefix in _BULLET_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return ""


def _truncate_text(value: str, max_length: int) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if len(cleaned) <= max_length:
        return cleaned
    truncated = cleaned[: max_length - 1].rsplit(" ", 1)[0].rstrip(",;:-")
    return f"{truncated}..."


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
