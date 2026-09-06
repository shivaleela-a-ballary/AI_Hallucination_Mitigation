# Research Problem & Formulation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Formal Research Problem Statement

> **How can we systematically detect, quantify, and mitigate intrinsic and extrinsic factual hallucinations in Large Language Model outputs in real time without introducing recursive hallucination risks or prohibitive computational overhead?**

As generative language models are increasingly deployed in high-stakes domains (healthcare, law, education, scientific discovery), their propensity to generate plausible-sounding falsehoods poses a severe reliability and safety bottleneck.

---

## 2. Research Motivation

1. **The Black-Box Evaluation Dilemma:** Contemporary LLM auditing frequently relies on "LLM-as-a-Judge" (e.g., using GPT-4 to judge GPT-3.5). This introduces recursive hallucinations, sycophancy, circular confirmation bias, and high financial cost.
2. **Contextual Fragility in Standard RAG:** Standard dense retrieval systems frequently retrieve semantically related but factually non-probative context. If the generator is unconstrained, it incorporates context hallucinations.
3. **Lack of Fine-Grained Interpretability:** Most safety classifiers yield a single scalar probability without attributing which specific sentence, entity, or numerical value caused the hallucination.

---

## 3. Formal Research Questions (RQs)

- **RQ-1 (Decomposition & Stance Accuracy):** Does decomposing generated text into atomic factual claims before performing Cross-Encoder NLI verification significantly improve hallucination detection F1 compared to whole-passage evaluation?
- **RQ-2 (Hybrid Multi-Source Retrieval):** To what extent does fusing sparse lexical indexing (BM25) and dense embeddings (`all-MiniLM-L6-v2`) via Reciprocal Rank Fusion across heterogeneous academic and encyclopedic sources improve evidence recall compared to single-source dense retrieval?
- **RQ-3 (Uncertainty-Aware Fusion):** Can combining white-box token perplexity metrics with cross-encoder NLI probabilities reduce false positive fact-checking errors on ambiguous or emerging knowledge?
- **RQ-4 (Symbolic & Rule Integration):** How effectively does a lightweight rule-based contradiction detector prevent numerical and polarity blind spots common in pure neural NLI models?

---

## 4. Formal Research Hypotheses

- **$H_1$ (Atomic Granularity):** Claim-level stance classification will achieve a statistically significant ($p < 0.05$) increase in Macro-F1 over passage-level baseline classification on the HaluEval and FEVER benchmarks.
- **$H_2$ (Retrieval Consensus):** Multi-source hybrid retrieval with RRF will increase Top-5 Evidence Recall by at least $15\%$ over single-vector Wikipedia retrieval.
- **$H_3$ (Uncertainty Calibration):** Weighting NLI scores by token predictive uncertainty will reduce overconfident hallucination verdicts on TruthfulQA misconception subsets.

---

## 5. Experimental Variables

| Variable Category | Variable Name | Operational Definition / Units |
| :--- | :--- | :--- |
| **Independent Variables (IV)** | Verification Architecture | Baseline LLM vs. Dense RAG vs. Proposed Multi-Stage Ensemble |
| | Retrieval Source Strategy | Single-source Wikipedia vs. Multi-source (Wiki + arXiv + Scholar) |
| | Stance Modality | Bi-encoder vs. Cross-Encoder NLI vs. Multi-Expert Fusion |
| **Dependent Variables (DV)** | Detection Precision ($P$) | Ratio of true hallucinated claims to total flagged claims |
| | Detection Recall ($R$) | Ratio of detected hallucinations to total benchmark hallucinations |
| | Macro-F1 Score | Harmonic mean of precision and recall ($0.0 \dots 1.0$) |
| | Hallucination Rate (HR) | Percentage of ungrounded statements in final output |
| | System Latency | End-to-end processing time (milliseconds) |
| **Control Variables (CV)** | Hardware Environment | Standardized 4-core CPU / 16GB RAM runtime |
| | Benchmark Subsets | Fixed test splits of TruthfulQA, HaluEval, and FEVER |
