"""
Orchestrates the end-to-end resume optimization flow.

This is a lightweight placeholder that wires together the parsing, analysis,
optimization, diffing, and ATS scoring steps. Real logic will be added in later
phases.
"""
import logging
from typing import Any, Dict, Optional

from packages.ai_engine.optimizer import optimize_resume
from packages.ats_score.scorer import calculate_ats_score
from packages.diff_engine.diff_engine import generate_diff
from packages.job_intelligence.extractor import analyze_job_description, extract_resume_skills, keyword_names
from packages.readiness_score.scorer import calculate_application_readiness
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
    job_intelligence = analyze_job_description(job_description or "")
    job_skills = job_intelligence.get("skills", [])
    role_type = job_intelligence.get("role_type", {"id": "general_software", "label": "Software Engineer"})
    resume_skill_names = set(keyword_names(extract_resume_skills(resume_text)))

    matched_skills = [skill for skill in job_skills if skill["name"] in resume_skill_names]
    missing_skills = [skill for skill in job_skills if skill["name"] not in resume_skill_names]
    suggested_changes = [
        f"Add {skill['name']} in {', '.join(skill['suggested_sections'][:2])}."
        for skill in missing_skills[:3]
    ]
    if resume_text and not any(char.isdigit() for char in resume_text):
        suggested_changes.append("Quantify impact in your recent experience bullets.")
    if role_type["label"]:
        suggested_changes.append(f"Align the summary with {role_type['label']} language from the job description.")

    return {
        "summary": (
            f"Detected {role_type['label']} role. Resume matches {len(matched_skills)} of "
            f"{len(job_skills)} high-signal skills."
            if job_skills
            else "Paste a job description to generate alignment insights."
        ),
        "role_type": role_type,
        "top_skills": job_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "suggested_changes": suggested_changes,
        "keywords": {
            "job": keyword_names(job_skills),
            "matched": keyword_names(matched_skills),
            "missing": keyword_names(missing_skills),
        },
        "job_alignment": {
            "job_description_provided": bool(job_description),
            "matched_count": len(matched_skills),
            "missing_count": len(missing_skills),
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
    current_readiness = calculate_application_readiness(original_text, job_description or "")
    projected_readiness = calculate_application_readiness(optimized_text, job_description or "")
    readiness = {
        **current_readiness,
        "projected_score": projected_readiness.get("score", current_readiness.get("score", 0)),
        "projected_breakdown": projected_readiness.get("breakdown", {}),
        "projected_top_issues": projected_readiness.get("top_issues", []),
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
        application_readiness=readiness,
    )
