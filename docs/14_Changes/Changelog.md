# Project Changelog & Evolution History
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Version History Summary

- **v1.0.0 (Initial Prototype):** Basic single-claim verification script with OpenAI API dependency and simple sentence embeddings.
- **v1.5.0 (Modular Pipeline):** Added local DeBERTa NLI cross-encoder, Wikipedia retrieval, and initial React frontend.
- **v2.0.0 (Current Production Architecture):** Complete multi-tier architecture featuring TanStack Router, React 19, Tailwind CSS 4, hybrid multi-source retrieval (Wikipedia + arXiv + Semantic Scholar), Reciprocal Rank Fusion, token perplexity heuristics, rule-based contradiction filtering, Knowledge Graph extraction (`@xyflow/react`), MongoDB Atlas with thread-safe in-memory fallback, and 51 automated unit/integration tests.

---

## 2. Major Changes Breakdown Matrix

| Change Area | Before (v1.x) | After (v2.0.0) | Impact & Rationale | Evidence / Verification |
| :--- | :--- | :--- | :--- | :--- |
| **API Architecture** | Single script / Flask endpoint | FastAPI async router architecture with lifespan context | High-throughput asynchronous request handling and clean OpenAPI docs | `backend/api/app.py`, `backend/api/routes/*` |
| **Verification Engine** | Single similarity threshold | Multi-expert ensemble (DeBERTa-v3 NLI, MiniLM, GPT-2 PPL, Contradiction Engine) | Massive reduction in false positives; robust handling of numerical and polarity conflicts | `backend/verification/ensemble.py`, `backend/verification/cross_encoder_verifier.py` |
| **Retrieval Engine** | Single-source Wikipedia search | Hybrid sparse-dense retrieval (BM25 + Dense) across Wikipedia, arXiv, and Semantic Scholar | Broader domain coverage for scientific and general queries; RRF rank fusion | `backend/retrieval/multi_source.py`, `backend/retrieval/hybrid_search.py` |
| **Persistence Layer** | Static JSON file storage | MongoDB Atlas with thread-safe in-memory cache fallback | Enterprise cloud database durability with zero-config local developer fallback | `backend/api/database.py` (`db_manager`) |
| **Frontend Framework** | Basic HTML / Plain React | React 19, Vite 8, TanStack Router, Tailwind CSS 4, Motion, Lucide | Modern, fluid, accessible dashboard with real-time UI state management | `frontend/src/*`, `frontend/package.json` |
| **Explainability UI** | Plain text verdict string | Interactive Knowledge Graph (`@xyflow/react`), Confidence Breakdown Bar, Source Badges | Visual entity-relation tracing for research explainability | `frontend/src/routes/graph.tsx`, `frontend/src/components/app/ui-kit.tsx` |
| **Document Ingestion** | No file upload support | Full multi-format file ingestion (PDF, TXT, MD, CSV, DOCX) with 500-token chunking | Grounding against proprietary enterprise documents | `backend/api/routes/upload.py`, `frontend/src/routes/uploads.tsx` |
| **Benchmarking** | Ad-hoc manual prompts | Automated benchmark harness on TruthfulQA, HaluEval, and FEVER | Standardized empirical research evaluation | `backend/evaluation/evaluate.py`, `backend/evaluation/benchmark_datasets.py` |
| **Test Coverage** | 0 automated tests | 51 automated test cases across 6 test modules | Verified 100% pass rate across all core components | `backend/tests/test_*.py` |

---

## 3. Detailed File Additions & Modifications

### Added Backend Modules
- `backend/verification/cross_encoder_verifier.py`: DeBERTa-v3 NLI stance classifier.
- `backend/verification/token_probability.py`: GPT-2 token uncertainty and perplexity calculator.
- `backend/verification/contradiction_detector.py`: Rule-based numerical and negation detector.
- `backend/verification/ensemble.py`: Multi-expert score calibrator.
- `backend/verification/kg_extractor.py`: Dynamic knowledge graph triple parser.
- `backend/retrieval/hybrid_search.py`: BM25 and dense vector rank fusion.
- `backend/retrieval/multi_source.py`: Academic and encyclopedic API integrations.
- `backend/retrieval/reranker.py`: Cross-encoder passage reranker.
- `backend/api/database.py`: Resilient dual-mode database manager.
- `backend/evaluation/evaluate.py`: Standardized evaluation benchmark suite.

### Added Frontend Components & Routes
- `frontend/src/routes/index.tsx`: Evidence Workspace dashboard.
- `frontend/src/routes/new-verification.tsx`: Interactive single-claim verifier.
- `frontend/src/routes/check-answer.tsx`: Multi-claim LLM answer auditor.
- `frontend/src/routes/ask.tsx`: RAG grounded Q&A with live citations.
- `frontend/src/routes/uploads.tsx`: File upload manager and chunk inspector.
- `frontend/src/routes/history.tsx`: Searchable audit logs with filtering.
- `frontend/src/routes/graph.tsx`: React Flow interactive knowledge graph canvas.
- `frontend/src/components/app/ui-kit.tsx`: Accessible UI badges, cards, and confidence meters.
