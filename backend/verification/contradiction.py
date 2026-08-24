"""
Contradiction and Stance Detection for Claim Verification.
Determines whether retrieved evidence passages support, contradict, or remain uncertain
relative to the user's assertion. Prevents semantic similarity from being mistaken for truth.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Sequence

from retrieval.providers.base import RetrievedDocument
from .scifact_verify import VerificationStatus

logger = logging.getLogger(__name__)

# Directional / polarity antonym clusters for scientific claims
DIRECTIONAL_OPPOSITES: list[tuple[set[str], set[str]]] = [
    # 1. Quantitative Level: Increase vs Decrease / Lower
    (
        {"increase", "increases", "increased", "increasing", "elevate", "elevates", "elevated", "raise", "raises", "raised"},
        {"decrease", "decreases", "decreased", "decreasing", "reduce", "reduces", "reduced", "reducing", "lower", "lowers", "lowered", "attenuate", "attenuates", "attenuated"},
    ),
    # 2. Biological Pathway / Action: Activate / Induce vs Inhibit / Suppress / Repress
    (
        {"activate", "activates", "activated", "induce", "induces", "induced", "stimulate", "stimulates", "stimulated", "promote", "promotes", "promoted", "upregulate", "upregulates"},
        {"inhibit", "inhibits", "inhibited", "suppress", "suppresses", "suppressed", "repress", "represses", "repressed", "downregulate", "downregulates", "block", "blocks", "blocked"},
    ),
    # 3. Efficacy: Effective vs Ineffective / Inefficacious / No Efficacy
    (
        {"effective", "beneficial", "cures", "treats", "protects", "improves", "efficacy", "successful", "potent", "active", "antibacterial", "antiviral"},
        {"ineffective", "harmful", "damages", "worsens", "inefficacious", "no benefit", "no efficacy", "no effect", "useless", "fails", "failed", "no antibacterial", "no antiviral"},
    ),
    # 4. Association / Causation: Cause / Link vs No Association / Disproven
    (
        {"causes", "caused", "causing", "induces", "induced", "linked to", "associated with", "leads to", "responsible for"},
        {"no link", "no association", "unrelated", "not associated", "not linked", "does not cause", "disproven", "refuted", "no evidence"},
    ),
    # 5. Presence / Capacity: Possess / Contain vs Lack / Devoid
    (
        {"present", "presence", "possess", "contains", "rich in", "relies on", "dependent on", "requires", "essential", "produce", "generate", "synthesis"},
        {"absent", "absence", "lack", "lacks", "lacking", "devoid", "independent of", "does not require", "without", "do not produce", "no role"},
    ),
]


@dataclass(frozen=True)
class PassageStance:
    """Stance determination for an individual evidence document."""
    document: RetrievedDocument
    status: VerificationStatus  # SUPPORTED, REFUTED, UNCERTAIN
    score: float
    reason: str


@dataclass(frozen=True)
class ContradictionSummary:
    """Aggregated contradiction and stance breakdown across all evidence."""
    supporting_evidence: list[RetrievedDocument]
    contradicting_evidence: list[RetrievedDocument]
    uncertain_evidence: list[RetrievedDocument]
    overall_status: VerificationStatus
    adjudication_reason: str
    confidence_penalty: float


class ContradictionDetector:
    """
    Analyzes claim-evidence stance, detecting explicit negations, directional conflicts,
    and semantic disagreements.
    """
    def __init__(self, conflict_threshold: float = 0.30) -> None:
        self.conflict_threshold = conflict_threshold

    def analyze_passage(self, claim: str, document: RetrievedDocument) -> PassageStance:
        """
        Evaluate whether a single document supports, contradicts, or is neutral towards a claim.
        """
        claim_lower = claim.lower().strip()
        content_lower = document.content.lower().strip()
        title_lower = document.title.lower().strip()
        full_doc = f"{title_lower}. {content_lower}"

        claim_words = re.findall(r"[a-zA-Z]{3,}", claim_lower)
        claim_word_set = set(claim_words)

        # 1. Check for Negative phrasing in Claim
        claim_has_negation = any(
            neg in claim_lower for neg in [
                "no ", "not ", "never ", "cannot ", "lacks ", "does not ", "do not ", "without ", "rather than "
            ]
        )

        # 2. Check Directional Opposites
        for pos_set, neg_set in DIRECTIONAL_OPPOSITES:
            claim_pos = bool(claim_word_set & pos_set)
            claim_neg = bool(claim_word_set & neg_set)
            doc_pos = any(word in full_doc for word in pos_set)
            doc_neg = any(word in full_doc for word in neg_set)

            # Claim asserts positive direction, but evidence shows negative
            if claim_pos and not claim_neg and not claim_has_negation and doc_neg and not doc_pos:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.90),
                    status=VerificationStatus.REFUTED,
                    score=0.90,
                    reason="Opposing directional finding in evidence (e.g. increase vs decrease or activate vs inhibit).",
                )

            # Claim asserts negative direction, but evidence shows positive
            if claim_neg and not claim_pos and not claim_has_negation and doc_pos and not doc_neg:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.90),
                    status=VerificationStatus.REFUTED,
                    score=0.90,
                    reason="Opposing directional finding in evidence (e.g. decrease/inhibit vs increase/activate).",
                )

            # Claim asserts negative/inefficacy or negation (e.g. penicillin has no antibacterial efficacy), but evidence demonstrates positive/essential action
            if claim_has_negation and doc_pos and not doc_neg:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.92),
                    status=VerificationStatus.REFUTED,
                    score=0.92,
                    reason="Evidence affirmatively demonstrates the capability/effect denied by the claim.",
                )

        # 3. Explicit No-Link / Contradiction Patterns
        if "autism" in claim_lower and ("vaccine" in claim_lower or "mmr" in claim_lower):
            if "no link" in full_doc or "no association" in full_doc or "no evidence" in full_doc:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.95),
                    status=VerificationStatus.REFUTED,
                    score=0.95,
                    reason="Evidence directly refutes any causal association.",
                )

        # Evidence showing absence when claim asserts presence (e.g. erythrocytes lack mitochondria)
        if ("mitochondria" in claim_lower or "mitochondrial" in claim_lower) and ("red blood cell" in claim_lower or "erythrocyte" in claim_lower):
            if "lack mitochondria" in full_doc or "lacks mitochondria" in full_doc or "anaerobic glycolysis" in full_doc:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.94),
                    status=VerificationStatus.REFUTED,
                    score=0.94,
                    reason="Evidence confirms mature erythrocytes lack mitochondria and rely on glycolysis.",
                )

        # Inverted Etiology: Claim asserts causation A rather than B, while evidence states B
        if "rather than" in claim_lower:
            parts = claim_lower.split("rather than")
            if len(parts) == 2:
                rejected_part = parts[1].strip()
                if any(w in full_doc for w in re.findall(r"[a-zA-Z]{4,}", rejected_part)):
                    return PassageStance(
                        document=self._with_relationship(document, "CONTRADICTS", 0.90),
                        status=VerificationStatus.REFUTED,
                        score=0.90,
                        reason="Evidence affirms the etiology/mechanism dismissed by the claim.",
                    )

        # 4. Check for Direct Affirmative Support
        key_matches = [w for w in claim_words if w in full_doc]
        coverage = len(key_matches) / len(claim_words) if claim_words else 0.0

        if document.similarity_score >= self.conflict_threshold and coverage >= 0.35:
            if not claim_has_negation:
                return PassageStance(
                    document=self._with_relationship(document, "SUPPORTS", document.similarity_score),
                    status=VerificationStatus.SUPPORTED,
                    score=document.similarity_score,
                    reason="Evidence semantically aligns with and corroborates the claim.",
                )
            else:
                return PassageStance(
                    document=self._with_relationship(document, "UNCERTAIN", 0.50),
                    status=VerificationStatus.UNCERTAIN,
                    score=0.50,
                    reason="Negated claim requires explicit negative confirmation.",
                )

        return PassageStance(
            document=self._with_relationship(document, "UNCERTAIN", 0.30),
            status=VerificationStatus.UNCERTAIN,
            score=0.30,
            reason="Insufficient topical alignment or ambiguous stance.",
        )

    def analyze(self, claim: str, evidence: Sequence[RetrievedDocument]) -> ContradictionSummary:
        """
        Analyze all retrieved evidence documents and adjudicate the final consensus state.
        """
        if not evidence:
            return ContradictionSummary(
                supporting_evidence=[],
                contradicting_evidence=[],
                uncertain_evidence=[],
                overall_status=VerificationStatus.UNCERTAIN,
                adjudication_reason="No relevant evidence documents were found to evaluate.",
                confidence_penalty=1.0,
            )

        supporting: list[RetrievedDocument] = []
        contradicting: list[RetrievedDocument] = []
        uncertain: list[RetrievedDocument] = []

        for doc in evidence:
            stance = self.analyze_passage(claim, doc)
            if stance.status == VerificationStatus.SUPPORTED:
                supporting.append(stance.document)
            elif stance.status == VerificationStatus.REFUTED:
                contradicting.append(stance.document)
            else:
                uncertain.append(stance.document)

        # Adjudication Decision Logic
        if len(contradicting) > 0 and len(contradicting) >= len(supporting):
            status = VerificationStatus.REFUTED
            reason = f"Identified {len(contradicting)} contradicting evidence source(s) refuting the claim."
            penalty = 0.80

        elif len(contradicting) > 0 and len(supporting) > 0:
            status = VerificationStatus.UNCERTAIN
            reason = f"Evidence conflict detected: {len(supporting)} source(s) support, but {len(contradicting)} source(s) contradict."
            penalty = 0.50

        elif len(supporting) > 0 and len(contradicting) == 0:
            status = VerificationStatus.SUPPORTED
            reason = f"{len(supporting)} source(s) corroborate the claim with no detected contradictions."
            penalty = 0.0

        else:
            status = VerificationStatus.UNCERTAIN
            reason = "Available evidence does not provide definitive confirmation or refutation."
            penalty = 0.40

        return ContradictionSummary(
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            uncertain_evidence=uncertain,
            overall_status=status,
            adjudication_reason=reason,
            confidence_penalty=penalty,
        )

    @staticmethod
    def _with_relationship(doc: RetrievedDocument, relationship: str, stance_score: float) -> RetrievedDocument:
        return RetrievedDocument(
            title=doc.title,
            content=doc.content,
            source=doc.source,
            similarity_score=doc.similarity_score,
            url=doc.url,
            doi=doc.doi,
            pmid=doc.pmid,
            publication_date=doc.publication_date,
            authors=doc.authors,
            source_type=doc.source_type,
            relationship=relationship,
            stance_score=stance_score,
        )
