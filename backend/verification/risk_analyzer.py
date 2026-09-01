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

        # 4. Source Reliability Score (0-100)
        if num_evidence == 0:
            source_reliability_score = 0
            source_reliability_label = "Low"
        else:
            base_authorities = []
            for doc in evidence:
                src_lower = (doc.source or "").lower()
                st_lower = (doc.source_type or "").lower()
                if "pubmed" in src_lower or "crossref" in src_lower or st_lower == "peer_reviewed_journal":
                    auth = 0.95
                elif "scifact" in src_lower or st_lower == "scientific_corpus":
                    auth = 0.92
                elif "upload" in src_lower or "upload" in st_lower or "user" in src_lower:
                    auth = 0.88
                elif "arxiv" in src_lower or "semantic" in src_lower or st_lower == "preprint":
                    auth = 0.86
                elif "wikipedia" in src_lower or st_lower == "encyclopedia":
                    auth = 0.78
                else:
                    auth = 0.75

                # Metadata completeness bonus
                if doc.doi or doc.pmid:
                    auth += 0.03
                if doc.authors:
                    auth += 0.02
                base_authorities.append(min(1.0, auth))

            avg_auth = sum(base_authorities) / len(base_authorities)
            sim_factor = min(1.0, max(0.4, avg_similarity))
            source_reliability_score = int(round((0.65 * avg_auth + 0.35 * sim_factor) * 100))
            source_reliability_score = max(30, min(98, source_reliability_score))
            source_reliability_label = "High" if source_reliability_score >= 80 else "Medium" if source_reliability_score >= 60 else "Low"

        # 5. Hallucination Risk Calculation (Separate from raw model confidence)
        status = contradiction_summary.overall_status

        if status == VerificationStatus.REFUTED:
            risk_score = round(min(0.95, max(0.75, 0.78 + (len(contradicting) * 0.04))), 2)
            hallucination_risk = "HIGH"
        elif status == VerificationStatus.UNVERIFIED:
            # Unverified means corpus lacked matching evidence; not confirmed false, but moderate uncertainty
            risk_score = 0.48
            hallucination_risk = "MEDIUM"
        elif status == VerificationStatus.UNCERTAIN:
            if len(contradicting) > 0 and len(supporting) > 0:
                # Direct conflict
                risk_score = 0.62
                hallucination_risk = "HIGH"
            else:
                risk_score = 0.45
                hallucination_risk = "MEDIUM"
        else:  # SUPPORTED
            base_risk = 0.12
            if evidence_quality == "LOW":
                base_risk += 0.20
            elif evidence_quality == "MEDIUM":
                base_risk += 0.08

            if model_conf < 0.70:
                base_risk += 0.10

            risk_score = round(min(0.40, max(0.08, base_risk)), 2)
            if risk_score <= 0.25:
                hallucination_risk = "LOW"
            elif risk_score <= 0.50:
                hallucination_risk = "MEDIUM"
            else:
                hallucination_risk = "HIGH"

        # 6. Explainable Reasoning Bullets
        bullets: list[str] = []
        if num_evidence > 0:
            source_names = list(dict.fromkeys(doc.source for doc in evidence))
            bullets.append(f"{num_evidence} relevant evidence passage(s) retrieved from {', '.join(source_names)}.")
        else:
            bullets.append("No sufficiently relevant evidence was retrieved from the indexed corpora.")

        if len(supporting) > 0:
            bullets.append(f"{len(supporting)} source(s) directly support the claim with affirmative findings.")

        if len(contradicting) > 0:
            bullets.append(f"{len(contradicting)} source(s) contradict the claim with conflicting or opposing results.")

        if len(uncertain) > 0 and num_evidence > len(uncertain):
            bullets.append(f"{len(uncertain)} source(s) were topically related but neutral or non-definitive.")

        if num_evidence > 0:
            bullets.append(f"Evidence quality evaluated as {evidence_quality} (average relevance score: {avg_similarity * 100:.1f}%).")
            bullets.append(f"Source reliability evaluated at {source_reliability_score}% ({source_reliability_label} Reliability).")

        if model_conf > 0:
            bullets.append(f"SciBERT sequence classifier confidence: {model_conf * 100:.1f}%.")

        if status == VerificationStatus.UNVERIFIED:
            bullets.append("Status is UNVERIFIED: Insufficient matching evidence exists in current corpora to confirm or reject this claim.")
        elif hallucination_risk == "LOW":
            bullets.append("Hallucination Risk is LOW: High evidence consensus and strong source agreement.")
        elif hallucination_risk == "MEDIUM":
            bullets.append("Hallucination Risk is MEDIUM: Moderate evidence support or nuanced population variation.")
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
