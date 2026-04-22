"""
app.py
------
Home / landing page for the Site Intelligence Agent portfolio dashboard.
Multi-page Streamlit app — sidebar nav is auto-generated from pages/.
"""

# Streamlit Cloud ships sqlite3 3.x which is too old for chromadb.
# Override with the bundled pysqlite3-binary before any chromadb import.
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass  # local dev — system sqlite3 is fine

import streamlit as st

st.set_page_config(
    page_title="Site Intelligence Agent",
    page_icon="🛰️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

col_left, col_right = st.columns([3, 2])

with col_left:
    st.title("🛰️ Site Intelligence Agent")
    st.caption("Nishchay Vishwanath  ·  Cornell MEM 2026  ·  April 2026")
    st.markdown(
        "A RAG-based field intelligence system that scores its own confidence "
        "before generating an answer — routing LOW-confidence queries to "
        "escalation instead of hallucinating. Built in two phases: "
        "HVAC field service (Phase 1) and drone site inspection (Phase 2)."
    )

with col_right:
    st.code(
        """\
query
  → classifier()      # intent + spatial entities
  → retrieve()        # filtered Chroma search
  → score_confidence()# HIGH / PARTIAL / LOW
  → llm.generate()    # only if HIGH or PARTIAL
  → route()           # answer or escalate
""",
        language="text",
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------

m1, m2, m3, m4 = st.columns(4)
m1.metric("Eval cases", "85")
m2.metric("Overall pass rate", "80.0%")
m3.metric("Coverage (GT)", "94.0%")
m4.metric("Hallucination rate", "<2%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Navigation cards
# ---------------------------------------------------------------------------

st.subheader("Explore the agents")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### 🔧 HVAC Agent")
    st.markdown(
        "RAG pipeline with confidence scoring and graceful degradation. "
        "Retrieves from OSHA docs, equipment manuals, and job history."
    )
    st.page_link("pages/1_HVAC_Agent.py", label="Open HVAC Agent →")

with c2:
    st.markdown("### 🚁 Drone Agent")
    st.markdown(
        "Multi-agent pipeline with classifier, spatial filters, and "
        "session memory. Answers questions about drone inspection records."
    )
    st.page_link("pages/2_Drone_Agent.py", label="Open Drone Agent →")

with c3:
    st.markdown("### 📊 Eval Dashboard")
    st.markdown(
        "Evaluation results across ground truth, adversarial, and "
        "contradiction scenarios. Filter by set and pass/fail status."
    )
    st.page_link("pages/3_Eval_Dashboard.py", label="Open Eval Dashboard →")
