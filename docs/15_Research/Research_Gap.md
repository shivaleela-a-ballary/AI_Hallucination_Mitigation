# Research Gap Analysis
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Critical Review of Existing Mitigation Approaches

| Approach | Typical Implementation | Core Limitations |
| :--- | :--- | :--- |
| **1. LLM-as-a-Judge / Self-Reflection** | Prompting GPT-4 to critique GPT-3.5 outputs (e.g., SelfCheckGPT, RARR) | Expensive API costs, recursive hallucinations, vulnerability to prompt injection, high latency. |
| **2. Standard Dense RAG** | Single-pass vector retrieval (kNN search) prepended to LLM prompt | High sensitivity to chunk boundaries, vector hallucination when top-k passages contain distractor noise. |
| **3. Pure Bi-Encoder Similarity** | Cosine similarity between sentence embeddings (`sentence-transformers`) | Inability to evaluate directional logic (e.g., "A caused B" vs. "B caused A" yields identical cosine similarity). |
| **4. Black-Box Uncertainty Probing** | Activation probing on hidden states | Requires access to model internals/weights; impossible for closed-source APIs. |

---

## 2. Identified Research Gaps

### Research Gap 1: Disconnect Between Information Retrieval Consensus and Stance Calibration
Most RAG verifiers assume that if a passage has high semantic similarity to a generated answer, the answer is factual. In reality, a passage may discuss the exact topic while directly contradicting the claim. There is an empirical gap in creating unified pipelines that combine **multi-source reciprocal rank fusion** with **disentangled cross-encoder NLI and symbolic numerical filters**.

### Research Gap 2: Explainability vs. Computational Efficiency Trade-off
Current interpretability methods for hallucination either require heavy fine-tuned critique LLMs (slow, parameter-heavy) or shallow token highlights (opaque). There is a distinct gap for lightweight, real-time architectures that generate **structural Knowledge Graphs and atomic claim attribution** on consumer hardware.

---

## 3. How Our Proposed Architecture Bridges the Gap

```
┌─────────────────────────────────────────────────────────────────────────┐
│               KNOWN EXISTING TECHNIQUES (Foundation Layer)              │
│  ├─ DeBERTa-v3 NLI classification (He et al., 2021)                     │
│  ├─ BM25 + Dense vector retrieval (Robertson et al., Karpukhin et al.)  │
│  ├─ Reciprocal Rank Fusion (Cormack et al., 2009)                       │
│  └─ Perplexity-based uncertainty estimation                             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              POTENTIALLY NOVEL CONTRIBUTIONS OF THIS PROJECT             │
│  ├─ Multi-Expert Calibrated Stance Fusion combining NLI with            │
│  │   token logit entropy and rule-based numerical contradiction heads.   │
│  ├─ Dynamic Heterogeneous Multi-Source Evidence Aggregation across      │
│  │   Wikipedia, arXiv preprints, Semantic Scholar, and local corpora.   │
│  ├─ Synchronous Interactive Knowledge Graph Extraction rendering       │
│  │   entity-relation topology for human-in-the-loop fact checking.      │
│  └─ Dual-Mode Resilient Architecture ensuring graceful local fallback    │
│      without sacrificing research reproducibility.                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Empirical Evidence Required to Validate Claims of Novelty

To substantiate claims in a formal peer-reviewed publication, the following empirical evidence must be recorded:
1. **Ablation Performance Table:** Proving that adding the rule-based contradiction detector and token perplexity head produces a statistically significant improvement over baseline DeBERTa-v3 NLI alone.
2. **Retrieval Recall Curve:** Graphing Top-$K$ retrieval recall comparing Single-Source Dense Retrieval vs. Hybrid Multi-Source RRF across scientific queries on the arXiv/Semantic Scholar subsets.
3. **Latency Benchmarking:** Documenting that the ensemble executes in under $1.5\text{s}$ per claim on standard CPU hardware.
