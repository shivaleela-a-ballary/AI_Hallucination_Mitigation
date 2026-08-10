"""Response-formatting helpers."""

from __future__ import annotations

from retrieval.retrieve import RetrievedDocument


def source_payload(document: RetrievedDocument) -> dict[str, object]:
    """Convert a retrieval result to the public API source representation."""
    return {
        "title": document.title,
        "content": document.content,
        "source": document.source,
        "similarity_score": document.similarity_score,
    }
