"""Grounded response generation with an explicit local development fallback."""

from __future__ import annotations

from typing import Sequence

from retrieval.retrieve import RetrievedDocument
from verification.scifact_verify import ClaimVerification, VerificationStatus


class GroundedResponseGenerator:
    """Create an evidence-only answer when no external LLM is configured."""

    def generate(
        self,
        query: str,
        evidence: Sequence[RetrievedDocument],
        verification_status: VerificationStatus,
        claims: Sequence[ClaimVerification],
    ) -> str:
        if not evidence:
            return "I could not find indexed evidence to answer this question."
        if verification_status == VerificationStatus.REFUTED:
            return "The retrieved evidence does not support the requested claim. " + evidence[0].content
        qualifier = "Based on the retrieved development evidence: "
        if verification_status == VerificationStatus.UNCERTAIN:
            qualifier = "The available evidence is insufficient for a confident answer. Relevant evidence: "
        return qualifier + evidence[0].content
