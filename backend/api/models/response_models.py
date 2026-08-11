from pydantic import BaseModel
from typing import List


class Source(BaseModel):
    title: str
    content: str
    source: str
    similarity_score: float


class ClaimResponse(BaseModel):
    claim: str
    status: str
    evidence_titles: List[str]
    evidence_score: float
    method: str


class ChatResponse(BaseModel):
    answer: str
    verification_status: str
    confidence_score: float
    sources: List[Source]
    evidence: List[Source]
    claims: List[ClaimResponse]
    confidence_explanation: str
