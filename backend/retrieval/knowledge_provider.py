"""Real external general-knowledge retrieval through MediaWiki."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from api.config import settings
from .retrieve import Document, DocumentRetriever, RetrievedDocument


class KnowledgeSourceUnavailable(RuntimeError):
    """Raised when the configured knowledge provider cannot be reached."""


@dataclass(frozen=True)
class WikipediaProvider:
    api_url: str
    timeout_seconds: float
    top_k: int

    def search(self, query: str) -> list[Document]:
        search_payload = self._request({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": self.top_k,
            "format": "json",
            "formatversion": 2,
        })
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
        documents: list[Document] = []
        for page in pages_payload.get("query", {}).get("pages", []):
            title = page.get("title")
            extract = (page.get("extract") or "").strip()
            url = page.get("fullurl")
            if title and extract and url:
                documents.append(Document(title=title, content=extract, source="Wikipedia", url=url))
        return documents

    def _request(self, params: dict[str, object]) -> dict:
        request = Request(
            f"{self.api_url}?{urlencode(params)}",
            headers={"User-Agent": "AI-Hallucination-Mitigation/1.0 (knowledge retrieval)"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise KnowledgeSourceUnavailable("The configured knowledge source is unavailable.") from exc
        if not isinstance(payload, dict):
            raise KnowledgeSourceUnavailable("The knowledge source returned an invalid response.")
        return payload


class GeneralKnowledgeRetriever:
    """Fetch real knowledge, then apply local semantic relevance filtering."""

    def __init__(self, provider: WikipediaProvider | None = None) -> None:
        self.provider = provider or WikipediaProvider(
            api_url=settings.KNOWLEDGE_API_URL,
            timeout_seconds=settings.KNOWLEDGE_TIMEOUT_SECONDS,
            top_k=settings.KNOWLEDGE_TOP_K,
        )

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedDocument]:
        documents = self.provider.search(query)
        if not documents:
            return []
        retriever = DocumentRetriever(min_similarity=settings.KNOWLEDGE_MIN_SIMILARITY)
        retriever.add_documents(documents)
        return retriever.retrieve(query, k=k)