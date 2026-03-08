"""Build a structured resume document from plain text."""
from __future__ import annotations

import re
from statistics import median
from typing import Dict, Iterable, List, Tuple

from .normalizer import normalize_resume_line
from packages.shared_types.resume_document import (
    ResumeDocument,
    ResumeEducationItem,
    ResumeExperienceItem,
    ResumeLayoutBlock,
    ResumeProjectItem,
)

_SECTION_ALIASES = {
    "education": "education",
    "technical skills": "skills",
    "technical expertise": "skills",
    "skills and tools": "skills",
    "skills & tools": "skills",
    "skills": "skills",
    "core skills": "skills",
    "certifications": "skills",
    "certification": "skills",
    "experience": "experience",
    "professional experience": "experience",
    "work experience": "experience",
    "employment": "experience",
    "projects": "projects",
    "selected projects": "projects",
    "publications": "projects",
    "publication": "projects",
    "research": "projects",
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "target role alignment": "summary",
    "objective": "summary",
}

_COMPACT_SECTION_ALIASES = {
    re.sub(r"[^a-z]", "", alias): section for alias, section in _SECTION_ALIASES.items()
}

_BULLET_PREFIXES = ("- ", "* ", "• ", "\u2022 ")
_ROLE_KEYWORDS = {
    "engineer",
    "developer",
    "intern",
    "manager",
    "lead",
    "architect",
    "scientist",
    "analyst",
    "consultant",
    "assistant",
    "specialist",
    "director",
    "administrator",
    "owner",
    "founder",
    "researcher",
}
_COMPANY_HINTS = {
    "inc",
    "llc",
    "ltd",
    "corp",
    "corporation",
    "company",
    "technologies",
    "technology",
    "systems",
    "solutions",
    "labs",
    "health",
    "university",
    "institute",
    "bank",
    "group",
}
_DATE_PATTERN = re.compile(
    r"(?P<date>("
    r"(?:[A-Za-z]{3,9}\s+\d{4}(?:\s*\(Expected\))?(?:\s*[-\u2013]\s*(?:[A-Za-z]{3,9}\s+\d{4}|Present|Current))?)"
    r"|(?:\d{4}\s*[-\u2013]\s*(?:\d{4}|Present|Current))"
    r"))$"
)


