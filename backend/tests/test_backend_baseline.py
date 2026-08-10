"""Deterministic tests for the local baseline backend components."""

from __future__ import annotations

import numpy as np
from fastapi.testclient import TestClient

from api.app import app
from api.services.rag_pipeline import RAGPipeline
from preprocessing.preprocess import QueryPreprocessor
from retrieval.retrieve import Document, DocumentRetriever


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
    result = RAGPipeline(retrieval_service=retriever).run("What is retrieval augmented generation?")
    assert result["sources"][0]["title"] == "RAG"
    assert isinstance(result["sources"][0]["similarity_score"], float)
    assert result["verification_status"] in {"SUPPORTED", "UNCERTAIN", "REFUTED"}
    assert 0.0 <= result["confidence_score"] <= 1.0


def test_health_endpoint() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
