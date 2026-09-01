"""Unit and integration tests for Document Uploads and Ingestion."""

from __future__ import annotations

import io
from fastapi.testclient import TestClient
from api.app import app
from api.db.mongodb import db_manager
from retrieval.document_parser import chunk_text, extract_text_from_file
from retrieval.providers.uploads_provider import UserUploadsProvider


def test_chunk_text_produces_overlapping_passages() -> None:
    text = " ".join([f"Word{i}" for i in range(500)])
    chunks = chunk_text(text, title="Test Doc", target_words=100, overlap_words=20)
    assert len(chunks) > 1
    assert all("Test Doc" in c["title"] for c in chunks)
    assert all(len(c["content"].split()) > 0 for c in chunks)


def test_extract_text_from_plain_text() -> None:
    content = b"This is a scientific clinical trial abstract regarding pembrolizumab."
    text = extract_text_from_file("trial.txt", content)
    assert "pembrolizumab" in text


def test_upload_text_api_and_search() -> None:
    client = TestClient(app)

    # 1. Ingest raw text
    payload = {
        "title": "Oncology Research on Pembrolizumab",
        "content": "Pembrolizumab is a humanized antibody used in cancer immunotherapy targeting PD-1 receptors.",
    }
    response = client.post("/api/uploads/text", json=payload)
    assert response.status_code == 201
    data = response.json()
    doc_id = data["document"]["id"]

    # 2. List uploads
    list_resp = client.get("/api/uploads")
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # 3. Search via UserUploadsProvider
    provider = UserUploadsProvider()
    found = provider.search("Pembrolizumab immunotherapy PD-1")
    assert len(found) > 0
    assert any("Pembrolizumab" in d.content for d in found)

    # 4. Clean up
    del_resp = client.delete(f"/api/uploads/{doc_id}")
    assert del_resp.status_code == 200


def test_upload_file_api() -> None:
    client = TestClient(app)
    file_bytes = b"Statins competitively inhibit 3-hydroxy-3-methylglutaryl-coenzyme A reductase."
    files = {"file": ("statins_paper.txt", io.BytesIO(file_bytes), "text/plain")}
    data = {"title": "Statin Pharmacology Study"}

    resp = client.post("/api/uploads/file", files=files, data=data)
    assert resp.status_code == 201
    doc_id = resp.json()["document"]["id"]

    # Clean up
    client.delete(f"/api/uploads/{doc_id}")


def test_upload_image_file_api() -> None:
    # 1x1 raw valid PNG bytes in memory
    img_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    client = TestClient(app)
    files = {"file": ("pasted_screenshot.png", io.BytesIO(img_bytes), "image/png")}
    data = {"title": "Biomedical Diagram Screenshot"}

    resp = client.post("/api/uploads/file", files=files, data=data)
    assert resp.status_code == 201
    doc = resp.json()["document"]
    assert doc["file_type"] == "png"
    assert len(doc["chunks"]) > 0

    # Clean up
    client.delete(f"/api/uploads/{doc['id']}")

