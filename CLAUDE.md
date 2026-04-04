# Field Service Intelligence Assistant
## Claude Code Project Context

---

## What This Project Is

A RAG-based (Retrieval-Augmented Generation) Field Service Intelligence Assistant built for Cornell MEM AI for Building Solutions capstone (Team TBH-20). The system helps frontline field workers (HVAC technicians, inspectors, field engineers) retrieve relevant documentation, past job history, and compliance requirements in real time during a job.

**This is a minimal working prototype, not a production system.** The goal is a live RAG query that takes a technician question and returns a cited, reliable answer — with explicit handling for when the context is incomplete or contradictory.

---

## Stack

- **Language:** Python 3.11+
- **LLM API:** Anthropic (Claude 3.5 Sonnet via `anthropic` SDK)
- **Vector store:** Chroma (local, no signup required)
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (free, local)
- **RAG framework:** LangChain
- **Interface:** Simple CLI for demo purposes (no frontend needed for prototype)

---

## Repo Structure

```
field-service-assistant/
├── CLAUDE.md                  # This file — read first
├── README.md                  # Project overview
├── requirements.txt           # All dependencies
├── .env.example               # API key template (never commit .env)
├── .gitignore
│
├── data/
│   ├── raw/                   # Raw source documents (PDFs, txt)
│   │   ├── osha/              # OSHA field documentation
│   │   ├── manuals/           # Equipment maintenance manuals
│   │   └── job_history/       # Synthetic job history records
│   └── processed/             # Chunked and cleaned documents
│
├── src/
│   ├── ingest.py              # Document loading, chunking, embedding, Chroma indexing
│   ├── retriever.py           # Query embedding, vector similarity search, top-k retrieval
│   ├── confidence.py          # Confidence scoring logic and routing decisions
│   ├── degradation.py         # Graceful degradation: HIGH / PARTIAL / LOW routing
│   ├── assistant.py           # Main assistant pipeline: query in, answer out
│   └── generate_synthetic.py  # Script to generate synthetic job history using Claude API
│
├── eval/
│   ├── ground_truth.json      # 50 curated query-answer pairs
│   ├── adversarial.json       # 20 queries with no correct answer in corpus
│   ├── contradictions.json    # 15 contradiction scenarios
│   └── run_eval.py            # Evaluation runner: outputs metrics table
│
├── demo/
│   └── demo.py                # CLI demo script for live presentation
│
└── tests/
    └── test_degradation.py    # Unit tests for the three failure mode paths
```

---

## Core System Design

### The Four Layers

**Layer 1: Retrieval (RAG Core)**
- Takes a structured technician query
- Embeds it using sentence-transformers
- Retrieves top-5 relevant chunks from three Chroma collections (osha, manuals, job_history)
- Returns ranked context with source metadata

**Layer 2: Confidence Scoring (`confidence.py`)**
- Evaluates retrieved context quality
- Inputs: cosine similarity scores, source freshness tag, number of results returned
- Outputs: confidence level (HIGH / PARTIAL / LOW) and reason
- Thresholds (starting point, tune during eval):
  - HIGH: top result similarity > 0.75, at least 2 results above 0.60
  - PARTIAL: top result similarity 0.50-0.75, OR two results conflict on same topic
  - LOW: top result similarity < 0.50, OR zero results returned

**Layer 3: Graceful Degradation (`degradation.py`)**
This is the core differentiator. Three routing paths:

| Confidence | Action |
|------------|--------|
| HIGH | Return answer with source citations |
| PARTIAL | Return answer WITH explicit conflict flag: "Two sources disagree. Source A says X, Source B says Y." |
| LOW | Return escalation message: "I did not find sufficient information for [query]. Here is what I found: [partial context]. Recommend contacting office." |

**Layer 4: Answer Generation (`assistant.py`)**
- Takes retrieved context + confidence level + routing decision
- Calls Claude API with a structured system prompt
- System prompt enforces: no hallucination, citation required, explicit uncertainty language for PARTIAL/LOW
- Returns final answer to the technician

---

## Data Sources

### OSHA Documentation
- Source: https://www.osha.gov/enforcement/directives/cpl-02-00-164
- What to download: Field Operations Manual sections relevant to HVAC, electrical, and plumbing inspection
- Also useful: OSHA 29 CFR 1910 Subpart S (electrical), 1910.303, 1910.147 (lockout/tagout)

### Equipment Manuals
- Source: public manufacturer documentation
- Good starting points: Carrier HVAC manuals (publicly available on carrierhvac.com), Trane technical manuals
- Target: 3-5 manuals covering different equipment types

### Synthetic Job History
- Generated using `generate_synthetic.py` (calls Claude API)
- Schema per record:
  ```json
  {
    "job_id": "JOB-001",
    "date": "2024-11-15",
    "equipment_id": "CARRIER-RTU-48XL",
    "job_type": "preventive_maintenance",
    "site_id": "SITE-CHICAGO-03",
    "technician_notes": "...",
    "anomalies_flagged": ["..."],
    "resolution": "...",
    "compliance_notes": "..."
  }
  ```
