from __future__ import annotations

import unittest

from packages.ai_engine.editor import apply_resume_edit
from packages.resume_formatter.builder import build_resume_document
from packages.shared_types.resume_document import ResumeDocument


class ResumeEditorTests(unittest.TestCase):
    def test_apply_resume_edit_updates_targeted_experience_bullet(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Distributed Systems Engineer | Cloud Data Infrastructure & Scalable Platforms",
                "Experience",
                "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                "- Architected high-scale distributed backend services using AWS Lambda and RDS to process 11M+ records across 30-40 concurrent workers with fault-tolerant orchestration.",
            ]
        )
        document = build_resume_document(resume_text)

        result = apply_resume_edit(
            original_document=document,
            current_document=document,
            instruction="Mention AWS more clearly and keep the scale signal.",
            target={"section": "experience", "entry_index": 0, "bullet_index": 0},
            job_description="Backend Engineer\nRequirements:\n- AWS\n- Distributed Systems",
        )

        updated_document = ResumeDocument.model_validate(result["optimized"]["document"])
        updated_bullet = updated_document.experience[0].bullets[0]

        self.assertIn("AWS", updated_bullet)
        self.assertRegex(updated_bullet, r"11\s?M\+")
        self.assertIn("manual_edit_experience_bullet", result["optimized"]["metadata"]["kept_changes"][0]["action"])
        self.assertIn("score_delta", result["edit"])
        self.assertIn("reason", result["edit"])

    def test_apply_resume_edit_rejects_unsupported_skill_requests(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Experience",
                "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                "- Built backend services using AWS Lambda and RDS.",
            ]
        )
        document = build_resume_document(resume_text)

        with self.assertRaisesRegex(ValueError, "not supported by the current resume"):
            apply_resume_edit(
                original_document=document,
                current_document=document,
                instruction="Add Kubernetes and mention it explicitly.",
                target={"section": "experience", "entry_index": 0, "bullet_index": 0},
                job_description="Backend Engineer\nRequirements:\n- AWS\n- Kubernetes",
            )


if __name__ == "__main__":
    unittest.main()