def build_resume_document(
    resume_text: str,
    role_label: str | None = None,
    layout_blocks: List[ResumeLayoutBlock] | None = None,
) -> ResumeDocument:
    sections = _split_layout_sections(layout_blocks) if layout_blocks else _split_sections(resume_text or "")
    name, title, contact_items, header_summary = _parse_header(sections.get("header", []), role_label)
    summary_lines = sections.get("summary", []) or ([header_summary] if header_summary else [])

    return ResumeDocument(
        name=name,
        title=title,
        contact_items=contact_items,
        summary=_clean_text(" ".join(summary_lines).strip()),
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


def _split_layout_sections(blocks: List[ResumeLayoutBlock]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {
        "header": [],
        "summary": [],
        "education": [],
        "skills": [],
        "experience": [],
        "projects": [],
    }
    if not blocks:
        return sections

    font_sizes = [block.font_size for block in blocks if block.font_size > 0]
    baseline_font = median(font_sizes) if font_sizes else 11.0
    current_section = "header"

    for block in sorted(blocks, key=lambda item: (item.page, item.order, item.top, item.x0)):
        line = _normalize_line(block.text)
        if not line:
            continue

        section_key = _layout_section_key(line, block, baseline_font)
        if section_key:
            current_section = section_key
            continue

        sections.setdefault(current_section, []).append(line)

    return sections


def _section_key(line: str) -> str | None:
    normalized = re.sub(r"[:\s]+", " ", line.strip().lower()).strip()
    compact = re.sub(r"[^a-z]", "", normalized)
    return _SECTION_ALIASES.get(normalized) or _COMPACT_SECTION_ALIASES.get(compact)


def _layout_section_key(line: str, block: ResumeLayoutBlock, baseline_font: float) -> str | None:
    explicit = _section_key(line)
    if explicit:
        return explicit

    normalized_style = block.style_name.lower().strip()
    if normalized_style.startswith("heading") or normalized_style in {"title", "subtitle"}:
        return _section_key(line)

    looks_like_header = (
        len(line.split()) <= 4
        and not _looks_like_contact(line)
        and not re.search(r"\d{4}", line)
        and (block.is_bold or block.font_size >= baseline_font * 1.18)
    )
    if looks_like_header:
        return _section_key(line)

    return None


def _normalize_line(line: str) -> str:
    return normalize_resume_line(line)


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
            current.details.append(_clean_text(bullet))
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
    current_category = "Core Skills"
    for line in lines:
        cleaned = _strip_bullet(line) or line
        if ":" in cleaned:
            category, values = cleaned.split(":", 1)
            category_name = category.strip() or "Core Skills"
            skill_values = _split_skill_values(values)
            current_category = category_name
        else:
            category_name = current_category
            skill_values = _split_skill_values(cleaned)

        if not skill_values:
            continue

        categories.setdefault(category_name, [])
        _merge_skill_fragments(categories[category_name], skill_values)
        categories[category_name] = _dedupe(categories[category_name])[:10]

    return categories


def _split_skill_values(values: str) -> List[str]:
    items = [item.strip(" -") for item in re.split(r",|;|\u2022", values) if item.strip(" -")]
    return [item for item in items if item]


def _merge_skill_fragments(existing: List[str], incoming: List[str]) -> None:
    if not incoming:
        return

    if existing:
        previous = existing[-1]
        first = incoming[0]
        if _should_join_skill_fragments(previous, first):
            existing[-1] = _clean_text(f"{previous.rstrip('-')}{first}")
            incoming = incoming[1:]

    existing.extend(_clean_text(item) for item in incoming)


def _should_join_skill_fragments(previous: str, current: str) -> bool:
    prev = previous.strip()
    curr = current.strip()
    if not prev or not curr:
        return False
    if prev.endswith("-"):
        return True
    if " " in prev or " " in curr:
        return False
    if not curr[:1].islower():
        return False
    if not prev.replace("/", "").replace("+", "").isalpha():
        return False
    if not curr.replace("/", "").replace("+", "").isalpha():
        return False
    return len(prev) <= 10 and len(curr) <= 10


def _should_merge_bullet_continuation(line: str) -> bool:
    if not line:
        return False
    if _DATE_PATTERN.search(line):
        return False
    if _section_key(line):
        return False
    if any(separator in line for separator in (" @ ", " | ", " – ", " - ", " -- ")):
        return False
    first_char = line[0]
    if first_char.islower() or first_char.isdigit():
        return True
    return len(line.split()) >= 7


def _merge_wrapped_text(previous: str, current: str) -> str:
    if previous.rstrip().endswith("-") and current[:1].islower():
        return _clean_text(f"{previous.rstrip()[:-1]}{current}")
    return _clean_text(f"{previous} {current}")


def _parse_experience(lines: List[str]) -> List[ResumeExperienceItem]:
    entries: List[ResumeExperienceItem] = []
    current: ResumeExperienceItem | None = None

    for line in lines:
        cleaned_line = _clean_text(line)
        bullet = _strip_bullet(line)
        if bullet:
            if current is None:
                current = ResumeExperienceItem(role="Experience", company="", date="", start_date="", end_date="", bullets=[])
                entries.append(current)
            current.bullets.append(_clean_text(bullet))
            current.bullets = current.bullets[:4]
            continue

        if current and current.bullets and _should_merge_bullet_continuation(cleaned_line):
            current.bullets[-1] = _merge_wrapped_text(current.bullets[-1], cleaned_line)
            continue

        if current and current.bullets:
            role, company, date, start_date, end_date = _parse_role_company_date(cleaned_line)
            if role or company or date:
                current = ResumeExperienceItem(
                    role=role,
                    company=company,
                    date=date,
                    start_date=start_date,
                    end_date=end_date,
                    bullets=[],
                )
                entries.append(current)
                continue

        role, company, date, start_date, end_date = _parse_role_company_date(cleaned_line)
        if role or company or date:
            current = ResumeExperienceItem(
                role=role,
                company=company,
                date=date,
                start_date=start_date,
                end_date=end_date,
                bullets=[],
            )
            entries.append(current)
            continue

        if current is None:
            current = ResumeExperienceItem(role=cleaned_line, company="", date="", start_date="", end_date="", bullets=[])
            entries.append(current)
            continue

        if current.company:
            current.company = _clean_text(f"{current.company} {cleaned_line}".strip())
        else:
            current.company = cleaned_line

    return [entry for entry in entries if entry.role or entry.company or entry.bullets]


def _parse_projects(lines: List[str]) -> List[ResumeProjectItem]:
    entries: List[ResumeProjectItem] = []
    current: ResumeProjectItem | None = None

    for line in lines:
        cleaned_line = _clean_text(line)
        bullet = _strip_bullet(line)
        if bullet:
            if current is None:
                current = ResumeProjectItem(name="Project", details="", bullets=[])
                entries.append(current)
            current.bullets.append(_clean_text(bullet))
            current.bullets = current.bullets[:3]
            continue

        if current and current.bullets and _should_merge_bullet_continuation(cleaned_line):
            current.bullets[-1] = _merge_wrapped_text(current.bullets[-1], cleaned_line)
            continue

        if ":" in cleaned_line:
            name, details = _split_once(cleaned_line, ":")
            current = ResumeProjectItem(
                name=name or "Project",
                details=_clean_text(details),
                bullets=[],
            )
            entries.append(current)
            continue

        current = ResumeProjectItem(name=cleaned_line, details="", bullets=[])
        entries.append(current)

    return entries[:3]


def _parse_role_company_date(line: str) -> Tuple[str, str, str, str, str]:
    main, date = _split_trailing_date(line)
    start_date, end_date = _split_date_range(date)
    parts = _split_experience_heading(main)

    if len(parts) >= 2:
        role, company = _classify_role_company(parts)
        return (
            _clean_text(role),
            _clean_text(company),
            date,
            start_date,
            end_date,
        )

    return _clean_text(main.strip()), "", date, start_date, end_date


def _split_trailing_date(line: str) -> Tuple[str, str]:
    match = _DATE_PATTERN.search(line)
    if not match:
        return line.strip(), ""
    date = match.group("date").strip()
    main = line[: match.start()].strip(" ,-")
    return main, date


def _split_date_range(value: str) -> Tuple[str, str]:
    if not value:
        return "", ""
    parts = [part.strip() for part in re.split(r"\s*[-\u2013]\s*", value, maxsplit=1) if part.strip()]
    if len(parts) == 2:
        return parts[0], parts[1]
    return value.strip(), ""


def _split_experience_heading(value: str) -> List[str]:
    for separator in (" @ ", " | ", " – ", " - ", " -- ", ", "):
        if separator in value:
            return [part.strip() for part in value.split(separator) if part.strip()]
    return [value.strip()]


def _classify_role_company(parts: List[str]) -> Tuple[str, str]:
    if len(parts) == 2:
        left, right = parts
        left_role_score = _role_score(left)
        right_role_score = _role_score(right)
        left_company_score = _company_score(left)
        right_company_score = _company_score(right)

        if left_role_score > right_role_score or right_company_score > left_company_score:
            return left, right
        if right_role_score > left_role_score or left_company_score > right_company_score:
            return right, left
        return left, right

    left = parts[0]
    right = parts[-1]
    middle = " - ".join(parts[1:-1]).strip()
    if middle and _role_score(middle) >= max(_role_score(left), _role_score(right)):
        return middle, f"{left} - {right}".strip(" -")
    return _classify_role_company([left, " - ".join(parts[1:]).strip()])


def _role_score(value: str) -> int:
    lowered = value.lower()
    score = sum(2 for token in _ROLE_KEYWORDS if token in lowered)
    if "software" in lowered or "data" in lowered or "backend" in lowered:
        score += 1
    return score


def _company_score(value: str) -> int:
    lowered = value.lower()
    score = sum(2 for token in _COMPANY_HINTS if token in lowered)
    if value and value == value.title():
        score += 1
    if len(value.split()) <= 4:
        score += 1
    return score


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
