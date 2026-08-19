"""Direct claim verification using the preserved local SciFact model."""

from fastapi import APIRouter

from api.config import settings
from api.models.request_models import VerifyRequest
from api.models.response_models import VerificationResponse
from retrieval.retrieve import Document, DocumentRetriever, RetrievedDocument
from retrieval.scifact_documents import load_scifact_documents
from response_generation.formatter import source_payload
from verification.scifact_verify import LocalSciFactVerifier, VerificationStatus
from verification.knowledge_graph import EvidenceKnowledgeGraph

router = APIRouter(tags=["Verification"])
_verifier: LocalSciFactVerifier | None = None
_retriever: DocumentRetriever | None = None


@router.post("/verify", response_model=VerificationResponse)
def verify(request: VerifyRequest) -> VerificationResponse:
    global _retriever, _verifier
    if request.evidence.strip():
        evidence = [RetrievedDocument("User-provided evidence", request.evidence, "user-provided", 1.0)]
    else:
        if _retriever is None:
            _retriever = DocumentRetriever(min_similarity=settings.SCIFACT_MIN_SIMILARITY)
            _retriever.add_documents(load_scifact_documents(settings.SCIFACT_CORPUS_PATH))
        retriever = _retriever
        evidence = retriever.retrieve(request.claim, k=settings.TOP_K)

    if not evidence:
        return VerificationResponse(
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
        _verifier = LocalSciFactVerifier(str(settings.SCIFACT_MODEL_PATH))
    verifier = _verifier
    claims = verifier.extract_claims(request.claim, evidence)
    verifications = verifier.verify(claims, evidence)
    result = verifications[0]
    probabilities = verifier.inference.predict(request.claim, "\n".join(item.content for item in evidence)).probabilities
    graph = EvidenceKnowledgeGraph()
    graph.add_evidence(evidence)
    return VerificationResponse(
        claim=request.claim,
        verification_status=result.status,
        confidence_score=result.evidence_score,
        confidence_available=result.status in {VerificationStatus.SUPPORTED, VerificationStatus.REFUTED},
        probabilities=probabilities,
        evidence=[source_payload(item) for item in evidence],
        claims=[{
            "claim": item.claim,
            "status": item.status,
            "evidence_titles": item.evidence_titles,
            "evidence_score": item.evidence_score,
            "method": item.method,
        } for item in verifications],
        confidence_explanation="SciFact model confidence for the retrieved evidence.",
        knowledge_graph={
            "nodes": [
                {"id": str(node_id), **attributes}
                for node_id, attributes in graph.graph.nodes(data=True)
            ],
            "edges": [
                {"source": str(source), "target": str(target), **attributes}
                for source, target, attributes in graph.graph.edges(data=True)
            ],
        },
    )