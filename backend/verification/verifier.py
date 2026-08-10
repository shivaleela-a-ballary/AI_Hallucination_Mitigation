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
    """Calculate explainable confidence from retrieval and verification."""

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

        # Use only evidence that has a corresponding verification result.
        pairs = list(zip(evidence, verifications))

        # Retrieval relevance.
        similarity_values = [
            max(float(document.similarity_score), 0.0)
            for document, _ in pairs
        ]

        similarity = sum(similarity_values) / len(similarity_values)

        # Evidence coverage.
        coverage = min(len(pairs), 4) / 4

        # Weight each verification by:
        # retrieval relevance × model confidence.
        support_weight = 0.0
        refute_weight = 0.0
        uncertain_weight = 0.0

        for document, result in pairs:
            status = getattr(
                result,
                "status",
                VerificationStatus.UNCERTAIN,
            )

            confidence = float(
                getattr(result, "confidence", 0.0)
            )

            relevance = max(
                float(document.similarity_score),
                0.0,
            )

            weight = relevance * confidence

            if status == VerificationStatus.SUPPORTED:
                support_weight += weight

            elif status == VerificationStatus.REFUTED:
                refute_weight += weight

            else:
                uncertain_weight += weight

        total_weight = (
            support_weight
            + refute_weight
            + uncertain_weight
        )

        if total_weight <= 0:
            outcome = 0.25
            status = VerificationStatus.UNCERTAIN

        else:
            support_ratio = support_weight / total_weight
            refute_ratio = refute_weight / total_weight

            if support_ratio >= 0.60:
                outcome = support_ratio
                status = VerificationStatus.SUPPORTED

            elif refute_ratio >= 0.60:
                outcome = 0.0
                status = VerificationStatus.REFUTED

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
                "+ weighted verification outcome 25%. "
                "Verification is weighted by retrieval relevance "
                "and SciFact model confidence."
            ),
        )