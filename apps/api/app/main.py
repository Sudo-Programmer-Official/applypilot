from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .orchestrator.resume_pipeline import run_resume_pipeline

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
SUPPORTED_RESUME_TYPES = {".pdf", ".docx"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting ApplyPilot API")
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


@app.get("/health")
async def health_check():
    """Lightweight liveness probe endpoint."""
    return {"status": "ok"}


@app.post("/resume/analyze")
async def analyze_resume(file: UploadFile = File(...), job_description: str | None = Form(default=None)):
    """
    Upload a resume file and run the pipeline.

    Accepts PDF or DOCX uploads. Job description is optional for now.
    """
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

    logger.info("Analyzing resume file=%s size_bytes=%s", filename, len(contents))
    try:
        result = run_resume_pipeline(temp_path, job_description)
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
