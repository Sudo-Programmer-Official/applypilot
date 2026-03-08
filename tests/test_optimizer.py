from __future__ import annotations

import unittest

from packages.ai_engine.optimizer import optimize_resume
from packages.resume_formatter.builder import build_resume_document
from packages.shared_types.resume_document import ResumeDocument


class ResumeOptimizerTests(unittest.TestCase):
    def test_optimizer_keeps_strong_original_summary(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Distributed Systems Engineer | Cloud Data Infrastructure & Scalable Platforms",
                "Distributed systems engineer designing fault-tolerant, horizontally scalable data platforms processing 10M+ records across high-concurrency cloud workloads.",
                "Experience",
                "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                "- Architected distributed backend services on AWS Lambda and RDS to process 11M+ records across 30-40 concurrent workers with fault-tolerant orchestration.",
            ]
        )
        document = build_resume_document(resume_text)

        optimized = optimize_resume(
            resume_text,
            "Senior Backend Engineer\nRequirements:\n- AWS\n- Distributed Systems\n- CI/CD",
            resume_document=document,
        )

        optimized_document = ResumeDocument.model_validate(optimized["optimized_document"])

        self.assertRegex(optimized_document.summary, r"10\s?M\+\srecords")
        self.assertIn("fault-tolerant", optimized_document.summary.lower())
        self.assertNotIn("experienced in scalable backend systems", optimized_document.summary.lower())

    def test_optimizer_reorders_skills_for_backend_roles(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Software Engineer",
                "Technical Skills",
                "Cloud & Infrastructure: AWS, Docker",
                "Systems Engineering: Fault Tolerance",
                "Languages: Python, Java",
                "Databases: PostgreSQL",
                "Backend & Distributed Systems: REST APIs, Microservices",
                "Experience",
                "Software Engineer - Example Corp Jan 2022 - Present",
                "- Built backend systems.",
            ]
        )
        document = build_resume_document(resume_text)

        optimized = optimize_resume(
            resume_text,
            "Backend Engineer\nRequirements:\n- Python\n- AWS\n- PostgreSQL\n- Microservices",
            resume_document=document,
        )

        optimized_document = ResumeDocument.model_validate(optimized["optimized_document"])
        self.assertEqual(
            list(optimized_document.skills.keys())[:5],
            [
                "Languages",
                "Backend & Distributed Systems",
                "Databases",
                "Cloud & Infrastructure",
                "Systems Engineering",
            ],
        )

    def test_optimizer_preserves_experience_entries_and_avoids_reliability_filler(self) -> None:
        resume_text = "\n".join(
            [
                "ABHISHEK JHA",
                "Distributed Systems Engineer | Cloud Data Infrastructure & Scalable Platforms",
                "abhishek@example.com | linkedin.com/in/abhishek-jha-ai",
                "Experience",
                "Software Engineering Intern - Braintree Health May 2025 - Aug 2025",
                "- Architected high-scale distributed backend services using AWS Lambda and RDS to process 11M+ records across 30-40 concurrent workers with fault-tolerant orchestration.",
                "- Designed checkpoint-based execution control and indexed resume mechanisms enabling resilient high-availability execution under heavy parallel workloads.",
                "- Improved service throughput and latency by implementing workload sharding, parallel execution strategies, and advanced SQL indexing - reducing runtime from multi-week cycles to 1.5 hours.",
                "- Resolved database deadlocks and write-contention issues under concurrent load by redesigning indexing strategy and optimizing transactional boundaries.",
                "Graduate Assistant - Computer Science, TAMU-CC Jan 2025 - May 2025",
                "- Built an LLM-powered requirement traceability system to automate mapping between functional and quality requirements using semantic similarity techniques.",
                "- Designed evaluation pipelines to benchmark AI-generated outputs against manual scoring frameworks.",
                "Senior Software Engineer - Eruvaka Technology Nov 2021 - Aug 2024",
                "- Led architectural migration across production systems serving enterprise clients, improving maintainability and deployment efficiency.",
                "- Automated CI/CD workflows, reducing deployment effort by 40%.",
                "- Collaborated across backend, product, and infrastructure teams to deliver scalable feature releases.",
                "Software Engineer - Accenture Jul 2019 - Nov 2021",
                "- Delivered enterprise software modules within cross-functional Agile teams.",
                "- Developed and deployed enterprise-grade software components within large-scale distributed systems.",
            ]
        )
        document = build_resume_document(resume_text)

        optimized = optimize_resume(
            resume_text,
            "Senior Backend Engineer\nRequirements:\n- FastAPI\n- Docker\n- AWS\n- PostgreSQL\n- REST APIs",
            resume_document=document,
        )

        optimized_document = ResumeDocument.model_validate(optimized["optimized_document"])
        optimized_text = optimized["optimized_text"]

        self.assertEqual(len(optimized_document.experience), 4)
        self.assertEqual(len(optimized_document.experience[0].bullets), 4)
        self.assertIn("semantic similarity scoring", optimized_text)
        self.assertNotIn("using reliability", optimized_text.lower())
        self.assertNotIn("improving delivery quality", optimized_text.lower())
        self.assertIn("deployment effort by 40%", optimized_text)


if __name__ == "__main__":
    unittest.main()
