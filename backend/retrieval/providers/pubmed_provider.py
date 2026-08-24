"""
PubMed / NCBI E-utilities Evidence Provider.
Queries the National Center for Biotechnology Information (NCBI) Entrez API for biomedical literature.
Extracts PMIDs, DOIs, article abstracts, author lists, journals, and publication dates.
"""

from __future__ import annotations

import json
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


@dataclass(frozen=True)
class PubMedConfig:
    search_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    fetch_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    summary_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    timeout_seconds: float = 8.0
    email: str = ""
    api_key: str = ""
    tool_name: str = "AIHallucinationMitigation"


class PubMedProvider(EvidenceProvider):
    """
    Biomedical literature evidence provider using NCBI PubMed E-utilities.
    """
    def __init__(self, config: PubMedConfig | None = None) -> None:
        self.config = config or PubMedConfig(
            timeout_seconds=getattr(settings, "PUBMED_TIMEOUT_SECONDS", 8.0),
            email=getattr(settings, "PUBMED_EMAIL", "researcher@example.com"),
            api_key=getattr(settings, "PUBMED_API_KEY", ""),
        )

    @property
    def name(self) -> str:
        return "PubMed"

    def _build_params(self, base_params: dict[str, str | int]) -> str:
        params = dict(base_params)
        params["tool"] = self.config.tool_name
        if self.config.email:
            params["email"] = self.config.email
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        return urllib.parse.urlencode(params)

    def _http_get(self, url: str, params: dict[str, str | int]) -> bytes | None:
        full_url = f"{url}?{self._build_params(params)}"
        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": f"AIHallucinationMitigation/2.0 (mailto:{self.config.email or 'researcher@example.com'})",
                "Accept": "*/*",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                if response.status == 200:
                    return response.read()
                logger.warning(f"PubMed API returned HTTP status {response.status}")
                return None
        except Exception as exc:
            logger.warning(f"PubMed API request failed ({type(exc).__name__}): {exc}")
            return None

    def search_pmids(self, query: str, top_k: int = 5) -> list[str]:
        """Search PubMed Entrez and return matching PMIDs."""
        # Sanitize search term: extract key scientific entities/terms for best search precision
        clean_query = re.sub(r"[^\w\s-]", " ", query).strip()
        if not clean_query:
            return []

        # Take the most relevant scientific tokens if query is long
        tokens = [t for t in clean_query.split() if len(t) > 2]
        search_term = " ".join(tokens[:12]) if len(tokens) > 12 else clean_query

        params = {
            "db": "pubmed",
            "term": search_term,
            "retmode": "json",
            "retmax": top_k,
            "sort": "relevance",
        }
        data = self._http_get(self.config.search_url, params)
        if not data:
            return []

        try:
            parsed = json.loads(data.decode("utf-8"))
            id_list = parsed.get("esearchresult", {}).get("idlist", [])
            return [str(pid) for pid in id_list if pid]
        except Exception as exc:
            logger.warning(f"Failed to parse PubMed esearch response: {exc}")
            return []

    def fetch_records(self, pmids: Sequence[str]) -> list[Document]:
        """Fetch article details (title, abstract, authors, DOI, date) for given PMIDs."""
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }
        xml_data = self._http_get(self.config.fetch_url, params)
        if not xml_data:
            return []

        documents: list[Document] = []
        try:
            root = ET.fromstring(xml_data)
            for article in root.findall(".//PubmedArticle"):
                try:
                    # PMID
                    pmid_elem = article.find(".//MedlineCitation/PMID")
                    pmid = pmid_elem.text.strip() if pmid_elem is not None and pmid_elem.text else None

                    # Title
                    title_elem = article.find(".//MedlineCitation/Article/ArticleTitle")
                    title = "".join(title_elem.itertext()).strip() if title_elem is not None else ""

                    # Abstract
                    abstract_texts = []
                    for abs_elem in article.findall(".//MedlineCitation/Article/Abstract/AbstractText"):
                        label = abs_elem.get("Label")
                        text = "".join(abs_elem.itertext()).strip()
                        if label and text:
                            abstract_texts.append(f"{label}: {text}")
                        elif text:
                            abstract_texts.append(text)
                    abstract = "\n".join(abstract_texts).strip()

                    if not abstract and title:
                        abstract = title

                    if not abstract:
                        continue

                    # Authors
                    authors = []
                    for author_elem in article.findall(".//MedlineCitation/Article/AuthorList/Author"):
                        last_name = author_elem.find("LastName")
                        fore_name = author_elem.find("ForeName")
                        if last_name is not None and last_name.text:
                            name = last_name.text.strip()
                            if fore_name is not None and fore_name.text:
                                name = f"{fore_name.text.strip()} {name}"
                            authors.append(name)

                    # Publication Date
                    pub_date = None
                    year_elem = article.find(".//MedlineCitation/Article/Journal/JournalIssue/PubDate/Year")
                    if year_elem is not None and year_elem.text:
                        pub_date = year_elem.text.strip()

                    # DOI
                    doi = None
                    for article_id in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                        if article_id.get("IdType") == "doi" and article_id.text:
                            doi = article_id.text.strip()
                            break

                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

                    documents.append(
                        Document(
                            title=title or f"PubMed Article {pmid}",
                            content=abstract,
                            source="PubMed",
                            url=url,
                            doi=doi,
                            pmid=pmid,
                            publication_date=pub_date,
                            authors=authors[:5],
                            source_type="peer_reviewed_journal",
                        )
                    )
                except Exception as doc_err:
                    logger.debug(f"Error parsing individual PubMed article: {doc_err}")
                    continue

        except Exception as exc:
            logger.warning(f"Failed to parse PubMed XML response: {exc}")
            return []

        return documents

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        """End-to-end PubMed search and document generation."""
        try:
            pmids = self.search_pmids(query, top_k=top_k)
            if not pmids:
                return []
            return self.fetch_records(pmids)
        except Exception as exc:
            logger.warning(f"PubMed search failed gracefully: {exc}")
            return []
