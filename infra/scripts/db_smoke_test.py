from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from psycopg import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.app.main import app  # noqa: E402
from packages.resume_parser import PARSER_VERSION  # noqa: E402

FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "resumes" / "compact_resume.docx"
DEFAULT_JOB_DESCRIPTION = """Backend Engineer

Requirements:
- Python
- FastAPI
- PostgreSQL
- CI/CD
- Docker
"""


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required")
        return 1

    if not FIXTURE_PATH.exists():
        print(f"Fixture resume not found: {FIXTURE_PATH}")
        return 1

    file_bytes = FIXTURE_PATH.read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    with TestClient(app) as client:
        response = client.post(
            "/resume/analyze",
            files={
                "file": (
                    FIXTURE_PATH.name,
                    file_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"job_description": DEFAULT_JOB_DESCRIPTION},
        )

    if response.status_code != 200:
        print(f"/resume/analyze failed: {response.status_code} {response.text}")
        return 1

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM parsed_resumes
                WHERE source_file_hash = %s
                  AND parser_version = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (file_hash, PARSER_VERSION),
            )
            parsed_row = cursor.fetchone()
            if not parsed_row:
                print("parsed_resumes row not found")
                return 1
            parsed_resume_id = int(parsed_row[0])

            cursor.execute(
                """
                SELECT id
                FROM resume_analysis
                WHERE parsed_resume_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (parsed_resume_id,),
            )
            analysis_row = cursor.fetchone()
            if not analysis_row:
                print("resume_analysis row not found")
                return 1
            analysis_id = int(analysis_row[0])

            cursor.execute(
                """
                SELECT id
                FROM optimized_resumes
                WHERE analysis_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (analysis_id,),
            )
            optimized_row = cursor.fetchone()
            if not optimized_row:
                print("optimized_resumes row not found")
                return 1
            optimized_resume_id = int(optimized_row[0])

    print(
        {
            "status": "ok",
            "parsed_resume_id": parsed_resume_id,
            "analysis_id": analysis_id,
            "optimized_resume_id": optimized_resume_id,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
