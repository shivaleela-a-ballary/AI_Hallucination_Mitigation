"""
SciFact Evidence Provider.
Interfaces with the local FAISS index and SciFact corpus (~5,183 peer-reviewed documents).
"""

from __future__ import annotations

import logging
from pathlib import Path

from api.config import settings
from retrieval.scifact_documents import load_scifact_documents
from .base import Document, EvidenceProvider

logger = logging.getLogger(__name__)


class SciFactProvider(EvidenceProvider):
    """
    Evidence provider backed by the local SciFact scientific research dataset.
    """
    def __init__(self, corpus_path: Path | None = None, cache_dir: Path | None = None) -> None:
        self.corpus_path = corpus_path or settings.SCIFACT_CORPUS_PATH
        self.cache_dir = cache_dir or (settings.PROJECT_ROOT / "data" / "scifact" / "cache")
        self._retriever = None

    @property
    def name(self) -> str:
        return "SciFact"

    def _get_retriever(self):
        if self._retriever is None:
            from retrieval.retrieve import DocumentRetriever
            self._retriever = DocumentRetriever(min_similarity=settings.SCIFACT_MIN_SIMILARITY)
            if not self._retriever.load(self.cache_dir):
                if self.corpus_path.is_file():
                    documents = load_scifact_documents(self.corpus_path)
                    self._retriever.add_documents(documents)
                    try:
                        self._retriever.save(self.cache_dir)
                    except Exception as e:
                        logger.warning(f"Could not persist SciFact cache: {e}")
        return self._retriever

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Retrieve candidate documents from SciFact."""
        if not self.corpus_path.is_file() and not (self.cache_dir / "index.faiss").is_file():
            logger.warning("SciFact corpus is not available on disk.")
            return []

        try:
            retriever = self._get_retriever()
            retrieved = retriever.retrieve(query, k=top_k, min_similarity=settings.SCIFACT_MIN_SIMILARITY)
            return [
                Document(
                    title=item.title,
                    content=item.content,
                    source="SciFact",
                    url=item.url,
                    source_type="scientific_corpus",
                )
                for item in retrieved
            ]
        except Exception as exc:
            logger.error(f"SciFact retrieval error: {exc}")
            return []
