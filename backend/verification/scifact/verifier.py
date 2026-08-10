"""SciFact model-backed verification adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .inference import SciFactInference
from ..scifact_verify import VerificationStatus


@dataclass(frozen=True)
class SciFactVerificationResult:
    claim: str
    status: VerificationStatus
    confidence: float
    probabilities: dict[str, float]
    method: str
    evidence_titles: list[str]
    evidence_score: float


class SciFactModelVerifier:
    """Use the locally trained SciBERT model for evidence verification."""

    def __init__(
        self,
        model_path: str | Path = "models/scifact-sanity",
        max_length: int = 256,
        minimum_evidence_score: float = 0.20,
    ) -> None:
        self.minimum_evidence_score = minimum_evidence_score

        self.inference = SciFactInference(
            model_path=model_path,
            max_length=max_length,
        )

    def verify(
        self,
        claim: str,
        evidence: str,
        evidence_score: float,
        evidence_title: str = "",
    ) -> SciFactVerificationResult:

        # No sufficiently relevant evidence means UNCERTAIN.
        if evidence_score < self.minimum_evidence_score:
            return SciFactVerificationResult(
                claim=claim,
                status=VerificationStatus.UNCERTAIN,
                confidence=0.0,
                probabilities={},
                method=(
                    "SciFact model not used because "
                    "retrieved evidence was insufficient"
                ),
                evidence_titles=[evidence_title] if evidence_title else [],
                evidence_score=float(evidence_score),
            )

        prediction = self.inference.predict(
            claim=claim,
            evidence=evidence,
        )

        if prediction.label == "SUPPORTED":
            status = VerificationStatus.SUPPORTED
        elif prediction.label == "REFUTED":
            status = VerificationStatus.REFUTED
        else:
            status = VerificationStatus.UNCERTAIN

        return SciFactVerificationResult(
            claim=claim,
            status=status,
            confidence=float(prediction.confidence),
            probabilities={
                key: float(value)
                for key, value in prediction.probabilities.items()
            },
            method="local SciBERT evidence classifier",
            evidence_titles=[evidence_title] if evidence_title else [],
            evidence_score=float(evidence_score),
        )