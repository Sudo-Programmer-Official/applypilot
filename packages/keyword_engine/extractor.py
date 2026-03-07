"""Keyword extraction utilities for job descriptions and resumes."""
from __future__ import annotations

import re
from typing import List, Set

# Minimal stopword list to reduce noise; keep small to avoid heavy deps.
_STOPWORDS: Set[str] = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "your",
    "you",
    "are",
    "our",
    "will",
    "have",
    "has",
    "on",
    "in",
    "of",
    "to",
    "a",
    "an",
}


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract de-duplicated keywords from text using simple heuristics."""
    if not text:
        return []

    tokens = re.findall(r"[A-Za-z0-9+#\.\-]{2,}", text.lower())
    keywords: Set[str] = set()
    for tok in tokens:
        if len(tok) < min_length:
            continue
        if tok in _STOPWORDS:
            continue
        keywords.add(tok)

    return sorted(keywords)
