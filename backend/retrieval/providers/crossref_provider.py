"""
Crossref Evidence Provider.
Queries the Crossref REST API for peer-reviewed journal articles, DOIs, publisher abstracts, and citations.
"""

from __future__ import annotations

import html
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
class CrossrefConfig:
    search_url: str = "https://api.crossref.org/works"
    timeout_seconds: float = 8.0
    email: str = "researcher@example.com"
    tool_name: str = "AIHallucinationMitigation"


def clean_jats_abstract(text: str) -> str:
    """Remove JATS XML / HTML tags and unescape entities from Crossref abstracts."""
    if not text:
        return ""
    # Strip XML/HTML tags
    stripped = re.sub(r"<[^>]+>", " ", text)
    # Unescape HTML entities (&lt;, &gt;, &amp;, etc.)
    unescaped = html.unescape(stripped)
    # Collapse multiple whitespaces
    return " ".join(unescaped.split()).strip()


class CrossrefProvider(EvidenceProvider):
    """
    Peer-reviewed scholarly literature provider using the Crossref REST API.
    """
    def __init__(self, config: CrossrefConfig | None = None) -> None:
        self.config = config or CrossrefConfig(
            timeout_seconds=getattr(settings, "CROSSREF_TIMEOUT_SECONDS", 8.0),
            email=getattr(settings, "CROSSREF_EMAIL", "researcher@example.com"),
        )

    @property
    def name(self) -> str:
        return "Crossref"

    def _http_get(self, url: str, params: dict[str, str | int]) -> bytes | None:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        headers = {
            "User-Agent": f"AIHallucinationMitigation/2.0 (mailto:{self.config.email})",
            "Accept": "application/json",
        }
        req = urllib.request.Request(full_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    return response.read()
                logger.warning(f"Crossref API returned HTTP status {response.status}")
                return None
        except Exception as exc:
            logger.warning(f"Crossref API request failed ({type(exc).__name__}): {exc}")
            return None

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Query Crossref REST API and return standardized candidate documents."""
        clean_query = re.sub(r"[^\w\s-]", " ", query).strip()
        if not clean_query:
            return []

        tokens = [t for t in clean_query.split() if len(t) > 2]
        search_term = " ".join(tokens[:12]) if len(tokens) > 12 else clean_query

        params = {
            "query": search_term,
            "rows": top_k,
            "sort": "relevance",
        }

        raw_data = self._http_get(self.config.search_url, params)
        if not raw_data:
            return []

        documents: list[Document] = []
        try:
            payload = json.loads(raw_data.decode("utf-8"))
            items = payload.get("message", {}).get("items", []) or []

            for item in items:
                try:
                    # Title (Crossref returns title as a list of strings)
                    title_list = item.get("title", [])
                    title = title_list[0].strip() if title_list and isinstance(title_list, list) else str(item.get("title") or "").strip()

                    if not title:
                        continue

                    # Abstract
                    raw_abstract = item.get("abstract") or ""
                    abstract = clean_jats_abstract(raw_abstract)

                    # Journal / Container Title
                    containers = item.get("container-title", [])
                    journal = containers[0].strip() if containers and isinstance(containers, list) else ""

                    if not abstract:
                        subtitles = item.get("subtitle", [])
                        subtitle = subtitles[0].strip() if subtitles and isinstance(subtitles, list) else ""
                        if subtitle:
                            abstract = f"{title}: {subtitle}." + (f" Published in {journal}." if journal else "")
                        elif journal:
                            abstract = f"{title}. Published in {journal}."
                        else:
                            abstract = title

                    if not abstract:
                        continue

                    # DOI & URL
                    doi = item.get("DOI")
                    url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)

                    # Authors
                    authors: list[str] = []
                    for author in item.get("author", []):
                        given = author.get("given", "").strip()
                        family = author.get("family", "").strip()
                        full_name = f"{given} {family}".strip() if given else family
                        if full_name:
                            authors.append(full_name)

                    # Publication Date (Year)
                    pub_date = None
                    for date_field in ["published-print", "published-online", "created"]:
                        date_parts = item.get(date_field, {}).get("date-parts", [])
                        if date_parts and len(date_parts[0]) > 0 and date_parts[0][0]:
                            pub_date = str(date_parts[0][0])
                            break

                    documents.append(
                        Document(
                            title=title,
                            content=abstract,
                            source="Crossref",
                            url=url,
                            doi=doi,
                            pmid=None,
                            publication_date=pub_date,
                            authors=authors[:5],
                            source_type="peer_reviewed_journal",
                        )
                    )
                except Exception as item_err:
                    logger.debug(f"Error parsing Crossref item: {item_err}")
                    continue

        except Exception as exc:
            logger.warning(f"Failed to parse Crossref response: {exc}")
            return []

        return documents
