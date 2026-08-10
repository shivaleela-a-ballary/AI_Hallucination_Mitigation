"""Typed query preprocessing interface for the RAG pipeline."""

from __future__ import annotations

import logging

from .text_cleaning import clean_text

logger = logging.getLogger(__name__)


class QueryPreprocessor:
    """Normalise and validate a raw user query before retrieval."""

    def process(self, query: str) -> str:
        """Return a clean query suitable for embedding and retrieval.

        The original meaning and punctuation are intentionally preserved; this
        stage only performs safe normalisation.
        """
        try:
            processed_query = clean_text(query)
        except (TypeError, ValueError):
            logger.warning("Rejected an invalid query during preprocessing.")
            raise

        logger.debug(
            "Preprocessed query from %d to %d characters.",
            len(query),
            len(processed_query),
        )
        return processed_query


def preprocess_query(query: str) -> str:
    """Convenience function for preprocessing a single user query."""
    return QueryPreprocessor().process(query)
