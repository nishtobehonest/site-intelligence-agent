"""
shared.py
---------
Registry and UI helpers shared across all dashboard pages.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------

AGENTS = {
    "hvac": {
        "name": "HVAC Site Intelligence Agent",
        "domain": "HVAC",
        "phase": "Phase 1",
        "tagline": "RAG pipeline with graceful degradation for field technicians",
        "why_it_matters": (
            "Most RAG systems answer every query — even when they shouldn't. "
            "This agent scores its own confidence before calling the LLM. "
            "LOW-confidence queries skip the model entirely: no hallucination, "
            "just a clean escalation. In a safety-critical environment, "
            "a wrong answer is worse than no answer. "
            "\n\n"
            "**For interviewers:** The confidence scoring and routing logic in "
            "`src/confidence.py` and `src/degradation.py` is the differentiator. "
            "The LLM is the last step, not the first."
        ),
        "metrics": {
            "eval_cases": 85,
            "overall_pass": "80.0%",
            "coverage": "94.0%",
            "hallucination": "<2%",
        },
    },
    "drone": {
        "name": "Drone Site Intelligence Agent",
        "domain": "Drone Inspection",
        "phase": "Phase 2",
        "tagline": "Multi-agent pipeline with spatial filters and session memory",
        "why_it_matters": (
            "Phase 2 adds a classifier agent that runs before retrieval — "
            "classifying query intent (ANOMALY_QUERY / COMPLIANCE_LOOKUP / "
            "HISTORICAL_LOOKUP / OUT_OF_SCOPE) and routing to the right "
            "Chroma collections. Spatial metadata filtering means a Zone-C "
            "question only retrieves Zone-C records. "
            "\n\n"
            "Session memory resolves follow-up questions: 'What about last month?' "
            "works because the agent remembers which zone you just asked about. "
            "\n\n"
            "**For interviewers:** This is the multi-agent handoff pattern — "
            "classifier → retrieval agent → confidence scorer → router. "
            "Each boundary is an explicit interface, not a monolith."
        ),
        "metrics": {},
    },
}

# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

BADGE_COLORS = {
    "HIGH":    ("#15803d", "white"),
    "PARTIAL": ("#b45309", "white"),
    "LOW":     ("#b91c1c", "white"),
}


def confidence_badge_html(level: str, top_score: float) -> str:
    bg, fg = BADGE_COLORS.get(level, ("#888", "white"))
    return (
        f'<span style="background:{bg};color:{fg};padding:5px 16px;'
        f'border-radius:4px;font-weight:bold;font-size:0.95rem">'
        f'{level} CONFIDENCE</span>'
        f'&nbsp;&nbsp;<span style="color:#aaa;font-size:0.9rem">'
        f'similarity score: {top_score:.2f}</span>'
    )


def render_escalation_warning(route_type: str) -> None:
    if route_type == "LOW":
        st.error(
            "No reliable documentation found for this query. "
            "Contact your office or supervisor before proceeding."
        )
    elif route_type == "PARTIAL":
        st.warning("Conflicting sources detected. Verify this answer before acting.")


def render_source_expander(sources: str, route_type: str) -> None:
    if sources and sources.strip() and sources != "None" and route_type != "LOW":
        with st.expander("Sources", expanded=True):
            st.text(sources)


def render_why_it_matters(agent_key: str) -> None:
    agent = AGENTS.get(agent_key, {})
    why = agent.get("why_it_matters", "")
    if why:
        with st.expander("Why this matters (for interviewers / employers)", expanded=False):
            st.markdown(why)
