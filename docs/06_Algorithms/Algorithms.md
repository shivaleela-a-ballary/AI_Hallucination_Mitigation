# Algorithm Specifications
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Overview of System Algorithms

The system implements five core algorithms spanning lexical retrieval, dense ranking, neural natural language inference, token predictive entropy, and score fusion.

| Algorithm | Primary Purpose | Time Complexity | Space Complexity |
| :--- | :--- | :--- | :--- |
| **1. Reciprocal Rank Fusion (RRF)** | Merging multi-source ranking lists | $O(|M| \cdot K)$ | $O(|D|)$ |
| **2. Cross-Encoder NLI Stance Classification** | Directional premise-hypothesis entailment | $O(L^2)$ | $O(L)$ |
| **3. Sliding-Window Text Chunking & Indexing** | Ingesting and partitioning document corpora | $O(N)$ | $O(N)$ |
| **4. Token-Level Predictive Perplexity & Entropy** | Measuring autoregressive model uncertainty | $O(T)$ | $O(T)$ |
| **5. Multi-Expert Calibrated Score Fusion** | Combining ensemble verification signals | $O(E)$ | $O(1)$ |

---

## 2. Detailed Algorithm Specifications

### 2.1 Algorithm 1: Reciprocal Rank Fusion (RRF) for Multi-Source Evidence Retrieval
- **Purpose:** Combines search results from diverse retrieval modalities (BM25 lexical search, dense embedding search, Wikipedia API, arXiv search) without requiring score normalization.
- **Input:** Set of ranked result lists $R = \{r_1, r_2, \dots, r_m\}$, smoothing constant $k = 60$.
- **Output:** Aggregated ranked list of unique passages $D^*$ sorted by RRF score descending.
- **Step-by-Step Process:**
  1. Initialize empty hash map `rrf_scores = {}`.
  2. For each ranked list $r_m \in R$:
     - For each document $d$ at rank index $i \in [1, |r_m|]$:
       - $\text{rrf\_scores}[d] \leftarrow \text{rrf\_scores}[d] + \frac{1}{k + i}$
  3. Sort documents by $\text{rrf\_scores}[d]$ in descending order.
  4. Truncate to top-$K$ candidates ($K=5$).
- **Pseudocode:**
  ```python
  def reciprocal_rank_fusion(ranking_lists: List[List[Document]], k: int = 60) -> List[Document]:
      scores = defaultdict(float)
      doc_map = {}
      for r_list in ranking_lists:
          for rank, doc in enumerate(r_list, start=1):
              scores[doc.id] += 1.0 / (k + rank)
              doc_map[doc.id] = doc
      sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
      return [doc_map[doc_id] for doc_id in sorted_ids]
  ```
- **Complexity:** Time $O(M \cdot K)$ where $M$ is number of retrievers and $K$ is candidate list size; Space $O(|D|)$ where $|D|$ is unique documents.
- **Why Selected:** Robust to disparate score distributions (BM25 vs. cosine similarity) without requiring calibrated temperature scaling.
- **Implementation File:** `backend/retrieval/hybrid_search.py`

---

### 2.2 Algorithm 2: Cross-Encoder NLI Stance Inference
- **Purpose:** Evaluates whether a claim is mathematically entailed by, neutral to, or contradicted by retrieved evidence passages.
- **Input:** Claim string $c$, Evidence string $e$, Max sequence length $L=512$.
- **Output:** Softmax probabilities $[p_{\text{contradiction}}, p_{\text{entailment}}, p_{\text{neutral}}]$ and discrete verdict.
- **Step-by-Step Process:**
  1. Concatenate inputs with special separator tokens: $\mathbf{x} = [\text{CLS}] \circ c \circ [\text{SEP}] \circ e \circ [\text{SEP}]$.
  2. Pass $\mathbf{x}$ through 12-layer DeBERTa-v3 Transformer backbone with disentangled attention.
  3. Extract $[\text{CLS}]$ pooled representation $\mathbf{h} \in \mathbb{R}^{d}$.
  4. Compute linear projection logits: $\mathbf{z} = \mathbf{W}\mathbf{h} + \mathbf{b} \in \mathbb{R}^3$.
  5. Apply softmax: $\mathbf{p} = \text{softmax}(\mathbf{z})$.
  6. Return verdict: $\arg\max(\mathbf{p})$.
