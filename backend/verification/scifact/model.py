"""Local-only model factory for three-way SciFact sequence classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SciFactModelConfig:
    model_path: Path
    max_length: int = 512
    num_labels: int = 3
    local_files_only: bool = True

    def __post_init__(self) -> None:
        if self.max_length <= 0 or self.num_labels != 3:
            raise ValueError("SciFact model configuration requires max_length > 0 and exactly 3 labels.")


def load_local_sequence_classifier(config: SciFactModelConfig):
    """Load only an already-present local checkpoint; never contact Hugging Face."""
    if not config.model_path.is_dir():
        raise FileNotFoundError(f"Local SciFact model checkpoint does not exist: {config.model_path}")
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(config.model_path), local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        str(config.model_path), num_labels=config.num_labels, local_files_only=True
    )
    return tokenizer, model
