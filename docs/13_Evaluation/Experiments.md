# Experimental Evaluation & Benchmarking
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Research Evaluation Framework

The system includes a dedicated research benchmarking suite implemented in `backend/evaluation/evaluate.py` and `backend/evaluation/benchmark_datasets.py`. The framework measures the empirical performance of individual verification heads versus the full multi-expert ensemble.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       BENCHMARK EVALUATION HARNESS                      │
│ ├─ TruthfulQA Subset       ├─ HaluEval QA Subset    ├─ FEVER Claims     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    EXPERIMENTAL CONFIGURATIONS TESTED                   │
│  ├─ Baseline 1: Raw Generative LLM (Zero-shot, No Grounding)            │
│  ├─ Baseline 2: Standard Dense RAG (Single-pass Retrieval)              │
│  ├─ Baseline 3: Pure Lexical BM25 Fact Checker                          │
│  ├─ Ablation A: Cross-Encoder NLI Only                                  │
│  ├─ Ablation B: Dense Semantic Similarity Only                          │
│  └─ Proposed System: Multi-Stage Hybrid Ensemble + RRF + Rule Engine    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                         EVALUATION METRICS HARVEST                      │
│  ├─ Precision, Recall, Macro-F1    ├─ Hallucination Detection Rate (%) │
│  ├─ False Positive / Negative Rate ├─ End-to-End Latency (ms)          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Evaluation Metrics Formalization

1. **Precision ($P$):** Fraction of flagged claims that are genuinely hallucinated:
   $$P = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Positives (FP)}}$$
2. **Recall ($R$):** Fraction of all actual hallucinations detected by the system:
   $$R = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Negatives (FN)}}$$
3. **Macro-F1 Score ($F_1$):** Harmonic mean of Precision and Recall:
   $$F_1 = 2 \cdot \frac{P \cdot R}{P + R}$$
4. **Hallucination Mitigation Rate ($\Delta \text{HR}$):** Percentage reduction in unverified/hallucinated statements delivered to the user compared to ungrounded baselines:
   $$\Delta \text{HR} = \frac{\text{Baseline Hallucination Rate} - \text{Mitigated Hallucination Rate}}{\text{Baseline Hallucination Rate}} \times 100\%$$
5. **Inference Latency:** Wall-clock time from query submission to verified JSON payload response.

---

## 3. Implemented Benchmark Runner (`evaluate.py`)

The evaluation harness in `backend/evaluation/evaluate.py` supports running automated experiments via:
```bash
python -m backend.evaluation.evaluate --dataset all --samples 100 --output data/results/benchmark_report.json
```

### Supported Benchmark Suites
- **`TruthfulQA` (Factuality & Misconceptions):** Evaluates whether the system resists endorsing false common beliefs (e.g., "Do vaccines cause autism?").
- **`HaluEval` (Binary Hallucination Detection):** Evaluates detection of synthetic and natural hallucinations in passage summarization.
- **`FEVER` (3-Class Entailment):** Validates classification over `SUPPORTED`, `REFUTED`, and `NOT ENOUGH INFO`.

---

## 4. Experimental Comparison & Ablation Design

### 4.1 Comparative Baseline Definitions
- **Base LLM:** Generates responses without reference evidence or post-hoc auditing.
- **Standard RAG:** Appends top-$K$ dense retrieved passages to context without stance verification.
- **Proposed Framework:** Executes atomic claim decomposition, hybrid multi-source retrieval (RRF), DeBERTa-v3 NLI, token probability heuristics, and numerical contradiction filtering.

### 4.2 Recommended Ablation Matrix

| Configuration | Retrieval Method | Stance Verification | Uncertainty Check | Rule Filter |
| :--- | :--- | :--- | :--- | :--- |
| **Ablation 1** | Sparse BM25 Only | None (Cosine Sim) | Disabled | Disabled |
| **Ablation 2** | Dense Vector Only | None (Cosine Sim) | Disabled | Disabled |
| **Ablation 3** | Hybrid RRF | Cross-Encoder NLI Only | Disabled | Disabled |
| **Ablation 4** | Hybrid RRF | DeBERTa-v3 + MiniLM | GPT-2 PPL Enabled | Disabled |
| **Full Ensemble**| **Hybrid RRF (Multi-Source)** | **DeBERTa-v3 + MiniLM** | **GPT-2 PPL Enabled** | **Active (Contradiction Engine)** |

---

## 5. Error Analysis Protocol

When hallucinations evade detection (False Negatives) or factual statements are incorrectly flagged (False Positives), the system categorizes errors into four buckets:
1. **Retrieval Misses:** Relevant evidence exists in world knowledge but failed to rank in the top-$K$ retrieved candidates.
2. **NLI Reasoning Errors:** Nuanced multi-step logic where the cross-encoder fails to map complex grammatical premises.
3. **Temporal Inconsistencies:** Facts that were true at a past timestamp but have changed recently (e.g., current head of state).
4. **Context Truncation:** Long complex evidence passages exceeding the 512-token cross-encoder attention limit.
