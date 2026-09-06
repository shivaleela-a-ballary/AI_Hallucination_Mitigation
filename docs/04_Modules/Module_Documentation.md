# Module Documentation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Module Dependency Matrix

| Module Name | Layer | Depends On | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **API Gateway & App** | Routing | All Services, Database | HTTP request handling, lifespan, CORS, error middleware |
| **Claim Extractor** | NLP Processing | `re`, `nltk`/tokenizers | Deconstruct multi-sentence text into atomic propositions |
| **Multi-Source Retriever** | Information Retrieval | `requests`, `urllib`, Vector Store | Fetch relevant passages from Wikipedia, arXiv, Semantic Scholar |
| **Hybrid Search & Reranker**| Information Retrieval | `rank-bm25`, `sentence-transformers` | Lexical + semantic retrieval with Reciprocal Rank Fusion |
| **Cross-Encoder Verifier** | AI/ML Verification | `transformers`, `torch`, DeBERTa-v3 | 3-class NLI stance inference (Entailment/Contradiction/Neutral) |
| **Token Probability Engine** | AI/ML Uncertainty | `transformers`, `gpt2` | Log-likelihood, perplexity, and token uncertainty metrics |
| **Semantic Similarity** | AI/ML Verification | `sentence-transformers` | Cosine similarity scoring between claims and evidence chunks |
| **Contradiction Detector** | Rule Engine | Regex, Negation patterns | Hard logic filtering for numbers, dates, antonyms, negations |
| **Ensemble Evaluator** | Orchestration | All Verification Modules | Calibrated score fusion and multi-expert consensus |
| **Knowledge Graph Builder** | Graph Analytics | Regex, String parsing | Extract entity nodes and relationship edges for UI |
| **Database Manager** | Persistence | `motor`, `pymongo`, In-Memory | Resilient dual-mode data storage and CRUD operations |
| **Evaluation Suite** | Benchmarking | All verification modules | Run automated experiments on TruthfulQA/HaluEval/FEVER |

---

## 2. Detailed Module Specifications

### 2.1 Module: `verification.cross_encoder_verifier`
- **Purpose:** Primary stance detection head using deep pre-trained Natural Language Inference.
- **Responsibilities:**
  - Tokenize `[Premise, Hypothesis]` pairs.
  - Compute softmax probability distribution over `[Contradiction, Entailment, Neutral]`.
  - Handle out-of-vocabulary terms and long text truncations (max sequence length 512).
- **Files & Classes:**
  - File: `backend/verification/cross_encoder_verifier.py`
  - Class: `CrossEncoderVerifier`
  - Key Methods: `predict_stance(claim, evidence)`, `get_entailment_score(claim, evidence)`, `batch_verify(pairs)`.
- **Inputs:** `claim` (str), `evidence` (str).
- **Outputs:** Dict `{ "verdict": str, "scores": { "entailment": float, "contradiction": float, "neutral": float }, "confidence": float }`.
- **Error Handling:** Gracefully catches Hugging Face Hub offline errors; initializes lazily on first request.
- **Limitations:** Higher computational cost on CPU compared to lightweight lexical matching.

### 2.2 Module: `verification.token_probability`
- **Purpose:** Quantifies model-internal generation confidence and token predictive uncertainty.
- **Responsibilities:**
  - Calculate token-level log probabilities using autoregressive logits (`gpt2`).
  - Calculate sequence perplexity: $\text{PPL}(W) = \exp\left(-\frac{1}{N} \sum_{i=1}^N \log P(w_i \mid w_{<i})\right)$.
  - Identify low-confidence "hallucination hotspot" tokens (tokens with probability $< 0.15$).
- **Files & Classes:**
  - File: `backend/verification/token_probability.py`
  - Class: `TokenProbabilityEstimator`
  - Key Methods: `compute_token_probabilities(text)`, `get_uncertainty_score(text)`.
- **Inputs:** `text` (str).
- **Outputs:** Dict `{ "mean_log_prob": float, "perplexity": float, "min_token_prob": float, "uncertainty_score": float }`.
- **Error Handling:** Truncates input exceeding model maximum position embeddings (1024 tokens).

