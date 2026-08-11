"""Inference utilities for a locally trained SciFact classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

from .labels import ID_TO_LABEL
from .model import SciFactModelConfig, load_local_sequence_classifier


@dataclass(frozen=True)
class SciFactPrediction:
    label: str
    confidence: float
    probabilities: dict[str, float]


class SciFactInference:
    """Run local inference using a trained SciFact checkpoint."""

    def __init__(
        self,
        model_path: str | Path,
        max_length: int = 512,
    ) -> None:

        config = SciFactModelConfig(
            model_path=Path(model_path),
            max_length=max_length,
        )

        self.tokenizer, self.model = load_local_sequence_classifier(config)

        self.model.eval()
        self.device = torch.device("cpu")
        self.model.to(self.device)

        self.max_length = max_length

    def predict(
        self,
        claim: str,
        evidence: str,
    ) -> SciFactPrediction:

        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("claim must be a non-empty string.")

        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("evidence must be a non-empty string.")

        encoded = self.tokenizer(
            claim,
            evidence,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(self.device)
            for key, value in encoded.items()
        }

        with torch.no_grad():
            outputs = self.model(**encoded)

        probabilities = torch.softmax(outputs.logits, dim=-1)[0]

        predicted_id = int(torch.argmax(probabilities).item())

        label = ID_TO_LABEL[predicted_id].value

        probability_map = {
            ID_TO_LABEL[index].value: float(probabilities[index].item())
            for index in range(len(probabilities))
        }

        return SciFactPrediction(
            label=label,
            confidence=float(probabilities[predicted_id].item()),
            probabilities=probability_map,
        )