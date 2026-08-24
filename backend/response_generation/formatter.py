"""Response-formatting helpers."""

from __future__ import annotations

from typing import Any
from retrieval.providers.base import RetrievedDocument


def source_payload(document: Any) -> dict[str, object]:
    """Convert a retrieval result to the public API source representation."""
    return {
        "title": getattr(document, "title", ""),
        "content": getattr(document, "content", ""),
        "source": getattr(document, "source", "Unknown"),
        "similarity_score": round(float(getattr(document, "similarity_score", 0.0)), 4),
        "url": getattr(document, "url", None),
        "doi": getattr(document, "doi", None),
        "pmid": getattr(document, "pmid", None),
        "authors": getattr(document, "authors", []) or [],
        "publication_date": getattr(document, "publication_date", None),
        "source_type": getattr(document, "source_type", "scientific"),
        "relationship": getattr(document, "relationship", "UNCERTAIN"),
        "stance_score": round(float(getattr(document, "stance_score", 0.0)), 4),
    }
