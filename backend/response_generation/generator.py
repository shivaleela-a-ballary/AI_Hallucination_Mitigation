"""Deterministic response generation that never invents unsupported answers."""

from __future__ import annotations

from typing import Sequence

from retrieval.retrieve import RetrievedDocument
from verification.scifact_verify import ClaimVerification, VerificationStatus


class GroundedResponseGenerator:
    """Create an evidence-only answer when no external LLM is configured."""

    def generate(
        self,
        query: str,
        candidate_answer: str,
        evidence: Sequence[RetrievedDocument],
        verification_status: VerificationStatus,
        claims: Sequence[ClaimVerification],
        answer_sources: Sequence[RetrievedDocument] = (),
    ) -> str:
        if not evidence:
            if answer_sources and candidate_answer:
                return (
                    "Based on the retrieved general-knowledge sources, with SciFact verification "
                    "inconclusive: " + candidate_answer
                )
            return "I could not find sufficient verified evidence to answer this question."
        if verification_status == VerificationStatus.REFUTED:
            return "The retrieved evidence refutes the candidate claim; I cannot present it as fact."
        if verification_status == VerificationStatus.UNCERTAIN:
            return "The available evidence is insufficient to verify a reliable answer to this question."
        return candidate_answer or "The retrieved evidence supports a claim, but no answer text was generated."

    def generate_candidate(
        self,
        query: str,
        documents: Sequence[RetrievedDocument],
    ) -> str:
        """Use retrieved answer documents as a transparent local candidate."""
        if not documents:
            return ""
        return documents[0].content
