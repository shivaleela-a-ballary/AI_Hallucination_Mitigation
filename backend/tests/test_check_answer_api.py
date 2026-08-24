"""Unit and integration tests for Check AI Answer API endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from api.app import app
from api.routes.check_answer import split_into_claims


def test_split_into_claims() -> None:
    text = (
        "MicroRNAs regulate gene expression in human cells. "
        "Statins reduce cholesterol levels by inhibiting enzymes. "
        "Penicillin is a common antibiotic."
    )
    claims = split_into_claims(text)
    assert len(claims) == 3
    assert "MicroRNAs" in claims[0]
    assert "Statins" in claims[1]
    assert "Penicillin" in claims[2]


def test_check_ai_answer_endpoint() -> None:
    client = TestClient(app)
    payload = {
        "text": "MicroRNAs inhibit target mRNA translation. Statins lower LDL cholesterol. Telepathy occurs across long distances."
    }
    response = client.post("/api/check-answer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_reliability_score" in data
    assert "overall_hallucination_risk" in data
    assert data["total_claims"] == 3
    assert len(data["claims"]) == 3
    assert data["overall_hallucination_risk"] in {"LOW", "MEDIUM", "HIGH"}
