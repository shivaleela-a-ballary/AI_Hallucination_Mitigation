# API Documentation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Internal REST API Endpoints Overview

All internal endpoints are served asynchronously by FastAPI at base URL `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `/docs` (Swagger UI) and `/redoc` (ReDoc).

```
 ┌──────────────────────┬─────────┬────────────────────────────────────────────────────────┐
 │ Endpoint             │ Method  │ Primary Function                                       │
 ├──────────────────────┼─────────┼────────────────────────────────────────────────────────┤
 │ /api/verify          │ POST    │ Verify a factual claim against provided/retrieved data │
 │ /api/verify/batch    │ POST    │ Batch verification of multiple claims                  │
 │ /api/check-answer    │ POST    │ Audit full LLM answer and score hallucination risk     │
 │ /api/ask             │ POST    │ Grounded RAG query answering with citations            │
 │ /api/upload          │ POST    │ Upload and index document corpus (PDF, TXT, MD)        │
 │ /api/documents       │ GET     │ List all indexed documents and chunk statistics        │
 │ /api/documents/search│ POST    │ Semantic search across uploaded document chunks        │
 │ /api/history         │ GET     │ Fetch paginated verification history                   │
 │ /api/history/{id}    │ DELETE  │ Delete specific verification record                    │
 │ /api/history/clear   │ POST    │ Wipe all stored verification records                   │
 │ /api/health          │ GET     │ Server liveness, version, and database mode probe      │
 │ /api/stats           │ GET     │ System usage and verification aggregate statistics     │
 └──────────────────────┴─────────┴────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Internal Endpoint Specifications

### 2.1 POST `/api/verify`
- **Purpose:** Primary stance detection and factuality verification for a single claim.
- **Implementation File:** `backend/api/routes/verify.py`
- **Request Headers:** `Content-Type: application/json`
- **Request Body (JSON):**
  ```json
  {
    "claim": "The Pacific Ocean is the largest ocean on Earth.",
    "evidence": "The Pacific Ocean is the largest and deepest of Earth's oceanic divisions.",
    "methods": ["cross_encoder", "semantic_similarity"]
  }
  ```
- **Response Body (200 OK):**
  ```json
  {
    "claim": "The Pacific Ocean is the largest ocean on Earth.",
    "verdict": "SUPPORTED",
    "confidence": 0.96,
    "is_hallucinated": false,
    "methods_used": ["cross_encoder", "semantic_similarity"],
    "evidence_sources": [
      {
        "title": "Pacific Ocean",
        "source": "Wikipedia",
        "similarity_score": 0.94,
        "content": "The Pacific Ocean is the largest and deepest..."
      }
    ],
    "entities": ["Pacific Ocean", "Earth", "Ocean"],
    "knowledge_graph": {
      "nodes": [
        { "id": "Pacific Ocean", "label": "Pacific Ocean", "type": "subject" },
        { "id": "Earth", "label": "Earth", "type": "object" }
      ],
      "edges": [
        { "source": "Pacific Ocean", "target": "Earth", "predicate": "is largest ocean on" }
      ]
    }
  }
  ```
- **Error Codes:** `400 Bad Request` (empty claim), `422 Unprocessable Entity` (invalid types), `500 Internal Error`.

---

### 2.2 POST `/api/check-answer`
- **Purpose:** Decomposes a multi-paragraph LLM-generated answer, extracts propositions, cross-references evidence, and scores hallucination risk.
- **Implementation File:** `backend/api/routes/check_answer.py`
- **Request Body (JSON):**
  ```json
  {
    "query": "Who invented the telephone?",
    "answer": "Alexander Graham Bell was awarded the first US patent for the telephone in 1876. He also invented the steam engine in 1712.",
    "documents": []
  }
  ```
