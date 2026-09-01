"""Verification primitives, Hugging Face NLI verification, and SciFact infrastructure."""

from .hf_verifier import HuggingFaceClaimVerifier, hf_verifier, StructuredClaimReport, ComprehensiveVerificationSummary
from .scifact_verify import BaselineSciFactVerifier, VerificationStatus

__all__ = [
    "BaselineSciFactVerifier",
    "VerificationStatus",
    "HuggingFaceClaimVerifier",
    "hf_verifier",
    "StructuredClaimReport",
    "ComprehensiveVerificationSummary",
]