- **Pseudocode:**
  ```python
  def predict_stance(claim: str, evidence: str, model, tokenizer):
      inputs = tokenizer(claim, evidence, return_tensors="pt", truncation=True, max_length=512)
      with torch.no_grad():
          logits = model(**inputs).logits
          probs = torch.softmax(logits, dim=-1).squeeze().tolist()
      # Label mapping: 0: Contradiction, 1: Entailment, 2: Neutral
      p_contra, p_entail, p_neut = probs[0], probs[1], probs[2]
      if p_contra >= 0.50:
          verdict = "REFUTED"
      elif p_entail >= 0.60:
          verdict = "SUPPORTED"
      else:
          verdict = "UNCERTAIN"
      return {"verdict": verdict, "probs": {"entailment": p_entail, "contradiction": p_contra, "neutral": p_neut}}
  ```
- **Complexity:** Time $O(L^2 \cdot d)$ due to all-to-all cross-attention; Space $O(L \cdot d)$.
- **Implementation File:** `backend/verification/cross_encoder_verifier.py`

---

### 2.3 Algorithm 3: Overlapping Sliding-Window Text Ingestion
- **Purpose:** Partitions raw documents (PDF, TXT, MD) into coherent semantic chunks preserving boundary context.
- **Input:** Document token sequence $T = [t_1, t_2, \dots, t_N]$, window size $W=500$, step size $S=450$ (overlap 50).
- **Output:** Array of chunks $C = [c_1, c_2, \dots, c_m]$.
- **Step-by-Step Process:**
  1. Tokenize document text into word/subword tokens.
  2. Iterate $i$ from $0$ to $N$ with step increment $S$:
     - Extract slice $T[i : i+W]$.
     - Detokenize slice into clean string.
     - Append to chunk list with metadata `{ doc_id, chunk_index, start_token, end_token }`.
  3. Batch-encode all chunks into dense embedding vectors via `all-MiniLM-L6-v2`.
- **Complexity:** Time $O(N)$; Space $O(N)$.
- **Implementation File:** `backend/api/routes/upload.py`

---

### 2.4 Algorithm 4: Token-Level Predictive Perplexity & Uncertainty
- **Purpose:** Estimates internal model generation uncertainty without requiring external ground truth.
- **Input:** Generated text string $X = [w_1, w_2, \dots, w_T]$.
- **Output:** Sequence Perplexity $\text{PPL}(X)$, Mean Log-Likelihood $\mathcal{L}$, Min Token Probability $p_{\min}$.
- **Step-by-Step Process:**
  1. Tokenize $X$ into input IDs $\mathbf{x} \in \mathbb{R}^T$.
  2. Compute forward pass through GPT-2 causal language model:
     $$\mathbf{z}_t = f_{\text{LLM}}(\mathbf{x}_{<t}) \quad \forall t \in [1, T]$$
  3. Compute token log-probabilities: $\log P(w_t \mid w_{<t}) = \log \text{softmax}(\mathbf{z}_t)[w_t]$.
  4. Compute negative log-likelihood loss: $\text{NLL} = -\frac{1}{T} \sum_{t=1}^T \log P(w_t \mid w_{<t})$.
  5. Compute Perplexity: $\text{PPL} = \exp(\text{NLL})$.
  6. Compute min probability: $p_{\min} = \min_t P(w_t \mid w_{<t})$.
- **Complexity:** Time $O(T)$; Space $O(T)$.
- **Implementation File:** `backend/verification/token_probability.py`

---

### 2.5 Algorithm 5: Multi-Expert Calibrated Score Fusion
- **Purpose:** Produces a single calibrated confidence score from heterogeneous verification heads.
- **Input:**
  - NLI entailment probability $p_{\text{entail}} \in [0, 1]$
  - NLI contradiction probability $p_{\text{contra}} \in [0, 1]$
  - Semantic cosine similarity $s_{\text{sim}} \in [0, 1]$
  - Normalized token uncertainty $u_{\text{token}} \in [0, 1]$
  - Rule contradiction flag $b_{\text{contra}} \in \{0, 1\}$
- **Output:** Final Confidence $C \in [0, 1]$ and Final Verdict $V \in \{\text{SUPPORTED}, \text{REFUTED}, \text{UNCERTAIN}\}$.
- **Step-by-Step Process:**
  1. If $b_{\text{contra}} == 1$ or $p_{\text{contra}} \ge 0.50$:
     - Return $V = \text{REFUTED}$, $C = \max(p_{\text{contra}}, 0.85)$.
  2. Else:
     - Compute weighted confidence:
       $$C = 0.55 \cdot p_{\text{entail}} + 0.30 \cdot s_{\text{sim}} + 0.15 \cdot (1.0 - u_{\text{token}})$$
     - If $C \ge 0.70$ and $p_{\text{entail}} \ge 0.55$:
       - Return $V = \text{SUPPORTED}$, $C = C$.
     - Else:
       - Return $V = \text{UNCERTAIN}$, $C = C$.
- **Complexity:** Time $O(1)$; Space $O(1)$.
- **Implementation File:** `backend/verification/ensemble.py`
