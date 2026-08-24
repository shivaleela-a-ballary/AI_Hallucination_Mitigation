"""
Multi-Source Evidence Retrieval Coordinator.
Executes concurrent retrieval across SciFact, PubMed, and Wikipedia providers.
Ensures zero-crash resilience if external providers fail or time out.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Sequence

from api.config import settings
from .base import Document, EvidenceProvider
from .pubmed_provider import PubMedProvider
from .scifact_provider import SciFactProvider
from .uploads_provider import UserUploadsProvider
from .wikipedia_provider import WikipediaProvider

logger = logging.getLogger(__name__)


class MultiSourceEvidenceManager:
    """
    Coordinates multi-source candidate evidence harvesting from all active providers.
    """
    def __init__(
        self,
        providers: Sequence[EvidenceProvider] | None = None,
        enable_pubmed: bool | None = None,
        enable_scifact: bool | None = None,
        enable_wikipedia: bool | None = None,
        enable_uploads: bool | None = True,
    ) -> None:
        if providers is not None:
            self.providers: list[EvidenceProvider] = list(providers)
        else:
            self.providers = []
            # User Uploads
            if enable_uploads is not False:
                self.providers.append(UserUploadsProvider())

            # SciFact (Local)
            if enable_scifact is not False:
                self.providers.append(SciFactProvider())

            # PubMed (NCBI)
            is_pubmed_enabled = getattr(settings, "PUBMED_ENABLED", True) if enable_pubmed is None else enable_pubmed
            if is_pubmed_enabled:
                self.providers.append(PubMedProvider())

            # Wikipedia
            is_wiki_enabled = getattr(settings, "WIKIPEDIA_ENABLED", True) if enable_wikipedia is None else enable_wikipedia
            if is_wiki_enabled:
                self.providers.append(WikipediaProvider())

    def get_provider(self, name: str) -> EvidenceProvider | None:
        """Find an active provider by name."""
        name_lower = name.strip().lower()
        for p in self.providers:
            if p.name.lower() == name_lower:
                return p
        return None

    def retrieve_candidates(
        self,
        query: str,
        top_k_per_source: int = 10,
    ) -> list[Document]:
        """
        Query all active providers concurrently and return a raw candidate evidence pool.
        """
        if not query or not query.strip():
            return []

        all_candidates: list[Document] = []

        # Run provider searches concurrently with ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.providers) or 1) as executor:
            future_to_provider = {
                executor.submit(p.search, query, top_k_per_source): p
                for p in self.providers
            }
            for future in concurrent.futures.as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    docs = future.result()
                    logger.info(f"[{provider.name}] Retrieved {len(docs)} candidate documents.")
                    all_candidates.extend(docs)
                except Exception as exc:
                    logger.warning(f"[{provider.name}] Retrieval encountered an error: {exc}")

        return all_candidates
