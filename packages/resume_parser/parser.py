"""Resume parsing utilities for PDF and DOCX inputs."""
from pathlib import Path
from typing import Any, Dict, List

import pdfplumber
from docx import Document
from packages.resume_formatter.builder import build_resume_document, summarize_resume_sections


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
    if suffix == ".pdf":
        text = _parse_pdf(path)
    elif suffix == ".docx":
        text = _parse_docx(path)
    else:
        raise ValueError(f"Unsupported resume format: {suffix}")

    document = build_resume_document(text)

    return {
        "file_name": path.name,
        "text": text,
        "sections": _extract_sections(document),
        "document": document.model_dump(),
        "metadata": {"format": suffix.lstrip(".")},
    }


def _parse_pdf(path: Path) -> str:
    """Extract plain text from a PDF using pdfplumber."""
    lines: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            content = page.extract_text() or ""
            if content:
                lines.append(content.strip())
    return "\n".join(lines).strip()


def _parse_docx(path: Path) -> str:
    """Extract plain text from a DOCX using python-docx."""
    doc = Document(path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(lines).strip()


def _extract_sections(document: Any) -> List[Dict[str, Any]]:
    """Summarize the structured resume sections for downstream consumers."""
    return summarize_resume_sections(document)
