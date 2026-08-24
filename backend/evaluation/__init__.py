"""
Evaluation package for AI Hallucination Mitigation System.
Provides evaluation datasets, standard metrics, and CLI evaluation runners.
"""

from .metrics import (
    calculate_verification_metrics,
    calculate_retrieval_metrics,
    VerificationMetrics,
    RetrievalMetrics,
)
from .dataset import (
    load_evaluation_dataset,
    EvaluationExample,
)

__all__ = [
    "calculate_verification_metrics",
    "calculate_retrieval_metrics",
    "VerificationMetrics",
    "RetrievalMetrics",
    "load_evaluation_dataset",
    "EvaluationExample",
]
