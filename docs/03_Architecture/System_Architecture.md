# System Architecture Documentation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Architectural Overview

The AI Hallucination Mitigation System is built on a **Decoupled Asynchronous Micro-Layered Architecture**. The system cleanly separates presentation, API routing, business logic orchestration, retrieval indexing, neural inference, and data persistence.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                            │
│   React 19 SPA • TanStack Router • Tailwind CSS 4 • Motion • React Flow │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ JSON over HTTP/REST
┌────────────────────────────────────▼────────────────────────────────────┐
│                            API ROUTING LAYER                            │
│       FastAPI Gateway • Pydantic v2 Serialization • CORS Middleware     │
│   ├─ /api/verify          ├─ /api/check-answer    ├─ /api/ask           │
│   ├─ /api/documents       ├─ /api/history         ├─ /api/health        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                       ORCHESTRATION & LOGIC LAYER                       │
│  ├─ Claim Decomposition Engine                                          │
│  ├─ Multi-Source Retrieval Pipeline (Wikipedia, arXiv, Semantic Scholar)│
│  ├─ Reciprocal Rank Fusion (RRF) & Cross-Encoder Reranker               │
│  ├─ Knowledge Graph Extraction Engine                                   │
│  └─ Dynamic Grounding & Post-Generation Verifier                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                            AI / ML ENGINE LAYER                         │
│  ├─ DeBERTa-v3 NLI (`cross-encoder/nli-deberta-v3-small`)              │
│  ├─ Dense Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)         │
│  ├─ Token Logits & Perplexity (`gpt2`)                                  │
│  └─ Rule-Based Stance & Contradiction Classifier                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                          DATA PERSISTENCE LAYER                         │
│  ├─ MongoDB Atlas (Motor async driver / PyMongo)                        │
│  ├─ Thread-Safe In-Memory Document & History Store                      │
│  └─ Local FAISS / Vector Index Cache                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Architectural Breakdown

### 2.1 Presentation Layer (Frontend)
- **Technology:** React 19, TypeScript 5.8, Vite 8, TanStack Router, TanStack Query, Tailwind CSS 4, Radix UI primitives.
- **Key Modules:**
  - `src/routes/index.tsx`: Main Evidence Workspace and dashboard statistics.
  - `src/routes/new-verification.tsx`: Interactive single/multi-claim stance verifier.
  - `src/routes/check-answer.tsx`: Detailed LLM answer auditor and hallucination risk evaluator.
  - `src/routes/ask.tsx`: RAG-grounded question-answering assistant with live source citations.
  - `src/routes/uploads.tsx`: File upload, chunk preview, and vector index status manager.
  - `src/routes/history.tsx`: Searchable, filterable audit log of past verifications.
  - `src/routes/graph.tsx`: Interactive Knowledge Graph canvas built on `@xyflow/react`.
  - `src/routes/benchmark.tsx`: Evaluation benchmark dashboard.
- **State Management:** TanStack Query (`@tanstack/react-query`) for asynchronous caching and optimistic updates; React Context (`src/lib/auth-context.tsx`) for session and user authentication.

### 2.2 API Routing & Serialization Layer
- **Technology:** FastAPI, Uvicorn, Pydantic v2 models, Starlette middleware.
- **Key Source Files:**
  - `backend/api/app.py`: Application entry point, lifespan context, router registrations, CORS, database connection lifecycle.
  - `backend/api/routes/verify.py`: Claim verification endpoints (`/api/verify`, `/api/verify/batch`).
  - `backend/api/routes/check_answer.py`: Answer auditing endpoints (`/api/check-answer`).
  - `backend/api/routes/ask.py`: Grounded RAG query endpoint (`/api/ask`).
  - `backend/api/routes/upload.py`: File ingestion, chunking, and document search (`/api/upload`, `/api/documents`).
  - `backend/api/routes/history.py`: History retrieval and deletion endpoints.
  - `backend/api/routes/health.py`: Liveness/readiness probes with DB status detection.

### 2.3 Business Logic & Orchestration Layer
- **Claim Decomposition (`backend/verification/claim_extractor.py`):**
  - Isolates independent propositions from compound/complex sentences using clause boundary detection and syntactic rules.
- **Multi-Source Retrieval (`backend/retrieval/multi_source.py`):**
  - Dispatches parallel queries across Wikipedia API, arXiv search, Semantic Scholar API, and local uploaded indices.
