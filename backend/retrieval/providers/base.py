"""
Base abstraction and models for multi-source evidence providers.
Standardizes documents and metadata across SciFact, PubMed, Wikipedia, and future sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class Document:
    """
    Standard unified document representation across all evidence providers.
    """
    title: str
    content: str
    source: str
    url: str | None = None
    doi: str | None = None
    pmid: str | None = None
    publication_date: str | None = None
    authors: list[str] = field(default_factory=list)
    source_type: str = "scientific"  # "scientific", "peer_reviewed", "encyclopedia", "user_provided"


@dataclass(frozen=True)
class RetrievedDocument:
    """
    A document retrieved with relevance scoring and relationship metadata.
    """
    title: str
    content: str
    source: str
    similarity_score: float
    url: str | None = None
    doi: str | None = None
    pmid: str | None = None
    publication_date: str | None = None
    authors: list[str] = field(default_factory=list)
    source_type: str = "scientific"
    relationship: str = "UNCERTAIN"  # "SUPPORTS", "CONTRADICTS", "UNCERTAIN"
    stance_score: float = 0.0


class EvidenceProvider(ABC):
    """
    Abstract interface for all evidence sources.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name, e.g. 'SciFact', 'PubMed', 'Wikipedia'."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """
        Retrieve raw relevant candidate documents for a given query.
        Must handle errors internally and return an empty list upon failure.
        """
        pass
