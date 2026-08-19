"""Deterministic tests for the local baseline backend components."""

from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient
from pathlib import Path

from api.app import app
from api.services.rag_pipeline import RAGPipeline
from preprocessing.preprocess import QueryPreprocessor
from retrieval.retrieve import Document, DocumentRetriever
from verification.scifact_verify import (
    BaselineSciFactVerifier,
    Claim,
    ClaimVerification,
    VerificationStatus,
)
from retrieval.knowledge_provider import GeneralKnowledgeRetriever, WikipediaProvider


class TestEmbedder:
    dimension = 3

    def encode(self, text: str) -> np.ndarray:
        return self._vector(text)

    def encode_many(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self._vector(text) for text in texts])

    @staticmethod
    def _vector(text: str) -> np.ndarray:
        if "retrieval" in text.lower():
            return np.array([1.0, 0.0, 0.0], dtype=np.float32)
        return np.array([0.0, 1.0, 0.0], dtype=np.float32)


def make_retriever() -> DocumentRetriever:
    retriever = DocumentRetriever(embedder=TestEmbedder())
    retriever.add_documents([
        Document("RAG", "Retrieval augmented generation retrieves relevant documents.", "test"),
        Document("Other", "Unrelated text for deterministic testing.", "test"),
    ])
    return retriever


def test_preprocessing_rejects_empty_text() -> None:
    preprocessor = QueryPreprocessor()
    assert preprocessor.process("  retrieval\n generation ") == "retrieval generation"
    try:
        preprocessor.process("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for blank input")


def test_retrieval_and_pipeline_baseline() -> None:
    retriever = make_retriever()
    assert retriever.index.count == 2
    # The production pipeline requires an actual local SciFact checkpoint.  This
    # component test injects the deterministic baseline deliberately.
    result = RAGPipeline(
        retrieval_service=retriever,
        verification_service=BaselineSciFactVerifier(),
    ).run("What is retrieval augmented generation?")
    assert result["sources"][0]["title"] == "RAG"
    assert isinstance(result["sources"][0]["similarity_score"], float)
    assert result["verification_status"] in {"SUPPORTED", "UNCERTAIN", "REFUTED"}
    assert 0.0 <= result["confidence_score"] <= 1.0


def test_health_endpoint() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "degraded"}


def test_retrieval_threshold_excludes_unrelated_documents() -> None:
    retriever = DocumentRetriever(embedder=TestEmbedder(), min_similarity=0.9)
    retriever.add_documents([Document("Other", "Unrelated text.", "real-source")])
    assert retriever.retrieve("retrieval") == []


class FixedVerifier:
    def __init__(self, status: VerificationStatus) -> None:
        self.status = status

    def extract_claims(self, text: str, evidence: list) -> list[Claim]:
        return [Claim(text=text, evidence_titles=[item.title for item in evidence])] if text else []

    def verify(self, claims: list[Claim], evidence: list) -> list[ClaimVerification]:
        return [
            ClaimVerification(
                claim=claim.text,
                status=self.status,
                evidence_titles=[item.title for item in evidence],
                evidence_score=0.95,
                method="deterministic test verifier",
            )
            for claim in claims
        ]


def make_answer_pipeline(status: VerificationStatus) -> RAGPipeline:
    return RAGPipeline(
        retrieval_service=make_retriever(),
        verification_service=FixedVerifier(status),
    )


def test_supported_claim_is_grounded_in_retrieved_source() -> None:
    result = make_answer_pipeline(VerificationStatus.SUPPORTED).run(
        "What is retrieval augmented generation?"
    )
    assert result["verification_status"] == VerificationStatus.SUPPORTED
    assert result["sources"][0]["source"] == "test"
    assert result["answer"] == result["sources"][0]["content"]


def test_refuted_claim_is_not_presented_as_fact() -> None:
    result = make_answer_pipeline(VerificationStatus.REFUTED).run(
        "What is retrieval augmented generation?"
    )
    assert result["verification_status"] == VerificationStatus.REFUTED
    assert "refutes" in result["answer"]
    assert result["confidence_score"] < 0.5


def test_missing_answer_corpus_returns_uncertain_without_sources() -> None:
    result = RAGPipeline(
        evidence_retrieval_service=make_retriever(),
        verification_service=FixedVerifier(VerificationStatus.SUPPORTED),
    ).run("A question with no configured answer corpus")
    assert result["verification_status"] == VerificationStatus.UNCERTAIN
    assert result["confidence_score"] == 0.0
    assert result["sources"] == []
    assert "sufficient verified evidence" in result["answer"]


def test_production_code_has_no_sample_fallback_markers() -> None:
    backend = Path(__file__).resolve().parents[1]
    production_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in backend.rglob("*.py")
        if "tests" not in path.parts
    ).lower()
    assert "sample_documents" not in production_text
    assert "development-sample" not in production_text
    assert "acid rain" not in production_text


def test_general_provider_preserves_real_source_url() -> None:
    class Provider:
        def search(self, query: str) -> list[Document]:
            return [Document("RAG", "Retrieval augmented generation uses external documents.", "Wikipedia", "https://en.wikipedia.org/wiki/RAG")]

    result = GeneralKnowledgeRetriever(provider=Provider()).retrieve("retrieval augmented generation")
    assert result[0].source == "Wikipedia"
    assert result[0].url == "https://en.wikipedia.org/wiki/RAG"


def test_unavailable_provider_is_explicitly_reported() -> None:
    class UnavailableProvider(WikipediaProvider):
        def search(self, query: str) -> list[Document]:
            raise RuntimeError("offline")

    try:
        UnavailableProvider("https://example.invalid", 1, 1).search("question")
    except RuntimeError as exc:
        assert str(exc) == "offline"
    else:
        raise AssertionError("Expected provider failure")
