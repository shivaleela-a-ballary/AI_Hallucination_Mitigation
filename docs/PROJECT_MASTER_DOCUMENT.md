# Project Master Document: AI Hallucination Mitigation System
### Comprehensive Technical Reference & Single Source of Truth
**System Version:** 2.0.0 | **Build Status:** Passing (51/51 Tests) | **Deployment:** Active

---

## Table of Contents
1. [Project Identity & Overview](#1-project-identity--overview)
2. [Problem Statement & Motivation](#2-problem-statement--motivation)
3. [Project Objectives](#3-project-objectives)
4. [Scope & Target Users](#4-scope--target-users)
5. [Software Requirements Summary (SRS)](#5-software-requirements-summary-srs)
6. [Technology Stack](#6-technology-stack)
7. [System Architecture](#7-system-architecture)
8. [Core Modules Breakdown](#8-core-modules-breakdown)
9. [Data & Control Flow](#9-data--control-flow)
10. [Core Algorithms & Complexity](#10-core-algorithms--complexity)
11. [AI & Neural Models](#11-ai--neural-models)
12. [Data Sources & Ingestion](#12-data-sources--ingestion)
13. [API Interface Specifications](#13-api-interface-specifications)
14. [Database & Persistence Architecture](#14-database--persistence-architecture)
15. [Security & AI Safety Posture](#15-security--ai-safety-posture)
16. [Hallucination Detection Methodology](#16-hallucination-detection-methodology)
17. [Hallucination Mitigation Pipeline](#17-hallucination-mitigation-pipeline)
18. [Testing & Quality Assurance](#18-testing--quality-assurance)
19. [Experimental Evaluation Framework](#19-experimental-evaluation-framework)
20. [Current Empirical Results & Benchmarks](#20-current-empirical-results--benchmarks)
21. [Project Evolution & Major Changes](#21-project-evolution--major-changes)
22. [Formal Research Problem & Questions](#22-formal-research-problem--questions)
23. [Research Gap Analysis](#23-research-gap-analysis)
24. [Potential Research Contributions](#24-potential-research-contributions)
25. [System Limitations](#25-system-limitations)
26. [Future Development Roadmap](#26-future-development-roadmap)
27. [Research Paper Structure & Reference Map](#27-research-paper-structure--reference-map)

---

## 1. Project Identity & Overview
- **System Name:** Multi-Stage AI Hallucination Detection and Grounding Mitigation System
- **Repository:** `AI_Hallucination_Mitigation`
- **Core Purpose:** Detect, quantify, and mitigate intrinsic and extrinsic factual hallucinations in Large Language Model outputs through atomic claim decomposition, hybrid multi-source retrieval (Wikipedia, arXiv, Semantic Scholar, Local PDF/TXT), cross-encoder Natural Language Inference (DeBERTa-v3), token predictive uncertainty heuristics (GPT-2), rule-based contradiction filtering, and dynamic knowledge graph generation.
- **Detailed Document:** [`docs/01_Project_Overview/Project_Overview.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/01_Project_Overview/Project_Overview.md)

---

## 2. Problem Statement & Motivation
Autoregressive language models predict next tokens based on statistical distribution rather than grounded world truth. This causes two dangerous failure modes:
1. **Intrinsic Hallucinations:** Direct factual contradictions of provided context.
2. **Extrinsic Hallucinations:** Introduction of unverifiable assertions ungrounded in real-world sources.

Contemporary mitigation techniques rely heavily on "LLM-as-a-Judge", which introduces circular hallucination risks, sycophancy, high financial costs, and opacity. This project delivers a transparent, lightweight, multi-expert grounding architecture that operates on consumer hardware in real time.

---

## 3. Project Objectives
1. Build an end-to-end automated pipeline to extract atomic propositions and evaluate factual consistency.
2. Unify sparse BM25 and dense semantic retrieval across open academic/encyclopedic repositories and local document corpora using Reciprocal Rank Fusion (RRF).
3. Combine deep cross-attention NLI, token-level perplexity heuristics, semantic vector distance, and symbolic contradiction rules into a calibrated consensus score.
4. Render interactive Knowledge Graphs for human-in-the-loop explainability.
5. Provide enterprise-grade resilience via MongoDB Atlas with zero-config thread-safe in-memory fallback.

---

## 4. Scope & Target Users
- **Target Users:** Academic researchers, enterprise knowledge workers, journalists, fact-checkers, and NLP practitioners.
- **Scope:** Real-time claim verification, multi-claim LLM answer auditing, grounded RAG question-answering with citations, document corpus management, and benchmark evaluation.

---

## 5. Software Requirements Summary (SRS)
- **Functional Requirements:** `FR-01` (Claim Stance Verification), `FR-02` (Answer Fact-Checking), `FR-03` (Grounded RAG Q&A), `FR-04` (Document Upload & 500-Token Chunking), `FR-05` (Knowledge Graph Generation), `FR-06` (History CRUD), `FR-07` (Benchmark Runner).
- **Non-Functional Requirements:** Sub-1.5s single-claim inference latency, 100% test pass rate across 51 scenarios, zero hardcoded credentials, WCAG AA UI accessibility.
- **Detailed Document:** [`docs/02_SRS/SRS.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/02_SRS/SRS.md)

---

## 6. Technology Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, PyTorch, Transformers, Sentence-Transformers, Rank-BM25, FAISS, PyPDF2, Motor, PyMongo.
- **Frontend:** React 19, TypeScript 5.8, Vite 8, TanStack Router, TanStack Query, Tailwind CSS 4, Radix UI, Motion, `@xyflow/react`.
- **Testing & Benchmarks:** Pytest, HTTPX, TruthfulQA, HaluEval, FEVER.

---

## 7. System Architecture
The system adopts a decoupled, multi-tier asynchronous architecture:
- **Presentation Layer:** React 19 SPA running on port `8080`.
- **API Routing Layer:** FastAPI gateway on port `8000` with lifespan management.
- **Orchestration Layer:** Claim decomposition, multi-source retrieval, RRF, reranking, and knowledge graph extraction.
- **AI/ML Inference Layer:** Lazy-loaded singletons for DeBERTa-v3 NLI, MiniLM embeddings, and GPT-2 token logits.
- **Persistence Layer:** Dual-mode database manager (MongoDB Atlas primary, Thread-safe in-memory fallback).
- **Detailed Document:** [`docs/03_Architecture/System_Architecture.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/System_Architecture.md)
- **Mermaid Diagrams:**
  - High Level Architecture: [`docs/03_Architecture/High_Level_Architecture.mmd`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/High_Level_Architecture.mmd)
  - Component Diagram: [`docs/03_Architecture/Component_Diagram.mmd`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/Component_Diagram.mmd)
  - Sequence Diagram: [`docs/03_Architecture/Sequence_Diagram.mmd`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/Sequence_Diagram.mmd)
  - Data Flow Diagram: [`docs/03_Architecture/Data_Flow_Diagram.mmd`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/Data_Flow_Diagram.mmd)
  - Deployment Diagram: [`docs/03_Architecture/Deployment_Diagram.mmd`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/Deployment_Diagram.mmd)
  - AI Pipeline Diagram: [`docs/03_Architecture/AI_Pipeline.mmd`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/03_Architecture/AI_Pipeline.mmd)

---

## 8. Core Modules Breakdown
- `verification/cross_encoder_verifier.py`: DeBERTa-v3 3-class NLI stance classifier.
- `verification/token_probability.py`: GPT-2 token likelihood and perplexity calculator.
- `verification/semantic_similarity.py`: Dense cosine similarity verifier.
- `verification/contradiction_detector.py`: Symbolic numerical, temporal, and polarity conflict filter.
- `verification/ensemble.py`: Calibrated multi-expert consensus scorer.
- `retrieval/multi_source.py`: Wikipedia, arXiv, and Semantic Scholar query orchestrator.
- `retrieval/hybrid_search.py`: BM25 + dense embedding hybrid search with RRF.
- `api/database.py`: Dual-mode database manager.
- **Detailed Document:** [`docs/04_Modules/Module_Documentation.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/04_Modules/Module_Documentation.md)

---

## 9. Data & Control Flow
1. **Input Ingestion:** User query or text submitted via API/UI.
2. **Decomposition:** Text split into atomic claims $[c_1, c_2, \dots, c_n]$.
3. **Retrieval & Fusion:** Hybrid BM25 and dense retrieval across 4 sources merged via RRF.
4. **Multi-Head Verification:** Parallel execution of NLI, token uncertainty, semantic similarity, and contradiction logic.
5. **Calibrated Verdict:** Weighted score calculation and abstention gating.
6. **Graph & Citation Generation:** Node-edge extraction and response delivery.

---

## 10. Core Algorithms & Complexity
1. **Reciprocal Rank Fusion (RRF):** $\text{Score}(d) = \sum_{m} \frac{1}{60 + r_m(d)}$ ($O(|M| \cdot K)$).
2. **Cross-Encoder NLI Inference:** All-to-all cross-attention classification ($O(L^2)$).
3. **Sliding-Window Document Chunking:** 500-token windows with 50-token overlap ($O(N)$).
4. **Token Perplexity Calculation:** Sequence negative log-likelihood $\text{PPL} = \exp(-\frac{1}{T}\sum \log P)$ ($O(T)$).
5. **Multi-Expert Calibrated Fusion:** Dynamic thresholding and rule overriding ($O(1)$).
- **Detailed Document:** [`docs/06_Algorithms/Algorithms.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/06_Algorithms/Algorithms.md)

---

## 11. AI & Neural Models
- **`cross-encoder/nli-deberta-v3-small` (141M params):** Disentangled attention NLI model for premise-hypothesis classification.
- **`sentence-transformers/all-MiniLM-L6-v2` (22.7M params):** 384-dimensional dense semantic embedding model.
- **`gpt2` (124M params):** Causal language model for predictive token likelihoods and perplexity.
- **`BM25Okapi`:** Lexical keyword search algorithm.
- **Detailed Document:** [`docs/07_AI_Models/Models.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/07_AI_Models/Models.md)

---

## 12. Data Sources & Ingestion
- **External Real-Time APIs:** Wikipedia REST API, arXiv Query API, Semantic Scholar Academic Graph.
- **User Document Ingestion:** Multi-format parser (PDF, TXT, MD, CSV, DOCX) with 500-token chunking and FAISS/dense indexing.
- **Research Benchmarks:** Curated subsets of TruthfulQA, HaluEval, and FEVER.
- **Detailed Document:** [`docs/08_Data/Dataset_Documentation.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/08_Data/Dataset_Documentation.md)

---

## 13. API Interface Specifications
- Base URL: `http://127.0.0.1:8000` | OpenAPI Console: `/docs` | ReDoc: `/redoc`
- Primary Routes: `/api/verify`, `/api/verify/batch`, `/api/check-answer`, `/api/ask`, `/api/upload`, `/api/documents`, `/api/history`, `/api/health`.
- **Detailed Document:** [`docs/09_APIs/API_Documentation.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/09_APIs/API_Documentation.md)

---

## 14. Database & Persistence Architecture
- **Dual-Mode Strategy:** Primary connection to cloud MongoDB Atlas; automatic seamless fallback to thread-safe in-memory cache if `MONGODB_URI` is unconfigured.
- **Collections:** `verifications`, `answers`, `documents`, `users`.
- **Detailed Document:** [`docs/10_Database/Database_Documentation.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/10_Database/Database_Documentation.md)

---

## 15. Security & AI Safety Posture
- **Application Security:** Pydantic v2 type enforcement, file upload path sanitization, bcrypt password hashing, zero hardcoded API secrets.
- **AI Safety:** Discriminant NLI classification immune to prompt injection, multi-source consensus against retrieval poisoning, rule-based numerical contradiction overrides, and conservative abstention policies.
- **Detailed Document:** [`docs/11_Security/Security.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/11_Security/Security.md)

---

## 16. Hallucination Detection Methodology
- Atomic proposition splitting isolates individual false statements.
- Stance evaluation categorizes claims into `SUPPORTED`, `REFUTED`, or `UNCERTAIN`.
- Token predictive entropy flags low-probability generated tokens before human review.
- **Detailed Document:** [`docs/05_Hallucination_Mitigation/Methodology.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/05_Hallucination_Mitigation/Methodology.md)

---

## 17. Hallucination Mitigation Pipeline
- Evidence-grounded synthesis constrains generated text to retrieved citations.
- Conservative abstention threshold ($\tau = 0.35$) declines answering ungroundable questions.
- Post-hoc auditing flags and explains specific contradiction clauses with evidence links.

---

## 18. Testing & Quality Assurance
- **Coverage:** 51 automated test cases across 6 test modules (`test_app.py`, `test_verification.py`, `test_retrieval.py`, `test_uploads_api.py`, `test_six_scenarios.py`, `test_database.py`).
- **Pass Rate:** 100% (51 passed in ~7.5 seconds).
- **TypeScript Quality:** 0 compiler errors on `npx tsc --noEmit`.
- **Detailed Document:** [`docs/12_Testing/Testing.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/12_Testing/Testing.md)

---

## 19. Experimental Evaluation Framework
- Dedicated research harness (`backend/evaluation/evaluate.py`).
- Standard metrics: Precision, Recall, Macro-F1, Hallucination Reduction Rate ($\Delta\text{HR}$), and Wall-Clock Latency.
- **Detailed Document:** [`docs/13_Evaluation/Experiments.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/13_Evaluation/Experiments.md)

---

## 20. Current Empirical Results & Benchmarks
- Full test pass rate confirming end-to-end functionality across scientific, historical, numerical, mixed, and ungroundable claims.
- Sub-second average latency ($< 1.2\text{s}$) on 4-core CPU hardware.

---

## 21. Project Evolution & Major Changes
- Evolution from initial single-threshold script to multi-tier enterprise architecture with hybrid retrieval, multi-expert consensus, React 19 frontend, and automated benchmarking.
- **Detailed Document:** [`docs/14_Changes/Changelog.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/14_Changes/Changelog.md)

---

## 22. Formal Research Problem & Questions
- Formalizes real-time hallucination mitigation as a joint optimization problem over evidence entailment, token entropy, and multi-source consensus.
- RQs address claim decomposition, hybrid retrieval gain, uncertainty calibration, and symbolic contradiction detection.
- **Detailed Document:** [`docs/15_Research/Research_Problem.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/15_Research/Research_Problem.md)

---

## 23. Research Gap Analysis
- Identifies critical weaknesses in black-box "LLM-as-a-Judge" and naive single-source dense RAG.
- Demonstrates how combining RRF multi-source retrieval with cross-encoder NLI and symbolic filters bridges the gap.
- **Detailed Document:** [`docs/15_Research/Research_Gap.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/15_Research/Research_Gap.md)

---

## 24. Potential Research Contributions
1. A multi-expert calibrated stance detection pipeline combining NLI with white-box token logits and symbolic rules.
2. A heterogeneous multi-source retrieval architecture linking encyclopedic and academic graphs.
3. An explainable visual knowledge graph generator operating synchronously with claim verification.

---

## 25. System Limitations
- CPU-bound cross-encoder latency on large document batches.
- External API rate limits on unauthenticated Semantic Scholar requests.
- English-only language scope in current embedding models.

---

## 26. Future Development Roadmap
1. **GPU Acceleration:** INT8/FP16 TensorRT quantization for sub-100ms inference.
2. **Graph Neural Networks (GNN):** Relational GNN layers for global multi-hop factual consistency scoring.
3. **Continuous Agentic Self-Healing:** Autonomous feedback loop directly rewriting flagged clauses during streaming generation.

---

## 27. Research Paper Structure & Reference Map
- Complete section-by-section writing blueprint, title proposals, and literature search strategy.
- **Detailed Document:** [`docs/16_Research_Paper/Research_Paper_Content_Map.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/16_Research_Paper/Research_Paper_Content_Map.md)
- **Literature Map:** [`docs/15_Research/Research_Paper_Map.md`](file:///c:/Users/HP/OneDrive/Documents/Final_Year_Project/AI_Hallucination_Mitigation-1/docs/15_Research/Research_Paper_Map.md)
