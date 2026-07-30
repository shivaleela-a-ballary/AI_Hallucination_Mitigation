"""
LLM Service

Provides a single interface for interacting with
Large Language Models (LLMs).
"""

from typing import List, Dict


class LLMService:
    """
    Handles AI response generation.
    """

    def __init__(self):
        pass

    def generate(
        self,
        query: str,
        documents: List[Dict],
        verification: Dict
    ) -> str:
        """
        Generate a response using retrieved evidence.
        """

        evidence_titles = ", ".join(
            doc["title"] for doc in documents
        )

        response = (
            f"Answer for: '{query}'.\n\n"
            f"Verification Status: {verification['status']}.\n"
            f"Confidence: {verification['confidence']:.2f}.\n\n"
            f"Evidence Used:\n{evidence_titles}"
        )

        return response