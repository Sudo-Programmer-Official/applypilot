from __future__ import annotations

import unittest
from unittest.mock import patch

from packages.postgres_store.store import ensure_schema, persist_pipeline_result, persist_resume_version


class PostgresStoreTests(unittest.TestCase):
    def test_persist_pipeline_result_stores_parsed_resume_and_analysis(self) -> None:
        executed: list[tuple[str, object]] = []

        class FakeCursor:
            def __init__(self) -> None:
                self._fetch_queue = [(301,), (401,), (501,)]

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


if __name__ == "__main__":
    unittest.main()
