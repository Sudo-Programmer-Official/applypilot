"""Persistent cache for imported job postings."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict

from packages.postgres_store import get_cached_job as get_postgres_cached_job
from packages.postgres_store import upsert_cached_job

_DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[2] / "apps" / "api" / "data" / "job_cache.db"


def get_cached_job(
    url: str,
    cache_path: str | None = None,
    database_url: str | None = None,
) -> Dict[str, Any] | None:
    if database_url:
        return get_postgres_cached_job(database_url, url)

    with _connect(cache_path) as connection:
        row = connection.execute(
            """
            SELECT source, title, company, location, description, skills_json
            FROM job_cache
            WHERE url = ?
            """,
            (url,),
        ).fetchone()

    if row is None:
        return None

    return {
        "url": url,
        "source": row[0],
        "title": row[1],
        "company": row[2],
        "location": row[3],
        "description": row[4],
        "skills": json.loads(row[5] or "[]"),
        "raw_json": {},
    }


def set_cached_job(
    url: str,
    job: Dict[str, Any],
    cache_path: str | None = None,
    database_url: str | None = None,
    ttl_hours: int = 168,
) -> None:
    if database_url:
        payload = {"url": url, **job}
        upsert_cached_job(database_url, payload, ttl_hours=ttl_hours)
        return

    with _connect(cache_path) as connection:
        connection.execute(
            """
            INSERT INTO job_cache (
                url, source, title, company, location, description, skills_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                source = excluded.source,
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                description = excluded.description,
                skills_json = excluded.skills_json,
                created_at = excluded.created_at
            """,
            (
                url,
                job.get("source", ""),
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("description", ""),
                json.dumps(job.get("skills", [])),
                int(time.time()),
            ),
        )
        connection.commit()


def _connect(cache_path: str | None) -> sqlite3.Connection:
    resolved_path = Path(cache_path) if cache_path else _DEFAULT_CACHE_PATH
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved_path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS job_cache (
            url TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            skills_json TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    return connection
