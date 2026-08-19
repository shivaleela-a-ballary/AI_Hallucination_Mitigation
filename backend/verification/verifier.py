"""Evidence ranking and explainable confidence scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from retrieval.retrieve import RetrievedDocument
from .scifact_verify import ClaimVerification, VerificationStatus


class EvidenceRanker:
    """Rank evidence by the genuine cosine similarity returned from FAISS."""

    def rank(self, documents: Sequence[RetrievedDocument]) -> list[RetrievedDocument]:
        return sorted(documents, key=lambda item: item.similarity_score, reverse=True)


@dataclass(frozen=True)
class ConfidenceResult:
    score: float
    status: VerificationStatus
    explanation: str


class EvidenceScorer:
    """Score relevance, claim coverage, model confidence, and outcome."""

    def score(
        self,
        evidence: Sequence[RetrievedDocument],
        verifications: Sequence[ClaimVerification],
    ) -> ConfidenceResult:
        if not evidence or not verifications:
            return ConfidenceResult(0.0, VerificationStatus.UNCERTAIN, "No verifiable evidence was retrieved.")

        relevance = sum(max(item.similarity_score, 0.0) for item in evidence) / len(evidence)
        covered_claims = sum(bool(result.evidence_titles) for result in verifications)
        coverage = covered_claims / len(verifications)
        model_confidence = sum(max(result.evidence_score, 0.0) for result in verifications) / len(verifications)
        statuses = [result.status for result in verifications]
        if VerificationStatus.REFUTED in statuses:
            outcome, status = 0.0, VerificationStatus.REFUTED
        elif all(value == VerificationStatus.SUPPORTED for value in statuses):
            outcome, status = 1.0, VerificationStatus.SUPPORTED
        else:
            outcome, status = 0.25, VerificationStatus.UNCERTAIN
        score = round(
            min(1.0, 0.35 * relevance + 0.25 * coverage + 0.25 * outcome + 0.15 * model_confidence),
            4,
        )
        if status == VerificationStatus.REFUTED:
            score = min(score, 0.25)
        explanation = (
            "Retrieval relevance 35% + claim evidence coverage 25% + verification result 25% "
            "+ SciFact model confidence 15%."
        )
        return ConfidenceResult(score, status, explanation)
