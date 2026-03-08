from __future__ import annotations

import unittest

from packages.ai_engine.humanizer import ai_footprint_score, humanize_bullet, humanize_experience_bullets
from packages.resume_formatter.builder import build_resume_document


class HumanizerTests(unittest.TestCase):
    def test_ai_footprint_score_flags_banned_phrases(self) -> None:
        text = "Built scalable services using reliability, improving delivery quality through cutting-edge innovation."
        score = ai_footprint_score(text, {"delivery quality"})
        self.assertGreaterEqual(score, 7)

    def test_humanizer_rewrites_known_backend_bullets_without_inventing_tools(self) -> None:
        document = build_resume_document(
            "\n".join(
                [
                    "ABHISHEK JHA",
                    "Experience",
                    "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                    "- Improved service throughput and latency by implementing workload sharding, parallel execution strategies, and advanced SQL indexing - reducing runtime from multi-week cycles to 1.5 hours.",
                    "- Resolved database deadlocks and write-contention issues under concurrent load by redesigning indexing strategy and optimizing transactional boundaries.",
                ]
            )
        )

        changes = humanize_experience_bullets(document)

        self.assertEqual(changes, 2)
        self.assertIn("workload sharding, parallel execution, and SQL indexing optimization", document.experience[0].bullets[0])
        self.assertNotIn("Machine Learning", document.experience[0].bullets[0])
        self.assertIn("transactional boundaries", document.experience[0].bullets[1])

    def test_humanize_bullet_removes_repeated_filler(self) -> None:
        document = build_resume_document(
            "\n".join(
                [
                    "ABHISHEK JHA",
                    "Experience",
                    "Senior Software Engineer - Example Corp Jan 2022 - Present",
                    "- Collaborated across backend, product, and infrastructure teams to deliver scalable feature releases using reliability, improving delivery quality.",
                ]
            )
        )
        entry = document.experience[0]

        rewritten = humanize_bullet(entry, entry.bullets[0], {"AWS", "Docker"}, set())

        self.assertNotIn("using reliability", rewritten.lower())
        self.assertNotIn("improving delivery quality", rewritten.lower())
        self.assertIn("scalable feature releases", rewritten.lower())


if __name__ == "__main__":
    unittest.main()
