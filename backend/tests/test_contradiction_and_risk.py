"""Unit tests for contradiction detection, stance classification, and hallucination risk calculation."""

from __future__ import annotations

from retrieval.providers.base import RetrievedDocument
from verification.contradiction import ContradictionDetector
from verification.risk_analyzer import RiskAnalyzer
from verification.scifact_verify import VerificationStatus


def test_contradiction_detector_supports_claim() -> None:
    detector = ContradictionDetector()
    claim = "MicroRNAs inhibit target mRNA translation."
    doc = RetrievedDocument(
        title="MicroRNA Mechanisms",
        content="MicroRNAs repress translation and accelerate mRNA decay in target cells.",
        source="SciFact",
        similarity_score=0.85,
    )
    stance = detector.analyze_passage(claim, doc)
    assert stance.status == VerificationStatus.SUPPORTED
    assert stance.document.relationship == "SUPPORTS"

    summary = detector.analyze(claim, [doc])
    assert summary.overall_status == VerificationStatus.SUPPORTED
    assert len(summary.supporting_evidence) == 1
    assert len(summary.contradicting_evidence) == 0


def test_contradiction_detector_detects_directional_refutation() -> None:
    detector = ContradictionDetector()
    claim = "Insulin increases hepatic glucose production."
    doc = RetrievedDocument(
        title="Insulin Physiology",
        content="Insulin suppresses hepatic gluconeogenesis and lowers blood glucose concentration.",
        source="PubMed",
        similarity_score=0.82,
    )
    stance = detector.analyze_passage(claim, doc)
    assert stance.status == VerificationStatus.REFUTED
    assert stance.document.relationship == "CONTRADICTS"

    summary = detector.analyze(claim, [doc])
    assert summary.overall_status == VerificationStatus.REFUTED
    assert len(summary.contradicting_evidence) == 1
    assert len(summary.supporting_evidence) == 0


def test_contradiction_detector_detects_negated_claim_refutation() -> None:
    detector = ContradictionDetector()
    claim = "Penicillin has no antibacterial efficacy against bacterial infections."
    doc = RetrievedDocument(
        title="Penicillin Pharmacology",
        content="Penicillin is a potent bactericidal antibiotic with strong efficacy against susceptible strains.",
        source="SciFact",
        similarity_score=0.80,
    )
    stance = detector.analyze_passage(claim, doc)
    assert stance.status == VerificationStatus.REFUTED

    summary = detector.analyze(claim, [doc])
    assert summary.overall_status == VerificationStatus.REFUTED


def test_risk_analyzer_calculates_transparent_metrics() -> None:
    analyzer = RiskAnalyzer()
    claim = "Statins inhibit HMG-CoA reductase."
    docs = [
        RetrievedDocument("Statin Study 1", "Statins inhibit HMG-CoA reductase.", "SciFact", 0.88),
        RetrievedDocument("Statin Study 2", "Inhibition of HMG-CoA reductase by statin therapy.", "PubMed", 0.84),
    ]
    detector = ContradictionDetector()
    summary = detector.analyze(claim, docs)

    report = analyzer.evaluate(
        claim=claim,
        evidence=docs,
        contradiction_summary=summary,
        verifications=[],
        raw_model_confidence=0.91,
    )

    assert report.evidence_quality == "HIGH"
    assert report.source_agreement_ratio == "2 / 2"
    assert report.hallucination_risk == "LOW"
    assert report.supporting_count == 2
    assert report.contradicting_count == 0
    assert len(report.explanation_bullets) >= 4
