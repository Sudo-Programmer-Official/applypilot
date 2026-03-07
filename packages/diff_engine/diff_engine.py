"""Stub diff engine using Python's difflib.

Generates a unified diff between original and optimized resume text.
"""
import difflib
from typing import Iterable


def generate_diff(original_text: str, optimized_text: str) -> str:
    """Return a unified diff string comparing the two text inputs."""
    original_lines: Iterable[str] = original_text.splitlines(keepends=True)
    optimized_lines: Iterable[str] = optimized_text.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines,
        optimized_lines,
        fromfile="original",
        tofile="optimized",
        lineterm="",
    )
    return "\n".join(diff)
