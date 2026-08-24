"""Unit tests for multi-source evidence manager, deduplication, and reranking."""

from __future__ import annotations

import numpy as np
from retrieval.deduplication import EvidenceDeduplicator, normalize_title, text_similarity_jaccard
from retrieval.providers.base import Document, EvidenceProvider
from retrieval.providers.manager import MultiSourceEvidenceManager
from retrieval.reranker import EvidenceReranker


class MockProvider(EvidenceProvider):
    def __init__(self, name: str, docs: list[Document]) -> None:
        self._name = name
        self.docs = docs

    @property
    def name(self) -> str:
        return self._name

    def search(self, query: str, top_k: int = 5) -> list[Document]:
        return self.docs[:top_k]


def test_deduplicator_doi_and_pmid_matching() -> None:
    deduplicator = EvidenceDeduplicator()
    docs = [
        Document("Study A", "First copy of abstract text.", "SciFact", doi="10.1234/test.1"),
        Document("Study A Alternative", "Second copy of abstract from PubMed.", "PubMed", doi="10.1234/TEST.1"),  # Same DOI
        Document("Study B", "Abstract for study B.", "PubMed", pmid="12345678"),
        Document("Study B Duplicate", "Another duplicate.", "SciFact", pmid="12345678"),  # Same PMID
    ]
    unique = deduplicator.deduplicate(docs)
    assert len(unique) == 2
    assert unique[0].title == "Study A"
    assert unique[1].title == "Study B"


def test_deduplicator_title_normalization() -> None:
    deduplicator = EvidenceDeduplicator()
    docs = [
        Document("The Role of MicroRNAs in Human Oncology.", "Content one.", "SciFact"),
        Document("Role of MicroRNAs in Human Oncology", "Content two.", "PubMed"),
    ]
    unique = deduplicator.deduplicate(docs)
    assert len(unique) == 1


def test_deduplicator_content_jaccard_similarity() -> None:
    sim = text_similarity_jaccard(
        "MicroRNAs regulate gene expression post-transcriptionally by binding target mRNAs.",
        "MicroRNAs regulate gene expression post-transcriptionally by binding target mRNAs.",
    )
    assert sim == 1.0


def test_multisource_manager_aggregates_providers() -> None:
    p1 = MockProvider("P1", [Document("Doc1", "Content1", "P1")])
    p2 = MockProvider("P2", [Document("Doc2", "Content2", "P2")])
    mgr = MultiSourceEvidenceManager(providers=[p1, p2])
    candidates = mgr.retrieve_candidates("test query")
    assert len(candidates) == 2
    sources = {d.source for d in candidates}
    assert sources == {"P1", "P2"}


class SimpleEmbedder:
    dimension = 3

    def encode(self, text: str) -> np.ndarray:
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

    def encode_many(self, texts: list[str]) -> np.ndarray:
        return np.vstack([np.array([1.0, 0.0, 0.0], dtype=np.float32) for _ in texts])


def test_evidence_reranker_scores_and_orders() -> None:
    reranker = EvidenceReranker(embedder=SimpleEmbedder(), min_similarity=0.1)
    docs = [
        Document("Title A", "MicroRNA regulation and translation.", "SciFact", source_type="scientific_corpus"),
        Document("Title B", "Unrelated geology rock formations.", "Wikipedia", source_type="encyclopedia"),
    ]
    ranked = reranker.rerank("MicroRNA", docs, top_k=2)
    assert len(ranked) == 2
    assert ranked[0].similarity_score >= ranked[1].similarity_score
    assert ranked[0].title == "Title A"
