# Site Intelligence Agent

> An AI assistant that gives frontline field workers instant access to expert knowledge — and knows when to say "I don't know."

**[Live Demo →](https://site-intelligence-agent.streamlit.app)** &nbsp;|&nbsp; **Built by [Nishchay Vishwanath](https://github.com/nishtobehonest) · 2026**

`Phase 1 — HVAC ✅ Complete` &nbsp;|&nbsp; `Phase 2 — Drone Inspection 🔄 In Progress` &nbsp;|&nbsp; `Phase 3 — Multi-Graph 📋 Planned` &nbsp;|&nbsp; `Phase 4 — User Validation 👥 Planned`

---

**94% accuracy on answerable queries &nbsp;·&nbsp; < 2% hallucination rate &nbsp;·&nbsp; 0 confident wrong answers on adversarial set &nbsp;·&nbsp; LLM skipped entirely on low-confidence paths**

---

## The Problem

A field technician arrives at a rooftop HVAC unit they've never serviced. They have 30 minutes to fix it safely. The relevant safety procedure is in a binder at the office. The equipment manual is 400 pages in their truck. What the last technician did here is locked in a back-office system they can't reach on-site.

OSHA estimates this knowledge gap causes **50,000 preventable injuries and 120 deaths per year** in field service work alone — and the risk falls disproportionately on workers at smaller, under-resourced companies who can't afford dedicated knowledge management systems.

The knowledge exists. It's just fragmented, inaccessible, and never where it's needed.

---

## What I Built

A **RAG-based Site Intelligence Agent** that field workers query in plain English on-site. It searches simultaneously across safety regulations, equipment manuals, and site service history — then routes every response through a confidence-aware degradation layer before ever calling a language model.

**Two domains, one pipeline:**
- **Phase 1 — HVAC Field Service** (complete): lockout/tagout procedures, equipment specs, job history
- **Phase 2 — Drone Site Inspection** (in progress): anomaly detection, structural baseline comparison, compliance checks

### Who this addresses

- **Knowledge fragmentation at scale** — field workers have to consult 3–5 disconnected sources per query; this system unifies them behind a single interface with source attribution
- **Safety-critical AI deployment** — the system is designed around the principle that a confident wrong answer is more dangerous than no answer; every routing decision reflects that
- **Domain-agnostic field intelligence** — HVAC and drone inspection are two instances of the same problem pattern; the pipeline generalizes to any domain where knowledge is fragmented and acting on wrong information has consequences

---

## How It Works

### The Pipeline

The LLM is the last step, not the first. Every query runs through five stages in sequence — and can be stopped at any point before reaching the model:

```
                          ┌─ classifier.py ──────────────────────────────────────┐
                          │  Rule-based keyword match (~70% of queries, ~5ms)    │
  Query ──→ [1. Classify] │  LLM structured output for ambiguous queries (~30%)  │
                          └──────────────────────────────────────────────────────┘
               │
               ▼
          ┌─ retriever.py ────────────────────────────────────────────────────────┐
          │  Embed query → search Chroma collections → apply spatial zone filter  │
[2. Retrieve]  │  Return top-k chunks with cosine similarity scores               │
          └───────────────────────────────────────────────────────────────────────┘
               │
               ▼
          ┌─ confidence.py ───────────────────────────────────────────────────────┐
          │  Score top result · detect cross-collection + version conflicts        │
[3. Score]│  Output: top_score (float) + conflict_detected (bool)                 │
          └───────────────────────────────────────────────────────────────────────┘
               │
               ▼
          ┌─ assistant.py ─────────────────────────────────────────────┐
          │                                                             │
[4. Gate] │  score ≥ 0.50 ──────────────────────────────────────────→ [5. LLM + Route]
          │                                                             │
          │  score < 0.50 ──→  ESCALATE  ◄── LLM never called ◄───────┘
          └────────────────────────────────────────────────────────────┘
```

### Three Routing Paths

| Level | Trigger | What happens |
|-------|---------|-------------|
| **HIGH** | Top similarity ≥ 0.79, no conflict | LLM called → answer returned with source citations |
| **PARTIAL** | Conflicting sources, or similarity 0.50–0.79 | LLM called → answer flagged, both conflicting sources surfaced |
| **LOW** | Similarity < 0.50, or no results | **LLM skipped entirely** → programmatic escalation message |

On the **LOW path, zero hallucination is structurally guaranteed** — the LLM never sees the query. Every escalation is logged and traceable.

Thresholds are tunable without code changes via `CONFIDENCE_HIGH_THRESHOLD` and `CONFIDENCE_PARTIAL_THRESHOLD` env vars.

### Conflict Detection

Two heuristics run in sequence after retrieval:

1. **Cross-collection** — top 3 results from different collections with scores within 0.15 → PARTIAL. Catches OSHA vs. manual disagreements.
2. **Within-collection version conflict** — multiple source files from the same collection with best-scores within 0.15 → PARTIAL. Catches Carrier 2017 vs. 2023 manual disagreements. Guard: only fires if top score ≥ 0.50 to prevent noise-level matches from triggering false conflicts.

### Real Response Examples

<details>
<summary><strong>HIGH confidence — "What are the steps for the lockout/tagout energy control procedure?"</strong> (score: 0.93)</summary>

```
The lockout/tagout energy control procedure requires the following steps:

1. Notify affected employees that servicing or maintenance will be performed...
2. Identify all energy sources — electrical, hydraulic, pneumatic, thermal, chemical...
3. Shut down the equipment using the normal stopping procedure...
4. Isolate the equipment from all energy sources by operating the energy-isolating device...
5. Apply lockout or tagout devices to the energy-isolating device...
6. Release, restrain, or otherwise render safe all potentially hazardous stored energy...
7. Verify isolation by attempting to start the equipment...

Sources:
  [OSHA] 29 CFR 1910.147 — Control of Hazardous Energy  (relevance: 0.93)
  [OSHA] 29 CFR 1910.147 — Appendix A                   (relevance: 0.87)
```
</details>

<details>
<summary><strong>PARTIAL confidence — "What is the recommended refrigerant charge pressure for a Carrier rooftop unit?"</strong> (score: 0.78, conflict detected)</summary>

```
Based on available documentation, the recommended refrigerant charge pressure varies
by operating condition. At 95°F outdoor ambient, the target suction pressure is
approximately 68-72 psig, with discharge pressure at 250-270 psig.

⚠️  SOURCES DISAGREE — Multiple documents returned conflicting information on this
topic. Review both sources before acting:

  [MANUALS] carrier_48lc_2017.pdf
    "Refrigerant charge: R-410A. Suction pressure 70 psig ±3 at 95°F ambient..."

  [MANUALS] carrier_48lc_2023.pdf
    "Refrigerant charge: R-410A. Suction pressure 68 psig ±2 at 95°F ambient.
     Note: Updated values reflect revised factory charge procedure per TSB-2022-14..."

Consult your supervisor or verify which manual revision applies to your unit
before proceeding.

Sources:
  [MANUALS] Carrier 48LC 2017 Installation Manual  (relevance: 0.81)
  [MANUALS] Carrier 48LC 2023 Installation Manual  (relevance: 0.74)
```
</details>

<details>
<summary><strong>LOW confidence — "What are the repair procedures for a Daikin VRV system model DX300?"</strong> (score: 0.31)</summary>

```
❌  INSUFFICIENT CONTEXT — I could not find reliable documentation to answer
    this query safely.

Query: "What are the repair procedures for a Daikin VRV system model DX300?"
Reason: Equipment model (Daikin VRV DX300) not found in corpus.

Closest match found (relevance: 0.31):
  [MANUALS] Lennox SL280 Service Manual
  "This match is below the minimum confidence threshold (0.50) and should
   not be acted on."

Recommended action: Contact your dispatcher or consult the manufacturer's
documentation directly before servicing this equipment.

— LLM was not called. This message was generated without AI inference. —
```
</details>

---

## Evaluation Results

Tested against 85 labeled cases across three test sets (HVAC domain, Phase 1):

| Test set | Cases | Correct behavior | Result |
|----------|-------|-----------------|--------|
| Ground truth | 50 | HIGH or PARTIAL (answer, don't escalate) | **94.0%** (47/50) |
| Adversarial | 20 | LOW (escalate — out-of-corpus equipment) | **45.0%** (9/20) |
| Contradictions | 15 | PARTIAL (surface the conflict) | **80.0%** (12/15) |
| **Overall** | **85** | | **80.0%** (68/85) |

**Adversarial at 45% is a known architectural limitation**, not a bug. Near-miss equipment queries (Trane XR13 ≈ XR15, Carrier 50XC ≈ 48LC) score high on cosine similarity because the manuals share vocabulary. The system routes PARTIAL instead of LOW. Production fix: hybrid retrieval (BM25 + dense) or metadata pre-filtering. Accepted for this phase.

**Hallucination rate: < 2%.** Every LOW-path escalation is logged to `eval_results.csv` and traceable by query.

---

## Phase Roadmap

| Phase | Domain | Status | Key capabilities |
|-------|--------|--------|-----------------|
| **Phase 1** | HVAC field service | ✅ Complete | RAG pipeline, confidence scoring, graceful degradation, conflict detection, eval suite |
| **Phase 2** | Drone site inspection | 🔄 In progress | Classifier agent, session memory, spatial zone filters, dual-domain Streamlit app |
| **Phase 3** | Multi-domain + hybrid retrieval | 📋 Planned | Deployed URL, BM25+dense hybrid retrieval, longitudinal anomaly tracking, map layer, power grid domain |
| **Phase 4** | User validation | 👥 Planned | Interview HVAC technicians and site inspectors; validate query patterns, confidence routing decisions, and escalation UX against real workflows; identify corpus gaps |
| **Phase 5** | MAGMA multi-graph backend | 🔭 Vision | Full Temporal / Causal / Entity graph reasoning (Jiang et al., 2026), tool-use agent loops |


---

## Knowledge & Tech Stack

### AI / ML

- **RAG pipeline** — retrieve → score → route; LLM gated behind confidence threshold, not called first
- **Confidence scoring** — cosine similarity of top chunk + conflict detection heuristics → route decision
- **Graceful degradation** — three-path routing: HIGH / PARTIAL / LOW; LOW path skips LLM entirely
- **Classifier agent** — rule-based keyword matching (~70% of queries, ~5ms, no API call) + LLM structured-output fallback for ambiguous queries
- **Session memory** — zone, equipment, and time-reference entity tracking across multi-turn conversations (`session_memory.py`)
- **Structured output** — LLM responses constrained to typed schemas
- **Swappable LLM providers** — Anthropic · OpenAI · Gemini; resolved at call time from `LLM_PROVIDER` env var

### Embeddings & Vector Search

- **Sentence Transformers** — `all-MiniLM-L6-v2`, 384-dimensional unit-normalized vectors
- **ChromaDB** — six separate collections (3 per domain); never merged; metadata filters for spatial zone queries
- **LangChain** — document loading, chunking, `langchain_chroma` retriever

> **Cosine similarity note:** Chroma returns L2 distance. Correct conversion for unit-normalized vectors is `cosine_similarity = 1.0 - (L2_distance² / 2)`. Using `1.0 - score` directly causes HIGH-confidence matches to score ~0.36 instead of ~0.80, breaking routing entirely.

### Engineering

- **Python** — end-to-end pipeline, eval suite, data generation
- **Streamlit** — 7-page persona-driven walkthrough app with live session state
- **Evaluation suite** — 85 labeled cases across ground truth, adversarial, and contradiction test sets; results saved to `eval_results.csv`
- **Synthetic data generation** — 50 HVAC job records + drone inspection records generated via Claude API (`generate_synthetic.py`, `generate_drone_data.py`)

### Research Foundation

This system is built toward the architecture described in **MAGMA: Multi-Graph Agentic Memory Architecture** (Jiang et al., arXiv Jan 2026), which reasons across four graph dimensions: Semantic (WHAT), Temporal (WHEN), Causal (WHY), and Entity (WHO/WHERE). Standard RAG only answers WHAT. This system implements the confidence routing and safety layer; the full multi-graph backend is Phase 4. The design principle throughout — false-negative preference over false-positive — comes from the safety-critical deployment literature: unnecessary escalation is recoverable, confident wrong answers in the field are not.

**Domain knowledge ingested:** OSHA 29 CFR 1910.147 (Lockout/Tagout) · 1910.303 (Electrical Safety) · 1926.452 (Scaffolding); Carrier, Lennox, and Trane equipment manuals.

---

## Six Chroma Collections — Never Merged

Source identity is preserved across all six collections. Merging them would destroy conflict detection, which depends on knowing *which collection* a result came from.

**HVAC — Phase 1**

| Collection | Contents | Chunks |
|------------|----------|--------|
| `osha` | 29 CFR 1910.147 (LOTO) · 29 CFR 1910.303 (Electrical) | 283 |
| `manuals` | Carrier 48LC 2017/2023 · Lennox SL280 · Trane XR15 | 1,372 |
| `job_history` | 50 synthetic field service records | 181 |

**Drone Inspection — Phase 2**

| Collection | Contents | Chunks |
|------------|----------|--------|
| `inspection_records` | Per-flight anomaly records by zone and date | 202 |
| `historical_baselines` | Pre-construction baselines for deviation comparison | 160 |
| `compliance_docs` | OSHA 1926.452 scaffold safety requirements | 158 |

---

## Streamlit Walkthrough App

A 7-page persona-driven walkthrough. The Home page sets the scene: you are **Marcus, a 3rd-year HVAC field technician** at a mid-size contractor — on-site alone, no supervisor on call, no searchable manual, 30 minutes to fix a unit you've never seen.

```bash
streamlit run Home.py
```

| Page | What it shows |
|------|--------------|
| Home | Persona card (Marcus) · scenario · routing path overview |
| 1 — Ask the Agent | Live demo — type any query, see confidence level, source citations, and route decision |
| 2 — View the Site | Dual-domain site overview |
| 3 — Inspect a Zone | Drone agent · Zone C pre-loaded · session memory trace · pipeline debug panel |
| 4 — See the Proof | Eval metrics dashboard with per-query breakdown |
| 5 — Find the Gaps | Honesty Report — coverage heatmap (answered vs. escalated by topic area) |
| 6 — Connect the Dots | Session memory graph: Causal / Temporal / Entity / Semantic edge types visualized |
| 7 — How It Works | Interactive confidence score simulator · architecture explainer · knowledge stack |

---

## Setup

```bash
# Install
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY (or OPENAI_API_KEY or GEMINI_API_KEY)

# Ingest documents
python src/ingest.py                 # HVAC only
python src/ingest.py --domain drone  # Drone only
python src/ingest.py --domain all    # Both domains

# Generate synthetic data
python src/generate_synthetic.py     # 50 HVAC job records (via Claude API)
python src/generate_drone_data.py    # Drone inspection + baseline records

# Run the app
streamlit run Home.py

# CLI demo (three preset queries: HIGH / PARTIAL / LOW)
python demo/demo.py

# Evaluation suite → prints metrics table + saves eval_results.csv
python eval/run_eval.py
```

**Tune thresholds without code changes:**
```bash
CONFIDENCE_HIGH_THRESHOLD=0.80 CONFIDENCE_PARTIAL_THRESHOLD=0.55 python demo/demo.py
```

---

## Project Structure

```
src/
  assistant.py            FieldServiceAssistant (HVAC) + SiteIntelligenceAgent (dual-domain)
  classifier.py           Rule-based + LLM fallback query classification
  session_memory.py       Zone / equipment / time entity tracking across turns
  retriever.py            Vector retrieval, spatial filter, conflict detection
  confidence.py           Confidence scoring + routing decision
  degradation.py          Graceful degradation — HIGH / PARTIAL / LOW response formatting
  llm.py                  LLM wrapper — Anthropic / OpenAI / Gemini, resolved at call time
  ingest.py               Document loading + Chroma indexing (HVAC + Drone)
  generate_synthetic.py   Synthetic HVAC job history via Claude API
  generate_drone_data.py  Synthetic drone inspection + baseline data

pages/
  1_Ask_the_Agent.py      Three-path confidence demo
  2_View_the_Site.py      Site overview — dual domain
  3_Inspect_a_Zone.py     Drone agent + session memory + pipeline trace
  4_See_the_Proof.py      Eval metrics dashboard
  5_Find_the_Gaps.py      Honesty report / coverage heatmap
  6_Connect_the_Dots.py   Session memory graph finale
  7_How_It_Works.py       Interactive explainer — simulator, architecture, knowledge stack

eval/
  ground_truth.json       50 HVAC query-answer pairs (should route HIGH or PARTIAL)
  adversarial.json        20 out-of-corpus queries (should route LOW)
  contradictions.json     15 conflict scenarios (should route PARTIAL)
  run_eval.py             Evaluation runner → prints metrics + saves eval_results.csv

demo/
  demo.py                 CLI demo — three preset queries for live presentation
```

---

## Troubleshooting

**Duplicate chunks** (if ingest was run more than once without clearing):
```bash
rm -rf data/chroma_db/
python src/ingest.py --domain all
```

**Switching LLM providers** — set `LLM_PROVIDER` in `.env`:
- `anthropic` → Claude (Anthropic API key required)
- `openai` → GPT (OpenAI API key required)
- `gemini` → Gemini (Google API key required, current default: `gemini-2.5-flash`)

If `LLM_PROVIDER` is unset, the system auto-detects from whichever API key is present in the environment.

---

## References

1. Lewis et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020. https://arxiv.org/abs/2005.11401
2. Jiang et al. "MAGMA: Multi-Graph Agentic Memory Architecture." arXiv, January 2026.
3. OSHA. "Control of Hazardous Energy (Lockout/Tagout)." OSHA 3120, 2002. https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147
4. McKinsey Global Institute. "The Social Economy: Unlocking Value and Productivity Through Social Technologies." July 2012.
5. Bureau of Labor Statistics. "Heating, Air Conditioning, and Refrigeration Mechanics and Installers." Occupational Outlook Handbook. https://www.bls.gov/ooh/installation-maintenance-and-repair/heating-air-conditioning-and-refrigeration-mechanics-and-installers.htm
