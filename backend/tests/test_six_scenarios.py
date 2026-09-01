import pytest
from verification.scifact_verify import VerificationStatus, RetrievedDocument
from verification.hf_verifier import HuggingFaceClaimVerifier
from verification.contradiction import ContradictionDetector
from verification.risk_analyzer import RiskAnalyzer
from api.services.llm_service import LLMService


@pytest.fixture
def hf_verifier():
    return HuggingFaceClaimVerifier()


@pytest.fixture
def contradiction_detector():
    return ContradictionDetector()


@pytest.fixture
def risk_analyzer():
    return RiskAnalyzer()


@pytest.fixture
def llm_service():
    return LLMService()


# ---------------------------------------------------------------------------
# Test 1: Basic factual question
# "How many hearts does a human have?"
# Must NOT be marked REFUTED due to lack of SciFact.
# ---------------------------------------------------------------------------
def test_scenario_1_basic_factual_question(llm_service, hf_verifier):
    question = "How many hearts does a human have?"
    structured_output = llm_service.generate_structured_answer(question)
    
    assert structured_output.answer is not None
    assert "one" in structured_output.answer.lower() or "1" in structured_output.answer
    assert len(structured_output.claims) >= 1
    
    # Mock retrieval from general knowledge (Wikipedia/Anatomy)
    anatomy_doc = RetrievedDocument(
        title="Human Anatomy: Cardiovascular System",
        content="The human heart is a single muscular organ located in the mediastinum of the thorax with four chambers.",
        source="General Medical Knowledge",
        similarity_score=0.92,
    )
    
    report = hf_verifier.verify_single_claim(
        claim_text=structured_output.claims[0].claim,
        evidence=[anatomy_doc],
        claim_index=1,
    )
    
    assert report.verdict != "REFUTED", "Basic factual truth must not be refuted"
    assert report.verdict in ["SUPPORTED", "UNVERIFIED", "UNCERTAIN"]


# ---------------------------------------------------------------------------
# Test 2: Clearly supported scientific claim
# "Smoking increases the risk of lung cancer."
# Must be marked SUPPORTED with low hallucination risk.
# ---------------------------------------------------------------------------
def test_scenario_2_clearly_supported_scientific_claim(hf_verifier):
    claim = "Smoking increases the risk of lung cancer."
    evidence_docs = [
        RetrievedDocument(
            title="Tobacco smoke carcinogens and lung cancer",
            content="Cigarette smoking is the primary cause of lung cancer, increasing risk by 15- to 30-fold.",
            source="PubMed Central",
            similarity_score=0.94,
            pmid="12345678",
        ),
        RetrievedDocument(
            title="Epidemiology of lung cancer and smoking",
            content="Extensive epidemiological evidence establishes that tobacco smoking directly causes lung carcinoma.",
            source="Crossref",
            similarity_score=0.91,
            doi="10.1016/j.lungcan.2021.01.001",
        ),
    ]
    
    report = hf_verifier.verify_single_claim(claim, evidence_docs, claim_index=1)
    
    assert report.verdict == "SUPPORTED"
    assert report.supporting_count >= 1
    assert report.contradicting_count == 0
    assert report.hallucination_risk_score <= 35
    assert report.hallucination_risk_label == "Low"


# ---------------------------------------------------------------------------
# Test 3: Clearly false / reversed claim
# "Smoking reduces the risk of lung cancer."
# Must be marked REFUTED with high hallucination risk and corrected answer.
# ---------------------------------------------------------------------------
def test_scenario_3_clearly_false_reversed_claim(hf_verifier):
    claim = "Smoking reduces the risk of lung cancer."
    evidence_docs = [
        RetrievedDocument(
            title="Tobacco smoke and oncogenesis",
            content="Smoking is the single greatest risk factor for lung cancer and substantially elevates malignant transformation. It does not prevent or reduce cancer risk.",
            source="PubMed Central",
            similarity_score=0.92,
            pmid="87654321",
        )
    ]
    
    report = hf_verifier.verify_single_claim(claim, evidence_docs, claim_index=1)
    
    assert report.verdict == "REFUTED"
    assert report.contradicting_count >= 1
    assert report.hallucination_risk_score >= 70
    assert report.hallucination_risk_label == "High"
    
    full_analysis = hf_verifier.generate_full_analysis(
        question="Does smoking reduce the risk of lung cancer?",
        claims=[claim],
        evidence_map={claim: evidence_docs},
        candidate_answer="Smoking has been claimed to reduce cancer risk.",
    )
    
    assert full_analysis.overall_verdict == "REFUTED"
    assert "increases" in full_analysis.corrected_answer.lower() or "not" in full_analysis.corrected_answer.lower()
    assert full_analysis.overall_hallucination_risk >= 70


