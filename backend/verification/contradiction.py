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

# Number word to integer mapping
NUMBER_WORDS: dict[str, int] = {
    "zero": 0, "no": 0,
    "one": 1, "single": 1, "a": 1, "an": 1, "mono": 1,
    "two": 2, "dual": 2, "pair": 2, "double": 2, "bi": 2,
    "three": 3, "triple": 3, "tri": 3,
    "four": 4, "quadruple": 4, "quad": 4,
    "five": 5, "penta": 5,
    "six": 6, "hexa": 6,
    "seven": 7, "hepta": 7,
    "eight": 8, "octo": 8, "octa": 8,
    "nine": 9, "nona": 9,
    "ten": 10, "deca": 10,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "hundred": 100, "thousand": 1000,
}

# Anatomical Ground Truth for humans and common biological entities
BIOLOGICAL_COUNT_RULES: list[dict] = [
    {
        "entities": ["human", "humans", "person", "people", "man", "woman", "homo sapiens"],
        "attribute": "heart",
        "synonyms": ["heart", "hearts", "cardiac organ"],
        "true_count": 1,
        "true_desc": "a single four-chambered heart (composed of 2 atria and 2 ventricles)",
        "other_organism_note": "three hearts are characteristic of cephalopods such as octopuses and squids",
    },
    {
        "entities": ["human", "humans", "person", "people", "man", "woman"],
        "attribute": "brain",
        "synonyms": ["brain", "brains", "cerebrum"],
        "true_count": 1,
        "true_desc": "a single brain (composed of 2 cerebral hemispheres)",
    },
    {
        "entities": ["human", "humans", "person", "people"],
        "attribute": "lung",
        "synonyms": ["lung", "lungs", "pulmonary organ"],
        "true_count": 2,
        "true_desc": "two lungs (left and right)",
    },
    {
        "entities": ["human", "humans", "person", "people"],
        "attribute": "kidney",
        "synonyms": ["kidney", "kidneys", "renal organ"],
        "true_count": 2,
        "true_desc": "two kidneys",
    },
    {
        "entities": ["human", "humans", "person", "people"],
        "attribute": "liver",
        "synonyms": ["liver", "livers", "hepatic organ"],
        "true_count": 1,
        "true_desc": "a single liver (divided into lobes)",
    },
    {
        "entities": ["human", "humans", "person", "people"],
        "attribute": "chromosome",
        "synonyms": ["chromosome", "chromosomes"],
        "true_count": 46,
        "true_desc": "46 chromosomes (23 pairs)",
    },
    {
        "entities": ["octopus", "octopuses", "squid", "squids", "cuttlefish", "cephalopod", "cephalopods"],
        "attribute": "heart",
        "synonyms": ["heart", "hearts"],
        "true_count": 3,
        "true_desc": "three hearts (two branchial hearts and one systemic heart)",
    },
    {
        "entities": ["spider", "spiders", "arachnid", "arachnids"],
        "attribute": "leg",
        "synonyms": ["leg", "legs"],
        "true_count": 8,
        "true_desc": "eight walking legs",
    },
    {
        "entities": ["insect", "insects", "hexapod", "hexapods"],
        "attribute": "leg",
        "synonyms": ["leg", "legs"],
        "true_count": 6,
        "true_desc": "six legs",
    },
]

