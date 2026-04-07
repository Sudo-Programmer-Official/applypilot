"""Postgres-backed persistence for job imports and resume pipeline runs."""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable

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
    owner_firebase_uid TEXT,
    source_file_name TEXT,
    source_file_hash TEXT,
    source_format TEXT,
    parser_mode TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    structured_resume JSONB NOT NULL,
    section_summary JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE parsed_resumes
ADD COLUMN IF NOT EXISTS source_file_hash TEXT;

ALTER TABLE parsed_resumes
ADD COLUMN IF NOT EXISTS owner_firebase_uid TEXT;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'parsed_resumes_content_hash_parser_version_key'
    ) THEN
        ALTER TABLE parsed_resumes
        DROP CONSTRAINT parsed_resumes_content_hash_parser_version_key;
    END IF;
END $$;

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

CREATE TABLE IF NOT EXISTS developer_profiles (
    id SERIAL PRIMARY KEY,
    firebase_uid TEXT UNIQUE,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    headline TEXT,
    summary TEXT,
    location TEXT,
    primary_role TEXT,
    contact_email TEXT,
    email TEXT,
    photo_url TEXT,
    hiring_status TEXT NOT NULL DEFAULT 'open',
    hero_statement TEXT,
    resume_snapshot JSONB,
    metadata JSONB,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE developer_profiles
ADD COLUMN IF NOT EXISTS firebase_uid TEXT;

ALTER TABLE developer_profiles
ADD COLUMN IF NOT EXISTS email TEXT;

ALTER TABLE developer_profiles
ADD COLUMN IF NOT EXISTS photo_url TEXT;

ALTER TABLE developer_profiles
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS portfolio_projects (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES developer_profiles(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    impact_statement TEXT,
    source TEXT NOT NULL,
    tech_stack JSONB,
    bullets JSONB,
    proof_points JSONB,
    links JSONB,
    featured BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(profile_id, slug)
);

CREATE TABLE IF NOT EXISTS portfolio_activity_events (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES developer_profiles(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES portfolio_projects(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT,
    impact TEXT,
    source TEXT NOT NULL,
    happened_on DATE,
    tags JSONB,
    links JSONB,
    proof_json JSONB,
    visibility TEXT NOT NULL DEFAULT 'public',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS proof_artifacts (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES developer_profiles(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES portfolio_projects(id) ON DELETE SET NULL,
    activity_event_id INTEGER REFERENCES portfolio_activity_events(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence TEXT,
    metric_label TEXT,
    metric_before TEXT,
    metric_after TEXT,
    source TEXT NOT NULL,
    links JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_cache_expires_at
ON job_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_parsed_resumes_content_hash
ON parsed_resumes(content_hash);

CREATE INDEX IF NOT EXISTS idx_parsed_resumes_source_file_hash
ON parsed_resumes(source_file_hash);

CREATE INDEX IF NOT EXISTS idx_parsed_resumes_owner_firebase_uid
ON parsed_resumes(owner_firebase_uid);

CREATE UNIQUE INDEX IF NOT EXISTS idx_parsed_resumes_owner_content_hash_parser_version
ON parsed_resumes ((COALESCE(owner_firebase_uid, '')), content_hash, parser_version);

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

CREATE INDEX IF NOT EXISTS idx_developer_profiles_username
ON developer_profiles(username);

CREATE UNIQUE INDEX IF NOT EXISTS idx_developer_profiles_firebase_uid
ON developer_profiles(firebase_uid);

CREATE INDEX IF NOT EXISTS idx_portfolio_projects_profile_id
ON portfolio_projects(profile_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_activity_events_profile_id
ON portfolio_activity_events(profile_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_activity_events_happened_on
ON portfolio_activity_events(happened_on);

CREATE INDEX IF NOT EXISTS idx_proof_artifacts_profile_id
ON proof_artifacts(profile_id);
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
    owner_firebase_uid: str | None = None,
) -> Dict[str, Any] | None:
    if not database_url or not source_file_hash:
        return None

    version = parser_version or "layout_v1"
    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, owner_firebase_uid, source_file_name, source_file_hash, source_format, parser_mode,
                       parser_version, normalized_text, structured_resume, section_summary
                FROM parsed_resumes
                WHERE source_file_hash = %s
                  AND parser_version = %s
                  AND ((%s IS NULL AND owner_firebase_uid IS NULL) OR owner_firebase_uid = %s)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (source_file_hash, version, owner_firebase_uid, owner_firebase_uid),
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
            "owner_firebase_uid": row.get("owner_firebase_uid") or owner_firebase_uid or "",
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
    owner_firebase_uid: str | None = None,
) -> Dict[str, int] | None:
    if not database_url:
        return None

    job_id = get_cached_job_id(database_url, job_url)
    parsed_text = result.parsed.get("text", "")
    parsed_resume_id = upsert_parsed_resume(database_url, result.parsed, owner_firebase_uid=owner_firebase_uid)
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
    owner_firebase_uid: str | None = None,
) -> Dict[str, Any] | None:
    if not database_url or not parsed_resume_id:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
                FROM resume_versions
                JOIN parsed_resumes ON parsed_resumes.id = resume_versions.parsed_resume_id
                WHERE resume_versions.parsed_resume_id = %s
                  AND ((%s IS NULL AND parsed_resumes.owner_firebase_uid IS NULL) OR parsed_resumes.owner_firebase_uid = %s)
                """,
                (parsed_resume_id, owner_firebase_uid, owner_firebase_uid),
            )
            next_version_row = cursor.fetchone() or {"next_version": 1}
            next_version = int(next_version_row.get("next_version") or 1)

            cursor.execute(
                """
                SELECT 1
                FROM parsed_resumes
                WHERE id = %s
                  AND ((%s IS NULL AND owner_firebase_uid IS NULL) OR owner_firebase_uid = %s)
                """,
                (parsed_resume_id, owner_firebase_uid, owner_firebase_uid),
            )
            if cursor.fetchone() is None:
                return None

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


def upsert_parsed_resume(
    database_url: str | None,
    parsed: Dict[str, Any],
    owner_firebase_uid: str | None = None,
) -> int | None:
    if not database_url:
        return None

    normalized_text = str(parsed.get("text", "") or "").strip()
    document = parsed.get("document") or {}
    metadata = parsed.get("metadata") or {}
    sections = parsed.get("sections") or []
    parser_version = str(metadata.get("parser_version") or "layout_v1")
    content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    owner_value = owner_firebase_uid or metadata.get("owner_firebase_uid")

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM parsed_resumes
                WHERE content_hash = %s
                  AND parser_version = %s
                  AND ((%s IS NULL AND owner_firebase_uid IS NULL) OR owner_firebase_uid = %s)
                LIMIT 1
                """,
                (content_hash, parser_version, owner_value, owner_value),
            )
            existing_row = cursor.fetchone()

            if existing_row is not None:
                cursor.execute(
                    """
                    UPDATE parsed_resumes
                    SET source_file_name = %s,
                        owner_firebase_uid = %s,
                        source_file_hash = %s,
                        source_format = %s,
                        parser_mode = %s,
                        normalized_text = %s,
                        structured_resume = %s,
                        section_summary = %s
                    WHERE id = %s
                    RETURNING id
                    """,
                    (
                        parsed.get("file_name"),
                        owner_value,
                        metadata.get("source_file_hash"),
                        metadata.get("format"),
                        metadata.get("parser_mode") or "layout_aware",
                        normalized_text,
                        Jsonb(document),
                        Jsonb(sections),
                        int(existing_row[0] if isinstance(existing_row, tuple) else existing_row["id"]),
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO parsed_resumes (
                        source_file_name,
                        owner_firebase_uid,
                        source_file_hash,
                        source_format,
                        parser_mode,
                        parser_version,
                        content_hash,
                        normalized_text,
                        structured_resume,
                        section_summary
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        parsed.get("file_name"),
                        owner_value,
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


def ensure_developer_profile(
    database_url: str | None,
    firebase_uid: str,
    email: str = "",
    display_name: str = "",
    photo_url: str = "",
    username: str | None = None,
) -> Dict[str, Any] | None:
    if not database_url or not firebase_uid:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            existing_profile = _fetch_portfolio_profile_row(cursor, firebase_uid=firebase_uid)
            display_name_value = _clean_text(existing_profile.get("display_name") if existing_profile else "") or _clean_text(display_name) or "ApplyPilot Builder"
            requested_username = username or (existing_profile.get("username") if existing_profile else None) or _username_seed(email=email, display_name=display_name_value)
            resolved_username = _ensure_available_username(cursor, requested_username, firebase_uid=firebase_uid)
            payload = {
                "profile_id": existing_profile.get("id") if existing_profile else None,
                "firebase_uid": firebase_uid,
                "username": resolved_username,
                "display_name": display_name_value,
                "headline": _clean_text(existing_profile.get("headline") if existing_profile else ""),
                "summary": _clean_text(existing_profile.get("summary") if existing_profile else ""),
                "location": _clean_text(existing_profile.get("location") if existing_profile else ""),
                "primary_role": _clean_text(existing_profile.get("primary_role") if existing_profile else ""),
                "contact_email": _clean_text(existing_profile.get("contact_email") if existing_profile else ""),
                "email": _clean_text(email) or _clean_text(existing_profile.get("email") if existing_profile else ""),
                "photo_url": _clean_text(photo_url) or _clean_text(existing_profile.get("photo_url") if existing_profile else ""),
                "hiring_status": _clean_text(existing_profile.get("hiring_status") if existing_profile else "open") or "open",
                "hero_statement": _clean_text(existing_profile.get("hero_statement") if existing_profile else ""),
                "resume_snapshot": (existing_profile.get("resume_snapshot") if existing_profile else {}) or {},
                "metadata": (existing_profile.get("metadata") if existing_profile else {}) or {},
            }
            row = _upsert_portfolio_profile_row(cursor, payload)
        connection.commit()

    return _row_to_portfolio_profile(row) if row else None


def bootstrap_portfolio_profile(
    database_url: str | None,
    firebase_uid: str,
    username: str | None = None,
    parsed_resume_id: int | None = None,
    email: str = "",
    display_name: str = "",
    photo_url: str = "",
) -> Dict[str, Any] | None:
    if not database_url or not firebase_uid:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            resume_row = _fetch_portfolio_resume_source(
                cursor,
                parsed_resume_id=parsed_resume_id,
                owner_firebase_uid=firebase_uid,
            )
            if resume_row is None:
                return None

            document = resume_row.get("structured_resume") or {}
            versions = _fetch_resume_versions(cursor, int(resume_row["id"]))
            existing_profile_row = _fetch_portfolio_profile_row(cursor, firebase_uid=firebase_uid)
            if existing_profile_row is None:
                return None
            resolved_username = _sanitize_username(existing_profile_row.get("username") or username or "")
            profile_payload = _build_portfolio_profile_payload(
                existing_profile=existing_profile_row,
                firebase_uid=firebase_uid,
                resolved_username=resolved_username,
                resume_row=resume_row,
                document=document,
                versions=versions,
                email=email,
                display_name=display_name,
                photo_url=photo_url,
            )
            profile_row = _upsert_portfolio_profile_row(cursor, profile_payload)
            profile_id = int(profile_row["id"])

            cursor.execute(
                """
                DELETE FROM proof_artifacts
                WHERE profile_id = %s
                  AND source IN ('resume_experience', 'resume_project', 'resume_version')
                """,
                (profile_id,),
            )
            cursor.execute(
                """
                DELETE FROM portfolio_activity_events
                WHERE profile_id = %s
                  AND source IN ('resume_bootstrap', 'resume_version')
                """,
                (profile_id,),
            )
            cursor.execute(
                """
                DELETE FROM portfolio_projects
                WHERE profile_id = %s
                  AND source IN ('resume_experience', 'resume_project')
                """,
                (profile_id,),
            )

            global_skills = _flatten_skill_values(document.get("skills") or {})
            used_slugs: set[str] = set()
            for record in _resume_project_records(document, global_skills):
                slug = _unique_slug(record["slug"], used_slugs)
                cursor.execute(
                    """
                    INSERT INTO portfolio_projects (
                        profile_id, slug, title, summary, impact_statement, source,
                        tech_stack, bullets, proof_points, links, featured, sort_order, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    RETURNING id
                    """,
                    (
                        profile_id,
                        slug,
                        record["title"],
                        record["summary"],
                        record["impact_statement"],
                        record["source"],
                        Jsonb(record["tech_stack"]),
                        Jsonb(record["bullets"]),
                        Jsonb(record["proof_points"]),
                        Jsonb(record["links"]),
                        record["featured"],
                        record["sort_order"],
                    ),
                )
                project_row = cursor.fetchone() or {"id": None}
                project_id = int(project_row["id"]) if project_row.get("id") is not None else None
                if project_id and record["impact_statement"]:
                    cursor.execute(
                        """
                        INSERT INTO proof_artifacts (
                            profile_id, project_id, title, claim, evidence, metric_label,
                            metric_before, metric_after, source, links, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            profile_id,
                            project_id,
                            record["title"],
                            record["impact_statement"],
                            " ".join(record["proof_points"][:2]).strip(),
                            "",
                            "",
                            "",
                            record["source"],
                            Jsonb(record["links"]),
                            Jsonb({"seeded": True}),
                        ),
                    )

            cursor.execute(
                """
                INSERT INTO portfolio_activity_events (
                    profile_id, event_type, title, detail, impact, source, happened_on,
                    tags, links, proof_json, visibility
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    profile_id,
                    "bootstrap",
                    "Built live profile from latest resume",
                    "ApplyPilot translated the latest structured resume and optimization history into shareable projects and proof cards.",
                    f"Seeded {len(document.get('experience') or []) + len(document.get('projects') or [])} project narratives.",
                    "resume_bootstrap",
                    date.today(),
                    Jsonb(["resume", "bootstrap", "applypilot"]),
                    Jsonb([]),
                    Jsonb({}),
                    "public",
                ),
            )

            for version in versions[:8]:
                reason = str((version.get("metadata") or {}).get("reason") or "").strip()
                instruction = str((version.get("metadata") or {}).get("instruction") or "").strip()
                score_delta = int((version.get("metadata") or {}).get("score_delta") or 0)
                detail_parts = [part for part in [reason, instruction] if part]
                cursor.execute(
                    """
                    INSERT INTO portfolio_activity_events (
                        profile_id, event_type, title, detail, impact, source, happened_on,
                        tags, links, proof_json, visibility
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        profile_id,
                        str(version.get("source") or "resume_version"),
                        _resume_version_title(version),
                        " ".join(detail_parts).strip(),
                        _resume_version_impact(score_delta),
                        "resume_version",
                        _coerce_date(version.get("created_at")) or date.today(),
                        Jsonb(_resume_version_tags(version)),
                        Jsonb([]),
                        Jsonb(
                            {
                                "claim": reason,
                                "evidence": instruction,
                                "metric_label": "Score delta" if score_delta else "",
                                "metric_before": "",
                                "metric_after": f"+{score_delta}" if score_delta > 0 else str(score_delta or ""),
                            }
                        ),
                        "public",
                    ),
                )
                activity_row = cursor.fetchone() or {"id": None}
                activity_id = int(activity_row["id"]) if activity_row.get("id") is not None else None
                if activity_id and (reason or score_delta):
                    cursor.execute(
                        """
                        INSERT INTO proof_artifacts (
                            profile_id, activity_event_id, title, claim, evidence, metric_label,
                            metric_before, metric_after, source, links, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            profile_id,
                            activity_id,
                            _resume_version_title(version),
                            reason or _resume_version_title(version),
                            instruction,
                            "Score delta" if score_delta else "",
                            "",
                            f"+{score_delta}" if score_delta > 0 else str(score_delta or ""),
                            "resume_version",
                            Jsonb([]),
                            Jsonb({"version_number": version.get("version_number")}),
                        ),
                    )
        connection.commit()

    return get_portfolio_overview(database_url, firebase_uid=firebase_uid, public_only=False)


def get_portfolio_overview(
    database_url: str | None,
    firebase_uid: str | None = None,
    username: str | None = None,
    profile_id: int | None = None,
    public_only: bool = False,
) -> Dict[str, Any] | None:
    if not database_url:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            profile_row = _fetch_portfolio_profile_row(
                cursor,
                firebase_uid=firebase_uid,
                username=username,
                profile_id=profile_id,
            )
            if profile_row is None and firebase_uid is None and username is None and profile_id is None:
                cursor.execute(
                    """
                    SELECT id, firebase_uid, username, display_name, headline, summary, location, primary_role,
                           contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata,
                           last_login_at, created_at, updated_at
                    FROM developer_profiles
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT 1
                    """
                )
                profile_row = cursor.fetchone()
            if profile_row is None:
                return None

            resolved_profile_id = int(profile_row["id"])
            cursor.execute(
                """
                SELECT id, slug, title, summary, impact_statement, source, tech_stack,
                       bullets, proof_points, links, featured, sort_order
                FROM portfolio_projects
                WHERE profile_id = %s
                ORDER BY featured DESC, sort_order ASC, created_at DESC
                """,
                (resolved_profile_id,),
            )
            project_rows = cursor.fetchall() or []

            activity_filters = ["profile_id = %s"]
            activity_params: list[Any] = [resolved_profile_id]
            if public_only:
                activity_filters.append("visibility = 'public'")
            cursor.execute(
                f"""
                SELECT id, project_id, event_type, title, detail, impact, source, happened_on,
                       tags, links, proof_json, visibility, created_at
                FROM portfolio_activity_events
                WHERE {' AND '.join(activity_filters)}
                ORDER BY COALESCE(happened_on, created_at::date) DESC, created_at DESC
                LIMIT 14
                """,
                tuple(activity_params),
            )
            activity_rows = cursor.fetchall() or []

            proof_filters = ["proof_artifacts.profile_id = %s"]
            proof_params: list[Any] = [resolved_profile_id]
            if public_only:
                proof_filters.append("(portfolio_activity_events.visibility = 'public' OR portfolio_activity_events.id IS NULL)")
            cursor.execute(
                f"""
                SELECT proof_artifacts.id, proof_artifacts.project_id, portfolio_projects.title AS project_title,
                       proof_artifacts.title, proof_artifacts.claim, proof_artifacts.evidence,
                       proof_artifacts.metric_label, proof_artifacts.metric_before, proof_artifacts.metric_after,
                       proof_artifacts.source, proof_artifacts.links, proof_artifacts.metadata,
                       proof_artifacts.created_at
                FROM proof_artifacts
                LEFT JOIN portfolio_projects ON portfolio_projects.id = proof_artifacts.project_id
                LEFT JOIN portfolio_activity_events ON portfolio_activity_events.id = proof_artifacts.activity_event_id
                WHERE {' AND '.join(proof_filters)}
                ORDER BY proof_artifacts.created_at DESC
                LIMIT 10
                """,
                tuple(proof_params),
            )
            proof_rows = cursor.fetchall() or []

    profile = _row_to_portfolio_profile(profile_row)
    projects = [_row_to_portfolio_project(row) for row in project_rows]
    activity = [_row_to_portfolio_activity(row) for row in activity_rows]
    proof_cards = [_row_to_portfolio_proof(row) for row in proof_rows]
    metrics = _build_portfolio_metrics(
        projects=projects,
        activity=activity,
        proof_cards=proof_cards,
        metadata=profile.get("metadata") or {},
    )

    return {
        "profile": profile,
        "metrics": metrics,
        "projects": projects,
        "activity": activity,
        "proof_cards": proof_cards,
    }


def upsert_portfolio_profile(
    database_url: str | None,
    payload: Dict[str, Any],
    firebase_uid: str,
    email: str = "",
    display_name: str = "",
    photo_url: str = "",
) -> Dict[str, Any] | None:
    if not database_url or not firebase_uid:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            existing = _fetch_portfolio_profile_row(cursor, firebase_uid=firebase_uid)

            merged_payload = {
                "profile_id": (existing or {}).get("id"),
                "firebase_uid": firebase_uid,
                "username": _ensure_available_username(
                    cursor,
                    payload.get("username") or (existing or {}).get("username") or _username_seed(email=email, display_name=display_name),
                    firebase_uid=firebase_uid,
                ),
                "display_name": _clean_text(payload.get("display_name") or (existing or {}).get("display_name") or display_name or "ApplyPilot Builder"),
                "headline": _clean_text(payload.get("headline") or (existing or {}).get("headline")),
                "summary": _clean_text(payload.get("summary") or (existing or {}).get("summary")),
                "location": _clean_text(payload.get("location") or (existing or {}).get("location")),
                "primary_role": _clean_text(payload.get("primary_role") or (existing or {}).get("primary_role")),
                "contact_email": _clean_text(payload.get("contact_email") or (existing or {}).get("contact_email")),
                "email": _clean_text(email) or _clean_text((existing or {}).get("email")),
                "photo_url": _clean_text(photo_url) or _clean_text((existing or {}).get("photo_url")),
                "hiring_status": _clean_text(payload.get("hiring_status") or (existing or {}).get("hiring_status") or "open"),
                "hero_statement": _clean_text(payload.get("hero_statement") or (existing or {}).get("hero_statement")),
                "resume_snapshot": payload.get("resume_snapshot") or (existing or {}).get("resume_snapshot") or {},
                "metadata": {**((existing or {}).get("metadata") or {}), **(payload.get("metadata") or {})},
            }
            row = _upsert_portfolio_profile_row(cursor, merged_payload)
        connection.commit()

    return _row_to_portfolio_profile(row)


def persist_portfolio_activity(
    database_url: str | None,
    payload: Dict[str, Any],
    firebase_uid: str,
) -> Dict[str, Any] | None:
    if not database_url or not firebase_uid:
        return None

    with connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            profile_row = _fetch_portfolio_profile_row(cursor, firebase_uid=firebase_uid)
            if profile_row is None:
                return None

            profile_id = int(profile_row["id"])
            project_id = payload.get("project_id")
            if project_id:
                cursor.execute(
                    """
                    SELECT id
                    FROM portfolio_projects
                    WHERE id = %s
                      AND profile_id = %s
                    """,
                    (project_id, profile_id),
                )
                if cursor.fetchone() is None:
                    raise ValueError("Project does not belong to the authenticated profile.")
            proof = payload.get("proof") or {}
            cursor.execute(
                """
                INSERT INTO portfolio_activity_events (
                    profile_id, project_id, event_type, title, detail, impact, source, happened_on,
                    tags, links, proof_json, visibility
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, project_id, event_type, title, detail, impact, source, happened_on,
                          tags, links, proof_json, visibility, created_at
                """,
                (
                    profile_id,
                    project_id,
                    _clean_text(payload.get("event_type") or "manual_log"),
                    _clean_text(payload.get("title")),
                    _clean_text(payload.get("detail")),
                    _clean_text(payload.get("impact")),
                    "manual_log",
                    payload.get("happened_on") or date.today(),
                    Jsonb(_unique_strings(payload.get("tags") or [])),
                    Jsonb(_normalize_links(payload.get("links") or [])),
                    Jsonb(proof),
                    "public",
                ),
            )
            row = cursor.fetchone()

            claim = _clean_text(proof.get("claim"))
            if claim and row is not None:
                cursor.execute(
                    """
                    INSERT INTO proof_artifacts (
                        profile_id, project_id, activity_event_id, title, claim, evidence, metric_label,
                        metric_before, metric_after, source, links, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        profile_id,
                        project_id,
                        int(row["id"]),
                        _clean_text(payload.get("title")),
                        claim,
                        _clean_text(proof.get("evidence")),
                        _clean_text(proof.get("metric_label")),
                        _clean_text(proof.get("metric_before")),
                        _clean_text(proof.get("metric_after")),
                        "manual_log",
                        Jsonb(_normalize_links(proof.get("links") or [])),
                        Jsonb({"manual": True}),
                    ),
                )
        connection.commit()

    return _row_to_portfolio_activity(row) if row else None


def _fetch_portfolio_resume_source(
    cursor: Any,
    parsed_resume_id: int | None = None,
    owner_firebase_uid: str | None = None,
) -> Dict[str, Any] | None:
    if parsed_resume_id:
        cursor.execute(
            """
            SELECT id, owner_firebase_uid, source_file_name, source_file_hash, source_format, parser_version,
                   structured_resume, normalized_text, created_at
            FROM parsed_resumes
            WHERE id = %s
              AND ((%s IS NULL AND owner_firebase_uid IS NULL) OR owner_firebase_uid = %s)
            """,
            (parsed_resume_id, owner_firebase_uid, owner_firebase_uid),
        )
    else:
        cursor.execute(
            """
            SELECT id, owner_firebase_uid, source_file_name, source_file_hash, source_format, parser_version,
                   structured_resume, normalized_text, created_at
            FROM parsed_resumes
            WHERE owner_firebase_uid = %s
            ORDER BY created_at DESC
            LIMIT 1
            """
            ,
            (owner_firebase_uid,),
        )
    return cursor.fetchone()


def _fetch_resume_versions(cursor: Any, parsed_resume_id: int) -> list[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT id, version_number, source, metadata, created_at
        FROM resume_versions
        WHERE parsed_resume_id = %s
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (parsed_resume_id,),
    )
    return cursor.fetchall() or []


def _fetch_portfolio_profile_row(
    cursor: Any,
    firebase_uid: str | None = None,
    username: str | None = None,
    profile_id: int | None = None,
) -> Dict[str, Any] | None:
    if profile_id:
        cursor.execute(
            """
            SELECT id, firebase_uid, username, display_name, headline, summary, location, primary_role,
                   contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata,
                   last_login_at, created_at, updated_at
            FROM developer_profiles
            WHERE id = %s
            """,
            (profile_id,),
        )
        return cursor.fetchone()

    if firebase_uid:
        cursor.execute(
            """
            SELECT id, firebase_uid, username, display_name, headline, summary, location, primary_role,
                   contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata,
                   last_login_at, created_at, updated_at
            FROM developer_profiles
            WHERE firebase_uid = %s
            """,
            (firebase_uid,),
        )
        return cursor.fetchone()

    if username:
        cursor.execute(
            """
            SELECT id, firebase_uid, username, display_name, headline, summary, location, primary_role,
                   contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata,
                   last_login_at, created_at, updated_at
            FROM developer_profiles
            WHERE username = %s
            """,
            (_sanitize_username(username),),
        )
        return cursor.fetchone()

    return None


def _upsert_portfolio_profile_row(cursor: Any, payload: Dict[str, Any]) -> Dict[str, Any]:
    profile_id = payload.get("profile_id")
    if profile_id:
        cursor.execute(
            """
            UPDATE developer_profiles
            SET firebase_uid = %s,
                username = %s,
                display_name = %s,
                headline = %s,
                summary = %s,
                location = %s,
                primary_role = %s,
                contact_email = %s,
                email = %s,
                photo_url = %s,
                hiring_status = %s,
                hero_statement = %s,
                resume_snapshot = %s,
                metadata = %s,
                last_login_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, firebase_uid, username, display_name, headline, summary, location, primary_role,
                      contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata,
                      last_login_at, created_at, updated_at
            """,
            (
                payload["firebase_uid"],
                payload["username"],
                payload["display_name"],
                payload["headline"],
                payload["summary"],
                payload["location"],
                payload["primary_role"],
                payload["contact_email"],
                payload.get("email") or "",
                payload.get("photo_url") or "",
                payload["hiring_status"],
                payload["hero_statement"],
                Jsonb(payload.get("resume_snapshot") or {}),
                Jsonb(payload.get("metadata") or {}),
                profile_id,
            ),
        )
        row = cursor.fetchone()
        if row is not None:
            return row

    cursor.execute(
        """
        INSERT INTO developer_profiles (
            firebase_uid, username, display_name, headline, summary, location, primary_role,
            contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata, last_login_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT(firebase_uid) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            username = EXCLUDED.username,
            headline = EXCLUDED.headline,
            summary = EXCLUDED.summary,
            location = EXCLUDED.location,
            primary_role = EXCLUDED.primary_role,
            contact_email = EXCLUDED.contact_email,
            email = EXCLUDED.email,
            photo_url = EXCLUDED.photo_url,
            hiring_status = EXCLUDED.hiring_status,
            hero_statement = EXCLUDED.hero_statement,
            resume_snapshot = EXCLUDED.resume_snapshot,
            metadata = EXCLUDED.metadata,
            last_login_at = NOW(),
            updated_at = NOW()
        RETURNING id, firebase_uid, username, display_name, headline, summary, location, primary_role,
                  contact_email, email, photo_url, hiring_status, hero_statement, resume_snapshot, metadata,
                  last_login_at, created_at, updated_at
        """,
        (
            payload["firebase_uid"],
            payload["username"],
            payload["display_name"],
            payload["headline"],
            payload["summary"],
            payload["location"],
            payload["primary_role"],
            payload["contact_email"],
            payload.get("email") or "",
            payload.get("photo_url") or "",
            payload["hiring_status"],
            payload["hero_statement"],
            Jsonb(payload.get("resume_snapshot") or {}),
            Jsonb(payload.get("metadata") or {}),
        ),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError("Could not persist developer profile.")
    return row


def _build_portfolio_profile_payload(
    existing_profile: Dict[str, Any] | None,
    firebase_uid: str,
    resolved_username: str,
    resume_row: Dict[str, Any],
    document: Dict[str, Any],
    versions: list[Dict[str, Any]],
    email: str = "",
    display_name: str = "",
    photo_url: str = "",
) -> Dict[str, Any]:
    existing = existing_profile or {}
    display_name_value = _clean_text(existing.get("display_name") or document.get("name") or display_name or resolved_username.replace("-", " ").title())
    primary_role = _clean_text(existing.get("primary_role") or document.get("title") or "Software Engineer")
    summary = _clean_text(existing.get("summary") or document.get("summary"))
    headline = _clean_text(existing.get("headline") or f"{primary_role} building visible, proof-backed work")
    hero_statement = _clean_text(
        existing.get("hero_statement")
        or f"Live signal over static claims. {display_name_value} ships work, captures impact, and keeps the profile current."
    )

    return {
        "profile_id": existing.get("id"),
        "firebase_uid": firebase_uid,
        "username": resolved_username,
        "display_name": display_name_value,
        "headline": headline,
        "summary": summary,
        "location": _clean_text(existing.get("location")),
        "primary_role": primary_role,
        "contact_email": _clean_text(existing.get("contact_email")),
        "email": _clean_text(email) or _clean_text(existing.get("email")),
        "photo_url": _clean_text(photo_url) or _clean_text(existing.get("photo_url")),
        "hiring_status": _clean_text(existing.get("hiring_status") or "open"),
        "hero_statement": hero_statement,
        "resume_snapshot": {
            "parsed_resume_id": int(resume_row["id"]),
            "file_name": resume_row.get("source_file_name") or "",
            "format": resume_row.get("source_format") or "",
            "parser_version": resume_row.get("parser_version") or "",
            "source_file_hash": resume_row.get("source_file_hash") or "",
            "name": document.get("name") or "",
            "title": document.get("title") or "",
            "summary": document.get("summary") or "",
            "updated_at": resume_row.get("created_at").isoformat() if resume_row.get("created_at") else None,
        },
        "metadata": {
            **(existing.get("metadata") or {}),
            "resume_version_count": len(versions),
            "experience_count": len(document.get("experience") or []),
            "project_count": len(document.get("projects") or []),
            "bootstrap_source": "resume",
        },
    }


def _resume_project_records(document: Dict[str, Any], global_skills: list[str]) -> list[Dict[str, Any]]:
    records: list[Dict[str, Any]] = []
    experience_items = document.get("experience") or []
    for index, item in enumerate(experience_items):
        role = _clean_text(item.get("role"))
        company = _clean_text(item.get("company"))
        bullets = _unique_strings(item.get("bullets") or [])
        title = " · ".join(part for part in [role, company] if part) or f"Experience {index + 1}"
        summary = bullets[0] if bullets else _clean_text(item.get("date"))
        impact_statement = _best_impact_statement(bullets)
        tech_stack = _match_relevant_skills(
            global_skills,
            " ".join([role, company, item.get("date") or "", *bullets]),
        )
        records.append(
            {
                "slug": _slugify(title),
                "title": title,
                "summary": summary,
                "impact_statement": impact_statement,
                "source": "resume_experience",
                "tech_stack": tech_stack,
                "bullets": bullets[:4],
                "proof_points": bullets[:3],
                "links": [],
                "featured": index < 3,
                "sort_order": index,
            }
        )

    project_items = document.get("projects") or []
    offset = len(records)
    for index, item in enumerate(project_items):
        name = _clean_text(item.get("name")) or f"Project {index + 1}"
        details = _clean_text(item.get("details"))
        bullets = _unique_strings(item.get("bullets") or [])
        impact_statement = _best_impact_statement([details, *bullets])
        tech_stack = _match_relevant_skills(global_skills, " ".join([name, details, *bullets]))
        records.append(
            {
                "slug": _slugify(name),
                "title": name,
                "summary": details or (bullets[0] if bullets else ""),
                "impact_statement": impact_statement,
                "source": "resume_project",
                "tech_stack": tech_stack,
                "bullets": bullets[:4],
                "proof_points": ([details] if details else []) + bullets[:2],
                "links": [],
                "featured": index < 2,
                "sort_order": offset + index,
            }
        )

    return records


def _row_to_portfolio_profile(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row["id"]),
        "username": row["username"],
        "display_name": row.get("display_name") or "",
        "headline": row.get("headline") or "",
        "summary": row.get("summary") or "",
        "location": row.get("location") or "",
        "primary_role": row.get("primary_role") or "",
        "contact_email": row.get("contact_email") or "",
        "email": row.get("email") or "",
        "photo_url": row.get("photo_url") or "",
        "hiring_status": row.get("hiring_status") or "open",
        "hero_statement": row.get("hero_statement") or "",
        "resume_snapshot": row.get("resume_snapshot") or {},
        "metadata": row.get("metadata") or {},
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
        "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
    }


def _row_to_public_portfolio_profile(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "display_name": row.get("display_name") or "",
        "headline": row.get("headline") or "",
        "summary": row.get("summary") or "",
        "location": row.get("location") or "",
        "primary_role": row.get("primary_role") or "",
        "hero_statement": row.get("hero_statement") or "",
    }


def _row_to_portfolio_project(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row["id"]),
        "slug": row.get("slug") or "",
        "title": row.get("title") or "",
        "summary": row.get("summary") or "",
        "impact_statement": row.get("impact_statement") or "",
        "source": row.get("source") or "",
        "tech_stack": row.get("tech_stack") or [],
        "bullets": row.get("bullets") or [],
        "proof_points": row.get("proof_points") or [],
        "links": row.get("links") or [],
        "featured": bool(row.get("featured")),
        "sort_order": int(row.get("sort_order") or 0),
    }


def _row_to_portfolio_activity(row: Dict[str, Any]) -> Dict[str, Any]:
    happened_on = row.get("happened_on")
    return {
        "id": int(row["id"]),
        "project_id": int(row["project_id"]) if row.get("project_id") is not None else None,
        "event_type": row.get("event_type") or "",
        "title": row.get("title") or "",
        "detail": row.get("detail") or "",
        "impact": row.get("impact") or "",
        "source": row.get("source") or "",
        "happened_on": happened_on.isoformat() if happened_on else None,
        "tags": row.get("tags") or [],
        "links": row.get("links") or [],
        "visibility": row.get("visibility") or "public",
        "proof": row.get("proof_json") or {},
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
    }


def _row_to_portfolio_proof(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row["id"]),
        "project_id": int(row["project_id"]) if row.get("project_id") is not None else None,
        "project_title": row.get("project_title") or None,
        "title": row.get("title") or "",
        "claim": row.get("claim") or "",
        "evidence": row.get("evidence") or "",
        "metric_label": row.get("metric_label") or "",
        "metric_before": row.get("metric_before") or "",
        "metric_after": row.get("metric_after") or "",
        "source": row.get("source") or "",
        "links": row.get("links") or [],
        "metadata": row.get("metadata") or {},
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
    }


def _build_portfolio_metrics(
    projects: list[Dict[str, Any]],
    activity: list[Dict[str, Any]],
    proof_cards: list[Dict[str, Any]],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    recent_cutoff = date.today() - timedelta(days=6)
    recent_activity_count = 0
    for item in activity:
        activity_day = _coerce_date(item.get("happened_on")) or _coerce_date(item.get("created_at"))
        if activity_day and activity_day >= recent_cutoff:
            recent_activity_count += 1

    tech_diversity = len(
        {
            skill.strip().lower()
            for project in projects
            for skill in (project.get("tech_stack") or [])
            if str(skill).strip()
        }
    )
    resume_versions = int(metadata.get("resume_version_count") or 0)
    project_count = len(projects)
    activity_count = len(activity)
    proof_count = len(proof_cards)
    impact_score = min(
        99,
        24
        + (project_count * 7)
        + (proof_count * 8)
        + (recent_activity_count * 6)
        + (min(tech_diversity, 12) * 2)
        + min(resume_versions, 10),
    )

    return {
        "impact_score": impact_score,
        "project_count": project_count,
        "activity_count": activity_count,
        "proof_count": proof_count,
        "recent_activity_count": recent_activity_count,
        "tech_diversity": tech_diversity,
        "resume_versions": resume_versions,
    }


def _flatten_skill_values(skills: Dict[str, Any]) -> list[str]:
    flattened: list[str] = []
    for values in skills.values():
        if isinstance(values, list):
            flattened.extend(str(value).strip() for value in values if str(value).strip())
    return _unique_strings(flattened)


def _match_relevant_skills(skill_names: list[str], content: str) -> list[str]:
    haystack = content.lower()
    matched = [skill for skill in skill_names if skill.lower() in haystack]
    if matched:
        return matched[:6]
    return skill_names[:6]


def _best_impact_statement(items: Iterable[str]) -> str:
    cleaned = [_clean_text(item) for item in items if _clean_text(item)]
    for item in cleaned:
        if re.search(r"\d", item):
            return item
    return cleaned[0] if cleaned else ""


def _resume_version_title(version: Dict[str, Any]) -> str:
    metadata = version.get("metadata") or {}
    edit_type = _clean_text(metadata.get("edit_type")).replace("_", " ")
    source = _clean_text(version.get("source")).replace("_", " ")
    if edit_type:
        return f"{edit_type.title()} update"
    if source:
        return f"{source.title()} update"
    return "Resume version update"


def _resume_version_impact(score_delta: int) -> str:
    if score_delta > 0:
        return f"Improved portfolio credibility signal by {score_delta} points."
    if score_delta < 0:
        return f"Captured a {abs(score_delta)} point regression for review."
    return "Tracked a new iteration in the resume-to-profile history."


def _resume_version_tags(version: Dict[str, Any]) -> list[str]:
    metadata = version.get("metadata") or {}
    return _unique_strings(
        [
            version.get("source"),
            metadata.get("edit_type"),
            metadata.get("target_section"),
        ]
    )


def _sanitize_username(value: str) -> str:
    candidate = _slugify(value)[:40]
    return candidate or "builder"


def _username_seed(email: str = "", display_name: str = "") -> str:
    local_part = _clean_text(email).split("@")[0] if email else ""
    return _sanitize_username(local_part or display_name or "builder")


def _ensure_available_username(cursor: Any, requested_username: str, firebase_uid: str | None = None) -> str:
    slug = _sanitize_username(requested_username)
    cursor.execute(
        """
        SELECT firebase_uid
        FROM developer_profiles
        WHERE username = %s
        """,
        (slug,),
    )
    row = cursor.fetchone()
    if row is None or row.get("firebase_uid") == firebase_uid:
        return slug

    suffix = 2
    while True:
        candidate = _sanitize_username(f"{slug}-{suffix}")[:40]
        cursor.execute(
            """
            SELECT firebase_uid
            FROM developer_profiles
            WHERE username = %s
            """,
            (candidate,),
        )
        existing = cursor.fetchone()
        if existing is None or existing.get("firebase_uid") == firebase_uid:
            return candidate
        suffix += 1


def _slugify(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
    return normalized.strip("-")


def _unique_slug(base: str, used_slugs: set[str]) -> str:
    slug = _slugify(base) or "project"
    if slug not in used_slugs:
        used_slugs.add(slug)
        return slug

    suffix = 2
    candidate = f"{slug}-{suffix}"
    while candidate in used_slugs:
        suffix += 1
        candidate = f"{slug}-{suffix}"
    used_slugs.add(candidate)
    return candidate


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _coerce_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = _clean_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _unique_strings(items: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        text = _clean_text(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(text)
    return unique


def _normalize_links(items: Iterable[Any]) -> list[str]:
    return [link for link in _unique_strings(items) if link.startswith("http://") or link.startswith("https://")]


def _skill_names(items: Any) -> list[str]:
    if not items:
        return []
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return [str(item.get("name", "")).strip() for item in items if item.get("name")]
    if isinstance(items, list):
        return [str(item).strip() for item in items if str(item).strip()]
    return []
