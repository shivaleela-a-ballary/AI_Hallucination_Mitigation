"""Direct claim verification using the preserved local SciFact model."""

from fastapi import APIRouter, Depends

from api.config import settings
from api.db.mongodb import db_manager
from api.dependencies import get_optional_current_user
from api.services.history_store import history_store
from api.models.request_models import VerifyRequest
from api.models.response_models import VerificationResponse
from retrieval.knowledge_provider import GeneralKnowledgeRetriever
from retrieval.retrieve import Document, DocumentRetriever, RetrievedDocument
from retrieval.scifact_documents import load_scifact_documents
from response_generation.formatter import source_payload
from verification.scifact_verify import BaselineSciFactVerifier, LocalSciFactVerifier, VerificationStatus
from verification.knowledge_graph import EvidenceKnowledgeGraph

router = APIRouter(tags=["Verification"])
_verifier: LocalSciFactVerifier | BaselineSciFactVerifier | None = None
_retriever: DocumentRetriever | None = None


@router.post("/verify", response_model=VerificationResponse)
def verify(
    request: VerifyRequest,
    current_user: dict | None = Depends(get_optional_current_user),
) -> VerificationResponse:
    global _retriever, _verifier
    user_id = current_user.get("id") if current_user else None

    if request.evidence.strip():
        evidence = [RetrievedDocument("User-provided evidence", request.evidence, "user-provided", 1.0)]
    else:
        if _retriever is None:
            _retriever = DocumentRetriever(min_similarity=settings.SCIFACT_MIN_SIMILARITY)
            cache_dir = settings.PROJECT_ROOT / "data" / "scifact" / "cache"
            if not _retriever.load(cache_dir):
                _retriever.add_documents(load_scifact_documents(settings.SCIFACT_CORPUS_PATH))
                _retriever.save(cache_dir)
        retriever = _retriever
        evidence = retriever.retrieve(request.claim, k=settings.TOP_K, min_similarity=settings.SCIFACT_MIN_SIMILARITY)
        if not evidence:
            try:
                evidence = GeneralKnowledgeRetriever().retrieve(request.claim, k=settings.TOP_K)
            except Exception:
                evidence = []

    if not evidence:
        payload = {
            "type": "claim_verification",
            "claim": request.claim,
            "query": request.claim,
            "answer": f"Verification for: {request.claim}",
            "verification_status": VerificationStatus.UNCERTAIN.value if hasattr(VerificationStatus.UNCERTAIN, "value") else str(VerificationStatus.UNCERTAIN),
            "confidence_score": 0.0,
            "confidence_available": False,
            "probabilities": None,
            "sources": [],
            "evidence": [],
            "claims": [],
            "confidence_explanation": "No sufficiently relevant SciFact evidence was retrieved.",
            "knowledge_graph": {"nodes": [], "edges": []},
        }
        saved = db_manager.add_verification_history(payload, user_id=user_id)
        history_store.add(request.claim, saved)
        return VerificationResponse(
            id=saved["id"],
            created_at=saved["created_at"],
            claim=request.claim,
            verification_status=VerificationStatus.UNCERTAIN,
            confidence_score=0.0,
            confidence_available=False,
            probabilities=None,
            evidence=[],
            claims=[],
            confidence_explanation="No sufficiently relevant SciFact evidence was retrieved.",
            knowledge_graph={"nodes": [], "edges": []},
        )

    if _verifier is None:
        if settings.SCIFACT_MODEL_PATH.is_dir():
            _verifier = LocalSciFactVerifier(str(settings.SCIFACT_MODEL_PATH))
        else:
            _verifier = BaselineSciFactVerifier()
    verifier = _verifier
    claims = verifier.extract_claims(request.claim, evidence)
    verifications = verifier.verify(claims, evidence)
    result = verifications[0]
    if hasattr(verifier, "inference"):
        probabilities = verifier.inference.predict(request.claim, "\n".join(item.content for item in evidence)).probabilities
    else:
        probabilities = None
    graph = EvidenceKnowledgeGraph()
    graph.add_evidence(evidence)

    verification_status_str = result.status.value if hasattr(result.status, "value") else str(result.status)
    evidence_list = [source_payload(item) for item in evidence]
    claims_list = [{
        "claim": item.claim,
        "status": item.status.value if hasattr(item.status, "value") else str(item.status),
        "evidence_titles": item.evidence_titles,
        "evidence_score": float(item.evidence_score),
        "method": item.method,
    } for item in verifications]
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

    payload = {
        "type": "claim_verification",
        "claim": request.claim,
        "query": request.claim,
        "answer": f"Verification for: {request.claim}",
        "verification_status": verification_status_str,
        "confidence_score": float(result.evidence_score),
        "confidence_available": result.status in {VerificationStatus.SUPPORTED, VerificationStatus.REFUTED},
        "probabilities": probabilities,
        "sources": [],
        "evidence": evidence_list,
        "claims": claims_list,
        "confidence_explanation": "SciFact model confidence for the retrieved evidence.",
        "knowledge_graph": knowledge_graph_dict,
    }
    saved = db_manager.add_verification_history(payload, user_id=user_id)
    history_store.add(request.claim, saved)

    return VerificationResponse(
        id=saved["id"],
        created_at=saved["created_at"],
        claim=request.claim,
        verification_status=result.status,
        confidence_score=float(result.evidence_score),
        confidence_available=result.status in {VerificationStatus.SUPPORTED, VerificationStatus.REFUTED},
        probabilities=probabilities,
        evidence=evidence_list,
        claims=claims_list,
        confidence_explanation="SciFact model confidence for the retrieved evidence.",
        knowledge_graph=knowledge_graph_dict,
    )