"""
arXiv Evidence Provider.
Queries the arXiv API (Atom 1.0 XML) for preprint research in computer science,
quantitative biology, physics, mathematics, and machine learning.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Sequence

from api.config import settings
from .base import Document, EvidenceProvider

logger = logging.getLogger(__name__)

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


@dataclass(frozen=True)
class ArxivConfig:
    search_url: str = "https://export.arxiv.org/api/query"
    timeout_seconds: float = 8.0
    tool_name: str = "AIHallucinationMitigation"


class ArxivProvider(EvidenceProvider):
    """
    Open-access preprint literature provider using the arXiv API.
    """
    def __init__(self, config: ArxivConfig | None = None) -> None:
        self.config = config or ArxivConfig(
            timeout_seconds=getattr(settings, "ARXIV_TIMEOUT_SECONDS", 8.0),
        )

    @property
    def name(self) -> str:
        return "arXiv"

    def _http_get(self, url: str, params: dict[str, str | int]) -> bytes | None:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        headers = {
            "User-Agent": f"AIHallucinationMitigation/2.0 (arXiv integration; mailto:researcher@example.com)",
            "Accept": "application/atom+xml, application/xml, text/xml, */*",
        }
        req = urllib.request.Request(full_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    return response.read()
                logger.warning(f"arXiv API returned HTTP status {response.status}")
                return None
        except Exception as exc:
            logger.warning(f"arXiv API request failed ({type(exc).__name__}): {exc}")
            return None

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Query arXiv Atom feed and parse candidate documents."""
        clean_query = re.sub(r"[^\w\s-]", " ", query).strip()
        if not clean_query:
            return []

        tokens = [t for t in clean_query.split() if len(t) > 2]
        search_term = " ".join(tokens[:10]) if len(tokens) > 10 else clean_query

        params = {
            "search_query": f"all:{search_term}",
            "start": 0,
            "max_results": top_k,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        raw_xml = self._http_get(self.config.search_url, params)
        if not raw_xml:
            return []

        documents: list[Document] = []
        try:
            root = ET.fromstring(raw_xml)
            entries = root.findall(f"{ATOM_NS}entry")

            for entry in entries:
                try:
                    # Title
                    title_elem = entry.find(f"{ATOM_NS}title")
                    title = " ".join(title_elem.text.split()) if title_elem is not None and title_elem.text else ""

                    # Filter out arXiv error/empty entries
                    if not title or title.lower().startswith("error"):
                        continue

                    # Summary / Abstract
                    summary_elem = entry.find(f"{ATOM_NS}summary")
                    summary = " ".join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else ""

                    if not summary and title:
                        summary = title

                    if not summary:
                        continue

                    # URL / arXiv ID
                    id_elem = entry.find(f"{ATOM_NS}id")
                    raw_url = id_elem.text.strip() if id_elem is not None and id_elem.text else None
                    url = raw_url.replace("http://", "https://") if raw_url else None

                    # DOI if present
                    doi = None
                    doi_elem = entry.find(f"{ARXIV_NS}doi")
                    if doi_elem is not None and doi_elem.text:
                        doi = doi_elem.text.strip()

                    # Publication Date (Year)
                    pub_date = None
                    published_elem = entry.find(f"{ATOM_NS}published")
                    if published_elem is not None and published_elem.text:
                        pub_date = published_elem.text.strip()[:4]

                    # Authors
                    authors: list[str] = []
                    for author_elem in entry.findall(f"{ATOM_NS}author"):
                        name_elem = author_elem.find(f"{ATOM_NS}name")
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())

                    documents.append(
                        Document(
                            title=title,
                            content=summary,
                            source="arXiv",
                            url=url,
                            doi=doi,
                            pmid=None,
                            publication_date=pub_date,
                            authors=authors[:5],
                            source_type="preprint",
                        )
                    )
                except Exception as entry_err:
                    logger.debug(f"Error parsing arXiv entry: {entry_err}")
                    continue

        except Exception as exc:
            logger.warning(f"Failed to parse arXiv Atom XML response: {exc}")
            return []

        return documents
