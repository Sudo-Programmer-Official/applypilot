from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from packages.resume_formatter.builder import build_resume_document
from packages.resume_formatter.normalizer import normalize_resume_line, normalize_resume_text
from packages.resume_parser.layout import extract_layout_blocks
from packages.resume_parser.parser import parse_resume

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "resumes"


class ResumeNormalizerTests(unittest.TestCase):
    def test_restores_spacing_and_protected_tokens(self) -> None:
        line = (
            "DistributedSystemsEngineer|CloudDataInfrastructure&ScalablePlatforms "
            "Open AI Git Hub Linked In Tensor Flow Type Script Java Script Postgre SQL "
            "Node js CI / CD C + + Fast API AP Is"
        )

        normalized = normalize_resume_line(line)

        self.assertIn(
            "Distributed Systems Engineer | Cloud Data Infrastructure & Scalable Platforms",
            normalized,
        )
        self.assertIn("OpenAI", normalized)
        self.assertIn("GitHub", normalized)
        self.assertIn("LinkedIn", normalized)
        self.assertIn("TensorFlow", normalized)
        self.assertIn("TypeScript", normalized)
        self.assertIn("JavaScript", normalized)
        self.assertIn("PostgreSQL", normalized)
        self.assertIn("Node.js", normalized)
        self.assertIn("CI/CD", normalized)
        self.assertIn("FastAPI", normalized)
        self.assertIn("APIs", normalized)

    def test_normalize_resume_text_collapses_blank_lines_only(self) -> None:
        text = "ABHISHEK JHA\n\n\nTechnicalSkills\nPython"
        normalized = normalize_resume_text(text)
        self.assertEqual(normalized, "ABHISHEK JHA\n\nTechnical Skills\nPython")


class ResumeBuilderTests(unittest.TestCase):
    def test_detects_compact_section_headers(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "BackendEngineer",
                "abhishek@example.com | linkedin.com/in/abhishek-jha-ai",
                "TechnicalSkills",
                "Languages: Python, TypeScript",
                "ProfessionalExperience",
                "SoftwareEngineer - Example May 2025 - Present",
                "- Built APIs using FastAPI and PostgreSQL",
                "SelectedProjects",
                "ApplyPilot: Resume intelligence platform",
                "Publications",
                "ScalingDistributedSystems: Paper accepted at ExampleConf",
            ]
        )

        document = build_resume_document(resume_text)

        self.assertEqual(document.title, "Backend Engineer")
        self.assertIn("Languages", document.skills)
        self.assertEqual(len(document.experience), 1)
        self.assertEqual(document.experience[0].role, "Software Engineer")
        self.assertGreaterEqual(len(document.projects), 2)


class ResumeParserTests(unittest.TestCase):
    def test_parse_docx_fixture_preserves_structure(self) -> None:
        result = parse_resume(str(FIXTURE_DIR / "compact_resume.docx"))

        self.assertIn("Backend Engineer", result["text"])
        self.assertEqual(result["metadata"]["format"], "docx")
        self.assertEqual(result["metadata"]["parser_mode"], "layout_aware")
        self.assertEqual(result["metadata"]["parser_version"], "layout_v1")
        self.assertGreater(result["metadata"]["layout_block_count"], 0)
        self.assertIn("Frameworks", result["document"]["skills"])
        self.assertEqual(result["document"]["experience"][0]["role"], "Software Engineer")
        self.assertEqual(result["document"]["experience"][0]["company"], "Example Labs")
        self.assertEqual(result["document"]["experience"][0]["start_date"], "Jan 2022")
        self.assertEqual(result["document"]["experience"][0]["end_date"], "Present")

    def test_parse_pdf_fixture_preserves_canonical_tokens(self) -> None:
        result = parse_resume(str(FIXTURE_DIR / "backend_layout_resume.pdf"))

        self.assertIn("Distributed Systems Engineer | Cloud Data Infrastructure & Scalable Platforms", result["text"])
        self.assertIn("Texas A&M University Corpus Christi", result["text"])
        self.assertIn("CI/CD", result["text"])
        self.assertEqual(result["metadata"]["parser_mode"], "layout_aware")
        self.assertGreater(result["metadata"]["layout_block_count"], 0)
        self.assertEqual(result["document"]["experience"][0]["role"], "Software Engineering Intern")
        self.assertEqual(result["document"]["experience"][0]["company"], "Braintree Health")
        self.assertEqual(result["document"]["experience"][1]["company"], "Accenture")

    def test_extract_layout_blocks_captures_pdf_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "resume.pdf"
            pdf = canvas.Canvas(str(path), pagesize=letter)
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(72, 760, "Experience")
            pdf.setFont("Helvetica", 11)
            pdf.drawString(72, 742, "Software Engineer - Example May 2025 - Present")
            pdf.save()

            blocks = extract_layout_blocks(path)

        self.assertGreaterEqual(len(blocks), 2)
        self.assertEqual(blocks[0].text, "Experience")
        self.assertGreater(blocks[0].font_size, blocks[1].font_size)
        self.assertTrue(blocks[0].is_bold)


if __name__ == "__main__":
    unittest.main()
