from __future__ import annotations

import unittest

from packages.job_intelligence.extractor import analyze_job_description, keyword_names


class JobIntelligenceTests(unittest.TestCase):
    def test_analyze_job_description_handles_workday_meta_description_format(self) -> None:
        description = (
            "Position Summary Samsung Electronics America, Inc. is now accepting applications for its Summer 2026 Intern Program. "
            "Role and Responsibilities About the Team: The Network Tool Automation Team develops automation solutions for Samsung network products. "
            "Key Focus: A key focus of the team is the development of an Agentic AI System designed to assist in troubleshooting network issues. "
            "Responsibilities: Design and Implement Automated Scripts: Develop and optimize automated scripts. "
            "Utilize Advanced Technologies: Leverage advancements in AI, machine learning, and data analytics. "
            "Contribute to the Agentic AI System: Gain hands-on experience with state-of-the-art technologies. "
            "Qualifications: Education: Currently pursuing a Bachelor's Degree. "
            "Technical Skills: Proficiency in Python, React, Django, FastAPI, SQL/NoSQL databases, Unix OS, and Bash scripting. "
            "Experience building Agentic AI solutions. Benefits: Medical, dental, vision."
        )

        report = analyze_job_description(description, limit=12)
        skills = keyword_names(report["skills"])

        self.assertEqual(report["role_type"]["id"], "agentic_ai_engineer")
        self.assertIn("Python", skills)
        self.assertIn("React", skills)
        self.assertIn("FastAPI", skills)
        self.assertIn("SQL", skills)
        self.assertIn("NoSQL", skills)
        self.assertIn("Bash", skills)
        self.assertIn("Agentic AI", skills)
        self.assertIn("Machine Learning", skills)
        self.assertGreater(len(report["cleaned_text"]), 100)


if __name__ == "__main__":
    unittest.main()