### 2.3 Module: `verification.semantic_similarity`
- **Purpose:** Computes continuous semantic distance in dense embedding space.
- **Responsibilities:**
  - Map claim and evidence passages to 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`.
  - Compute normalized cosine similarity: $\cos(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$.
- **Files & Classes:**
  - File: `backend/verification/semantic_similarity.py`
  - Class: `SemanticSimilarityVerifier`
  - Key Methods: `compute_similarity(claim, evidence)`, `batch_similarity(claims, evidences)`.
- **Inputs:** `claim` (str), `evidence` (str).
- **Outputs:** Dict `{ "similarity_score": float, "is_similar": bool }`.
- **Error Handling:** Returns default similarity $0.0$ if input text is empty or blank.

### 2.4 Module: `verification.contradiction_detector`
- **Purpose:** High-precision symbolic and pattern-based rule engine to catch blatant factual contradictions.
- **Responsibilities:**
  - Extract numbers, percentages, dates, and currency values.
  - Detect negation polarity flips (e.g., "did not discover" vs. "discovered").
  - Detect antonym pairs and directional opposites (e.g., "increased" vs. "decreased").
- **Files & Classes:**
  - File: `backend/verification/contradiction_detector.py`
  - Class: `ContradictionDetector`
  - Key Methods: `detect_contradiction(claim, evidence)`, `extract_numeric_entities(text)`.
- **Inputs:** `claim` (str), `evidence` (str).
- **Outputs:** Dict `{ "is_contradiction": bool, "reason": str, "contradiction_type": str }`.

### 2.5 Module: `retrieval.multi_source` & `retrieval.hybrid_search`
- **Purpose:** Aggregates and ranks evidence from heterogeneous sources.
- **Responsibilities:**
  - Query Wikipedia search and summary REST APIs.
  - Query arXiv open-access API for scientific preprints.
  - Query Semantic Scholar Academic Graph API for peer-reviewed papers.
  - Query local document index (PDF, TXT, MD).
  - Fuse rankings via Reciprocal Rank Fusion (RRF): $\text{RRF\_Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$.
- **Files & Classes:**
  - Files: `backend/retrieval/multi_source.py`, `backend/retrieval/hybrid_search.py`, `backend/retrieval/reranker.py`
  - Classes: `MultiSourceRetriever`, `HybridRetriever`, `PassageReranker`
  - Key Methods: `retrieve_all(query, top_k)`, `fuse_rankings(bm25_hits, dense_hits)`.
- **Error Handling:** Catches HTTP 429 rate limits, network timeouts, and malformed XML/JSON responses without failing parent query.

### 2.6 Module: `api.database`
- **Purpose:** Resilient data management supporting both production database clusters and zero-config local development.
- **Responsibilities:**
  - Manage async connection pool to MongoDB Atlas via Motor.
  - Maintain thread-safe in-memory collections (`verifications`, `answers`, `documents`, `users`) with locks.
  - Provide uniform CRUD interface regardless of active storage backend.
- **Files & Classes:**
  - File: `backend/api/database.py`
  - Class: `DatabaseManager` (`db_manager`)
  - Key Methods: `connect()`, `disconnect()`, `save_verification(data)`, `get_verifications(limit, skip)`, `save_document(doc)`, `delete_verification(id)`.
- **Error Handling:** Emits informative startup warning if `MONGODB_URI` is unconfigured and switches to in-memory mode silently.

### 2.7 Module: `api.services.rag_pipeline`
- **Purpose:** End-to-end evidence-grounded question answering and fact-auditing pipeline.
- **Responsibilities:**
  - Orchestrate retrieval, context construction, answer synthesis, citation matching, and post-generation verification.
  - Calculate hallucination risk metric: $\text{HR} = 1.0 - \text{Grounding\_Score}$.
  - Support strict abstention when evidence is insufficient.
- **Files & Classes:**
  - File: `backend/api/services/rag_pipeline.py`
  - Class: `RAGPipeline`
  - Key Methods: `answer_query(query)`, `audit_answer(answer, context)`.
