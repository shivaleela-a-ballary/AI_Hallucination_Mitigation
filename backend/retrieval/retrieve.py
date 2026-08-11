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


@dataclass(frozen=True)
class RetrievedDocument:
    """A document returned by semantic search with cosine similarity."""

    title: str
    content: str
    source: str
    similarity_score: float


# Development-only local knowledge base. It is explicitly not external evidence.
SAMPLE_DOCUMENTS: tuple[Document, ...] = (
    Document(
        title="Retrieval-augmented generation overview",
        content=(
            "Retrieval-augmented generation retrieves relevant documents and "
            "uses them as context when generating an answer."
        ),
        source="development-sample",
    ),
    Document(
        title="Evidence-based answering",
        content=(
            "Evidence-based answering should cite retrieved passages and express "
            "uncertainty when the available evidence is insufficient."
        ),
        source="development-sample",
    ),
    Document(
        title="FAISS similarity search",
        content=(
            "FAISS IndexFlatIP performs exact inner-product search. With L2-normalized "
            "embeddings, inner product is equivalent to cosine similarity."
        ),
        source="development-sample",
    ),
)

# Backwards-compatible test alias. Documents are never indexed automatically.
TEST_DOCUMENTS = SAMPLE_DOCUMENTS


class DocumentRetriever:
    """Index documents and retrieve them using the existing project embedder."""

    def __init__(self, embedder: SentenceTransformerEmbedder | None = None) -> None:
        self.embedder = embedder or SentenceTransformerEmbedder()
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

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedDocument]:
        """Return up to ``k`` documents ranked by cosine similarity."""
        if not isinstance(k, Integral) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer.")

        cleaned_query = clean_text(query)
        if self.index.count == 0:
            logger.info("No documents are indexed; retrieval returned no results.")
            return []

        query_embedding = self.embedder.encode(cleaned_query)
        hits = self.index.search(query_embedding, int(k))
        return [
            RetrievedDocument(
                title=self._documents[hit.vector_id].title,
                content=self._documents[hit.vector_id].content,
                source=self._documents[hit.vector_id].source,
                similarity_score=hit.similarity_score,
            )
            for hit in hits
        ]

    @staticmethod
    def _validate_document(document: Document) -> Document:
        if not isinstance(document, Document):
            raise TypeError("Documents must be Document instances.")

        return Document(
            title=clean_text(document.title),
            content=clean_text(document.content),
            source=clean_text(document.source),
        )
