"""
Evaluate Hallucination Detection Performance for Table III.
Methods:
1. Base LLM (Zero-shot parametric verification without external evidence)
2. Dense RAG (Dense FAISS retrieval + NLI cross-verification)
3. BM25 RAG (BM25 sparse retrieval + NLI cross-verification)
4. Hybrid RAG (Linear score combination retrieval + NLI cross-verification)
5. Proposed Framework (Hybrid + RRF retrieval + DeBERTa NLI + Contradiction Detection + Uncertainty Calibration)

Metrics:
- Precision (Macro)
- Recall (Macro)
- Macro-F1
- End-to-end Latency (seconds per claim)
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
    from evaluation.metrics import calculate_verification_metrics, VerificationMetrics
except (ImportError, ModuleNotFoundError):
    from hybrid_retriever import HybridRetriever
    from metrics import calculate_verification_metrics, VerificationMetrics

from retrieval.providers.base import RetrievedDocument
from verification.hf_verifier import HuggingFaceClaimVerifier, StructuredClaimReport

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_stratified_detection_dataset(
    claims_path: Path | str = PROJECT_ROOT / "data" / "scifact" / "claims_dev.jsonl",
    sample_size: int = 100,
    random_seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Load reproducible, stratified subset of SciFact dev claims.
    Maintains exact class proportions: SUPPORTED, REFUTED, UNCERTAIN.
    """
    raw_claims = []
    with open(claims_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            ev = item.get("evidence", {})
            has_sup = any(v.get("label") == "SUPPORT" for ev_list in ev.values() for v in ev_list)
            has_ref = any(v.get("label") == "CONTRADICT" for ev_list in ev.values() for v in ev_list)

            if has_sup:
                label = "SUPPORTED"
            elif has_ref:
                label = "REFUTED"
            else:
                label = "UNCERTAIN"

            raw_claims.append({
                "id": item.get("id"),
                "claim": item["claim"],
                "actual_label": label,
                "cited_doc_ids": [str(d) for d in item.get("cited_doc_ids", [])],
            })

    # Group by label
    by_label: dict[str, list[dict[str, Any]]] = {"SUPPORTED": [], "REFUTED": [], "UNCERTAIN": []}
    for item in raw_claims:
        by_label[item["actual_label"]].append(item)

    rng = random.Random(random_seed)
    total_raw = len(raw_claims)
    stratified_sample: list[dict[str, Any]] = []

    # Proportional allocation
    for label, items in by_label.items():
        n_samples = round(sample_size * (len(items) / total_raw))
        items_copy = list(items)
        rng.shuffle(items_copy)
        stratified_sample.extend(items_copy[:n_samples])

    # If rounding led to slightly different total, adjust from largest category
    if len(stratified_sample) > sample_size:
        stratified_sample = stratified_sample[:sample_size]
    elif len(stratified_sample) < sample_size:
        diff = sample_size - len(stratified_sample)
        remaining = [x for x in by_label["SUPPORTED"] if x not in stratified_sample]
        stratified_sample.extend(remaining[:diff])

    stratified_sample.sort(key=lambda x: x["id"])
    logger.info(
        f"Selected stratified evaluation set of {len(stratified_sample)} claims "
        f"(SUPPORTED={sum(1 for x in stratified_sample if x['actual_label'] == 'SUPPORTED')}, "
        f"REFUTED={sum(1 for x in stratified_sample if x['actual_label'] == 'REFUTED')}, "
        f"UNCERTAIN={sum(1 for x in stratified_sample if x['actual_label'] == 'UNCERTAIN')})."
    )
    return stratified_sample


def to_retrieved_docs(hits: list[dict[str, Any]]) -> list[RetrievedDocument]:
    """Convert hit dictionaries to RetrievedDocument objects."""
    return [
        RetrievedDocument(
            title=h.get("title", ""),
            content=h.get("content", ""),
            source=h.get("source", f"scifact:{h.get('doc_id', '')}"),
            similarity_score=float(h.get("score", 0.0)),
        )
        for h in hits
    ]


def run_detection_experiments(
    dataset: list[dict[str, Any]] | None = None,
    output_path: Path | str = PROJECT_ROOT / "evaluation" / "results" / "detection_results.json",
    top_k: int = 5,
) -> dict[str, Any]:
    """Execute evaluation for Table III."""
    if dataset is None:
        dataset = load_stratified_detection_dataset()

    retriever = HybridRetriever()
    verifier = HuggingFaceClaimVerifier()
    verifier._lazy_init_hf_pipeline()

    # Warm-up verifier to eliminate cold-start timing distortion
    logger.info("Warming up verification pipeline...")
    _ = verifier.verify_single_claim("Test claim for pipeline initialization.", [])

    methods = ["Base LLM", "Dense RAG", "BM25 RAG", "Hybrid RAG", "Proposed Framework"]
    results_by_method: dict[str, Any] = {}
    predictions_by_method: dict[str, list[dict[str, Any]]] = {m: [] for m in methods}

    actual_labels = [item["actual_label"] for item in dataset]

    # Pre-retrieve documents for all claims across methods to ensure fairness and speed
    logger.info("Pre-retrieving candidate evidence per method...")
    retrieved_cache: dict[str, dict[int, list[dict[str, Any]]]] = {
        "Dense": {},
        "BM25": {},
        "Hybrid": {},
        "Hybrid_RRF": {},
    }
    retrieval_latencies: dict[str, list[float]] = {
        "Dense": [],
        "BM25": [],
        "Hybrid": [],
        "Hybrid_RRF": [],
    }

    for item in dataset:
        cid = item["id"]
        q = item["claim"]

        t0 = time.perf_counter()
        retrieved_cache["Dense"][cid] = retriever.retrieve_dense(q, k=top_k)
        retrieval_latencies["Dense"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        retrieved_cache["BM25"][cid] = retriever.retrieve_bm25(q, k=top_k)
        retrieval_latencies["BM25"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        retrieved_cache["Hybrid"][cid] = retriever.retrieve_hybrid(q, k=top_k)
        retrieval_latencies["Hybrid"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        retrieved_cache["Hybrid_RRF"][cid] = retriever.retrieve_hybrid_rrf(q, k=top_k)
        retrieval_latencies["Hybrid_RRF"].append(time.perf_counter() - t0)

    # Evaluate each method
    for method in methods:
        logger.info(f"Evaluating Hallucination Detection method: {method}...")
        pred_labels: list[str] = []
        latencies: list[float] = []

        for idx, item in enumerate(dataset):
            cid = item["id"]
            claim = item["claim"]

            if method == "Base LLM":
                # Zero-shot parametric evaluation (no external retrieval)
                t0 = time.perf_counter()
                if verifier._hf_pipeline is not None:
                    try:
                        res = verifier._hf_pipeline({
                            "text": "General medical knowledge and scientific consensus.",
                            "text_pair": claim,
                        })
                        if isinstance(res, list) and res:
                            res = res[0]
                        lbl = (res.get("label") or "").upper()
                        score = float(res.get("score", 0.5))
                        if score > 0.60:
                            if "ENTAIL" in lbl:
                                pred = "SUPPORTED"
                            elif "CONTRADICT" in lbl:
                                pred = "REFUTED"
                            else:
                                pred = "UNCERTAIN"
                        else:
                            pred = "UNCERTAIN"
                    except Exception:
                        pred = "UNCERTAIN"
                else:
                    pred = "UNCERTAIN"
                lat = time.perf_counter() - t0

            else:
                # Determine which retrieval cache to use
                if method == "Dense RAG":
                    raw_docs = retrieved_cache["Dense"][cid]
                    ret_lat = retrieval_latencies["Dense"][idx]
                elif method == "BM25 RAG":
                    raw_docs = retrieved_cache["BM25"][cid]
                    ret_lat = retrieval_latencies["BM25"][idx]
                elif method == "Hybrid RAG":
                    raw_docs = retrieved_cache["Hybrid"][cid]
                    ret_lat = retrieval_latencies["Hybrid"][idx]
                elif method == "Proposed Framework":
                    raw_docs = retrieved_cache["Hybrid_RRF"][cid]
                    ret_lat = retrieval_latencies["Hybrid_RRF"][idx]
                else:
                    raise ValueError(f"Unknown method: {method}")

                docs = to_retrieved_docs(raw_docs)

                t0 = time.perf_counter()
                report = verifier.verify_single_claim(claim, docs)
                verif_lat = time.perf_counter() - t0
                pred = report.verdict
                lat = ret_lat + verif_lat

            # Normalize UNVERIFIED to UNCERTAIN for 3-way evaluation
            if pred == "UNVERIFIED":
                pred = "UNCERTAIN"

            pred_labels.append(pred)
            latencies.append(lat)

            predictions_by_method[method].append({
                "claim_id": cid,
                "claim": claim,
                "actual": item["actual_label"],
                "predicted": pred,
                "correct": bool(pred == item["actual_label"]),
                "latency_s": round(lat, 4),
            })

        metrics = calculate_verification_metrics(
            actual=actual_labels,
            predicted=pred_labels,
            latencies=latencies,
            labels=["SUPPORTED", "REFUTED", "UNCERTAIN"],
        )
        method_summary = metrics.to_dict()
        results_by_method[method] = method_summary

        logger.info(
            f"[{method}] P: {metrics.precision_macro:.4f} | "
            f"R: {metrics.recall_macro:.4f} | "
            f"Macro-F1: {metrics.f1_macro:.4f} | "
            f"Latency: {metrics.mean_latency:.4f}s"
        )

    # Format Table III
    table_iii_data = {
        "title": "TABLE III – HALLUCINATION DETECTION PERFORMANCE",
        "columns": ["Method", "P", "R", "Macro-F1", "Latency"],
        "rows": [
            {
                "Method": m,
                "P": round(results_by_method[m]["precision_macro"], 3),
                "R": round(results_by_method[m]["recall_macro"], 3),
                "Macro-F1": round(results_by_method[m]["f1_macro"], 3),
                "Latency": f"{round(results_by_method[m]['mean_latency_s'], 3)}s",
            }
            for m in methods
        ],
    }

    full_output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_claims_evaluated": len(dataset),
        "table_iii": table_iii_data,
        "metrics_summary": results_by_method,
        "detailed_predictions": predictions_by_method,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    logger.info(f"Saved Table III results to {out_file}")
    return full_output


if __name__ == "__main__":
    run_detection_experiments()