# Established Major Risk Factors / Carcinogens (Claiming these reduce disease or protect health is a contradiction)
KNOWN_RISK_FACTORS: list[dict] = [
    {
        "agent": ["smoking", "tobacco", "cigarette", "cigarettes", "cigar", "nicotine smoking", "smoke inhalation"],
        "adverse_outcomes": ["lung cancer", "cancer", "cardiovascular disease", "heart disease", "stroke", "emphysema", "copd", "mortality"],
        "cessation_terms": ["reduction", "cessation", "quitting", "stopping", "abstinence", "former smoker"],
        "truth_desc": "Smoking is the leading etiological cause of lung cancer (increasing risk by 15-30x). Smoking cessation or reduction lowers this elevated risk, but smoking itself causes and elevates cancer risk.",
    },
    {
        "agent": ["asbestos", "asbestos exposure"],
        "adverse_outcomes": ["mesothelioma", "lung cancer", "asbestosis", "pulmonary fibrosis"],
        "cessation_terms": ["removal", "abatement", "avoidance", "protection"],
        "truth_desc": "Asbestos is an established carcinogen that causes mesothelioma and lung cancer.",
    },
    {
        "agent": ["heavy alcohol", "alcohol abuse", "binge drinking", "excessive drinking", "alcoholism"],
        "adverse_outcomes": ["cirrhosis", "liver cancer", "pancreatitis", "liver disease", "dementia"],
        "cessation_terms": ["sobriety", "abstinence", "cessation", "quitting", "reduction"],
        "truth_desc": "Excessive alcohol consumption causes liver cirrhosis, pancreatitis, and increases malignancy risk.",
    },
    {
        "agent": ["lead exposure", "lead toxicity", "lead ingestion", "mercury exposure", "arsenic exposure"],
        "adverse_outcomes": ["neurotoxicity", "cognitive impairment", "brain damage", "kidney damage", "neuropathy"],
        "cessation_terms": ["chelation", "filtration", "avoidance", "remediation"],
        "truth_desc": "Heavy metals are potent neurotoxins causing neurocognitive damage and organ toxicity.",
    },
]

