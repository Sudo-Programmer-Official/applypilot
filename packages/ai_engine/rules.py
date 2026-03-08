"""Shared deterministic rules for resume optimization."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

from packages.job_intelligence.extractor import extract_resume_skills_from_document, keyword_names
from packages.shared_types.resume_document import ResumeDocument

CATEGORY_HINTS = {
    "language": "Languages",
    "framework": "Frameworks",
    "tool": "Cloud & Infrastructure",
    "cloud": "Cloud & Infrastructure",
    "methodology": "Cloud & Infrastructure",
    "architecture": "Backend & Distributed Systems",
    "database": "Databases",
    "data": "Data Engineering",
    "ml": "AI & Machine Learning",
}

SUMMARY_FOCUS = {
    "backend engineer": "scalable backend systems, cloud infrastructure, and service reliability",
    "data engineer": "data pipelines, distributed processing, and production reliability",
    "ml engineer": "applied machine learning systems, evaluation rigor, and production delivery",
    "frontend engineer": "product-facing interfaces, performance, and cross-functional delivery",
    "devops engineer": "platform reliability, cloud infrastructure, and deployment automation",
}

BACKEND_SKILL_ORDER = [
    "Languages",
    "Backend & Distributed Systems",
    "Databases",
    "Cloud & Infrastructure",
    "Systems Engineering",
    "Core CS",
    "Frameworks",
    "AI & Machine Learning",
    "Data Engineering",
    "Technical Skills",
]

GENERIC_SKILL_ORDER = [
    "Languages",
    "Frameworks",
    "Backend & Distributed Systems",
    "Databases",
    "Cloud & Infrastructure",
    "Systems Engineering",
    "Core CS",
    "Data Engineering",
    "AI & Machine Learning",
    "Technical Skills",
]

SUMMARY_GENERIC_PATTERNS = (
    "experienced in scalable",
    "service reliability",
    "measurable impact",
    "production reliability",
)

METRIC_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:%|x|m\+|k\+|records?|workers?|hours?|hrs?|services?|pipelines?|clients?)\b",
    re.IGNORECASE,
)

TECHNICAL_SIGNAL_PATTERN = re.compile(
    r"\b(?:distributed|fault-tolerant|scalable|high-concurrency|concurrency|cloud|backend|lambda|rds|"
    r"microservices|systems?|llm(?:-powered)?|semantic similarity|evaluation pipelines?|automation pipelines?|"
    r"ai systems?|ci/cd|aws|postgresql|sql|docker|kubernetes)\b",
    re.IGNORECASE,
)

METRIC_CATEGORY_WEIGHTS = {
    "scale": 0.4,
    "performance": 0.3,
    "business_impact": 0.2,
    "quantity": 0.1,
}

HIGH_IMPACT_METRIC_CATEGORIES = {"scale", "performance", "business_impact"}

_METRIC_VALUE_PATTERN = re.compile(
    r"\b\d+\s*[-–]\s*\d+\b|\b\d+(?:\.\d+)?(?:\s?(?:m|k)\+?|\+|%)?(?=\s|$)",
    re.IGNORECASE,
)

_SCALE_HINTS = (
    ("records", "record processing scale"),
    ("record", "record processing scale"),
    ("users", "user scale"),
    ("requests", "request throughput scale"),
    ("req/sec", "request throughput scale"),
    ("transactions", "transaction scale"),
    ("events", "event stream scale"),
    ("messages", "message throughput scale"),
    ("workers", "concurrent workers"),
    ("worker", "concurrent workers"),
    ("nodes", "cluster node scale"),
    ("services", "service scale"),
    ("pipelines", "pipeline scale"),
    ("clients", "client scale"),
)

_PERFORMANCE_HINTS = (
    ("runtime", "runtime improvement"),
    ("latency", "latency improvement"),
    ("throughput", "throughput improvement"),
    ("performance", "performance improvement"),
    ("minutes", "runtime improvement"),
    ("minute", "runtime improvement"),
    ("hours", "runtime improvement"),
    ("hour", "runtime improvement"),
    ("seconds", "runtime improvement"),
    ("second", "runtime improvement"),
)

_BUSINESS_HINTS = (
    ("deployment effort", "deployment automation gain"),
    ("deployment", "deployment automation gain"),
    ("automation", "automation gain"),
    ("reliability", "reliability improvement"),
    ("availability", "availability improvement"),
    ("conversion", "conversion gain"),
    ("efficiency", "efficiency gain"),
    ("cost", "cost reduction"),
    ("revenue", "revenue impact"),
    ("effort", "effort reduction"),
)

_QUANTITY_HINTS = (
    ("apis", "API scope"),
    ("api", "API scope"),
    ("services", "service scope"),
    ("service", "service scope"),
    ("dashboards", "dashboard scope"),
    ("dashboard", "dashboard scope"),
    ("integrations", "integration scope"),
    ("integration", "integration scope"),
    ("features", "feature scope"),
    ("feature", "feature scope"),
    ("modules", "module scope"),
    ("module", "module scope"),
)

STRONG_ACTION_VERBS = (
    "architected",
    "built",
    "designed",
    "developed",
    "implemented",
    "improved",
    "optimized",
    "resolved",
    "led",
    "automated",
    "deployed",
)

GENERIC_BULLET_PATTERNS = (
    "responsible for",
    "worked on",
    "helped",
    "assisted with",
    "involved in",
)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_terminal(text: str) -> str:
    cleaned = clean_text(text).rstrip(".")
    return f"{cleaned}."


def finalize_summary(summary: str) -> str:
    cleaned = clean_text(summary).rstrip(".")
    return f"{cleaned}."


def dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def preferred_skill_order(role_label: str) -> List[str]:
    role_lower = (role_label or "").lower()
    if any(token in role_lower for token in ("backend", "distributed", "platform", "devops")):
        return BACKEND_SKILL_ORDER
    return GENERIC_SKILL_ORDER


def skill_order_index(category: str, preferred_order: List[str]) -> Tuple[int, str]:
    normalized = category.lower()
    for index, preferred in enumerate(preferred_order):
        preferred_lower = preferred.lower()
        if normalized == preferred_lower:
            return index, normalized
        if preferred_lower in normalized or normalized in preferred_lower:
            return index, normalized
    return len(preferred_order), normalized


def pick_skill_category(document: ResumeDocument, category: str, fallback: str | None = None) -> str:
    preferred = fallback or CATEGORY_HINTS.get(category, "Technical Skills")
    preferred_lower = preferred.lower()
    for existing in document.skills:
        lowered = existing.lower()
        if preferred_lower in lowered:
            return existing
        if category == "language" and "language" in lowered:
            return existing
        if category in {"cloud", "tool", "methodology"} and ("cloud" in lowered or "infra" in lowered):
            return existing
        if category == "database" and "database" in lowered:
            return existing
        if category == "architecture" and ("backend" in lowered or "system" in lowered):
            return existing
        if category == "ml" and ("ai" in lowered or "machine" in lowered):
            return existing
    return preferred


def summary_score(summary: str) -> int:
    lowered = summary.lower()
    metrics = len(METRIC_PATTERN.findall(lowered))
    technical_signals = len(TECHNICAL_SIGNAL_PATTERN.findall(lowered))
    generic_hits = sum(1 for pattern in SUMMARY_GENERIC_PATTERNS if pattern in lowered)
    sentence_length_bonus = 1 if 10 <= len(summary.split()) <= 24 else 0
    return metrics * 3 + technical_signals + sentence_length_bonus - generic_hits


def bullet_strength_score(text: str) -> int:
    cleaned = clean_text(text)
    lowered = cleaned.lower()
    metrics = len(METRIC_PATTERN.findall(cleaned))
    technical_signals = len(TECHNICAL_SIGNAL_PATTERN.findall(cleaned))
    action_bonus = 1 if cleaned.split(" ", 1)[0].lower().rstrip(":") in STRONG_ACTION_VERBS else 0
    generic_penalty = sum(1 for pattern in GENERIC_BULLET_PATTERNS if pattern in lowered)
    return metrics * 3 + technical_signals + action_bonus - generic_penalty * 2


def technical_signal_count(text: str) -> int:
    return len(set(match.lower() for match in TECHNICAL_SIGNAL_PATTERN.findall(text or "")))


def metric_count(text: str) -> int:
    return len(METRIC_PATTERN.findall(text or ""))


def extract_metric_signals(text: str) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []
    seen = set()

    for fragment in _split_metric_fragments(text):
        for match in _METRIC_VALUE_PATTERN.finditer(fragment):
            metric = clean_text(match.group(0))
            lowered_context = fragment.lower()[max(0, match.start() - 18): min(len(fragment), match.end() + 42)]
            category, descriptor = _classify_metric_fragment(metric, lowered_context)
            if not category or not descriptor:
                continue

            signal = {
                "metric": metric,
                "category": category,
                "descriptor": descriptor,
                "label": f"{metric} {descriptor}",
                "impact_weight": METRIC_CATEGORY_WEIGHTS[category],
                "context": fragment,
                "key": _metric_signal_key(metric, category, descriptor),
            }
            if signal["key"] in seen:
                continue
            seen.add(signal["key"])
            signals.append(signal)

    return signals


def metric_impact_summary(text: str) -> Dict[str, Any]:
    signals = extract_metric_signals(text)
    grouped = {
        "scale": [signal for signal in signals if signal["category"] == "scale"],
        "performance": [signal for signal in signals if signal["category"] == "performance"],
        "business_impact": [signal for signal in signals if signal["category"] == "business_impact"],
        "quantity": [signal for signal in signals if signal["category"] == "quantity"],
    }
    breakdown = {
        "scale": min(100.0, len(grouped["scale"]) * 42.0),
        "performance": min(100.0, len(grouped["performance"]) * 38.0),
        "business_impact": min(100.0, len(grouped["business_impact"]) * 30.0),
        "quantity": min(100.0, len(grouped["quantity"]) * 18.0),
    }
    score = round(
        sum(METRIC_CATEGORY_WEIGHTS[key] * value for key, value in breakdown.items()),
        2,
    )
    return {
        "score": score,
        "breakdown": breakdown,
        "signals": signals[:6],
        "counts": {key: len(value) for key, value in grouped.items()},
    }


def detect_lost_metric_signals(before_text: str, after_text: str) -> List[Dict[str, Any]]:
    after_keys = {signal["key"] for signal in extract_metric_signals(after_text)}
    return [
        signal
        for signal in extract_metric_signals(before_text)
        if signal["key"] not in after_keys
    ]


def document_skill_names(document: ResumeDocument) -> List[str]:
    return keyword_names(extract_resume_skills_from_document(document.model_dump()))


def extract_primary_scale_metric(text: str) -> str:
    for match in METRIC_PATTERN.findall(text or ""):
        lowered = match.lower()
        if any(token in lowered for token in ("record", "worker", "service", "pipeline", "client")):
            return match
    return ""


def infer_focus_phrases(source_text: str, job_skill_names: List[str]) -> List[str]:
    lowered = clean_text(source_text).lower()
    phrases: List[str] = []

    if "llm" in lowered or "large language model" in lowered:
        phrases.append("LLM-powered systems")
    if "semantic similarity" in lowered:
        phrases.append("semantic similarity workflows")
    if "distributed" in lowered or "high-concurrency" in lowered:
        phrases.append("distributed systems")
    if "backend" in lowered or "api" in lowered:
        phrases.append("backend services")
    if "aws" in lowered or "cloud" in lowered or "lambda" in lowered:
        phrases.append("cloud infrastructure")
    if "pipeline" in lowered or "orchestration" in lowered or "automation" in lowered:
        phrases.append("automation pipelines")

    if not phrases:
        for skill in job_skill_names[:3]:
            phrases.append(skill.lower())

    return dedupe(phrases)


def build_summary(role_label: str, job_skill_names: List[str], evidence_text: str = "") -> str:
    focus = infer_focus_phrases(evidence_text, job_skill_names)
    scale_metric = extract_primary_scale_metric(evidence_text)

    if focus and scale_metric:
        return f"{role_label} building {', '.join(focus[:2])} across workloads handling {scale_metric}."
    if focus:
        return f"{role_label} building {', '.join(focus[:3])} with measurable production impact."

    default_focus = SUMMARY_FOCUS.get(role_label.lower(), "scalable systems, measurable impact, and production reliability")
    lead_skills = ", ".join(job_skill_names[:3])
    if lead_skills:
        return f"{role_label} building {default_focus} across {lead_skills}."
    return f"{role_label} building {default_focus}."


def _split_metric_fragments(text: str) -> List[str]:
    return [
        clean_text(fragment)
        for fragment in re.split(r"(?:\n+|(?<=[.!?])\s+)", text or "")
        if clean_text(fragment)
    ]


def _classify_metric_fragment(metric: str, lowered_fragment: str) -> Tuple[str | None, str | None]:
    normalized_metric = metric.lower().replace(" ", "")
    has_percent = "%" in normalized_metric
    has_range = bool(re.search(r"\d+\s*[-–]\s*\d+", metric))
    has_large_suffix = bool(re.search(r"(?:m|k)\+$", normalized_metric))

    scale_descriptor = _match_metric_descriptor(lowered_fragment, _SCALE_HINTS)
    performance_descriptor = _match_metric_descriptor(lowered_fragment, _PERFORMANCE_HINTS)
    business_descriptor = _match_metric_descriptor(lowered_fragment, _BUSINESS_HINTS)
    quantity_descriptor = _match_metric_descriptor(lowered_fragment, _QUANTITY_HINTS)

    if scale_descriptor and (has_large_suffix or has_range or not has_percent):
        return "scale", scale_descriptor
    if performance_descriptor and (has_percent or any(token in lowered_fragment for token in ("runtime", "latency", "throughput", "hour", "minute", "second"))):
        return "performance", performance_descriptor
    if business_descriptor and (has_percent or any(token in lowered_fragment for token in ("deployment", "effort", "reliability", "conversion", "cost"))):
        return "business_impact", business_descriptor
    if scale_descriptor:
        return "scale", scale_descriptor
    if performance_descriptor:
        return "performance", performance_descriptor
    if business_descriptor:
        return "business_impact", business_descriptor
    if quantity_descriptor:
        return "quantity", quantity_descriptor
    if has_percent:
        return "business_impact", "business impact"
    return None, None


def _match_metric_descriptor(fragment: str, hints: Tuple[Tuple[str, str], ...]) -> str | None:
    for needle, descriptor in hints:
        if needle in fragment:
            return descriptor
    return None


def _metric_signal_key(metric: str, category: str, descriptor: str) -> str:
    normalized_metric = re.sub(r"\s+", "", metric.lower()).replace("–", "-")
    normalized_descriptor = re.sub(r"[^a-z0-9]+", "-", descriptor.lower()).strip("-")
    return f"{category}:{normalized_metric}:{normalized_descriptor}"
