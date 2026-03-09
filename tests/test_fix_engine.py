from __future__ import annotations

import unittest
from unittest import mock

from packages.ai_engine.fix_engine import apply_resume_fixes
from packages.resume_formatter.builder import build_resume_document
from packages.shared_types.resume_document import ResumeDocument


class FixEngineTests(unittest.TestCase):
    def test_fix_engine_injects_machine_learning_and_improves_ats(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Technical Skills",
                "Languages: Python",
                "Experience",
                "Graduate Assistant - Computer Science, TAMU-CC Jan 2025 - May 2025",
                "- Built an LLM-powered requirement traceability system with semantic similarity scoring, improving mapping accuracy by 18%.",
            ]
        )
        document = build_resume_document(resume_text)

        result = apply_resume_fixes(
            original_document=document,
            current_document=document,
            job_description="ML Engineer\nRequirements:\n- Machine Learning\n- AI Systems\n- Python",
        )

        updated_document = ResumeDocument.model_validate(result["optimized"]["document"])
        updated_bullet = updated_document.experience[0].bullets[0]

        self.assertIn("machine learning", updated_bullet.lower())
        self.assertRegex(updated_bullet, r"18%")
        self.assertGreater(result["ats_score"]["projected_score"], result["ats_score"]["score"])
        self.assertTrue(result["fixes"]["applied"])

    def test_fix_engine_surfaces_bash_without_removing_metrics(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Technical Skills",
                "Languages: Python",
                "Experience",
                "Senior Software Engineer - Example Corp Jan 2022 - Present",
                "- Automated CI/CD workflows, reducing deployment effort by 40%.",
            ]
        )
        document = build_resume_document(resume_text)

        result = apply_resume_fixes(
            original_document=document,
            current_document=document,
            job_description="Platform Engineer\nRequirements:\n- Bash\n- CI/CD\n- Python",
        )

        updated_document = ResumeDocument.model_validate(result["optimized"]["document"])
        updated_bullet = updated_document.experience[0].bullets[0]

        self.assertIn("bash", updated_bullet.lower())
        self.assertRegex(updated_bullet, r"40%")
        self.assertGreater(result["ats_score"]["projected_score"], result["ats_score"]["score"])

    def test_fix_engine_verifier_rejects_unsafe_candidate(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Experience",
                "Graduate Assistant - Computer Science, TAMU-CC Jan 2025 - May 2025",
                "- Built an LLM-powered requirement traceability system with semantic similarity scoring, improving mapping accuracy by 18%.",
            ]
        )
        document = build_resume_document(resume_text)

        with mock.patch(
            "packages.ai_engine.fix_engine._inject_phrase_into_bullet",
            return_value="Built an LLM-powered requirement traceability system.",
        ):
            result = apply_resume_fixes(
                original_document=document,
                current_document=document,
                job_description="ML Engineer\nRequirements:\n- Machine Learning\n- Python",
            )

        self.assertFalse(result["fixes"]["applied"])
        self.assertTrue(
            any(
                keyword in reason.lower()
                for reason in result["fixes"]["rejected"]
                for keyword in ("metric", "technical specificity", "first bullet")
            )
        )


if __name__ == "__main__":
    unittest.main()
