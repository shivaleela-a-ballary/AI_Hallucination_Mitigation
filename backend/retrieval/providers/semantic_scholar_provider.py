"""
Semantic Scholar Evidence Provider.
Queries the Semantic Scholar Academic Graph API for scientific literature, DOIs, PMIDs, and abstracts.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Sequence

from api.config import settings
from .base import Document, EvidenceProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SemanticScholarConfig:
    search_url: str = "https://api.semanticscholar.org/graph/v1/paper/search"
    timeout_seconds: float = 8.0
    api_key: str = ""
    tool_name: str = "AIHallucinationMitigation"


class SemanticScholarProvider(EvidenceProvider):
    """
    Multidisciplinary scientific literature provider using the Semantic Scholar Academic Graph API.
    """
    def __init__(self, config: SemanticScholarConfig | None = None) -> None:
        self.config = config or SemanticScholarConfig(
            timeout_seconds=getattr(settings, "SEMANTIC_SCHOLAR_TIMEOUT_SECONDS", 8.0),
            api_key=getattr(settings, "SEMANTIC_SCHOLAR_API_KEY", ""),
        )

    @property
    def name(self) -> str:
        return "Semantic Scholar"

    def _http_get(self, url: str, params: dict[str, str | int]) -> bytes | None:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        headers = {
            "User-Agent": f"AIHallucinationMitigation/2.0 (https://github.com/shivaleela-a-ballary/AI_Hallucination_Mitigation)",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key

        req = urllib.request.Request(full_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    return response.read()
                logger.warning(f"Semantic Scholar API returned HTTP status {response.status}")
                return None
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                logger.warning("Semantic Scholar API rate limit exceeded (HTTP 429).")
            else:
                logger.warning(f"Semantic Scholar HTTP request failed ({exc.code}): {exc.reason}")
            return None
        except Exception as exc:
            logger.warning(f"Semantic Scholar API request failed ({type(exc).__name__}): {exc}")
            return None

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Query Semantic Scholar Graph API and return standardized candidate documents."""
        clean_query = re.sub(r"[^\w\s-]", " ", query).strip()
        if not clean_query:
            return []

        tokens = [t for t in clean_query.split() if len(t) > 2]
        search_term = " ".join(tokens[:12]) if len(tokens) > 12 else clean_query

        params = {
            "query": search_term,
            "limit": top_k,
            "fields": "paperId,title,abstract,authors,year,url,externalIds,venue,publicationDate",
        }

        raw_data = self._http_get(self.config.search_url, params)
        if not raw_data:
            return []

        documents: list[Document] = []
        try:
            payload = json.loads(raw_data.decode("utf-8"))
            papers = payload.get("data", []) or []

            for paper in papers:
                try:
                    title = (paper.get("title") or "").strip()
                    abstract = (paper.get("abstract") or "").strip()

                    # Fallback to title + venue if abstract is empty
                    if not abstract and title:
                        venue = paper.get("venue") or ""
                        abstract = f"{title}. Published in {venue}." if venue else title

                    if not title or not abstract:
                        continue

                    # External IDs
                    external_ids = paper.get("externalIds") or {}
                    doi = external_ids.get("DOI")
                    pmid = external_ids.get("PubMed") or external_ids.get("PubMedCentral")

                    # URL
                    url = paper.get("url")
                    if not url:
                        if doi:
                            url = f"https://doi.org/{doi}"
                        elif paper.get("paperId"):
                            url = f"https://www.semanticscholar.org/paper/{paper['paperId']}"

                    # Authors
                    authors_data = paper.get("authors") or []
                    authors = [a.get("name").strip() for a in authors_data if a.get("name")][:5]

                    # Publication date
                    year = paper.get("year")
                    pub_date = str(year) if year else paper.get("publicationDate")

                    documents.append(
                        Document(
                            title=title,
                            content=abstract,
                            source="Semantic Scholar",
                            url=url,
                            doi=doi,
                            pmid=pmid,
                            publication_date=pub_date,
                            authors=authors,
                            source_type="peer_reviewed_journal",
                        )
                    )
                except Exception as paper_err:
                    logger.debug(f"Error parsing Semantic Scholar paper entry: {paper_err}")
                    continue

        except Exception as exc:
            logger.warning(f"Failed to parse Semantic Scholar response: {exc}")
            return []

        return documents
