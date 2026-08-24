"""
Wikipedia / MediaWiki General Knowledge Provider.
Fetches factual encyclopedia introductions for general knowledge queries.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass

from api.config import settings
from .base import Document, EvidenceProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WikipediaConfig:
    api_url: str = "https://en.wikipedia.org/w/api.php"
    timeout_seconds: float = 8.0
    user_agent: str = "AI-Hallucination-Mitigation/2.0 (knowledge-retrieval)"


class WikipediaProvider(EvidenceProvider):
    """
    General encyclopedia knowledge provider backed by MediaWiki.
    """
    def __init__(self, config: WikipediaConfig | None = None) -> None:
        self.config = config or WikipediaConfig(
            api_url=getattr(settings, "KNOWLEDGE_API_URL", "https://en.wikipedia.org/w/api.php"),
            timeout_seconds=getattr(settings, "KNOWLEDGE_TIMEOUT_SECONDS", 8.0),
        )

    @property
    def name(self) -> str:
        return "Wikipedia"

    def _request(self, params: dict[str, object]) -> dict | None:
        url = f"{self.config.api_url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.config.user_agent, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    return payload if isinstance(payload, dict) else None
                return None
        except Exception as exc:
            logger.warning(f"Wikipedia provider request error ({type(exc).__name__}): {exc}")
            return None

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """Search Wikipedia and retrieve page extracts."""
        search_payload = self._request({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": top_k,
            "format": "json",
            "formatversion": 2,
        })
        if not search_payload:
            return []

        search_items = search_payload.get("query", {}).get("search", [])
        page_ids = [str(item["pageid"]) for item in search_items if item.get("pageid")]
        if not page_ids:
            return []

        pages_payload = self._request({
            "action": "query",
            "pageids": "|".join(page_ids),
            "prop": "extracts|info",
            "exintro": 1,
            "explaintext": 1,
            "inprop": "url",
            "redirects": 1,
            "format": "json",
            "formatversion": 2,
        })
        if not pages_payload:
            return []

        documents: list[Document] = []
        for page in pages_payload.get("query", {}).get("pages", []):
            title = page.get("title")
            extract = (page.get("extract") or "").strip()
            url = page.get("fullurl")
            if title and extract:
                documents.append(
                    Document(
                        title=title,
                        content=extract,
                        source="Wikipedia",
                        url=url,
                        source_type="encyclopedia",
                    )
                )
        return documents
