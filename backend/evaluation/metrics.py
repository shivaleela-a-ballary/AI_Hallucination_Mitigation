"""
Evaluation metrics for verification and retrieval.
Computes real, un-falsified accuracy, precision, recall, F1, confusion matrix, Recall@K, and MRR.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class VerificationMetrics:
    """Metrics for claim verification evaluation."""
    total_examples: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    per_class_metrics: dict[str, dict[str, float]]
    confusion_matrix: dict[str, dict[str, int]]

    def summary_table(self) -> str:
        """Format metrics as a clean, readable text table."""
        lines = [
            "=" * 60,
            "            CLAIM VERIFICATION EVALUATION METRICS",
            "=" * 60,
            f"Total Evaluated Claims : {self.total_examples}",
            f"Overall Accuracy       : {self.accuracy * 100:.2f}%",
            f"Macro Precision        : {self.precision_macro * 100:.2f}%",
            f"Macro Recall           : {self.recall_macro * 100:.2f}%",
            f"Macro F1-Score         : {self.f1_macro * 100:.2f}%",
            "-" * 60,
            f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<8}",
            "-" * 60,
        ]
        for cls, m in self.per_class_metrics.items():
            lines.append(
                f"{cls:<15} {m['precision'] * 100:>8.2f}%   {m['recall'] * 100:>8.2f}%   {m['f1'] * 100:>8.2f}%   {int(m['support']):>7}"
            )
        lines.append("-" * 60)
        lines.append("Confusion Matrix (Rows = Actual, Columns = Predicted):")
        classes = sorted(self.confusion_matrix.keys())
        col_title = "Actual \\ Pred"
        header = f"{col_title:<15} " + " ".join(f"{c:>12}" for c in classes)
        lines.append(header)
        for actual in classes:
            row_str = f"{actual:<15} " + " ".join(
                f"{self.confusion_matrix[actual].get(pred, 0):>12}" for pred in classes
            )
            lines.append(row_str)
        lines.append("=" * 60)
        return "\n".join(lines)


@dataclass
class RetrievalMetrics:
    """Metrics for document retrieval evaluation."""
    total_queries: int
    recall_at_5: float
    recall_at_10: float
    mrr: float

    def summary_table(self) -> str:
        """Format retrieval metrics as a clean text table."""
        lines = [
            "=" * 60,
            "             EVIDENCE RETRIEVAL EVALUATION METRICS",
            "=" * 60,
            f"Total Queries Evaluated: {self.total_queries}",
            f"Recall@5               : {self.recall_at_5 * 100:.2f}%",
            f"Recall@10              : {self.recall_at_10 * 100:.2f}%",
            f"Mean Reciprocal Rank   : {self.mrr:.4f}",
            "=" * 60,
        ]
        return "\n".join(lines)


def calculate_verification_metrics(
    actual: Sequence[str],
    predicted: Sequence[str],
    labels: Sequence[str] = ("SUPPORTED", "REFUTED", "UNCERTAIN"),
) -> VerificationMetrics:
    """
    Compute Accuracy, Precision, Recall, F1, and Confusion Matrix.
    """
    if len(actual) != len(predicted):
        raise ValueError(f"Length mismatch: {len(actual)} actual vs {len(predicted)} predicted")

    total = len(actual)
    if total == 0:
        return VerificationMetrics(
            total_examples=0,
            accuracy=0.0,
            precision_macro=0.0,
            recall_macro=0.0,
            f1_macro=0.0,
            per_class_metrics={l: {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0} for l in labels},
            confusion_matrix={l: {p: 0 for p in labels} for l in labels},
        )

    # Standardize label strings
    actual_norm = [str(a).strip().upper() for a in actual]
    pred_norm = [str(p).strip().upper() for p in predicted]
    unique_labels = sorted(set(labels) | set(actual_norm) | set(pred_norm))

    # Confusion matrix
    matrix: dict[str, dict[str, int]] = {l: {p: 0 for p in unique_labels} for l in unique_labels}
    correct = 0
    for a, p in zip(actual_norm, pred_norm):
        if a in matrix and p in matrix[a]:
            matrix[a][p] += 1
        if a == p:
            correct += 1

    accuracy = correct / total

    # Per-class metrics
    per_class: dict[str, dict[str, float]] = {}
    precisions = []
    recalls = []
    f1s = []

    for l in unique_labels:
        tp = matrix[l][l]
        fp = sum(matrix[other][l] for other in unique_labels if other != l)
        fn = sum(matrix[l][other] for other in unique_labels if other != l)
        support = sum(matrix[l].values())

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[l] = {
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "support": float(support),
        }

        if support > 0 or (tp + fp) > 0:
            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

    macro_prec = sum(precisions) / len(precisions) if precisions else 0.0
    macro_rec = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return VerificationMetrics(
        total_examples=total,
        accuracy=accuracy,
        precision_macro=macro_prec,
        recall_macro=macro_rec,
        f1_macro=macro_f1,
        per_class_metrics=per_class,
        confusion_matrix=matrix,
    )


def calculate_retrieval_metrics(
    relevant_doc_titles_per_query: Sequence[Sequence[str]],
    retrieved_doc_titles_per_query: Sequence[Sequence[str]],
) -> RetrievalMetrics:
    """
    Compute Recall@5, Recall@10, and Mean Reciprocal Rank (MRR).
    """
    total = len(relevant_doc_titles_per_query)
    if total == 0:
        return RetrievalMetrics(0, 0.0, 0.0, 0.0)

    recall_5_list: list[float] = []
    recall_10_list: list[float] = []
    reciprocal_ranks: list[float] = []

    for relevant, retrieved in zip(relevant_doc_titles_per_query, retrieved_doc_titles_per_query):
        relevant_set = {r.strip().lower() for r in relevant if r}
        if not relevant_set:
            continue

        retrieved_list = [r.strip().lower() for r in retrieved]

        # Recall@5
        top_5 = set(retrieved_list[:5])
        hits_5 = len(relevant_set & top_5)
        recall_5_list.append(hits_5 / len(relevant_set))

        # Recall@10
        top_10 = set(retrieved_list[:10])
        hits_10 = len(relevant_set & top_10)
        recall_10_list.append(hits_10 / len(relevant_set))

        # MRR
        rr = 0.0
        for rank, item in enumerate(retrieved_list, start=1):
            if item in relevant_set:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return RetrievalMetrics(
        total_queries=len(recall_5_list),
        recall_at_5=sum(recall_5_list) / len(recall_5_list) if recall_5_list else 0.0,
        recall_at_10=sum(recall_10_list) / len(recall_10_list) if recall_10_list else 0.0,
        mrr=sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0,
    )
