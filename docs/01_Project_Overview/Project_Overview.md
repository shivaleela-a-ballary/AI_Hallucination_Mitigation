# Project Overview: AI Hallucination Mitigation System

---

## 1. Project Identity
- **Project Title:** Multi-Stage AI Hallucination Detection and Grounding Mitigation System
- **Repository Name:** `AI_Hallucination_Mitigation`
- **System Version:** 2.0.0
- **Primary Domain:** Natural Language Processing (NLP), Large Language Model (LLM) Reliability, Retrieval-Augmented Generation (RAG), Automated Fact Verification

---

## 2. Explaining the Project at 4 Levels of Abstraction

### Level 1: One-Sentence Summary
> An end-to-end, multi-tier verification and grounding framework that detects factual hallucinations in LLM outputs and mitigates them using hybrid retrieval, cross-encoder natural language inference, semantic uncertainty estimation, and dynamic knowledge graph generation.

### Level 2: Beginner / Layman Explanation
> Generative AI systems like ChatGPT or Gemini are powerful, but they often make up facts that sound convincing—a problem called "AI hallucination." This project is an intelligent safety inspection system for AI. Whenever an AI writes an answer or makes a claim, our system breaks the text down into individual facts, searches trustworthy sources (like Wikipedia, research papers, and uploaded documents), compares the AI's claims against real facts using advanced language models, and flags anything that is unsupported or contradicted, providing a verified answer backed by real citations.

### Level 3: Technical / Engineering Explanation
> The system implements a full-stack asynchronous architecture consisting of a FastAPI backend and a React/TypeScript frontend. The backend orchestrates a multi-step hallucination mitigation pipeline:
> 1. **Decomposition & Parsing:** Extracts atomic claims and noun-phrase entity triples.
> 2. **Hybrid Multi-Source Retrieval:** Combines sparse lexical retrieval (BM25) and dense vector retrieval (`all-MiniLM-L6-v2`) over external APIs (Wikipedia, arXiv, Semantic Scholar) and local uploaded corpora.
> 3. **Reciprocal Rank Fusion & Cross-Encoder Reranking:** Filters and orders evidence chunks.
> 4. **Ensemble Stance Detection:** Combines Cross-Encoder DeBERTa-v3 NLI (`nli-deberta-v3-small`), Semantic Similarity, Token-level Perplexity/Probability (`gpt2`), and rule-based Contradiction Detection.
> 5. **Knowledge Graph Extraction:** Dynamically maps entity-relation-entity triples and builds interactive graph topologies.
> 6. **Fallback Persistence:** Employs dual-mode MongoDB Atlas with thread-safe in-memory storage fallback.

### Level 4: Academic / Research Explanation
> This research project investigates the systematic mitigation of intrinsic and extrinsic hallucinations in Transformer-based autoregressive language models. By integrating multi-modal stance classifiers with hybrid sparse-dense retrieval-augmented grounding, the framework models factuality as a joint optimization problem over evidence entailment probability, token predictive uncertainty, and cross-source consensus. The pipeline formalizes an uncertainty-aware decision threshold:
> $$\text{Verdict} = \arg\max_{c \in \{\text{Entailment}, \text{Contradiction}, \text{Neutral}\}} \sum_{m \in M} w_m P_m(c \mid \text{claim}, \text{evidence})$$
> where $M$ represents the verification model ensemble with calibrated weights $w_m$. The system bridges the gap between static retrieval pipelines and black-box LLM verifiers by exposing transparent reasoning traces, entity graph consensus, and empirical ablation baselines on standard fact-checking benchmarks (TruthfulQA, HaluEval, FEVER).

---

## 3. Abstract
Large Language Models (LLMs) demonstrate impressive generative capabilities across diverse knowledge domains but remain susceptible to hallucinations—generating syntactically fluent yet factually inaccurate or unsubstantiated statements. In high-stakes applications such as medicine, law, scientific research, and academic analysis, unchecked hallucinations undermine model trustworthiness. 

This project presents the **AI Hallucination Mitigation System (v2.0)**, a production-grade software and research platform engineered to detect, quantify, and mitigate AI hallucinations in real time. The platform combines a modular FastAPI computational engine with a modern TanStack/React visualization dashboard. The system evaluates arbitrary claims and multi-paragraph LLM responses through four core mechanisms: (i) atomic claim extraction, (ii) multi-source hybrid retrieval incorporating BM25 and dense semantic embeddings with cross-encoder reranking, (iii) an ensemble verification engine combining DeBERTa-v3 Natural Language Inference, token probability distributions, and semantic cosine similarity, and (iv) automated knowledge graph extraction for entity-relationship validation. The system features database resilience via MongoDB Atlas with automatic in-memory fallback, full test coverage across 51 integration test scenarios, and a reproducible evaluation suite over TruthfulQA, FEVER, and HaluEval.

---

## 4. Problem Statement
Autoregressive Large Language Models predict next tokens based on statistical regularities rather than grounded world knowledge. Consequently, they exhibit two primary classes of hallucination:
1. **Extrinsic Hallucinations:** Introducing unverifiable details not present or supported by the source context.
2. **Intrinsic Hallucinations:** Directly contradicting known factual evidence or premise context.

Existing mitigation techniques typically suffer from one of three key limitations:
- **Black-box LLM-as-a-Judge:** Evaluating an LLM's output with another LLM is expensive, prone to sycophancy, and introduces recursive hallucination risks.
- **Pure Lexical Retrieval:** Traditional keyword search fails on complex paraphrasing and multi-hop reasoning.
- **Lack of Interpretability:** Most systems provide a binary factuality score without transparent claim decomposition, evidence citations, or visual relationship graphs.

