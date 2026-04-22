"""
app.py
------
Home / landing page for the Site Intelligence Agent portfolio dashboard.
"""

try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

import streamlit as st

st.set_page_config(
    page_title="Site Intelligence Agent",
    page_icon="🛰️",
    layout="wide",
)

# Light-theme palette
ACCENT      = "#0086A8"
TEXT        = "#1A1A2E"
MUTED       = "#6B7280"
SECONDARY   = "#F0F2F6"
BORDER      = "#E2E8F0"
GREEN       = "#15803d"
GREEN_BG    = "#f0fdf4"
GREEN_BORDER= "#86efac"
AMBER       = "#b45309"
AMBER_BG    = "#fffbeb"
AMBER_BORDER= "#d97706"
RED         = "#b91c1c"
RED_BG      = "#fef2f2"
RED_BORDER  = "#fca5a5"

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div style="padding:3rem 0 1.5rem 0;max-width:780px;">
      <p style="color:{ACCENT};font-size:0.8rem;font-weight:700;letter-spacing:0.14em;
                text-transform:uppercase;margin:0 0 0.75rem 0;">
        Cornell MEM Capstone · Nishchay Vishwanath · April 2026
      </p>
      <h1 style="font-size:3rem;font-weight:800;color:{TEXT};line-height:1.1;margin:0 0 1rem 0;">
        AI that knows<br>what it doesn't know.
      </h1>
      <p style="font-size:1.1rem;color:{MUTED};line-height:1.7;margin:0 0 1rem 0;max-width:620px;">
        Most AI systems generate an answer to every query — even when they shouldn't.
        This system scores its own retrieval confidence before calling the LLM,
        and routes low-confidence queries to escalation instead of hallucinating.
        In safety-critical field work, a wrong answer is worse than no answer.
      </p>
      <p style="font-size:0.95rem;color:{MUTED};line-height:1.6;margin:0;max-width:620px;">
        Built across two domains: <strong style="color:{TEXT};">HVAC field service</strong>
        (Phase 1, complete) and
        <strong style="color:{TEXT};">drone site inspection</strong> (Phase 2, in progress).
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ---------------------------------------------------------------------------
# The core innovation — three routing paths
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div style="margin:1.5rem 0 1.25rem 0;">
      <p style="color:{ACCENT};font-size:0.78rem;font-weight:700;letter-spacing:0.12em;
                text-transform:uppercase;margin:0 0 0.4rem 0;">The core innovation</p>
      <h2 style="font-size:1.75rem;font-weight:700;color:{TEXT};margin:0 0 0.4rem 0;">
        Every query gets one of three responses — and the system decides which before calling the LLM.
      </h2>
      <p style="color:{MUTED};font-size:0.95rem;margin:0 0 1.5rem 0;max-width:620px;">
        Confidence is scored against retrieved documents. The routing decision is deterministic —
        not a prompt instruction the model might ignore.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

r1, r2, r3 = st.columns(3, gap="medium")

