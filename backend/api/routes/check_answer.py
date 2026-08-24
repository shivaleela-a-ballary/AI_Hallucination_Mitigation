"""
Check AI Answer Endpoint.
Decomposes complex AI-generated answers or text into individual claims,
verifies each claim across multi-source evidence, and compiles an Overall Reliability Report.
"""

from __future__ import annotations

import logging
import re
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from api.config import settings
from api.db.mongodb import db_manager
from api.dependencies import get_optional_current_user
from api.models.request_models import CheckAnswerRequest
from api.models.response_models import CheckAnswerClaim, CheckAnswerResponse
from api.services.history_store import history_store
from response_generation.formatter import source_payload
from retrieval.deduplication import EvidenceDeduplicator
from retrieval.providers.manager import MultiSourceEvidenceManager
from retrieval.reranker import EvidenceReranker
from verification.contradiction import ContradictionDetector
from verification.risk_analyzer import RiskAnalyzer
from verification.scifact_verify import BaselineSciFactVerifier, LocalSciFactVerifier, VerificationStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Answer Checker"])

# Pipeline components
_evidence_mgr = None
_deduplicator = None
_reranker = None
_contradiction_detector = None
_risk_analyzer = None
_verifier = None


def get_checker_components():
    global _evidence_mgr, _deduplicator, _reranker, _contradiction_detector, _risk_analyzer, _verifier
    if _evidence_mgr is None:
        _evidence_mgr = MultiSourceEvidenceManager()
    if _deduplicator is None:
        _deduplicator = EvidenceDeduplicator()
    if _reranker is None:
        _reranker = EvidenceReranker(min_similarity=settings.SCIFACT_MIN_SIMILARITY)
    if _contradiction_detector is None:
        _contradiction_detector = ContradictionDetector()
    if _risk_analyzer is None:
        _risk_analyzer = RiskAnalyzer()
    if _verifier is None:
        if settings.SCIFACT_MODEL_PATH.is_dir():
            _verifier = LocalSciFactVerifier(str(settings.SCIFACT_MODEL_PATH))
        else:
            _verifier = BaselineSciFactVerifier()
    return _evidence_mgr, _deduplicator, _reranker, _contradiction_detector, _risk_analyzer, _verifier


def split_into_claims(text: str) -> list[str]:
    """Split input paragraph into clean declarative claim sentences."""
    cleaned = text.strip()
    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    valid_claims = []
    for s in raw_sentences:
        s_clean = s.strip()
        # Must be at least 15 chars and contain at least 3 words to constitute a factual assertion
        if len(s_clean) >= 15 and len(s_clean.split()) >= 3:
            valid_claims.append(s_clean)
    return valid_claims or [cleaned]


@router.post("/check-answer", response_model=CheckAnswerResponse)
def check_ai_answer(
    request: CheckAnswerRequest,
    current_user: dict | None = Depends(get_optional_current_user),
) -> CheckAnswerResponse:
    evidence_mgr, deduplicator, reranker, contradiction_detector, risk_analyzer, verifier = get_checker_components()
    user_id = current_user.get("id") if current_user else None

    raw_text = request.text.strip()
    claims = split_into_claims(raw_text)
    logger.info(f"Checking AI Answer with {len(claims)} extracted claims.")

    verified_claims: list[CheckAnswerClaim] = []
    supported_count = 0
    refuted_count = 0
    uncertain_count = 0
    reliability_scores: list[float] = []

    for claim in claims:
        # Retrieve multi-source candidates
        raw_candidates = evidence_mgr.retrieve_candidates(claim, top_k_per_source=4)
        deduped = deduplicator.deduplicate(raw_candidates)
        evidence = reranker.rerank(claim, deduped, top_k=3, min_similarity=settings.SCIFACT_MIN_SIMILARITY)

        if not evidence:
            verified_claims.append(
                CheckAnswerClaim(
                    claim=claim,
                    verification_status="UNCERTAIN",
                    confidence_score=0.0,
                    hallucination_risk="MEDIUM",
                    evidence_count=0,
                    supporting_evidence=[],
                    contradicting_evidence=[],
                    explanation="No indexed evidence found to verify this specific assertion.",
                )
            )
            uncertain_count += 1
            reliability_scores.append(0.30)
            continue

        contradiction_summary = contradiction_detector.analyze(claim, evidence)
        status = contradiction_summary.overall_status
        status_str = status.value if hasattr(status, "value") else str(status)

        risk_report = risk_analyzer.evaluate(
            claim=claim,
            evidence=evidence,
            contradiction_summary=contradiction_summary,
            verifications=[],
            raw_model_confidence=0.85 if status == VerificationStatus.SUPPORTED else 0.75,
        )

        if status == VerificationStatus.SUPPORTED:
            supported_count += 1
            reliability_scores.append(0.90)
        elif status == VerificationStatus.REFUTED:
            refuted_count += 1
            reliability_scores.append(0.0)
        else:
            uncertain_count += 1
            reliability_scores.append(0.40)

        supporting_payloads = [source_payload(d) for d in contradiction_summary.supporting_evidence]
        contradicting_payloads = [source_payload(d) for d in contradiction_summary.contradicting_evidence]

        verified_claims.append(
            CheckAnswerClaim(
                claim=claim,
                verification_status=status_str,
                confidence_score=risk_report.model_confidence,
                hallucination_risk=risk_report.hallucination_risk,
                evidence_count=len(evidence),
                supporting_evidence=supporting_payloads,
                contradicting_evidence=contradicting_payloads,
                explanation=risk_report.explanation_bullets[0] if risk_report.explanation_bullets else "",
            )
        )

    # Compute Aggregate Reliability Score
    total_claims = len(claims)
    if total_claims > 0:
        overall_reliability = round((sum(reliability_scores) / total_claims) * 100, 1)
    else:
        overall_reliability = 0.0

    if refuted_count > 0 or overall_reliability < 50.0:
        overall_risk = "HIGH"
    elif uncertain_count > supported_count or overall_reliability < 75.0:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    summary_text = (
        f"Evaluated {total_claims} claim(s): {supported_count} Supported, "
        f"{refuted_count} Refuted, {uncertain_count} Uncertain. "
        f"Overall Reliability: {overall_reliability}%, Hallucination Risk: {overall_risk}."
    )

    result_payload = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "type": "ai_answer_check",
        "original_text": raw_text,
        "overall_reliability_score": overall_reliability,
        "overall_hallucination_risk": overall_risk,
        "total_claims": total_claims,
        "supported_claims_count": supported_count,
        "refuted_claims_count": refuted_count,
        "uncertain_claims_count": uncertain_count,
        "claims": [c.model_dump() for c in verified_claims],
        "summary": summary_text,
    }

    # Save to history
    saved = db_manager.add_verification_history(result_payload, user_id=user_id)
    history_store.add(raw_text[:80], saved)

    return CheckAnswerResponse(**saved)
