"""Whitespace-safe normalization for resume text extracted from uploads."""
from __future__ import annotations

import re

_CANONICAL_TOKEN_PATTERNS = (
    (re.compile(r"\bOpen\s*AI\b", re.IGNORECASE), "OpenAI"),
    (re.compile(r"\bGit\s*Hub\b", re.IGNORECASE), "GitHub"),
    (re.compile(r"\bLinked\s*In\b", re.IGNORECASE), "LinkedIn"),
    (re.compile(r"\bTensor\s*Flow\b", re.IGNORECASE), "TensorFlow"),
    (re.compile(r"\bType\s*Script\b", re.IGNORECASE), "TypeScript"),
    (re.compile(r"\bJava\s*Script\b", re.IGNORECASE), "JavaScript"),
    (re.compile(r"\bPostgre\s*SQL\b", re.IGNORECASE), "PostgreSQL"),
    (re.compile(r"\bMy\s*SQL\b", re.IGNORECASE), "MySQL"),
    (re.compile(r"\bFast\s*API\b", re.IGNORECASE), "FastAPI"),
    (re.compile(r"\bPy\s*Torch\b", re.IGNORECASE), "PyTorch"),
    (re.compile(r"\bNum\s*Py\b", re.IGNORECASE), "NumPy"),
    (re.compile(r"\bGraph\s*QL\b", re.IGNORECASE), "GraphQL"),
    (re.compile(r"\bAP\s*I\b"), "API"),
    (re.compile(r"\bAP\s*Is\b"), "APIs"),
    (re.compile(r"\bREST\s*AP(?:\s*I)?s\b", re.IGNORECASE), "REST APIs"),
    (re.compile(r"\bNode\s*\.?\s*js\b", re.IGNORECASE), "Node.js"),
    (re.compile(r"\bNext\s*\.?\s*js\b", re.IGNORECASE), "Next.js"),
    (re.compile(r"\bVue\s*\.?\s*js\b", re.IGNORECASE), "Vue.js"),
    (re.compile(r"\bCI\s*/\s*CD\b", re.IGNORECASE), "CI/CD"),
    (re.compile(r"\bC\s*\+\s*\+\b"), "C++"),
    (re.compile(r"\bA\s*&\s*M\b", re.IGNORECASE), "A&M"),
    (re.compile(r"\bPrompt\s*driven\b", re.IGNORECASE), "Prompt-driven"),
)

_PROTECTED_TOKEN_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.\w+|linkedin\.com/\S+|github\.com/\S+)",
    re.IGNORECASE,
)


def normalize_resume_text(text: str) -> str:
    lines = [normalize_resume_line(line) for line in (text or "").splitlines()]
    normalized_lines: list[str] = []
    blank_streak = 0

    for line in lines:
        if not line:
            blank_streak += 1
            if blank_streak <= 1:
                normalized_lines.append("")
            continue
        blank_streak = 0
        normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def normalize_resume_line(line: str) -> str:
    if not line:
        return ""

    text = line.replace("\xa0", " ").replace("\uf0b7", "•").strip()
    if not text:
        return ""

    protected_tokens: list[str] = []

    def _protect(match: re.Match[str]) -> str:
        protected_tokens.append(match.group(0))
        return f"__TOKEN_{len(protected_tokens) - 1}__"

    text = _PROTECTED_TOKEN_PATTERN.sub(_protect, text)
    text = re.sub(r"\s*\|\s*", " | ", text)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"(?<=[a-z])&(?=[A-Z])", " & ", text)
    text = re.sub(r"(?<=\s)-(?=[A-Z][A-Za-z])", "- ", text)
    text = re.sub(r"(?<=[A-Za-z])-(?=[A-Z][A-Za-z])", " - ", text)
    text = re.sub(r"(?<=[,;:])(?=[^\s])", " ", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    text = _restore_canonical_tokens(text)

    for index, token in enumerate(protected_tokens):
        text = text.replace(f"__TOKEN_{index}__", token)

    return text


def _restore_canonical_tokens(text: str) -> str:
    restored = text
    for pattern, replacement in _CANONICAL_TOKEN_PATTERNS:
        restored = pattern.sub(replacement, restored)
    return restored
