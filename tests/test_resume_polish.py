from __future__ import annotations

import unittest

from packages.ai_engine.polish import polish_resume_text
from packages.shared_types.resume_document import (
    ResumeDocument,
    ResumeExperienceItem,
    ResumeProjectItem,
)


class ResumePolishTests(unittest.TestCase):
    def test_polish_fixes_spacing_and_fragment_artifacts(self) -> None:
        document = ResumeDocument(
            experience=[
                ResumeExperienceItem(
                    role="Software Engineer",
                    company="Example",
                    bullets=[
                        "Improved service throughput and latency by implementing workload sharding, parallel execution strategies, and advanced SQL indexing — reducing runtime from multi-week cycles to 1.5 hours .",
                        "Resolved database deadlocks and write-contention issues under concurrent load by redesigning indexing strategy and optimizing transactional boundaries. servability, and performance stability .",
                    ],
                )
            ]
        )

        polished, _ = polish_resume_text(document, role_label="Backend Engineer")

        self.assertIn("1.5 hours.", polished.experience[0].bullets[0])
        self.assertNotIn("hours .", polished.experience[0].bullets[0])
        self.assertIn("observability and performance stability.", polished.experience[0].bullets[1])
        self.assertNotRegex(polished.experience[0].bullets[1].lower(), r"\bservability\b")

    def test_polish_normalizes_known_technology_names(self) -> None:
        document = ResumeDocument(
            skills={
                "Cloud & Infrastructure": ["Cloud Watch", "Fast API", "Mongo DB"],
            }
        )

        polished, _ = polish_resume_text(document)

        self.assertEqual(
            polished.skills["Cloud & Infrastructure"],
            ["CloudWatch", "FastAPI", "MongoDB"],
        )

    def test_polish_repairs_truncated_project_details(self) -> None:
        document = ResumeDocument(
            projects=[
                ResumeProjectItem(
                    name="AI Productivity & Microservices Platform",
                    details="Built cloud-native automation system integrating conversational workflows,",
                    bullets=[],
                )
            ]
        )

        polished, _ = polish_resume_text(document)

        self.assertTrue(polished.projects[0].details.endswith("."))
        self.assertIn("supporting backend APIs and stateful orchestration.", polished.projects[0].details)

    def test_polish_keeps_bullets_terminal_and_capitalized(self) -> None:
        document = ResumeDocument(
            experience=[
                ResumeExperienceItem(
                    role="Software Engineer",
                    company="Example",
                    bullets=["built python api services using Fast API"],
                )
            ]
        )

        polished, _ = polish_resume_text(document)

        self.assertEqual(
            polished.experience[0].bullets[0],
            "Built python api services using FastAPI.",
        )


if __name__ == "__main__":
    unittest.main()
