# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What This Project Is

A RAG-based Field Service Intelligence Assistant (Cornell MEM capstone, Team TBH-20, submission April 8 2026). Technicians ask natural-language questions; the system retrieves from three Chroma document collections, scores confidence, and either answers with citations (HIGH), flags conflicting sources (PARTIAL), or escalates without calling the LLM (LOW). The graceful degradation layer is the core differentiator.

**Prototype only** — CLI interface, no auth, no frontend, no production deployment.

---

## Commands

```bash
# Install
pip install -r requirements.txt
cp .env.example .env   # then add ANTHROPIC_API_KEY

# Ingest documents into Chroma (run after adding files to data/raw/)
python src/ingest.py

# Run interactive demo or three preset demo queries
python demo/demo.py

# Generate synthetic job history (50 records via Claude API)
python src/generate_synthetic.py

# Run full evaluation suite → prints metrics table + saves eval_results.csv
python eval/run_eval.py

# Run unit tests
pytest tests/
```

**Tuning confidence thresholds without code changes:**
```bash
CONFIDENCE_HIGH_THRESHOLD=0.80 CONFIDENCE_PARTIAL_THRESHOLD=0.55 python demo/demo.py
```
Or set these in `.env`. Raising `HIGH_THRESHOLD` reduces hallucination risk; raising `PARTIAL_THRESHOLD` increases escalation rate.

---

## Architecture

The pipeline in `src/assistant.py:FieldServiceAssistant.ask()` runs four steps in sequence:

```
query
  → retrieve()           # retriever.py: embed query, search all 3 Chroma collections, return top-k ranked results
  → score_confidence()   # confidence.py: score based on cosine similarity + conflict detection
  → llm.generate()       # llm.py: called ONLY if confidence is HIGH or PARTIAL
  → route()              # degradation.py: format final response based on route type
```

**Three Chroma collections** (`osha`, `manuals`, `job_history`) are kept separate intentionally — merging them would break conflict detection, which relies on identifying that the same query returns high-scoring results from multiple collections with similar scores (`retriever.py:detect_conflicts`).

**Conflict detection heuristic** (`retriever.py:detect_conflicts`): Two heuristics run in sequence:
1. **Cross-collection** (top 3): results from different collections with scores within 0.15 → PARTIAL. Catches OSHA vs manual disagreements.
2. **Within-collection version conflict** (top 6): multiple source *files* from the same collection with best-scores within 0.15 → PARTIAL. Added in Phase 2 to catch Carrier 48LC 2017 vs 2023 conflicts. Guard: only fires if the top source score ≥ 0.50 (prevents noise-level matches from triggering false conflicts).

**LOW path skips the LLM entirely** (`assistant.py:82`). The escalation message is built programmatically in `degradation.py`. Do not change this — calling the LLM on LOW-confidence context is exactly the hallucination scenario the system is designed to prevent.

**LLM provider is swappable** via `LLM_PROVIDER` env var (`anthropic` / `openai` / `gemini`). Currently configured for Gemini. Working model: `gemini-2.5-flash` (gemini-1.5-pro and gemini-2.0-flash are deprecated and return 404).

**Chroma similarity scores**: Chroma returns L2 distance for unit-normalized sentence-transformer vectors. Correct conversion formula is `1.0 - (L2_distance² / 2)` — this gives true cosine similarity. Do NOT use `1.0 - score` (that formula was wrong and caused HIGH-confidence matches to score ~0.36 instead of ~0.80).

---

## Current Data State (Phase 2 Complete)

| Collection | Files | Chunks |
|---|---|---|
| `osha` | 29 CFR 1910.147 (Lockout/Tagout), 29 CFR 1910.303 (Electrical Safety) | 566 |
| `manuals` | Carrier 48LC 2017, Carrier 48LC 2023, Lennox SL280, Trane XR15 | 2,744 |
| `job_history` | synthetic_jobs.json (50 records) | 183 |

Chroma DB lives at `./data/chroma_db/`. Re-run `python src/ingest.py` after adding documents.

