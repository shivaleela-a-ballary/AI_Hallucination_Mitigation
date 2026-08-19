"""Local model factory for the two-class SciFact sequence classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SciFactModelConfig:
    model_path: Path
    max_length: int = 512
    num_labels: int = 2
    local_files_only: bool = True

    def __post_init__(self) -> None:
        if self.max_length <= 0:
            raise ValueError("max_length must be greater than 0.")

        if self.num_labels != 2:
            raise ValueError(
                "SciFact classifier must use exactly 2 labels: "
                "SUPPORTED and REFUTED."
            )


def load_local_sequence_classifier(
    config: SciFactModelConfig,
):
    """Load the locally trained two-class SciFact checkpoint."""

    if not config.model_path.is_dir():
        raise FileNotFoundError(
            f"Local SciFact model checkpoint does not exist: "
            f"{config.model_path}"
        )

    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        str(config.model_path),
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        str(config.model_path),
        local_files_only=True,
    )

    # Safety check: never silently accept the wrong classifier shape.
    if model.config.num_labels != 2:
        raise ValueError(
            f"Expected a 2-class SciFact model, but loaded "
            f"{model.config.num_labels} classes."
        )

    return tokenizer, model