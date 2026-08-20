"""
Unit and integration tests for Authentication, User API, and MongoDB collections layer.
"""

import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from api.app import app
from api.db.mongodb import db_manager

client = TestClient(app)


def test_auth_and_user_lifecycle():
    # 1. Health check includes mongo status
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    data = health_res.json()
    assert "mongodb_connected" in data
    assert "stats" in data

    # 2. Register user
    reg_payload = {
        "username": "testverifier",
        "email": "verifier@example.com",
        "password": "Password123!",
        "full_name": "Test Verifier",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["username"] == "testverifier"
    token = reg_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Duplicate registration should fail
    dup_res = client.post("/api/auth/register", json=reg_payload)
    assert dup_res.status_code == 400

    # 4. Login with email
    login_res = client.post("/api/auth/login", json={"username": "verifier@example.com", "password": "Password123!"})
    assert login_res.status_code == 200
    login_token = login_res.json()["access_token"]
    assert login_token

    # 5. Check /api/auth/me
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == "verifier@example.com"
    assert me_data["settings"] is not None

    # 6. User Profile Update
    prof_update = client.put("/api/user/profile", headers=auth_headers, json={"full_name": "Senior Verifier", "bio": "SciFact Researcher"})
    assert prof_update.status_code == 200
    assert prof_update.json()["user"]["full_name"] == "Senior Verifier"

    # 7. User Settings Update
    settings_update = client.put("/api/user/settings", headers=auth_headers, json={"theme": "dark", "default_top_k": 7})
    assert settings_update.status_code == 200
    assert settings_update.json()["default_top_k"] == 7

    # 8. Add item directly to MongoDB verification history
    history_record = {
        "claim": "Direct test claim",
        "answer": "Grounded answer",
        "verification_status": "SUPPORTED",
        "confidence_score": 0.95,
        "confidence_available": True,
        "sources": [],
        "evidence": [],
        "claims": [],
        "confidence_explanation": "Test explanation",
    }
    saved = db_manager.add_verification_history(history_record, user_id=reg_data["user"]["id"])
    item_id = saved["id"]

    # 9. Get User History via /api/user/history
    history_res = client.get("/api/user/history", headers=auth_headers)
    assert history_res.status_code == 200
    h_items = history_res.json()["history"]
    assert any(h["id"] == item_id for h in h_items)

    # 10. Delete specific history item
    del_res = client.delete(f"/api/user/history/{item_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # 11. Clear user history
    clear_res = client.delete("/api/user/history", headers=auth_headers)
    assert clear_res.status_code == 200
    assert clear_res.json()["deleted_count"] >= 0

