"""
RAG Pipeline

This module coordinates the complete Retrieval-Augmented
Generation (RAG) workflow.
"""
from api.services.llm_service import LLMService
from typing import Any

from preprocessing.preprocess import QueryPreprocessor
from retrieval.retrieve import DocumentRetriever, SAMPLE_DOCUMENTS
from response_generation.formatter import source_payload
from verification.knowledge_graph import EvidenceKnowledgeGraph
from verification.scifact_verify import BaselineSciFactVerifier
from verification.verifier import EvidenceRanker, EvidenceScorer


class RAGPipeline:
    """
    Coordinates the entire AI pipeline.
    """

    def __init__(
        self,
        preprocessing_service: QueryPreprocessor | None = None,
        retrieval_service: DocumentRetriever | None = None,
        verification_service: BaselineSciFactVerifier | None = None,
        llm_service: LLMService | None = None,
        evidence_ranker: EvidenceRanker | None = None,
        evidence_scorer: EvidenceScorer | None = None,
    ) -> None:
        self.preprocessing_service = preprocessing_service or QueryPreprocessor()
        self.retrieval_service = retrieval_service
        self.verification_service = verification_service or BaselineSciFactVerifier()
        self.llm_service = llm_service or LLMService()
        self.evidence_ranker = evidence_ranker or EvidenceRanker()
        self.evidence_scorer = evidence_scorer or EvidenceScorer()


    def run(self, query: str) -> dict[str, Any]:
        """
        Execute the complete RAG workflow.
        """

        processed_query = self.preprocessing_service.process(query)
        retriever = self._get_retriever()
        retrieved_documents = retriever.retrieve(processed_query)
        ranked_evidence = self.evidence_ranker.rank(retrieved_documents)

        knowledge_graph = EvidenceKnowledgeGraph()
        knowledge_graph.add_evidence(ranked_evidence)
        claims = self.verification_service.extract_claims(processed_query, ranked_evidence)
        verifications = self.verification_service.verify(claims, ranked_evidence)
        confidence = self.evidence_scorer.score(ranked_evidence, verifications)
        answer = self.llm_service.generate(
            processed_query, ranked_evidence, confidence.status, verifications
        )

        return {
            "query": query,
            "processed_query": processed_query,
            "sources": [source_payload(document) for document in ranked_evidence],
            "evidence": [source_payload(document) for document in ranked_evidence],
            "claims": [
                {"claim": item.claim, "status": item.status, "evidence_titles": item.evidence_titles,
                 "evidence_score": item.evidence_score, "method": item.method}
                for item in verifications
            ],
            "verification_status": confidence.status,
            "confidence_score": confidence.score,
            "confidence_explanation": confidence.explanation,
            "knowledge_graph": {
                "nodes": knowledge_graph.graph.number_of_nodes(),
                "edges": knowledge_graph.graph.number_of_edges(),
            },
            "answer": answer
        }

    def _get_retriever(self) -> DocumentRetriever:
        """Lazily initialise the model/index so API startup remains lightweight."""
        if self.retrieval_service is None:
            self.retrieval_service = DocumentRetriever()
            self.retrieval_service.add_documents(SAMPLE_DOCUMENTS)
        return self.retrieval_service
