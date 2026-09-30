"""
Hybrid Retriever for SciFact Evaluation and Benchmarking.
Implements:
1. BM25 (Sparse) via Rank-BM25
2. Dense Retrieval via Pre-indexed FAISS & Sentence-Transformers (all-MiniLM-L6-v2)
3. Hybrid Score Fusion (Linear Combination of Normalized Scores)
4. Hybrid + RRF (Reciprocal Rank Fusion with standard k_0=60)
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure backend modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from retrieval.providers.base import Document, RetrievedDocument
from retrieval.retrieve import DocumentRetriever
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def tokenize_text(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens for BM25."""
    return re.findall(r"\b\w+\b", text.lower())


def extract_doc_id(source: str) -> str:
    """Extract numeric/canonical doc_id from source string (e.g. 'scifact:12345' -> '12345')."""
    if ":" in source:
        return source.split(":")[-1].strip()
    return source.strip()


class BM25Retriever:
    """In-memory BM25 retriever over SciFact corpus with disk caching."""

    def __init__(
        self,
        corpus_path: Path | str = PROJECT_ROOT / "data" / "scifact" / "corpus.jsonl",
        cache_path: Path | str = PROJECT_ROOT / "data" / "scifact" / "cache" / "bm25_model.pkl",
    ) -> None:
        self.corpus_path = Path(corpus_path)
        self.cache_path = Path(cache_path)
        self.doc_ids: list[str] = []
        self.titles: list[str] = []
        self.contents: list[str] = []
        self.bm25: Optional[BM25Okapi] = None
        self._cache: dict[tuple[str, int], list[dict[str, Any]]] = {}
        self._initialize()

    def _initialize(self) -> None:
        """Load from cache if exists, otherwise index from corpus.jsonl and cache."""
        if self.cache_path.exists():
            try:
                logger.info(f"Loading cached BM25 index from {self.cache_path}...")
                with open(self.cache_path, "rb") as f:
                    cache_data = pickle.load(f)
                self.doc_ids = cache_data["doc_ids"]
                self.titles = cache_data["titles"]
                self.contents = cache_data["contents"]
                self.bm25 = cache_data["bm25"]
                logger.info(f"Successfully loaded BM25 index with {len(self.doc_ids)} documents.")
                return
            except Exception as e:
                logger.warning(f"Failed to load cached BM25: {e}. Rebuilding...")

        logger.info(f"Building BM25 index from {self.corpus_path}...")
        tokenized_corpus = []
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                doc_id = str(data["doc_id"])
                title = data.get("title", "")
                abstract = data.get("abstract", [])
                abstract_text = " ".join(abstract) if isinstance(abstract, list) else str(abstract)
                full_text = f"{title} {abstract_text}"

                self.doc_ids.append(doc_id)
                self.titles.append(title)
                self.contents.append(abstract_text)
                tokenized_corpus.append(tokenize_text(full_text))

        self.bm25 = BM25Okapi(tokenized_corpus)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_path, "wb") as f:
                pickle.dump(
                    {
                        "doc_ids": self.doc_ids,
                        "titles": self.titles,
                        "contents": self.contents,
                        "bm25": self.bm25,
                    },
                    f,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            logger.info(f"Saved BM25 index to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Could not cache BM25 index: {e}")

    def retrieve(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Retrieve top-k documents by BM25 score."""
        cache_key = (query, k)
        if cache_key in self._cache:
            return self._cache[cache_key]

        tokens = tokenize_text(query)
        if not tokens or self.bm25 is None:
            return []

        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            results.append({
                "doc_id": self.doc_ids[idx],
                "score": score,
                "title": self.titles[idx],
                "content": self.contents[idx],
                "source": f"scifact:{self.doc_ids[idx]}",
            })
        self._cache[cache_key] = results
        return results


class DenseRetrieverWrapper:
    """Dense retriever wrapping backend DocumentRetriever with query embedding caching."""

    def __init__(
        self,
        cache_dir: Path | str = PROJECT_ROOT / "data" / "scifact" / "cache",
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.retriever = DocumentRetriever()
        if not self.retriever.load(self.cache_dir):
            raise RuntimeError(f"Could not load pre-indexed FAISS cache from {self.cache_dir}")
        self._embedding_cache: dict[str, np.ndarray] = {}
        self._results_cache: dict[tuple[str, int], list[dict[str, Any]]] = {}
        logger.info(f"Loaded Dense FAISS retriever with {self.retriever.document_count} documents.")

    def retrieve(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Retrieve top-k documents by cosine similarity (all-MiniLM-L6-v2 embeddings)."""
        cache_key = (query, k)
        if cache_key in self._results_cache:
            return self._results_cache[cache_key]

        from preprocessing.text_cleaning import clean_text
        cleaned_query = clean_text(query)
        if cleaned_query not in self._embedding_cache:
            self._embedding_cache[cleaned_query] = self.retriever.embedder.encode(cleaned_query)
        query_embedding = self._embedding_cache[cleaned_query]

        hits = self.retriever.index.search(query_embedding, int(k))
        results = []
        for hit in hits:
            doc = self.retriever._documents[hit.vector_id]
            doc_id = extract_doc_id(doc.source)
            results.append({
                "doc_id": doc_id,
                "score": float(hit.similarity_score),
                "title": doc.title,
                "content": doc.content,
                "source": doc.source,
            })
        self._results_cache[cache_key] = results
        return results


class HybridRetriever:
    """Unified retrieval engine providing BM25, Dense, Hybrid, and Hybrid+RRF."""

    def __init__(
        self,
        corpus_path: Path | str = PROJECT_ROOT / "data" / "scifact" / "corpus.jsonl",
        cache_dir: Path | str = PROJECT_ROOT / "data" / "scifact" / "cache",
    ) -> None:
        self.corpus_path = Path(corpus_path)
        self.cache_dir = Path(cache_dir)
        self.bm25_retriever = BM25Retriever(
            corpus_path=self.corpus_path,
            cache_path=self.cache_dir / "bm25_model.pkl",
        )
        self.dense_retriever = DenseRetrieverWrapper(cache_dir=self.cache_dir)
        self._hybrid_cache: dict[tuple[str, int, float], list[dict[str, Any]]] = {}
        self._rrf_cache: dict[tuple[str, int, int, int], list[dict[str, Any]]] = {}

    def retrieve_bm25(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Retrieve using BM25 sparse matching."""
        return self.bm25_retriever.retrieve(query, k=k)

    def retrieve_dense(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """Retrieve using dense embedding similarity."""
        return self.dense_retriever.retrieve(query, k=k)

    def retrieve_hybrid(self, query: str, k: int = 10, alpha: float = 0.5) -> list[dict[str, Any]]:
        """
        Hybrid retrieval combining normalized BM25 and Dense scores.
        Score = alpha * norm_dense + (1 - alpha) * norm_bm25
        """
        cache_key = (query, k, alpha)
        if cache_key in self._hybrid_cache:
            return self._hybrid_cache[cache_key]

        candidate_pool = max(k * 4, 40)
        bm25_hits = self.bm25_retriever.retrieve(query, k=candidate_pool)
        dense_hits = self.dense_retriever.retrieve(query, k=candidate_pool)

        # Build candidate map
        doc_map: dict[str, dict[str, Any]] = {}
        bm25_scores: dict[str, float] = {}
        dense_scores: dict[str, float] = {}

        for h in bm25_hits:
            did = h["doc_id"]
            doc_map[did] = h
            bm25_scores[did] = h["score"]

        for h in dense_hits:
            did = h["doc_id"]
            doc_map[did] = h
            dense_scores[did] = h["score"]

        # Min-Max normalize BM25 scores
        if bm25_scores:
            b_vals = list(bm25_scores.values())
            b_min, b_max = min(b_vals), max(b_vals)
            b_range = b_max - b_min if b_max > b_min else 1.0
            norm_bm25 = {did: (s - b_min) / b_range for did, s in bm25_scores.items()}
        else:
            norm_bm25 = {}

        # Min-Max normalize Dense scores
        if dense_scores:
            d_vals = list(dense_scores.values())
            d_min, d_max = min(d_vals), max(d_vals)
            d_range = d_max - d_min if d_max > d_min else 1.0
            norm_dense = {did: (s - d_min) / d_range for did, s in dense_scores.items()}
        else:
            norm_dense = {}

        combined: list[tuple[str, float]] = []
        for did in doc_map:
            s_b = norm_bm25.get(did, 0.0)
            s_d = norm_dense.get(did, 0.0)
            final_score = alpha * s_d + (1.0 - alpha) * s_b
            combined.append((did, final_score))

        combined.sort(key=lambda x: x[1], reverse=True)

        results = []
        for did, score in combined[:k]:
            item = dict(doc_map[did])
            item["score"] = float(score)
            results.append(item)

        self._hybrid_cache[cache_key] = results
        return results

    def retrieve_hybrid_rrf(
        self,
        query: str,
        k: int = 10,
        k_rrf: int = 60,
        candidate_pool: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Hybrid retrieval with Reciprocal Rank Fusion (RRF).
        RRF_Score(d) = sum_{m in {bm25, dense}} 1.0 / (k_rrf + rank_m(d))
        where rank is 1-based.
        """
        cache_key = (query, k, k_rrf, candidate_pool)
        if cache_key in self._rrf_cache:
            return self._rrf_cache[cache_key]

        bm25_hits = self.bm25_retriever.retrieve(query, k=candidate_pool)
        dense_hits = self.dense_retriever.retrieve(query, k=candidate_pool)

        rrf_scores: dict[str, float] = {}
        doc_map: dict[str, dict[str, Any]] = {}

        for rank, h in enumerate(bm25_hits, start=1):
            did = h["doc_id"]
            doc_map[did] = h
            rrf_scores[did] = rrf_scores.get(did, 0.0) + (1.0 / (k_rrf + rank))

        for rank, h in enumerate(dense_hits, start=1):
            did = h["doc_id"]
            doc_map[did] = h
            rrf_scores[did] = rrf_scores.get(did, 0.0) + (1.0 / (k_rrf + rank))

        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for did, score in sorted_docs[:k]:
            item = dict(doc_map[did])
            item["score"] = float(score)
            item["rrf_score"] = float(score)
            results.append(item)

        self._rrf_cache[cache_key] = results
        return results
