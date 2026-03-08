"""Structured job description intelligence and resume skill extraction."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

_NOISE_MARKERS = (
    "equal opportunity",
    "all qualified applicants",
    "reasonable accommodation",
    "benefits",
    "medical",
    "dental",
    "vision",
    "parental leave",
    "salary",
    "compensation",
    "pay range",
    "visa",
    "sponsorship",
    "relocation",
    "amazon.jobs",
    "applicants",
    "background check",
    "drug test",
    "location:",
    "located in",
)

_SECTION_PATTERNS = {
    "requirements": r"^(requirements|qualifications|basic qualifications|required skills|must have|what you bring)[: ]*$",
    "preferred": r"^(preferred qualifications|nice to have|preferred skills)[: ]*$",
    "responsibilities": r"^(responsibilities|what you will do|what you'll do|you will|in this role)[: ]*$",
}

_PHRASE_MARKERS = (
    "experience with",
    "knowledge of",
    "proficiency in",
    "hands-on with",
    "familiar with",
    "expertise in",
    "working with",
)

_CATEGORY_SECTIONS = {
    "language": ["Technical Skills", "Experience", "Projects"],
    "framework": ["Technical Skills", "Projects", "Experience"],
    "tool": ["Technical Skills", "Projects", "Experience"],
    "cloud": ["Cloud Infrastructure", "Technical Skills", "Projects"],
    "architecture": ["Experience", "Projects", "Professional Summary"],
    "methodology": ["Cloud Infrastructure", "Technical Skills", "Experience"],
    "database": ["Technical Skills", "Projects", "Experience"],
    "data": ["Projects", "Experience", "Technical Skills"],
    "ml": ["Projects", "Experience", "Technical Skills"],
}

_SKILL_LIBRARY: List[Dict[str, Any]] = [
    {"name": "Python", "category": "language", "patterns": [r"\bpython\b"]},
    {"name": "Java", "category": "language", "patterns": [r"\bjava\b"]},
    {"name": "Go", "category": "language", "patterns": [r"\bgolang\b", r"\bgo\b"]},
    {"name": "JavaScript", "category": "language", "patterns": [r"\bjavascript\b"]},
    {"name": "TypeScript", "category": "language", "patterns": [r"\btypescript\b"]},
    {"name": "SQL", "category": "language", "patterns": [r"\bsql\b"]},
    {"name": "FastAPI", "category": "framework", "patterns": [r"\bfastapi\b"]},
    {"name": "Django", "category": "framework", "patterns": [r"\bdjango\b"]},
    {"name": "Flask", "category": "framework", "patterns": [r"\bflask\b"]},
    {"name": "Node.js", "category": "framework", "patterns": [r"\bnode\.?js\b"]},
    {"name": "React", "category": "framework", "patterns": [r"\breact\b"]},
    {"name": "Vue", "category": "framework", "patterns": [r"\bvue\b", r"\bvue\.js\b"]},
    {"name": "AWS", "category": "cloud", "patterns": [r"\baws\b", r"amazon web services"]},
    {"name": "GCP", "category": "cloud", "patterns": [r"\bgcp\b", r"google cloud"]},
    {"name": "Azure", "category": "cloud", "patterns": [r"\bazure\b"]},
    {"name": "Docker", "category": "tool", "patterns": [r"\bdocker\b"]},
    {"name": "Kubernetes", "category": "tool", "patterns": [r"\bkubernetes\b", r"\bk8s\b"]},
    {"name": "Terraform", "category": "tool", "patterns": [r"\bterraform\b"]},
    {"name": "PostgreSQL", "category": "database", "patterns": [r"\bpostgresql\b", r"\bpostgres\b"]},
    {"name": "MySQL", "category": "database", "patterns": [r"\bmysql\b"]},
    {"name": "MongoDB", "category": "database", "patterns": [r"\bmongodb\b"]},
    {"name": "Redis", "category": "database", "patterns": [r"\bredis\b"]},
    {"name": "REST APIs", "category": "architecture", "patterns": [r"\brest(?:ful)? api[s]?\b", r"\brest services?\b"]},
    {"name": "GraphQL", "category": "architecture", "patterns": [r"\bgraphql\b"]},
    {"name": "Microservices", "category": "architecture", "patterns": [r"\bmicroservices?\b"]},
    {"name": "Distributed Systems", "category": "architecture", "patterns": [r"\bdistributed systems?\b"]},
    {"name": "Event-Driven Systems", "category": "architecture", "patterns": [r"\bevent[- ]driven systems?\b"]},
    {"name": "System Design", "category": "architecture", "patterns": [r"\bsystem design\b"]},
    {"name": "CI/CD", "category": "methodology", "patterns": [r"\bci\s*/\s*cd\b", r"\bcontinuous integration\b", r"\bcontinuous delivery\b", r"\bcontinuous deployment\b"]},
    {"name": "Agile", "category": "methodology", "patterns": [r"\bagile\b", r"\bscrum\b"]},
    {"name": "Data Pipelines", "category": "data", "patterns": [r"\bdata pipelines?\b", r"\betl\b"]},
    {"name": "Airflow", "category": "data", "patterns": [r"\bairflow\b"]},
    {"name": "Spark", "category": "data", "patterns": [r"\bspark\b", r"\bapache spark\b"]},
    {"name": "Kafka", "category": "data", "patterns": [r"\bkafka\b", r"\bapache kafka\b"]},
    {"name": "Machine Learning", "category": "ml", "patterns": [r"\bmachine learning\b"]},
    {"name": "LLMs", "category": "ml", "patterns": [r"\bllms?\b", r"\blarge language models?\b"]},
    {"name": "MLOps", "category": "ml", "patterns": [r"\bmlops\b"]},
]

_ROLE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "backend_engineer",
        "label": "Backend Engineer",
        "patterns": [r"\bbackend engineer\b", r"\bsoftware engineer\b", r"\bplatform engineer\b", r"\bapi\b"],
        "priority_skills": [
            "Python",
            "Java",
            "Go",
            "FastAPI",
            "Django",
            "AWS",
            "Docker",
            "Kubernetes",
            "CI/CD",
            "Terraform",
            "REST APIs",
            "Microservices",
            "Distributed Systems",
            "PostgreSQL",
        ],
    },
    {
        "id": "data_engineer",
        "label": "Data Engineer",
        "patterns": [r"\bdata engineer\b", r"\bdata platform\b", r"\bdata pipelines?\b", r"\betl\b"],
        "priority_skills": [
            "Python",
            "SQL",
            "AWS",
            "Spark",
            "Airflow",
            "Kafka",
            "Data Pipelines",
            "Docker",
            "CI/CD",
            "Terraform",
            "PostgreSQL",
        ],
    },
    {
        "id": "ml_engineer",
        "label": "ML Engineer",
        "patterns": [r"\bml engineer\b", r"\bmachine learning engineer\b", r"\bai engineer\b"],
        "priority_skills": [
            "Python",
            "Machine Learning",
            "LLMs",
            "AWS",
            "Docker",
            "Kubernetes",
            "MLOps",
            "CI/CD",
            "Data Pipelines",
        ],
    },
    {
        "id": "frontend_engineer",
        "label": "Frontend Engineer",
        "patterns": [r"\bfrontend engineer\b", r"\bfront-end engineer\b", r"\bui engineer\b"],
        "priority_skills": [
            "JavaScript",
            "TypeScript",
            "React",
            "Vue",
            "Node.js",
            "REST APIs",
            "CI/CD",
        ],
    },
    {
        "id": "devops_engineer",
        "label": "DevOps Engineer",
        "patterns": [r"\bdevops engineer\b", r"\bsite reliability engineer\b", r"\bsre\b", r"\bplatform engineer\b"],
        "priority_skills": [
            "AWS",
            "Docker",
            "Kubernetes",
            "Terraform",
            "CI/CD",
            "Python",
            "Go",
            "System Design",
            "Distributed Systems",
        ],
    },
]


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"https?://\S+|www\.\S+", " ", lowered)
    lowered = re.sub(r"\S+@\S+", " ", lowered)
    lowered = re.sub(r"[^\w\s/\-+.#]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _is_noise_line(line: str) -> bool:
    lowered = _normalize_text(line)
    if not lowered:
        return True
    if lowered.startswith("location "):
        return True
    if any(marker in lowered for marker in _NOISE_MARKERS):
        return True
    if re.search(r"\$\s?\d", lowered):
        return True
    return False


def _split_sections(job_description: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {
        "title": [],
        "summary": [],
        "responsibilities": [],
        "requirements": [],
        "preferred": [],
        "other": [],
    }

    current_section = "summary"
    for index, raw_line in enumerate(job_description.splitlines()):
        line = raw_line.strip()
        if not line or _is_noise_line(line):
            continue

        if index == 0 and len(line.split()) <= 8:
            sections["title"].append(line)
            continue

        normalized = _normalize_text(line)
        matched_section = None
        for section_name, pattern in _SECTION_PATTERNS.items():
            if re.match(pattern, normalized):
                matched_section = section_name
                break

        if matched_section:
            current_section = matched_section
            continue

        sections[current_section].append(line)

    return sections


def detect_role_type(job_description: str) -> Dict[str, str]:
    sections = _split_sections(job_description)
    title = " ".join(sections.get("title", []))
    normalized = _normalize_text(f"{title} {' '.join(sum(sections.values(), []))}")
    scored_roles = []
    for template in _ROLE_TEMPLATES:
        score = 0
        for pattern in template["patterns"]:
            score += len(re.findall(pattern, normalized)) * 2
        for skill_name in template["priority_skills"]:
            if skill_name.lower() in normalized:
                score += 1
        scored_roles.append((score, template))

    scored_roles.sort(key=lambda item: item[0], reverse=True)
    best_score, best_match = scored_roles[0]
    if best_score == 0:
        return {"id": "general_software", "label": "Software Engineer"}
    return {"id": best_match["id"], "label": best_match["label"]}


def get_role_template_skills(role_id: str) -> List[str]:
    for template in _ROLE_TEMPLATES:
        if template["id"] == role_id:
            return list(template["priority_skills"])
    return []


def _suggest_sections(category: str) -> List[str]:
    return list(_CATEGORY_SECTIONS.get(category, ["Experience", "Projects", "Technical Skills"]))


def _score_skill(entry: Dict[str, Any], sections: Dict[str, List[str]], role_id: str) -> Dict[str, Any] | None:
    title_text = _normalize_text(" ".join(sections.get("title", [])))
    summary_text = _normalize_text(" ".join(sections.get("summary", [])))
    responsibility_lines = [_normalize_text(line) for line in sections.get("responsibilities", [])]
    requirement_lines = [_normalize_text(line) for line in sections.get("requirements", [])]
    preferred_lines = [_normalize_text(line) for line in sections.get("preferred", [])]
    other_lines = [_normalize_text(line) for line in sections.get("other", [])]

    title_hits = 0
    requirement_hits = 0
    preferred_hits = 0
    responsibility_hits = 0
    phrase_hits = 0
    total_count = 0

    priority_skills = set(get_role_template_skills(role_id))

    for pattern in entry["patterns"]:
        title_hits += len(re.findall(pattern, title_text))
        total_count += len(re.findall(pattern, summary_text))
        for line in requirement_lines:
            matches = len(re.findall(pattern, line))
            requirement_hits += matches
            total_count += matches
            if matches and any(marker in line for marker in _PHRASE_MARKERS):
                phrase_hits += 1
        for line in preferred_lines:
            matches = len(re.findall(pattern, line))
            preferred_hits += matches
            total_count += matches
        for line in responsibility_lines:
            matches = len(re.findall(pattern, line))
            responsibility_hits += matches
            total_count += matches
            if matches and any(marker in line for marker in _PHRASE_MARKERS):
                phrase_hits += 1
        for line in other_lines:
            total_count += len(re.findall(pattern, line))

    if title_hits + requirement_hits + preferred_hits + responsibility_hits + total_count == 0:
        return None

    repetitions = max(total_count - 1, 0)
    score = (
        title_hits * 5
        + requirement_hits * 4
        + preferred_hits * 2
        + responsibility_hits * 2
        + phrase_hits * 3
        + repetitions * 2
        + (3 if entry["name"] in priority_skills else 0)
    )
    reason_parts = []
    if title_hits:
        reason_parts.append("appears in the title")
    if requirement_hits:
        reason_parts.append("appears in requirements")
    if preferred_hits:
        reason_parts.append("appears in preferred skills")
    if responsibility_hits:
        reason_parts.append("appears in responsibilities")
    if phrase_hits:
        reason_parts.append("appears in experience-style phrases")
    if entry["name"] in priority_skills:
        reason_parts.append("aligned with this role template")
    if not reason_parts:
        reason_parts.append(f"mentioned {total_count} times")

    return {
        "name": entry["name"],
        "category": entry["category"],
        "count": title_hits + requirement_hits + preferred_hits + responsibility_hits + total_count,
        "score": score,
        "reason": ", ".join(reason_parts).capitalize() + ".",
        "suggested_sections": _suggest_sections(entry["category"]),
    }


def analyze_job_description(job_description: str, limit: int = 10) -> Dict[str, Any]:
    if not job_description.strip():
        return {
            "role_type": {"id": "general_software", "label": "Software Engineer"},
            "title": "",
            "cleaned_text": "",
            "sections": {},
            "skills": [],
        }

    sections = _split_sections(job_description)
    role_type = detect_role_type(job_description)
    ranked_skills: List[Dict[str, Any]] = []
    for entry in _SKILL_LIBRARY:
        ranked = _score_skill(entry, sections, role_type["id"])
        if ranked:
            ranked_skills.append(ranked)

    ranked_skills.sort(key=lambda item: (-item["score"], -item["count"], item["name"]))
    cleaned_lines = [line for section_lines in sections.values() for line in section_lines]

    return {
        "role_type": role_type,
        "title": sections.get("title", [""])[0] if sections.get("title") else "",
        "cleaned_text": "\n".join(cleaned_lines),
        "sections": sections,
        "skills": ranked_skills[:limit],
    }


def extract_resume_skills(resume_text: str) -> List[Dict[str, Any]]:
    return _score_resume_skill_segments(
        [{"label": "resume", "text": resume_text, "weight": 1}],
        reason_template="Found {count} mention{suffix} in the resume.",
    )


def extract_resume_skills_from_document(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not document:
        return []

    segments: List[Dict[str, Any]] = []
    if document.get("title"):
        segments.append({"label": "title", "text": document.get("title", ""), "weight": 3})
    if document.get("summary"):
        segments.append({"label": "summary", "text": document.get("summary", ""), "weight": 2})

    for category, values in (document.get("skills") or {}).items():
        segments.append(
            {
                "label": f"skills:{category}",
                "text": f"{category} {' '.join(values)}",
                "weight": 4,
            }
        )

    for item in document.get("experience") or []:
        segments.append(
            {
                "label": "experience_heading",
                "text": " ".join(
                    part for part in [item.get("role", ""), item.get("company", ""), item.get("date", "")]
                    if part
                ),
                "weight": 2,
            }
        )
        for bullet in item.get("bullets") or []:
            segments.append({"label": "experience_bullet", "text": bullet, "weight": 1})

    for item in document.get("projects") or []:
        segments.append(
            {
                "label": "project_heading",
                "text": " ".join(part for part in [item.get("name", ""), item.get("details", "")] if part),
                "weight": 2,
            }
        )
        for bullet in item.get("bullets") or []:
            segments.append({"label": "project_bullet", "text": bullet, "weight": 1})

    return _score_resume_skill_segments(
        segments,
        reason_template="Found {count} weighted mention{suffix} across structured resume sections.",
    )


def _score_resume_skill_segments(
    segments: List[Dict[str, Any]],
    reason_template: str,
) -> List[Dict[str, Any]]:
    matched_skills: List[Dict[str, Any]] = []
    normalized_segments = [
        {
            "label": segment["label"],
            "text": _normalize_text(str(segment.get("text", ""))),
            "weight": int(segment.get("weight", 1)),
        }
        for segment in segments
        if str(segment.get("text", "")).strip()
    ]

    for entry in _SKILL_LIBRARY:
        count = 0
        score = 0
        sources: List[str] = []
        for segment in normalized_segments:
            segment_hits = 0
            for pattern in entry["patterns"]:
                segment_hits += len(re.findall(pattern, segment["text"]))
            if segment_hits == 0:
                continue
            count += segment_hits
            score += segment_hits * max(segment["weight"], 1)
            sources.append(segment["label"])

        if count == 0:
            continue

        unique_sources = sorted(set(sources))
        reason = reason_template.format(count=count, suffix="s" if count != 1 else "")
        if unique_sources:
            reason = f"{reason} Sources: {', '.join(unique_sources[:3])}."

        matched_skills.append(
            {
                "name": entry["name"],
                "category": entry["category"],
                "count": count,
                "score": score,
                "reason": reason,
                "suggested_sections": _suggest_sections(entry["category"]),
            }
        )

    matched_skills.sort(key=lambda item: (-item["score"], -item["count"], item["name"]))
    return matched_skills


def keyword_names(items: Iterable[Dict[str, Any]]) -> List[str]:
    return [item["name"] for item in items]
