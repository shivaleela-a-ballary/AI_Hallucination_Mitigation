from pydantic import BaseModel
from typing import List


class Source(BaseModel):
    title: str
    content: str
    source: str
    similarity_score: float
    url: str | None = None


class ClaimResponse(BaseModel):
    claim: str
    status: str
    evidence_titles: List[str]
    evidence_score: float
    method: str


class ChatResponse(BaseModel):
    id: str | None = None
    created_at: str | None = None
    query: str | None = None
    knowledge_graph: dict | None = None
    answer: str
    verification_status: str
    confidence_score: float
    confidence_available: bool = False
    sources: List[Source]
    evidence: List[Source]
    claims: List[ClaimResponse]
    confidence_explanation: str


class VerificationResponse(BaseModel):
    id: str | None = None
    created_at: str | None = None
    claim: str
    verification_status: str
    confidence_score: float
    confidence_available: bool
    probabilities: dict[str, float] | None = None
    evidence: List[Source]
    claims: List[ClaimResponse]
    confidence_explanation: str
    knowledge_graph: dict