- **Hybrid Search & Reranking (`backend/retrieval/hybrid_search.py`, `backend/retrieval/reranker.py`):**
  - Computes BM25 lexical scores and cosine embedding similarity scores, merges rank lists via Reciprocal Rank Fusion (RRF), and applies Cross-Encoder reranking to retain the top-$K$ most relevant passages.
- **Knowledge Graph Extractor (`backend/verification/kg_extractor.py`):**
  - Extracts subject-predicate-object triples and entity co-occurrence edges to construct directed graph topologies.

### 2.4 AI / ML Model Inference Layer
- **Cross-Encoder NLI (`backend/verification/cross_encoder_verifier.py`):**
  - Loads `cross-encoder/nli-deberta-v3-small` to compute soft probability distribution over `[Contradiction, Entailment, Neutral]`.
- **Semantic Similarity Verifier (`backend/verification/semantic_similarity.py`):**
  - Generates 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2` and computes normalized cosine similarity between claim and retrieved evidence.
- **Token Probability Estimator (`backend/verification/token_probability.py`):**
  - Calculates token-level perplexity, min-probability, and average log-likelihood using `gpt2` to detect high-uncertainty generations.
- **Contradiction Detector (`backend/verification/contradiction_detector.py`):**
  - Rule-based stance engine checking numerical contradictions, negation shifts, temporal inconsistencies, and antonym conflicts.
- **Ensemble Orchestrator (`backend/verification/ensemble.py`):**
  - Calibrates confidence scores using weighted multi-expert voting.

### 2.5 Persistence & Database Layer
- **Primary:** MongoDB Atlas connection managed via Motor (async) and PyMongo.
- **Fallback:** Thread-safe in-memory cache implemented in `backend/api/database.py` (`db_manager`). If `MONGODB_URI` is not configured, the system automatically uses this in-memory fallback without throwing runtime connection errors.
- **Collections / Data Stores:**
  - `verifications`: Stores claim verifications, verdicts, scores, and entity graphs.
  - `answers`: Stores full Q&A sessions, decomposed claims, and citations.
  - `documents`: Stores document metadata, raw text, chunk tokens, and vector embeddings.
  - `users`: Stores user authentication records, hashed credentials, and preferences.

---

## 3. Data Flow & Control Flow

### Verification Data Flow
1. **Request Ingestion:** Client submits `{ "claim": "...", "evidence": "..." }` to `/api/verify`.
2. **Retrieval (if evidence omitted):** Hybrid retriever queries external APIs and local vector index; passes top candidate chunks through Cross-Encoder reranker.
3. **Inference Pipeline:**
   - NLI model computes: $P(\text{Entailment}), P(\text{Contradiction}), P(\text{Neutral})$.
   - Embedding model computes: $\cos(\mathbf{e}_{\text{claim}}, \mathbf{e}_{\text{evidence}})$.
   - Perplexity model computes: $\text{Perplexity}(\text{claim})$.
   - Rule engine evaluates: $\text{Negation/Numerical Stance}$.
4. **Score Fusion:** Computes final confidence score and discrete verdict.
5. **Graph Generation:** Triple extractor converts tokens into `{ nodes, edges }`.
6. **Response & Persistence:** Result returned to client as JSON and asynchronously saved to DB/Memory.

---

## 4. Deployment Architecture

```
                                [Internet]
                                    │
                         ┌──────────▼──────────┐
                         │   Reverse Proxy /   │
                         │   Frontend Host     │
                         │   (Port 8080)       │
                         └──────────┬──────────┘
                                    │ /api/* proxy / direct CORS
                         ┌──────────▼──────────┐
                         │   FastAPI Backend   │
                         │   Uvicorn Server    │
                         │   (Port 8000)       │
                         └────┬───────────┬────┘
                              │           │
           ┌──────────────────▼──┐     ┌──▼──────────────────┐
           │ Local AI Engine     │     │ MongoDB Atlas       │
           │ (PyTorch/DeBERTa)   │     │ (Cloud Cluster /    │
           │ Local Disk Cache    │     │ In-Memory Fallback) │
           └─────────────────────┘     └─────────────────────┘
```

The system is fully portable and runs on local developer workstations or cloud containers (Docker, AWS EC2, GCP Compute Engine).
