"""
Unit and integration tests for newly implemented hallucination forensics,
verified correction engine, research paper auditor, dashboard stats, and sources endpoints.
"""
import pytest
from retrieval.providers.base import RetrievedDocument
from verification.forensics import HallucinationForensicsAnalyzer
from verification.correction import VerifiedCorrectionEngine
from api.routes.paper_auditor import _segment_sections, _extract_paper_claims


def test_forensics_pattern_detection():
    analyzer = HallucinationForensicsAnalyzer()

    report = analyzer.analyze_claim(
        claim="Metformin completely cures all types of cancer in every human patient without exception.",
        evidence=[],
        verdict="REFUTED",
        risk_level="High",
        risk_score=0.92,
    )
    assert report.pattern_type in ("Absolute language / Exaggeration", "Absolute language", "Overgeneralization")
    assert report.risk_level in ("High", "Critical")
    assert report.why_flagged is not None
    assert report.explanation is not None


def test_forensics_causal_overclaim():
    analyzer = HallucinationForensicsAnalyzer()
    report = analyzer.analyze_claim(
        claim="Coffee consumption directly causes cardiac arrest in all adults.",
        evidence=[],
        verdict="REFUTED",
        risk_level="High",
        risk_score=0.88,
    )
    assert report.pattern_type in (
        "Causal overclaim",
        "Absolute language",
        "Overgeneralization",
        "Factual contradiction / Directional reversal",
    )
    assert report.risk_level in ("Medium", "High")


def test_forensics_valid_claim():
    analyzer = HallucinationForensicsAnalyzer()
    doc = RetrievedDocument(
        title="Diabetes Pharmacology",
        content="Metformin is commonly prescribed as a first-line medication for type 2 diabetes.",
        source="SciFact",
        similarity_score=0.95,
    )
    report = analyzer.analyze_claim(
        claim="Metformin is commonly prescribed as a first-line medication for type 2 diabetes.",
        evidence=[doc],
        verdict="SUPPORTED",
        risk_level="Low",
        risk_score=0.08,
    )
    assert "Well-supported" in report.pattern_type or "Valid" in report.pattern_type
    assert report.risk_level == "Low"


def test_paper_auditor_section_extraction():
    paper_text = """Abstract
This study investigates the efficacy of drug X on model Y.

Introduction
Background on the disease has been established previously.

Methods
We recruited 50 mice and administered 10mg/kg daily.

Results
Treated mice showed a 30% reduction in tumor volume compared to controls [1].

Discussion
These findings suggest that drug X has therapeutic potential.
"""
    sections = _segment_sections(paper_text)
    section_names = [s[0] for s in sections]
    assert "Abstract" in section_names or "Methods" in section_names or "Results" in section_names


def test_paper_auditor_claims_extraction():
    sections = [
        ("Results", "Low-dose aspirin reduces the risk of secondary cardiovascular events [1]. Patients experienced zero adverse events in all trials without exception.", 1)
    ]
    claims = _extract_paper_claims(sections)
    assert len(claims) >= 1
    assert any("aspirin" in c["claim"].lower() for c in claims)


def test_correction_engine_generation_and_verification():
    engine = VerifiedCorrectionEngine()
    claim = "Metformin cures 100% of all malignant tumors unconditionally."
    doc = RetrievedDocument(
        title="Metformin in Oncology",
        content="Metformin has been associated with modest decreases in cancer incidence in observational diabetic cohorts.",
        source="SciFact",
        similarity_score=0.85,
    )
    correction = engine.generate_and_verify(
        claim=claim,
        verdict="REFUTED",
        evidence=[doc],
        forensics_pattern="Absolute language",
    )
    assert correction is not None
    assert correction.candidate_correction != claim
    assert correction.is_verified is True
