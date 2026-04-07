from __future__ import annotations

import hashlib
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .auth import FirebaseIdentity, require_firebase_identity, require_workspace_identity
from .config import settings
from .models.edit import ResumeEditRequest
from .models.export import ResumeDownloadRequest
from .models.fix import ResumeFixRequest
from .models.job_import import JobImportRequest, JobImportResponse
from .models.portfolio import (
    PortfolioActivityCreateRequest,
    PortfolioBootstrapRequest,
    PortfolioOverviewResponse,
    PortfolioProfileResponse,
    PortfolioProfileUpdateRequest,
    PublicPortfolioOverviewResponse,
)
from .orchestrator.resume_pipeline import run_resume_pipeline
from .orchestrator.suggestion_pipeline import apply_suggestion_pipeline
from packages.ai_engine import apply_resume_edit, apply_resume_fixes
from packages.ai_engine.polish import polish_resume_text
from packages.job_importer import import_job_posting
from packages.postgres_store import (
    bootstrap_portfolio_profile,
    ensure_developer_profile,
    ensure_schema,
    get_parsed_resume_by_source_hash,
    get_portfolio_overview,
    persist_pipeline_result,
    persist_portfolio_activity,
    persist_resume_version,
    upsert_portfolio_profile,
    upsert_parsed_resume,
)
from packages.resume_formatter.builder import build_resume_document
from packages.resume_formatter.renderer import render_resume_pdf
from packages.resume_parser import PARSER_VERSION, parse_resume
from packages.shared_types.resume_document import ResumeDocument

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


@app.get("/portfolio/me", response_model=PortfolioOverviewResponse)
async def get_portfolio_me(identity: FirebaseIdentity = Depends(require_firebase_identity)):
    ensure_developer_profile(
        settings.database_url,
        firebase_uid=identity.uid,
        email=identity.email,
        display_name=identity.display_name,
        photo_url=identity.photo_url,
    )
    portfolio = get_portfolio_overview(settings.database_url, firebase_uid=identity.uid, public_only=False)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="No portfolio exists yet. Bootstrap one from your resume first.")
    return portfolio


@app.get("/portfolio/public/{username}", response_model=PublicPortfolioOverviewResponse)
async def get_public_portfolio(username: str):
    portfolio = get_portfolio_overview(settings.database_url, username=username, public_only=True)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Public profile not found.")
    return _serialize_public_portfolio(portfolio)


@app.post("/portfolio/bootstrap", response_model=PortfolioOverviewResponse)
async def bootstrap_portfolio(
    payload: PortfolioBootstrapRequest,
    identity: FirebaseIdentity = Depends(require_firebase_identity),
):
    ensure_developer_profile(
        settings.database_url,
        firebase_uid=identity.uid,
        email=identity.email,
        display_name=identity.display_name,
        photo_url=identity.photo_url,
        username=payload.username,
    )
    portfolio = bootstrap_portfolio_profile(
        settings.database_url,
        firebase_uid=identity.uid,
        username=payload.username,
        parsed_resume_id=payload.parsed_resume_id,
        email=identity.email,
        display_name=identity.display_name,
        photo_url=identity.photo_url,
    )
    if portfolio is None:
        raise HTTPException(
            status_code=404,
            detail="No resume owned by this account is available yet. Run the resume workflow after signing in.",
        )
    return portfolio