with r1:
    st.markdown(
        f"""
        <div style="background:{GREEN_BG};border:1.5px solid {GREEN_BORDER};border-radius:10px;
                    padding:1.4rem;height:100%;">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
            <span style="background:{GREEN};color:white;font-size:0.68rem;font-weight:700;
                         padding:3px 10px;border-radius:4px;letter-spacing:0.05em;">HIGH</span>
            <span style="font-size:1rem;">✅</span>
          </div>
          <p style="color:{TEXT};font-weight:700;font-size:0.98rem;margin:0 0 0.4rem 0;">
            Confident. Cited. Act on it.
          </p>
          <p style="color:{MUTED};font-size:0.85rem;line-height:1.55;margin:0 0 0.9rem 0;">
            Retrieval score ≥ 0.75, no conflicting sources.
            LLM generates a grounded answer with explicit citations.
          </p>
          <p style="color:{GREEN};font-size:0.8rem;margin:0;font-style:italic;
                    border-top:1px solid {GREEN_BORDER};padding-top:0.65rem;">
            "Steps for lockout/tagout?" → score 0.93, 29 CFR 1910.147 cited
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r2:
    st.markdown(
        f"""
        <div style="background:{AMBER_BG};border:1.5px solid {AMBER_BORDER};border-radius:10px;
                    padding:1.4rem;height:100%;">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
            <span style="background:{AMBER};color:white;font-size:0.68rem;font-weight:700;
                         padding:3px 10px;border-radius:4px;letter-spacing:0.05em;">PARTIAL</span>
            <span style="font-size:1rem;">⚠️</span>
          </div>
          <p style="color:{TEXT};font-weight:700;font-size:0.98rem;margin:0 0 0.4rem 0;">
            Conflict detected. Verify before acting.
          </p>
          <p style="color:{MUTED};font-size:0.85rem;line-height:1.55;margin:0 0 0.9rem 0;">
            Sources disagree or score is borderline. LLM answers,
            but the conflict is surfaced explicitly for review.
          </p>
          <p style="color:{AMBER};font-size:0.8rem;margin:0;font-style:italic;
                    border-top:1px solid {AMBER_BORDER};padding-top:0.65rem;">
            "Carrier refrigerant pressure?" → 2017 vs 2023 manual conflict
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r3:
    st.markdown(
        f"""
        <div style="background:{RED_BG};border:1.5px solid {RED_BORDER};border-radius:10px;
                    padding:1.4rem;height:100%;">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
            <span style="background:{RED};color:white;font-size:0.68rem;font-weight:700;
                         padding:3px 10px;border-radius:4px;letter-spacing:0.05em;">LOW</span>
            <span style="font-size:1rem;">🚫</span>
          </div>
          <p style="color:{TEXT};font-weight:700;font-size:0.98rem;margin:0 0 0.4rem 0;">
            Unknown. LLM skipped entirely.
          </p>
          <p style="color:{MUTED};font-size:0.85rem;line-height:1.55;margin:0 0 0.9rem 0;">
            Score below threshold — no reliable docs found.
            The LLM is never called. Zero hallucination risk by design.
          </p>
          <p style="color:{RED};font-size:0.8rem;margin:0;font-style:italic;
                    border-top:1px solid {RED_BORDER};padding-top:0.65rem;">
            "Daikin VRV DX300 repair?" → score 0.31, escalate to supervisor
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div style="margin:1.5rem 0 1.25rem 0;">
      <p style="color:{ACCENT};font-size:0.78rem;font-weight:700;letter-spacing:0.12em;
                text-transform:uppercase;margin:0 0 0.4rem 0;">Evaluation results</p>
      <h2 style="font-size:1.75rem;font-weight:700;color:{TEXT};margin:0 0 0.3rem 0;">
        Measured across 85 test cases.
      </h2>
      <p style="color:{MUTED};font-size:0.92rem;margin:0 0 1.25rem 0;">
        Ground truth coverage · adversarial robustness · contradiction surfacing
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Eval cases", "85")
m2.metric("Overall pass rate", "80.0%")
m3.metric("Coverage (GT)", "94.0%")
m4.metric("Hallucination rate", "<2%")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------------------------
# Navigation cards
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div style="margin:1.5rem 0 1.25rem 0;">
      <p style="color:{ACCENT};font-size:0.78rem;font-weight:700;letter-spacing:0.12em;
                text-transform:uppercase;margin:0 0 0.4rem 0;">Two phases</p>
      <h2 style="font-size:1.75rem;font-weight:700;color:{TEXT};margin:0 0 0.3rem 0;">
        Explore the system.
      </h2>
      <p style="color:{MUTED};font-size:0.92rem;margin:0 0 1.25rem 0;">
        Each agent is live — try the preset queries to see HIGH, PARTIAL, and LOW routing in action.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.markdown(
        f"""
        <div style="background:{SECONDARY};border:1.5px solid {ACCENT};border-radius:10px;
                    padding:1.4rem;height:100%;">
          <p style="color:{ACCENT};font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                    text-transform:uppercase;margin:0 0 0.4rem 0;">Phase 1 · Complete</p>
          <p style="color:{TEXT};font-weight:700;font-size:1.05rem;margin:0 0 0.4rem 0;">
            🔧 HVAC Field Service Agent
          </p>
          <p style="color:{MUTED};font-size:0.85rem;line-height:1.5;margin:0 0 1rem 0;">
            RAG pipeline with confidence scoring and graceful degradation.
            Retrieves from OSHA regulations, equipment manuals (Carrier, Lennox, Trane),
            and job history. Includes a <em>Why It Matters</em> visual explainer tab.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.page_link("pages/1_HVAC_Agent.py", label="Open HVAC Agent →")

with c2:
    st.markdown(
        f"""
        <div style="background:{SECONDARY};border:1.5px solid {BORDER};border-radius:10px;
                    padding:1.4rem;height:100%;">
          <p style="color:{MUTED};font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                    text-transform:uppercase;margin:0 0 0.4rem 0;">Phase 2 · In progress</p>
          <p style="color:{TEXT};font-weight:700;font-size:1.05rem;margin:0 0 0.4rem 0;">
            🚁 Drone Site Intelligence Agent
          </p>
          <p style="color:{MUTED};font-size:0.85rem;line-height:1.5;margin:0 0 1rem 0;">
            Multi-agent pipeline with classifier, spatial metadata filters,
            and session memory. Answers questions about drone inspection records
            across zones, baselines, and OSHA compliance docs.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.page_link("pages/2_Drone_Agent.py", label="Open Drone Agent →")

with c3:
    st.markdown(
        f"""
        <div style="background:{SECONDARY};border:1.5px solid {BORDER};border-radius:10px;
                    padding:1.4rem;height:100%;">
          <p style="color:{MUTED};font-size:0.72rem;font-weight:700;letter-spacing:0.1em;
                    text-transform:uppercase;margin:0 0 0.4rem 0;">Metrics</p>
          <p style="color:{TEXT};font-weight:700;font-size:1.05rem;margin:0 0 0.4rem 0;">
            📊 Evaluation Dashboard
          </p>
          <p style="color:{MUTED};font-size:0.85rem;line-height:1.5;margin:0 0 1rem 0;">
            85 test cases across three categories: ground truth (known equipment),
            adversarial (out-of-corpus queries), and contradictions (conflicting
            manual versions). Filter by set and pass/fail status.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.page_link("pages/3_Eval_Dashboard.py", label="Open Eval Dashboard →")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <p style="color:{MUTED};font-size:0.8rem;margin:0.5rem 0;">
      Nishchay Vishwanath · Cornell MEM 2026 ·
      RAG + Confidence Routing + Graceful Degradation ·
      <a href="https://github.com/nishtobehonest/field-service-assistant"
         style="color:{ACCENT};text-decoration:none;">GitHub ↗</a>
    </p>
    """,
    unsafe_allow_html=True,
)
