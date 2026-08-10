"""SciFact dataset, training, inference, and evaluation utilities."""

from .labels import (
    ID_TO_LABEL,
    LABEL_TO_ID,
    VerificationLabel,
)

__all__ = [
    "VerificationLabel",
    "LABEL_TO_ID",
    "ID_TO_LABEL",
]
