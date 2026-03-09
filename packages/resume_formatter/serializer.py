"""Serialize structured resume documents back into editable plain text."""
from __future__ import annotations

from typing import List

from packages.shared_types.resume_document import ResumeDocument


def resume_document_to_text(document: ResumeDocument) -> str:
    lines: List[str] = []

    if document.name:
        lines.append(document.name)
    if document.title:
        lines.append(document.title)
    if document.contact_items:
        lines.append(" | ".join(document.contact_items))
    if document.summary:
        lines.append(document.summary)

    _append_education(lines, document)
    _append_skills(lines, document)
    _append_experience(lines, document)
    _append_projects(lines, document)

    return "\n".join(_trim_trailing_blanks(lines)).strip()


def _append_education(lines: List[str], document: ResumeDocument) -> None:
    if not document.education:
        return
    lines.extend(["", "Education"])
    for entry in document.education:
        line = entry.school
        if entry.degree:
            line = f"{line}, {entry.degree}"
        if entry.date:
            line = f"{line} {entry.date}"
        lines.append(line.strip())
        for detail in entry.details:
            lines.append(f"- {detail}")


def _append_skills(lines: List[str], document: ResumeDocument) -> None:
    if not document.skills:
        return
    lines.extend(["", "Technical Skills"])
    for category, values in document.skills.items():
        lines.append(f"{category}: {', '.join(values)}")


def _append_experience(lines: List[str], document: ResumeDocument) -> None:
    if not document.experience:
        return
    lines.extend(["", "Experience"])
    for entry in document.experience:
        line = entry.role
        if entry.company:
            line = f"{line} - {entry.company}"
        if entry.date:
            line = f"{line} {entry.date}"
        lines.append(line.strip())
        for bullet in entry.bullets:
            if bullet.strip():
                lines.append(f"- {bullet}")


def _append_projects(lines: List[str], document: ResumeDocument) -> None:
    if not document.projects:
        return
    lines.extend(["", "Selected Projects"])
    for entry in document.projects:
        line = entry.name
        if entry.details:
            line = f"{line}: {entry.details}"
        lines.append(line.strip())
        for bullet in entry.bullets:
            if bullet.strip():
                lines.append(f"- {bullet}")


def _trim_trailing_blanks(lines: List[str]) -> List[str]:
    trimmed = list(lines)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    return trimmed
