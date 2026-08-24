"""
Risk Analyzer and Multidimensional Confidence Calculator.
Computes Evidence Quality, Source Agreement, Hallucination Risk, and explainable reasoning narratives.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from retrieval.providers.base import RetrievedDocument
from .contradiction import ContradictionSummary
from .scifact_verify import ClaimVerification, VerificationStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskReport:
    """Multidimensional reliability and risk assessment."""
    model_confidence: float
    evidence_quality: str  # "HIGH", "MEDIUM", "LOW"
    source_agreement_ratio: str  # e.g. "4 / 5"
    supporting_count: int
    contradicting_count: int
    uncertain_count: int
    hallucination_risk: str  # "LOW", "MEDIUM", "HIGH"
    risk_score: float  # 0.0 (safest) to 1.0 (highest risk of hallucination)
    explanation: str
    explanation_bullets: list[str]


class RiskAnalyzer:
    """
    Computes multidimensional trustworthiness metrics from model outputs,
    retrieval relevance, contradiction ratio, and source authority.
    """
    def evaluate(
        self,
        claim: str,
        evidence: Sequence[RetrievedDocument],
        contradiction_summary: ContradictionSummary,
        verifications: Sequence[ClaimVerification],
        raw_model_confidence: float | None = None,
    ) -> RiskReport:
        num_evidence = len(evidence)
        supporting = contradiction_summary.supporting_evidence
        contradicting = contradiction_summary.contradicting_evidence
        uncertain = contradiction_summary.uncertain_evidence

        # 1. Model Confidence
        if raw_model_confidence is not None and raw_model_confidence > 0:
            model_conf = raw_model_confidence
        elif verifications:
            model_conf = sum(max(v.evidence_score, 0.0) for v in verifications) / len(verifications)
        else:
            model_conf = 0.0

        # 2. Evidence Quality Assessment
        if num_evidence == 0:
            evidence_quality = "LOW"
            avg_similarity = 0.0
        else:
            avg_similarity = sum(doc.similarity_score for doc in evidence) / num_evidence
            peer_reviewed_count = sum(1 for doc in evidence if doc.source in {"SciFact", "PubMed"})
            if avg_similarity >= 0.60 and peer_reviewed_count >= 2:
                evidence_quality = "HIGH"
            elif avg_similarity >= 0.35 or peer_reviewed_count >= 1:
                evidence_quality = "MEDIUM"
            else:
                evidence_quality = "LOW"

        # 3. Source Agreement
        agreement_ratio = f"{len(supporting)} / {num_evidence}" if num_evidence > 0 else "0 / 0"

        # 4. Hallucination Risk Calculation
        # Low risk = high supporting consensus, high model confidence, zero contradiction
        # High risk = refuted claim treated as fact, or unverified claims with strong contradiction
        status = contradiction_summary.overall_status

        if status == VerificationStatus.REFUTED:
            risk_score = 0.88 + min(0.12, len(contradicting) * 0.04)
            hallucination_risk = "HIGH"
        elif status == VerificationStatus.UNCERTAIN:
            if num_evidence == 0:
                risk_score = 0.70
                hallucination_risk = "HIGH"
            elif len(contradicting) > 0:
                risk_score = 0.65
                hallucination_risk = "HIGH"
            else:
                risk_score = 0.45
                hallucination_risk = "MEDIUM"
        else:  # SUPPORTED
            # Compute based on quality and agreement
            base_risk = 0.10
            if evidence_quality == "LOW":
                base_risk += 0.25
            elif evidence_quality == "MEDIUM":
                base_risk += 0.10

            if model_conf < 0.70:
                base_risk += 0.15

            risk_score = round(min(0.50, max(0.05, base_risk)), 2)
            if risk_score <= 0.20:
                hallucination_risk = "LOW"
            elif risk_score <= 0.40:
                hallucination_risk = "MEDIUM"
            else:
                hallucination_risk = "HIGH"

        # 5. Explainable Reasoning Bullets
        bullets: list[str] = []
        if num_evidence > 0:
            source_names = list(dict.fromkeys(doc.source for doc in evidence))
            bullets.append(f"{num_evidence} relevant scientific evidence passage(s) retrieved from {', '.join(source_names)}.")
        else:
            bullets.append("No sufficiently relevant scientific evidence was found in indexed corpora.")

        if len(supporting) > 0:
            bullets.append(f"{len(supporting)} source(s) directly support the claim with affirmative findings.")

        if len(contradicting) > 0:
            bullets.append(f"{len(contradicting)} source(s) contradict the claim with conflicting or opposing results.")

        if len(uncertain) > 0 and num_evidence > len(uncertain):
            bullets.append(f"{len(uncertain)} source(s) were topically related but neutral or non-definitive.")

        bullets.append(f"Evidence quality evaluated as {evidence_quality} (average relevance score: {avg_similarity * 100:.1f}%).")

        if model_conf > 0:
            bullets.append(f"SciBERT sequence classifier confidence: {model_conf * 100:.1f}%.")

        if hallucination_risk == "LOW":
            bullets.append("Hallucination Risk is LOW: High evidence consensus and strong source agreement.")
        elif hallucination_risk == "MEDIUM":
            bullets.append("Hallucination Risk is MEDIUM: Moderate evidence support or limited source coverage.")
        else:
            bullets.append("Hallucination Risk is HIGH: Claim is refuted or lacks scientific consensus.")

        explanation_narrative = " ".join(bullets)

        return RiskReport(
            model_confidence=round(model_conf, 4),
            evidence_quality=evidence_quality,
            source_agreement_ratio=agreement_ratio,
            supporting_count=len(supporting),
            contradicting_count=len(contradicting),
            uncertain_count=len(uncertain),
            hallucination_risk=hallucination_risk,
            risk_score=risk_score,
            explanation=explanation_narrative,
            explanation_bullets=bullets,
        )
