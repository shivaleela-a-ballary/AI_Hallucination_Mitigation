from pydantic import BaseModel
from typing import List


class Source(BaseModel):
    title: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    verification_status: str
    confidence_score: float
    sources: List[Source]