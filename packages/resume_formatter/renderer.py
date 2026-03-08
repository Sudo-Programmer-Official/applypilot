"""Render structured resumes into an ATS-safe PDF."""
from __future__ import annotations

import re
import textwrap
from ctypes.util import find_library
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple
from xml.sax.saxutils import escape

from jinja2 import Environment, FileSystemLoader, select_autoescape

from packages.shared_types.resume_document import ResumeDocument

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

_COMPACT_OVERRIDES = """
@page { margin: 0.42in; }
body { font-size: 11px; line-height: 1.22; }
.name { font-size: 24px; }
.summary { margin-bottom: 12px; }
.section { margin-top: 12px; }
ul { margin-top: 4px; }
li { margin-bottom: 2px; }
"""

_WEASYPRINT_NATIVE_CHECK: bool | None = None


def render_resume_pdf(document: ResumeDocument) -> Tuple[bytes, ResumeDocument, Dict[str, int]]:
    rendered_document = document
    pdf_bytes, page_count, used_fallback = _render_document(rendered_document)

    if page_count > 1:
        rendered_document = _compact_document(document)
        pdf_bytes, page_count, used_fallback = _render_document(rendered_document, compact=True)

    return pdf_bytes, rendered_document, {"page_count": page_count, "fallback": int(used_fallback)}


def _render_document(document: ResumeDocument, compact: bool = False) -> Tuple[bytes, int, bool]:
    if not _weasyprint_is_usable():
        pdf_bytes = _render_with_reportlab(document, compact=compact)
        return pdf_bytes, 1, True

    try:
        from weasyprint import CSS, HTML
    except Exception:
        pdf_bytes = _render_with_reportlab(document, compact=compact)
        return pdf_bytes, 1, True

    try:
        template = _ENV.get_template("classic_resume.html")
        html_string = template.render(resume=document)
        css_path = _TEMPLATE_DIR / "classic_resume.css"
        css_text = css_path.read_text(encoding="utf-8")
        if compact:
            css_text = f"{css_text}\n{_COMPACT_OVERRIDES}"

        rendered = HTML(string=html_string, base_url=str(_TEMPLATE_DIR)).render(
            stylesheets=[CSS(string=css_text)]
        )
        return rendered.write_pdf(), len(rendered.pages), False
    except Exception:
        pdf_bytes = _render_with_reportlab(document, compact=compact)
        return pdf_bytes, 1, True


def _compact_document(document: ResumeDocument) -> ResumeDocument:
    compact = document.model_copy(deep=True)
    compact.education = compact.education[:2]
    compact.skills = {category: values[:8] for category, values in compact.skills.items()}
    compact.experience = compact.experience[:4]
    for item in compact.experience:
        item.bullets = item.bullets[:4]
    compact.projects = compact.projects[:2]
    for item in compact.projects:
        item.bullets = item.bullets[:2]
    return compact


def _weasyprint_is_usable() -> bool:
    global _WEASYPRINT_NATIVE_CHECK

    if _WEASYPRINT_NATIVE_CHECK is not None:
        return _WEASYPRINT_NATIVE_CHECK

    required_libraries = ("gobject-2.0", "pango-1.0")
    _WEASYPRINT_NATIVE_CHECK = all(find_library(name) for name in required_libraries)
    return _WEASYPRINT_NATIVE_CHECK


