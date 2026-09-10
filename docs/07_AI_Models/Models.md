# AI Models Documentation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Model Summary & Comparison Matrix

| Model Identifier | Provider / Source | Parameters | Embedding Dim / Hidden Size | Primary Role | Inference Device |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`cross-encoder/nli-deberta-v3-small`** | Microsoft / Hugging Face | 141M | 768 | Stance Detection (NLI) | CPU / CUDA |
| **`sentence-transformers/all-MiniLM-L6-v2`** | sentence-transformers | 22.7M | 384 | Dense Semantic Retrieval & Cosine Similarity | CPU / CUDA |
| **`gpt2`** | OpenAI / Hugging Face | 124M | 768 | Token Logits & Uncertainty Estimation | CPU / CUDA |
| **`BM25Okapi`** | `rank-bm25` | N/A (Algorithmic) | Lexical vocabulary | Sparse Keyword Search | CPU |
| **Rule-Based Contradiction Engine** | Custom In-House | N/A (Heuristic) | N/A | Numerical & Polarity Contradiction Check | CPU |

---

## 2. Detailed Model Specifications

### 2.1 Model 1: DeBERTa-v3 Small NLI (`cross-encoder/nli-deberta-v3-small`)
- **Model Family:** Decoding-enhanced BERT with Disentangled Attention (DeBERTa-v3).
- **Provider / Repository:** Hugging Face Hub (`cross-encoder/nli-deberta-v3-small`).
- **Primary Function:** Deep textual entailment verification between premise evidence and hypothesis claim.
- **Architecture:** 12 Transformer layers, 768 hidden dimension, 12 attention heads, relative position encoding via disentangled matrices ($P_{content|pos} + P_{pos|content}$).
- **Parameter Count:** ~141 Million parameters.
- **Input Representation:** Tokenized pair `[CLS] Hypothesis [SEP] Premise [SEP]` (max length 512).
- **Output Representation:** 3-class classification logits projected via softmax:
  $$\mathbf{p} = [P(\text{Contradiction}), P(\text{Entailment}), P(\text{Neutral})]$$
- **Where Used:** `backend/verification/cross_encoder_verifier.py`.
- **Strengths:** Disentangled attention captures nuanced grammatical dependencies and negation scopes far superior to standard BERT or RoBERTa.
- **Limitations:** Quadratic inference time on long context windows; requires pre-caching weights (~280MB).

---

### 2.2 Model 2: All-MiniLM-L6-v2 (`sentence-transformers/all-MiniLM-L6-v2`)
- **Model Family:** Sentence-Transformers (Knowledge-distilled MiniLM).
- **Provider / Repository:** Hugging Face Hub (`sentence-transformers/all-MiniLM-L6-v2`).
- **Primary Function:** Semantic vector representation, passage indexing, dense retrieval, and cosine similarity.
- **Architecture:** 6 Transformer layers, 384 hidden dimension, 12 attention heads, mean-pooling over output token embeddings.
- **Parameter Count:** ~22.7 Million parameters.
- **Input Representation:** Cleaned text string (max length 256/512 tokens).
- **Output Representation:** 384-dimensional $L_2$-normalized vector $\mathbf{v} \in \mathbb{R}^{384}$.
- **Where Used:** `backend/retrieval/hybrid_search.py`, `backend/verification/semantic_similarity.py`, `backend/api/routes/upload.py`.
- **Strengths:** Ultra-fast embedding generation (~15ms on CPU per sentence), low memory footprint (~90MB), strong semantic transfer on MTEB benchmarks.
- **Limitations:** May miss exact keyword matches (e.g., specific part numbers or rare acronyms) which is why it is paired with BM25.

---

### 2.3 Model 3: GPT-2 (`gpt2` Base)
- **Model Family:** Autoregressive Generative Pre-trained Transformer.
- **Provider / Repository:** Hugging Face Hub (`gpt2`).
- **Primary Function:** Internal generation confidence estimation, token predictive entropy, and perplexity calculation.
- **Architecture:** 12 decoder-only Transformer layers with masked multi-head self-attention, 768 hidden dimension.
- **Parameter Count:** ~124 Million parameters.
- **Input Representation:** Tokenized sequence with Byte-Pair Encoding (BPE).
- **Output Representation:** Vocabulary logits $\mathbf{z}_t \in \mathbb{R}^{50257}$ across sequence length $T$.
- **Where Used:** `backend/verification/token_probability.py`.
- **Strengths:** Provides white-box access to raw token probabilities without requiring API tokens or cloud subscriptions.
- **Limitations:** Base GPT-2 pre-training corpus reflects older web text (WebText); serves as an uncertainty proxy rather than a world knowledge oracle.

---

### 2.4 Model 4: BM25 Lexical Model (`BM25Okapi`)
- **Provider / Library:** `rank-bm25` (Python).
- **Primary Function:** Exact term matching, keyword frequency scoring, document term saturation.
- **Mathematical Formulation:**
  $$\text{Score}(D, Q) = \sum_{q \in Q} \text{IDF}(q) \cdot \frac{f(q, D) \cdot (k_1 + 1)}{f(q, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
  with standard hyperparameters $k_1 = 1.5, b = 0.75$.
- **Where Used:** `backend/retrieval/bm25_retriever.py`, `backend/retrieval/hybrid_search.py`.
- **Strengths:** Fast lexical lookup, zero GPU requirements, highly effective for proper nouns, dates, and domain-specific terminology.

---

## 3. Model Orchestration & Lazy Loading Strategy

To ensure rapid startup and prevent unnecessary memory allocation, neural models are loaded via a **Thread-Safe Lazy Singleton Pattern**:
1. Upon server boot (`uvicorn api.app:app`), the lightweight FastAPI endpoints initialize in $< 500\text{ms}$.
2. On the first incoming verification or retrieval request, the corresponding singleton loads weights into memory and caches the initialized model instance.
3. If internet connectivity to Hugging Face Hub is interrupted, models load from the local cache directory (`~/.cache/huggingface/hub`).
