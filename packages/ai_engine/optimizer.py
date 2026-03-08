"""Deterministic placeholder optimizer for ApplyPilot's AI engine."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from packages.job_intelligence.extractor import analyze_job_description, extract_resume_skills, keyword_names


def _is_section_heading(line: str) -> bool:
    normalized = line.strip()
    if not normalized:
        return False
    return normalized.isupper() or normalized.endswith(":")


def _should_preserve_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if "@" in stripped or "http" in stripped.lower():
        return True
    if "|" in stripped or "\\" in stripped:
        return True
    if sum(char.isdigit() for char in stripped) >= 5:
        return True
    if len(stripped.split()) <= 2 and stripped == stripped.title():
        return True
    return False


def _inject_keyword(line: str, keyword: str) -> str:
    if keyword.lower() in line.lower():
        return line
    line = line.rstrip(".")
    return f"{line} using {keyword}."


def _add_impact(line: str) -> str:
    if any(char.isdigit() for char in line):
        return line
    line = line.rstrip(".")
    return f"{line} with measurable business impact."


def _seed_resume(job_keywords: List[str]) -> str:
    focus = ", ".join(job_keywords[:3]) or "target role keywords"
    return "\n".join(
        [
            "Professional Summary",
            f"Targeted candidate profile aligned to {focus}.",
            "",
            "Experience",
            "- Led cross-functional delivery with measurable business impact.",
            "- Improved systems reliability and stakeholder communication.",
        ]
    )


def _is_bullet(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("-") or stripped.startswith("*") or stripped.startswith("•")


def _split_bullet(line: str) -> tuple[str, str]:
    stripped = line.strip()
    if stripped.startswith(("•", "-", "*")):
        return stripped[0], stripped[1:].strip()
    return "-", stripped


def _stronger_opening(line: str) -> str:
    replacements = {
        "worked on": "Built",
        "responsible for": "Owned",
        "helped": "Supported",
        "used": "Applied",
        "built": "Architected",
        "developed": "Engineered",
    }
    lowered = line.lower()
    for old, new in replacements.items():
        if lowered.startswith(old):
            return f"{new}{line[len(old):]}"
    return line


def _compose_summary(job_keywords: List[str]) -> str:
    if not job_keywords:
        return "Distributed systems engineer focused on reliable backend delivery and measurable product impact."
    focus = ", ".join(job_keywords[:4])
    return f"Distributed systems engineer aligned to {focus}, with a focus on scalable backend delivery and reliability."


def _enrich_bullet(line: str, missing_keywords: List[str], keyword_cursor: int) -> tuple[str, int]:
    bullet = _stronger_opening(line.rstrip("."))
    additions: List[str] = []

    if keyword_cursor < len(missing_keywords):
        additions.append(missing_keywords[keyword_cursor])
        keyword_cursor += 1

    if not any(char.isdigit() for char in bullet):
        additions.append("reliability")

    if additions:
        bullet = f"{bullet} using {' and '.join(additions[:2])}"

    if not re.search(r"(improv|reduc|increas|optim|accelerat)", bullet.lower()):
        bullet = f"{bullet}, improving delivery quality"

    bullet = bullet.strip().rstrip(".")
    return f"{bullet}.", keyword_cursor


def optimize_resume(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Return a deterministic optimization pass that makes the UI feel alive.

    This is intentionally heuristic and does not claim model-driven accuracy.
    """
    job_keywords = keyword_names(analyze_job_description(job_description or "", limit=10).get("skills", []))
    resume_keywords = set(keyword_names(extract_resume_skills(resume_text or "")))
    missing_keywords = [keyword for keyword in job_keywords if keyword not in resume_keywords][:5]

    base_text = resume_text.strip()
    if not base_text:
        optimized_text = _seed_resume(job_keywords)
        suggestions = [
            "Created a targeted professional summary for the role.",
            "Added starter experience bullets so the resume is not blank.",
        ]
        if missing_keywords:
            suggestions.append(f"Prioritized ATS keywords: {', '.join(missing_keywords[:3])}.")
        return {
            "optimized_text": optimized_text,
            "job_description": job_description,
            "suggestions": suggestions,
            "highlighted_keywords": missing_keywords,
        }

    original_lines = [line.rstrip() for line in base_text.splitlines()]
    optimized_lines: List[str] = []
    keyword_cursor = 0
    rewritten_lines = 0

    for line in original_lines:
        stripped = line.strip()
        if not stripped:
            optimized_lines.append("")
            continue
        if stripped.lower() == "professional summary" and job_keywords:
            optimized_lines.append(stripped)
            optimized_lines.append(_compose_summary(job_keywords))
            continue
        if _is_section_heading(stripped) or _should_preserve_line(stripped):
            optimized_lines.append(stripped)
            continue

        updated_line = stripped
        if _is_bullet(stripped):
            marker, bullet = _split_bullet(stripped)
            updated_bullet, keyword_cursor = _enrich_bullet(bullet, missing_keywords, keyword_cursor)
            updated_line = f"{marker} {updated_bullet}"
            rewritten_lines += 1
        elif rewritten_lines < 2:
            updated_line = _add_impact(updated_line)
            rewritten_lines += 1
        optimized_lines.append(updated_line)

    optimized_text = "\n".join(optimized_lines).strip()

    suggestions = [
        "Added a role-alignment summary to mirror the target job language.",
        "Strengthened top resume lines with clearer impact-oriented phrasing.",
    ]
    if missing_keywords:
        suggestions.append(f"Introduced missing ATS terms: {', '.join(missing_keywords[:3])}.")
    else:
        suggestions.append("Your resume already overlaps with most extracted ATS keywords.")

    return {
        "optimized_text": optimized_text,
        "job_description": job_description,
        "suggestions": suggestions,
        "highlighted_keywords": missing_keywords,
    }
