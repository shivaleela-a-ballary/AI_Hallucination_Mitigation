"""Local-only model factory for SciFact evidence classification."""

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
            raise ValueError("max_length must be greater than zero.")

        if self.num_labels != 2:
            raise ValueError(
                "SciFact evidence classifier requires exactly 2 labels."
            )


def load_local_sequence_classifier(config: SciFactModelConfig):
    """Load an already-trained local checkpoint only."""

    if not config.model_path.is_dir():
        raise FileNotFoundError(
            f"Local SciFact model checkpoint does not exist: "
            f"{config.model_path}"
        )

    from transformers import AutoModelForSequenceClassification
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(config.model_path),
        local_files_only=config.local_files_only,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        str(config.model_path),
        num_labels=config.num_labels,
        local_files_only=config.local_files_only,
    )

    return tokenizer, model