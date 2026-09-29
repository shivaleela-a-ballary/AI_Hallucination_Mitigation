"""
Risk Analyzer and Multidimensional Confidence Calculator.
Computes Evidence Quality, Source Agreement, Hallucination Risk, and explainable reasoning narratives.

FORMULA SPECIFICATION:
======================
The hallucination risk score is computed as a transparent, normalized multi-factor model:

    raw_risk = verdict_component + contradiction_component + evidence_gap_component + forensic_component

1. Verdict Component (V):
   - SUPPORTED: Base risk = 0.08. If model confidence >= 0.85, reduced to 0.05.
   - REFUTED: Base risk = 0.70. If model confidence >= 0.85, elevated to 0.78.
   - UNCERTAIN: Base risk = 0.40. Literature is heterogeneous or non-definitive.
   - UNVERIFIED: Base risk = 0.45. Insufficient literature retrieved from corpora.

2. Contradiction Component (K_adj):
   - If contradicting sources K > 0: + min(0.20, K * 0.06).
   - If both supporting S > 0 and contradicting K > 0 (conflicting literature): + 0.08.
   - If supporting S > 0 and K == 0 (unanimous support): - min(0.06, S * 0.02).

3. Evidence Gap Component (G):
   - If number of evidence documents E == 0: + 0.15 (complete lack of evidence).
   - If E == 1: + 0.05 (sparse literature coverage).
   - If average evidence similarity < 0.40: + 0.06 (low relevance).
   - If average evidence similarity >= 0.70 and E >= 3: - 0.04 (dense grounding).

4. Forensic Component (F):
   - For each detected forensic distortion pattern:
     * critical: + 0.12
     * high: + 0.08
     * medium: + 0.04
   - Maximum forensic addition is capped at + 0.22.

5. Final Bounded & Normalized Score:
   risk_score = round(clamp(raw_risk, 0.02, 0.98), 2)  # Strictly 0.0 to 1.0 (display: 0% to 100%)

Risk Categories:
- LOW: 0% - 24% (0.00 <= risk_score <= 0.24)
- MODERATE: 25% - 59% (0.25 <= risk_score <= 0.59)
- HIGH: 60% - 100% (0.60 <= risk_score <= 1.00)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, Sequence

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
    hallucination_risk: str  # "LOW", "MODERATE", "HIGH"
    risk_score: float  # 0.0 (safest) to 1.0 (highest risk of hallucination)
    explanation: str
    explanation_bullets: list[str]


class RiskAnalyzer:
    """
    Computes multidimensional trustworthiness metrics from model outputs,
    retrieval relevance, contradiction ratio, source authority, and forensic signals.
    """

    def evaluate(
        self,
        claim: str,
        evidence: Sequence[RetrievedDocument],
        contradiction_summary: ContradictionSummary,
        verifications: Sequence[ClaimVerification] = (),
        raw_model_confidence: float | None = None,
        detected_forensic_patterns: Optional[Sequence[Any]] = None,
        verdict: Optional[str] = None,
    ) -> RiskReport:
        num_evidence = len(evidence)
        supporting = contradiction_summary.supporting_evidence
        contradicting = contradiction_summary.contradicting_evidence
        uncertain = contradiction_summary.uncertain_evidence

        # ---------------------------------------------------------------------
        # 1. Model Confidence Assessment (0.0 to 1.0)
        # ---------------------------------------------------------------------
        if raw_model_confidence is not None and raw_model_confidence > 0:
            model_conf = min(1.0, max(0.0, raw_model_confidence))
        elif verifications:
            model_conf = sum(max(v.evidence_score, 0.0) for v in verifications) / len(verifications)
        else:
            model_conf = 0.75 if num_evidence > 0 else 0.50

        # ---------------------------------------------------------------------
        # 2. Evidence Quality Assessment
        # ---------------------------------------------------------------------
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

        agreement_ratio = f"{len(supporting)} / {num_evidence}" if num_evidence > 0 else "0 / 0"

        # ---------------------------------------------------------------------
        # 3. Transparent Normalized Risk Calculation
        # ---------------------------------------------------------------------
        if verdict:
            try:
                status = VerificationStatus(verdict.upper())
            except Exception:
                status = contradiction_summary.overall_status
        else:
            status = contradiction_summary.overall_status

        # A. Base Verdict Component (V)
        if status == VerificationStatus.SUPPORTED:
            v_comp = 0.05 if model_conf >= 0.85 else 0.08
        elif status == VerificationStatus.REFUTED:
            v_comp = 0.78 if model_conf >= 0.85 else 0.70
        elif status == VerificationStatus.UNVERIFIED:
            v_comp = 0.38
        else:  # UNCERTAIN
            v_comp = 0.35

        # B. Contradiction Component (K_adj)
        k_count = len(contradicting)
        s_count = len(supporting)
        k_adj = 0.0
        if k_count > 0:
            k_adj += min(0.20, k_count * 0.06)
        if s_count > 0 and k_count > 0:
            k_adj += 0.08  # Severe conflict in literature
        elif s_count > 0 and k_count == 0:
            k_adj -= min(0.06, s_count * 0.02)  # Reassuring consensus

        # C. Evidence Gap Component (G)
        g_comp = 0.0
        if num_evidence == 0:
            g_comp += 0.10
        elif num_evidence == 1:
            g_comp += 0.05

        if avg_similarity < 0.40 and num_evidence > 0:
            g_comp += 0.06
        elif avg_similarity >= 0.70 and num_evidence >= 3:
            g_comp -= 0.04

        # D. Forensic Distortion Component (F)
        f_comp = 0.0
        forensic_details = []
        if detected_forensic_patterns:
            severity_weights = {"critical": 0.12, "high": 0.08, "medium": 0.04, "low": 0.0}
            for p in detected_forensic_patterns:
                p_detected = getattr(p, "detected", False) if hasattr(p, "detected") else p.get("detected", False)
                if p_detected:
                    sev = getattr(p, "severity", "medium") if hasattr(p, "severity") else p.get("severity", "medium")
                    w = severity_weights.get(sev.lower(), 0.04)
                    f_comp += w
                    pat_name = getattr(p, "pattern", "") if hasattr(p, "pattern") else p.get("pattern", "")
                    pat_reason = getattr(p, "reason", "") if hasattr(p, "reason") else p.get("reason", "")
                    if pat_name:
                        forensic_details.append(f"{pat_name}: {pat_reason}" if pat_reason else pat_name)
            f_comp = min(0.22, f_comp)

        # Total Raw Score & Strict Clamping
        raw_risk = v_comp + k_adj + g_comp + f_comp
        final_risk = round(min(0.98, max(0.02, raw_risk)), 2)

        # Standardized Risk Tiers
        # LOW: 0-24%, MEDIUM: 25-59%, HIGH: 60-100%
        if final_risk <= 0.24:
            hallucination_risk = "LOW"
        elif final_risk <= 0.59:
            hallucination_risk = "MEDIUM"
        else:
            hallucination_risk = "HIGH"

        # ---------------------------------------------------------------------
        # 4. Evidence-Grounded Reasoning Bullets (Why Flagged)
        # ---------------------------------------------------------------------
        bullets: list[str] = []
        status_name = status.value if hasattr(status, "value") else str(status)

        if status == VerificationStatus.SUPPORTED:
            bullets.append(
                f"Empirical evidence corroborates the claim (model confidence: {int(model_conf * 100)}%)."
            )
        elif status == VerificationStatus.REFUTED:
            bullets.append(
                f"Peer-reviewed literature directly refutes the claim (model confidence: {int(model_conf * 100)}%)."
            )
        elif status == VerificationStatus.UNVERIFIED:
            bullets.append(
                "Indexed corpora lack sufficient matching evidence to substantiate or refute the assertion."
            )
        else:
            bullets.append(
                "Retrieved literature reports heterogeneous, non-definitive, or conflicting outcomes."
            )

        bullets.append(
            f"Source agreement ratio: {agreement_ratio} ({evidence_quality} evidentiary grounding)."
        )

        if s_count > 0:
            bullets.append(
                f"{s_count} retrieved source(s) affirmatively support the statement."
            )
        else:
            bullets.append("Zero supporting citations identified in indexed scientific corpora.")

        if k_count > 0:
            bullets.append(
                f"{k_count} retrieved source(s) contradict the statement with opposing scientific findings."
            )
        else:
            bullets.append("Zero contradiction signals identified across evaluated literature.")

        if num_evidence == 0:
            bullets.append("No empirical citations were found in indexed repositories.")
        elif num_evidence < 2:
            bullets.append("Only a single relevant source was identified, limiting evidentiary consensus.")

        for f_desc in forensic_details[:3]:
            bullets.append(f"Forensic indicator — {f_desc}")

        primary_explanation = bullets[0] if bullets else "Multi-factor verification and evidence consensus evaluated."

        return RiskReport(
            model_confidence=round(model_conf, 2),
            evidence_quality=evidence_quality,
            source_agreement_ratio=agreement_ratio,
            supporting_count=len(supporting),
            contradicting_count=len(contradicting),
            uncertain_count=len(uncertain),
            hallucination_risk=hallucination_risk,
            risk_score=final_risk,
            explanation=primary_explanation,
            explanation_bullets=bullets,
        )
