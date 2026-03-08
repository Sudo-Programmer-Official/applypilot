"""Resume parsing utilities for PDF and DOCX inputs."""
from pathlib import Path
from typing import Any, Dict, List

from packages.resume_formatter.builder import build_resume_document, summarize_resume_sections
from packages.resume_parser.layout import blocks_to_text, extract_layout_blocks

PARSER_VERSION = "layout_v1"


def parse_resume(file_path: str) -> Dict[str, Any]:
    """
    Parse a resume file (PDF or DOCX) and return extracted text plus sections.

    Returns:
        {
            "file_name": "...",
            "text": "...",
            "sections": [...],
            "metadata": {...},
        }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume not found at {path}")

    suffix = path.suffix.lower()
    layout_blocks = extract_layout_blocks(path)
    text = blocks_to_text(layout_blocks)
    document = build_resume_document(text, layout_blocks=layout_blocks)

    return {
        "file_name": path.name,
        "text": text,
        "sections": _extract_sections(document),
        "document": document.model_dump(),
        "metadata": {
            "format": suffix.lstrip("."),
            "parser_mode": "layout_aware",
            "parser_version": PARSER_VERSION,
            "layout_block_count": len(layout_blocks),
        },
    }


def _extract_sections(document: Any) -> List[Dict[str, Any]]:
    """Summarize the structured resume sections for downstream consumers."""
    return summarize_resume_sections(document)