> ⚠️ **Duplicate chunks:** `src/ingest.py` was run twice without clearing the collections. Chunk counts are 2× the expected values (osha: 283→566, manuals: 1,372→2,744). Retrieval still functions correctly but may return duplicate chunks. Fix before final submission: drop and re-ingest with `chroma_db/` deleted first.

**LangChain imports updated:** `src/ingest.py` and `src/retriever.py` now use `langchain_chroma` and `langchain_huggingface` (replaces deprecated `langchain_community` classes). Both packages added to `requirements.txt`.

**Demo queries (updated in Phase 1 fix):**
- Demo 1 (HIGH): "What are the steps for the lockout tagout energy control procedure?" — score 0.93
- Demo 2 (PARTIAL): "What is the recommended refrigerant charge pressure for a Carrier rooftop unit?" — score 0.52
- Demo 3 (LOW): "What are the repair procedures for a Daikin VRV system model DX300?" — score 0.31 ✓ now correctly routes LOW

---

## Known Issues

1. ~~**`detect_conflicts` only fires across collection names**~~ — **FIXED in Phase 2.** Within-collection version conflict detection added to `retriever.py:detect_conflicts`. Carrier 2017 vs 2023 conflicts now correctly surface as PARTIAL.

2. **Semantic search cannot distinguish model numbers** — queries about near-miss equipment (Trane XR13, Carrier 50XC, Lennox XC25) score high against in-corpus counterparts (XR15, 48LC, SL280) and route PARTIAL instead of LOW. This is an architectural limitation of dense vector retrieval, not a bug. Accepted and documented. Production fix would require hybrid retrieval (BM25 + dense) or metadata filtering on equipment IDs.

3. **Duplicate chunks in Chroma** — ingest was run twice; all collections have 2× the expected chunk counts. See data state note above.

4. **Carrier 48LC airflow query retrieves Lennox content** — "airflow and static pressure settings for Carrier 48LC" returns Lennox SL280 results at top of ranking (score 0.78) because both manuals have similar airflow table content. No conflict fires. Chunking or query-formulation issue for Phase 3.

---

## Eval Sets (Phase 2 Complete)

All three eval files are fully populated. Baseline metrics from `eval/run_eval.py`:

| File | Size | Correct behavior | Baseline |
|------|------|-----------------|---------|
| `ground_truth.json` | 50 pairs | HIGH or PARTIAL (not LOW) | **94.0%** (47/50) |
| `adversarial.json` | 20 queries | LOW (escalate — no hallucination) | **45.0%** (9/20) |
| `contradictions.json` | 15 scenarios | PARTIAL (conflict surfaced) | **80.0%** (12/15) — after Phase 2 conflict fix |
| **Overall** | **85 cases** | | **80.0%** (68/85) |

**Adversarial at 45% is an accepted known limitation**, not a target to hit via threshold tuning. The failures are semantically similar near-miss equipment (XR13 ≈ XR15, etc.) — unfixable with cosine similarity alone. Score distributions for ground truth passes and adversarial failures overlap; raising `PARTIAL_THRESHOLD` sacrifices coverage faster than it gains adversarial precision.

Metric targets for submission: hallucination < 2%, coverage > 80%, escalation 10–25%.

---

## Key Constraints

- **Three separate Chroma collections — never merge.** Source-aware retrieval and conflict detection depend on this.
- **Every response must cite a source.** No uncited answers.
- **Confidence thresholds are product decisions, not engineering ones.** In a safety-critical context, false positives (confident wrong answer) are more dangerous than false negatives (unnecessary escalation). Tune conservatively.
- **The system prompt in `assistant.py` enforces grounding.** Do not weaken the "answer only from context" and "always cite" instructions.

---

## Future Domain Extensions

The pipeline is domain-agnostic. Swapping the three Chroma collections is sufficient to repurpose it:
- Drone inspection: `inspection_reports` / `flight_logs` / `site_anomalies`
- Power grid construction: `safety_procedures` / `equipment_specs` / `incident_logs`

No changes needed in `confidence.py`, `degradation.py`, or `assistant.py`.
