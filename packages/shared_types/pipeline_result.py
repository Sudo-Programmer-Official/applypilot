from pydantic import BaseModel
from typing import Any, Dict


class PipelineResult(BaseModel):
    """Unified schema for the resume pipeline output."""

    parsed: Dict[str, Any]
    analysis: Dict[str, Any]
    optimized: Dict[str, Any]
    diff: Dict[str, Any]
    ats_score: Dict[str, Any]
    application_readiness: Dict[str, Any]
