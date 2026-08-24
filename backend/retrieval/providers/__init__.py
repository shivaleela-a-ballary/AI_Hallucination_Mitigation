"""
Evidence providers package.
Provides unified interfaces for SciFact, PubMed, Wikipedia, and multi-source coordination.
"""

from .base import Document, RetrievedDocument, EvidenceProvider
from .scifact_provider import SciFactProvider
from .pubmed_provider import PubMedProvider
from .wikipedia_provider import WikipediaProvider
from .manager import MultiSourceEvidenceManager

__all__ = [
    "Document",
    "RetrievedDocument",
    "EvidenceProvider",
    "SciFactProvider",
    "PubMedProvider",
    "WikipediaProvider",
    "MultiSourceEvidenceManager",
]
