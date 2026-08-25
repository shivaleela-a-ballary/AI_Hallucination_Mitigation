"""Unit tests for arXiv Atom XML evidence provider."""

from __future__ import annotations

from unittest.mock import patch

from retrieval.providers.arxiv_provider import ArxivConfig, ArxivProvider

SAMPLE_ARXIV_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title type="text">arXiv Query: search_query=all:transformer</title>
  <id>http://arxiv.org/api/12345</id>
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:34Z</published>
    <title>
      Attention Is All You Need
    </title>
    <summary>
      The dominant sequence transduction models are based on complex recurrent or
      convolutional neural networks in an encoder-decoder configuration.
    </summary>
    <author>
      <name>Ashish Vaswani</name>
    </author>
    <author>
      <name>Noam Shazeer</name>
    </author>
    <arxiv:doi>10.48550/arXiv.1706.03762</arxiv:doi>
  </entry>
</feed>
"""


def test_arxiv_search_parsing() -> None:
    provider = ArxivProvider()
    with patch.object(provider, "_http_get", return_value=SAMPLE_ARXIV_XML):
        docs = provider.search("transformer deep learning", top_k=5)

    assert len(docs) == 1
    doc = docs[0]
    assert doc.source == "arXiv"
    assert doc.title == "Attention Is All You Need"
    assert "encoder-decoder configuration" in doc.content
    assert doc.source_type == "preprint"
    assert doc.doi == "10.48550/arXiv.1706.03762"
    assert doc.publication_date == "2017"
    assert "https://arxiv.org/abs/1706.03762v7" in (doc.url or "")
    assert len(doc.authors) == 2
    assert "Ashish Vaswani" in doc.authors


def test_arxiv_empty_query() -> None:
    provider = ArxivProvider()
    assert provider.search("") == []
    assert provider.search("   ") == []


def test_arxiv_network_failure_graceful() -> None:
    provider = ArxivProvider()
    with patch.object(provider, "_http_get", return_value=None):
        docs = provider.search("machine learning")
    assert docs == []


def test_arxiv_malformed_xml_graceful() -> None:
    provider = ArxivProvider()
    with patch.object(provider, "_http_get", return_value=b"<feed>INVALID XML"):
        docs = provider.search("machine learning")
    assert docs == []
