# Hallucination Mitigation Methodology
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Fundamentals of AI Hallucination

### 1.1 Definition
In Natural Language Processing, **AI Hallucination** refers to the phenomenon where a generative language model produces text that is grammatically correct and semantically fluent, but factually false, unfaithful to provided source material, or unsubstantiated by real-world knowledge.

### 1.2 Root Causes of Hallucination in LLMs
1. **Statistical Autoregression Objective:** LLMs are trained via Maximum Likelihood Estimation (MLE) on next-token prediction ($\arg\max_\theta \sum_t \log P(w_t \mid w_{<t})$), which rewards superficial token co-occurrence probabilities rather than underlying factual consistency.
2. **Knowledge Cutoffs & Parametric Decay:** Factual knowledge is compressed into static weights during pre-training, leading to outdated, incomplete, or fuzzy representations.
3. **Imperfect Decoding Strategies:** High sampling temperature ($T > 0.7$) or top-$p$ nucleus sampling can force the generator into low-probability factual trajectories.
4. **Context Misattribution & Distractor Noise:** In RAG architectures, irrelevant or noisy retrieved passages can trigger context misinterpretation.

### 1.3 Typology of Hallucinations
- **Intrinsic Hallucinations:** Direct contradictions of the given premise or reference evidence (e.g., source states "Born in 1950", model generates "Born in 1980").
- **Extrinsic Hallucinations:** Introduction of unverifiable assertions that neither contradict nor follow from the source evidence (e.g., source discusses a book's release, model invents an unmentioned awards list).
- **Faithfulness Hallucinations:** Divergence between generated output and input prompt constraints in conditional tasks (summarization, translation).
- **Factuality Hallucinations:** Discrepancy between generated assertions and consensus world knowledge.

---

## 2. The Multi-Stage Mitigation Pipeline

Our system employs a six-stage hybrid mitigation architecture:

```
                  ┌─────────────────────────────────────┐
                  │          1. User Input              │
                  │  (Claim / Question / LLM Answer)    │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │    2. Atomic Claim Decomposition    │
                  │ (Regex & Syntactic Clause Splitting)│
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 3. Multi-Source Hybrid Retrieval    │
                  │ (BM25 + all-MiniLM-L6-v2 Embeddings)│
                  │ (Wikipedia, arXiv, Semantic Scholar)│
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │ 4. Reciprocal Rank Fusion & Rerank  │
                  │ (Cross-Encoder Passage Selection)   │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │  5. Multi-Expert Stance Inference   │
                  │ ├─ DeBERTa-v3 NLI Engine            │
                  │ ├─ Token Uncertainty / PPL (GPT-2)  │
                  │ ├─ Semantic Cosine Similarity       │
                  │ └─ Rule-Based Contradiction Check   │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │  6. Decision, KG & Citation Gen     │
                  │ ├─ Supported   --> Verified Output  │
                  │ ├─ Refuted     --> Flagged / Warned │
                  │ └─ Uncertain   --> Safe Abstention  │
                  └─────────────────────────────────────┘
```

---

## 3. Detailed Breakdown of Implemented Techniques

### 3.1 Technique 1: Atomic Claim Decomposition
- **What It Is:** Deconstructing multi-sentence, complex paragraphs into discrete, independent factual propositions.
- **Why It Is Used:** LLM answers often blend true statements with subtle false details. Sentence-level evaluation isolates exact hallucinated clauses.
- **How It Is Implemented:** Uses clause boundary detection, relative pronoun splits (`which`, `that`, `who`), and sentence tokenization.
- **Relevant File:** `backend/verification/claim_extractor.py`
- **Key Function:** `extract_claims(text: str) -> List[str]`
- **Input:** Multi-sentence raw text or answer string.
- **Output:** Array of atomic claim strings $[c_1, c_2, \dots, c_n]$.
- **Advantages:** Prevents false-negative verification when an answer is 90% correct with one false clause.
- **Limitations:** May split co-referential pronouns without full coreference resolution.

### 3.2 Technique 2: Hybrid Multi-Source Retrieval
- **What It Is:** Parallel retrieval uniting sparse keyword indexing (BM25) and dense semantic embeddings across public academic/encyclopedic APIs and local user corpora.
- **Why It Is Used:** Overcomes single-source bias and retrieves exact terminology matches as well as conceptually related paraphrases.
- **How It Is Implemented:**
  - Lexical search via `rank-bm25`.
  - Dense search via `sentence-transformers/all-MiniLM-L6-v2` embeddings.
  - External API calls to Wikipedia REST API, arXiv Search API, and Semantic Scholar Graph API.
  - Reciprocal Rank Fusion (RRF) with constant $k=60$:
    $$\text{RRF}(d) = \sum_{m \in \{\text{BM25}, \text{Dense}, \text{Wiki}\}} \frac{1}{60 + \text{rank}_m(d)}$$
- **Relevant Files:** `backend/retrieval/multi_source.py`, `backend/retrieval/hybrid_search.py`
- **Key Functions:** `retrieve_all(query)`, `reciprocal_rank_fusion(rankings)`
- **Input:** Search query or claim string.
- **Output:** Ranked list of evidence passages with source titles, URLs, and similarity scores.
- **Advantages:** High recall across diverse knowledge domains.
- **Limitations:** Subject to external API latency and rate limits.

### 3.3 Technique 3: Cross-Encoder Natural Language Inference (NLI)
- **What It Is:** Deep cross-attention classification model evaluating directional entailment between premise and hypothesis.
- **Why It Is Used:** Unlike bi-encoders, cross-encoders compute all-to-all token attention between claim and evidence, capturing subtle semantic nuances and negation modifiers.
- **How It Is Implemented:** Fine-tuned `cross-encoder/nli-deberta-v3-small` outputting raw logits transformed via softmax into 3 class probabilities:
  $$P(\text{Entailment}), \quad P(\text{Contradiction}), \quad P(\text{Neutral})$$
- **Relevant File:** `backend/verification/cross_encoder_verifier.py`
- **Key Function:** `predict_stance(claim: str, evidence: str) -> Dict[str, Any]`
- **Input:** `claim` (hypothesis) and `evidence` (premise).
- **Output:** Stance verdict (`SUPPORTED`, `REFUTED`, `NEUTRAL`) and confidence score ($0.0 \dots 1.0$).
- **Advantages:** State-of-the-art accuracy on textual entailment benchmarks.
- **Limitations:** $O((L_c + L_e)^2)$ quadratic attention complexity.

### 3.4 Technique 4: Token Uncertainty & Predictive Entropy
- **What It Is:** Analysis of autoregressive token likelihoods and sequence perplexity to identify model uncertainty.
- **Why It Is Used:** Generative models exhibit higher predictive entropy and lower token probabilities when generating fabricated facts or rare entities.
- **How It Is Implemented:** Uses `gpt2` tokenizer and causal language modeling head to extract token log-probabilities $\log P(w_t \mid w_{<t})$, flagging tokens with probability $< 0.15$ as potential hallucination hotspots.
- **Relevant File:** `backend/verification/token_probability.py`
- **Key Function:** `compute_token_probabilities(text: str) -> Dict[str, Any]`
- **Input:** Text string.
- **Output:** Mean log-prob, sequence perplexity, minimum token probability, and uncertainty score.
- **Advantages:** Does not require external retrieval; evaluates intrinsic model certainty.
- **Limitations:** Does not catch "confident hallucinations" where the model generates false claims with high statistical fluency.

### 3.5 Technique 5: Rule-Based Stance & Contradiction Filtering
- **What It Is:** High-precision heuristic verification head targeting numerical, date, temporal, and polarity inconsistencies.
- **Why It Is Used:** Neural NLI models occasionally exhibit blind spots with exact numerical thresholds or subtle negative prefixes ("un-", "non-", "dis-").
- **How It Is Implemented:** Regex entity extraction parses numbers, percentages, dates, and currency; compares numeric ranges and evaluates negation polarity flips.
- **Relevant File:** `backend/verification/contradiction_detector.py`
- **Key Function:** `detect_contradiction(claim: str, evidence: str) -> Dict[str, Any]`
- **Input:** Claim and evidence strings.
- **Output:** Boolean `is_contradiction`, contradiction category (`NUMERICAL_MISMATCH`, `POLARITY_INVERSION`, `DATE_CONFLICT`), and explanatory string.
- **Advantages:** Zero false negatives on explicit numerical and polarity conflicts; sub-millisecond execution.
- **Limitations:** Cannot handle metaphoric or complex semantic reasoning.

### 3.6 Technique 6: Multi-Expert Consensus & Calibrated Decision Thresholds
- **What It Is:** Score fusion algorithm that aggregates individual signals from NLI, semantic cosine similarity, token uncertainty, and contradiction rules.
- **Why It Is Used:** Mitigates the weaknesses of any single verification modality.
- **How It Is Implemented:** Weighted linear combination:
  $$\text{Final\_Confidence} = w_1 P(\text{Entailment}) + w_2 \text{Sim}_{\text{cosine}} + w_3 (1.0 - \text{Uncertainty})$$
  Default calibrated weights: $w_1 = 0.55$, $w_2 = 0.30$, $w_3 = 0.15$.
  Decision policy:
  - If $\text{Contradiction\_Flag} == \text{True} \lor P(\text{Contradiction}) \ge 0.50 \implies \text{REFUTED}$
  - Else if $\text{Final\_Confidence} \ge 0.70 \implies \text{SUPPORTED}$
  - Else $\implies \text{UNCERTAIN / NOT ENOUGH INFO}$
- **Relevant File:** `backend/verification/ensemble.py`
- **Key Function:** `evaluate(claim, evidence, methods) -> Dict[str, Any]`

### 3.7 Technique 7: Dynamic Knowledge Graph Extraction
- **What It Is:** Transforming unstructured text and evidence pairs into interactive entity-relation-entity graphs.
- **Why It Is Used:** Enhances human explainability and reveals semantic alignment between claim entities and retrieved evidence nodes.
- **How It Is Implemented:** Noun phrase chunking and co-occurrence extraction links subject-verb-object triples into node/edge schema formatted for `@xyflow/react` rendering.
- **Relevant File:** `backend/verification/kg_extractor.py`
- **Key Function:** `extract_knowledge_graph(claim, evidence) -> Dict[str, List]`
- **Output:** `{ "nodes": [{"id": ..., "label": ..., "type": ...}], "edges": [{"source": ..., "target": ..., "predicate": ...}] }`.

### 3.8 Technique 8: Evidence-Grounded Abstention
- **What It Is:** Conservative output policy where the system explicitly declines to assert a factual verdict when retrieved evidence confidence falls below the reliability threshold ($\tau < 0.35$).
- **Why It Is Used:** Prevents the system itself from hallucinating verdicts on novel, ambiguous, or out-of-distribution queries.
- **How It Is Implemented:** Integrated into `backend/api/services/rag_pipeline.py` and `backend/api/routes/ask.py`. Returns `verification_status: "UNVERIFIED"`, explaining that available evidence is insufficient.
