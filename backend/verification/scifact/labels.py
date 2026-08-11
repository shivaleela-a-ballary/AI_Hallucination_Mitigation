"""Shared SciFact verification labels."""

from enum import Enum


class VerificationLabel(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    UNCERTAIN = "UNCERTAIN"


LABEL_TO_ID = {
    VerificationLabel.SUPPORTED: 0,
    VerificationLabel.REFUTED: 1,
    VerificationLabel.UNCERTAIN: 2,
}

ID_TO_LABEL = {value: key for key, value in LABEL_TO_ID.items()}


def label_to_id(label: VerificationLabel) -> int:
    return LABEL_TO_ID[label]


def id_to_label(value: int) -> VerificationLabel:
    if value not in ID_TO_LABEL:
        raise ValueError(f"Unknown verification label ID: {value}")
    return ID_TO_LABEL[value]