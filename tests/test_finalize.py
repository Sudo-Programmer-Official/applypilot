from __future__ import annotations

import unittest

from packages.ai_engine.finalize import build_output_diagnostics
from packages.ai_engine.fix_engine import apply_resume_fixes
from packages.ai_engine.scorer import score_resume
from packages.ats_score.scorer import calculate_ats_score
from packages.job_intelligence.extractor import analyze_job_description
from packages.readiness_score.scorer import calculate_application_readiness
from packages.resume_formatter import build_resume_document, resume_document_to_text
from packages.shared_types.resume_document import ResumeDocument


class FinalizeDiagnosticsTests(unittest.TestCase):
    def test_build_output_diagnostics_scores_the_final_document(self) -> None:
        original_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Experience",
                "Software Engineer - Example Corp Jan 2022 - Present",
                "- Built backend services for internal teams.",
            ]
        )
        final_document = build_resume_document(
            "\n".join(
                [
                    "ABHISHEK JHA",
                    "Software Engineer",
                    "Technical Skills",
                    "Languages: Python",
                    "Cloud & Infrastructure: AWS",
                    "Experience",
                    "Software Engineer - Example Corp Jan 2022 - Present",
                    "- Built distributed backend services on AWS Lambda for internal teams.",
                ]
            )
        )
        original_document = build_resume_document(original_text)
        job_description = "Backend Engineer\nRequirements:\n- Python\n- AWS\n- Distributed Systems"
        job_intelligence = analyze_job_description(job_description, limit=10)

        diagnostics = build_output_diagnostics(
            original_text=original_text,
            final_document=final_document,
            job_description=job_description,
            original_document=original_document,
            job_skills=job_intelligence["skills"],
            role_info=job_intelligence["role_type"],
        )

        final_text = resume_document_to_text(final_document)
        expected_ats = calculate_ats_score(final_text, job_description)
        expected_readiness = calculate_application_readiness(final_text, job_description)
        expected_score = score_resume(
            final_document,
            job_intelligence["skills"],
            original_document=original_document,
            role_info=job_intelligence["role_type"],
        )

        self.assertEqual(diagnostics["text"], final_text)
        self.assertEqual(diagnostics["ats_score"]["projected_score"], expected_ats["score"])
        self.assertEqual(
            diagnostics["application_readiness"]["projected_score"],
            expected_readiness["score"],
        )
        self.assertEqual(diagnostics["scores"]["optimized"]["total"], expected_score["total"])

    def test_apply_resume_fixes_returns_scores_for_the_finalized_document(self) -> None:
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
        job_description = "Platform Engineer\nRequirements:\n- Bash\n- CI/CD\n- Python"

        result = apply_resume_fixes(
            original_document=document,
            current_document=document,
            job_description=job_description,
        )

        optimized_document = ResumeDocument.model_validate(result["optimized"]["document"])
        optimized_text = resume_document_to_text(optimized_document)
        expected_ats = calculate_ats_score(optimized_text, job_description)
        expected_readiness = calculate_application_readiness(optimized_text, job_description)

        self.assertTrue(result["fixes"]["applied"])
        self.assertEqual(result["optimized"]["text"], optimized_text)
        self.assertEqual(result["ats_score"]["projected_score"], expected_ats["score"])
        self.assertEqual(
            result["application_readiness"]["projected_score"],
            expected_readiness["score"],
        )


if __name__ == "__main__":
    unittest.main()
