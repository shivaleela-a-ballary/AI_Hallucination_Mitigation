"""Utilities for normalising user-provided query text."""

from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    """Return a normalised, non-empty piece of text.

    Unicode is normalised with NFKC and consecutive whitespace (including
    newlines and tabs) is collapsed to one ordinary space.  Query wording and
    punctuation are otherwise preserved for downstream retrieval.

    Raises:
        TypeError: If ``text`` is not a string.
        ValueError: If the text is empty after normalisation.
    """
    if not isinstance(text, str):
        raise TypeError("Text to clean must be a string.")

    normalised = unicodedata.normalize("NFKC", text)
    cleaned = re.sub(r"\s+", " ", normalised).strip()

    if not cleaned:
        raise ValueError("Text to clean must not be empty or whitespace only.")

    return cleaned
