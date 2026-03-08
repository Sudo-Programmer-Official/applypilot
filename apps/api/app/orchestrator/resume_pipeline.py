"""
Orchestrates the end-to-end resume optimization flow.

This is a lightweight placeholder that wires together the parsing, analysis,
optimization, diffing, and ATS scoring steps. Real logic will be added in later
phases.
"""
import logging
from typing import Any, Dict, Optional

from packages.ats_score.scorer import calculate_ats_score
from packages.ai_engine.optimizer import optimize_resume
from packages.diff_engine.diff_engine import generate_diff
from packages.keyword_engine.extractor import extract_keywords
from packages.resume_parser.parser import parse_resume
from packages.shared_types.pipeline_result import PipelineResult

logger = logging.getLogger(__name__)


def analyze_resume(parsed_resume: Dict[str, Any], job_description: Optional[str]) -> Dict[str, Any]:
    """
    Placeholder analysis step.

    Future implementation will extract keywords, measure alignment, and
    generate actionable insights.
    """
    resume_text = parsed_resume.get("text", "")
    job_keywords = extract_keywords(job_description or "")[:12]
    resume_keywords = set(extract_keywords(resume_text))
    matched_keywords = [keyword for keyword in job_keywords if keyword in resume_keywords]
    missing_keywords = [keyword for keyword in job_keywords if keyword not in resume_keywords]

    return {
        "summary": (
            f"Resume currently matches {len(matched_keywords)} of {len(job_keywords)} "
            "keywords extracted from the job description."
            if job_keywords
            else "Paste a job description to generate alignment insights."
        ),
        "keywords": {
            "job": job_keywords,
            "matched": matched_keywords,
            "missing": missing_keywords,
        },
        "job_alignment": {
            "job_description_provided": bool(job_description),
            "matched_count": len(matched_keywords),
            "missing_count": len(missing_keywords),
        },
    }


def run_resume_pipeline(resume_path: str, job_description: Optional[str] = None) -> PipelineResult:
    """
    Execute the resume optimization pipeline and return structured results.

    Args:
        resume_path: Filesystem path to the resume input.
        job_description: Optional job description text for alignment.
    """
    logger.info("Running resume pipeline for path=%s", resume_path)
    parsed = parse_resume(resume_path)
    original_text = parsed.get("text", "")

    analysis = analyze_resume(parsed, job_description)
    optimized = optimize_resume(original_text, job_description or "")
    optimized_text = optimized.get("optimized_text", original_text)

    diff_text = generate_diff(original_text, optimized_text)
    current_ats = calculate_ats_score(original_text, job_description or "")
    projected_ats = calculate_ats_score(optimized_text, job_description or "")
    ats = {
        **current_ats,
        "projected_score": projected_ats.get("score", current_ats.get("score", 0)),
        "projected_matched_keywords": projected_ats.get("matched_keywords", []),
        "projected_missing_keywords": projected_ats.get("missing_keywords", []),
    }

    logger.info(
        "Resume pipeline completed chars=%s matched_keywords=%s",
        len(original_text),
        len(ats.get("matched_keywords", [])),
    )

    return PipelineResult(
        parsed=parsed,
        analysis=analysis,
        optimized={
            "text": optimized_text,
            "metadata": optimized,
        },
        diff={"unified": diff_text},
        ats_score=ats,
    )
