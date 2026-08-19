
<div align="center">

# 🛡️ AI HALLUCINATION MITIGATION SYSTEM

### Evidence-Grounded • Verified • Explainable AI

A reliability-focused AI system that retrieves relevant evidence, verifies claims using SciBERT and SciFact, estimates confidence, and exposes the evidence behind its answers.

<br>

![AI](https://img.shields.io/badge/AI-Hallucination%20Mitigation-6C63FF?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-Evidence%20Retrieval-00BFA6?style=for-the-badge)
![SciBERT](https://img.shields.io/badge/SciBERT-Claim%20Verification-FF6B6B?style=for-the-badge)
![SciFact](https://img.shields.io/badge/SciFact-Scientific%20Evidence-FF9F43?style=for-the-badge)

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=flat-square)

<br><br>

> **Don't just generate an answer. Retrieve the evidence. Verify the claim. Explain the result.**

</div>

---

# 🧭 01 · Overview

Artificial Intelligence systems can generate fluent and convincing answers, but fluency does not guarantee factual correctness.

A language model may:

- generate unsupported information
- combine unrelated facts
- confidently state incorrect claims
- provide weak or irrelevant evidence
- fail to communicate uncertainty

This phenomenon is commonly referred to as **AI hallucination**.

The **AI Hallucination Mitigation System** introduces an evidence and verification layer around AI-generated information.

Instead of relying only on generation, the system focuses on:

> **Retrieval → Evidence → Verification → Confidence → Explanation**

---

# 🎯 02 · The Core Idea

### Conventional AI

```text
┌───────────────┐
│    QUESTION   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  AI GENERATION│
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    ANSWER     │
└───────────────┘
````

The problem:

> How do we know whether the answer is actually supported?

### Our approach

```text
┌───────────────┐
│    QUESTION   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   RETRIEVAL   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    EVIDENCE   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  VERIFICATION │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   CONFIDENCE  │
└───────┬───────┘
        │
        ▼
┌────────────────────┐
│ ANSWER + EVIDENCE  │
└────────────────────┘
```

The system therefore acts less like a simple answer generator and more like an **AI researcher that checks evidence before trusting a claim**.

---

# 🧠 03 · What the System Does

| Capability               | Purpose                                                        |
| ------------------------ | -------------------------------------------------------------- |
| 🔎 Evidence Retrieval    | Finds relevant information for questions and claims            |
| 📚 Evidence Grounding    | Connects results to actual textual evidence                    |
| 🧠 SciBERT Verification  | Classifies scientific claims against evidence                  |
| 🎯 Confidence            | Displays model probability when available                      |
| 🔗 Source Traceability   | Allows users to inspect source information                     |
| 🕘 History               | Stores processed results during the active backend session     |
| 🕸️ Knowledge Graph      | Visualizes evidence-derived entities and relationships         |
| 🖥️ Interactive Frontend | Provides the complete user interface                           |
| ⚙️ FastAPI Backend       | Connects the frontend with retrieval and verification services |

---

# 🏗️ 04 · System Architecture

```text
                         ┌──────────────────────┐
                         │         USER         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      FRONTEND        │
                         │                      │
                         │  Ask Question       │
                         │  Verification       │
                         │  History             │
                         │  Sources             │
                         │  Knowledge Graph     │
                         │  Dashboard           │
                         └──────────┬───────────┘
                                    │
                              REST API
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FASTAPI        │
                         │       BACKEND        │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
     ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
     │   RETRIEVAL   │      │ VERIFICATION  │      │    EVIDENCE   │
     │               │      │               │      │               │
     │ SciFact       │      │ SciBERT       │      │ Sources       │
     │ Corpus        │      │ Classifier    │      │ Excerpts      │
     │ Ranking       │      │               │      │ Confidence     │
     └───────┬───────┘      └───────┬───────┘      └───────┬───────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   VERIFIED RESULT    │
                         │                      │
                         │ Answer               │
                         │ Evidence             │
                         │ Verification         │
                         │ Confidence           │
                         │ Sources              │
                         │ Graph                │
                         └──────────────────────┘
```

---

# 🔄 05 · End-to-End Workflow

The system processes information through several stages.

### 1️⃣ Question

The user submits a natural-language question or claim.

↓

### 2️⃣ Retrieval

The system searches available information for relevant evidence.

↓

### 3️⃣ Evidence Selection

Relevant textual passages are identified.

↓

### 4️⃣ Claim Verification

The claim and evidence are processed using the SciBERT-based verification model.

↓

### 5️⃣ Confidence Estimation

The classifier probability is exposed when a genuine prediction is available.

↓

### 6️⃣ Response Generation

The system presents the result with evidence and source information.

↓

### 7️⃣ Explainability

Users can inspect the answer, sources, evidence, history, and evidence-derived knowledge graph.

```text
QUESTION
   │
   ▼
RETRIEVAL
   │
   ▼
RELEVANT EVIDENCE
   │
   ▼
CLAIM VERIFICATION
   │
   ▼
CONFIDENCE
   │
   ▼
ANSWER
   │
   ├──────────────► SOURCES
   │
   ├──────────────► EVIDENCE
   │
   ├──────────────► HISTORY
   │
   └──────────────► KNOWLEDGE GRAPH
```

---

# 🔬 06 · Scientific Claim Verification

The verification component uses:

### `allenai/scibert_scivocab_uncased`

SciBERT is a language model designed for scientific text.

The project adapts SciBERT into a task-specific sequence classifier using real SciFact training examples.

### Verification pipeline

```text
                  CLAIM
                    +
                  EVIDENCE
                    │
                    ▼
           ┌─────────────────┐
           │     SciBERT     │
           │  Classification │
           └────────┬────────┘
                    │
             ┌──────┼──────┐
             ▼      ▼      ▼
        SUPPORTED REFUTED UNCERTAIN
```

The underlying classifier is trained for supported/refuted scientific claim classification.

The application layer additionally represents situations without sufficient applicable evidence as **UNCERTAIN** rather than forcing a confident decision.

---

# 📚 07 · SciFact Dataset

The project uses the **SciFact scientific claim verification dataset** as the foundation for scientific evidence verification.

The integrated corpus contains:

<div align="center">

# **5,183**

### Scientific Documents

</div>

The current training run produced:

| Dataset Split | Examples |
| ------------- | -------: |
| Training      |  **765** |
| Validation    |  **192** |

### Training labels

```text
SUPPORTED   ██████████████████████████████  489
REFUTED     █████████████████              276
```

### Validation labels

```text
SUPPORTED   ████████████████████████████   127
REFUTED     ██████████████                  65
```

---

# 🧪 08 · Model Training

The SciBERT classifier was trained locally using real SciFact examples.

### Training progress

```text
Epoch 1
Validation Accuracy

████████████████████░░░░░░░  62.50%


Epoch 2
Validation Accuracy

█████████████████████████░░  81.77%
```

| Training Stage | Validation Accuracy |
| -------------- | ------------------: |
| Epoch 1        |          **62.50%** |
| Epoch 2        |          **81.77%** |

### Current observed result

# **81.77% Validation Accuracy**

This represents the result of the current training run and should not be interpreted as a universal benchmark for SciBERT or SciFact.

---

# 🎯 09 · Verification States

The application uses three user-facing verification states.

### 🟢 SUPPORTED

The available evidence supports the claim.

### 🔴 REFUTED

The available evidence contradicts the claim.

### 🟡 UNCERTAIN

There is insufficient applicable evidence to confidently verify the claim.

The ability to return uncertainty is an important part of hallucination mitigation.

> **The system is allowed to say that there is not enough evidence.**

It does not need to force every question into a confident answer.

---

# 📊 10 · Confidence

The system exposes confidence when a genuine classifier prediction is available.

For example:

```text
Verification : REFUTED
Confidence   : 0.8723

SUPPORTED : 0.1277
REFUTED   : 0.8723
```

However:

```text
CONFIDENCE ≠ FACTUAL CERTAINTY
```

The confidence score represents the classifier's probability distribution for the given input.

It is therefore displayed alongside:

* verification status
* evidence
* sources
* claims
* context

rather than being treated as proof by itself.

---

# 🧾 11 · Real Verification Example

### Claim

> Sildenafil worsens erectile function in men who experience sexual dysfunction as a result of SSRI antidepressants.

### Evidence

> Sildenafil improved sexual function in men with SSRI-associated sexual dysfunction.

### Result

```text
┌───────────────────────────────────┐
│       VERIFICATION RESULT         │
├───────────────────────────────────┤
│                                   │
│  Prediction       REFUTED         │
│  Confidence       0.8723          │
│                                   │
│  SUPPORTED        0.1277          │
│  REFUTED          0.8723          │
│                                   │
└───────────────────────────────────┘
```

The model produced:

**REFUTED**

for the tested claim/evidence pair.

A separate inference smoke test also produced a **REFUTED** result with approximately **0.8496** confidence.

---

# 🔗 12 · Evidence & Source Traceability

A major principle of the project is that users should be able to inspect **why** a result was produced.

```text
                    RESULT
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        CLAIM      EVIDENCE      SOURCE
          │           │           │
          └───────────┼───────────┘
                      ▼
                VERIFICATION
                      │
                      ▼
                  CONFIDENCE
```

The system can expose:

* Evidence excerpts
* Source information
* Verification status
* Confidence
* Answer timestamp
* Relevant claims
* Source links

This makes the answer more transparent and inspectable.

---

# 🕸️ 13 · Knowledge Graph

The system includes an evidence-based knowledge graph for visualizing entities and relationships derived from verification evidence.

```text
              ┌────────────────────┐
              │       SOURCE       │
              └─────────┬──────────┘
                        │
                     mentions
                        │
                        ▼
                ┌──────────────┐
                │   ENTITY A   │
                └───────┬──────┘
                        │
              co-mentioned in
                  the evidence
                        │
                        ▼
                ┌──────────────┐
                │   ENTITY B   │
                └──────────────┘
```

### Evidence-first graph principle

The graph does not create relationships simply to make the visualization look complete.

Relationships must originate from the available evidence.

> **Evidence determines the graph.**

---

# 🖥️ 14 · Frontend Experience

The application provides an interactive interface around the complete verification workflow.

## 💬 Ask Question

The primary interface for submitting questions.

Users can inspect:

* Answer
* Verification status
* Confidence
* Evidence
* Sources
* Timestamp

---

## 🧪 New Verification

Designed specifically for claim-level verification.

The user provides:

```text
CLAIM
  +
EVIDENCE
```

The system returns:

```text
Verification Status
Confidence
Probability Distribution
Evidence
Knowledge Graph
```

---

## 🕘 History

History allows users to revisit previously processed results during the active backend session.

Each entry can provide:

* Question
* Answer preview
* Verification status
* Source count
* Confidence availability
* Timestamp
* Detailed result

---

## 📖 Answer Details

Provides a deeper view of an individual answer.

Users can inspect:

* Complete answer
* Claims
* Evidence
* Sources
* Verification
* Confidence
* Timestamp

---

## 🔗 Sources

The Sources interface aggregates source information associated with processed answers.

It presents information such as:

* Source title
* Publisher
* Excerpt
* Relevance
* Source URL

---

## 🕸️ Knowledge Graph

Provides an interactive visualization of evidence-derived entities and relationships.

---

## 📊 Dashboard

Provides a high-level overview of system activity, recent results, and verification information.

---

## ⚙️ Settings

Provides system health and configuration information, including:

* Backend availability
* SciFact corpus availability
* Verification model availability

---

# ⚙️ 15 · API Layer

The frontend communicates with the FastAPI backend through REST endpoints.

| Endpoint                | Purpose                         |
| ----------------------- | ------------------------------- |
| `GET /api/health`       | System and model health         |
| `POST /api/chat`        | Process a user question         |
| `POST /api/verify`      | Verify a claim against evidence |
| `GET /api/history`      | Retrieve answer history         |
| `GET /api/history/{id}` | Retrieve an individual answer   |
| `GET /api/graph/latest` | Retrieve graph information      |

The API layer connects the frontend with:

```text
Frontend
   │
   ▼
FastAPI
   │
   ├── Retrieval
   ├── Verification
   ├── Evidence
   ├── History
   └── Knowledge Graph
```

---

# 🧰 16 · Technology Stack

| Layer               | Technologies                                |
| ------------------- | ------------------------------------------- |
| 🧠 Machine Learning | PyTorch, SciBERT, Hugging Face Transformers |
| 🔎 Retrieval        | Sentence Transformers, semantic similarity  |
| 📚 Dataset          | SciFact                                     |
| ⚙️ Backend          | Python, FastAPI, Uvicorn, Pydantic          |
| 🖥️ Frontend        | React, TypeScript, Vite                     |
| 📊 Data Processing  | NumPy, scikit-learn                         |
| 📦 Environment      | Python virtual environment, Bun             |

---

# 🛡️ 17 · Reliability Principles

The project follows an **evidence-first** design philosophy.

### 01 — No fabricated evidence

The system does not create evidence to fill missing information.

### 02 — No fabricated sources

Sources are based on actual available source information.

### 03 — No fabricated confidence

Confidence is displayed only when a genuine model prediction is available.

### 04 — No fabricated graph relationships

Knowledge graph relationships are derived from evidence.

### 05 — No fake capabilities

If a capability is not implemented, the interface reports it honestly.

### 06 — Uncertainty is acceptable

An uncertain result is preferable to a confidently unsupported result.

---

# 🧪 18 · Validation

The current implementation has been validated across the main application layers.

### Backend

```text
10 tests passed
```

### Frontend

```text
Production build: PASSED
```

### API

```text
GET  /api/health        → 200
POST /api/chat          → working
POST /api/verify        → working
GET  /api/history       → working
GET  /api/history/:id   → working
GET  /api/graph/latest  → working
```

### Model

```text
Local SciBERT loading       ✓
Trained checkpoint loading  ✓
Inference smoke test        ✓
Claim verification          ✓
Confidence generation       ✓
```

---

# 📈 19 · Results at a Glance

<div align="center">

| Metric                   |        Result |
| ------------------------ | ------------: |
| 📚 SciFact Documents     |     **5,183** |
| 🧪 Training Examples     |       **765** |
| 🔬 Validation Examples   |       **192** |
| 📈 Epoch 1 Accuracy      |    **62.50%** |
| 📈 Epoch 2 Accuracy      |    **81.77%** |
| 🧪 Backend Tests         | **10 Passed** |
| 🖥️ Frontend Build       |    **Passed** |
| 🤖 Local Model Inference |    **Passed** |

</div>

---

# 🔬 20 · Research Perspective

The project approaches hallucination mitigation through:

```text
             INFORMATION RETRIEVAL
                      +
              SCIENTIFIC NLP
                      +
             CLAIM VERIFICATION
                      +
             CONFIDENCE ESTIMATION
                      +
             SOURCE TRACEABILITY
                      +
             KNOWLEDGE GRAPH
                      │
                      ▼
             EVIDENCE-GROUNDED AI
```

The central idea is to transform an AI response from an opaque generated statement into an **inspectable, evidence-aware result**.

---

# 💡 21 · What Makes This Project Different?

A conventional AI interaction often ends here:

```text
QUESTION
   ↓
ANSWER
```

This project extends the interaction:

```text
QUESTION
   ↓
RETRIEVAL
   ↓
EVIDENCE
   ↓
VERIFICATION
   ↓
CONFIDENCE
   ↓
ANSWER
   ↓
SOURCES
   ↓
KNOWLEDGE GRAPH
```

The goal is not simply to make AI generate more text.

The goal is to make AI-generated information:

### **More traceable.**

### **More inspectable.**

### **More evidence-grounded.**

### **More honest about uncertainty.**

---

# 🔮 22 · Future Scope

The current implementation provides the foundation for a broader AI reliability platform.

### 🔎 Advanced Retrieval

* Hybrid keyword + semantic retrieval
* Cross-encoder reranking
* Multi-stage evidence selection
* Multi-source retrieval

### 🧠 Advanced Verification

* Claim decomposition
* Multi-hop reasoning
* Contradiction detection
* Multi-class evidence classification

### 📚 Personal Knowledge Bases

* Document upload
* Custom evidence collections
* Private retrieval indexes
* Domain-specific verification

### 🕸️ Advanced Knowledge Graphs

* Semantic relationships
* Claim-to-evidence links
* Provenance tracking
* Interactive reasoning paths

### 📊 Persistent Analytics

* Database-backed history
* Verification statistics
* Model performance dashboards
* Long-term evaluation

### 🧪 Research Evaluation

Future evaluation can include:

* Precision
* Recall
* F1-score
* Retrieval relevance
* Evidence quality
* Hallucination rate
* Abstention quality
* Baseline comparison

---

# ⚠️ 23 · Current Limitations

The current implementation has several known boundaries.

### Scientific domain

SciFact focuses on scientific claims, so the verifier should not be treated as a universal fact-checker for every topic.

### General questions

Some questions may not have suitable evidence within the available scientific corpus.

In those situations, the system may return **UNCERTAIN** rather than treating unrelated documents as proof.

### History persistence

Current history is maintained in memory for the running backend process.

### Document ingestion

A complete user-document ingestion workflow is not currently implemented.

### Confidence interpretation

Classifier confidence represents model probability, not objective truth.

### Evaluation scope

The current validation accuracy represents the current training run. A larger evaluation framework is required before making broad claims about overall hallucination reduction.

---

# 🌍 24 · The Bigger Idea

Most AI systems focus on:

> **Can the model generate a good answer?**

This project focuses on:

> **Can the system provide an answer that can be checked?**

That distinction is the foundation of the project.

```text
                  GENERATION
                      │
                      ▼
              "What did AI say?"
                      │
                      ▼
                 VERIFICATION
                      │
                      ▼
             "Can evidence
              support it?"
                      │
                      ▼
                 EXPLANATION
                      │
                      ▼
             "What evidence
              supports this?"
```

---

# 🚀 25 · Project Status

<div align="center">

## 🟢 CORE SYSTEM OPERATIONAL

</div>

| Component                 |   Status  |
| ------------------------- | :-------: |
| Evidence Retrieval        |     🟢    |
| SciFact Integration       |     🟢    |
| SciBERT Training          |     🟢    |
| SciBERT Inference         |     🟢    |
| Claim Verification        |     🟢    |
| Confidence                |     🟢    |
| Evidence Display          |     🟢    |
| Sources                   |     🟢    |
| History                   |     🟢    |
| Knowledge Graph           |     🟢    |
| FastAPI Backend           |     🟢    |
| React Frontend            |     🟢    |
| Backend Tests             |     🟢    |
| Production Build          |     🟢    |
| Persistent Database       | 🟡 Future |
| Document Upload/Ingestion | 🟡 Future |
| Large-Scale Evaluation    | 🟡 Future |

---

# 🧭 26 · Final Perspective

<div align="center">

# AI SHOULD NOT ONLY BE ABLE TO ANSWER.

# IT SHOULD BE ABLE TO SHOW WHY ITS ANSWER DESERVES TRUST.

<br>

### 🔎 RETRIEVE

Find relevant information.

### 🧠 VERIFY

Check claims against evidence.

### 🎯 MEASURE

Expose confidence and uncertainty.

### 🔗 EXPLAIN

Connect answers to evidence and sources.

<br>

---

# 🛡️ AI HALLUCINATION MITIGATION SYSTEM

### **Retrieve. Verify. Explain.**

*Building more transparent and evidence-grounded AI systems.*

</div>
```
