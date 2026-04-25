"""
pages/1_HVAC_Agent.py
----------------------
HVAC Site Intelligence Agent — query UI with pipeline trace.
"""

import os
import streamlit as st
from src.assistant import FieldServiceAssistant
from pages.shared import confidence_badge_html, render_escalation_warning, render_source_expander, render_why_it_matters
from pages._why_it_matters_content import render as render_why_it_matters_visual

st.set_page_config(page_title="HVAC Agent", page_icon="🔧", layout="wide")

# ---------------------------------------------------------------------------
# Preset queries
# ---------------------------------------------------------------------------

PRESETS = [
    {
        "label": "HIGH — Lockout/Tagout",
        "query": "What are the steps for the lockout tagout energy control procedure?",
    },
    {
        "label": "PARTIAL — Carrier Refrigerant",
        "query": "What is the recommended refrigerant charge pressure for a Carrier rooftop unit?",
    },
    {
        "label": "LOW — Daikin VRV",
        "query": "What are the repair procedures for a Daikin VRV system model DX300?",
    },
]

# ---------------------------------------------------------------------------
# Load assistant (cached per server session)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading HVAC knowledge base...")
def load_assistant():
    return FieldServiceAssistant()

# ---------------------------------------------------------------------------
# Pipeline trace builder
# ---------------------------------------------------------------------------

def build_hvac_trace(result: dict) -> dict:
    """Reconstruct pipeline trace from the result dict."""
    high_threshold = float(os.getenv("CONFIDENCE_HIGH_THRESHOLD", 0.75))
    partial_threshold = float(os.getenv("CONFIDENCE_PARTIAL_THRESHOLD", 0.50))
    level = result["confidence_level"]
    score = result["top_score"]

    if level == "LOW":
        branch = f"score {score:.2f} < partial threshold {partial_threshold:.2f}"
        llm_called = False
    elif level == "PARTIAL":
        if score >= high_threshold:
            branch = f"score {score:.2f} ≥ high threshold but conflict detected → PARTIAL"
        else:
            branch = f"score {score:.2f} in partial range [{partial_threshold:.2f}, {high_threshold:.2f})"
        llm_called = True
    else:
        branch = f"score {score:.2f} ≥ high threshold {high_threshold:.2f}, no conflict"
        llm_called = True

    return {
        "retrieve": "Searched osha, manuals, job_history collections",
        "score": branch,
        "llm": "Called" if llm_called else "Skipped (LOW path — no hallucination)",
        "route": result["route_type"],
    }

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🔧 HVAC Site Intelligence Agent")
st.caption("Phase 1 · RAG + confidence scoring + graceful degradation")

st.markdown(
    """
    <style>
    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        letter-spacing: 0.02em;
        color: #6B7280;
        border-bottom: 3px solid transparent;
        transition: color 0.15s, border-color 0.15s;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #0086A8;
        border-bottom: 3px solid #0086A8;
        background: rgba(0, 134, 168, 0.06);
        border-radius: 6px 6px 0 0;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover {
        color: #1A1A2E;
        border-bottom: 3px solid #CBD5E1;
    }
    div[data-testid="stTabs"] div[role="tablist"] {
        border-bottom: 1px solid #E2E8F0;
        gap: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — threshold display
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Confidence thresholds")
    st.markdown(
        f"**HIGH ≥** `{os.getenv('CONFIDENCE_HIGH_THRESHOLD', '0.75')}`  \n"
        f"**PARTIAL ≥** `{os.getenv('CONFIDENCE_PARTIAL_THRESHOLD', '0.50')}`  \n"
        f"*(set in `.env` or as env vars)*"
    )
    st.markdown("---")
    render_why_it_matters("hvac")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_agent, tab_why = st.tabs(["🔧 Ask a Question", "💡 Why It Matters"])

with tab_agent:
    st.markdown("")

    # Preset buttons
    st.markdown("**Quick demos — one per routing path:**")
    btn_cols = st.columns(3)
    for i, preset in enumerate(PRESETS):
        if btn_cols[i].button(preset["label"], use_container_width=True):
            st.session_state["hvac_query"] = preset["query"]

    st.markdown("")

    # Layout: input left, output right
    col_in, col_out = st.columns([2, 3])

    with col_in:
        query = st.text_area(
            "Technician question",
            value=st.session_state.get("hvac_query", ""),
            height=120,
            placeholder="Ask about equipment procedures, OSHA requirements, or job history...",
            key="hvac_input",
        )
        submit = st.button("Ask", type="primary", use_container_width=True)

    with col_out:
        if submit and query.strip():
            assistant = load_assistant()

            with st.spinner("Retrieving documents and generating response..."):
                result = assistant.ask(query)

            # Badge
            st.markdown(
                confidence_badge_html(result["confidence_level"], result["top_score"]),
                unsafe_allow_html=True,
            )
            st.markdown("")

            # Pipeline trace
            trace = build_hvac_trace(result)
            with st.status("Pipeline trace", expanded=True):
                st.markdown(f"**1. Retrieve:** {trace['retrieve']}")
                st.markdown(f"**2. Score:** {trace['score']}")
                st.markdown(f"**3. LLM:** {trace['llm']}")
                st.markdown(f"**4. Route:** `{trace['route']}`")

            st.markdown("---")

            # Answer
            response_text = result["response"]
            if "\n\nSources:\n" in response_text:
                answer_text, _ = response_text.split("\n\nSources:\n", 1)
            else:
                answer_text = response_text
            st.markdown(answer_text)

            render_source_expander(result["sources"], result["route_type"])
            render_escalation_warning(result["route_type"])
        elif not submit:
            st.markdown("*Results will appear here after you submit a query.*")

with tab_why:
    render_why_it_matters_visual()