---

## 5. Objectives
1. **Build an Automated Multi-Stage Verification Pipeline:** Deconstruct text into atomic propositions and evaluate each against trusted evidence corpora.
2. **Develop a Multi-Source Hybrid Retrieval Engine:** Unify external academic and encyclopedic repositories (Wikipedia, arXiv, Semantic Scholar) with local user-uploaded documents (PDF, TXT, MD) using hybrid BM25 + dense embedding retrieval.
3. **Deploy Multi-Method Ensemble Verification:** Implement independent verification heads (Cross-Encoder NLI, Token Uncertainty, Semantic Cosine Similarity, Contradiction Engine) with weighted consensus scoring.
4. **Provide Full Visual Explainability:** Generate interactive Entity-Relationship Knowledge Graphs and confidence breakdowns for every verified claim.
5. **Deliver an Enterprise-Grade Web Application:** Build a responsive, accessible frontend with real-time feedback, history tracking, file management, and Swagger/OpenAPI endpoints.

---

## 6. Scope & Target Users

### Target Users
- **Academic Researchers & Students:** Cross-referencing literature claims against arXiv and Semantic Scholar.
- **Enterprise Knowledge Workers:** Auditing LLM summaries against internal company documentation.
- **Fact Checkers & Journalists:** Verifying claims against real-time encyclopedic sources with transparent citation trails.
- **AI/ML Engineers:** Benchmarking hallucination rates across model architectures.

### System Scope
- **In Scope:** Factual statement verification, document-grounded question answering, RAG pipeline evaluation, multi-source evidence extraction, claim graph generation, interactive UI auditing.
- **Out of Scope:** Real-time speech hallucination detection, image/video generation hallucination auditing, proprietary LLM fine-tuning weights modification.

---

## 7. Technology Stack

| Layer | Technologies / Libraries |
| :--- | :--- |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2, AsyncIO |
| **NLP & AI Models** | Hugging Face `transformers`, `torch`, `sentence-transformers`, `cross-encoder/nli-deberta-v3-small`, `gpt2`, `all-MiniLM-L6-v2` |
| **Retrieval & Indexing** | `rank-bm25`, `faiss-cpu`, PyPDF2, arXiv API, Semantic Scholar API, Wikipedia REST API |
| **Database & Caching** | MongoDB Atlas, Motor (async driver), PyMongo, Thread-Safe In-Memory Fallback Cache |
| **Frontend UI** | React 19, TypeScript 5.8, Vite 8, TanStack Router, TanStack Query, Tailwind CSS 4, Radix UI, Lucide Icons, Motion, `@xyflow/react` |
| **Testing & Evaluation** | Pytest, Pytest-Asyncio, HTTPX, TruthfulQA benchmark runner, FEVER evaluator, HaluEval parser |

---

## 8. High-Level Architecture Overview

```
 [User Input: Claim / Question / Document]
                  │
                  ▼
   ┌──────────────────────────────┐
   │    FastAPI API Gateway       │
   │  (/api/verify, /api/ask)     │
   └──────────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 ┌──────────────┐    ┌──────────────┐
 │ Claim Parser │    │ Multi-Source │
 │ & Triple Ext │    │  Retrieval   │
 └──────┬───────┘    └──────┬───────┘
        │                   │
        └─────────┬─────────┘
                  ▼
   ┌──────────────────────────────┐
   │ Ensemble Verification Engine │
   │ ├─ DeBERTa-v3 NLI            │
   │ ├─ Semantic Cosine Sim       │
   │ ├─ Token Probability (GPT-2) │
   │ └─ Contradiction Detector    │
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ Verdict, KG & Citations Gen  │
   └──────────────┬───────────────┘
                  ▼
   ┌──────────────────────────────┐
   │ React 19 TanStack Dashboard  │
   │ (Badges, Graphs, Citations)  │
   └──────────────────────────────┘
```

---

## 9. Expected Outcomes & Deliverables
1. **Verified Real-Time Pipeline:** Operational sub-second verification for direct claims and multi-source document Q&A.
2. **Interactive Web Dashboard:** Production UI with claim decomposition, evidence inspector, knowledge graph visualization, and document management.
3. **Reproducible Evaluation Framework:** Standardized test runner calculating Precision, Recall, F1, Accuracy, and Hallucination Reduction Rate.
4. **Complete Research Documentation:** 16-chapter technical reference, SRS, architecture blueprints, algorithm specifications, and research paper content map.

---

## 10. Limitations & Future Scope

### Current Limitations
- **External API Rate Limits:** Semantic Scholar and Wikipedia APIs enforce rate limits (HTTP 429) during rapid batch requests without dedicated API keys.
- **CPU Inference Latency:** Running local DeBERTa-v3 and embedding generation on CPU takes ~800ms–1.5s per multi-claim verification pass.
- **Context Length:** Local embedding chunks default to 500 tokens with 50-token overlaps.

### Future Scope
- **GPU TensorRT Acceleration:** Quantizing Cross-Encoder weights to INT8/FP16 for sub-100ms inference.
- **Graph Neural Network (GNN) Stance Refinement:** Incorporating graph convolutional layers over extracted entity triples for global factual consistency scoring.
- **Self-Healing LLM Feedback Loop:** Direct integration with agentic toolchains to automatically rewrite flagged claims in continuous generation streams.
