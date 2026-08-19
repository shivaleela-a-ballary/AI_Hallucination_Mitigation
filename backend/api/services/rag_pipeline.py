"""
RAG Pipeline

This module coordinates the complete Retrieval-Augmented
Generation (RAG) workflow.
"""
import logging

from api.services.llm_service import LLMService
from typing import Any

from preprocessing.preprocess import QueryPreprocessor
from retrieval.answer_documents import load_answer_documents
from retrieval.knowledge_provider import GeneralKnowledgeRetriever, KnowledgeSourceUnavailable
from retrieval.retrieve import DocumentRetriever
from retrieval.scifact_documents import load_scifact_documents
from response_generation.formatter import source_payload
from verification.knowledge_graph import EvidenceKnowledgeGraph
from verification.scifact_verify import LocalSciFactVerifier
from api.config import settings
from verification.verifier import EvidenceRanker, EvidenceScorer

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Coordinates the entire AI pipeline.
    """

    def __init__(
        self,
        preprocessing_service: QueryPreprocessor | None = None,
        retrieval_service: DocumentRetriever | None = None,
        verification_service: LocalSciFactVerifier | None = None,
        llm_service: LLMService | None = None,
        evidence_retrieval_service: DocumentRetriever | None = None,
        evidence_ranker: EvidenceRanker | None = None,
        evidence_scorer: EvidenceScorer | None = None,
    ) -> None:
        self.preprocessing_service = preprocessing_service or QueryPreprocessor()
        self.retrieval_service = retrieval_service
        self.answer_knowledge_retriever = None
        self.evidence_retrieval_service = evidence_retrieval_service
        self.verification_service = verification_service
        self.llm_service = llm_service or LLMService()
        self.evidence_ranker = evidence_ranker or EvidenceRanker()
        self.evidence_scorer = evidence_scorer or EvidenceScorer()


    def run(self, query: str) -> dict[str, Any]:
        """
        Execute the complete RAG workflow.
        """

        processed_query = self.preprocessing_service.process(query)
        knowledge_source_error = False
        answer_retriever = self._get_answer_retriever()
        try:
            answer_documents = (
                answer_retriever.retrieve(processed_query, k=settings.TOP_K)
                if answer_retriever is not None
                else []
            )
        except KnowledgeSourceUnavailable:
            logger.warning("General knowledge source is unavailable.")
            answer_documents = []
            knowledge_source_error = True
        candidate_answer = self.llm_service.generate_candidate(processed_query, answer_documents)

        retrieved_evidence = []
        should_verify_with_scifact = bool(candidate_answer and (
            settings.SCIFACT_VERIFY_GENERAL
            or settings.ANSWER_CORPUS_PATH
            or self.verification_service is not None
        ))
        if should_verify_with_scifact:
            evidence_retriever = self._get_evidence_retriever()
            retrieved_evidence = evidence_retriever.retrieve(
                candidate_answer,
                k=settings.TOP_K,
            )
        ranked_evidence = self.evidence_ranker.rank(retrieved_evidence)

        knowledge_graph = EvidenceKnowledgeGraph()
        knowledge_graph.add_evidence(ranked_evidence)
        if should_verify_with_scifact and ranked_evidence:
            verifier = self._get_verifier()
            claims = verifier.extract_claims(candidate_answer, ranked_evidence)
            verifications = verifier.verify(claims, ranked_evidence)
        else:
            claims = []
            verifications = []
        confidence = self.evidence_scorer.score(ranked_evidence, verifications)
        answer = self.llm_service.generate(
            processed_query,
            candidate_answer,
            ranked_evidence,
            confidence.status,
            verifications,
            answer_documents,
        )
        if knowledge_source_error:
            answer = "The configured general knowledge source is unavailable, so I cannot provide a verified answer."

        return {
            "query": query,
            "processed_query": processed_query,
            "sources": [source_payload(document) for document in answer_documents],
            "evidence": [source_payload(document) for document in ranked_evidence],
            "claims": [
                {"claim": item.claim, "status": item.status, "evidence_titles": item.evidence_titles,
                 "evidence_score": item.evidence_score, "method": item.method}
                for item in verifications
            ],
            "verification_status": confidence.status,
            "confidence_score": confidence.score,
            "confidence_available": confidence.status.value in {"SUPPORTED", "REFUTED"} and confidence.score > 0,
            "confidence_explanation": (
                "General knowledge source unavailable; no answer confidence was assigned."
                if knowledge_source_error
                else confidence.explanation
            ),
            "knowledge_graph": {
                "nodes": [
                    {"id": str(node_id), **attributes}
                    for node_id, attributes in knowledge_graph.graph.nodes(data=True)
                ],
                "edges": [
                    {"source": str(source), "target": str(target), **attributes}
                    for source, target, attributes in knowledge_graph.graph.edges(data=True)
                ],
            },
            "answer": answer
        }

    def _get_answer_retriever(self) -> DocumentRetriever | None:
        """Load only the separately configured corpus used to form an answer."""
        if self.retrieval_service is not None:
            return self.retrieval_service
        if settings.ANSWER_CORPUS_PATH:
            documents = load_answer_documents(settings.ANSWER_CORPUS_PATH)
            self.retrieval_service = DocumentRetriever(
                min_similarity=settings.RETRIEVAL_MIN_SIMILARITY
            )
            self.retrieval_service.add_documents(documents)
            return self.retrieval_service
        if settings.KNOWLEDGE_PROVIDER == "wikipedia":
            if self.answer_knowledge_retriever is None:
                self.answer_knowledge_retriever = GeneralKnowledgeRetriever()
            return self.answer_knowledge_retriever
        return None

    def _get_evidence_retriever(self) -> DocumentRetriever:
        """Lazily initialise the SciFact evidence index."""
        if self.evidence_retrieval_service is not None:
            return self.evidence_retrieval_service
        if self.verification_service is not None and self.retrieval_service is not None:
            return self.retrieval_service
        documents = load_scifact_documents(settings.SCIFACT_CORPUS_PATH)
        self.evidence_retrieval_service = DocumentRetriever(
            min_similarity=settings.SCIFACT_MIN_SIMILARITY
        )
        self.evidence_retrieval_service.add_documents(documents)
        return self.evidence_retrieval_service

    def _get_verifier(self) -> LocalSciFactVerifier:
        if self.verification_service is None:
            self.verification_service = LocalSciFactVerifier(str(settings.SCIFACT_MODEL_PATH))
        return self.verification_service
