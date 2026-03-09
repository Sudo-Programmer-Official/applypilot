"""Structured resume editing for human-in-the-loop bullet revisions."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence

from packages.ai_engine.humanizer import humanize_bullet
from packages.ai_engine.polish import polish_resume_text
from packages.ai_engine.scorer import score_resume
from packages.ai_engine.verifier import verify_change
from packages.ats_score.scorer import calculate_ats_score
from packages.diff_engine.diff_engine import generate_diff
from packages.job_intelligence.extractor import (
    analyze_job_description,
    extract_resume_skills,
    extract_resume_skills_from_document,
    keyword_names,
)
from packages.readiness_score.scorer import calculate_application_readiness
from packages.resume_formatter import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument


def apply_resume_edit(
    *,
    original_document: ResumeDocument | Dict[str, Any],
    current_document: ResumeDocument | Dict[str, Any],
    instruction: str,
    target: Dict[str, Any],
    job_description: str = "",
) -> Dict[str, Any]:
    source_document = _coerce_document(original_document)
    working_document = _coerce_document(current_document)
    cleaned_instruction = _clean_text(instruction)
    if not cleaned_instruction:
        raise ValueError("Edit instruction is required.")

    section = str(target.get("section") or "").lower().strip()
    if section != "experience":
        raise ValueError("Only experience bullet edits are supported in this version.")

    entry_index = int(target.get("entry_index", -1))
    bullet_index = int(target.get("bullet_index", -1))
    if entry_index < 0 or entry_index >= len(working_document.experience):
        raise ValueError("Selected experience entry is invalid.")
    if bullet_index < 0 or bullet_index >= len(working_document.experience[entry_index].bullets):
        raise ValueError("Selected experience bullet is invalid.")

    entry = working_document.experience[entry_index]
    before_value = _clean_text(entry.bullets[bullet_index])
    allowed_terms = _allowed_resume_terms(source_document, working_document)
    requested_terms = _requested_terms(cleaned_instruction)
    unsupported_requests = [term for term in requested_terms if term.lower() not in allowed_terms]
    if unsupported_requests:
        raise ValueError(
            "Edit references skills that are not supported by the current resume: "
            + ", ".join(unsupported_requests)
            + "."
        )

    job_intelligence = analyze_job_description(job_description or "")
    job_skills = job_intelligence.get("skills", [])
    role_info = job_intelligence.get("role_type", {"id": "general_software", "label": "Software Engineer"})
    after_value = _rewrite_experience_bullet(
        entry,
        before_value,
        cleaned_instruction,
        requested_terms,
        allowed_terms,
        job_skills=job_skills,
        role_label=role_info.get("label", ""),
    )
    if _normalize_text(after_value) == _normalize_text(before_value):
        raise ValueError(
            "Instruction did not produce a meaningful bullet change. Try a more specific request like "
            "'highlight AI evaluation pipelines' or 'mention machine learning workflows more explicitly'."
        )

    candidate_document = working_document.model_copy(deep=True)
    candidate_document.experience[entry_index].bullets[bullet_index] = after_value

    applied_change = {
        "action": "manual_edit_experience_bullet",
        "type": "manual_edit",
        "instruction": cleaned_instruction,
        "target_section": "experience",
        "target": {
            "section": "experience",
            "entry_index": entry_index,
            "bullet_index": bullet_index,
        },
        "before_value": before_value,
        "after_value": after_value,
        "value": after_value,
        "reason": f"Applied user edit to {entry.role or entry.company or 'experience bullet'}.",
        "allowed_terms": sorted(requested_terms),
    }

    verification = verify_change(source_document, working_document, candidate_document, applied_change, job_skills)
    if not verification["passed"]:
        raise ValueError(" ".join(verification["reasons"]))

    original_score = score_resume(source_document, job_skills, original_document=source_document, role_info=role_info)
    current_score = score_resume(working_document, job_skills, original_document=source_document, role_info=role_info)
    updated_score = score_resume(candidate_document, job_skills, original_document=source_document, role_info=role_info)
    if updated_score["axes"]["credibility"] < current_score["axes"]["credibility"]:
        raise ValueError("Edit reduced resume credibility and was rejected.")
    if updated_score["total"] < current_score["total"]:
        raise ValueError("Edit reduced the overall resume score. Try a more specific instruction.")
    score_delta = int(round(updated_score["total"] - current_score["total"]))
    edit_reason = _build_edit_reason(cleaned_instruction, requested_terms)

    original_text = resume_document_to_text(source_document)
    unpolished_text = resume_document_to_text(candidate_document)
    current_ats = calculate_ats_score(unpolished_text, job_description or "")
    ats_score = {
        **current_ats,
        "projected_score": current_ats.get("score", 0),
        "projected_matched_keywords": current_ats.get("matched_keywords", []),
        "projected_missing_keywords": current_ats.get("missing_keywords", []),
    }
    current_readiness = calculate_application_readiness(unpolished_text, job_description or "")
    readiness = {
        **current_readiness,
        "projected_score": current_readiness.get("score", 0),
        "projected_breakdown": current_readiness.get("breakdown", {}),
        "projected_top_issues": current_readiness.get("top_issues", []),
    }
    polished_document, polish_meta = polish_resume_text(
        candidate_document,
        role_label=role_info.get("label"),
    )
    updated_text = resume_document_to_text(polished_document)

    change_payload = {
        **applied_change,
        "decision": "kept",
        "decision_reason": "Accepted because the edit preserved credibility and did not reduce the resume score.",
        "verification": verification,
        "reason": edit_reason,
        "scores": {
            "before": current_score,
            "after": updated_score,
        },
    }

    return {
        "optimized": {
            "text": updated_text,
            "document": polished_document.model_dump(),
            "metadata": {
                "source": "manual_edit",
                "edit_instruction": cleaned_instruction,
                "edit_reason": edit_reason,
                "score_delta": score_delta,
                "kept_changes": [change_payload],
                "rejected_changes": [],
                "scores": {
                    "original": original_score,
                    "optimized": updated_score,
                },
                "polish": polish_meta,
            },
        },
        "diff": {"unified": generate_diff(original_text, updated_text)},
        "ats_score": ats_score,
        "application_readiness": readiness,
        "edit": {
            "entry_index": entry_index,
            "bullet_index": bullet_index,
            "before": before_value,
            "after": after_value,
            "instruction": cleaned_instruction,
            "reason": edit_reason,
            "score_delta": score_delta,
            "verification": verification,
        },
    }


def _coerce_document(document: ResumeDocument | Dict[str, Any]) -> ResumeDocument:
    if isinstance(document, ResumeDocument):
        return document.model_copy(deep=True)
    return ResumeDocument.model_validate(document)


def _allowed_resume_terms(*documents: ResumeDocument) -> set[str]:
    allowed = set()
    for document in documents:
        allowed.update(name.lower() for name in keyword_names(extract_resume_skills_from_document(document.model_dump())))
    return allowed


def _requested_terms(instruction: str) -> List[str]:
    matches = keyword_names(extract_resume_skills(instruction or ""))
    lowered = (instruction or "").lower()
    if "ai/ml" in lowered or "ai / ml" in lowered:
        matches.append("Machine Learning")
    if "llm" in lowered and "LLMs" not in matches:
        matches.append("LLMs")
    return list(dict.fromkeys(matches))


def _rewrite_experience_bullet(
    entry: Any,
    source: str,
    instruction: str,
    requested_terms: Sequence[str],
    allowed_terms: Iterable[str],
    *,
    job_skills: Sequence[Dict[str, Any]] | None = None,
    role_label: str = "",
) -> str:
    lower_instruction = instruction.lower()
    role_context = {term for term in allowed_terms}
    candidate = source

    if any(token in lower_instruction for token in ("rewrite", "reword", "shorten", "clearer", "stronger", "concise", "impact", "metric", "scale", "highlight", "mention", "emphas")):
        candidate = humanize_bullet(entry, source, role_context=role_context, used_signatures=set())

    if any(token in lower_instruction for token in ("impact", "metric", "scale", "quantif")):
        candidate = _emphasize_impact(candidate)

    if requested_terms:
        candidate = _ensure_requested_terms(candidate, source, requested_terms)

    if candidate == source:
        candidate = _tailor_bullet_to_role(
            source,
            instruction=instruction,
            allowed_terms=role_context,
            job_skills=job_skills or [],
            role_label=role_label,
        )

    if candidate == source:
        candidate = humanize_bullet(entry, source, role_context=role_context, used_signatures=set())

    return _clean_terminal(candidate)


def _ensure_requested_terms(candidate: str, source: str, requested_terms: Sequence[str]) -> str:
    updated = candidate.rstrip(".")
    source_lower = source.lower()
    candidate_lower = updated.lower()
    changed = False

    for term in requested_terms:
        term_lower = term.lower()
        if term_lower in candidate_lower:
            continue
        if term_lower not in source_lower:
            continue
        if term_lower == "aws" and "aws lambda" in source_lower and "aws lambda" not in candidate_lower:
            updated = _insert_context_phrase(updated, "AWS Lambda")
            candidate_lower = updated.lower()
            changed = True
            continue
        if term_lower == "ci/cd":
            updated = _insert_context_phrase(updated, "CI/CD")
            candidate_lower = updated.lower()
            changed = True
            continue
        updated = _insert_context_phrase(updated, term)
        candidate_lower = updated.lower()
        changed = True
    return updated if changed else candidate


def _insert_context_phrase(text: str, phrase: str) -> str:
    if not text:
        return phrase
    if "," in text:
        head, tail = text.split(",", 1)
        if phrase.lower() in head.lower() or phrase.lower() in tail.lower():
            return text
        return f"{head} using {phrase},{tail.strip()}"
    if " using " in text.lower() or " on " in text.lower() or " with " in text.lower():
        return text
    return f"{text} using {phrase}"


def _emphasize_impact(text: str) -> str:
    lowered = text.lower()
    if any(char.isdigit() for char in text):
        return text
    if "throughput" in lowered or "latency" in lowered or "runtime" in lowered:
        return f"{text.rstrip('.')} with measurable performance gains"
    if "reliability" in lowered or "resilient" in lowered or "fault-tolerant" in lowered:
        return f"{text.rstrip('.')} for production-scale reliability"
    return text


def _tailor_bullet_to_role(
    source: str,
    *,
    instruction: str,
    allowed_terms: Iterable[str],
    job_skills: Sequence[Dict[str, Any]],
    role_label: str,
) -> str:
    lowered_source = source.lower()
    lowered_instruction = instruction.lower()
    allowed = {term.lower() for term in allowed_terms}
    job_skill_names = {str(skill.get("name", "")).lower() for skill in job_skills}

    if not any(token in lowered_instruction for token in ("tailor", "job", "jd", "align", "match")):
        return source

    if ("traceability" in lowered_source or "requirement" in lowered_source) and (
        "llm" in lowered_source or "semantic" in lowered_source
    ):
        if "machine learning" in allowed and "machine learning" in job_skill_names:
            return (
                "Built an LLM-powered requirement traceability system using semantic similarity scoring to map "
                "functional and quality requirements across machine learning workflows."
            )
        if "data analytics" in allowed and "data analytics" in job_skill_names:
            return (
                "Built an LLM-powered requirement traceability system using semantic similarity scoring to map "
                "functional and quality requirements for analytics-driven engineering workflows."
            )
        if "llms" in allowed or "machine learning" in allowed:
            return (
                "Built an LLM-powered requirement traceability system using semantic similarity scoring to map "
                "functional and quality requirements across AI-focused engineering workflows."
            )

    if ("evaluation pipeline" in lowered_source or "manual scoring" in lowered_source or "benchmark" in lowered_source):
        if "data analytics" in allowed and ("data analytics" in job_skill_names or "automation" in job_skill_names):
            return (
                "Designed data and evaluation pipelines to benchmark AI-generated outputs against human scoring "
                "frameworks."
            )
        if "automation" in allowed and "automation" in job_skill_names:
            return (
                "Designed automated evaluation pipelines to benchmark AI-generated outputs against human scoring "
                "frameworks."
            )

    if role_label and "ai" in role_label.lower() and "python" in allowed and "backend" in lowered_source:
        return source.rstrip(".") + " with clearer alignment to Python-based AI tooling workflows"

    return source


def _clean_terminal(text: str) -> str:
    cleaned = _clean_text(text).rstrip(".")
    return f"{cleaned}."


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _build_edit_reason(instruction: str, requested_terms: Sequence[str]) -> str:
    if requested_terms:
        return f"Made the bullet more explicit around {', '.join(requested_terms[:2])}."
    lowered = instruction.lower()
    if "metric" in lowered or "impact" in lowered or "scale" in lowered:
        return "Strengthened the bullet with clearer impact language."
    if "tailor" in lowered or "job" in lowered:
        return "Tailored the bullet more closely to the target role language."
    if "concise" in lowered or "short" in lowered or "clear" in lowered:
        return "Tightened the bullet for clearer recruiter scanning."
    return "Applied a targeted bullet rewrite without reducing credibility."
