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
        if not candidate_answer and not evidence and not answer_sources:
            return "I could not find sufficient verified evidence to answer this question. Try phrasing the question with scientific or biomedical terms, or use the New Verification tool to check a direct claim."

        if candidate_answer:
            if verification_status == VerificationStatus.REFUTED:
                return (
                    f"Warning: Evidence contradicts the candidate claim.\n\n"
                    f"Candidate Extract:\n{candidate_answer}"
                )
            return candidate_answer

        if evidence:
            return f"Evidence retrieved from '{evidence[0].title}':\n\n{evidence[0].content}"

        return "No verified answer could be generated from available sources."

    def generate_candidate(
        self,
        query: str,
        documents: Sequence[RetrievedDocument],
    ) -> str:
        """Use retrieved answer documents as a transparent local candidate."""
        if not documents:
            return ""
        return documents[0].content
