from __future__ import annotations

import unittest
from unittest.mock import patch

from packages.postgres_store.store import (
    bootstrap_portfolio_profile,
    ensure_schema,
    persist_pipeline_result,
    persist_portfolio_activity,
    persist_resume_version,
)


class PostgresStoreTests(unittest.TestCase):
    def test_persist_pipeline_result_stores_parsed_resume_and_analysis(self) -> None:
        executed: list[tuple[str, object]] = []

        class FakeCursor:
            def __init__(self) -> None:
                self._fetch_queue = [None, (301,), (401,), (501,)]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, sql, params=None):
                executed.append((sql.strip().splitlines()[0], params))

            def fetchone(self):
                return self._fetch_queue.pop(0)

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_obj = FakeCursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def cursor(self):
                return self.cursor_obj

            def commit(self):
                executed.append(("COMMIT", None))

            def rollback(self):
                executed.append(("ROLLBACK", None))

        class Result:
            parsed = {
                "file_name": "resume.pdf",
                "text": "resume text",
                "document": {"name": "Abhishek Jha"},
                "sections": [{"name": "experience", "items": 2}],
                "metadata": {"format": "pdf", "parser_mode": "layout_aware", "parser_version": "layout_v1"},
            }
            analysis = {
                "missing_skills": [{"name": "Docker"}],
                "matched_skills": [{"name": "Python"}],
                "suggested_changes": ["Add Docker to skills section"],
            }
            optimized = {"text": "optimized text", "metadata": {"suggestions": ["Add Docker"]}}
            application_readiness = {"projected_score": 84, "top_issues": ["Add Docker"]}
            ats_score = {"projected_score": 82}

        with patch("packages.postgres_store.store.connect", return_value=FakeConnection()):
            ensure_schema("postgresql://example")

        with patch("packages.postgres_store.store.connect", return_value=FakeConnection()), patch(
            "packages.postgres_store.store.get_cached_job_id", return_value=11
        ):
            ids = persist_pipeline_result("postgresql://example", Result(), job_url="https://example.com/job")

        self.assertEqual(
            ids,
            {"parsed_resume_id": 301, "analysis_id": 401, "optimized_resume_id": 501},
        )
        first_statements = [sql for sql, _ in executed[:4]]
        self.assertIn("CREATE EXTENSION IF NOT EXISTS pg_trgm;", first_statements)
        self.assertIn("INSERT INTO parsed_resumes (", [sql for sql, _ in executed])
        self.assertIn("INSERT INTO resume_analysis (", [sql for sql, _ in executed])
        self.assertIn("INSERT INTO optimized_resumes (", [sql for sql, _ in executed])

    def test_persist_resume_version_creates_incremented_snapshot(self) -> None:
        executed: list[tuple[str, object]] = []

        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, sql, params=None):
                executed.append((sql.strip().splitlines()[0], params))

            def fetchone(self):
                if "COALESCE(MAX(version_number)" in executed[-1][0]:
                    return {"next_version": 3}
                if executed[-1][0] == "SELECT 1":
                    return (1,)
                return {
                    "id": 901,
                    "parsed_resume_id": 301,
                    "parent_version_id": 701,
                    "version_number": 3,
                    "source": "manual_edit",
                    "metadata": {"score_delta": 3, "reason": "Made AWS clearer."},
                    "created_at": None,
                }

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def cursor(self):
                return FakeCursor()

            def commit(self):
                executed.append(("COMMIT", None))

        with patch("packages.postgres_store.store.connect", return_value=FakeConnection()):
            version = persist_resume_version(
                "postgresql://example",
                parsed_resume_id=301,
                source="manual_edit",
                resume_text="updated text",
                document={"name": "Abhishek Jha"},
                metadata={"instruction": "Mention AWS more clearly"},
                parent_version_id=701,
            )

        self.assertEqual(version["id"], 901)
        self.assertEqual(version["version_number"], 3)
        self.assertEqual(version["metadata"]["score_delta"], 3)
        self.assertIn("INSERT INTO resume_versions (", [sql for sql, _ in executed])

    def test_bootstrap_portfolio_profile_seeds_projects_and_activity(self) -> None:
        executed: list[tuple[str, object]] = []

        class FakeCursor:
            def __init__(self) -> None:
                self.fetchone_queue = [
                    {
                        "id": 301,
                        "owner_firebase_uid": "firebase-uid-123",
                        "source_file_name": "resume.pdf",
                        "source_file_hash": "hash123",
                        "source_format": "pdf",
                        "parser_version": "layout_v1",
                        "structured_resume": {
                            "name": "Abhishek Jha",
                            "title": "Senior Backend Engineer",
                            "summary": "Builds ETL and platform workflows.",
                            "skills": {
                                "Languages": ["Python", "SQL"],
                                "Cloud": ["AWS", "Lambda"],
                            },
                            "experience": [
                                {
                                    "role": "Backend Engineer",
                                    "company": "Braintree Health",
                                    "date": "2025",
                                    "bullets": [
                                        "Optimized AWS Glue pipeline and reduced runtime from 6 hours to 1.5 hours.",
                                        "Built Lambda orchestration for ETL retries.",
                                    ],
                                }
                            ],
                            "projects": [],
                        },
                        "normalized_text": "resume text",
                        "created_at": None,
                    },
                    {
                        "id": 91,
                        "firebase_uid": "firebase-uid-123",
                        "username": "abhishek-jha",
                        "display_name": "Abhishek Jha",
                        "headline": "Senior Backend Engineer building visible, proof-backed work",
                        "summary": "Builds ETL and platform workflows.",
                        "location": "",
                        "primary_role": "Senior Backend Engineer",
                        "contact_email": "",
                        "email": "abhishek@example.com",
                        "photo_url": "",
                        "hiring_status": "open",
                        "hero_statement": "Live signal over static claims.",
                        "resume_snapshot": {},
                        "metadata": {"resume_version_count": 1},
                        "last_login_at": None,
                        "created_at": None,
                        "updated_at": None,
                    },
                    {
                        "id": 91,
                        "firebase_uid": "firebase-uid-123",
                        "username": "abhishek-jha",
                        "display_name": "Abhishek Jha",
                        "headline": "Senior Backend Engineer building visible, proof-backed work",
                        "summary": "Builds ETL and platform workflows.",
                        "location": "",
                        "primary_role": "Senior Backend Engineer",
                        "contact_email": "",
                        "email": "abhishek@example.com",
                        "photo_url": "",
                        "hiring_status": "open",
                        "hero_statement": "Live signal over static claims.",
                        "resume_snapshot": {},
                        "metadata": {"resume_version_count": 1},
                        "last_login_at": None,
                        "created_at": None,
                        "updated_at": None,
                    },
                    {"id": 401},
                    {"id": 801},
                ]
                self.fetchall_queue = [
                    [
                        {
                            "id": 701,
                            "version_number": 2,
                            "source": "manual_edit",
                            "metadata": {
                                "reason": "Clarified AWS platform ownership.",
                                "instruction": "Strengthened pipeline optimization bullet.",
                                "score_delta": 6,
                                "edit_type": "bullet_edit",
                                "target_section": "experience",
                            },
                            "created_at": None,
                        }
                    ]
                ]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, sql, params=None):
                executed.append((sql.strip().splitlines()[0], params))

            def fetchone(self):
                return self.fetchone_queue.pop(0)

            def fetchall(self):
                return self.fetchall_queue.pop(0)

        class FakeConnection:
            def __init__(self) -> None:
                self.cursor_obj = FakeCursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def cursor(self):
                return self.cursor_obj

            def commit(self):
                executed.append(("COMMIT", None))

        with patch("packages.postgres_store.store.connect", return_value=FakeConnection()), patch(
            "packages.postgres_store.store.get_portfolio_overview",
            return_value={"profile": {"username": "abhishek-jha"}, "projects": [], "activity": [], "proof_cards": [], "metrics": {}},
        ):
            portfolio = bootstrap_portfolio_profile(
                "postgresql://example",
                firebase_uid="firebase-uid-123",
                username="Abhishek Jha",
                email="abhishek@example.com",
                display_name="Abhishek Jha",
            )

        self.assertEqual(portfolio["profile"]["username"], "abhishek-jha")
        statements = [sql for sql, _ in executed]
        self.assertIn("UPDATE developer_profiles", statements)
        self.assertIn("INSERT INTO portfolio_projects (", statements)
        self.assertIn("INSERT INTO portfolio_activity_events (", statements)
        self.assertIn("INSERT INTO proof_artifacts (", statements)

    def test_persist_portfolio_activity_creates_manual_log_and_proof(self) -> None:
        executed: list[tuple[str, object]] = []

        class FakeCursor:
            def __init__(self) -> None:
                self.fetchone_queue = [
                    {
                        "id": 91,
                        "firebase_uid": "firebase-uid-123",
                        "username": "abhishek-jha",
                        "display_name": "Abhishek Jha",
                        "headline": "",
                        "summary": "",
                        "location": "",
                        "primary_role": "",
                        "contact_email": "",
                        "email": "abhishek@example.com",
                        "photo_url": "",
                        "hiring_status": "open",
                        "hero_statement": "",
                        "resume_snapshot": {},
                        "metadata": {},
                        "last_login_at": None,
                        "created_at": None,
                        "updated_at": None,
                    },
                    {"id": 401},
                    {
                        "id": 1001,
                        "project_id": 401,
                        "event_type": "manual_log",
                        "title": "Shipped orchestration retry fix",
                        "detail": "Handled noisy ETL retries with better fan-out control.",
                        "impact": "Reduced failure volume.",
                        "source": "manual_log",
                        "happened_on": None,
                        "tags": ["aws", "etl"],
                        "links": ["https://github.com/example/repo/pull/1"],
                        "proof_json": {"claim": "Reduced ETL failures by 42%."},
                        "visibility": "public",
                        "created_at": None,
                    },
                ]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, sql, params=None):
                executed.append((sql.strip().splitlines()[0], params))

            def fetchone(self):
                return self.fetchone_queue.pop(0)

        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def cursor(self):
                return FakeCursor()

            def commit(self):
                executed.append(("COMMIT", None))

        with patch("packages.postgres_store.store.connect", return_value=FakeConnection()):
            activity = persist_portfolio_activity(
                "postgresql://example",
                {
                    "project_id": 401,
                    "title": "Shipped orchestration retry fix",
                    "detail": "Handled noisy ETL retries with better fan-out control.",
                    "impact": "Reduced failure volume.",
                    "tags": ["aws", "etl"],
                    "links": ["https://github.com/example/repo/pull/1"],
                    "proof": {
                        "claim": "Reduced ETL failures by 42%.",
                        "evidence": "Introduced batched retries and smarter backoff.",
                        "metric_label": "Failure rate",
                        "metric_before": "19%",
                        "metric_after": "11%",
                    },
                },
                firebase_uid="firebase-uid-123",
            )

        self.assertEqual(activity["title"], "Shipped orchestration retry fix")
        statements = [sql for sql, _ in executed]
        self.assertIn("INSERT INTO portfolio_activity_events (", statements)
        self.assertIn("INSERT INTO proof_artifacts (", statements)


if __name__ == "__main__":
    unittest.main()
