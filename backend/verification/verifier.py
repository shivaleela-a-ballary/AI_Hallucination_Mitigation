"""Evidence ranking and explainable confidence scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from retrieval.retrieve import RetrievedDocument
from .scifact_verify import VerificationStatus


class EvidenceRanker:
    """Rank evidence by genuine FAISS cosine similarity."""

    def rank(
        self,
        documents: Sequence[RetrievedDocument],
    ) -> list[RetrievedDocument]:
        return sorted(
            documents,
            key=lambda item: item.similarity_score,
            reverse=True,
        )


@dataclass(frozen=True)
class ConfidenceResult:
    score: float
    status: VerificationStatus
    explanation: str


class EvidenceScorer:
    """Calculate explainable confidence from retrieval and verification.

    Formula:
        50% retrieval similarity
        25% evidence coverage
        25% verification outcome
    """

    def score(
        self,
        evidence: Sequence[RetrievedDocument],
        verifications: Sequence[object],
    ) -> ConfidenceResult:

        if not evidence or not verifications:
            return ConfidenceResult(
                score=0.0,
                status=VerificationStatus.UNCERTAIN,
                explanation="No verifiable evidence was retrieved.",
            )

        similarity = (
            sum(
                max(float(item.similarity_score), 0.0)
                for item in evidence
            )
            / len(evidence)
        )

        coverage = min(len(evidence), 4) / 4

        statuses = [
            getattr(result, "status", VerificationStatus.UNCERTAIN)
            for result in verifications
        ]

        normalized_statuses = [
            (
                status.value
                if isinstance(status, VerificationStatus)
                else str(status)
            )
            for status in statuses
        ]

        if VerificationStatus.REFUTED.value in normalized_statuses:
            outcome = 0.0
            status = VerificationStatus.REFUTED

        elif normalized_statuses and all(
            value == VerificationStatus.SUPPORTED.value
            for value in normalized_statuses
        ):
            outcome = 1.0
            status = VerificationStatus.SUPPORTED

        else:
            outcome = 0.25
            status = VerificationStatus.UNCERTAIN

        score = round(
            min(
                1.0,
                0.5 * similarity
                + 0.25 * coverage
                + 0.25 * outcome,
            ),
            4,
        )

        return ConfidenceResult(
            score=score,
            status=status,
            explanation=(
                "Similarity 50% + evidence coverage 25% "
                "+ verification outcome 25%."
            ),
        )