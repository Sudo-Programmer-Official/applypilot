from __future__ import annotations

import unittest

from packages.ai_engine.verifier import verify_change
from packages.resume_formatter.builder import build_resume_document


class ResumeVerifierTests(unittest.TestCase):
    def test_verifier_rejects_high_impact_metric_loss_in_bullet_rewrite(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Experience",
                "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                "- Architected distributed backend services on AWS Lambda and RDS to process 11M+ records across 30-40 concurrent workers with fault-tolerant orchestration.",
            ]
        )
        original_document = build_resume_document(resume_text)
        candidate_document = original_document.model_copy(deep=True)
        candidate_document.experience[0].bullets[0] = (
            "Architected distributed backend services on AWS Lambda and RDS to process large datasets across distributed workers."
        )

        verification = verify_change(
            original_document,
            original_document,
            candidate_document,
            {
                "action": "rewrite_experience_bullet",
                "target": {"entry_index": 0, "bullet_index": 0},
                "before_value": original_document.experience[0].bullets[0],
                "after_value": candidate_document.experience[0].bullets[0],
            },
            [
                {"name": "AWS", "category": "cloud", "suggested_sections": []},
                {"name": "Distributed Systems", "category": "architecture", "suggested_sections": []},
            ],
        )

        self.assertFalse(verification["passed"])
        self.assertIn("high_impact_metric_removed", verification["codes"])
        self.assertTrue(any("11M+" in reason or "30-40" in reason for reason in verification["reasons"]))

    def test_verifier_rejects_weaker_first_bullet_even_without_metric_loss(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Experience",
                "Graduate Assistant - Computer Science, TAMU-CC Jan 2025 - May 2025",
                "- Built an LLM-powered requirement traceability system using semantic similarity scoring to map functional and quality requirements.",
            ]
        )
        original_document = build_resume_document(resume_text)
        candidate_document = original_document.model_copy(deep=True)
        candidate_document.experience[0].bullets[0] = "Worked on an AI requirement mapping tool for the team."

        verification = verify_change(
            original_document,
            original_document,
            candidate_document,
            {
                "action": "rewrite_experience_bullet",
                "target": {"entry_index": 0, "bullet_index": 0},
                "before_value": original_document.experience[0].bullets[0],
                "after_value": candidate_document.experience[0].bullets[0],
            },
            [
                {"name": "LLMs", "category": "ml", "suggested_sections": []},
                {"name": "Distributed Systems", "category": "architecture", "suggested_sections": []},
            ],
        )

        self.assertFalse(verification["passed"])
        self.assertIn("first_bullet_weakened", verification["codes"])


if __name__ == "__main__":
    unittest.main()
