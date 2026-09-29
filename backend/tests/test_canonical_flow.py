"""
End-to-End verification script for the canonical user flow:
Claim: "The Python programming language was originally created by Guido van Rossum in 1989 while he was working at Google."
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_canonical_python_verification_flow():
    claim = "The Python programming language was originally created by Guido van Rossum in 1989 while he was working at Google."
    
    # 1. POST /api/verify
    res = client.post("/api/verify", json={"claim": claim})
    assert res.status_code == 200, res.text
    data = res.json()
    
    # Check canonical fields
    assert data["claim"] == claim
    assert data["verdict"] in ("REFUTED", "CONTRADICTS")
    assert 0.0 <= data["risk_score"] <= 1.0
    assert 0 <= data["hallucination_risk_score"] <= 100
    assert data["hallucination_risk_score"] >= 60, f"Expected HIGH risk for false claim, got {data['hallucination_risk_score']}"
    
    # Check Forensics
    assert "forensics" in data
    forensics = data["forensics"]
    assert forensics["claim_text"] == claim, f"Forensics analyzed claim must not be blank, got: {forensics['claim_text']!r}"
    assert len(forensics["claim_text"]) > 10
    assert forensics["severity"] in ("high", "critical")
    assert len(forensics["why_flagged"]) > 10
    
    # Check 12 patterns
    assert len(forensics["detected_patterns"]) == 12
    entity_pattern = next(p for p in forensics["detected_patterns"] if p["pattern"] == "Entity Confusion")
    assert entity_pattern["detected"] is True
    assert "cwi" in entity_pattern["reason"].lower() or "google" in entity_pattern["reason"].lower()
    
    # Check Risk Analysis
    assert "risk_analysis" in data
    risk_ana = data["risk_analysis"]
    assert 0.0 <= risk_ana["calibrated_risk_score"] <= 1.0
    assert risk_ana["hallucination_risk_tier"] == "HIGH"
    assert len(risk_ana["reasoning_bullets"]) >= 4
    
    # Check Before/After Grounded Correction
    assert "before_after" in data
    ba = data["before_after"]
    assert ba["original_text"] == claim
    assert "cwi" in ba["corrected_text"].lower() or "netherlands" in ba["corrected_text"].lower()
    assert ba["mitigated_risk_score"] < ba["original_risk_score"]
    
    # Check Knowledge Graph
    assert "knowledge_graph" in data
    kg = data["knowledge_graph"]
    assert "nodes" in kg and "edges" in kg
    
    # 2. Check GET /api/verification/current
    cur_res = client.get("/api/verification/current")
    assert cur_res.status_code == 200, cur_res.text
    cur_data = cur_res.json()
    assert cur_data["id"] == data["id"]
    assert cur_data["claim"] == claim
    assert cur_data["forensics"]["claim_text"] == claim
    
    print("\n[SUCCESS] Canonical verification flow passed with 100% adherence to requirements!")
    print(f"  - Verified Claim: {cur_data['claim']}")
    print(f"  - Verdict: {cur_data['verdict']}")
    print(f"  - Hallucination Risk Score: {cur_data['hallucination_risk_score']}% ({risk_ana['hallucination_risk_tier']})")
    print(f"  - Primary Forensic Pattern: {forensics['pattern_type']}")
    print(f"  - Forensic Why Flagged: {forensics['why_flagged']}")
    print(f"  - Grounded Correction: {ba['corrected_text']}")

if __name__ == "__main__":
    test_canonical_python_verification_flow()
