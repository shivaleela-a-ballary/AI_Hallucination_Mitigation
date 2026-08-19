"""Document retrieval over an in-memory FAISS CPU index."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from numbers import Integral
from typing import Sequence

from preprocessing.embeddings import SentenceTransformerEmbedder
from preprocessing.text_cleaning import clean_text

from .faiss_index import FaissVectorIndex

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Document:
    """A document supplied to the retriever before it is indexed."""

    title: str
    content: str
    source: str
    url: str | None = None


@dataclass(frozen=True)
class RetrievedDocument:
    """A document returned by semantic search with cosine similarity."""

    title: str
    content: str
    source: str
    similarity_score: float
    url: str | None = None


class DocumentRetriever:
    """Index documents and retrieve only semantically relevant results."""

    def __init__(
        self,
        embedder: SentenceTransformerEmbedder | None = None,
        min_similarity: float = 0.35,
    ) -> None:
        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between 0 and 1.")
        self.embedder = embedder or SentenceTransformerEmbedder()
        self.min_similarity = min_similarity
        self.index = FaissVectorIndex(self.embedder.dimension)
        self._documents: list[Document] = []

    @property
    def document_count(self) -> int:
        """Return the number of indexed documents."""
        return len(self._documents)

    def add_documents(self, documents: Sequence[Document]) -> None:
        """Embed and add documents to the in-memory index."""
        if not documents:
            raise ValueError("At least one document is required for indexing.")

        validated_documents = [self._validate_document(document) for document in documents]
        embeddings = self.embedder.encode_many(
            [document.content for document in validated_documents]
        )
        self.index.add(embeddings)
        self._documents.extend(validated_documents)
        logger.info("Indexed %d documents; index now contains %d vectors.", len(documents), self.index.count)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        min_similarity: float | None = None,
    ) -> list[RetrievedDocument]:
        """Return relevant documents, excluding nearest-neighbor noise."""
        if not isinstance(k, Integral) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer.")

        cleaned_query = clean_text(query)
        if self.index.count == 0:
            logger.info("No documents are indexed; retrieval returned no results.")
            return []

        query_embedding = self.embedder.encode(cleaned_query)
        hits = self.index.search(query_embedding, int(k))
        threshold = self.min_similarity if min_similarity is None else min_similarity
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("min_similarity must be between 0 and 1.")

        return [
            RetrievedDocument(
                title=self._documents[hit.vector_id].title,
                content=self._documents[hit.vector_id].content,
                source=self._documents[hit.vector_id].source,
                similarity_score=hit.similarity_score,
                url=self._documents[hit.vector_id].url,
            )
            for hit in hits
            if hit.similarity_score >= threshold
        ]

    @staticmethod
    def _validate_document(document: Document) -> Document:
        if not isinstance(document, Document):
            raise TypeError("Documents must be Document instances.")

        return Document(
            title=clean_text(document.title),
            content=clean_text(document.content),
            source=clean_text(document.source),
            url=document.url.strip() if document.url else None,
        )
