"""Standalone evaluation for the locally trained SciFact classifier."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_recall_fscore_support,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .dataset_loader import SciFactDatasetLoader
from .labels import VerificationLabel
from .preprocess import SciFactPreprocessor


LABELS = [
    VerificationLabel.SUPPORTED.value,
    VerificationLabel.REFUTED.value,
]


def evaluate_model(
    model_path: str | Path,
    dataset_root: str | Path = "data/scifact",
    max_length: int = 256,
) -> dict[str, object]:

    model_path = Path(model_path)

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        str(model_path),
        local_files_only=True,
    )

    model.eval()

    loader = SciFactDatasetLoader(dataset_root)
    corpus = loader.load_corpus()
    claims = loader.load_claims("dev")

    examples = SciFactPreprocessor().build_examples(
        claims=claims,
        corpus=corpus,
    )

    texts_a = [example.claim for example in examples]
    texts_b = [example.evidence for example in examples]

    true_labels = [
        0 if example.label == VerificationLabel.SUPPORTED else 1
        for example in examples
    ]

    predictions: list[int] = []

    with torch.no_grad():
        for start in range(0, len(examples), 8):
            batch_a = texts_a[start : start + 8]
            batch_b = texts_b[start : start + 8]

            inputs = tokenizer(
                batch_a,
                batch_b,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )

            outputs = model(**inputs)
            batch_predictions = outputs.logits.argmax(dim=-1)

            predictions.extend(
                batch_predictions.cpu().tolist()
            )

    accuracy = accuracy_score(
        true_labels,
        predictions,
    )

    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels,
        predictions,
        labels=[0, 1],
        zero_division=0,
    )

    macro_precision = precision.mean()
    macro_recall = recall.mean()
    macro_f1 = f1.mean()

    report = classification_report(
        true_labels,
        predictions,
        labels=[0, 1],
        target_names=LABELS,
        zero_division=0,
    )

    return {
        "dataset": "SciFact dev",
        "examples": len(examples),
        "accuracy": float(accuracy),
        "macro_precision": float(macro_precision),
        "macro_recall": float(macro_recall),
        "macro_f1": float(macro_f1),
        "classification_report": report,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default="models/scifact",
    )

    parser.add_argument(
        "--data",
        default="data/scifact",
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=256,
    )

    args = parser.parse_args()

    results = evaluate_model(
        model_path=args.model,
        dataset_root=args.data,
        max_length=args.max_length,
    )

    print(json.dumps(
        {
            key: value
            for key, value in results.items()
            if key != "classification_report"
        },
        indent=2,
    ))

    print("\nClassification report:")
    print(results["classification_report"])