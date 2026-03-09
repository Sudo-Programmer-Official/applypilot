"""Deterministic ATS fix engine for missing resume signals.

This module is the verified fix pass for an already optimized draft. It keeps
scope intentionally narrow: keyword injection, contextual bullet enhancement,
and skill expansion. Recommendation-only behaviors such as project renaming or
header rewriting belong in a separate future layer.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from packages.ai_engine.finalize import build_output_diagnostics
from packages.ai_engine.polish import polish_resume_text
from packages.ai_engine.rules import clean_terminal, dedupe, pick_skill_category
from packages.ai_engine.scorer import score_resume
from packages.ai_engine.verifier import verify_change
from packages.ats_score.scorer import calculate_ats_score
from packages.diff_engine.diff_engine import generate_diff
from packages.job_intelligence.extractor import (
    analyze_job_description,
    extract_resume_skills_from_document,
    keyword_names,
)
from packages.resume_formatter import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument

_KEYWORD_INJECTION_RULES = {
    "machine learning": {
        "evidence": ("llm", "semantic similarity", "embedding", "nlp", "retrieval", "language model"),
        "phrase": "using machine learning techniques and semantic similarity models",
        "log": "Machine Learning added.",
    },
    "ai systems": {
        "evidence": ("llm", "semantic similarity", "embedding", "evaluation", "agentic", "ai"),
        "phrase": "for AI systems evaluation and semantic similarity workflows",
        "log": "AI Systems surfaced in AI workflow experience.",
    },
    "prompt engineering": {
        "evidence": ("llm", "prompt", "semantic similarity", "evaluation"),
        "phrase": "and prompt-driven evaluation pipelines",
        "log": "Prompt Engineering surfaced in AI workflow experience.",
    },
    "evaluation pipelines": {
        "evidence": ("llm", "evaluation", "benchmark", "semantic similarity"),
        "phrase": "and prompt-driven evaluation pipelines",
        "log": "Evaluation Pipelines surfaced in AI workflow experience.",
    },
    "semantic retrieval": {
        "evidence": ("semantic similarity", "embedding", "retrieval", "llm"),
        "phrase": "with semantic retrieval workflows",
        "log": "Semantic Retrieval surfaced in AI workflow experience.",
    },
}

_SKILL_EXPANSION_RULES = {
    "fastapi": {
        "required_all": ("python",),
        "required_any": ("api", "apis", "backend", "microservices", "rest"),
        "category": "framework",
        "log": "FastAPI surfaced in backend stack.",
    },
    "django": {
        "required_all": ("python",),
        "required_any": ("api", "apis", "backend", "service", "services", "rest"),
        "category": "framework",
        "log": "Django surfaced in backend stack.",
    },
    "nosql": {
        "required_all": (),
        "required_any": ("mongodb", "dynamodb", "document db", "document database", "document store"),
        "category": "database",
        "log": "NoSQL surfaced in data stack.",
    },
    "bash": {
        "required_all": (),
        "required_any": ("ci/cd", "deployment", "automation", "script", "scripts", "shell"),
        "category": "tool",
        "log": "Bash surfaced in deployment automation.",
    },
    "prompt engineering": {
        "required_all": (),
        "required_any": ("llm", "prompt", "semantic similarity", "evaluation"),
        "category": "ml",
        "log": "Prompt Engineering surfaced in AI / LLM systems.",
    },
    "evaluation pipelines": {
        "required_all": (),
        "required_any": ("llm", "evaluation", "benchmark", "semantic similarity"),
        "category": "ml",
        "log": "Evaluation Pipelines surfaced in AI / LLM systems.",
    },
    "semantic retrieval": {
        "required_all": (),
        "required_any": ("semantic similarity", "embedding", "retrieval", "llm"),
        "category": "ml",
        "log": "Semantic Retrieval surfaced in AI / LLM systems.",
    },
    "unix": {
        "required_all": (),
        "required_any": ("bash", "shell", "linux", "ci/cd", "deployment"),
        "category": "tool",
        "log": "Unix surfaced in tooling stack.",
    },
}

_BULLET_ENHANCEMENT_RULES = {
    "bash": {
        "evidence": ("ci/cd", "deployment", "release", "automation", "pipeline", "pipelines", "script"),
        "phrase": "and Bash-based deployment scripts",
        "log": "Bash surfaced in deployment automation.",
    },
    "distributed systems": {
        "evidence": ("distributed", "backend", "microservices", "workers", "orchestration", "concurrency"),
        "phrase": "for distributed systems reliability",
        "log": "Distributed Systems surfaced in backend ownership.",
    },
    "automation": {
        "evidence": ("automation", "workflow", "workflows", "pipeline", "pipelines", "script", "scripts"),
        "phrase": "across automation pipelines",
        "log": "Automation surfaced in delivery workflow context.",
    },
    "data pipelines": {
        "evidence": ("pipeline", "pipelines", "etl", "batch", "streaming", "orchestration"),
        "phrase": "across data pipeline orchestration",
        "log": "Data Pipelines surfaced in implementation context.",
    },
}

_METRIC_CLAUSE_PATTERN = re.compile(
    r",\s*(reducing|improving|increasing|decreasing|cutting|saving|delivering|supporting)\b",
    re.IGNORECASE,
)


def apply_resume_fixes(
    *,
    original_document: ResumeDocument | Dict[str, Any],
    current_document: ResumeDocument | Dict[str, Any],
    job_description: str,
    analysis: Dict[str, Any] | None = None,
    missing_signals: Sequence[str] | None = None,
) -> Dict[str, Any]:
    source_document = _coerce_document(original_document)
    working_document = _coerce_document(current_document)
    original_text = resume_document_to_text(source_document)
    current_text = resume_document_to_text(working_document)

    job_intelligence = analyze_job_description(job_description or "", limit=10)
    job_skills = job_intelligence.get("skills", [])
    role_info = job_intelligence.get("role_type", {"id": "general_software", "label": "Software Engineer"})

    if not job_skills:
        diagnostics = build_output_diagnostics(
            original_text=original_text,
            final_document=working_document,
            job_description=job_description or "",
            original_document=source_document,
            job_skills=job_skills,
            role_info=role_info,
        )
        return {
            "optimized": {
                "text": diagnostics["text"],
                "document": working_document.model_dump(),
                "metadata": {
                    "source": "apply_fixes",
                    "applied_fixes": [],
                    "rejected_fixes": ["No high-signal job keywords were available for ATS fixes."],
                    "kept_changes": [],
                    "rejected_changes": [],
                    "scores": diagnostics.get("scores", {}),
                },
            },
            "analysis": {
                **(analysis or {}),
                "applied_changes": [],
                "summary": "No ATS fixes were applied because the job description did not produce reliable missing signals.",
            },
            "diff": {"unified": generate_diff(original_text, diagnostics["text"])},
            "ats_score": diagnostics["ats_score"],
            "application_readiness": diagnostics["application_readiness"],
            "fixes": {"applied": [], "rejected": ["No high-signal job keywords were available for ATS fixes."]},
        }

    missing_skill_names = _resolve_missing_signal_names(
        document=working_document,
        job_skills=job_skills,
        analysis=analysis or {},
        explicit_missing=missing_signals or [],
    )
    original_score = score_resume(source_document, job_skills, original_document=source_document, role_info=role_info)
    current_score = score_resume(working_document, job_skills, original_document=source_document, role_info=role_info)
    current_ats = int(calculate_ats_score(current_text, job_description or "").get("score", 0))

    kept_changes: List[Dict[str, Any]] = []
    rejected_changes: List[Dict[str, Any]] = []
    fix_log: List[str] = []
    used_targets: set[Tuple[str, int, int]] = set()

    for signal in missing_skill_names:
        candidate_applied = False
        for candidate in _build_fix_candidates(working_document, signal, used_targets):
            candidate_document = candidate["document"]
            change_payload = candidate["change"]
            verification = verify_change(source_document, working_document, candidate_document, change_payload, job_skills)
            score_before = current_score
            candidate_score = score_resume(
                candidate_document,
                job_skills,
                original_document=source_document,
                role_info=role_info,
            )
            candidate_ats = int(calculate_ats_score(resume_document_to_text(candidate_document), job_description or "").get("score", 0))
            rejection_reason = _candidate_rejection_reason(
                verification=verification,
                current_score=current_score,
                candidate_score=candidate_score,
                current_ats=current_ats,
                candidate_ats=candidate_ats,
            )
            if rejection_reason:
                rejected_changes.append(
                    {
                        **change_payload,
                        "decision": "rejected",
                        "decision_reason": rejection_reason,
                        "verification": verification,
                        "scores": {
                            "before": current_score,
                            "after": candidate_score,
                        },
                    }
                )
                continue

            working_document = candidate_document
            current_ats = candidate_ats
            kept_changes.append(
                {
                    **change_payload,
                    "decision": "kept",
                    "decision_reason": "Kept because it improved ATS alignment without weakening evidence.",
                    "verification": verification,
                    "scores": {
                        "before": score_before,
                        "after": candidate_score,
                    },
                }
            )
            current_score = candidate_score
            if candidate.get("used_target"):
                used_targets.add(candidate["used_target"])
            fix_log.append(candidate["log"])
            candidate_applied = True
            break

        if not candidate_applied and not any(change.get("value") == signal for change in rejected_changes):
            rejected_changes.append(
                {
                    "action": "auto_fix",
                    "type": "auto_fix",
                    "value": signal,
                    "decision": "rejected",
                    "decision_reason": "No safe fix candidate was found from the current resume evidence.",
                }
            )

    polished_document, polish_meta = polish_resume_text(
        working_document,
        role_label=role_info.get("label"),
    )
    diagnostics = build_output_diagnostics(
        original_text=original_text,
        final_document=polished_document,
        job_description=job_description or "",
        original_document=source_document,
        job_skills=job_skills,
        role_info=role_info,
        original_score=original_score,
    )
    updated_text = diagnostics["text"]
    updated_skill_names = {
        name.lower()
        for name in keyword_names(extract_resume_skills_from_document(polished_document.model_dump()))
    }
    matched_skills = [skill for skill in job_skills if skill["name"].lower() in updated_skill_names]
    remaining_skills = [skill for skill in job_skills if skill["name"].lower() not in updated_skill_names]

    summary = (
        f"Applied {len(fix_log)} verified ATS fix{'es' if len(fix_log) != 1 else ''}."
        if fix_log
        else "No safe ATS fixes were applied. The current draft already preserved the strongest supported evidence."
    )

    return {
        "optimized": {
            "text": updated_text,
            "document": polished_document.model_dump(),
            "metadata": {
                "source": "apply_fixes",
                "applied_fixes": fix_log,
                "rejected_fixes": [change.get("decision_reason", "") for change in rejected_changes if change.get("decision_reason")],
                "kept_changes": kept_changes,
                "rejected_changes": rejected_changes,
                "scores": diagnostics.get("scores", {}),
                "polish": polish_meta,
            },
        },
        "analysis": {
            "mode": "analysis",
            "summary": summary,
            "role_type": role_info,
            "top_skills": job_skills,
            "matched_skills": matched_skills,
            "missing_skills": remaining_skills,
            "keywords": {
                "job": keyword_names(job_skills),
                "matched": keyword_names(matched_skills),
                "missing": keyword_names(remaining_skills),
            },
            "job_alignment": {
                "job_description_provided": bool(job_description),
                "matched_count": len(matched_skills),
                "missing_count": len(remaining_skills),
            },
            "applied_changes": fix_log,
            "suggested_changes": fix_log,
        },
        "diff": {"unified": generate_diff(original_text, updated_text)},
        "ats_score": diagnostics["ats_score"],
        "application_readiness": diagnostics["application_readiness"],
        "fixes": {
            "applied": fix_log,
            "rejected": [change.get("decision_reason", "") for change in rejected_changes if change.get("decision_reason")],
        },
    }


def _coerce_document(document: ResumeDocument | Dict[str, Any]) -> ResumeDocument:
    if isinstance(document, ResumeDocument):
        return document.model_copy(deep=True)
    return ResumeDocument.model_validate(document)


def _normalize_signal(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _resolve_missing_signal_names(
    *,
    document: ResumeDocument,
    job_skills: Sequence[Dict[str, Any]],
    analysis: Dict[str, Any],
    explicit_missing: Sequence[str],
) -> List[str]:
    current_skill_names = {
        name.lower()
        for name in keyword_names(extract_resume_skills_from_document(document.model_dump()))
    }

    requested_names = list(explicit_missing)
    if not requested_names:
        requested_names.extend(analysis.get("keywords", {}).get("missing", []))
        requested_names.extend(
            skill.get("name", "")
            for skill in analysis.get("missing_skills", [])
            if isinstance(skill, dict)
        )

    requested = {
        _normalize_signal(name)
        for name in requested_names
        if name
    }

    ordered = []
    for skill in job_skills:
        normalized = _normalize_signal(skill["name"])
        if normalized in requested or not requested:
            if skill["name"].lower() in current_skill_names:
                continue
            ordered.append(skill["name"])
    return ordered


def _build_fix_candidates(
    document: ResumeDocument,
    signal: str,
    used_targets: set[Tuple[str, int, int]],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for builder in (
        _build_keyword_injection_candidate,
        _build_contextual_bullet_candidate,
        _build_skill_expansion_candidate,
    ):
        candidate = builder(document, signal, used_targets)
        if candidate:
            candidates.append(candidate)

    return candidates


def _build_keyword_injection_candidate(
    document: ResumeDocument,
    signal: str,
    used_targets: set[Tuple[str, int, int]],
) -> Dict[str, Any] | None:
    rule = _KEYWORD_INJECTION_RULES.get(_normalize_signal(signal))
    if not rule:
        return None

    target = _best_bullet_match(document, rule["evidence"], used_targets)
    if not target:
        return None

    entry_index, bullet_index, bullet = target
    updated_bullet = _inject_phrase_into_bullet(bullet, rule["phrase"], signal)
    if updated_bullet == bullet:
        return None

    candidate_document = document.model_copy(deep=True)
    candidate_document.experience[entry_index].bullets[bullet_index] = updated_bullet
    return {
        "document": candidate_document,
        "used_target": ("experience", entry_index, bullet_index),
        "log": rule["log"],
        "change": {
            "action": "rewrite_experience_bullet",
            "type": "auto_fix",
            "target_section": "experience",
            "target": {
                "section": "experience",
                "entry_index": entry_index,
                "bullet_index": bullet_index,
            },
            "before_value": bullet,
            "after_value": updated_bullet,
            "value": signal,
            "reason": f"Added supported {signal} terminology from existing experience context.",
            "allowed_terms": [signal],
        },
    }


def _build_skill_expansion_candidate(
    document: ResumeDocument,
    signal: str,
    _: set[Tuple[str, int, int]],
) -> Dict[str, Any] | None:
    rule = _SKILL_EXPANSION_RULES.get(_normalize_signal(signal))
    if not rule:
        return None

    resume_text = resume_document_to_text(document).lower()
    if any(token and token not in resume_text for token in rule["required_all"]):
        return None
    if rule["required_any"] and not any(token in resume_text for token in rule["required_any"]):
        return None

    existing_skills = {
        item.lower()
        for values in document.skills.values()
        for item in values
    }
    if signal.lower() in existing_skills:
        return None

    candidate_document = document.model_copy(deep=True)
    category = pick_skill_category(candidate_document, rule["category"])
    candidate_document.skills.setdefault(category, [])
    candidate_document.skills[category] = dedupe(candidate_document.skills[category] + [signal])[:10]
    return {
        "document": candidate_document,
        "log": rule["log"],
        "change": {
            "action": "add_derived_skill",
            "type": "auto_fix",
            "target_section": "skills",
            "value": signal,
            "reason": f"Added {signal} to the skills section because the existing stack strongly implies it.",
            "allowed_terms": [signal],
            "evidence": "Supported by the current stack and technical context in the resume.",
            "job_relevant": True,
        },
    }


def _build_contextual_bullet_candidate(
    document: ResumeDocument,
    signal: str,
    used_targets: set[Tuple[str, int, int]],
) -> Dict[str, Any] | None:
    rule = _BULLET_ENHANCEMENT_RULES.get(_normalize_signal(signal))
    if not rule:
        return None

    target = _best_bullet_match(document, rule["evidence"], used_targets)
    if not target:
        return None

    entry_index, bullet_index, bullet = target
    updated_bullet = _inject_phrase_into_bullet(bullet, rule["phrase"], signal)
    if updated_bullet == bullet:
        return None

    candidate_document = document.model_copy(deep=True)
    candidate_document.experience[entry_index].bullets[bullet_index] = updated_bullet
    return {
        "document": candidate_document,
        "used_target": ("experience", entry_index, bullet_index),
        "log": rule["log"],
        "change": {
            "action": "rewrite_experience_bullet",
            "type": "auto_fix",
            "target_section": "experience",
            "target": {
                "section": "experience",
                "entry_index": entry_index,
                "bullet_index": bullet_index,
            },
            "before_value": bullet,
            "after_value": updated_bullet,
            "value": signal,
            "reason": f"Strengthened backend context to surface supported {signal} terminology.",
            "allowed_terms": [signal],
        },
    }


def _best_bullet_match(
    document: ResumeDocument,
    evidence_tokens: Iterable[str],
    used_targets: set[Tuple[str, int, int]],
) -> Tuple[int, int, str] | None:
    best: Tuple[int, int, str] | None = None
    best_score = 0

    for entry_index, entry in enumerate(document.experience):
        for bullet_index, bullet in enumerate(entry.bullets[:4]):
            target_key = ("experience", entry_index, bullet_index)
            if target_key in used_targets:
                continue

            lowered = bullet.lower()
            score = sum(1 for token in evidence_tokens if token in lowered)
            if score == 0:
                continue
            if bullet_index == 0:
                score += 1
            if any(char.isdigit() for char in bullet):
                score += 1

            if score > best_score:
                best = (entry_index, bullet_index, bullet)
                best_score = score

    return best


def _inject_phrase_into_bullet(text: str, phrase: str, signal: str) -> str:
    stripped = (text or "").strip().rstrip(".")
    lowered = stripped.lower()
    normalized_signal = _normalize_signal(signal)
    if not stripped or normalized_signal in _normalize_signal(stripped):
        return text
    if phrase.lower() in lowered:
        return text

    metric_clause = _METRIC_CLAUSE_PATTERN.search(stripped)
    if metric_clause:
        head = stripped[:metric_clause.start()].rstrip(", ")
        tail = stripped[metric_clause.start() + 2:]
        return clean_terminal(f"{head} {phrase}, {tail}")
    if "," in stripped:
        head, tail = stripped.split(",", 1)
        return clean_terminal(f"{head} {phrase}, {tail.strip()}")
    if " using " in lowered or " with " in lowered or " across " in lowered:
        return clean_terminal(f"{stripped} {phrase}")
    return clean_terminal(f"{stripped} {phrase}")


def _candidate_rejection_reason(
    *,
    verification: Dict[str, Any],
    current_score: Dict[str, Any],
    candidate_score: Dict[str, Any],
    current_ats: int,
    candidate_ats: int,
) -> str | None:
    if not verification["passed"]:
        return " ".join(verification["reasons"])
    if candidate_score["axes"]["credibility"] < 70:
        return "Rejected because the fix reduced credibility."
    if candidate_score["axes"]["metric_impact"] < current_score["axes"]["metric_impact"]:
        return "Rejected because the fix reduced measurable impact signals."
    if candidate_score["axes"]["technical_strength"] < current_score["axes"]["technical_strength"]:
        return "Rejected because the fix reduced system complexity signals."
    if candidate_ats <= current_ats:
        return "Rejected because the fix did not improve ATS alignment."
    return None
