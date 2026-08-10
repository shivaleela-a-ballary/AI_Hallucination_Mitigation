"""
RAG Pipeline

Coordinates preprocessing, retrieval, evidence ranking,
SciFact verification, confidence scoring, and response generation.
"""

from __future__ import annotations

from typing import Any

from api.services.llm_service import LLMService
from preprocessing.preprocess import QueryPreprocessor
from retrieval.retrieve import DocumentRetriever, SAMPLE_DOCUMENTS
from response_generation.formatter import source_payload
from verification.knowledge_graph import EvidenceKnowledgeGraph
from verification.scifact.verifier import SciFactModelVerifier
from verification.verifier import EvidenceRanker, EvidenceScorer


class RAGPipeline:
    """Coordinates the complete AI hallucination-mitigation pipeline."""

    def __init__(
        self,
        preprocessing_service: QueryPreprocessor | None = None,
        retrieval_service: DocumentRetriever | None = None,
        verification_service: SciFactModelVerifier | None = None,
        llm_service: LLMService | None = None,
        evidence_ranker: EvidenceRanker | None = None,
        evidence_scorer: EvidenceScorer | None = None,
    ) -> None:

        self.preprocessing_service = (
            preprocessing_service or QueryPreprocessor()
        )

        self.retrieval_service = retrieval_service

        self.verification_service = (
            verification_service
            or SciFactModelVerifier(
                model_path="models/scifact",
                max_length=128,
            )
        )

        self.llm_service = llm_service or LLMService()
        self.evidence_ranker = evidence_ranker or EvidenceRanker()
        self.evidence_scorer = evidence_scorer or EvidenceScorer()

    def run(self, query: str) -> dict[str, Any]:
        """Execute the complete RAG workflow."""

        processed_query = self.preprocessing_service.process(query)

        # Retrieval
        retriever = self._get_retriever()
        retrieved_documents = retriever.retrieve(processed_query)

        # Evidence ranking
        ranked_evidence = self.evidence_ranker.rank(
            retrieved_documents
        )

        # Evidence-backed knowledge graph
        knowledge_graph = EvidenceKnowledgeGraph()
        knowledge_graph.add_evidence(ranked_evidence)

        # SciFact verification
        verifications = []

        for document in ranked_evidence:
            verification = self.verification_service.verify(
                claim=processed_query,
                evidence=document.content,
                evidence_score=document.similarity_score,
                evidence_title=document.title,
            )

            verifications.append(verification)

        # Explainable confidence
        confidence = self.evidence_scorer.score(
            ranked_evidence,
            verifications,
        )

        # Grounded response generation
        answer = self.llm_service.generate(
            processed_query,
            ranked_evidence,
            confidence.status,
            verifications,
        )

        return {
            "query": query,
            "processed_query": processed_query,

            "sources": [
                source_payload(document)
                for document in ranked_evidence
            ],

            "evidence": [
                source_payload(document)
                for document in ranked_evidence
            ],

            "claims": [
                {
                    "claim": item.claim,
                    "status": (
                        item.status.value
                        if hasattr(item.status, "value")
                        else item.status
                    ),
                    "evidence_titles": item.evidence_titles,
                    "evidence_score": item.evidence_score,
                    "method": item.method,
                }
                for item in verifications
            ],

            "verification_status": (
                confidence.status.value
                if hasattr(confidence.status, "value")
                else confidence.status
            ),

            "confidence_score": confidence.score,

            "confidence_explanation": confidence.explanation,

            "knowledge_graph": {
                "nodes": knowledge_graph.graph.number_of_nodes(),
                "edges": knowledge_graph.graph.number_of_edges(),
            },

            "answer": answer,
        }

    def _get_retriever(self) -> DocumentRetriever:
        """Lazily initialize the retrieval model/index."""

        if self.retrieval_service is None:
            self.retrieval_service = DocumentRetriever()
            self.retrieval_service.add_documents(SAMPLE_DOCUMENTS)

        return self.retrieval_service