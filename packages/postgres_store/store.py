"""Postgres-backed persistence for job imports and resume pipeline runs."""
from __future__ import annotations

import hashlib
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

CREATE TABLE IF NOT EXISTS parsed_resumes (
    id SERIAL PRIMARY KEY,
    source_file_name TEXT,
    source_file_hash TEXT,
    source_format TEXT,
    parser_mode TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    structured_resume JSONB NOT NULL,
    section_summary JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(content_hash, parser_version)
);

ALTER TABLE parsed_resumes
ADD COLUMN IF NOT EXISTS source_file_hash TEXT;

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

ALTER TABLE resume_analysis
ADD COLUMN IF NOT EXISTS parsed_resume_id INTEGER;

CREATE TABLE IF NOT EXISTS optimized_resumes (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES resume_analysis(id) ON DELETE CASCADE,
    optimized_resume TEXT,
    generated_pdf_url TEXT,
    ats_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resume_versions (
    id SERIAL PRIMARY KEY,
    parsed_resume_id INTEGER REFERENCES parsed_resumes(id) ON DELETE CASCADE,
    parent_version_id INTEGER,
    version_number INTEGER NOT NULL,
    source TEXT NOT NULL,
    resume_text TEXT NOT NULL,
    document_json JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parsed_resume_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_job_cache_expires_at
ON job_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_parsed_resumes_content_hash
ON parsed_resumes(content_hash);

CREATE INDEX IF NOT EXISTS idx_parsed_resumes_source_file_hash
ON parsed_resumes(source_file_hash);

CREATE INDEX IF NOT EXISTS idx_resume_analysis_job_id
ON resume_analysis(job_id);

CREATE INDEX IF NOT EXISTS idx_resume_analysis_parsed_resume_id
ON resume_analysis(parsed_resume_id);

CREATE INDEX IF NOT EXISTS idx_optimized_resumes_analysis_id
ON optimized_resumes(analysis_id);

CREATE INDEX IF NOT EXISTS idx_resume_versions_parsed_resume_id
ON resume_versions(parsed_resume_id);

CREATE INDEX IF NOT EXISTS idx_resume_versions_parent_version_id
ON resume_versions(parent_version_id);
"""

_PARSED_RESUME_FK_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_resume_analysis_parsed_resume'
    ) THEN
        ALTER TABLE resume_analysis
        ADD CONSTRAINT fk_resume_analysis_parsed_resume
        FOREIGN KEY (parsed_resume_id)
        REFERENCES parsed_resumes(id)
        ON DELETE SET NULL;
    END IF;
END $$;
"""

_RESUME_VERSION_FK_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_resume_versions_parent_version'
    ) THEN
        ALTER TABLE resume_versions
        ADD CONSTRAINT fk_resume_versions_parent_version
        FOREIGN KEY (parent_version_id)
        REFERENCES resume_versions(id)
        ON DELETE SET NULL;
    END IF;
END $$;
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
            cursor.execute(_PARSED_RESUME_FK_SQL)
            cursor.execute(_RESUME_VERSION_FK_SQL)
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


def get_parsed_resume_by_source_hash(
    database_url: str | None,
    source_file_hash: str | None,
    parser_version: str | None = None,
) -> Dict[str, Any] | None:
    if not database_url or not source_file_hash:
        return None

    version = parser_version or "layout_v1"
    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, source_file_name, source_file_hash, source_format, parser_mode,
                       parser_version, normalized_text, structured_resume, section_summary
                FROM parsed_resumes
                WHERE source_file_hash = %s
                  AND parser_version = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (source_file_hash, version),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "file_name": row.get("source_file_name") or "resume",
        "text": row.get("normalized_text") or "",
        "sections": row.get("section_summary") or [],
        "document": row.get("structured_resume") or {},
        "metadata": {
            "format": row.get("source_format") or "",
            "parser_mode": row.get("parser_mode") or "layout_aware",
            "parser_version": row.get("parser_version") or version,
            "source_file_hash": row.get("source_file_hash") or source_file_hash,
        },
    }


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
    parsed_resume_id = upsert_parsed_resume(database_url, result.parsed)
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
                    job_id, parsed_resume_id, resume_text, match_score, missing_skills, strengths, weaknesses, suggestions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    job_id,
                    parsed_resume_id,
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

    return {
        "parsed_resume_id": parsed_resume_id or 0,
        "analysis_id": analysis_id,
        "optimized_resume_id": optimized_id,
    }


def persist_resume_version(
    database_url: str | None,
    parsed_resume_id: int | None,
    source: str,
    resume_text: str,
    document: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
    parent_version_id: int | None = None,
) -> Dict[str, Any] | None:
    if not database_url or not parsed_resume_id:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
                FROM resume_versions
                WHERE parsed_resume_id = %s
                """,
                (parsed_resume_id,),
            )
            next_version_row = cursor.fetchone() or {"next_version": 1}
            next_version = int(next_version_row.get("next_version") or 1)

            cursor.execute(
                """
                INSERT INTO resume_versions (
                    parsed_resume_id,
                    parent_version_id,
                    version_number,
                    source,
                    resume_text,
                    document_json,
                    metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, parsed_resume_id, parent_version_id, version_number, source, metadata, created_at
                """,
                (
                    parsed_resume_id,
                    parent_version_id,
                    next_version,
                    source,
                    resume_text,
                    Jsonb(document),
                    Jsonb(metadata or {}),
                ),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        return None

    return {
        "id": int(row["id"]),
        "parsed_resume_id": int(row["parsed_resume_id"]),
        "parent_version_id": int(row["parent_version_id"]) if row.get("parent_version_id") is not None else None,
        "version_number": int(row["version_number"]),
        "source": row["source"],
        "metadata": row.get("metadata") or {},
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def upsert_parsed_resume(database_url: str | None, parsed: Dict[str, Any]) -> int | None:
    if not database_url:
        return None

    normalized_text = str(parsed.get("text", "") or "").strip()
    document = parsed.get("document") or {}
    metadata = parsed.get("metadata") or {}
    sections = parsed.get("sections") or []
    parser_version = str(metadata.get("parser_version") or "layout_v1")
    content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO parsed_resumes (
                    source_file_name,
                    source_file_hash,
                    source_format,
                    parser_mode,
                    parser_version,
                    content_hash,
                    normalized_text,
                    structured_resume,
                    section_summary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(content_hash, parser_version) DO UPDATE SET
                    source_file_name = EXCLUDED.source_file_name,
                    source_file_hash = EXCLUDED.source_file_hash,
                    source_format = EXCLUDED.source_format,
                    parser_mode = EXCLUDED.parser_mode,
                    normalized_text = EXCLUDED.normalized_text,
                    structured_resume = EXCLUDED.structured_resume,
                    section_summary = EXCLUDED.section_summary
                RETURNING id
                """,
                (
                    parsed.get("file_name"),
                    metadata.get("source_file_hash"),
                    metadata.get("format"),
                    metadata.get("parser_mode") or "layout_aware",
                    parser_version,
                    content_hash,
                    normalized_text,
                    Jsonb(document),
                    Jsonb(sections),
                ),
            )
            row = cursor.fetchone()
        connection.commit()

    return int(row[0]) if row else None


def _skill_names(items: Any) -> list[str]:
    if not items:
        return []
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return [str(item.get("name", "")).strip() for item in items if item.get("name")]
    if isinstance(items, list):
        return [str(item).strip() for item in items if str(item).strip()]
    return []
