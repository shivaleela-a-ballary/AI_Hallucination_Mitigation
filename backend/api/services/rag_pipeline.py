"""
RAG Pipeline

This module coordinates the complete Retrieval-Augmented
Generation (RAG) workflow.
"""
from api.services.services import BackendServices
from api.services.llm_service import LLMService
from typing import Dict, Any


class RAGPipeline:
    """
    Coordinates the entire AI pipeline.
    """

    def __init__(
        self,
        preprocessing_service=None,
        retrieval_service=None,
        verification_service=None,
        llm_service=None
    ):
        self.backend = BackendServices()


    def run(self, query: str) -> Dict[str, Any]:
        """
        Execute the complete RAG workflow.
        """

        # Step 1
        processed_query = self._preprocess(query)

        # Step 2
        retrieved_documents = self.backend.retrieve(processed_query)

        # Step 3
        verification_result = self.backend.verify(
            processed_query,
            retrieved_documents
        )

        # Step 4
        answer = self._generate_response(
            processed_query,
            retrieved_documents,
            verification_result
        )

        return {
            "query": query,
            "processed_query": processed_query,
            "documents": retrieved_documents,
            "verification": verification_result,
            "answer": answer
        }

    # ----------------------------
    # Internal helper methods
    # ----------------------------

    def _preprocess(self, query):

        if self.preprocessing_service:
            return self.preprocessing_service.process(query)

        return query

    def _retrieve(self, query):

        if self.retrieval_service:
            return self.retrieval_service.retrieve(query)

        return [
            {
                "title": "Sample Document",
                "content": "Sample retrieved evidence."
            }
        ]

    def _verify(self, query, documents):

        if self.verification_service:
            return self.verification_service.verify(
                query,
                documents
            )

        return {
            "status": "SUPPORTED",
            "confidence": 0.96
        }

    def _generate_response(
        self,
        query,
        documents,
        verification
    ):

        return self.llm_service.generate(
            query,
            documents,
            verification
        )