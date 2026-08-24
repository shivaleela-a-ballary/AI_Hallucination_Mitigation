"""Unit tests for PubMed NCBI E-utilities evidence provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from retrieval.providers.base import Document
from retrieval.providers.pubmed_provider import PubMedConfig, PubMedProvider


SAMPLE_PUBMED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">31978945</PMID>
      <Article PubModel="Print-Electronic">
        <Journal>
          <JournalIssue CitedMedium="Internet">
            <PubDate>
              <Year>2020</Year>
              <Month>Feb</Month>
            </PubDate>
          </JournalIssue>
          <Title>Nature medicine</Title>
        </Journal>
        <ArticleTitle>Clinical characteristics of coronavirus disease 2019 in China.</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">A novel coronavirus emerged in Wuhan.</AbstractText>
          <AbstractText Label="RESULTS">The median incubation period was 4.0 days.</AbstractText>
        </Abstract>
        <AuthorList CompleteYN="Y">
          <Author ValidYN="Y">
            <LastName>Guan</LastName>
            <ForeName>Wei-Jie</ForeName>
          </Author>
          <Author ValidYN="Y">
            <LastName>Zhong</LastName>
            <ForeName>Nan-Shan</ForeName>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="pubmed">31978945</ArticleId>
        <ArticleId IdType="doi">10.1056/NEJMoa2002032</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_pubmed_provider_parsing() -> None:
    provider = PubMedProvider()
    with patch.object(provider, "_http_get", return_value=SAMPLE_PUBMED_XML):
        records = provider.fetch_records(["31978945"])

    assert len(records) == 1
    doc = records[0]
    assert doc.source == "PubMed"
    assert doc.pmid == "31978945"
    assert doc.doi == "10.1056/NEJMoa2002032"
    assert "Guan" in doc.authors[0]
    assert "incubation period" in doc.content
    assert doc.publication_date == "2020"
    assert doc.url == "https://pubmed.ncbi.nlm.nih.gov/31978945/"


def test_pubmed_provider_empty_query() -> None:
    provider = PubMedProvider()
    assert provider.search("") == []
    assert provider.search("   ") == []


def test_pubmed_provider_network_failure_graceful() -> None:
    provider = PubMedProvider()
    with patch.object(provider, "_http_get", return_value=None):
        docs = provider.search("COVID-19 pathogenesis")
    assert docs == []
