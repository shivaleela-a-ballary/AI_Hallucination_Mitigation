"""
Evaluate Evidence Retrieval Performance for Table IV.
Methods:
- BM25
- Dense
- Hybrid
- Hybrid + RRF

Metrics:
- Recall@1
- Recall@5
- Recall@10
- MRR
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from evaluation.hybrid_retriever import HybridRetriever
    from evaluation.metrics import calculate_retrieval_metrics, RetrievalMetrics
except (ImportError, ModuleNotFoundError):
    from hybrid_retriever import HybridRetriever
    from metrics import calculate_retrieval_metrics, RetrievalMetrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_retrieval_dataset(
    claims_path: Path | str = PROJECT_ROOT / "data" / "scifact" / "claims_dev.jsonl",
) -> list[dict[str, Any]]:
    """Load claims with gold cited document IDs for retrieval evaluation."""
    claims = []
    with open(claims_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            # Gather gold doc IDs from cited_doc_ids and evidence keys
            gold_ids = set()
            for did in item.get("cited_doc_ids", []):
                gold_ids.add(str(did).strip())
            for did in item.get("evidence", {}).keys():
                gold_ids.add(str(did).strip())

            claims.append({
                "id": item.get("id"),
                "claim": item["claim"],
                "gold_doc_ids": list(gold_ids),
            })
    return claims


def run_retrieval_experiments(
    claims: list[dict[str, Any]] | None = None,
    output_path: Path | str = PROJECT_ROOT / "evaluation" / "results" / "retrieval_results.json",
) -> dict[str, Any]:
    """Execute retrieval evaluation across BM25, Dense, Hybrid, and Hybrid+RRF."""
    if claims is None:
        claims = load_retrieval_dataset()

    logger.info(f"Loaded {len(claims)} evaluation claims with evidence annotations.")
    retriever = HybridRetriever()

    methods = ["BM25", "Dense", "Hybrid", "Hybrid + RRF"]
    results_by_method: dict[str, Any] = {}
    detailed_predictions: dict[str, list[dict[str, Any]]] = {m: [] for m in methods}

    for method in methods:
        logger.info(f"Evaluating retrieval method: {method}...")
        gold_lists = []
        retrieved_lists = []
        start_time = time.perf_counter()

        for idx, item in enumerate(claims):
            query = item["claim"]
            gold = item["gold_doc_ids"]

            if method == "BM25":
                hits = retriever.retrieve_bm25(query, k=10)
            elif method == "Dense":
                hits = retriever.retrieve_dense(query, k=10)
            elif method == "Hybrid":
                hits = retriever.retrieve_hybrid(query, k=10, alpha=0.5)
            elif method == "Hybrid + RRF":
                hits = retriever.retrieve_hybrid_rrf(query, k=10, k_rrf=60)
            else:
                raise ValueError(f"Unknown method: {method}")

            ret_ids = [str(h["doc_id"]) for h in hits]
            gold_lists.append(gold)
            retrieved_lists.append(ret_ids)

            detailed_predictions[method].append({
                "claim_id": item["id"],
                "query": query,
                "gold_docs": gold,
                "retrieved_docs": ret_ids,
                "hit_at_1": bool(any(r in gold for r in ret_ids[:1])),
                "hit_at_5": bool(any(r in gold for r in ret_ids[:5])),
                "hit_at_10": bool(any(r in gold for r in ret_ids[:10])),
            })

        duration = time.perf_counter() - start_time
        metrics = calculate_retrieval_metrics(gold_lists, retrieved_lists)
        method_dict = metrics.to_dict()
        method_dict["total_time_seconds"] = round(duration, 3)
        method_dict["avg_query_latency_ms"] = round((duration / len(claims)) * 1000, 2)
        results_by_method[method] = method_dict

        logger.info(
            f"[{method}] Recall@1: {metrics.recall_at_1:.4f} | "
            f"Recall@5: {metrics.recall_at_5:.4f} | "
            f"Recall@10: {metrics.recall_at_10:.4f} | "
            f"MRR: {metrics.mrr:.4f} | "
            f"Time: {duration:.2f}s"
        )

    # Compile Table IV
    table_iv_data = {
        "title": "TABLE IV – EVIDENCE RETRIEVAL PERFORMANCE",
        "columns": ["Retrieval Method", "Recall@1", "Recall@5", "Recall@10"],
        "rows": [
            {
                "Retrieval Method": m,
                "Recall@1": round(results_by_method[m]["recall_at_1"], 3),
                "Recall@5": round(results_by_method[m]["recall_at_5"], 3),
                "Recall@10": round(results_by_method[m]["recall_at_10"], 3),
                "MRR": round(results_by_method[m]["mrr"], 3),
            }
            for m in methods
        ],
    }

    full_output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_claims_evaluated": len(claims),
        "table_iv": table_iv_data,
        "metrics_summary": results_by_method,
        "detailed_predictions": detailed_predictions,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    logger.info(f"Saved Table IV results to {out_file}")
    return full_output


if __name__ == "__main__":
    run_retrieval_experiments()
