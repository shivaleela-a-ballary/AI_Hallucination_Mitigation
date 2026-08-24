"""
Multi-source Evidence Deduplication.
Deduplicates candidate documents across SciFact, PubMed, Wikipedia, and other providers.
Uses prioritized matching: DOI -> PMID -> Normalized Title -> Text Overlap.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

from .providers.base import Document

logger = logging.getLogger(__name__)


def normalize_title(title: str) -> str:
    """Normalize article title for fuzzy comparison."""
    if not title:
        return ""
    # Lowercase, replace non-alphanumeric with space, collapse whitespace
    text = re.sub(r"[^\w\s]", " ", title.lower())
    words = [w for w in text.split() if w not in {"the", "a", "an", "of", "in", "on", "for", "and", "to", "with", "by", "is", "at"}]
    return " ".join(words)


def text_similarity_jaccard(text1: str, text2: str, sample_len: int = 250) -> float:
    """Compute character 4-gram Jaccard similarity on initial text passages."""
    s1 = text1[:sample_len].lower().strip()
    s2 = text2[:sample_len].lower().strip()
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    ngrams1 = {s1[i:i+4] for i in range(len(s1) - 3)}
    ngrams2 = {s2[i:i+4] for i in range(len(s2) - 3)}
    if not ngrams1 or not ngrams2:
        return 0.0
    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)
    return intersection / union if union > 0 else 0.0


class EvidenceDeduplicator:
    """
    Identifies and removes duplicate papers across heterogeneous data sources.
    """
    def __init__(self, text_similarity_threshold: float = 0.85) -> None:
        self.text_similarity_threshold = text_similarity_threshold

    def deduplicate(self, documents: Sequence[Document]) -> list[Document]:
        """
        Deduplicate candidate documents preserving order of highest quality source.
        """
        if not documents:
            return []

        seen_dois: set[str] = set()
        seen_pmids: set[str] = set()
        seen_titles: set[str] = set()
        unique_docs: list[Document] = []

        for doc in documents:
            # 1. Match on DOI
            if doc.doi:
                norm_doi = doc.doi.strip().lower()
                if norm_doi in seen_dois:
                    logger.debug(f"Dropped duplicate document by DOI: {norm_doi}")
                    continue

            # 2. Match on PMID
            if doc.pmid:
                norm_pmid = doc.pmid.strip()
                if norm_pmid in seen_pmids:
                    logger.debug(f"Dropped duplicate document by PMID: {norm_pmid}")
                    continue

            # 3. Match on Normalized Title
            norm_title = normalize_title(doc.title)
            if norm_title and len(norm_title) > 10:
                if norm_title in seen_titles:
                    logger.debug(f"Dropped duplicate document by Title: {doc.title}")
                    continue

            # 4. Match on Content Text Overlap against already accepted documents
            is_content_duplicate = False
            for existing in unique_docs:
                if text_similarity_jaccard(doc.content, existing.content) >= self.text_similarity_threshold:
                    logger.debug(f"Dropped duplicate document by Content similarity: {doc.title} matches {existing.title}")
                    is_content_duplicate = True
                    break

            if is_content_duplicate:
                continue

            # Register identifiers
            if doc.doi:
                seen_dois.add(doc.doi.strip().lower())
            if doc.pmid:
                seen_pmids.add(doc.pmid.strip())
            if norm_title and len(norm_title) > 10:
                seen_titles.add(norm_title)

            unique_docs.append(doc)

        logger.info(f"Deduplication: {len(documents)} raw candidates -> {len(unique_docs)} unique documents.")
        return unique_docs
