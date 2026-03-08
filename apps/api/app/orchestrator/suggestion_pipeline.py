"""Apply external improvement suggestions to a parsed resume."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from packages.diff_engine.diff_engine import generate_diff
from packages.job_intelligence.extractor import extract_resume_skills, extract_resume_skills_from_document
from packages.readiness_score.scorer import calculate_application_readiness
from packages.resume_formatter import build_resume_document, resume_document_to_text
from packages.resume_parser.parser import parse_resume
from packages.shared_types.pipeline_result import PipelineResult
from packages.shared_types.resume_document import ResumeDocument
from packages.suggestion_engine import apply_suggestions_to_document

logger = logging.getLogger(__name__)


def apply_suggestion_pipeline(
    resume_path: str,
    suggestions_text: str,
    parsed_resume: Dict[str, Any] | None = None,
) -> PipelineResult:
    logger.info("Running suggestion pipeline for path=%s", resume_path)
    parsed = parsed_resume or parse_resume(resume_path)
    original_text = parsed.get("text", "")
    original_document = (
        ResumeDocument(**parsed["document"])
        if parsed.get("document")
        else build_resume_document(original_text)
    )

    suggestion_result = apply_suggestions_to_document(original_document, suggestions_text)
    updated_document = suggestion_result["document"]
    updated_text = resume_document_to_text(updated_document)

    current_readiness = calculate_application_readiness(original_text, "")
    projected_readiness = calculate_application_readiness(updated_text, "")
    updated_resume_skills = extract_resume_skills_from_document(updated_document.model_dump()) or extract_resume_skills(updated_text)
    top_skills = updated_resume_skills[:8]
    requested_skills = suggestion_result.get("requested_skills", [])
    remaining_skills = suggestion_result.get("remaining_skills", [])
    updated_skill_names = {skill["name"] for skill in updated_resume_skills}
    matched_requested = [skill for skill in requested_skills if skill["name"] in updated_skill_names]
    role_label = updated_document.title.split("|", 1)[0].strip() if updated_document.title else "Software Engineer"

    summary = _build_summary(suggestion_result.get("applied_changes", []), suggestion_result.get("unresolved_suggestions", []))

    readiness = {
        **current_readiness,
        "projected_score": projected_readiness.get("score", current_readiness.get("score", 0)),
        "projected_breakdown": projected_readiness.get("breakdown", {}),
        "projected_top_issues": projected_readiness.get("top_issues", []),
    }

    ats_proxy = {
        "score": current_readiness.get("score", 0),
        "projected_score": projected_readiness.get("score", current_readiness.get("score", 0)),
        "matched_keywords": [skill["name"] for skill in matched_requested],
        "missing_keywords": [skill["name"] for skill in remaining_skills],
        "notes": ["Resume quality proxy used because no job description was provided."],
    }

    return PipelineResult(
        parsed=parsed,
        analysis={
            "mode": "suggestions",
            "summary": summary,
            "role_type": {"id": "resume_improvement", "label": role_label},
            "top_skills": top_skills,
            "matched_skills": matched_requested,
            "missing_skills": remaining_skills,
            "suggested_changes": suggestion_result.get("applied_changes", []),
            "applied_changes": suggestion_result.get("applied_changes", []),
            "unresolved_suggestions": suggestion_result.get("unresolved_suggestions", []),
        },
        optimized={
            "text": updated_text,
            "document": updated_document.model_dump(),
            "metadata": {
                "source": "external_suggestions",
                "suggestions": suggestion_result.get("applied_changes", []),
            },
        },
        diff={"unified": generate_diff(original_text, updated_text)},
        ats_score=ats_proxy,
        application_readiness=readiness,
    )


def _build_summary(applied_changes: List[str], unresolved_suggestions: List[str]) -> str:
    applied_count = len(applied_changes)
    unresolved_count = len(unresolved_suggestions)
    if applied_count == 0:
        return "Parsed the resume and preserved formatting, but no suggestions could be mapped automatically."
    if unresolved_count == 0:
        return f"Applied {applied_count} requested changes and preserved the ATS-safe resume layout."
    return f"Applied {applied_count} requested changes and left {unresolved_count} suggestion(s) for manual review."