def _render_with_reportlab(document: ResumeDocument, compact: bool = False) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
    except Exception as exc:
        raise RuntimeError("PDF export requires WeasyPrint or ReportLab to be installed.") from exc

    styles = getSampleStyleSheet()
    base_font = 10.4 if compact else 10.8
    section_gap = 8 if compact else 10
    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=base_font,
        leading=12 if compact else 13,
        spaceAfter=2,
        alignment=TA_LEFT,
        splitLongWords=0,
        embeddedHyphenation=0,
        wordWrap="LTR",
    )
    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=body_style,
        leftIndent=16,
        firstLineIndent=0,
        bulletIndent=0,
        spaceBefore=0,
        spaceAfter=2,
    )
    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=19 if compact else 21,
        leading=22 if compact else 24,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    title_style = ParagraphStyle(
        "ResumeTitle",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=11.3 if compact else 11.8,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    centered_body = ParagraphStyle(
        "ResumeCenteredBody",
        parent=body_style,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    summary_style = ParagraphStyle(
        "ResumeSummary",
        parent=body_style,
        fontName="Helvetica-Oblique",
        alignment=TA_CENTER,
        spaceAfter=section_gap,
    )
    section_style = ParagraphStyle(
        "ResumeSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13.5 if compact else 14.5,
        leading=16,
        spaceBefore=section_gap,
        spaceAfter=5,
        borderWidth=0,
        borderPadding=0,
        borderColor=colors.HexColor("#9CA3AF"),
        borderBottomWidth=0.6,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.48 * inch if compact else 0.55 * inch,
        rightMargin=0.48 * inch if compact else 0.55 * inch,
        topMargin=0.45 * inch if compact else 0.55 * inch,
        bottomMargin=0.45 * inch if compact else 0.55 * inch,
    )

    flow = []
    flow.append(Paragraph(escape(document.name or "Candidate"), name_style))
    if document.title:
        flow.append(Paragraph(escape(document.title), title_style))
    if document.contact_items:
        flow.append(Paragraph(escape(" | ".join(document.contact_items)), centered_body))
    if document.summary:
        flow.append(Paragraph(escape(document.summary), summary_style))

    if document.education:
        flow.append(Paragraph("Education", section_style))
        for entry in document.education:
            flow.extend(_build_entry_block(
                left_html=_education_left(entry),
                right_text=entry.date,
                bullets=entry.details,
                body_style=body_style,
                bullet_style=bullet_style,
                table_cls=Table,
                paragraph_cls=Paragraph,
                spacer_cls=Spacer,
                compact=compact,
            ))

    if document.skills:
        flow.append(Paragraph("Technical Skills", section_style))
        for category, values in document.skills.items():
            skill_line = _build_wrapped_skill_html(category, values, width=92 if compact else 102)
            flow.append(Paragraph(skill_line, body_style))

    if document.experience:
        flow.append(Paragraph("Experience", section_style))
        for entry in document.experience:
            left_html = f"<b>{escape(entry.role)}</b>"
            if entry.company:
                left_html = f"{left_html} - {escape(entry.company)}"
            flow.extend(_build_entry_block(
                left_html=left_html,
                right_text=entry.date,
                bullets=entry.bullets,
                body_style=body_style,
                bullet_style=bullet_style,
                table_cls=Table,
                paragraph_cls=Paragraph,
                spacer_cls=Spacer,
                compact=compact,
            ))

    if document.projects:
        flow.append(Paragraph("Selected Projects", section_style))
        for entry in document.projects:
            left_html = f"<b>{escape(entry.name)}</b>"
            if entry.details:
                left_html = f"{left_html}: {escape(entry.details)}"
            flow.extend(_build_entry_block(
                left_html=left_html,
                right_text="",
                bullets=entry.bullets,
                body_style=body_style,
                bullet_style=bullet_style,
                table_cls=Table,
                paragraph_cls=Paragraph,
                spacer_cls=Spacer,
                compact=compact,
            ))

    doc.build(flow)
    return buffer.getvalue()


def _education_left(entry) -> str:
    left_html = f"<b>{escape(entry.school)}</b>"
    if entry.degree:
        left_html = f"{left_html}, {escape(entry.degree)}"
    return left_html


def _build_entry_block(left_html, right_text, bullets, body_style, bullet_style, table_cls, paragraph_cls, spacer_cls, compact=False):
    block = []
    row = table_cls(
        [[paragraph_cls(left_html, body_style), paragraph_cls(escape(right_text), body_style)]],
        colWidths=[402 if compact else 394, 108 if compact else 116],
        hAlign="LEFT",
    )
    row.setStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    block.append(row)

    if bullets:
        for bullet in bullets:
            block.append(_build_bullet_paragraph(bullet, bullet_style, paragraph_cls, width=90 if compact else 98))

    block.append(spacer_cls(1, 4))
    return block


def _build_bullet_paragraph(text: str, bullet_style, paragraph_cls, width: int):
    wrapped_lines = _wrap_resume_text(text, width)
    html = "<br/>".join(escape(line) for line in wrapped_lines)
    return paragraph_cls(html, bullet_style, bulletText="•")


def _build_wrapped_skill_html(category: str, values: list[str], width: int) -> str:
    prefix_width = max(width - len(category) - 2, 36)
    wrapped_values = _wrap_resume_text(", ".join(values), prefix_width)
    if not wrapped_values:
        return f"<b>{escape(category)}:</b>"
    first_line = f"<b>{escape(category)}:</b> {escape(wrapped_values[0])}"
    continuation = "".join(f"<br/>{escape(line)}" for line in wrapped_values[1:])
    return f"{first_line}{continuation}"


def _wrap_resume_text(text: str, width: int) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return [""]
    return textwrap.wrap(
        cleaned,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [cleaned]
