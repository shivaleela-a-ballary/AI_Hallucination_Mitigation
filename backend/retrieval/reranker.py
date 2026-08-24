"""
Evidence Reranker.
Scores and ranks multi-source candidate documents against a claim/query.
Uses dense semantic similarity with exact keyword coverage and source authority weighting.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

import numpy as np

from preprocessing.embeddings import SentenceTransformerEmbedder
from .providers.base import Document, RetrievedDocument

logger = logging.getLogger(__name__)


def extract_keywords(text: str) -> set[str]:
    """Extract significant lowercase keywords (>= 3 chars) ignoring common stopwords."""
    words = re.findall(r"[a-zA-Z0-9_-]{3,}", text.lower())
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "are", "was", "were",
        "has", "have", "had", "can", "could", "should", "will", "would", "about",
        "been", "into", "more", "most", "other", "some", "such", "than", "them",
        "then", "there", "these", "they", "which", "what", "when", "where", "who",
    }
    return {w for w in words if w not in stopwords}


class EvidenceReranker:
    """
    Reranks candidate evidence passages against a query using hybrid scoring:
    Dense embedding similarity (70%) + Keyword overlap (20%) + Source authority (10%).
    """
    def __init__(
        self,
        embedder: SentenceTransformerEmbedder | None = None,
        min_similarity: float = 0.18,
    ) -> None:
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.min_similarity = min_similarity

    def rerank(
        self,
        query: str,
        candidates: Sequence[Document],
        top_k: int = 5,
        min_similarity: float | None = None,
    ) -> list[RetrievedDocument]:
        """
        Score and return the top_k most relevant candidate documents.
        """
        if not candidates or not query.strip():
            return []

        threshold = self.min_similarity if min_similarity is None else min_similarity
        query_clean = query.strip()
        query_embedding = self.embedder.encode(query_clean)
        query_words = extract_keywords(query_clean)

        # Batch encode candidate contents
        contents = [f"{doc.title}. {doc.content}" for doc in candidates]
        doc_embeddings = self.embedder.encode_many(contents)

        scored_results: list[RetrievedDocument] = []

        for idx, doc in enumerate(candidates):
            doc_vec = doc_embeddings[idx]
            # 1. Cosine similarity
            norm_q = np.linalg.norm(query_embedding)
            norm_d = np.linalg.norm(doc_vec)
            if norm_q > 0 and norm_d > 0:
                dense_sim = float(np.dot(query_embedding, doc_vec) / (norm_q * norm_d))
            else:
                dense_sim = 0.0

            dense_sim = max(0.0, min(1.0, (dense_sim + 1.0) / 2.0 if dense_sim < 0 else dense_sim))

            # 2. Keyword overlap
            doc_words = extract_keywords(f"{doc.title} {doc.content}")
            if query_words:
                kw_overlap = len(query_words & doc_words) / len(query_words)
            else:
                kw_overlap = 0.0

            # 3. Source authority boost
            source_weight = 1.0
            if doc.source_type in {"peer_reviewed_journal", "scientific_corpus"}:
                source_weight = 1.05
            elif doc.source_type == "encyclopedia":
                source_weight = 1.0

            # Combined calibrated similarity score
            final_score = round(
                min(1.0, (0.75 * dense_sim + 0.25 * kw_overlap) * source_weight),
                4,
            )

            if final_score >= threshold:
                scored_results.append(
                    RetrievedDocument(
                        title=doc.title,
                        content=doc.content,
                        source=doc.source,
                        similarity_score=final_score,
                        url=doc.url,
                        doi=doc.doi,
                        pmid=doc.pmid,
                        publication_date=doc.publication_date,
                        authors=doc.authors,
                        source_type=doc.source_type,
                    )
                )

        # Sort descending by final calibrated similarity score
        ranked = sorted(scored_results, key=lambda x: x.similarity_score, reverse=True)
        return ranked[:top_k]
