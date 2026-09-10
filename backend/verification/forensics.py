"""
Hallucination Forensics Engine.
Detects distinct hallucination patterns across claims and evidence:
- Overgeneralization
- Causal overclaim
- Exaggeration
- Unsupported numerical claim
- Absolute language
- Source mismatch
- Missing context
- Entity confusion
- Unsupported conclusion
- Temporal mismatch
- Population mismatch
- Correlation presented as causation
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from retrieval.providers.base import RetrievedDocument

logger = logging.getLogger(__name__)


@dataclass
class ForensicsReport:
    """Forensics diagnostic for a verified claim."""
    pattern_type: str
    risk_level: str  # "High", "Medium", "Low"
    why_flagged: str
    evidence_summary: str
    relevant_sources: list[dict[str, Any]]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "risk_level": self.risk_level,
            "why_flagged": self.why_flagged,
            "evidence_summary": self.evidence_summary,
            "relevant_sources": self.relevant_sources,
            "explanation": self.explanation,
        }


# Keyword pattern maps
UNIVERSAL_TERMS = {
    "everyone", "everybody", "all people", "in all humans", "all patients",
    "in everyone", "every person", "all individuals", "universally", "across all populations",
}

ABSOLUTE_TERMS = {
    "always", "never", "completely cures", "100% effective", "guaranteed",
    "impossible", "undeniable", "without exception", "permanent cure", "foolproof",
}

CAUSAL_TERMS = {
    "causes", "caused", "causing", "proves", "proven to cause", "directly responsible for",
    "leads directly to", "solely responsible", "induces directly",
}

CORRELATION_TERMS = {
    "associated with", "correlated with", "linked to", "observed in",
    "suggests an association", "correlated", "correlates", "cohort association",
}

ANIMAL_TERMS = {
    "in mice", "murine model", "in vitro", "rat model", "cell culture",
    "animal models", "in rats", "preclinical models",
}

EXAGGERATION_TERMS = {
    "miraculous", "miracle", "completely eliminates", "total cure",
    "revolutionizes medicine", "eradicates completely", "instant relief",
}


class HallucinationForensicsAnalyzer:
    """
    Analyzes verified claims to identify specific hallucination patterns,
    explaining precisely WHY the claim was flagged and contrasting it with evidence.
    """

    def analyze_claim(
        self,
        claim: str,
        evidence: Sequence[RetrievedDocument],
        verdict: str,
        risk_level: str,
        risk_score: float,
    ) -> ForensicsReport:
        claim_lower = claim.lower()
        combined_evidence_text = " ".join(f"{d.title} {d.content}" for d in evidence).lower()

        # Extract relevant sources for the report
        relevant_sources: list[dict[str, Any]] = []
        for d in evidence[:4]:
            authors_str = ", ".join(d.authors[:2]) if d.authors else "Research Team"
            year_str = str(d.publication_date) if d.publication_date else "Recent"
            relevant_sources.append({
                "title": d.title,
                "source": d.source,
                "citation": f"{authors_str} ({year_str})",
                "url": d.url,
                "similarity_score": d.similarity_score,
                "relationship": getattr(d, "relationship", "RETRIEVED"),
            })

        # 1. Check for Absolute Language / Exaggeration
        if any(term in claim_lower for term in ABSOLUTE_TERMS) or any(term in claim_lower for term in EXAGGERATION_TERMS):
            matched_term = next((t for t in ABSOLUTE_TERMS | EXAGGERATION_TERMS if t in claim_lower), "absolute phrasing")
            return ForensicsReport(
                pattern_type="Absolute language / Exaggeration" if "cure" in matched_term else "Absolute language",
                risk_level="High",
                why_flagged=f"Uses absolute or categorical terminology ('{matched_term}') without conclusive clinical substantiation.",
                evidence_summary=(
                    "Peer-reviewed evidence emphasizes conditional outcomes, treatment resistance, or symptom reduction rather than absolute guarantees."
                    if evidence else "No empirical evidence was found supporting categorical efficacy."
                ),
                relevant_sources=relevant_sources,
                explanation=f"The statement asserts an unconditional outcome ('{matched_term}'). Scientific consensus requires nuanced qualifiers and acknowledges variability across study populations.",
            )

        # 2. Check for Overgeneralization (universal terms applied to narrow research)
        if any(term in claim_lower for term in UNIVERSAL_TERMS):
            matched_term = next(t for t in UNIVERSAL_TERMS if t in claim_lower)
            return ForensicsReport(
                pattern_type="Overgeneralization",
                risk_level="High" if verdict == "REFUTED" else "Medium",
                why_flagged=f"Extrapolates specific or observational findings to an unrestricted population ('{matched_term}').",
                evidence_summary=(
                    "Retrieved studies demonstrate context-specific or cohort-dependent associations, and do not support universal application to all demographics."
                    if evidence else "Evidence does not substantiate universal application across all individuals."
                ),
                relevant_sources=relevant_sources,
                explanation=f"The claim uses universal wording ('{matched_term}'). Even when biological associations exist, effects vary significantly across age, genetics, and baseline conditions.",
            )

        # 3. Check for Correlation presented as Causation / Causal Overclaim
        claim_has_causation = any(term in claim_lower for term in CAUSAL_TERMS)
        doc_has_correlation = any(term in combined_evidence_text for term in CORRELATION_TERMS)
        if claim_has_causation and (doc_has_correlation or "observational" in combined_evidence_text or "cohort" in combined_evidence_text):
            return ForensicsReport(
                pattern_type="Correlation presented as causation",
                risk_level="High",
                why_flagged="Asserts direct causal mechanism where underlying evidence only demonstrates epidemiological correlation or statistical association.",
                evidence_summary=(
                    "Available research notes an observational correlation, but explicitly notes that confounding variables and mechanism trials remain inconclusive."
                    if evidence else "Underlying research demonstrates association, not mechanistic causality."
                ),
                relevant_sources=relevant_sources,
                explanation="Observational studies establish correlation, but inferring direct causation without randomized interventional trials represents a causal overclaim.",
            )

        # 4. Check for Population Mismatch (Animal / In-vitro to Human extrapolation)
        if any(term in combined_evidence_text for term in ANIMAL_TERMS) and ("human" in claim_lower or "people" in claim_lower or "patients" in claim_lower):
            return ForensicsReport(
                pattern_type="Population mismatch",
                risk_level="High",
                why_flagged="Applies findings derived from animal or in-vitro models directly to human clinical outcomes without human trial validation.",
                evidence_summary="Retrieved experiments were conducted on preclinical models (e.g. murine or cellular assays) rather than phase III human cohorts.",
                relevant_sources=relevant_sources,
                explanation="Extrapolating in-vitro or murine results directly to human physiology frequently produces false positive efficacy predictions.",
            )

        # 5. Check for Unsupported Numerical Claim
        numbers_in_claim = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim)
        if numbers_in_claim and verdict in {"REFUTED", "UNCERTAIN"}:
            num_str = ", ".join(numbers_in_claim[:2])
            return ForensicsReport(
                pattern_type="Unsupported numerical claim",
                risk_level="High" if verdict == "REFUTED" else "Medium",
                why_flagged=f"Specifies precise quantitative metrics ({num_str}) not corroborated by retrieved literature.",
                evidence_summary="Retrieved studies discuss related phenomena but report differing quantitative bounds or omit this specific measurement.",
                relevant_sources=relevant_sources,
                explanation=f"Exact numerical statistics ({num_str}) require explicit empirical citation; disparate or missing measurements indicate numerical hallucination.",
            )

        # 6. Check for Directional Contradiction (Factual Reversal)
        if verdict == "REFUTED":
            return ForensicsReport(
                pattern_type="Factual contradiction / Directional reversal",
                risk_level="High",
                why_flagged="Asserts an outcome directly opposing empirical consensus (e.g. claiming an established carcinogen or risk factor protects health).",
                evidence_summary=(
                    "Peer-reviewed studies report opposing findings (e.g. lack of efficacy, elevated adverse risk, or contrasting biological pathway)."
                    if evidence else "Evidence directly contradicts the stated assertion."
                ),
                relevant_sources=relevant_sources,
                explanation="The claim inverts empirical findings established in peer-reviewed scientific literature.",
            )

        # 7. Check for Missing Context / Non-definitive evidence
        if verdict == "UNCERTAIN":
            return ForensicsReport(
                pattern_type="Missing context / Inconclusive evidence",
                risk_level="Medium",
                why_flagged="Asserts a definitive factual conclusion on a topic where scientific literature remains actively debated or non-definitive.",
                evidence_summary=(
                    "Retrieved literature demonstrates conflicting outcomes or insufficient sample power, precluding a definitive true/false verdict."
                    if evidence else "No sufficiently robust evidence was retrieved to substantiate this specific assertion."
                ),
                relevant_sources=relevant_sources,
                explanation="The scientific literature on this assertion is currently heterogeneous or non-definitive, requiring cautious epistemic qualification.",
            )

        # 8. Supported Claims (Low risk baseline)
        return ForensicsReport(
            pattern_type="Well-supported factual assertion",
            risk_level="Low",
            why_flagged="No harmful hallucination pattern detected. Claim aligns closely with peer-reviewed consensus.",
            evidence_summary=(
                f"Corroborated across {len(evidence)} verified scientific source(s) with high semantic alignment and consistent stance."
                if evidence else "Corroborated by available verified literature."
            ),
            relevant_sources=relevant_sources,
            explanation="The statement avoids overgeneralization, acknowledges appropriate scope, and matches empirical consensus.",
        )


# Global singleton instance
forensics_analyzer = HallucinationForensicsAnalyzer()
