"""Sentence-transformer embeddings for processed user queries."""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from api.config import settings
from .text_cleaning import clean_text

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    """Encode non-empty text using the configured sentence-transformer model."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.MODEL_NAME
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as exc:
            logger.exception("Unable to load embedding model '%s'.", self.model_name)
            raise RuntimeError(
                f"Unable to load sentence-transformer model '{self.model_name}'."
            ) from exc

        if hasattr(self.model, "get_embedding_dimension"):
            self.dimension = self.model.get_embedding_dimension()
        else:
            self.dimension = self.model.get_sentence_embedding_dimension()
        if not self.dimension:
            raise RuntimeError(
                f"Embedding model '{self.model_name}' did not report an embedding dimension."
            )
        logger.info(
            "Loaded embedding model '%s' with dimension %d.",
            self.model_name,
            self.dimension,
        )

    def encode(self, text: str) -> np.ndarray:
        """Return one normalised float32 embedding for ``text``."""
        cleaned_text = clean_text(text)
        try:
            embedding = self.model.encode(
                cleaned_text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        except Exception as exc:
            logger.exception("Failed to encode query text.")
            raise RuntimeError("Failed to generate the query embedding.") from exc

        vector = np.asarray(embedding, dtype=np.float32)
        if vector.ndim != 1 or vector.shape[0] != self.dimension:
            raise RuntimeError(
                "Embedding model returned an unexpected vector shape: "
                f"{vector.shape}; expected ({self.dimension},)."
            )
        return vector

    def encode_many(self, texts: Sequence[str], batch_size: int = 128) -> np.ndarray:
        """Return one normalised float32 embedding per supplied text."""
        if not texts:
            raise ValueError("At least one text is required to generate embeddings.")

        cleaned_texts = [clean_text(text) for text in texts]
        try:
            embeddings = self.model.encode(
                cleaned_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        except Exception as exc:
            logger.exception("Failed to encode %d texts.", len(cleaned_texts))
            raise RuntimeError("Failed to generate text embeddings.") from exc

        matrix = np.asarray(embeddings, dtype=np.float32)
        expected_shape = (len(cleaned_texts), self.dimension)
        if matrix.shape != expected_shape:
            raise RuntimeError(
                "Embedding model returned an unexpected matrix shape: "
                f"{matrix.shape}; expected {expected_shape}."
            )
        return matrix