- Generate at least 50 records covering 5 equipment types and 3 job types

---

## Key Design Decisions (Do Not Change Without Discussion)

1. **Confidence thresholds are product decisions, not engineering ones.** When tuning thresholds, ask: what is the cost of a false positive (confident wrong answer) vs a false negative (unnecessary escalation)? In a safety-critical field context, false positives are more dangerous. Tune conservatively.

2. **The system prompt must enforce no hallucination.** The Claude system prompt must include explicit instruction: "If you are not certain, say so. Do not fabricate procedures or specifications. Always cite your source."

3. **Source citations are mandatory on every answer.** No response is returned to the user without at least one source citation (document name, section, date).

4. **Graceful degradation is a first-class feature, not an edge case.** The demo must show all three routing paths: HIGH, PARTIAL, and LOW. Prepare demo queries that trigger each one deliberately.

5. **Chroma uses three separate collections** (osha, manuals, job_history), not one combined collection. This allows source-aware retrieval and makes conflict detection between sources possible.

---

## Evaluation Plan

### Metrics to Track
- **Hallucination rate:** confident wrong answers / total responses (target: below 2%)
- **Escalation rate:** LOW confidence routes / total queries (target: 10-25%)
- **Coverage rate:** queries with at least one relevant result / total queries (target: above 80%)
- **Conflict detection rate:** PARTIAL routes correctly identified / total contradiction scenarios

### Eval Sets (in eval/)
- `ground_truth.json`: 50 query-answer pairs. Built from OSHA docs and manuals. Correct answer is a specific section or spec.
- `adversarial.json`: 20 queries with no correct answer in the corpus. Correct system behavior is LOW confidence escalation, not a hallucinated answer.
- `contradictions.json`: 15 scenarios where two sources say different things. Correct system behavior is PARTIAL route with both sources surfaced.

### Running Eval
```bash
python eval/run_eval.py --collection all --output eval_results.csv
```

---

## Demo Script (for presentation)

Three queries to demo live, one per routing path:

**HIGH confidence query:**
"What is the lockout/tagout procedure for a Carrier RTU-48XL before performing electrical maintenance?"
Expected: cited answer from OSHA 1910.147 + Carrier manual

**PARTIAL confidence query (contradiction):**
"What is the recommended refrigerant charge pressure for a Carrier RTU-48XL?"
Expected: system flags that the 2019 manual and 2023 manual list different values, surfaces both

**LOW confidence query (incomplete context):**
"What was the last maintenance performed on equipment ID HVAC-SITE07-UNIT-99?"
Expected: system escalates with "I did not find a job history record for this equipment ID"

---

## Environment Setup

```bash
# Clone and install
git clone https://github.com/[your-username]/field-service-assistant
cd field-service-assistant
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Ingest documents (run after adding files to data/raw/)
python src/ingest.py

# Run the assistant
python demo/demo.py

# Run evaluation
python eval/run_eval.py
```

---

## Dependencies (requirements.txt)

```
anthropic>=0.25.0
langchain>=0.1.0
langchain-community>=0.0.20
chromadb>=0.4.0
sentence-transformers>=2.2.2
python-dotenv>=1.0.0
pypdf>=4.0.0
tiktoken>=0.6.0
pandas>=2.0.0
numpy>=1.24.0
```

---

## What Is Out of Scope for This Prototype

- No frontend or web UI (CLI only)
- No user authentication or session management
- No real-time document updates
- No fine-tuning
- No multi-agent orchestration (single pipeline only)
- No production deployment

These are all valid next steps but are explicitly out of scope for the April 8 submission.

---

## Team

| Name | NetID | Role |
|------|-------|------|
| Nishchay Vishwanath | nv268 | RAG pipeline, graceful degradation, demo |
| Dhruvil Matalia | dm973 | Data collection, document ingestion |
| Harshita Sahni | hs2288 | Evaluation framework, ground truth annotation |

---

## References

1. Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020. https://arxiv.org/abs/2005.11401
2. Gao, Y., et al. "Retrieval-Augmented Generation for Large Language Models: A Survey." arXiv 2023. https://arxiv.org/abs/2312.10997
3. OSHA Field Operations Manual. U.S. Department of Labor, 2024. https://www.osha.gov/enforcement/directives/cpl-02-00-164
4. Anthropic. Claude Model Card. 2024. https://www.anthropic.com/claude
5. Karpukhin, V., et al. "Dense Passage Retrieval for Open-Domain Question Answering." EMNLP 2020. https://arxiv.org/abs/2004.04906



# Future domain extensions (post-April 8)
# - Drone inspection: replace osha/manuals/job_history collections with
#   inspection_reports/flight_logs/site_anomalies
# - Power grid construction: replace with safety_procedures/equipment_specs/incident_logs
# - No code changes required in confidence.py, degradation.py, or assistant.py