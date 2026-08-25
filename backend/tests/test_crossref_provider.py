"""Unit tests for Crossref REST API evidence provider."""

from __future__ import annotations

import json
from unittest.mock import patch

from retrieval.providers.crossref_provider import (
    CrossrefConfig,
    CrossrefProvider,
    clean_jats_abstract,
)

SAMPLE_CROSSREF_RESPONSE = json.dumps({
    "status": "ok",
    "message": {
        "items": [
            {
                "title": ["CRISPR-Cas9 Structures and Mechanisms of Action"],
                "abstract": "<jats:p>The CRISPR-Cas9 system has revolutionized genome editing across biology.</jats:p>",
                "DOI": "10.1016/j.cell.2017.05.008",
                "URL": "http://dx.doi.org/10.1016/j.cell.2017.05.008",
                "container-title": ["Cell"],
                "published-print": {
                    "date-parts": [[2017, 6, 1]]
                },
                "author": [
                    {"given": "Hiroshi", "family": "Nishimasu"},
                    {"given": "Feng", "family": "Zhang"}
                ]
            }
        ]
    }
}).encode("utf-8")


def test_clean_jats_abstract() -> None:
    jats_text = "<jats:title>Abstract</jats:title><jats:p>This is a &lt;sample&gt; paper on &amp; testing.</jats:p>"
    cleaned = clean_jats_abstract(jats_text)
    assert cleaned == "Abstract This is a <sample> paper on & testing."


def test_crossref_search_success() -> None:
    provider = CrossrefProvider()
    with patch.object(provider, "_http_get", return_value=SAMPLE_CROSSREF_RESPONSE):
        docs = provider.search("CRISPR Cas9 genome editing", top_k=5)

    assert len(docs) == 1
    doc = docs[0]
    assert doc.source == "Crossref"
    assert doc.title == "CRISPR-Cas9 Structures and Mechanisms of Action"
    assert "revolutionized genome editing" in doc.content
    assert doc.doi == "10.1016/j.cell.2017.05.008"
    assert doc.publication_date == "2017"
    assert len(doc.authors) == 2
    assert "Hiroshi Nishimasu" in doc.authors
    assert "Feng Zhang" in doc.authors
    assert doc.url == "http://dx.doi.org/10.1016/j.cell.2017.05.008"


def test_crossref_empty_query() -> None:
    provider = CrossrefProvider()
    assert provider.search("") == []
    assert provider.search("   ") == []


def test_crossref_http_failure_graceful() -> None:
    provider = CrossrefProvider()
    with patch.object(provider, "_http_get", return_value=None):
        docs = provider.search("cancer immunology")
    assert docs == []


def test_crossref_malformed_json_graceful() -> None:
    provider = CrossrefProvider()
    with patch.object(provider, "_http_get", return_value=b"{not valid json"):
        docs = provider.search("cancer immunology")
    assert docs == []
