"""
Evidence provider for User Uploaded Documents and Custom Ingested Literature.
"""

from __future__ import annotations

import logging
from typing import Optional

from api.db.mongodb import db_manager
from preprocessing.embeddings import SentenceTransformerEmbedder
from .base import Document, EvidenceProvider

logger = logging.getLogger(__name__)


class UserUploadsProvider(EvidenceProvider):
    """
    Retrieves evidence from user-uploaded and custom-ingested documents.
    """

    def __init__(self, embedder: Optional[SentenceTransformerEmbedder] = None) -> None:
        self._embedder = embedder

    @property
    def embedder(self) -> SentenceTransformerEmbedder:
        if self._embedder is None:
            self._embedder = SentenceTransformerEmbedder()
        return self._embedder

    @property
    def name(self) -> str:
        return "User Uploads"

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Search all uploaded documents and passages."""
        clean_query = query.strip()
        if not clean_query:
            return []

        passages = db_manager.get_all_uploaded_passages()
        if not passages:
            return []

        try:
            query_emb = self.embedder.encode(clean_query)
            texts = [p["content"] for p in passages]
            doc_embs = self.embedder.encode_many(texts)

            # Compute cosine similarities
            scores = doc_embs @ query_emb
            
            # Pair and sort
            scored_passages = []
            for score, p in zip(scores, passages):
                if float(score) >= 0.20:  # Minimum relevance threshold
                    scored_passages.append((float(score), p))

            scored_passages.sort(key=lambda x: x[0], reverse=True)

            results: list[Document] = []
            for score, p in scored_passages[:top_k]:
                results.append(Document(
                    title=p.get("title", "Uploaded Evidence"),
                    content=p["content"],
                    source=p.get("source", "User Upload"),
                    source_type="user_upload",
                ))

            return results
        except Exception as exc:
            logger.warning("Error searching uploaded documents: %s", exc)
            return []
