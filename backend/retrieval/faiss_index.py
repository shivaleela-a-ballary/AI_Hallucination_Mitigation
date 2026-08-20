"""FAISS CPU vector index backed by normalised inner-product similarity."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from pathlib import Path

import faiss
import numpy as np


@dataclass(frozen=True)
class SearchHit:
    """One vector-search result returned by :class:`FaissVectorIndex`."""

    vector_id: int
    similarity_score: float


class FaissVectorIndex:
    """In-memory FAISS CPU index using cosine similarity.

    Vectors are L2-normalised before storage and queries are normalised before
    search.  Inner product is therefore equivalent to cosine similarity.
    """

    def __init__(self, dimension: int) -> None:
        if not isinstance(dimension, Integral) or isinstance(dimension, bool) or dimension <= 0:
            raise ValueError("Embedding dimension must be a positive integer.")

        self.dimension = int(dimension)
        self.index = faiss.IndexFlatIP(self.dimension)

    @property
    def count(self) -> int:
        """Return the number of vectors stored in the index."""
        return int(self.index.ntotal)

    def save(self, file_path: str | Path) -> None:
        """Save the FAISS index to disk."""
        faiss.write_index(self.index, str(file_path))

    @classmethod
    def load(cls, file_path: str | Path) -> FaissVectorIndex:
        """Load a FAISS index from disk."""
        idx = faiss.read_index(str(file_path))
        instance = cls(idx.d)
        instance.index = idx
        return instance

    def add(self, embeddings: np.ndarray) -> None:
        """Validate, normalise, and add a batch of embeddings to the index."""
        vectors = self._validate_matrix(embeddings)
        normalised_vectors = np.ascontiguousarray(vectors.copy(), dtype=np.float32)
        faiss.normalize_L2(normalised_vectors)
        self.index.add(normalised_vectors)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[SearchHit]:
        """Return up to ``k`` nearest vectors, or an empty list for an empty index."""
        if not isinstance(k, Integral) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer.")
        if self.count == 0:
            return []

        query = self._validate_vector(query_embedding)
        normalised_query = np.ascontiguousarray(query.reshape(1, -1).copy(), dtype=np.float32)
        faiss.normalize_L2(normalised_query)

        result_count = min(int(k), self.count)
        scores, ids = self.index.search(normalised_query, result_count)
        return [
            SearchHit(vector_id=int(vector_id), similarity_score=float(score))
            for score, vector_id in zip(scores[0], ids[0])
            if vector_id >= 0
        ]

    def _validate_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        vectors = np.asarray(embeddings, dtype=np.float32)
        if vectors.ndim != 2:
            raise ValueError("Embeddings must be a two-dimensional array.")
        if vectors.shape[0] == 0:
            raise ValueError("At least one embedding is required for indexing.")
        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {vectors.shape[1]} does not match index dimension "
                f"{self.dimension}."
            )
        if not np.isfinite(vectors).all():
            raise ValueError("Embeddings must contain only finite numeric values.")
        return vectors

    def _validate_vector(self, embedding: np.ndarray) -> np.ndarray:
        vector = np.asarray(embedding, dtype=np.float32)
        if vector.ndim != 1:
            raise ValueError("A query embedding must be a one-dimensional array.")
        if vector.shape[0] != self.dimension:
            raise ValueError(
                f"Query embedding dimension {vector.shape[0]} does not match index dimension "
                f"{self.dimension}."
            )
        if not np.isfinite(vector).all():
            raise ValueError("Query embedding must contain only finite numeric values.")
        return vector