# ---------------------------------------------------------------------------
# Test 4: Conflicting evidence
# "Drinking coffee improves memory and cognitive health."
# Must detect contradictions / mixed stances -> UNCERTAIN.
# ---------------------------------------------------------------------------
def test_scenario_4_conflicting_evidence(hf_verifier, contradiction_detector):
    claim = "Drinking coffee improves memory and cognitive performance in all individuals."
    evidence_docs = [
        RetrievedDocument(
            title="Caffeine and acute cognitive enhancement",
            content="Low doses of caffeine improved working memory and reaction time in young adult cohorts.",
            source="PubMed Central",
            similarity_score=0.88,
        ),
        RetrievedDocument(
            title="Long-term cognitive effects of coffee consumption",
            content="Clinical trials found that coffee does not improve memory retention in all individuals and high intake was associated with cognitive decline.",
            source="Crossref",
            similarity_score=0.86,
        ),
    ]
    
    report = hf_verifier.verify_single_claim(claim, evidence_docs, claim_index=1)
    
    # When evidence has both supporting and contradicting outcomes -> UNCERTAIN
    assert report.verdict in ["UNCERTAIN", "REFUTED"]
    assert report.total_evidence_count == 2
    
    full_analysis = hf_verifier.generate_full_analysis(
        question="Does drinking coffee improve brain health?",
        claims=[claim],
        evidence_map={claim: evidence_docs},
        candidate_answer="Coffee improves brain health for everyone.",
    )
    
    assert full_analysis.contradictions_detected == "Yes"
    assert full_analysis.overall_verdict in ["UNCERTAIN", "REFUTED"]


# ---------------------------------------------------------------------------
# Test 5: No evidence / obscure claim
# "Zephyros XI discovered Martian crystals in 2049."
# Must yield UNVERIFIED, NEVER REFUTED or UNSUPPORTED.
# ---------------------------------------------------------------------------
def test_scenario_5_no_evidence_obscure_claim(hf_verifier, risk_analyzer):
    claim = "Zephyros XI discovered Martian crystals in 2049."
    # Zero matching evidence returned
    empty_evidence: list[RetrievedDocument] = []
    
    report = hf_verifier.verify_single_claim(claim, empty_evidence, claim_index=1)
    
    # Crucial Rule: Lack of evidence MUST NEVER be treated as REFUTED
    assert report.verdict == "UNVERIFIED", "Zero evidence must produce UNVERIFIED, not REFUTED"
    assert report.supporting_count == 0
    assert report.contradicting_count == 0
    assert report.total_evidence_count == 0
    assert "UNVERIFIED" in report.why_flagged_desc or "unverified" in report.explanation.lower()
    
    # Test Risk Analyzer handling of UNVERIFIED
    from verification.contradiction import ContradictionSummary
    contra_sum = ContradictionSummary(
        supporting_evidence=[],
        contradicting_evidence=[],
        uncertain_evidence=[],
        unverified_evidence=[],
        overall_status=VerificationStatus.UNVERIFIED,
        adjudication_reason="No matching evidence found in corpus.",
        confidence_penalty=0.50,
    )
    risk_rep = risk_analyzer.evaluate(
        claim=claim,
        evidence=[],
        contradiction_summary=contra_sum,
        verifications=[],
        raw_model_confidence=0.5,
    )
    assert risk_rep.hallucination_risk == "MEDIUM"


# ---------------------------------------------------------------------------
# Test 6: Multi-claim answer
# Claim 1: "Smoking causes lung cancer." (SUPPORTED)
# Claim 2: "Penicillin is ineffective against bacterial infections." (REFUTED)
# ---------------------------------------------------------------------------
def test_scenario_6_multi_claim_independent_verification(hf_verifier):
    claim1 = "Smoking causes lung cancer."
    claim2 = "Penicillin is ineffective against bacterial infections."
    
    evidence1 = [
        RetrievedDocument(
            title="Tobacco etiology of lung cancer",
            content="Cigarette smoking is established as the primary causal factor of lung cancer.",
            source="PubMed Central",
            similarity_score=0.95,
        )
    ]
    evidence2 = [
        RetrievedDocument(
            title="Penicillin mechanisms in bacterial infection",
            content="Penicillin is a potent bactericidal beta-lactam antibiotic highly effective against susceptible bacterial strains.",
            source="PubMed Central",
            similarity_score=0.93,
        )
    ]
    
    evidence_map = {
        claim1: evidence1,
        claim2: evidence2,
    }
    
    full_analysis = hf_verifier.generate_full_analysis(
        question="What are the effects of smoking and penicillin?",
        claims=[claim1, claim2],
        evidence_map=evidence_map,
        candidate_answer="Smoking causes lung cancer. Penicillin is ineffective against bacterial infections.",
    )
    
    assert len(full_analysis.claims) == 2
    c1 = full_analysis.claims[0]
    c2 = full_analysis.claims[1]
    
    assert c1.verdict == "SUPPORTED"
    assert c1.hallucination_risk_label == "Low"
    
    assert c2.verdict == "REFUTED"
    assert c2.hallucination_risk_label == "High"
    
    # Overall analysis should detect contradictions and high risk
    assert full_analysis.contradictions_detected == "Yes"
    assert full_analysis.overall_verdict == "REFUTED"
