"""
pages/6_Connect_the_Dots.py
---------------------------
Memory graph walkthrough finale.
"""

import streamlit as st
from src.ui.shared import clear_walkthrough_state, render_walkthrough_banner, render_walkthrough_progress

st.set_page_config(page_title="Connect the Dots", page_icon="🕸️", layout="wide")

ACCENT = "#0086A8"
TEXT = "#1A1A2E"
MUTED = "#6B7280"
BORDER = "#E2E8F0"
SECONDARY = "#F0F2F6"

render_walkthrough_progress(6)

st.title("🕸️ Connect the Dots")
st.caption("Step 6 · Memory graph and system architecture")
render_walkthrough_banner(
    6,
    "You're seeing how it all connects.",
    "Four memory types answer why something failed, when it changed, who owns it, and what is affected.",
)

st.info(
    "The Zone C corrosion anomaly from August triggered a follow-up in Zone B three weeks later. "
    "That is a causal edge: the system traces the cause forward in time instead of treating each inspection as isolated."
)

st.markdown(
    f"""
    <div style="border:1px solid {BORDER};border-radius:16px;padding:1.2rem;background:white;">
      <div style="display:grid;grid-template-columns:1fr 0.4fr 1fr 0.4fr 1fr;gap:0.75rem;
                  align-items:center;text-align:center;">
        <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;padding:1rem;">
          <strong style="color:#b91c1c;">Zone C corrosion</strong>
          <p style="color:{MUTED};font-size:0.85rem;margin:0.35rem 0 0 0;">August inspection</p>
        </div>
        <div style="color:#b91c1c;font-weight:900;">caused</div>
        <div style="background:#fffbeb;border:1px solid #d97706;border-radius:12px;padding:1rem;">
          <strong style="color:#b45309;">Follow-up inspection</strong>
          <p style="color:{MUTED};font-size:0.85rem;margin:0.35rem 0 0 0;">Three weeks later</p>
        </div>
        <div style="color:{ACCENT};font-weight:900;">linked to</div>
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:1rem;">
          <strong style="color:#15803d;">Zone B baseline</strong>
          <p style="color:{MUTED};font-size:0.85rem;margin:0.35rem 0 0 0;">Normal comparison</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Four memory links")
c1, c2, c3, c4 = st.columns(4)
c1.metric("WHY", "Causal")
c2.metric("WHEN", "Temporal")
c3.metric("WHO", "Responsibility")
c4.metric("WHAT", "Entity")

st.markdown("---")
st.markdown(
    f"""
    <div style="background:{SECONDARY};border:1px solid {BORDER};border-radius:18px;
                padding:1.4rem;max-width:760px;">
      <h2 style="color:{TEXT};margin:0 0 0.75rem 0;">You've seen the full system.</h2>
      <p style="color:{MUTED};font-size:1.05rem;line-height:1.7;margin:0 0 1rem 0;">
        6 steps · 3 routing paths · 85 test cases · &lt;2% hallucination rate ·
        2 domains · 0 guesses on LOW queries
      </p>
      <p style="color:{TEXT};font-weight:700;margin:0;">
        Built by Nishchay Vishwanath · Cornell MEM 2026
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("← Start over", type="primary"):
    clear_walkthrough_state()
    if hasattr(st, "switch_page"):
        st.switch_page("Home.py")
    else:
        st.success("Walkthrough state cleared. Return to Home from the sidebar.")
