from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Source(BaseModel):
    title: str
    content: str
    source: str
    similarity_score: float
    url: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_date: Optional[str] = None
    source_type: str = "scientific"
    relationship: str = "UNCERTAIN"  # "SUPPORTS", "CONTRADICTS", "UNCERTAIN"
    stance_score: float = 0.0


class ClaimResponse(BaseModel):
    claim: str
    status: str
    evidence_titles: List[str]
    evidence_score: float
    method: str


class ChatResponse(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    query: Optional[str] = None
    knowledge_graph: Optional[dict] = None
    answer: str
    verification_status: str
    confidence_score: float
    confidence_available: bool = False
    sources: List[Source] = Field(default_factory=list)
    evidence: List[Source] = Field(default_factory=list)
    supporting_evidence: List[Source] = Field(default_factory=list)
    contradicting_evidence: List[Source] = Field(default_factory=list)
    uncertain_evidence: List[Source] = Field(default_factory=list)
    claims: List[ClaimResponse] = Field(default_factory=list)
    confidence_explanation: str = ""
    evidence_quality: str = "MEDIUM"
    hallucination_risk: str = "MEDIUM"
    explanation: str = ""
    explanation_bullets: List[str] = Field(default_factory=list)


class VerificationResponse(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    claim: str
    verification_status: str
    prediction: Optional[str] = None
    confidence_score: float
    confidence_available: bool
    probabilities: Optional[Dict[str, float]] = None
    evidence: List[Source] = Field(default_factory=list)
    supporting_evidence: List[Source] = Field(default_factory=list)
    contradicting_evidence: List[Source] = Field(default_factory=list)
    uncertain_evidence: List[Source] = Field(default_factory=list)
    source_summary: Dict[str, int] = Field(default_factory=dict)
    claims: List[ClaimResponse] = Field(default_factory=list)
    confidence_explanation: str
    evidence_quality: str = "MEDIUM"
    hallucination_risk: str = "MEDIUM"
    explanation: str = ""
    explanation_bullets: List[str] = Field(default_factory=list)
    knowledge_graph: dict = Field(default_factory=lambda: {"nodes": [], "edges": []})


class CheckAnswerClaim(BaseModel):
    claim: str
    verification_status: str
    confidence_score: float
    hallucination_risk: str
    evidence_count: int
    supporting_evidence: List[Source] = Field(default_factory=list)
    contradicting_evidence: List[Source] = Field(default_factory=list)
    explanation: str = ""


class CheckAnswerResponse(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    original_text: str
    overall_reliability_score: float
    overall_hallucination_risk: str
    total_claims: int
    supported_claims_count: int
    refuted_claims_count: int
    uncertain_claims_count: int
    claims: List[CheckAnswerClaim] = Field(default_factory=list)
    summary: str
