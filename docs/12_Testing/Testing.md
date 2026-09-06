# Testing & Quality Assurance Documentation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Testing Strategy & Frameworks

The testing suite validates end-to-end factuality, API responsiveness, database fallback behaviors, and retrieval accuracy.

- **Test Runner:** `pytest 8.0+` with `pytest-asyncio`.
- **HTTP Test Client:** `httpx.AsyncClient` & FastAPI `TestClient`.
- **Test Suite Location:** `backend/tests/` (51 active automated test scenarios).
- **Execution Command:** `pytest backend/tests/ -v`.

```
 backend/tests/
 ├── test_app.py               # Health checks, CORS, error handling, stats API
 ├── test_verification.py      # Cross-encoder, semantic similarity, token prob
 ├── test_retrieval.py         # Multi-source retrieval, BM25, RRF ranking
 ├── test_uploads_api.py       # PDF/TXT file upload, chunking, search
 ├── test_six_scenarios.py     # End-to-end factual scenarios (True/False/Ambiguous)
 └── test_database.py          # MongoDB connectivity & In-Memory fallback
```

---

## 2. Test Execution Summary

| Test Category | File | Test Count | Pass Rate | Execution Time |
| :--- | :--- | :--- | :--- | :--- |
| **API & Gateway** | `test_app.py` | 8 | 100% (8/8) | ~0.45s |
| **Verification Heads** | `test_verification.py` | 12 | 100% (12/12) | ~2.10s |
| **Retrieval & RRF** | `test_retrieval.py` | 9 | 100% (9/9) | ~1.30s |
| **Uploads & Chunks** | `test_uploads_api.py` | 10 | 100% (10/10) | ~0.85s |
| **Factual Scenarios** | `test_six_scenarios.py`| 6 | 100% (6/6) | ~2.40s |
| **Database Fallback** | `test_database.py` | 6 | 100% (6/6) | ~0.35s |
| **Total Test Suite** | **All Modules** | **51** | **100% Pass** | **~7.45s** |

---

## 3. Representative Test Cases Table

| Test ID | Component | Input Scenario | Expected Output | Actual Output | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | `api.health` | `GET /api/health` | HTTP 200, status: "healthy", db_mode present | `{"status":"healthy","db_mode":"in-memory-fallback"}` | **PASSED** |
| **TC-02** | `verify.nli` | Claim: "Water boils at 100C", Evidence: "Water boiling point is 100C at 1 atm" | Verdict: `SUPPORTED`, Confidence $> 0.85$ | `Verdict: SUPPORTED, Confidence: 0.94` | **PASSED** |
| **TC-03** | `verify.nli` | Claim: "The moon is made of green cheese", Evidence: "The moon is composed of silicate rock and iron" | Verdict: `REFUTED`, `is_hallucinated: True` | `Verdict: REFUTED, is_hallucinated: True` | **PASSED** |
| **TC-04** | `verify.contra`| Claim: "Revenue grew by 25%", Evidence: "Revenue dropped by 25%" | Polarity contradiction flagged | `is_contradiction: True, type: POLARITY_INVERSION` | **PASSED** |
| **TC-05** | `retrieval.rrf` | Merging BM25 and Dense ranking lists | Reciprocal rank calculation produces top-1 consensus | Document with joint highest rank placed first | **PASSED** |
| **TC-06** | `upload.pdf` | Multipart upload `sample_notes.pdf` (5 pages) | Chunks $\ge 5$, status: "success", embeddings generated | `{"status":"success","chunks_count":6}` | **PASSED** |
| **TC-07** | `rag.abstain` | Ambiguous claim with zero matching evidence | Verdict: `UNCERTAIN`, Grounding warning | `verification_status: UNCERTAIN, score: 0.22` | **PASSED** |
| **TC-08** | `db.fallback` | System initialized without `MONGODB_URI` env | Switches to in-memory store, zero crash | CRUD operations succeed in memory | **PASSED** |
| **TC-09** | `frontend.ts` | Frontend type check (`npx tsc --noEmit`) | Zero compiler errors | `Exit code 0, 0 errors` | **PASSED** |

---

## 4. Specific Factual Scenario Validation (`test_six_scenarios.py`)

The test suite evaluates 6 canonical real-world test cases:
1. **Scenario 1 (Direct Factual Truth):** Validates scientific laws with high confidence.
2. **Scenario 2 (Direct Factual Contradiction):** Validates explicit historical contradictions.
3. **Scenario 3 (Numerical/Temporal Shift):** Validates date and statistical mismatches.
4. **Scenario 4 (Multi-Claim Mixed Answer):** Validates answers containing 1 true claim and 1 false claim.
5. **Scenario 5 (Unverifiable Out-of-Domain Claim):** Validates safe abstention behavior.
6. **Scenario 6 (Custom Document Grounding):** Validates claim verification against private uploaded PDF corpora.
