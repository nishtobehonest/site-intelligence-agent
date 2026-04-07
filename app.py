"""
app.py
------
Streamlit interface for the Field Service Intelligence Assistant.
Wraps FieldServiceAssistant.ask() with a browser UI showing color-coded
confidence routing (HIGH / PARTIAL / LOW) and source citations.

Usage:
    streamlit run app.py
"""

import streamlit as st
from src.assistant import FieldServiceAssistant

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Field Service Intelligence Assistant",
    page_icon="🔧",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Constants
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

BADGE_COLORS = {
    "HIGH":    ("#28a745", "white"),
    "PARTIAL": ("#e6a817", "#1a1a1a"),
    "LOW":     ("#dc3545", "white"),
}

# ---------------------------------------------------------------------------
# Load assistant (cached — loads once per server session)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading knowledge base...")
def load_assistant():
    return FieldServiceAssistant()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🔧 Field Service Intelligence Assistant")
st.caption("Team TBH-20  |  Cornell MEM Capstone  |  April 2026")
st.markdown("---")

# ---------------------------------------------------------------------------
# Preset buttons
# ---------------------------------------------------------------------------

st.markdown("**Quick demos — one for each routing path:**")
cols = st.columns(3)
for i, preset in enumerate(PRESETS):
    if cols[i].button(preset["label"], use_container_width=True):
        st.session_state["query"] = preset["query"]

st.markdown("")

# ---------------------------------------------------------------------------
# Query input
# ---------------------------------------------------------------------------

query = st.text_area(
    "Technician question",
    value=st.session_state.get("query", ""),
    height=100,
    placeholder="Ask about equipment procedures, OSHA requirements, or job history...",
)

submit = st.button("Ask", type="primary")

# ---------------------------------------------------------------------------
# Run and render result
# ---------------------------------------------------------------------------

if submit and query.strip():
    assistant = load_assistant()

    with st.spinner("Retrieving documents and generating response..."):
        result = assistant.ask(query)

    level = result["confidence_level"]
    bg, fg = BADGE_COLORS[level]

    st.markdown("")

    # Confidence badge + score
    st.markdown(
        f'<span style="background:{bg};color:{fg};padding:5px 16px;'
        f'border-radius:4px;font-weight:bold;font-size:0.95rem">'
        f'{level} CONFIDENCE</span>'
        f'&nbsp;&nbsp;<span style="color:#666;font-size:0.9rem">'
        f'similarity score: {result["top_score"]:.2f}</span>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Answer text — split sources out of response for cleaner layout
    response_text = result["response"]
    if "\n\nSources:\n" in response_text:
        answer_text, _ = response_text.split("\n\nSources:\n", 1)
    else:
        answer_text = response_text

    st.markdown(answer_text)

    # Source citations expander (HIGH and PARTIAL only)
    if result["sources"] and result["sources"] != "None":
        with st.expander("Sources", expanded=True):
            st.text(result["sources"])

    # Escalation / warning panel
    if result["route_type"] == "LOW":
        st.error(
            "No reliable documentation found for this query. "
            "Contact your office or supervisor before proceeding."
        )
    elif result["route_type"] == "PARTIAL":
        st.warning("Verify this answer before acting. See sources above.")
