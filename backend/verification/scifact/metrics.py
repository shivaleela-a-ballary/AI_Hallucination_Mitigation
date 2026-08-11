"""Metrics for three-way SciFact classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ClassificationMetrics:
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    per_label_precision: dict[int, float]
    per_label_recall: dict[int, float]
    per_label_f1: dict[int, float]


def compute_metrics(
    predictions: Sequence[int],
    labels: Sequence[int],
    num_labels: int = 3,
) -> ClassificationMetrics:
    """Compute accuracy, macro precision, recall, and F1."""

    if len(predictions) != len(labels) or not labels:
        raise ValueError(
            "Predictions and non-empty labels must have equal length."
        )

    if num_labels <= 0:
        raise ValueError("num_labels must be positive.")

    all_values = [*predictions, *labels]

    if any(value < 0 or value >= num_labels for value in all_values):
        raise ValueError("Labels must be in the configured class range.")

    accuracy = sum(
        prediction == label
        for prediction, label in zip(predictions, labels)
    ) / len(labels)

    precisions: dict[int, float] = {}
    recalls: dict[int, float] = {}
    f1_scores: dict[int, float] = {}

    for label in range(num_labels):

        true_positive = sum(
            prediction == label and actual == label
            for prediction, actual in zip(predictions, labels)
        )

        false_positive = sum(
            prediction == label and actual != label
            for prediction, actual in zip(predictions, labels)
        )

        false_negative = sum(
            prediction != label and actual == label
            for prediction, actual in zip(predictions, labels)
        )

        precision_denominator = true_positive + false_positive
        recall_denominator = true_positive + false_negative

        precision = (
            true_positive / precision_denominator
            if precision_denominator
            else 0.0
        )

        recall = (
            true_positive / recall_denominator
            if recall_denominator
            else 0.0
        )

        f1_denominator = precision + recall

        f1 = (
            2 * precision * recall / f1_denominator
            if f1_denominator
            else 0.0
        )

        precisions[label] = precision
        recalls[label] = recall
        f1_scores[label] = f1

    return ClassificationMetrics(
        accuracy=accuracy,
        macro_precision=sum(precisions.values()) / num_labels,
        macro_recall=sum(recalls.values()) / num_labels,
        macro_f1=sum(f1_scores.values()) / num_labels,
        per_label_precision=precisions,
        per_label_recall=recalls,
        per_label_f1=f1_scores,
    )