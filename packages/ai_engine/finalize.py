"""Build diagnostics from the final polished resume document.

The finalized structured document is the source of truth for preview and export,
so ATS/readiness/recruiter-facing scores must be recomputed from that exact
document before the UI renders or the PDF is generated.
"""
from __future__ import annotations

from typing import Any, Dict, List

from packages.ai_engine.scorer import score_resume
from packages.ats_score.scorer import calculate_ats_score
from packages.readiness_score.scorer import calculate_application_readiness
from packages.resume_formatter import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument


def build_output_diagnostics(
    *,
    original_text: str,
    final_document: ResumeDocument,
    job_description: str = "",
    original_document: ResumeDocument | None = None,
    job_skills: List[Dict[str, Any]] | None = None,
    role_info: Dict[str, str] | None = None,
    original_score: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Recompute ATS/readiness metrics from the final polished document."""
    final_text = resume_document_to_text(final_document)
    current_ats = calculate_ats_score(original_text, job_description or "")
    projected_ats = calculate_ats_score(final_text, job_description or "")
    current_readiness = calculate_application_readiness(original_text, job_description or "")
    projected_readiness = calculate_application_readiness(final_text, job_description or "")

    diagnostics: Dict[str, Any] = {
        "text": final_text,
        "ats_score": {
            **current_ats,
            "projected_score": projected_ats.get("score", current_ats.get("score", 0)),
            "projected_matched_keywords": projected_ats.get("matched_keywords", []),
            "projected_missing_keywords": projected_ats.get("missing_keywords", []),
        },
        "application_readiness": {
            **current_readiness,
            "projected_score": projected_readiness.get("score", current_readiness.get("score", 0)),
            "projected_breakdown": projected_readiness.get("breakdown", {}),
            "projected_top_issues": projected_readiness.get("top_issues", []),
        },
    }

    if original_document is not None and job_skills is not None:
        baseline_score = original_score or score_resume(
            original_document,
            job_skills,
            original_document=original_document,
            role_info=role_info or {},
        )
        diagnostics["scores"] = {
            "original": baseline_score,
            "optimized": score_resume(
                final_document,
                job_skills,
                original_document=original_document,
                role_info=role_info or {},
            ),
        }

    return diagnostics
