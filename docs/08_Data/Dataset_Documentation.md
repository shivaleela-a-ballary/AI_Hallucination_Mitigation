# Dataset & Knowledge Base Documentation
## AI Hallucination Mitigation System (v2.0.0)

---

## 1. Overview of Data Sources & Datasets

The AI Hallucination Mitigation System operates on three primary categories of data:
1. **Real-Time Dynamic Knowledge Bases:** External encyclopedic and academic search endpoints (Wikipedia, arXiv, Semantic Scholar).
2. **User-Uploaded Document Corpora:** Custom domain documents (PDF, TXT, MD, CSV, DOCX) uploaded by users for local indexing.
3. **Standard Benchmark Evaluation Datasets:** Standardized subsets of TruthfulQA, HaluEval, and FEVER used for research evaluation and pipeline benchmarking.

---

## 2. Dynamic Knowledge Retrieval Sources

### 2.1 Wikipedia REST API
- **Endpoint:** `https://en.wikipedia.org/w/api.php` and `https://en.wikipedia.org/api/rest_v1/page/summary/`
- **Content Type:** General encyclopedic knowledge, historical events, scientific consensus, geography, biography.
- **Preprocessing:** HTML tag stripping, regex header cleanup, citation reference removal (`[1]`, `[2]`), whitespace normalization.
- **Access Protocol:** Public HTTPS JSON API with user-agent attribution.

### 2.2 arXiv Open Access API
- **Endpoint:** `http://export.arxiv.org/api/query`
- **Content Type:** Preprints and peer-reviewed papers across computer science, physics, mathematics, quantitative biology, and AI/ML.
- **Preprocessing:** XML parsing, abstract extraction, author formatting, LaTeX symbol sanitization.

### 2.3 Semantic Scholar Academic Graph API
- **Endpoint:** `https://api.semanticscholar.org/graph/v1/paper/search`
- **Content Type:** Multi-disciplinary academic literature metadata, paper abstracts, citation graph counts, and venue information.
- **Preprocessing:** JSON response parsing, abstract text extraction, DOI resolution.
- **Rate Limit Handling:** Backoff on HTTP 429 status codes.

---

## 3. User-Uploaded Document Corpus Pipeline

```
  [User Document: PDF / TXT / MD / DOCX]
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │     1. File Validation & Parsing     │
  │  (Max 20MB, MIME Verification)       │
  │  (PyPDF2 / UTF-8 Text Decoder)       │
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │ 2. Sliding-Window Text Chunking      │
  │ (500 tokens / chunk, 50-token overlap│
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │   3. Neural Vector Embedding         │
  │ (sentence-transformers/all-MiniLM-L6)│
  │ (384-dimensional dense vectors)      │
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │ 4. Storage & Retrieval Indexing      │
  │ (FAISS Vector Store + In-Memory BM25)│
  └──────────────────────────────────────┘
```

---

## 4. Benchmark Evaluation Datasets (Research Evaluation)

The system includes pre-configured benchmark runners located in `backend/evaluation/benchmark_datasets.py` and `backend/evaluation/evaluate.py`:

### 4.1 TruthfulQA Benchmark Subset
- **Domain:** Questions designed to elicit human false beliefs, common misconceptions, and model hallucinations.
- **Format:** `{ "question": str, "correct_answers": List[str], "incorrect_answers": List[str], "category": str }`.
- **Evaluation Purpose:** Measures the pipeline's ability to resist common societal myths and factually incorrect common-sense assertions.

### 4.2 HaluEval Benchmark Subset
- **Domain:** General QA and summarization samples with explicitly annotated factual hallucinations.
- **Format:** `{ "query": str, "ground_truth": str, "hallucinated_answer": str, "right_answer": str }`.
- **Evaluation Purpose:** Benchmarks binary hallucination detection precision, recall, and F1.

### 4.3 FEVER (Fact Extraction and VERification) Subset
- **Domain:** Wikipedia-derived factual claims categorized into `SUPPORTS`, `REFUTES`, or `NOT ENOUGH INFO`.
- **Format:** `{ "id": int, "claim": str, "label": str, "evidence": str }`.
- **Evaluation Purpose:** Validates the core 3-class NLI stance detection head and hybrid retriever recall.

---

## 5. Data Privacy & Storage Policy

- **No Remote Telemetry:** All claim verification texts and uploaded documents remain within the local execution environment or the user's private MongoDB instance.
- **Volatile In-Memory Mode:** When running without a configured MongoDB URI, all document chunks and verification logs are kept strictly in volatile RAM and purged upon server termination.
- **Sanitization:** File upload handlers reject executable files, sanitize base filenames against directory traversal (`../`), and store chunks in structured JSON collections.
