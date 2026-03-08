"""Layout-aware resume extraction for PDF and DOCX inputs."""
from __future__ import annotations

from pathlib import Path
from statistics import median
from typing import Any, List

import pdfplumber
from docx import Document

from packages.resume_formatter.normalizer import normalize_resume_line
from packages.shared_types import ResumeLayoutBlock


def extract_layout_blocks(path: Path) -> List[ResumeLayoutBlock]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_layout(path)
    if suffix == ".docx":
        return _extract_docx_layout(path)
    raise ValueError(f"Unsupported resume format: {suffix}")


def blocks_to_text(blocks: List[ResumeLayoutBlock]) -> str:
    return "\n".join(block.text for block in blocks if block.text.strip()).strip()


def _extract_docx_layout(path: Path) -> List[ResumeLayoutBlock]:
    document = Document(path)
    blocks: List[ResumeLayoutBlock] = []

    for index, paragraph in enumerate(document.paragraphs):
        text = normalize_resume_line(paragraph.text)
        if not text:
            continue

        sizes = [
            float(run.font.size.pt)
            for run in paragraph.runs
            if run.text and run.text.strip() and run.font.size is not None
        ]
        is_bold = any(bool(run.bold) for run in paragraph.runs if run.text and run.text.strip())
        style_name = paragraph.style.name if paragraph.style is not None else ""

        blocks.append(
            ResumeLayoutBlock(
                text=text,
                page=1,
                order=len(blocks),
                x0=0.0,
                x1=float(len(text)),
                top=float(index * 14),
                bottom=float(index * 14 + 12),
                font_size=median(sizes) if sizes else 11.0,
                is_bold=is_bold,
                style_name=style_name,
                source="docx",
            )
        )

    return blocks


def _extract_pdf_layout(path: Path) -> List[ResumeLayoutBlock]:
    blocks: List[ResumeLayoutBlock] = []

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_blocks = _extract_pdf_page_blocks(page, page_number, len(blocks))
            if page_blocks:
                blocks.extend(page_blocks)
                continue

            content = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            for raw_line in content.splitlines():
                text = normalize_resume_line(raw_line)
                if not text:
                    continue
                blocks.append(
                    ResumeLayoutBlock(
                        text=text,
                        page=page_number,
                        order=len(blocks),
                        font_size=11.0,
                        source="pdf",
                    )
                )

    return blocks


def _extract_pdf_page_blocks(
    page: pdfplumber.page.Page,
    page_number: int,
    order_start: int,
) -> List[ResumeLayoutBlock]:
    try:
        words = page.extract_words(
            use_text_flow=True,
            keep_blank_chars=False,
            x_tolerance=2,
            y_tolerance=3,
            extra_attrs=["size", "fontname"],
        )
    except Exception:
        return []

    if not words:
        return []

    blocks: List[ResumeLayoutBlock] = []
    current_words: List[dict[str, Any]] = []
    current_top: float | None = None

    sorted_words = sorted(
        words,
        key=lambda item: (
            round(float(item.get("top", 0.0)), 1),
            float(item.get("x0", 0.0)),
        ),
    )

    for word in sorted_words:
        word_top = float(word.get("top", 0.0))
        if current_top is None or abs(word_top - current_top) <= 3:
            current_words.append(word)
            if current_top is None:
                current_top = word_top
            continue

        block = _build_pdf_block(current_words, page_number, order_start + len(blocks))
        if block is not None:
            blocks.append(block)
        current_words = [word]
        current_top = word_top

    if current_words:
        block = _build_pdf_block(current_words, page_number, order_start + len(blocks))
        if block is not None:
            blocks.append(block)

    return blocks


def _build_pdf_block(
    words: List[dict[str, Any]],
    page_number: int,
    order: int,
) -> ResumeLayoutBlock | None:
    if not words:
        return None

    ordered = sorted(words, key=lambda item: float(item.get("x0", 0.0)))
    text = normalize_resume_line(" ".join(str(item.get("text", "")).strip() for item in ordered))
    if not text:
        return None

    sizes = [float(item.get("size", 0.0)) for item in ordered if float(item.get("size", 0.0)) > 0]
    font_names = [str(item.get("fontname", "")) for item in ordered]

    return ResumeLayoutBlock(
        text=text,
        page=page_number,
        order=order,
        x0=min(float(item.get("x0", 0.0)) for item in ordered),
        x1=max(float(item.get("x1", 0.0)) for item in ordered),
        top=min(float(item.get("top", 0.0)) for item in ordered),
        bottom=max(float(item.get("bottom", 0.0)) for item in ordered),
        font_size=median(sizes) if sizes else 11.0,
        is_bold=any("bold" in name.lower() for name in font_names),
        style_name="",
        source="pdf",
    )
