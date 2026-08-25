"""Unit tests for Semantic Scholar Graph API evidence provider."""

from __future__ import annotations

import json
from unittest.mock import patch

from retrieval.providers.semantic_scholar_provider import (
    SemanticScholarConfig,
    SemanticScholarProvider,
)

SAMPLE_S2_RESPONSE = json.dumps({
    "total": 1,
    "offset": 0,
    "data": [
        {
            "paperId": "abcdef1234567890",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            "year": 2017,
            "publicationDate": "2017-06-12",
            "venue": "NeurIPS",
            "url": "https://www.semanticscholar.org/paper/abcdef1234567890",
            "externalIds": {
                "DOI": "10.48550/arXiv.1706.03762",
                "ArXiv": "1706.03762",
                "PubMed": "12345678"
            },
            "authors": [
                {"name": "Ashish Vaswani"},
                {"name": "Noam Shazeer"}
            ]
        }
    ]
}).encode("utf-8")


def test_semantic_scholar_search_success() -> None:
    provider = SemanticScholarProvider()
    with patch.object(provider, "_http_get", return_value=SAMPLE_S2_RESPONSE):
        docs = provider.search("transformer attention mechanism", top_k=5)

    assert len(docs) == 1
    doc = docs[0]
    assert doc.source == "Semantic Scholar"
    assert doc.title == "Attention Is All You Need"
    assert "recurrent or convolutional" in doc.content
    assert doc.doi == "10.48550/arXiv.1706.03762"
    assert doc.pmid == "12345678"
    assert doc.publication_date == "2017"
    assert len(doc.authors) == 2
    assert "Ashish Vaswani" in doc.authors
    assert doc.url == "https://www.semanticscholar.org/paper/abcdef1234567890"


def test_semantic_scholar_empty_query() -> None:
    provider = SemanticScholarProvider()
    assert provider.search("") == []
    assert provider.search("   ") == []


def test_semantic_scholar_http_failure_graceful() -> None:
    provider = SemanticScholarProvider()
    with patch.object(provider, "_http_get", return_value=None):
        docs = provider.search("CRISPR gene editing")
    assert docs == []


def test_semantic_scholar_malformed_json_graceful() -> None:
    provider = SemanticScholarProvider()
    with patch.object(provider, "_http_get", return_value=b"INVALID JSON"):
        docs = provider.search("Quantum computing")
    assert docs == []
