"""
Multi-source Evidence Claim Verification Pipeline.
Integrates Multi-source Retrieval (SciFact + PubMed + Wikipedia), Deduplication,
Evidence Reranking, Contradiction/Stance Analysis, SciBERT Verification, and Hallucination Risk Scoring.
"""

from __future__ import annotations

import logging
from collections import Counter
from fastapi import APIRouter, Depends

from api.config import settings
from api.db.mongodb import db_manager
from api.dependencies import get_optional_current_user
from api.models.request_models import VerifyRequest
from api.models.response_models import VerificationResponse
from api.services.history_store import history_store
from response_generation.formatter import source_payload
from retrieval.deduplication import EvidenceDeduplicator
from retrieval.providers.base import Document, RetrievedDocument
from retrieval.providers.manager import MultiSourceEvidenceManager
from retrieval.reranker import EvidenceReranker
from verification.contradiction import ContradictionDetector
from verification.knowledge_graph import EvidenceKnowledgeGraph
from verification.risk_analyzer import RiskAnalyzer
from verification.scifact_verify import (
    BaselineSciFactVerifier,
    Claim,
    ClaimVerification,
    LocalSciFactVerifier,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Verification"])

# Module singletons
_evidence_manager: MultiSourceEvidenceManager | None = None
_deduplicator: EvidenceDeduplicator | None = None
_reranker: EvidenceReranker | None = None
_contradiction_detector: ContradictionDetector | None = None
_risk_analyzer: RiskAnalyzer | None = None
_verifier: LocalSciFactVerifier | BaselineSciFactVerifier | None = None


def get_pipeline_components():
    global _evidence_manager, _deduplicator, _reranker, _contradiction_detector, _risk_analyzer, _verifier
    if _evidence_manager is None:
        _evidence_manager = MultiSourceEvidenceManager()
    if _deduplicator is None:
        _deduplicator = EvidenceDeduplicator(text_similarity_threshold=settings.DEDUPLICATION_THRESHOLD)
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
    return _evidence_manager, _deduplicator, _reranker, _contradiction_detector, _risk_analyzer, _verifier


@router.post("/verify", response_model=VerificationResponse)
def verify(
    request: VerifyRequest,
    current_user: dict | None = Depends(get_optional_current_user),
) -> VerificationResponse:
    evidence_mgr, deduplicator, reranker, contradiction_detector, risk_analyzer, verifier = get_pipeline_components()
    user_id = current_user.get("id") if current_user else None
    claim_text = request.claim.strip()

    logger.info(f"Verification request received for claim: '{claim_text[:80]}...'")

    # 1. Harvest candidates
    if request.evidence.strip():
        logger.info("Using user-supplied evidence.")
        candidates = [
            Document(
                title="User-provided evidence",
                content=request.evidence.strip(),
                source="user-provided",
                source_type="user_provided",
            )
        ]
        evidence = reranker.rerank(claim_text, candidates, top_k=1, min_similarity=0.0)
    else:
        logger.info("Running multi-source retrieval (SciFact + PubMed + Wikipedia)...")
        raw_candidates = evidence_mgr.retrieve_candidates(claim_text, top_k_per_source=settings.TOP_K)
        deduped_candidates = deduplicator.deduplicate(raw_candidates)
        evidence = reranker.rerank(
            claim_text,
            deduped_candidates,
            top_k=settings.TOP_K,
            min_similarity=settings.SCIFACT_MIN_SIMILARITY,
        )

    # 2. If no evidence retrieved, return UNCERTAIN
    if not evidence:
        logger.info("No sufficiently relevant evidence found; returning UNCERTAIN.")
        empty_risk = risk_analyzer.evaluate(
            claim=claim_text,
            evidence=[],
            contradiction_summary=contradiction_detector.analyze(claim_text, []),
            verifications=[],
            raw_model_confidence=0.0,
        )
        payload = {
            "type": "claim_verification",
            "claim": claim_text,
            "query": claim_text,
            "answer": f"Verification for: {claim_text}",
            "verification_status": "UNCERTAIN",
            "prediction": "UNCERTAIN",
            "confidence_score": 0.0,
            "confidence_available": False,
            "probabilities": None,
            "sources": [],
            "evidence": [],
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "uncertain_evidence": [],
            "source_summary": {},
            "claims": [],
            "confidence_explanation": "No sufficiently relevant multi-source evidence was retrieved.",
            "evidence_quality": empty_risk.evidence_quality,
            "hallucination_risk": empty_risk.hallucination_risk,
            "explanation": empty_risk.explanation,
            "explanation_bullets": empty_risk.explanation_bullets,
            "knowledge_graph": {"nodes": [], "edges": []},
        }
        saved = db_manager.add_verification_history(payload, user_id=user_id)
        history_store.add(claim_text, saved)
        return VerificationResponse(**saved)

    # 3. Contradiction & Stance Detection
    contradiction_summary = contradiction_detector.analyze(claim_text, evidence)
    final_status = contradiction_summary.overall_status

    # 4. SciBERT Classifier / Inference
    claims_to_verify = verifier.extract_claims(claim_text, evidence)
    verifications = verifier.verify(claims_to_verify, evidence)

    raw_model_confidence = 0.0
    probabilities = None
    if hasattr(verifier, "inference"):
        try:
            inference_pred = verifier.inference.predict(claim_text, "\n".join(doc.content for doc in evidence))
            raw_model_confidence = inference_pred.confidence
            probabilities = inference_pred.probabilities
        except Exception as exc:
            logger.debug(f"SciFact inference error: {exc}")
    elif verifications:
        raw_model_confidence = verifications[0].evidence_score

    # Reconcile status: if contradiction detector found explicit strong opposition, respect REFUTED
    if contradiction_summary.overall_status == VerificationStatus.REFUTED:
        final_status = VerificationStatus.REFUTED
    elif contradiction_summary.overall_status == VerificationStatus.UNCERTAIN:
        final_status = VerificationStatus.UNCERTAIN
    else:
        # If contradiction detector found SUPPORTED, check classifier
        if verifications and verifications[0].status == VerificationStatus.REFUTED and not contradiction_summary.supporting_evidence:
            final_status = VerificationStatus.REFUTED
        else:
            final_status = VerificationStatus.SUPPORTED

    # 5. Risk & Explainability Analysis
    risk_report = risk_analyzer.evaluate(
        claim=claim_text,
        evidence=evidence,
        contradiction_summary=contradiction_summary,
        verifications=verifications,
        raw_model_confidence=raw_model_confidence,
    )

    # 6. Knowledge Graph Construction
    graph = EvidenceKnowledgeGraph()
    graph.add_evidence(evidence)
    knowledge_graph_dict = {
        "nodes": [
            {"id": str(node_id), **attributes}
            for node_id, attributes in graph.graph.nodes(data=True)
        ],
        "edges": [
            {"source": str(source), "target": str(target), **attributes}
            for source, target, attributes in graph.graph.edges(data=True)
        ],
    }

    # 7. Format Payloads
    status_str = final_status.value if hasattr(final_status, "value") else str(final_status)
    evidence_list = [source_payload(item) for item in evidence]
    supporting_list = [source_payload(item) for item in contradiction_summary.supporting_evidence]
    contradicting_list = [source_payload(item) for item in contradiction_summary.contradicting_evidence]
    uncertain_list = [source_payload(item) for item in contradiction_summary.uncertain_evidence]

    source_counts = dict(Counter(item.source for item in evidence))

    claims_list = [
        {
            "claim": item.claim,
            "status": status_str,
            "evidence_titles": item.evidence_titles,
            "evidence_score": float(item.evidence_score),
            "method": item.method,
        }
        for item in verifications
    ]

    payload = {
        "type": "claim_verification",
        "claim": claim_text,
        "query": claim_text,
        "answer": f"Verification for: {claim_text}",
        "verification_status": status_str,
        "prediction": status_str,
        "confidence_score": float(risk_report.model_confidence),
        "confidence_available": final_status in {VerificationStatus.SUPPORTED, VerificationStatus.REFUTED},
        "probabilities": probabilities,
        "sources": [],
        "evidence": evidence_list,
        "supporting_evidence": supporting_list,
        "contradicting_evidence": contradicting_list,
        "uncertain_evidence": uncertain_list,
        "source_summary": source_counts,
        "claims": claims_list,
        "confidence_explanation": risk_report.explanation,
        "evidence_quality": risk_report.evidence_quality,
        "hallucination_risk": risk_report.hallucination_risk,
        "explanation": risk_report.explanation,
        "explanation_bullets": risk_report.explanation_bullets,
        "knowledge_graph": knowledge_graph_dict,
    }

    saved = db_manager.add_verification_history(payload, user_id=user_id)
    history_store.add(claim_text, saved)

    logger.info(f"Verification complete: status={status_str}, risk={risk_report.hallucination_risk}, sources={len(evidence)}")
    return VerificationResponse(**saved)