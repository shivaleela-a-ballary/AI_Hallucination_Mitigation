"""Training utilities for a SciFact sequence classifier.

Training is intentionally explicit and is never executed during import.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .dataset_loader import SciFactDatasetLoader
from .labels import VerificationLabel, label_to_id
from .preprocess import SciFactExample, SciFactPreprocessor


def build_training_examples(
    dataset_root: str | Path,
) -> list[SciFactExample]:

    loader = SciFactDatasetLoader(dataset_root)

    corpus = loader.load_corpus()
    claims = loader.load_claims("train")

    preprocessor = SciFactPreprocessor()

    return preprocessor.build_examples(
        claims=claims,
        corpus=corpus,
    )


def convert_examples_to_training_rows(
    examples: Iterable[SciFactExample],
) -> list[dict[str, object]]:

    rows: list[dict[str, object]] = []

    for example in examples:
        rows.append(
            {
                "claim": example.claim,
                "evidence": example.evidence,
                "label": label_to_id(example.label),
            }
        )

    return rows


def validate_training_data(
    examples: Iterable[SciFactExample],
) -> None:

    examples = list(examples)

    if not examples:
        raise ValueError("No SciFact training examples were found.")

    labels = {example.label for example in examples}

    expected = {
        VerificationLabel.SUPPORTED,
        VerificationLabel.REFUTED,
        VerificationLabel.UNCERTAIN,
    }

    # This is informational validation rather than fabricated data.
    missing = expected - labels

    if missing:
        raise ValueError(
            "Training data does not contain all three verification labels: "
            + ", ".join(label.value for label in missing)
        )