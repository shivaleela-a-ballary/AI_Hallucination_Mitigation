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
    reliability_score: int = 85


class ClaimResponse(BaseModel):
    id: Optional[int] = None
    claim: str
    claim_type: str = "factual"  # "general", "scientific", "medical", "factual"
    importance: str = "high"     # "high", "medium", "low"
    status: str
    verdict: Optional[str] = None
    evidence_titles: List[str] = Field(default_factory=list)
    evidence_score: float = 0.0
    hallucination_risk_score: Optional[int] = None
    hallucination_risk_label: Optional[str] = None
    supporting_count: int = 0
    contradicting_count: int = 0
    neutral_count: int = 0
    unverified_count: int = 0
    evidence_summary: Optional[str] = None
    explanation: Optional[str] = None
    key_takeaway: Optional[str] = None
    method: str = "HuggingFace NLI + Multi-Source Evidence"


class ChatResponse(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    analyzed_at: Optional[str] = None
    query: Optional[str] = None
    knowledge_graph: Optional[dict] = None
    answer: str
    corrected_answer: Optional[str] = None
    key_takeaway: Optional[str] = None
    verification_status: str
    overall_verdict: Optional[str] = None
    confidence_score: float
    confidence_percentage: Optional[int] = None
    confidence_available: bool = False
    hallucination_risk_score: Optional[int] = None
    hallucination_risk_label: Optional[str] = None
    source_reliability_score: Optional[int] = None
    source_reliability_label: Optional[str] = None
    contradictions_detected: Optional[str] = None
    contradictions_subtext: Optional[str] = None
    sources: List[Source] = Field(default_factory=list)
    evidence: List[Source] = Field(default_factory=list)
    supporting_evidence: List[Source] = Field(default_factory=list)
    contradicting_evidence: List[Source] = Field(default_factory=list)
    uncertain_evidence: List[Source] = Field(default_factory=list)
    unverified_evidence: List[Source] = Field(default_factory=list)
    claims: List[ClaimResponse] = Field(default_factory=list)
    flagged_reasons: List[dict] = Field(default_factory=list)
    confidence_explanation: str = ""
    evidence_quality: str = "MEDIUM"
    hallucination_risk: str = "MEDIUM"
    explanation: str = ""
    explanation_bullets: List[str] = Field(default_factory=list)


class VerificationResponse(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    analyzed_at: Optional[str] = None
    claim: str
    verification_status: str
    overall_verdict: str = "REFUTED"
    prediction: Optional[str] = None
    confidence_score: float
    confidence_percentage: int = 89
    confidence_available: bool
    probabilities: Optional[Dict[str, float]] = None
    hallucination_risk_score: int = 82
    hallucination_risk_label: str = "High Risk"
    source_reliability_score: int = 92
    source_reliability_label: str = "High Reliability"
    contradiction_status: str = "CONFLICTING EVIDENCE"
    contradictions_subtext: str = "5 contradict • 1 support"
    supporting_count: int = 1
    contradicting_count: int = 5
    neutral_count: int = 2
    unverified_count: int = 0
    key_takeaway: str = ""
    disclaimer: str = (
        "This system provides automated analysis based on scientific literature and AI models. "
        "Results should be considered as guidance and not a replacement for professional medical advice."
    )
    why_flagged_list: List[dict] = Field(default_factory=list)
    evidence: List[Source] = Field(default_factory=list)
    supporting_evidence: List[Source] = Field(default_factory=list)
    contradicting_evidence: List[Source] = Field(default_factory=list)
    uncertain_evidence: List[Source] = Field(default_factory=list)
    unverified_evidence: List[Source] = Field(default_factory=list)
    source_summary: Dict[str, int] = Field(default_factory=dict)
    claims: List[ClaimResponse] = Field(default_factory=list)
    confidence_explanation: str
    evidence_quality: str = "HIGH"
    hallucination_risk: str = "HIGH"
    explanation: str = ""
    explanation_bullets: List[str] = Field(default_factory=list)
    knowledge_graph: dict = Field(default_factory=lambda: {"nodes": [], "edges": []})


class CheckAnswerClaim(BaseModel):
    claim: str
    claim_type: str = "factual"
    importance: str = "high"
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
    unverified_claims_count: int = 0
    claims: List[CheckAnswerClaim] = Field(default_factory=list)
    summary: str