@app.patch("/portfolio/me", response_model=PortfolioProfileResponse)
async def update_portfolio_profile(
    payload: PortfolioProfileUpdateRequest,
    identity: FirebaseIdentity = Depends(require_firebase_identity),
):
    try:
        profile = upsert_portfolio_profile(
            settings.database_url,
            payload.model_dump(),
            firebase_uid=identity.uid,
            email=identity.email,
            display_name=identity.display_name,
            photo_url=identity.photo_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Portfolio profile update failed")
        raise HTTPException(status_code=500, detail="Portfolio profile update failed.") from exc

    if profile is None:
        raise HTTPException(status_code=503, detail="Portfolio persistence is unavailable.")
    return profile


@app.post("/portfolio/activity")
async def create_portfolio_activity(
    payload: PortfolioActivityCreateRequest,
    identity: FirebaseIdentity = Depends(require_firebase_identity),
):
    try:
        activity = persist_portfolio_activity(
            settings.database_url,
            payload.model_dump(),
            firebase_uid=identity.uid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Portfolio activity logging failed")
        raise HTTPException(status_code=500, detail="Portfolio activity logging failed.") from exc

    if activity is None:
        raise HTTPException(status_code=404, detail="Portfolio profile not found.")
    return {"status": "ok", "activity": activity}


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
        logger.info(
            "Job import succeeded source=%s role_title=%s extracted_skills=%s",
            job.get("source"),
            job.get("title"),
            job.get("skills", [])[:12],
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


@app.post("/resume/parse")
async def parse_resume_upload(
    file: UploadFile = File(...),
    identity: FirebaseIdentity | None = Depends(require_workspace_identity),
):
    filename, temp_path, size_bytes, file_hash = await _store_upload(file)
    owner_firebase_uid = identity.uid if identity else None

    logger.info("Parsing resume file=%s size_bytes=%s", filename, size_bytes)
    try:
        parsed_resume = _load_parsed_resume(temp_path, filename, file_hash, owner_firebase_uid=owner_firebase_uid)
        parsed_resume_id = upsert_parsed_resume(
            settings.database_url,
            parsed_resume,
            owner_firebase_uid=owner_firebase_uid,
        )
        if parsed_resume_id:
            logger.info("Persisted parsed resume parsed_resume_id=%s", parsed_resume_id)
        return {"status": "ok", "parsed": parsed_resume}
    except ValueError as exc:
        logger.warning("Resume parsing rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        logger.warning("Resume file missing during parsing: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume parsing failed")
        raise HTTPException(status_code=500, detail="Resume parsing failed.") from exc
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _cleanup_file(path: str) -> None:
    Path(path).unlink(missing_ok=True)


def _pdf_file_name(original_file_name: str | None, use_optimized: bool) -> str:
    stem = Path(original_file_name or "resume").stem
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "resume"
    suffix = "optimized" if use_optimized else "preview"
    return f"{stem}_{suffix}.pdf"


async def _store_upload(file: UploadFile) -> tuple[str, str, int, str]:
    filename = file.filename or "resume"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_RESUME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload a PDF or DOCX resume.")

    contents = await file.read()
    if len(contents) > settings.max_file_bytes:
        raise HTTPException(status_code=400, detail="File too large. Max 5 MB.")
    file_hash = hashlib.sha256(contents).hexdigest()

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        temp_path = tmp.name

    return filename, temp_path, len(contents), file_hash


def _serialize_public_portfolio(portfolio: dict) -> dict:
    profile = portfolio.get("profile") or {}
    return {
        "profile": {
            "display_name": profile.get("display_name") or "",
            "headline": profile.get("headline") or "",
            "summary": profile.get("summary") or "",
            "location": profile.get("location") or "",
            "primary_role": profile.get("primary_role") or "",
            "hero_statement": profile.get("hero_statement") or "",
        },
        "metrics": portfolio.get("metrics") or {},
        "projects": portfolio.get("projects") or [],
        "activity": portfolio.get("activity") or [],
        "proof_cards": portfolio.get("proof_cards") or [],
    }


def _load_parsed_resume(
    temp_path: str,
    filename: str,
    file_hash: str,
    owner_firebase_uid: str | None = None,
) -> dict:
    parsed_resume = get_parsed_resume_by_source_hash(
        settings.database_url,
        file_hash,
        parser_version=PARSER_VERSION,
        owner_firebase_uid=owner_firebase_uid,
    )
    if parsed_resume:
        parsed_resume["file_name"] = filename
        parsed_resume.setdefault("metadata", {})["source_file_hash"] = file_hash
        if owner_firebase_uid:
            parsed_resume.setdefault("metadata", {})["owner_firebase_uid"] = owner_firebase_uid
        logger.info(
            "Reusing parsed resume parsed_resume_id=%s file_hash=%s",
            parsed_resume.get("id"),
            file_hash[:12],
        )
        return parsed_resume

    parsed_resume = parse_resume(temp_path)
    parsed_resume["file_name"] = filename
    parsed_resume.setdefault("metadata", {})["source_file_hash"] = file_hash
    if owner_firebase_uid:
        parsed_resume.setdefault("metadata", {})["owner_firebase_uid"] = owner_firebase_uid
    return parsed_resume


@app.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str | None = Form(default=None),
    job_url: str | None = Form(default=None),
    identity: FirebaseIdentity | None = Depends(require_workspace_identity),
):
    """
    Upload a resume file and run the pipeline.

    Accepts PDF or DOCX uploads. Job description is optional for now.
    """
    filename, temp_path, size_bytes, file_hash = await _store_upload(file)
    owner_firebase_uid = identity.uid if identity else None

    logger.info("Analyzing resume file=%s size_bytes=%s", filename, size_bytes)
    try:
        parsed_resume = _load_parsed_resume(temp_path, filename, file_hash, owner_firebase_uid=owner_firebase_uid)
        result = run_resume_pipeline(temp_path, job_description, parsed_resume=parsed_resume)
        persistence_ids = persist_pipeline_result(
            settings.database_url,
            result,
            job_url=job_url,
            owner_firebase_uid=owner_firebase_uid,
        )
        version_snapshot = None
        if persistence_ids and persistence_ids.get("parsed_resume_id"):
            score_meta = result.optimized.get("metadata", {}).get("scores", {})
            before_total = int(round(score_meta.get("original", {}).get("total", 0)))
            after_total = int(round(score_meta.get("optimized", {}).get("total", before_total)))
            version_snapshot = persist_resume_version(
                settings.database_url,
                persistence_ids.get("parsed_resume_id"),
                source="optimize",
                resume_text=result.optimized.get("text", ""),
                document=result.optimized.get("document", {}),
                metadata={
                    "mode": "analyze",
                    "job_url": job_url,
                    "edit_type": "optimize",
                    "target_section": "resume",
                    "target_path": "resume",
                    "reason": "Generated an optimized draft from the uploaded resume and job context.",
                    "score_delta": after_total - before_total,
                },
                owner_firebase_uid=owner_firebase_uid,
            )
        if version_snapshot:
            result.optimized.setdefault("metadata", {})["version_snapshot"] = version_snapshot
        if persistence_ids:
            logger.info(
                "Persisted resume analysis parsed_resume_id=%s analysis_id=%s optimized_resume_id=%s",
                persistence_ids.get("parsed_resume_id"),
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
async def apply_resume_suggestions(
    file: UploadFile = File(...),
    suggestions: str = Form(...),
    identity: FirebaseIdentity | None = Depends(require_workspace_identity),
):
    if not suggestions.strip():
        raise HTTPException(status_code=400, detail="Paste at least one suggestion before applying changes.")

    filename, temp_path, size_bytes, file_hash = await _store_upload(file)
    owner_firebase_uid = identity.uid if identity else None

    logger.info("Applying resume suggestions file=%s size_bytes=%s", filename, size_bytes)
    try:
        parsed_resume = _load_parsed_resume(temp_path, filename, file_hash, owner_firebase_uid=owner_firebase_uid)
        result = apply_suggestion_pipeline(temp_path, suggestions, parsed_resume=parsed_resume)
        persistence_ids = persist_pipeline_result(
            settings.database_url,
            result,
            owner_firebase_uid=owner_firebase_uid,
        )
        version_snapshot = None
        if persistence_ids and persistence_ids.get("parsed_resume_id"):
            readiness_before = int(result.application_readiness.get("score", 0))
            readiness_after = int(result.application_readiness.get("projected_score", readiness_before))
            version_snapshot = persist_resume_version(
                settings.database_url,
                persistence_ids.get("parsed_resume_id"),
                source="suggestions",
                resume_text=result.optimized.get("text", ""),
                document=result.optimized.get("document", {}),
                metadata={
                    "mode": "suggestions",
                    "edit_type": "suggestions",
                    "target_section": "resume",
                    "target_path": "resume",
                    "reason": "Applied external suggestions to the structured resume.",
                    "score_delta": readiness_after - readiness_before,
                },
                owner_firebase_uid=owner_firebase_uid,
            )
        if version_snapshot:
            result.optimized.setdefault("metadata", {})["version_snapshot"] = version_snapshot
        if persistence_ids:
            logger.info(
                "Persisted suggestion run parsed_resume_id=%s analysis_id=%s optimized_resume_id=%s",
                persistence_ids.get("parsed_resume_id"),
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


@app.post("/resume/edit")
async def edit_resume(
    payload: ResumeEditRequest,
    identity: FirebaseIdentity | None = Depends(require_workspace_identity),
):
    try:
        edit_result = apply_resume_edit(
            original_document=payload.original_document,
            current_document=payload.current_document,
            instruction=payload.instruction,
            target=payload.target.model_dump(),
            job_description=payload.job_description or "",
        )
        version_snapshot = persist_resume_version(
            settings.database_url,
            payload.parsed_resume_id,
            source="manual_edit",
            resume_text=edit_result["optimized"]["text"],
            document=edit_result["optimized"]["document"],
            metadata={
                "edit_type": "bullet_edit",
                "target_section": payload.target.section,
                "target_path": f"experience[{payload.target.entry_index}].bullets[{payload.target.bullet_index}]",
                "instruction": payload.instruction.strip(),
                "reason": edit_result["edit"].get("reason"),
                "score_delta": edit_result["edit"].get("score_delta", 0),
                "target": payload.target.model_dump(),
            },
            parent_version_id=payload.parent_version_id,
            owner_firebase_uid=identity.uid if identity else None,
        )
        if version_snapshot:
            edit_result["optimized"].setdefault("metadata", {})["version_snapshot"] = version_snapshot
        logger.info(
            "Resume edit applied parsed_resume_id=%s entry_index=%s bullet_index=%s",
            payload.parsed_resume_id,
            payload.target.entry_index,
            payload.target.bullet_index,
        )
        return {"status": "ok", "result": edit_result}
    except ValueError as exc:
        logger.warning("Resume edit rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume edit failed")
        raise HTTPException(status_code=500, detail="Resume edit failed.") from exc


@app.post("/resume/apply_fixes")
async def apply_resume_fix_pass(
    payload: ResumeFixRequest,
    identity: FirebaseIdentity | None = Depends(require_workspace_identity),
):
    try:
        fix_result = apply_resume_fixes(
            original_document=payload.original_document,
            current_document=payload.current_document,
            job_description=payload.job_description,
            analysis=payload.analysis,
            missing_signals=payload.missing_signals,
        )
        version_snapshot = persist_resume_version(
            settings.database_url,
            payload.parsed_resume_id,
            source="apply_fixes",
            resume_text=fix_result["optimized"]["text"],
            document=fix_result["optimized"]["document"],
            metadata={
                "edit_type": "apply_fixes",
                "target_section": "resume",
                "target_path": "resume",
                "reason": fix_result["analysis"].get("summary"),
                "score_delta": int(round(
                    fix_result["optimized"].get("metadata", {}).get("scores", {}).get("optimized", {}).get("total", 0)
                    - fix_result["optimized"].get("metadata", {}).get("scores", {}).get("original", {}).get("total", 0)
                )),
            },
            parent_version_id=payload.parent_version_id,
            owner_firebase_uid=identity.uid if identity else None,
        )
        if version_snapshot:
            fix_result["optimized"].setdefault("metadata", {})["version_snapshot"] = version_snapshot
        logger.info(
            "Resume fixes applied parsed_resume_id=%s applied=%s rejected=%s",
            payload.parsed_resume_id,
            len(fix_result.get("fixes", {}).get("applied", [])),
            len(fix_result.get("fixes", {}).get("rejected", [])),
        )
        return {"status": "ok", "result": fix_result}
    except ValueError as exc:
        logger.warning("Resume fix pass rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume fix pass failed")
        raise HTTPException(status_code=500, detail="Resume fix pass failed.") from exc


@app.post("/resume/download")
async def download_resume_pdf(payload: ResumeDownloadRequest):
    resume_text = payload.resume_text.strip()
    if not resume_text and not payload.document:
        raise HTTPException(status_code=400, detail="Resume text is required for PDF export.")

    try:
        if payload.document:
            document = ResumeDocument.model_validate(payload.document)
        else:
            document = build_resume_document(resume_text, role_label=payload.role_label)
        document, polish_meta = polish_resume_text(document, role_label=payload.role_label)
    except Exception as exc:
        logger.warning("Resume export payload could not be normalized: %s", exc)
        raise HTTPException(status_code=400, detail="Resume document payload is invalid.") from exc

    try:
        pdf_bytes, rendered_document, render_meta = render_resume_pdf(
            document,
            layout_density=payload.layout_density,
        )
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
        "Generated resume PDF file=%s pages=%s name=%s polished=%s",
        payload.file_name,
        render_meta.get("page_count", 0),
        rendered_document.name,
        polish_meta.get("applied", False),
    )

    return FileResponse(
        temp_path,
        media_type="application/pdf",
        filename=_pdf_file_name(payload.file_name, payload.use_optimized),
        background=BackgroundTask(_cleanup_file, temp_path),
    )
