import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from api.db.mongodb import db_manager
from api.security.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_auth_and_mongo():
    print("Testing Password Hashing...")
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed), "Password verification failed"
    assert not verify_password("WrongPassword", hashed), "Invalid password verified as true"
    print("Password hashing test passed.")

    print("Testing JWT Token Creation and Decoding...")
    payload = {"sub": "user-uuid-1234", "username": "alice", "email": "alice@example.com"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None, "Token decoding returned None"
    assert decoded["sub"] == "user-uuid-1234", "Token sub mismatch"
    assert decoded["username"] == "alice", "Token username mismatch"
    print("JWT test passed.")

    print("Testing MongoDB Manager Users Collection...")
    user = db_manager.create_user({
        "username": "alice_test",
        "email": "alice@test.com",
        "hashed_password": hashed,
        "full_name": "Alice Test",
    })
    assert user["id"] is not None
    found = db_manager.find_user_by_email("alice@test.com")
    assert found is not None
    assert found["username"] == "alice_test"
    found_by_uname = db_manager.find_user_by_username("alice_test")
    assert found_by_uname is not None
    print("MongoDB Users collection test passed.")

    print("Testing MongoDB Manager User Settings Collection...")
    settings = db_manager.get_user_settings(user["id"])
    assert settings["default_min_similarity"] == 0.45
    updated_settings = db_manager.update_user_settings(user["id"], {"theme": "light", "default_top_k": 10})
    assert updated_settings["theme"] == "light"
    assert updated_settings["default_top_k"] == 10
    print("MongoDB User Settings collection test passed.")

    print("Testing MongoDB Manager Verification History Collection...")
    history_record = {
        "claim": "Vitamin D supports bone density.",
        "answer": "Scientific studies show Vitamin D facilitates calcium absorption.",
        "verification_status": "SUPPORTED",
        "confidence_score": 0.94,
        "confidence_available": True,
        "sources": [],
        "evidence": [],
        "claims": [],
        "confidence_explanation": "SciFact supported evidence.",
    }
    saved = db_manager.add_verification_history(history_record, user_id=user["id"])
    assert saved["id"] is not None
    user_history = db_manager.get_user_verification_history(user_id=user["id"])
    assert len(user_history) >= 1
    assert user_history[0]["id"] == saved["id"]

    # Delete history item
    deleted = db_manager.delete_history_item(saved["id"], user_id=user["id"])
    assert deleted is True
    print("MongoDB Verification History collection test passed.")

    print("ALL DIRECT AUTH & MONGO TESTS PASSED!")


if __name__ == "__main__":
    test_auth_and_mongo()
