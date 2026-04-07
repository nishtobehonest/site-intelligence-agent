# Field Service Intelligence Assistant

**Team TBH-20 | Cornell AI for Building Solutions Capstone | April 2026**

Nishchay Vishwanath (nv268) · Dhruvil Matalia (dm973) · Harshita Sahni (hs2288)

---

## What This Is

A RAG-based assistant for frontline field workers (HVAC technicians, inspectors, field engineers) that retrieves relevant documentation, past job history, and compliance requirements in real time during a job.

The core design question: **what happens when the retrieved context is incomplete or contradictory?** Most RAG systems stop at "the model found something." This system is designed for when it does not.

---

## Three Routing Paths (Graceful Degradation)

| Confidence | Trigger | Response |
|------------|---------|----------|
| **HIGH** | Top result similarity > 0.75, no conflict | Answer with source citations |
| **PARTIAL** | Conflicting sources, or similarity 0.50–0.75 | Answer with explicit conflict flag and both sources |
| **LOW** | Similarity < 0.50, or no results | Escalation message with what was and was not found |

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY

# Add documents to data/raw/ (see Data Sources below)

# Ingest documents into Chroma
python src/ingest.py

# Generate synthetic job history
python src/generate_synthetic.py --count 50

# Launch browser demo (Streamlit UI)
streamlit run app.py

# Run CLI demo with three preset queries (HIGH / PARTIAL / LOW)
python demo/demo.py

# Run evaluation
python eval/run_eval.py
```

The Streamlit UI (`app.py`) provides a browser interface with color-coded confidence badges (green / amber / red), three preset query buttons, inline source citations, and escalation warnings for LOW-confidence routes.

---

## Data Sources

| Collection | What | Where to get it |
|------------|------|-----------------|
| `osha` | OSHA Field Operations Manual, 29 CFR 1910 | osha.gov (public domain) |
| `manuals` | HVAC equipment manuals (Carrier, Trane, Lennox) | Manufacturer sites (public) |
| `job_history` | Synthetic job records | Run `generate_synthetic.py` |

---

## Project Structure

```
src/
  ingest.py            # Document loading + Chroma indexing
  retriever.py         # Vector similarity retrieval
  confidence.py        # Confidence scoring and routing decision
  degradation.py       # Graceful degradation routing (HIGH/PARTIAL/LOW)
  assistant.py         # Main pipeline
  generate_synthetic.py # Synthetic job history generation

eval/
  ground_truth.json    # 50 known query-answer pairs
  adversarial.json     # 20 queries with no correct answer in corpus
  contradictions.json  # 15 contradiction scenarios
  run_eval.py          # Evaluation runner

demo/
  demo.py              # CLI demo for live presentation
```

---

## Troubleshooting

**Duplicate chunks in Chroma** (if ingest was run more than once):
```bash
rm -rf data/chroma_db/
python src/ingest.py
```
Never run `ingest.py` twice without clearing `data/chroma_db/` first — each run appends to existing collections.

**Switching LLM providers** — set `LLM_PROVIDER` in `.env` (`anthropic` / `openai` / `gemini`). Current working model: `gemini-2.5-flash`.

**Tuning confidence thresholds** without code changes:
```bash
CONFIDENCE_HIGH_THRESHOLD=0.80 CONFIDENCE_PARTIAL_THRESHOLD=0.55 python demo/demo.py
```

---

## References

1. Lewis et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020. https://arxiv.org/abs/2005.11401
2. Gao et al. "RAG for Large Language Models: A Survey." arXiv 2023. https://arxiv.org/abs/2312.10997
3. OSHA Field Operations Manual. U.S. DOL, 2024. https://www.osha.gov/enforcement/directives/cpl-02-00-164
4. Anthropic. Claude Model Card. 2024. https://www.anthropic.com/claude
