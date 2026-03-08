"""Postgres-backed persistence for job imports and resume pipeline runs."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

_EXTENSION_SQL = "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

_SCHEMA_SQL = """

CREATE TABLE IF NOT EXISTS job_cache (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    company TEXT,
    location TEXT,
    description TEXT,
    skills JSONB,
    source TEXT,
    raw_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resume_analysis (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES job_cache(id) ON DELETE SET NULL,
    resume_text TEXT,
    match_score INTEGER,
    missing_skills JSONB,
    strengths JSONB,
    weaknesses JSONB,
    suggestions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS optimized_resumes (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES resume_analysis(id) ON DELETE CASCADE,
    optimized_resume TEXT,
    generated_pdf_url TEXT,
    ats_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_cache_expires_at
ON job_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_resume_analysis_job_id
ON resume_analysis(job_id);

CREATE INDEX IF NOT EXISTS idx_optimized_resumes_analysis_id
ON optimized_resumes(analysis_id);
"""


def ensure_schema(database_url: str | None) -> None:
    if not database_url:
        return

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(_EXTENSION_SQL)
            except Exception as exc:
                connection.rollback()
                logger.warning("Could not enable pg_trgm extension: %s", exc)
            cursor.execute(_SCHEMA_SQL)
        connection.commit()


def get_cached_job(database_url: str | None, url: str) -> Dict[str, Any] | None:
    if not database_url:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, url, source, title, company, location, description, skills, raw_json
                FROM job_cache
                WHERE url = %s
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                (url,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "url": row["url"],
        "source": row.get("source") or "",
        "title": row.get("title") or "",
        "company": row.get("company") or "",
        "location": row.get("location") or "",
        "description": row.get("description") or "",
        "skills": row.get("skills") or [],
        "raw_json": row.get("raw_json") or {},
    }


def get_cached_job_id(database_url: str | None, url: str | None) -> int | None:
    if not database_url or not url:
        return None

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM job_cache
                WHERE url = %s
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                (url,),
            )
            row = cursor.fetchone()

    return int(row[0]) if row else None


def upsert_cached_job(
    database_url: str | None,
    job: Dict[str, Any],
    ttl_hours: int = 168,
) -> Dict[str, Any] | None:
    if not database_url:
        return None

    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    raw_json = job.get("raw_json") or {}

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO job_cache (
                    url, title, company, location, description, skills, source, raw_json, expires_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT(url) DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    skills = EXCLUDED.skills,
                    source = EXCLUDED.source,
                    raw_json = EXCLUDED.raw_json,
                    expires_at = EXCLUDED.expires_at
                RETURNING id, url, source, title, company, location, description, skills, raw_json
                """,
                (
                    job.get("url", ""),
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("description"),
                    Jsonb(job.get("skills", [])),
                    job.get("source"),
                    Jsonb(raw_json),
                    expires_at,
                ),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        return None

    return {
        "id": row["id"],
        "url": row["url"],
        "source": row.get("source") or "",
        "title": row.get("title") or "",
        "company": row.get("company") or "",
        "location": row.get("location") or "",
        "description": row.get("description") or "",
        "skills": row.get("skills") or [],
        "raw_json": row.get("raw_json") or {},
    }


def persist_pipeline_result(
    database_url: str | None,
    result: Any,
    job_url: str | None = None,
) -> Dict[str, int] | None:
    if not database_url:
        return None

    job_id = get_cached_job_id(database_url, job_url)
    parsed_text = result.parsed.get("text", "")
    analysis = result.analysis
    optimized = result.optimized
    readiness = result.application_readiness
    ats_score = result.ats_score

    match_score = int(readiness.get("projected_score") or readiness.get("score") or ats_score.get("projected_score") or ats_score.get("score") or 0)
    missing_skills = _skill_names(analysis.get("missing_skills")) or ats_score.get("missing_keywords") or []
    strengths = _skill_names(analysis.get("matched_skills")) or []
    weaknesses = readiness.get("top_issues") or analysis.get("unresolved_suggestions") or []
    suggestions = (
        analysis.get("applied_changes")
        or analysis.get("suggested_changes")
        or optimized.get("metadata", {}).get("suggestions")
        or []
    )

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO resume_analysis (
                    job_id, resume_text, match_score, missing_skills, strengths, weaknesses, suggestions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    job_id,
                    parsed_text,
                    match_score,
                    Jsonb(missing_skills),
                    Jsonb(strengths),
                    Jsonb(weaknesses),
                    Jsonb(suggestions),
                ),
            )
            analysis_row = cursor.fetchone()
            analysis_id = int(analysis_row[0])

            cursor.execute(
                """
                INSERT INTO optimized_resumes (
                    analysis_id, optimized_resume, generated_pdf_url, ats_score
                ) VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    analysis_id,
                    optimized.get("text", ""),
                    None,
                    int(ats_score.get("projected_score") or ats_score.get("score") or match_score),
                ),
            )
            optimized_row = cursor.fetchone()
            optimized_id = int(optimized_row[0])
        connection.commit()

    return {"analysis_id": analysis_id, "optimized_resume_id": optimized_id}


def _skill_names(items: Any) -> list[str]:
    if not items:
        return []
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return [str(item.get("name", "")).strip() for item in items if item.get("name")]
    if isinstance(items, list):
        return [str(item).strip() for item in items if str(item).strip()]
    return []
