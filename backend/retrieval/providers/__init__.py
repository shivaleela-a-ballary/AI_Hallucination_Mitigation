"""
Evidence providers package.
Provides unified interfaces for SciFact, PubMed, Wikipedia, and multi-source coordination.
"""

from .base import Document, RetrievedDocument, EvidenceProvider
from .scifact_provider import SciFactProvider
from .pubmed_provider import PubMedProvider
from .semantic_scholar_provider import SemanticScholarProvider
from .arxiv_provider import ArxivProvider
from .crossref_provider import CrossrefProvider
from .wikipedia_provider import WikipediaProvider
from .uploads_provider import UserUploadsProvider
from .manager import MultiSourceEvidenceManager

__all__ = [
    "Document",
    "RetrievedDocument",
    "EvidenceProvider",
    "SciFactProvider",
    "PubMedProvider",
    "SemanticScholarProvider",
    "ArxivProvider",
    "CrossrefProvider",
    "WikipediaProvider",
    "UserUploadsProvider",
    "MultiSourceEvidenceManager",
]
