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
