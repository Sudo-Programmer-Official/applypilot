"""Document-level scoring for deterministic optimization decisions."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from packages.ai_engine.rules import (
    GENERIC_BULLET_PATTERNS,
    STRONG_ACTION_VERBS,
    clean_text,
    document_skill_names,
    extract_metric_signals,
    metric_impact_summary,
    preferred_skill_order,
    skill_order_index,
    summary_score,
    technical_signal_count,
)
from packages.job_intelligence.extractor import extract_resume_skills, keyword_names
from packages.resume_formatter import resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument

_SKILLS_SURFACE_TERMS = (
    "llm",
    "evaluation pipelines",
    "automation pipelines",
    "semantic similarity",
    "ai systems",
    "distributed systems",
    "aws",
    "ci/cd",
)

_CLUNKY_PATTERNS = (
    re.compile(r"\busing [a-z0-9 /-]+ techniques\b", re.IGNORECASE),
    re.compile(r"\bto automate\b", re.IGNORECASE),
    re.compile(r"\bunder heavy\b", re.IGNORECASE),
)

_SECTION_WEIGHTS = {
    "summary": 0.20,
    "experience": 0.45,
    "skills": 0.20,
    "projects": 0.10,
    "education": 0.05,
}

_KEYWORD_CONTEXT_WEIGHTS = {
    "title": 1.7,
    "summary": 1.5,
    "skills": 1.0,
    "experience_first_bullet": 3.0,
    "experience": 2.0,
    "projects": 1.25,
    "education": 0.5,
}

_FIRST_BULLET_MULTIPLIER = 1.5
_KEYWORD_WINDOW_SIZE = 6
_WEAK_ACTION_PREFIXES = ("worked", "helped", "responsible", "assisted", "supported", "involved")
_SYSTEM_COMPLEXITY_TERMS = (
    "distributed",
    "concurrency",
    "concurrent",
    "scalable",
    "fault-tolerant",
    "event-driven",
    "parallel",
    "orchestration",
    "microservices",
    "serverless",
)

_KEYWORD_VARIANT_HINTS = {
    "aws": (("aws",), ("amazon", "web", "services")),
    "llms": (("llm",), ("llms",), ("large", "language", "model"), ("large", "language", "models")),
    "rest apis": (("rest", "api"), ("rest", "apis"), ("restful", "api"), ("restful", "apis"), ("api",), ("apis",)),
    "ci/cd": (("ci", "cd"), ("continuous", "integration"), ("continuous", "delivery"), ("continuous", "deployment")),
    "distributed systems": (("distributed", "systems"), ("distributed", "system"), ("distributed",)),
    "event-driven systems": (("event", "driven", "systems"), ("event", "driven", "system"), ("event", "driven")),
    "data pipelines": (("data", "pipelines"), ("data", "pipeline"), ("pipeline",), ("pipelines",), ("etl",)),
    "node.js": (("node", "js"), ("nodejs",), ("node",)),
    "postgresql": (("postgresql",), ("postgres",)),
}

_RELATED_CONTEXT_TERMS = {
    "distributed systems": {"distributed", "scalable", "concurrent", "parallel", "workers", "cluster", "sharding", "fault", "tolerant", "backend"},
    "aws": {"lambda", "s3", "rds", "cloudwatch", "serverless", "cloud", "ec2"},
    "llms": {"prompt", "embedding", "retrieval", "semantic", "evaluation", "inference", "rag", "ai"},
    "rest apis": {"backend", "services", "endpoints", "microservices", "http"},
    "ci/cd": {"deployment", "pipeline", "pipelines", "release", "build", "automation"},
    "docker": {"containers", "container", "images", "kubernetes"},
    "kubernetes": {"cluster", "containers", "pods", "orchestration"},
    "python": {"backend", "automation", "api", "lambda", "fastapi", "django"},
    "data pipelines": {"etl", "batch", "streaming", "kafka", "spark", "orchestration"},
}

_KEYWORD_CLUSTERS = {
    "distributed_systems": {"distributed", "parallel", "concurrency", "concurrent", "sharding", "workers", "cluster", "fault", "tolerant"},
    "aws_cloud": {"aws", "lambda", "rds", "s3", "cloudwatch", "serverless", "cloud"},
    "llm_systems": {"llm", "llms", "prompt", "embedding", "retrieval", "semantic", "evaluation", "inference"},
    "backend_platform": {"backend", "service", "services", "api", "apis", "microservices", "endpoint", "endpoints"},
    "data_platform": {"pipeline", "pipelines", "spark", "kafka", "etl", "batch", "streaming", "sharding"},
}

_KEYWORD_CLUSTER_MAP = {
    "distributed systems": ("distributed_systems", "backend_platform"),
    "aws": ("aws_cloud",),
    "llms": ("llm_systems",),
    "rest apis": ("backend_platform",),
    "microservices": ("backend_platform", "distributed_systems"),
    "data pipelines": ("data_platform",),
    "docker": ("backend_platform",),
    "kubernetes": ("distributed_systems",),
}


def score_resume(
    document: ResumeDocument,
    job_skills: List[Dict[str, Any]],
    original_document: ResumeDocument | None = None,
    role_info: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    baseline_document = original_document or document
    text = resume_document_to_text(document)
    baseline_text = resume_document_to_text(baseline_document)
    job_skill_names = [skill["name"] for skill in job_skills]

    keyword_alignment = _jd_keyword_match_score(document, job_skill_names)
    technical_strength = _technical_strength_score(document, text)
    credibility = _credibility_score(document, baseline_document, text, baseline_text)
    metric_impact = _metric_impact_score(text)
    technology_density = _technology_density_score(document)
    action_verb_strength = _action_verb_strength_score(document)
    readability = _readability_score(document, text, role_info or {})

    total = round(
        0.30 * keyword_alignment["score"]
        + 0.20 * metric_impact["score"]
        + 0.20 * technical_strength
        + 0.15 * technology_density
        + 0.10 * action_verb_strength
        + 0.05 * readability,
        2,
    )

    return {
        "total": total,
        "axes": {
            "jd_keyword_match": round(keyword_alignment["score"], 2),
            "technical_strength": round(technical_strength, 2),
            "metric_impact": round(metric_impact["score"], 2),
            "technology_density": round(technology_density, 2),
            "action_verb_strength": round(action_verb_strength, 2),
            "readability": round(readability, 2),
            "credibility": round(credibility, 2),
        },
        "matched_job_keywords": keyword_alignment["matched_keywords"],
        "metric_signals": metric_impact["signals"],
        "metric_breakdown": metric_impact["breakdown"],
        "keyword_analysis": {
            "strong_matches": keyword_alignment["strong_matches"],
            "weak_matches": keyword_alignment["weak_matches"],
            "missing_keywords": keyword_alignment["missing_keywords"],
            "cluster_matches": keyword_alignment["cluster_matches"],
        },
    }


def _jd_keyword_match_score(document: ResumeDocument, job_skill_names: List[str]) -> Dict[str, Any]:
    if not job_skill_names:
        return {
            "score": 50.0,
            "matched_keywords": [],
            "strong_matches": [],
            "weak_matches": [],
            "missing_keywords": [],
            "cluster_matches": [],
        }

    section_skills = _skills_by_scan_section(document)
    scan_sections = _scan_sections(document)
    keyword_matches = []
    cluster_matches = set()

    for skill in job_skill_names:
        match = _score_keyword_match(skill, scan_sections, section_skills)
        keyword_matches.append(match)
        cluster_matches.update(match["clusters"])

    strong_matches = sorted(
        [match for match in keyword_matches if match["level"] == "strong"],
        key=lambda match: match["score"],
        reverse=True,
    )
    weak_matches = sorted(
        [match for match in keyword_matches if match["level"] == "weak"],
        key=lambda match: match["score"],
        reverse=True,
    )
    missing_keywords = [match["keyword"] for match in keyword_matches if match["level"] == "missing"]

    return {
        "score": round(sum(match["score"] for match in keyword_matches) / max(len(keyword_matches), 1), 2),
        "matched_keywords": sorted(match["keyword"] for match in keyword_matches if match["present"]),
        "strong_matches": strong_matches[:6],
        "weak_matches": weak_matches[:6],
        "missing_keywords": missing_keywords[:6],
        "cluster_matches": sorted(cluster_matches),
    }


def _technical_strength_score(document: ResumeDocument, text: str) -> float:
    summary_signals = technical_signal_count(document.summary or "") * _SECTION_WEIGHTS["summary"]
    skills_signals = technical_signal_count(_skills_text(document)) * _SECTION_WEIGHTS["skills"]
    project_signals = technical_signal_count(_project_text(document)) * _SECTION_WEIGHTS["projects"]
    education_signals = technical_signal_count(_education_text(document)) * _SECTION_WEIGHTS["education"]
    experience_signals = 0.0
    first_bullet_complexity = 0.0

    for entry in document.experience:
        for index, bullet in enumerate(entry.bullets):
            weight = _SECTION_WEIGHTS["experience"] * (_FIRST_BULLET_MULTIPLIER if index == 0 else 1.0)
            signal_count = technical_signal_count(bullet) + _complexity_signal_count(bullet)
            experience_signals += signal_count * weight
            if index == 0:
                first_bullet_complexity += signal_count

    summary_strength = max(summary_score(document.summary), 0)
    surface_bonus = _skills_surface_bonus(document)
    score = (
        18
        + summary_signals * 4
        + skills_signals * 2.5
        + project_signals * 3
        + education_signals
        + experience_signals * 5
        + first_bullet_complexity * 3
        + summary_strength * 1.5
        + surface_bonus
    )
    return min(100.0, max(0.0, float(score)))


def _credibility_score(
    document: ResumeDocument,
    baseline_document: ResumeDocument,
    text: str,
    baseline_text: str,
) -> float:
    baseline_skills = {name.lower() for name in document_skill_names(baseline_document)}
    current_skills = {name.lower() for name in document_skill_names(document)}
    unsupported_additions = len(current_skills - baseline_skills)
    baseline_metric_impact = _metric_impact_score(baseline_text)["score"]
    current_metric_impact = _metric_impact_score(text)["score"]
    metric_penalty = max(baseline_metric_impact - current_metric_impact, 0) * 0.6
    summary_penalty = max(summary_score(baseline_document.summary) - summary_score(document.summary), 0) * 4
    score = 100 - unsupported_additions * 25 - metric_penalty - summary_penalty
    return min(100.0, max(0.0, float(score)))


def _readability_score(document: ResumeDocument, text: str, role_info: Dict[str, str]) -> float:
    score = 38.0
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_lines = [line[2:].strip() for line in lines if line.startswith("- ")]

    if bullet_lines:
        bullet_score = _bullet_length_score(document)
        score += bullet_score * 0.45

        if all(line.endswith(".") for line in bullet_lines):
            score += 6

        clunky_hits = sum(1 for line in bullet_lines for pattern in _CLUNKY_PATTERNS if pattern.search(line))
        score -= clunky_hits * 3

    if not any("  " in line for line in lines):
        score += 4

    if document.skills:
        preferred = preferred_skill_order(role_info.get("label", ""))
        categories = list(document.skills.keys())
        current_order = [skill_order_index(category, preferred)[0] for category in categories]
        if current_order == sorted(current_order):
            score += 10

    summary_words = len(clean_text(document.summary).split())
    if 10 <= summary_words <= 24:
        score += 8
    elif summary_words > 30:
        score -= 8

    return min(100.0, max(0.0, score))


def _skills_surface_bonus(document: ResumeDocument) -> float:
    surfaced = " ".join(skill for values in document.skills.values() for skill in values).lower()
    return float(sum(3 for term in _SKILLS_SURFACE_TERMS if term in surfaced))


def _metric_impact_score(text: str) -> Dict[str, Any]:
    return metric_impact_summary(text)


def _technology_density_score(document: ResumeDocument) -> float:
    unique_technologies = {name.lower() for name in document_skill_names(document)}
    if not unique_technologies:
        return 20.0

    total_lines = len([line for line in resume_document_to_text(document).splitlines() if line.strip()])
    experience_skills = {
        name.lower()
        for entry in document.experience
        for bullet in entry.bullets
        for name in keyword_names(extract_resume_skills(bullet))
    }
    density_ratio = len(unique_technologies) / max(total_lines, 1)
    score = density_ratio * 80 + min(len(unique_technologies), 12) * 1.5 + min(len(experience_skills), 8) * 3
    return min(100.0, max(0.0, float(score)))


def _action_verb_strength_score(document: ResumeDocument) -> float:
    weighted_total = 0.0
    weighted_strong = 0.0
    weighted_weak = 0.0
    weak_prefixes = _WEAK_ACTION_PREFIXES + GENERIC_BULLET_PATTERNS

    for entry in document.experience:
        for index, bullet in enumerate(entry.bullets):
            weight = _FIRST_BULLET_MULTIPLIER if index == 0 else 1.0
            weighted_total += weight
            lowered = clean_text(bullet).lower()
            first_word = lowered.split(" ", 1)[0]
            if first_word in STRONG_ACTION_VERBS:
                weighted_strong += weight
            if any(lowered.startswith(prefix) for prefix in weak_prefixes):
                weighted_weak += weight

    if weighted_total == 0:
        return 50.0

    score = 35 + (weighted_strong / weighted_total) * 55 - (weighted_weak / weighted_total) * 25
    return min(100.0, max(0.0, float(score)))


def _bullet_length_score(document: ResumeDocument) -> float:
    weighted_score = 0.0
    total_weight = 0.0

    for entry in document.experience:
        for index, bullet in enumerate(entry.bullets):
            weight = _FIRST_BULLET_MULTIPLIER if index == 0 else 1.0
            words = len(clean_text(bullet).split())
            if 18 <= words <= 28:
                line_score = 100.0
            elif 12 <= words <= 34:
                line_score = 82.0
            elif 8 <= words <= 40:
                line_score = 62.0
            else:
                line_score = 35.0
            weighted_score += line_score * weight
            total_weight += weight

    if total_weight == 0:
        return 70.0
    return weighted_score / total_weight


def _skills_by_scan_section(document: ResumeDocument) -> Dict[str, set[str]]:
    section_skills = {
        "title": {name.lower() for name in keyword_names(extract_resume_skills(document.title or ""))},
        "summary": {name.lower() for name in keyword_names(extract_resume_skills(document.summary or ""))},
        "skills": {name.lower() for name in keyword_names(extract_resume_skills(_skills_text(document)))},
        "experience_first_bullet": set(),
        "experience": set(),
        "projects": {name.lower() for name in keyword_names(extract_resume_skills(_project_text(document)))},
        "education": {name.lower() for name in keyword_names(extract_resume_skills(_education_text(document)))},
    }

    for entry in document.experience:
        for index, bullet in enumerate(entry.bullets):
            matched = {name.lower() for name in keyword_names(extract_resume_skills(bullet))}
            if index == 0:
                section_skills["experience_first_bullet"].update(matched)
            else:
                section_skills["experience"].update(matched)

    return section_skills


def _score_keyword_match(
    keyword: str,
    scan_sections: List[Dict[str, Any]],
    section_skills: Dict[str, set[str]],
) -> Dict[str, Any]:
    normalized = keyword.lower()
    variants = _keyword_variants(normalized)
    present = False
    best_section = ""
    best_section_weight = 0.0
    best_context_score = 0.0
    best_related_terms: List[str] = []
    best_clusters: List[str] = []
    best_metric_support = False

    for section in scan_sections:
        occurrences = _find_keyword_occurrences(section["tokens"], variants)
        if not occurrences:
            continue

        present = True
        if section["weight"] > best_section_weight:
            best_section_weight = section["weight"]
            best_section = section["name"]

        for start, end in occurrences:
            window_tokens = section["tokens"][max(0, start - _KEYWORD_WINDOW_SIZE): min(len(section["tokens"]), end + _KEYWORD_WINDOW_SIZE + 1)]
            related_terms = _related_terms_in_window(normalized, window_tokens)
            clusters = _cluster_hits_for_keyword(normalized, window_tokens)
            metric_support = bool(extract_metric_signals(" ".join(window_tokens)))
            context_score = min(len(related_terms), 3) * 0.85 + len(clusters) * 0.65 + (1.0 if metric_support else 0.0)

            if context_score > best_context_score:
                best_context_score = context_score
                best_related_terms = related_terms[:4]
                best_clusters = clusters[:3]
                best_metric_support = metric_support
                best_section = section["name"]
                best_section_weight = section["weight"]

    if not present:
        return {
            "keyword": keyword,
            "score": 0.0,
            "level": "missing",
            "present": False,
            "section": "",
            "related_terms": [],
            "clusters": [],
            "metric_support": False,
        }

    presence_score = 100.0
    max_section_weight = max(_KEYWORD_CONTEXT_WEIGHTS.values())
    section_score = min(best_section_weight / max_section_weight, 1.0) * 100.0
    context_score = min(best_context_score / 4.2, 1.0) * 100.0
    total_score = round(0.4 * presence_score + 0.4 * context_score + 0.2 * section_score, 2)
    level = "strong" if total_score >= 65 or (context_score >= 50 and best_section_weight >= 2.0) else "weak"

    # If a keyword is only surfaced in a low-context section like skills, do not overstate it.
    if best_section == "skills" and not best_related_terms and not best_metric_support:
        level = "weak"

    return {
        "keyword": keyword,
        "score": total_score,
        "level": level,
        "present": True,
        "section": best_section,
        "related_terms": best_related_terms,
        "clusters": best_clusters,
        "metric_support": best_metric_support,
    }


def _scan_sections(document: ResumeDocument) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []

    sections.append(_build_scan_section("title", document.title, _KEYWORD_CONTEXT_WEIGHTS["title"]))
    sections.append(_build_scan_section("summary", document.summary, _KEYWORD_CONTEXT_WEIGHTS["summary"]))
    sections.append(_build_scan_section("skills", _skills_text(document), _KEYWORD_CONTEXT_WEIGHTS["skills"]))

    for entry in document.experience:
        for index, bullet in enumerate(entry.bullets):
            section_name = "experience_first_bullet" if index == 0 else "experience"
            sections.append(_build_scan_section(section_name, bullet, _KEYWORD_CONTEXT_WEIGHTS[section_name]))

    sections.append(_build_scan_section("projects", _project_text(document), _KEYWORD_CONTEXT_WEIGHTS["projects"]))
    sections.append(_build_scan_section("education", _education_text(document), _KEYWORD_CONTEXT_WEIGHTS["education"]))
    return [section for section in sections if section["tokens"]]


def _build_scan_section(name: str, text: str, weight: float) -> Dict[str, Any]:
    return {
        "name": name,
        "weight": weight,
        "tokens": _tokenize(text),
    }


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _keyword_variants(keyword: str) -> List[List[str]]:
    variants = [list(variant) for variant in _KEYWORD_VARIANT_HINTS.get(keyword, ())]
    base_tokens = _tokenize(keyword)
    if base_tokens:
        variants.append(base_tokens)
        singularized = base_tokens[:-1] + [base_tokens[-1][:-1]] if base_tokens[-1].endswith("s") and len(base_tokens[-1]) > 3 else base_tokens
        variants.append(singularized)

        # Allow high-signal anchor tokens for multi-word skills so contextual windows can still score them.
        if len(base_tokens) > 1 and base_tokens[0] not in {"continuous", "amazon"}:
            variants.append([base_tokens[0]])

    deduped: List[List[str]] = []
    seen = set()
    for variant in variants:
        key = tuple(variant)
        if not variant or key in seen:
            continue
        seen.add(key)
        deduped.append(variant)
    return deduped


def _find_keyword_occurrences(tokens: List[str], variants: List[List[str]]) -> List[tuple[int, int]]:
    matches: List[tuple[int, int]] = []
    seen = set()
    for variant in variants:
        variant_length = len(variant)
        if variant_length == 0 or variant_length > len(tokens):
            continue
        for index in range(len(tokens) - variant_length + 1):
            if tokens[index:index + variant_length] != variant:
                continue
            key = (index, index + variant_length - 1)
            if key in seen:
                continue
            seen.add(key)
            matches.append(key)
    return matches


def _related_terms_in_window(keyword: str, window_tokens: List[str]) -> List[str]:
    related_terms = _RELATED_CONTEXT_TERMS.get(keyword, set())
    present_terms = sorted(term for term in related_terms if term in set(window_tokens))
    return present_terms


def _cluster_hits_for_keyword(keyword: str, window_tokens: List[str]) -> List[str]:
    token_set = set(window_tokens)
    matches: List[str] = []
    for cluster_name in _KEYWORD_CLUSTER_MAP.get(keyword, ()):
        if len(token_set & _KEYWORD_CLUSTERS[cluster_name]) >= 2:
            matches.append(cluster_name.replace("_", " "))
    return matches


def _complexity_signal_count(text: str) -> int:
    lowered = clean_text(text).lower()
    return sum(1 for term in _SYSTEM_COMPLEXITY_TERMS if term in lowered)


def _skills_text(document: ResumeDocument) -> str:
    return " ".join(f"{category} {' '.join(values)}" for category, values in document.skills.items())


def _project_text(document: ResumeDocument) -> str:
    parts: List[str] = []
    for project in document.projects:
        parts.append(project.name)
        parts.append(project.details)
        parts.extend(project.bullets)
    return " ".join(part for part in parts if part)


def _education_text(document: ResumeDocument) -> str:
    parts: List[str] = []
    for item in document.education:
        parts.extend([item.school, item.degree, item.date, *item.details])
    return " ".join(part for part in parts if part)
