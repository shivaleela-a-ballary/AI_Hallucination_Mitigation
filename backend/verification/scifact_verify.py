"""Explainable baseline for claim verification when no trained SciFact model exists."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from retrieval.retrieve import RetrievedDocument
from .scifact.inference import SciFactInference


class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class Claim:
    text: str
    evidence_titles: list[str]


@dataclass(frozen=True)
class ClaimVerification:
    claim: str
    status: VerificationStatus
    evidence_titles: list[str]
    evidence_score: float
    method: str = "semantic-evidence baseline (not a trained SciFact model)"


class BaselineSciFactVerifier:
    """A transparent evidence-similarity baseline, not a SciFact-trained model."""

    support_threshold = 0.55

    def extract_claims(self, text: str, evidence: Sequence[RetrievedDocument]) -> list[Claim]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        titles = [document.title for document in evidence]
        return [Claim(text=sentence, evidence_titles=titles) for sentence in sentences]

    def verify(self, claims: Sequence[Claim], evidence: Sequence[RetrievedDocument]) -> list[ClaimVerification]:
        if not evidence:
            return [
                ClaimVerification(claim.text, VerificationStatus.UNCERTAIN, [], 0.0)
                for claim in claims
            ]

        top_score = max(max(document.similarity_score, 0.0) for document in evidence)
        evidence_titles = [document.title for document in evidence]
        results: list[ClaimVerification] = []
        for claim in claims:
            claim_words = set(re.findall(r"[a-zA-Z]{3,}", claim.text.lower()))
            evidence_text = " ".join(document.content.lower() for document in evidence)
            negated = any(f"not {word}" in evidence_text for word in claim_words)
            if negated:
                status = VerificationStatus.REFUTED
            elif top_score >= self.support_threshold:
                status = VerificationStatus.SUPPORTED
            else:
                status = VerificationStatus.UNCERTAIN
            results.append(ClaimVerification(claim.text, status, evidence_titles, top_score))
        return results


class LocalSciFactVerifier:
    """Verification backed by the project's local, trained SciFact checkpoint."""

    def __init__(self, model_path: str) -> None:
        self.inference = SciFactInference(model_path)

    def extract_claims(self, text: str, evidence: Sequence[RetrievedDocument]) -> list[Claim]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        return [Claim(text=sentence, evidence_titles=[item.title for item in evidence]) for sentence in sentences]

    def verify(self, claims: Sequence[Claim], evidence: Sequence[RetrievedDocument]) -> list[ClaimVerification]:
        if not evidence:
            return [ClaimVerification(claim.text, VerificationStatus.UNCERTAIN, [], 0.0, "local SciFact checkpoint") for claim in claims]
        evidence_text = "\n".join(item.content for item in evidence)
        titles = [item.title for item in evidence]
        results: list[ClaimVerification] = []
        for claim in claims:
            prediction = self.inference.predict(claim.text, evidence_text)
            results.append(ClaimVerification(
                claim=claim.text,
                status=VerificationStatus(prediction.label),
                evidence_titles=titles,
                evidence_score=prediction.confidence,
                method="local SciFact checkpoint",
            ))
        return results
