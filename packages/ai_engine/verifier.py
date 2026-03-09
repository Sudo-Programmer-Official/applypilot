"""Verification rules for candidate resume changes."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from packages.ai_engine.rules import (
    HIGH_IMPACT_METRIC_CATEGORIES,
    bullet_strength_score,
    detect_lost_metric_signals,
    metric_count,
    summary_score,
    technical_signal_count,
)
from packages.job_intelligence.extractor import extract_resume_skills, extract_resume_skills_from_document, keyword_names
from packages.resume_formatter import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument


def verify_change(
    original_document: ResumeDocument,
    current_document: ResumeDocument,
    candidate_document: ResumeDocument,
    applied_change: Dict[str, Any],
    job_skills: List[Dict[str, Any]],
) -> Dict[str, Any]:
    checks = {
        "truthfulness": True,
        "jd_relevance": True,
        "unsupported_technology_injection": True,
        "summary_weakening": True,
        "metric_preservation": True,
        "first_bullet_preservation": True,
    }
    reasons: List[str] = []
    codes: List[str] = []

    before_text = resume_document_to_text(current_document)
    after_text = resume_document_to_text(candidate_document)
    allowed_terms = list(applied_change.get("allowed_terms") or [])
    if applied_change.get("value"):
        allowed_terms.append(str(applied_change["value"]))

    unsupported = detect_unsupported_keyword_additions(original_document, before_text, after_text, allowed_terms=allowed_terms)
    if unsupported:
        checks["truthfulness"] = False
        checks["unsupported_technology_injection"] = False
        reasons.append(f"Introduced unsupported technology keywords: {', '.join(unsupported)}.")

    action = applied_change.get("action")
    job_skill_names = {name.lower() for name in keyword_names(job_skills)}

    if action == "rewrite_summary":
        before_value = str(applied_change.get("before_value") or "")
        after_value = str(applied_change.get("after_value") or "")
        lost_metrics = _high_impact_metric_loss(before_value, after_value)
        if lost_metrics:
            checks["truthfulness"] = False
            checks["metric_preservation"] = False
            codes.append("high_impact_metric_removed")
            reasons.append(
                f"Rejected because it removed high-impact metrics: {', '.join(signal['label'] for signal in lost_metrics)}."
            )
        if summary_score(after_value) < summary_score(before_value):
            checks["summary_weakening"] = False
            reasons.append("Summary rewrite weakened technical or scale signals from the original.")
        before_match = _keyword_overlap(before_value, job_skill_names)
        after_match = _keyword_overlap(after_value, job_skill_names)
        if job_skill_names and after_match < before_match:
            checks["jd_relevance"] = False
            reasons.append("Summary rewrite reduced job-relevant keyword coverage.")

    if action in {"add_skill", "add_derived_skill"}:
        if not applied_change.get("evidence"):
            checks["truthfulness"] = False
            reasons.append("Skill addition lacks resume-backed evidence.")
        if not applied_change.get("job_relevant"):
            checks["jd_relevance"] = False
            reasons.append("Skill addition is not tied back to the job description.")

    if action in {"rewrite_experience_bullet", "manual_edit_experience_bullet"}:
        before_value = str(applied_change.get("before_value") or "")
        after_value = str(applied_change.get("after_value") or "")
        bullet_index = int(applied_change.get("target", {}).get("bullet_index", -1))
        lost_metrics = _high_impact_metric_loss(before_value, after_value)
        if lost_metrics:
            checks["truthfulness"] = False
            checks["metric_preservation"] = False
            codes.append("high_impact_metric_removed")
            reasons.append(
                f"Rejected because it removed high-impact metrics: {', '.join(signal['label'] for signal in lost_metrics)}."
            )
        if metric_count(after_value) < metric_count(before_value):
            checks["truthfulness"] = False
            reasons.append("Bullet rewrite removed measurable evidence from the original.")
        if technical_signal_count(after_value) + metric_count(after_value) < technical_signal_count(before_value) + metric_count(before_value):
            checks["jd_relevance"] = False
            reasons.append("Bullet rewrite reduced technical specificity without adding stronger relevant signals.")
        if bullet_index == 0 and bullet_strength_score(after_value) < bullet_strength_score(before_value):
            checks["first_bullet_preservation"] = False
            checks["jd_relevance"] = False
            codes.append("first_bullet_weakened")
            reasons.append("Rejected because it weakened the first bullet of the role.")

    passed = all(checks.values())
    if passed and not reasons:
        reasons.append("Passed truthfulness, relevance, and weakening checks.")

    return {
        "passed": passed,
        "checks": checks,
        "reasons": reasons,
        "codes": codes,
    }


def detect_unsupported_keyword_additions(
    original_document: ResumeDocument,
    before_text: str,
    after_text: str,
    allowed_terms: Iterable[str] | None = None,
) -> List[str]:
    before_keywords = {name.lower(): name for name in keyword_names(extract_resume_skills(before_text))}
    after_keywords = {name.lower(): name for name in keyword_names(extract_resume_skills(after_text))}
    original_keywords = {name.lower() for name in keyword_names(extract_resume_skills_from_document(original_document.model_dump()))}
    allowed = {term.lower() for term in (allowed_terms or [])}

    unsupported = []
    for key, value in after_keywords.items():
        if key in before_keywords or key in original_keywords or key in allowed:
            continue
        unsupported.append(value)
    return sorted(unsupported)


def _keyword_overlap(text: str, job_skill_names: set[str]) -> int:
    lowered = (text or "").lower()
    return sum(1 for skill in job_skill_names if skill in lowered)


def _high_impact_metric_loss(before_text: str, after_text: str) -> List[Dict[str, Any]]:
    return [
        signal
        for signal in detect_lost_metric_signals(before_text, after_text)
        if signal["category"] in HIGH_IMPACT_METRIC_CATEGORIES
    ]
