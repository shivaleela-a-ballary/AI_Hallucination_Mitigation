"""
LLM Service

Provides a single interface for interacting with
Large Language Models (LLMs).
"""

import logging
from typing import Sequence

from api.config import settings
from response_generation.generator import GroundedResponseGenerator
from retrieval.retrieve import RetrievedDocument
from verification.scifact_verify import ClaimVerification, VerificationStatus

logger = logging.getLogger(__name__)


class LLMService:
    """
    Handles AI response generation.
    """

    def __init__(self, generator: GroundedResponseGenerator | None = None) -> None:
        self.generator = generator or GroundedResponseGenerator()

    def generate(
        self,
        query: str,
        documents: Sequence[RetrievedDocument],
        verification_status: VerificationStatus,
        claims: Sequence[ClaimVerification],
    ) -> str:
        """
        Generate an evidence-grounded response.

        When both ``OPENAI_API_KEY`` and ``LLM_MODEL`` are configured, use the
        optional OpenAI SDK with an evidence-only prompt. Otherwise use the
        explicit local development fallback.
        """

        if settings.OPENAI_API_KEY and settings.LLM_MODEL:
            try:
                from openai import OpenAI

                evidence_text = "\n".join(
                    f"- [{item.source}] {item.title}: {item.content}" for item in documents
                )
                response = OpenAI(api_key=settings.OPENAI_API_KEY).responses.create(
                    model=settings.LLM_MODEL,
                    input=(
                        "Answer only from the evidence below. State uncertainty if it does not "
                        "support the answer. Do not add uncited facts.\n\n"
                        f"Question: {query}\nVerification status: {verification_status.value}\n"
                        f"Evidence:\n{evidence_text}"
                    ),
                )
                if response.output_text.strip():
                    return response.output_text.strip()
            except Exception:
                logger.exception("Configured external LLM failed; using local fallback.")

        return self.generator.generate(query, documents, verification_status, claims)
