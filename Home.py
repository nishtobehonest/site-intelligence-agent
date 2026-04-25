"""
Home.py
-------
Scenario-driven landing page for the Site Intelligence Agent walkthrough.
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

ACCENT = "#0086A8"
TEXT = "#1A1A2E"
MUTED = "#6B7280"
SECONDARY = "#F0F2F6"
BORDER = "#E2E8F0"
GREEN = "#15803d"
GREEN_BG = "#f0fdf4"
AMBER = "#b45309"
AMBER_BG = "#fffbeb"
RED = "#b91c1c"
RED_BG = "#fef2f2"

st.markdown(
    f"""
    <style>
      @keyframes riseIn {{
        from {{ opacity:0; transform:translateY(10px); }}
        to {{ opacity:1; transform:translateY(0); }}
      }}
      .scenario-line {{
        opacity:0;
        animation:riseIn 0.55s ease forwards;
        color:{TEXT};
        font-size:1.55rem;
        line-height:1.45;
        font-weight:750;
        margin:0 0 0.55rem 0;
      }}
      .delay-1 {{ animation-delay:0.08s; }}
      .delay-2 {{ animation-delay:0.28s; }}
      .delay-3 {{ animation-delay:0.48s; }}
      .delay-4 {{ animation-delay:0.68s; }}
    </style>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.25, 0.75], gap="large")

with left:
    st.markdown(
        f"""
        <p style="color:{ACCENT};font-size:0.78rem;font-weight:800;letter-spacing:0.14em;
                  text-transform:uppercase;margin:1.25rem 0 1rem 0;">
          Cornell MEM Capstone · Nishchay Vishwanath · April 2026
        </p>
        <h1 style="font-size:3.7rem;line-height:1.02;color:{TEXT};font-weight:850;margin:0 0 1.5rem 0;">
          AI that knows<br>what it doesn't know.
        </h1>
        <div style="border-left:4px solid {ACCENT};padding-left:1.1rem;margin:1.5rem 0 1.5rem 0;">
          <p class="scenario-line delay-1">It's 2pm. You're on your fourth job today.</p>
          <p class="scenario-line delay-2">A rooftop unit you've never seen. A model you don't recognize.</p>
          <p class="scenario-line delay-3">The manual is 400 pages in your truck.</p>
          <p class="scenario-line delay-4">A wrong safety answer is worse than no answer.</p>
        </div>
        <p style="font-size:1.15rem;line-height:1.7;color:{MUTED};max-width:680px;margin:0 0 1.4rem 0;">
          This walkthrough puts you in the field technician's seat. The system will answer when
          the evidence is strong, flag conflicts when sources disagree, and stay silent when the
          safe move is escalation.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Ask_the_Agent.py", label="Begin Walkthrough →")

with right:
    st.markdown(
        f"""
        <div style="background:{SECONDARY};border:1px solid {BORDER};border-radius:16px;
                    padding:1.25rem;margin-top:4.2rem;">
          <p style="color:{MUTED};font-size:0.75rem;font-weight:800;letter-spacing:0.12em;
                    text-transform:uppercase;margin:0 0 0.75rem 0;">Routing before generation</p>
          <div style="background:{GREEN_BG};border-left:4px solid {GREEN};padding:0.8rem;
                      border-radius:10px;margin-bottom:0.75rem;">
            <strong style="color:{GREEN};">HIGH - Answer</strong>
            <p style="color:{TEXT};font-size:0.9rem;line-height:1.45;margin:0.25rem 0 0 0;">
              Strong evidence. Call the LLM and cite sources.
            </p>
          </div>
          <div style="background:{AMBER_BG};border-left:4px solid {AMBER};padding:0.8rem;
                      border-radius:10px;margin-bottom:0.75rem;">
            <strong style="color:{AMBER};">PARTIAL - Conflict</strong>
            <p style="color:{TEXT};font-size:0.9rem;line-height:1.45;margin:0.25rem 0 0 0;">
              Sources disagree. Show both and warn the tech.
            </p>
          </div>
          <div style="background:{RED_BG};border-left:4px solid {RED};padding:0.8rem;
                      border-radius:10px;">
            <strong style="color:{RED};">LOW - Silence</strong>
            <p style="color:{TEXT};font-size:0.9rem;line-height:1.45;margin:0.25rem 0 0 0;">
              Evidence is weak. Skip the LLM and escalate.
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption("Built for safety-critical field work: HVAC service, drone inspection, and any workflow where a confident wrong answer is dangerous.")