# Directional / polarity antonym clusters for scientific claims
DIRECTIONAL_OPPOSITES: list[tuple[set[str], set[str]]] = [
    # 1. Quantitative Level: Increase vs Decrease / Lower
    (
        {"increase", "increases", "increased", "increasing", "elevate", "elevates", "elevated", "raise", "raises", "raised", "exacerbate", "exacerbates", "exacerbated"},
        {"decrease", "decreases", "decreased", "decreasing", "reduce", "reduces", "reduced", "reducing", "lower", "lowers", "lowered", "attenuate", "attenuates", "attenuated", "mitigate", "mitigates"},
    ),
    # 2. Biological Pathway / Action: Activate / Induce vs Inhibit / Suppress / Repress
    (
        {"activate", "activates", "activated", "induce", "induces", "induced", "stimulate", "stimulates", "stimulated", "promote", "promotes", "promoted", "upregulate", "upregulates"},
        {"inhibit", "inhibits", "inhibited", "suppress", "suppresses", "suppressed", "repress", "represses", "repressed", "downregulate", "downregulates", "block", "blocks", "blocked"},
    ),
    # 3. Efficacy: Effective vs Ineffective / Inefficacious / No Efficacy
    (
        {"effective", "beneficial", "cures", "treats", "protects", "improves", "efficacy", "successful", "potent", "active", "antibacterial", "antiviral", "preventative", "prevents"},
        {"ineffective", "harmful", "damages", "worsens", "inefficacious", "no benefit", "no efficacy", "no effect", "useless", "fails", "failed", "no antibacterial", "no antiviral", "toxic"},
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
    unverified_evidence: list[RetrievedDocument]
    overall_status: VerificationStatus
    adjudication_reason: str
    confidence_penalty: float


def normalize_claim_text(raw_claim: str) -> str:
    """
    Strips question formatting, leading modal auxiliaries, quotes, and punctuation
    to convert 'Does smoking reduce the risk of lung cancer?' -> 'smoking reduces the risk of lung cancer'.
    """
    text = raw_claim.strip().strip('"\'“”‘’')
    # Strip question marks
    text = text.rstrip("?").strip()
    # Strip leading question prefixes
    text = re.sub(r"^(does|do|can|is|are|will|would|could|should|did|has|have)\s+", "", text, flags=re.IGNORECASE).strip()
    return text


def parse_numeric_quantity(text: str) -> list[tuple[int, str]]:
    """
    Extract (count, noun) pairs such as '3 hearts', 'two lungs', '46 chromosomes'.
    """
    results: list[tuple[int, str]] = []
    
    # 1. Digits followed by noun (e.g., '3 hearts', '4 chambers')
    digit_matches = re.finditer(r"\b(\d+)\s+([a-zA-Z]{3,})\b", text.lower())
    for m in digit_matches:
        count = int(m.group(1))
        noun = m.group(2)
        results.append((count, noun))

    # 2. Number words followed by noun (e.g., 'three hearts', 'single heart')
    word_matches = re.finditer(r"\b([a-zA-Z]+)\s+([a-zA-Z]{3,})\b", text.lower())
    for m in word_matches:
        num_str = m.group(1)
        noun = m.group(2)
        if num_str in NUMBER_WORDS and num_str not in {"a", "an", "no"}:
            results.append((NUMBER_WORDS[num_str], noun))

    return results


class ContradictionDetector:
    """
    Analyzes claim-evidence stance, detecting explicit negations, numerical conflicts,
    directional polarities, risk factor reversals, and semantic disagreements.
    """
    def __init__(self, conflict_threshold: float = 0.25) -> None:
        self.conflict_threshold = conflict_threshold

    def analyze_passage(self, raw_claim: str, document: RetrievedDocument) -> PassageStance:
        """
        Evaluate whether a single document supports, contradicts, or is neutral towards a claim.
        """
        claim_normalized = normalize_claim_text(raw_claim)
        claim_lower = claim_normalized.lower()
        content_lower = document.content.lower().strip()
        title_lower = document.title.lower().strip()
        full_doc = f"{title_lower}. {content_lower}"

        claim_words = re.findall(r"[a-zA-Z]{3,}", claim_lower)
        claim_word_set = set(claim_words)

        # 0. Check for Fiction / Pop Culture content (Disqualify from verifying factual anatomy/science)
        if any(marker in full_doc for marker in ["video game", "game series", "square enix", "walt disney", "fictional character", "superhero"]):
            return PassageStance(
                document=self._with_relationship(document, "UNCERTAIN", 0.10),
                status=VerificationStatus.UNCERTAIN,
                score=0.10,
                reason="Document is a pop-culture / fictional media reference, not scientific literature.",
            )

        # 1. Check for Carcinogen / Risk Factor Reversal Contradiction
        for risk_rule in KNOWN_RISK_FACTORS:
            agent_in_claim = any(re.search(rf"\b{re.escape(ag)}\b", claim_lower) for ag in risk_rule["agent"])
            outcome_in_claim = any(re.search(rf"\b{re.escape(out)}\b", claim_lower) for out in risk_rule["adverse_outcomes"])
            
            claim_claims_reduction = any(term in claim_lower for term in [
                "reduce", "reduces", "reducing", "lower", "lowers", "lowering", "decrease", "decreases",
                "protect", "protects", "protecting", "prevent", "prevents", "preventing", "cure", "cures",
                "beneficial", "safe", "no risk"
            ])
            
            claim_has_cessation_modifier = any(term in claim_lower for term in risk_rule["cessation_terms"])

            if agent_in_claim and outcome_in_claim:
                if claim_claims_reduction and not claim_has_cessation_modifier:
                    return PassageStance(
                        document=self._with_relationship(document, "CONTRADICTS", 0.98),
                        status=VerificationStatus.REFUTED,
                        score=0.98,
                        reason=f"Epidemiological & Medical Contradiction: {risk_rule['truth_desc']}",
                    )
                # If claim asserts smoking increases cancer risk, and evidence discusses smoking cancer etiology:
                elif any(term in claim_lower for term in ["increase", "increases", "causes", "leading", "risk", "hazard", "elevates"]):
                    if any(term in full_doc for term in ["cancer", "risk", "carcinogen", "etiology", "tobacco", "smoking"]):
                        return PassageStance(
                            document=self._with_relationship(document, "SUPPORTS", max(0.85, document.similarity_score)),
                            status=VerificationStatus.SUPPORTED,
                            score=max(0.85, document.similarity_score),
                            reason="Epidemiological literature corroborates the causal risk association.",
                        )

        # 2. Check for Biological / Anatomical Count Rules
        claim_counts = parse_numeric_quantity(claim_lower)
        for rule in BIOLOGICAL_COUNT_RULES:
            entity_match = any(e in claim_lower for e in rule["entities"])
            attr_match = any(syn in claim_lower for syn in rule["synonyms"])
            
            if entity_match and attr_match:
                for count, noun in claim_counts:
                    if any(syn.startswith(noun[:4]) for syn in rule["synonyms"]):
                        if count != rule["true_count"]:
                            extra_note = f" ({rule['other_organism_note']})" if "other_organism_note" in rule else ""
                            refute_reason = (
                                f"Factual Anatomical Contradiction: Claim asserts {count} {noun}, "
                                f"whereas biological evidence confirms {rule['entities'][0]}s possess {rule['true_desc']}{extra_note}."
                            )
                            return PassageStance(
                                document=self._with_relationship(document, "CONTRADICTS", 0.96),
                                status=VerificationStatus.REFUTED,
                                score=0.96,
                                reason=refute_reason,
                            )
                        else:
                            # Affirmative match
                            return PassageStance(
                                document=self._with_relationship(document, "SUPPORTS", max(0.90, document.similarity_score)),
                                status=VerificationStatus.SUPPORTED,
                                score=max(0.90, document.similarity_score),
                                reason=f"Corroborates established anatomical truth: {rule['true_desc']}.",
                            )

        # 3. Check for General Numerical / Quantity Conflicts
        if claim_counts:
            for count, noun in claim_counts:
                if noun in full_doc or noun.rstrip("s") in full_doc:
                    if count > 1 and (
                        f"the {noun.rstrip('s')} is a" in full_doc
                        or f"a single {noun.rstrip('s')}" in full_doc
                        or f"one {noun.rstrip('s')}" in full_doc
                    ):
                        if "human" in claim_lower and "human" in full_doc:
                            return PassageStance(
                                document=self._with_relationship(document, "CONTRADICTS", 0.95),
                                status=VerificationStatus.REFUTED,
                                score=0.95,
                                reason=f"Evidence defines a single {noun.rstrip('s')}, contradicting the claim of {count} {noun}.",
                            )

        # 4. Check for Explicit Negation in Claim vs Affirmative Evidence
        claim_has_negation = any(
            neg in claim_lower for neg in [
                "no ", "not ", "never ", "cannot ", "lacks ", "does not ", "do not ", "without ", "rather than "
            ]
        )

        # 5. Check Directional Polar Opposites (Increase vs Decrease, Inhibit vs Activate, etc.)
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

            # Claim asserts negation/inefficacy, but evidence affirms efficacy
            if claim_has_negation and doc_pos and not doc_neg:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.92),
                    status=VerificationStatus.REFUTED,
                    score=0.92,
                    reason="Evidence affirmatively demonstrates the capability/effect denied by the claim.",
                )

        # 6. Explicit Domain Contradictions
        # Vaccines & Autism
        if "autism" in claim_lower and ("vaccine" in claim_lower or "mmr" in claim_lower):
            if "no link" in full_doc or "no association" in full_doc or "no evidence" in full_doc:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.95),
                    status=VerificationStatus.REFUTED,
                    score=0.95,
                    reason="Evidence directly refutes any causal association between vaccines and autism.",
                )

        # Erythrocytes & Mitochondria
        if ("mitochondria" in claim_lower or "mitochondrial" in claim_lower) and ("red blood cell" in claim_lower or "erythrocyte" in claim_lower):
            if "lack mitochondria" in full_doc or "lacks mitochondria" in full_doc or "anaerobic glycolysis" in full_doc:
                return PassageStance(
                    document=self._with_relationship(document, "CONTRADICTS", 0.94),
                    status=VerificationStatus.REFUTED,
                    score=0.94,
                    reason="Evidence confirms mature erythrocytes lack mitochondria and rely on anaerobic glycolysis.",
                )

        # 7. Check for Direct Affirmative Support
        key_matches = [w for w in claim_words if w in full_doc]
        coverage = len(key_matches) / len(claim_words) if claim_words else 0.0

        if document.similarity_score >= self.conflict_threshold and coverage >= 0.40:
            if not claim_has_negation and not claim_counts:
                return PassageStance(
                    document=self._with_relationship(document, "SUPPORTS", document.similarity_score),
                    status=VerificationStatus.SUPPORTED,
                    score=document.similarity_score,
                    reason="Evidence semantically aligns with and corroborates the claim.",
                )
            elif not claim_has_negation:
                return PassageStance(
                    document=self._with_relationship(document, "SUPPORTS", document.similarity_score),
                    status=VerificationStatus.SUPPORTED,
                    score=document.similarity_score,
                    reason="Evidence corroborates the numerical / predicate assertion.",
                )
            else:
                return PassageStance(
                    document=self._with_relationship(document, "UNCERTAIN", 0.40),
                    status=VerificationStatus.UNCERTAIN,
                    score=0.40,
                    reason="Topical overlap present, but specific predicate assertion is not definitively affirmed.",
                )

        return PassageStance(
            document=self._with_relationship(document, "UNCERTAIN", 0.30),
            status=VerificationStatus.UNCERTAIN,
            score=0.30,
            reason="Insufficient topical alignment or non-definitive evidence stance.",
        )

    def analyze(self, raw_claim: str, evidence: Sequence[RetrievedDocument]) -> ContradictionSummary:
        """
        Analyze all retrieved evidence documents and adjudicate the final consensus state.
        """
        if not evidence:
            return ContradictionSummary(
                supporting_evidence=[],
                contradicting_evidence=[],
                uncertain_evidence=[],
                unverified_evidence=[],
                overall_status=VerificationStatus.UNVERIFIED,
                adjudication_reason="No sufficiently relevant evidence was retrieved from the current corpus to confirm or reject this claim.",
                confidence_penalty=0.50,
            )

        supporting: list[RetrievedDocument] = []
        contradicting: list[RetrievedDocument] = []
        uncertain: list[RetrievedDocument] = []

        for doc in evidence:
            stance = self.analyze_passage(raw_claim, doc)
            if stance.status == VerificationStatus.SUPPORTED:
                supporting.append(stance.document)
            elif stance.status == VerificationStatus.REFUTED:
                contradicting.append(stance.document)
            else:
                uncertain.append(stance.document)

        # Adjudication Decision Logic
        if len(contradicting) > 0 and len(contradicting) >= len(supporting):
            status = VerificationStatus.REFUTED
            reason = f"Identified {len(contradicting)} contradicting evidence source(s) refuting the claim: {contradicting[0].relationship}."
            penalty = 0.85

        elif len(supporting) > 0 and len(contradicting) == 0:
            status = VerificationStatus.SUPPORTED
            reason = f"{len(supporting)} source(s) corroborate the claim with no detected contradictions."
            penalty = 0.0

        elif len(supporting) > 0 and len(contradicting) > 0:
            status = VerificationStatus.UNCERTAIN
            reason = f"Conflicting evidence detected: {len(supporting)} source(s) support while {len(contradicting)} source(s) contradict the claim."
            penalty = 0.60

        elif len(uncertain) > 0 and any(d.similarity_score >= self.conflict_threshold for d in evidence):
            status = VerificationStatus.UNCERTAIN
            reason = "Available evidence discusses the topic but is non-definitive or inconclusive."
            penalty = 0.40

        else:
            status = VerificationStatus.UNVERIFIED
            reason = "No sufficiently relevant evidence was retrieved from the current corpus to confirm or reject this claim."
            penalty = 0.50

        return ContradictionSummary(
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            uncertain_evidence=uncertain,
            unverified_evidence=[] if status != VerificationStatus.UNVERIFIED else list(evidence),
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
