from pydantic import BaseModel
from typing import List


class JobContext(BaseModel):
    """Context for a target job posting."""

    title: str
    company: str
    description: str
    keywords: List[str]
