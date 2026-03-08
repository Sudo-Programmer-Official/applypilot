from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .config import settings
from .models.export import ResumeDownloadRequest
from .models.job_import import JobImportRequest, JobImportResponse
from .orchestrator.resume_pipeline import run_resume_pipeline
from .orchestrator.suggestion_pipeline import apply_suggestion_pipeline
from packages.job_importer import import_job_posting
from packages.postgres_store import ensure_schema, persist_pipeline_result
from packages.resume_formatter.builder import build_resume_document
from packages.resume_formatter.renderer import render_resume_pdf

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
SUPPORTED_RESUME_TYPES = {".pdf", ".docx"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting ApplyPilot API env=%s cors_origins=%s", settings.environment, settings.cors_origins)
    if settings.database_url:
        logger.info("Ensuring Postgres schema is available")
        ensure_schema(settings.database_url)
    yield
    logger.info("Shutting down ApplyPilot API")


app = FastAPI(title=settings.api_title, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Friendly root endpoint for smoke tests on the API domain."""
    return {"service": settings.api_title, "status": "running"}


@app.get("/health")
async def health_check():
    """Lightweight liveness probe endpoint."""
    return {"status": "ok"}


@app.post("/job/import", response_model=JobImportResponse)
async def import_job(request: JobImportRequest):
    logger.info("Importing job url=%s", request.url)
    try:
        job = import_job_posting(
            request.url,
            database_url=settings.database_url,
            cache_ttl_hours=settings.job_cache_ttl_hours,
            cache_path=settings.job_cache_path,
            timeout_seconds=settings.job_import_timeout_seconds,
        )
        return JobImportResponse(**job)
    except requests.RequestException as exc:
        logger.warning("Job import fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not fetch the job page. Paste the job description manually.") from exc
    except ValueError as exc:
        logger.warning("Job import rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Job import failed")
        raise HTTPException(status_code=500, detail="Job import failed.") from exc


def _cleanup_file(path: str) -> None:
    Path(path).unlink(missing_ok=True)


def _pdf_file_name(original_file_name: str | None, use_optimized: bool) -> str:
    stem = Path(original_file_name or "resume").stem
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "resume"
    suffix = "optimized" if use_optimized else "preview"
    return f"{stem}_{suffix}.pdf"


async def _store_upload(file: UploadFile) -> tuple[str, str, int]:
    filename = file.filename or "resume"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_RESUME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload a PDF or DOCX resume.")

    contents = await file.read()
    if len(contents) > settings.max_file_bytes:
        raise HTTPException(status_code=400, detail="File too large. Max 5 MB.")

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        temp_path = tmp.name

    return filename, temp_path, len(contents)


@app.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str | None = Form(default=None),
    job_url: str | None = Form(default=None),
):
    """
    Upload a resume file and run the pipeline.

    Accepts PDF or DOCX uploads. Job description is optional for now.
    """
    filename, temp_path, size_bytes = await _store_upload(file)

    logger.info("Analyzing resume file=%s size_bytes=%s", filename, size_bytes)
    try:
        result = run_resume_pipeline(temp_path, job_description)
        persistence_ids = persist_pipeline_result(settings.database_url, result, job_url=job_url)
        if persistence_ids:
            logger.info(
                "Persisted resume analysis analysis_id=%s optimized_resume_id=%s",
                persistence_ids.get("analysis_id"),
                persistence_ids.get("optimized_resume_id"),
            )
        return {"status": "ok", "result": result.model_dump()}
    except ValueError as exc:
        logger.warning("Resume analysis rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        logger.warning("Resume file missing during analysis: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume analysis failed")
        raise HTTPException(status_code=500, detail="Resume analysis failed.") from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)


@app.post("/resume/apply-suggestions")
async def apply_resume_suggestions(file: UploadFile = File(...), suggestions: str = Form(...)):
    if not suggestions.strip():
        raise HTTPException(status_code=400, detail="Paste at least one suggestion before applying changes.")

    filename, temp_path, size_bytes = await _store_upload(file)

    logger.info("Applying resume suggestions file=%s size_bytes=%s", filename, size_bytes)
    try:
        result = apply_suggestion_pipeline(temp_path, suggestions)
        persistence_ids = persist_pipeline_result(settings.database_url, result)
        if persistence_ids:
            logger.info(
                "Persisted suggestion run analysis_id=%s optimized_resume_id=%s",
                persistence_ids.get("analysis_id"),
                persistence_ids.get("optimized_resume_id"),
            )
        return {"status": "ok", "result": result.model_dump()}
    except ValueError as exc:
        logger.warning("Suggestion application rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        logger.warning("Resume file missing during suggestion flow: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume suggestion flow failed")
        raise HTTPException(status_code=500, detail="Resume suggestion flow failed.") from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)


@app.post("/resume/download")
async def download_resume_pdf(payload: ResumeDownloadRequest):
    resume_text = payload.resume_text.strip()
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text is required for PDF export.")

    document = build_resume_document(resume_text, role_label=payload.role_label)

    try:
        pdf_bytes, rendered_document, render_meta = render_resume_pdf(document)
    except RuntimeError as exc:
        logger.exception("Resume PDF export is not available")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume PDF export failed")
        raise HTTPException(status_code=500, detail="Resume PDF export failed.") from exc

    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        temp_path = tmp.name

    logger.info(
        "Generated resume PDF file=%s pages=%s name=%s",
        payload.file_name,
        render_meta.get("page_count", 0),
        rendered_document.name,
    )

    return FileResponse(
        temp_path,
        media_type="application/pdf",
        filename=_pdf_file_name(payload.file_name, payload.use_optimized),
        background=BackgroundTask(_cleanup_file, temp_path),
    )
