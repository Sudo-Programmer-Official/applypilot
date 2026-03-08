-- ApplyPilot Postgres bootstrap
-- Run with:
--   psql "$DATABASE_URL" -f infra/scripts/init_postgres.sql

CREATE EXTENSION IF NOT EXISTS pg_trgm;

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
