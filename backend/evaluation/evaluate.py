"""
Evaluation CLI runner for the AI Hallucination Mitigation System.
Calculates authentic evaluation metrics for claim verification and retrieval without fabricated data.

Usage:
    python -m evaluation.evaluate
    python -m evaluation.evaluate --dataset path/to/claims.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path if not present
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.config import settings
from evaluation.dataset import load_evaluation_dataset, EvaluationExample
from evaluation.metrics import calculate_verification_metrics, calculate_retrieval_metrics
from retrieval.retrieve import DocumentRetriever, RetrievedDocument
from retrieval.scifact_documents import load_scifact_documents
from verification.scifact_verify import (
    BaselineSciFactVerifier,
    LocalSciFactVerifier,
    VerificationStatus,
)


def run_evaluation(
    dataset_path: str | None = None,
    verbose: bool = True,
) -> tuple[dict, dict]:
    """
    Run authentic evaluation on the benchmark dataset.
    """
    dataset = load_evaluation_dataset(dataset_path)
    if verbose:
        print(f"\n[AI Hallucination Mitigation] Starting Evaluation on {len(dataset)} benchmark claims...")

    # Initialize verifier
    if settings.SCIFACT_MODEL_PATH.is_dir():
        verifier = LocalSciFactVerifier(str(settings.SCIFACT_MODEL_PATH))
        verifier_type = "Local SciFact Checkpoint"
    else:
        verifier = BaselineSciFactVerifier()
        verifier_type = "Deterministic Semantic Baseline Verifier"

    if verbose:
        print(f"[Verifier Model] Using {verifier_type}")

    # Initialize retriever
    retriever = DocumentRetriever(min_similarity=settings.SCIFACT_MIN_SIMILARITY)
    cache_dir = settings.PROJECT_ROOT / "data" / "scifact" / "cache"
    if not retriever.load(cache_dir) and settings.SCIFACT_CORPUS_PATH.is_file():
        retriever.add_documents(load_scifact_documents(settings.SCIFACT_CORPUS_PATH))

    actual_labels: list[str] = []
    predicted_labels: list[str] = []

    retrieval_relevant: list[list[str]] = []
    retrieval_retrieved: list[list[str]] = []

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    for idx, item in enumerate(dataset, start=1):
        actual_labels.append(item.actual_label)

        # Prepare evidence
        if item.evidence_text:
            evidence = [
                RetrievedDocument(
                    title="Benchmark Evidence",
                    content=item.evidence_text,
                    source="evaluation-ground-truth",
                    similarity_score=1.0,
                )
            ]
        else:
            # Retrieve from corpus
            evidence = retriever.retrieve(item.claim, k=settings.TOP_K)

        if item.relevant_doc_titles:
            retrieval_relevant.append(item.relevant_doc_titles)
            retrieval_retrieved.append([doc.title for doc in evidence])

        if not evidence:
            pred_status = "UNCERTAIN"
        else:
            claims = verifier.extract_claims(item.claim, evidence)
            verifications = verifier.verify(claims, evidence)
            if verifications:
                status = verifications[0].status
                pred_status = status.value if hasattr(status, "value") else str(status)
            else:
                pred_status = "UNCERTAIN"

        predicted_labels.append(pred_status)

        if verbose:
            mark = "[OK]" if pred_status.upper() == item.actual_label.upper() else "[X] "
            print(f" [{idx:02d}] {mark} Claim: {item.claim[:55]}... | Actual: {item.actual_label:<9} | Pred: {pred_status}")

    # Calculate verification metrics
    v_metrics = calculate_verification_metrics(actual_labels, predicted_labels)

    # Calculate retrieval metrics
    r_metrics = calculate_retrieval_metrics(retrieval_relevant, retrieval_retrieved)

    if verbose:
        print("\n" + v_metrics.summary_table())
        print("\n" + r_metrics.summary_table())

    return {
        "accuracy": v_metrics.accuracy,
        "precision_macro": v_metrics.precision_macro,
        "recall_macro": v_metrics.recall_macro,
        "f1_macro": v_metrics.f1_macro,
        "total": v_metrics.total_examples,
    }, {
        "recall_at_5": r_metrics.recall_at_5,
        "recall_at_10": r_metrics.recall_at_10,
        "mrr": r_metrics.mrr,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate AI Hallucination Mitigation System")
    parser.add_argument("--dataset", type=str, default=None, help="Path to evaluation JSONL dataset")
    args = parser.parse_args()

    run_evaluation(dataset_path=args.dataset, verbose=True)


if __name__ == "__main__":
    main()
