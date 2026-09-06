# Research Literature Mapping & Search Guide
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Research Domain Taxonomy & Project Mapping

| Research Domain | Relevance to Project | Key Search Terminology | Corresponding Project Component | Key Literature Focus |
| :--- | :--- | :--- | :--- | :--- |
| **1. LLM Hallucination Detection** | Core research objective | "hallucination detection", "faithfulness evaluation", "factuality assessment" | `backend/verification/` | Surveys on intrinsic vs. extrinsic hallucination taxonomy |
| **2. Retrieval-Augmented Generation (RAG)** | Primary mitigation paradigm | "RAG", "hybrid retrieval", "dense passage retrieval", "BM25 fusion" | `backend/retrieval/` | Multi-source evidence retrieval, dense indexing, reranking |
| **3. Natural Language Inference (NLI)** | Core stance classification | "textual entailment", "cross-encoder NLI", "DeBERTa-v3", "stance classification" | `cross_encoder_verifier.py` | 3-class premise-hypothesis entailment modeling |
| **4. Uncertainty Estimation** | Intrinsic model auditing | "token perplexity", "predictive entropy", "semantic uncertainty", "confidence calibration" | `token_probability.py` | White-box token likelihood probing for hallucination detection |
| **5. Claim Decomposition & Fact Checking** | Fine-grained auditing | "atomic claim extraction", "automated fact verification", "claim-level stance" | `claim_extractor.py`, `check_answer.py` | Syntactic and neural proposition splitting |
| **6. Knowledge Graph Grounding** | Visual explainability & consensus | "knowledge graph verification", "entity triple extraction", "graph-based factuality" | `kg_extractor.py`, `frontend/src/routes/graph.tsx` | Entity-relationship graph validation |
| **7. Conservative Abstention** | Safety policy under uncertainty | "selective generation", "abstention in QA", "hallucination mitigation thresholding" | `rag_pipeline.py`, `/api/ask` | Decision policies for declining unsupported queries |

---

## 2. Recommended Academic Database Search Queries

### 2.1 Google Scholar & Semantic Scholar
- `"LLM hallucination mitigation" AND "natural language inference" AND "hybrid retrieval"`
- `"atomic claim verification" AND "retrieval augmented generation" AND ("cross-encoder" OR "DeBERTa")`
- `"factuality assessment" "large language models" "reciprocal rank fusion" "BM25"`
- `"hallucination detection" "token probability" "uncertainty estimation" "faithfulness"`

### 2.2 IEEE Xplore & ACM Digital Library
- `("Large Language Models" OR "LLM") AND ("Hallucination Detection" OR "Fact Verification") AND ("NLI" OR "RAG")`
- `("Retrieval-Augmented Generation") AND ("Multi-Source Retrieval" OR "Hybrid Search") AND ("Faithfulness")`
- `("Knowledge Graph Extraction") AND ("Fact Checking") AND ("Natural Language Inference")`

### 2.3 arXiv & ScienceDirect
- `ti:"hallucination" AND abs:"retrieval" AND abs:"verification"`
- `ti:"factual" AND abs:"NLI" AND abs:"grounding"`
- `abs:"TruthfulQA" OR abs:"HaluEval" OR abs:"FEVER" AND abs:"hallucination"`

---

## 3. Targeted Literature Review Checklist for Paper Writing

1. **Foundational Surveys on Hallucination:** Papers defining hallucination taxonomies, benchmarks, and evaluation metrics in generative language models.
2. **Retrieval-Augmented Generation Foundations:** Foundational papers establishing hybrid BM25 + dense retrieval, Reciprocal Rank Fusion, and cross-encoder reranking.
3. **Automated Fact-Checking Benchmarks:** Methodological documentation for FEVER, TruthfulQA, and HaluEval.
4. **NLI for Hallucination Detection:** Studies evaluating BERT/DeBERTa-v3 cross-encoders for claim-level entailment classification.
5. **Calibrated Uncertainty Estimation:** Studies establishing token logit variance and predictive entropy as indicators of hallucination vulnerability.