- **Response Body (200 OK):**
  ```json
  {
    "id": "ans_9f8a2b3c",
    "query": "Who invented the telephone?",
    "answer": "Alexander Graham Bell was awarded the first US patent for the telephone in 1876. He also invented the steam engine in 1712.",
    "verification_status": "CONTRADICTED",
    "confidence_score": 0.88,
    "hallucination_risk_score": 0.50,
    "hallucination_risk_label": "HIGH",
    "claims": [
      {
        "claim": "Alexander Graham Bell was awarded the first US patent for the telephone in 1876.",
        "status": "SUPPORTED",
        "evidence_score": 0.95,
        "method": "cross_encoder"
      },
      {
        "claim": "He also invented the steam engine in 1712.",
        "status": "REFUTED",
        "evidence_score": 0.92,
        "method": "cross_encoder"
      }
    ],
    "sources": [
      {
        "title": "Alexander Graham Bell",
        "source": "Wikipedia",
        "content": "Alexander Graham Bell patented the telephone in 1876..."
      },
      {
        "title": "Steam engine",
        "source": "Wikipedia",
        "content": "Thomas Newcomen built the first commercial steam engine in 1712..."
      }
    ]
  }
  ```

---

### 2.3 POST `/api/ask`
- **Purpose:** Performs grounded question answering over retrieved multi-source evidence with source citations and abstention safeguards.
- **Implementation File:** `backend/api/routes/ask.py`
- **Request Body (JSON):**
  ```json
  {
    "query": "What is the speed of light in vacuum?",
    "max_sources": 3,
    "enable_grounding": true
  }
  ```
- **Response Body (200 OK):**
  ```json
  {
    "query": "What is the speed of light in vacuum?",
    "answer": "The speed of light in vacuum is exactly 299,792,458 meters per second (approximately 300,000 km/s) [1].",
    "verification_status": "SUPPORTED",
    "confidence_score": 0.98,
    "sources": [
      {
        "citation_id": 1,
        "title": "Speed of light",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Speed_of_light",
        "snippet": "The speed of light in vacuum is defined to be exactly 299,792,458 m/s..."
      }
    ]
  }
  ```

---

### 2.4 POST `/api/upload`
- **Purpose:** Ingests raw document files, extracts text, chunks, embeds, and stores in the vector index.
- **Implementation File:** `backend/api/routes/upload.py`
- **Request:** `multipart/form-data` with field `file` (`.pdf`, `.txt`, `.md`, `.docx`, `.csv`).
- **Response Body (200 OK):**
  ```json
  {
    "status": "success",
    "document_id": "doc_a1b2c3d4",
    "filename": "quantum_mechanics_notes.pdf",
    "chunks_count": 14,
    "tokens_total": 6840,
    "indexed_at": "2026-09-06T06:30:00Z"
  }
  ```

---

### 2.5 GET `/api/health`
- **Purpose:** Liveness and operational readiness probe.
- **Implementation File:** `backend/api/routes/health.py`
- **Response Body (200 OK):**
  ```json
  {
    "status": "healthy",
    "version": "2.0.0",
    "db_mode": "in-memory-fallback",
    "models_loaded": {
      "cross_encoder": true,
      "embeddings": true,
      "token_probability": true
    },
    "timestamp": "2026-09-06T06:30:15Z"
  }
  ```

---

## 3. External API Integrations

| Provider | Base URL | Auth Mechanism | Rate Limit / Quota |
| :--- | :--- | :--- | :--- |
| **Wikipedia REST API** | `https://en.wikipedia.org/` | User-Agent Header | Standard open-access rate limits |
| **arXiv Query API** | `http://export.arxiv.org/api/` | None (Public) | Max 1 request per 3 seconds |
| **Semantic Scholar API** | `https://api.semanticscholar.org/` | Optional API Key | 100 requests / 5 min without key |
| **Hugging Face Hub** | `https://huggingface.co/` | Optional `HF_TOKEN` | Unlimited for cached local downloads |
| **MongoDB Atlas** | `mongodb+srv://...` | Connection String URI | Governed by cloud cluster tier |
