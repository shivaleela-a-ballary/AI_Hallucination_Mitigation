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
    """Score evidence from similarity, coverage, and verification outcome.

    Formula: 50% mean non-negative cosine similarity, 25% evidence coverage
    (up to four documents), and 25% verification outcome (1/0.25/0 for
    supported/uncertain/refuted).  This is an explainable project baseline.
    """

    def score(
        self,
        evidence: Sequence[RetrievedDocument],
        verifications: Sequence[ClaimVerification],
    ) -> ConfidenceResult:
        if not evidence or not verifications:
            return ConfidenceResult(0.0, VerificationStatus.UNCERTAIN, "No verifiable evidence was retrieved.")

        similarity = sum(max(item.similarity_score, 0.0) for item in evidence) / len(evidence)
        coverage = min(len(evidence), 4) / 4
        statuses = [result.status for result in verifications]
        if VerificationStatus.REFUTED in statuses:
            outcome, status = 0.0, VerificationStatus.REFUTED
        elif all(value == VerificationStatus.SUPPORTED for value in statuses):
            outcome, status = 1.0, VerificationStatus.SUPPORTED
        else:
            outcome, status = 0.25, VerificationStatus.UNCERTAIN
        score = round(min(1.0, 0.5 * similarity + 0.25 * coverage + 0.25 * outcome), 4)
        return ConfidenceResult(score, status, "Similarity 50% + evidence coverage 25% + verification outcome 25%.")
