"""
Metrics calculation for Hallucination Detection, Evidence Retrieval, and Ablation Analysis.
Provides authentic statistical computations without mock or fabricated values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple
import numpy as np


@dataclass
class VerificationMetrics:
    """Metrics for 3-way hallucination stance classification."""
    total_examples: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    per_class_metrics: dict[str, dict[str, float]]
    confusion_matrix: dict[str, dict[str, int]]
    mean_latency: float = 0.0
    median_latency: float = 0.0
    std_latency: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_examples": self.total_examples,
            "accuracy": round(self.accuracy, 4),
            "precision_macro": round(self.precision_macro, 4),
            "recall_macro": round(self.recall_macro, 4),
            "f1_macro": round(self.f1_macro, 4),
            "per_class": {
                c: {k: round(v, 4) for k, v in m.items()}
                for c, m in self.per_class_metrics.items()
            },
            "confusion_matrix": self.confusion_matrix,
            "mean_latency_s": round(self.mean_latency, 4),
            "median_latency_s": round(self.median_latency, 4),
            "std_latency_s": round(self.std_latency, 4),
        }


@dataclass
class RetrievalMetrics:
    """Metrics for evidence retrieval (Recall@K and MRR)."""
    total_queries: int
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mrr: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "recall_at_1": round(self.recall_at_1, 4),
            "recall_at_5": round(self.recall_at_5, 4),
            "recall_at_10": round(self.recall_at_10, 4),
            "mrr": round(self.mrr, 4),
        }


def calculate_verification_metrics(
    actual: Sequence[str],
    predicted: Sequence[str],
    latencies: Sequence[float] | None = None,
    labels: Sequence[str] = ("SUPPORTED", "REFUTED", "UNCERTAIN"),
) -> VerificationMetrics:
    """
    Compute Precision, Recall, and Macro-F1 across classes according to standard formulas:
    Precision = TP / (TP + FP)
    Recall = TP / (TP + FN)
    F1 = 2 * Precision * Recall / (Precision + Recall)
    Macro-F1 = unweighted mean of per-class F1 scores.
    """
    if len(actual) != len(predicted):
        raise ValueError(f"Length mismatch: {len(actual)} actual vs {len(predicted)} predicted")

    total = len(actual)
    if total == 0:
        return VerificationMetrics(0, 0.0, 0.0, 0.0, 0.0, {}, {})

    actual_norm = [str(a).strip().upper() for a in actual]
    pred_norm = [str(p).strip().upper() for p in predicted]
    unique_labels = list(labels)

    # Build Confusion Matrix
    matrix: dict[str, dict[str, int]] = {l: {p: 0 for p in unique_labels} for l in unique_labels}
    correct = 0
    for a, p in zip(actual_norm, pred_norm):
        if a in matrix and p in matrix[a]:
            matrix[a][p] += 1
        elif a in matrix:
            # Handle unexpected predicted label
            matrix[a].setdefault(p, 0)
            matrix[a][p] += 1
        if a == p:
            correct += 1

    accuracy = correct / total

    # Per-Class Precision, Recall, F1
    per_class: dict[str, dict[str, float]] = {}
    precisions = []
    recalls = []
    f1s = []

    for l in unique_labels:
        tp = matrix[l].get(l, 0)
        fp = sum(matrix[other].get(l, 0) for other in matrix if other != l)
        fn = sum(matrix[l].get(other, 0) for other in matrix[l] if other != l)
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
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    macro_prec = sum(precisions) / len(precisions) if precisions else 0.0
    macro_rec = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    mean_lat, med_lat, std_lat = 0.0, 0.0, 0.0
    if latencies and len(latencies) > 0:
        mean_lat = float(np.mean(latencies))
        med_lat = float(np.median(latencies))
        std_lat = float(np.std(latencies))

    return VerificationMetrics(
        total_examples=total,
        accuracy=accuracy,
        precision_macro=macro_prec,
        recall_macro=macro_rec,
        f1_macro=macro_f1,
        per_class_metrics=per_class,
        confusion_matrix=matrix,
        mean_latency=mean_lat,
        median_latency=med_lat,
        std_latency=std_lat,
    )


def calculate_retrieval_metrics(
    gold_doc_ids_per_query: Sequence[Sequence[Any]],
    retrieved_doc_ids_per_query: Sequence[Sequence[Any]],
) -> RetrievalMetrics:
    """
    Compute Recall@1, Recall@5, Recall@10 and MRR over queries with gold evidence.
    Recall@K = fraction of queries where at least one gold document appears in Top-K.
    """
    total = len(gold_doc_ids_per_query)
    if total == 0:
        return RetrievalMetrics(0, 0.0, 0.0, 0.0, 0.0)

    recall_1_hits = 0
    recall_5_hits = 0
    recall_10_hits = 0
    reciprocal_ranks: list[float] = []

    valid_queries = 0
    for gold, retrieved in zip(gold_doc_ids_per_query, retrieved_doc_ids_per_query):
        gold_set = {str(g).strip().lower() for g in gold if g is not None}
        if not gold_set:
            continue

        valid_queries += 1
        ret_list = [str(r).strip().lower() for r in retrieved]

        # Top 1
        if any(r in gold_set for r in ret_list[:1]):
            recall_1_hits += 1

        # Top 5
        if any(r in gold_set for r in ret_list[:5]):
            recall_5_hits += 1

        # Top 10
        if any(r in gold_set for r in ret_list[:10]):
            recall_10_hits += 1

        # MRR
        rr = 0.0
        for rank, item in enumerate(ret_list, start=1):
            if item in gold_set:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return RetrievalMetrics(
        total_queries=valid_queries,
        recall_at_1=recall_1_hits / valid_queries if valid_queries else 0.0,
        recall_at_5=recall_5_hits / valid_queries if valid_queries else 0.0,
        recall_at_10=recall_10_hits / valid_queries if valid_queries else 0.0,
        mrr=sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0,
    )


def compute_statistical_tests(
    actual: Sequence[str],
    pred_baseline: Sequence[str],
    pred_proposed: Sequence[str],
) -> dict[str, Any]:
    """
    Compute paired statistical comparison (McNemar test & Wilcoxon signed-rank test).
    Tests hypothesis H1 (claim-level vs passage-level or baseline vs proposed).
    """
    from scipy import stats

    actual_norm = [str(a).strip().upper() for a in actual]
    base_corr = np.array([1 if p.strip().upper() == a else 0 for p, a in zip(pred_baseline, actual_norm)])
    prop_corr = np.array([1 if p.strip().upper() == a else 0 for p, a in zip(pred_proposed, actual_norm)])

    # Contingency matrix for McNemar
    # b: proposed correct, baseline incorrect
    # c: baseline correct, proposed incorrect
    b = int(np.sum((prop_corr == 1) & (base_corr == 0)))
    c = int(np.sum((prop_corr == 0) & (base_corr == 1)))
    a_both = int(np.sum((prop_corr == 1) & (base_corr == 1)))
    d_neither = int(np.sum((prop_corr == 0) & (base_corr == 0)))

    # McNemar test with continuity correction
    if (b + c) > 0:
        chi2 = ((abs(b - c) - 1.0) ** 2) / (b + c)
        p_mcnemar = 1.0 - stats.chi2.cdf(chi2, df=1)
    else:
        chi2 = 0.0
        p_mcnemar = 1.0

    # Wilcoxon signed-rank test
    diff = prop_corr - base_corr
    non_zero = diff[diff != 0]
    if len(non_zero) > 0:
        try:
            w_stat, p_wilcoxon = stats.wilcoxon(prop_corr, base_corr)
        except Exception:
            w_stat, p_wilcoxon = 0.0, 1.0
    else:
        w_stat, p_wilcoxon = 0.0, 1.0

    return {
        "contingency_matrix": {"both_correct": a_both, "proposed_only": b, "baseline_only": c, "neither_correct": d_neither},
        "mcnemar_chi2": float(chi2),
        "mcnemar_p_value": float(p_mcnemar),
        "wilcoxon_stat": float(w_stat),
        "wilcoxon_p_value": float(p_wilcoxon),
        "statistically_significant_p05": bool(p_mcnemar < 0.05),
    }
