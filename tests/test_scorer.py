from __future__ import annotations

import unittest

from packages.ai_engine.scorer import score_resume
from packages.resume_formatter.builder import build_resume_document


class ResumeScorerTests(unittest.TestCase):
    def test_scorer_rewards_keyword_alignment_in_first_bullet(self) -> None:
        skills_only_resume = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Technical Skills",
                "Cloud & Infrastructure: AWS",
                "Experience",
                "Software Engineer - Example Corp Jan 2023 - Present",
                "- Built backend services for internal systems.",
            ]
        )
        first_bullet_resume = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Technical Skills",
                "Cloud & Infrastructure: AWS",
                "Experience",
                "Software Engineer - Example Corp Jan 2023 - Present",
                "- Architected distributed backend services on AWS to support production APIs.",
            ]
        )

        job_skills = [
            {"name": "AWS", "category": "cloud", "suggested_sections": []},
            {"name": "Distributed Systems", "category": "architecture", "suggested_sections": []},
        ]

        skills_only_score = score_resume(build_resume_document(skills_only_resume), job_skills)
        first_bullet_score = score_resume(build_resume_document(first_bullet_resume), job_skills)

        self.assertGreater(
            first_bullet_score["axes"]["jd_keyword_match"],
            skills_only_score["axes"]["jd_keyword_match"],
        )
        self.assertGreater(
            first_bullet_score["axes"]["technical_strength"],
            skills_only_score["axes"]["technical_strength"],
        )
        self.assertTrue(
            any(match["keyword"] == "AWS" for match in first_bullet_score["keyword_analysis"]["strong_matches"])
        )
        self.assertTrue(
            any(match["keyword"] == "AWS" for match in skills_only_score["keyword_analysis"]["weak_matches"])
        )

    def test_scorer_returns_recruiter_scan_axes(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Distributed Systems Engineer",
                "Distributed systems engineer building scalable backend services for cloud workloads.",
                "Technical Skills",
                "Cloud & Infrastructure: AWS, Docker",
                "Experience",
                "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                "- Architected distributed backend services on AWS Lambda and RDS to process 11M+ records across 30-40 concurrent workers.",
            ]
        )

        score = score_resume(
            build_resume_document(resume_text),
            [
                {"name": "AWS", "category": "cloud", "suggested_sections": []},
                {"name": "Distributed Systems", "category": "architecture", "suggested_sections": []},
            ],
        )

        self.assertIn("jd_keyword_match", score["axes"])
        self.assertIn("metric_impact", score["axes"])
        self.assertIn("technical_strength", score["axes"])
        self.assertIn("technology_density", score["axes"])
        self.assertIn("action_verb_strength", score["axes"])
        self.assertIn("readability", score["axes"])
        self.assertIn("keyword_analysis", score)

    def test_scorer_reports_missing_keywords_when_context_is_absent(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Technical Skills",
                "Cloud & Infrastructure: AWS",
                "Experience",
                "Software Engineer - Example Corp Jan 2023 - Present",
                "- Built backend APIs for internal tools.",
            ]
        )

        score = score_resume(
            build_resume_document(resume_text),
            [
                {"name": "AWS", "category": "cloud", "suggested_sections": []},
                {"name": "Distributed Systems", "category": "architecture", "suggested_sections": []},
                {"name": "Event-Driven Systems", "category": "architecture", "suggested_sections": []},
            ],
        )

        self.assertIn("Distributed Systems", score["keyword_analysis"]["missing_keywords"])
        self.assertIn("Event-Driven Systems", score["keyword_analysis"]["missing_keywords"])


if __name__ == "__main__":
    unittest.main()
