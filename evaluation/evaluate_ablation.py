"""
Evaluate Ablation Configurations for Table V and Hypotheses Testing.
Configurations:
1. Full Framework
2. Without NLI
3. Without Dense Retrieval
4. Without BM25/RRF
5. Without Uncertainty
6. Without Contradiction Rules
7. Without Claim Decomposition

Metrics:
- Macro-F1
- Delta Macro-F1 (Full Framework - Ablation)
- McNemar's Chi-squared and p-value for H1 (Claim-level vs Passage-level)
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from evaluation.hybrid_retriever import HybridRetriever
    from evaluation.metrics import calculate_verification_metrics, compute_statistical_tests, VerificationMetrics
    from evaluation.evaluate_detection import load_stratified_detection_dataset, to_retrieved_docs
except (ImportError, ModuleNotFoundError):
    from hybrid_retriever import HybridRetriever
    from metrics import calculate_verification_metrics, compute_statistical_tests, VerificationMetrics
    from evaluate_detection import load_stratified_detection_dataset, to_retrieved_docs

from retrieval.providers.base import RetrievedDocument
from verification.hf_verifier import HuggingFaceClaimVerifier, StructuredClaimReport
from verification.scifact_verify import VerificationStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_ablation_experiments(
    dataset: list[dict[str, Any]] | None = None,
    output_path: Path | str = PROJECT_ROOT / "evaluation" / "results" / "ablation_results.json",
    top_k: int = 5,
) -> dict[str, Any]:
    """Execute evaluation for Table V."""
    if dataset is None:
        dataset = load_stratified_detection_dataset()

    retriever = HybridRetriever()
    actual_labels = [item["actual_label"] for item in dataset]

    # Pre-retrieve evidence for efficiency
    logger.info("Pre-retrieving evidence caches for ablation configurations...")
    cache_rrf = {item["id"]: retriever.retrieve_hybrid_rrf(item["claim"], k=top_k) for item in dataset}
    cache_dense = {item["id"]: retriever.retrieve_dense(item["claim"], k=top_k) for item in dataset}
    cache_bm25 = {item["id"]: retriever.retrieve_bm25(item["claim"], k=top_k) for item in dataset}

    configurations = [
        "Full Framework",
        "Without NLI",
        "Without Dense Retrieval",
        "Without BM25/RRF",
        "Without Uncertainty",
        "Without Contradiction Rules",
        "Without Claim Decomposition",
    ]

    results_by_config: dict[str, Any] = {}
    preds_by_config: dict[str, list[str]] = {}
    detailed_by_config: dict[str, list[dict[str, Any]]] = {c: [] for c in configurations}

    # Initialize standard verifier
    base_verifier = HuggingFaceClaimVerifier()
    base_verifier._lazy_init_hf_pipeline()

    for config in configurations:
        logger.info(f"Evaluating ablation configuration: {config}...")
        pred_labels: list[str] = []
        latencies: list[float] = []

        for idx, item in enumerate(dataset):
            cid = item["id"]
            claim = item["claim"]
            t0 = time.perf_counter()

            # Select evidence source based on configuration
            if config == "Without Dense Retrieval":
                evidence = to_retrieved_docs(cache_bm25[cid])
            elif config == "Without BM25/RRF":
                evidence = to_retrieved_docs(cache_dense[cid])
            else:
                evidence = to_retrieved_docs(cache_rrf[cid])

            # Apply configuration logic
            if config == "Without NLI":
                # Fallback purely to lexical similarity / stance overlap without transformer NLI
                # Uses simple token and keyword stance alignment
                sup_score = 0.0
                ref_score = 0.0
                for doc in evidence:
                    stance = base_verifier.contradiction_detector.analyze_passage(claim, doc)
                    if stance.status == VerificationStatus.SUPPORTED:
                        sup_score += doc.similarity_score
                    elif stance.status == VerificationStatus.REFUTED:
                        ref_score += doc.similarity_score

                if not evidence or (sup_score < 0.4 and ref_score < 0.4):
                    pred = "UNCERTAIN"
                elif ref_score > sup_score:
                    pred = "REFUTED"
                else:
                    pred = "SUPPORTED"

            elif config == "Without Uncertainty":
                # Standard verification, but disables the UNCERTAIN fallback
                # Forces prediction to argmax between SUPPORTED and REFUTED
                report = base_verifier.verify_single_claim(claim, evidence)
                if report.verdict in ["UNCERTAIN", "UNVERIFIED"]:
                    # Force decision based on which count or score is higher
                    if report.contradicting_count > 0:
                        pred = "REFUTED"
                    elif report.supporting_count > 0:
                        pred = "SUPPORTED"
                    else:
                        # Tie-breaker based on lexical cue
                        pred = "SUPPORTED" if "not" not in claim.lower() else "REFUTED"
                else:
                    pred = report.verdict

            elif config == "Without Contradiction Rules":
                # Bypasses heuristic contradiction rules and relies strictly on raw DeBERTa NLI outputs
                cross_checks = []
                for doc in evidence:
                    if base_verifier._hf_pipeline is not None:
                        try:
                            premise = doc.content[:500]
                            res = base_verifier._hf_pipeline({"text": premise, "text_pair": claim})
                            if isinstance(res, list) and res:
                                res = res[0]
                            lbl = (res.get("label") or "").upper()
                            score = float(res.get("score", 0.5))
                            if score > 0.60:
                                if "ENTAIL" in lbl:
                                    cross_checks.append("SUPPORTED")
                                elif "CONTRADICT" in lbl:
                                    cross_checks.append("REFUTED")
                                else:
                                    cross_checks.append("UNCERTAIN")
                            else:
                                cross_checks.append("UNCERTAIN")
                        except Exception:
                            cross_checks.append("UNCERTAIN")
                    else:
                        cross_checks.append("UNCERTAIN")

                sup_c = sum(1 for c in cross_checks if c == "SUPPORTED")
                ref_c = sum(1 for c in cross_checks if c == "REFUTED")
                if not evidence or len(cross_checks) == 0:
                    pred = "UNCERTAIN"
                elif ref_c > 0 and ref_c >= sup_c:
                    pred = "REFUTED"
                elif sup_c > 0 and ref_c == 0:
                    pred = "SUPPORTED"
                else:
                    pred = "UNCERTAIN"

            elif config == "Without Claim Decomposition":
                # Passage-level verification (evaluates full passage without atomic claim decomposition)
                # Matches monolithic verification behavior
                concatenated_evidence = " ".join(d.content[:300] for d in evidence[:2])
                if not concatenated_evidence.strip():
                    pred = "UNCERTAIN"
                else:
                    # Pass the entire claim and concatenated passage as one monolithic block
                    monolithic_doc = RetrievedDocument(
                        title="Aggregated Evidence",
                        content=concatenated_evidence,
                        source="aggregated",
                        similarity_score=max((d.similarity_score for d in evidence), default=0.5),
                    )
                    report = base_verifier.verify_single_claim(claim, [monolithic_doc])
                    pred = report.verdict if report.verdict != "UNVERIFIED" else "UNCERTAIN"

            else:  # "Full Framework"
                report = base_verifier.verify_single_claim(claim, evidence)
                pred = report.verdict if report.verdict != "UNVERIFIED" else "UNCERTAIN"

            lat = time.perf_counter() - t0
            pred_labels.append(pred)
            latencies.append(lat)

            detailed_by_config[config].append({
                "claim_id": cid,
                "claim": claim,
                "actual": item["actual_label"],
                "predicted": pred,
                "correct": bool(pred == item["actual_label"]),
                "latency_s": round(lat, 4),
            })

        preds_by_config[config] = pred_labels
        metrics = calculate_verification_metrics(
            actual=actual_labels,
            predicted=pred_labels,
            latencies=latencies,
            labels=["SUPPORTED", "REFUTED", "UNCERTAIN"],
        )
        results_by_config[config] = metrics.to_dict()

        logger.info(f"[{config}] Macro-F1: {metrics.f1_macro:.4f} | Acc: {metrics.accuracy:.4f}")

    full_f1 = results_by_config["Full Framework"]["f1_macro"]

    # Calculate Delta Macro-F1: Δ Macro-F1 = Ablation - Full Framework (negative indicates drop)
    table_v_rows = []
    for config in configurations:
        cfg_f1 = results_by_config[config]["f1_macro"]
        delta_f1 = cfg_f1 - full_f1 if config != "Full Framework" else 0.0
        table_v_rows.append({
            "Configuration": config,
            "Macro-F1": round(cfg_f1, 3),
            "Δ Macro-F1": f"{delta_f1:+.3f}" if config != "Full Framework" else "0.000",
        })

    # Statistical significance test for H1: Claim-level (Full Framework) vs Passage-level (Without Claim Decomposition)
    h1_stats = compute_statistical_tests(
        actual=actual_labels,
        pred_baseline=preds_by_config["Without Claim Decomposition"],
        pred_proposed=preds_by_config["Full Framework"],
    )
    logger.info(
        f"Hypothesis H1 McNemar Test: chi2={h1_stats['mcnemar_chi2']:.4f}, "
        f"p={h1_stats['mcnemar_p_value']:.4e} (p < 0.05: {h1_stats['statistically_significant_p05']})"
    )

    table_v_data = {
        "title": "TABLE V – ABLATION STUDY",
        "columns": ["Configuration", "Macro-F1", "Δ Macro-F1"],
        "rows": table_v_rows,
    }

    full_output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_claims_evaluated": len(dataset),
        "table_v": table_v_data,
        "metrics_summary": results_by_config,
        "hypothesis_h1_test": h1_stats,
        "detailed_predictions": detailed_by_config,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    logger.info(f"Saved Table V results to {out_file}")
    return full_output


if __name__ == "__main__":
    run_ablation_experiments()
