"""
pages/3_Eval_Dashboard.py
--------------------------
Static eval metrics dashboard. Loads eval_results.csv — no re-running evals.
"""

from pathlib import Path
import pandas as pd
import streamlit as st
from pages.shared import render_why_it_matters

st.set_page_config(page_title="Eval Dashboard", page_icon="📊", layout="wide")

CSV_PATH = Path(__file__).parent.parent / "eval_results.csv"

st.title("📊 Evaluation Dashboard")
st.caption("Phase 1 · Ground truth / adversarial / contradiction scenarios")
st.markdown("---")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@st.cache_data
def load_results() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH)

if not CSV_PATH.exists():
    st.error(f"eval_results.csv not found at {CSV_PATH}. Run `python eval/run_eval.py` first.")
    st.stop()

df = load_results()

# ---------------------------------------------------------------------------
# Top metrics row
# ---------------------------------------------------------------------------

total = len(df)
passed = df["passed"].sum()
overall_pct = passed / total * 100 if total else 0

sets = {
    "ground_truth": "Ground Truth",
    "adversarial": "Adversarial",
    "contradictions": "Contradictions",
}

m_cols = st.columns(4)
m_cols[0].metric("Overall pass rate", f"{overall_pct:.1f}%", f"{int(passed)}/{total} cases")

for i, (set_key, set_label) in enumerate(sets.items(), start=1):
    subset = df[df["set"] == set_key]
    if len(subset):
        pct = subset["passed"].sum() / len(subset) * 100
        m_cols[i].metric(set_label, f"{pct:.1f}%", f"{int(subset['passed'].sum())}/{len(subset)}")
    else:
        m_cols[i].metric(set_label, "—")

st.markdown("---")

# ---------------------------------------------------------------------------
# Per-set breakdown with confidence distribution
# ---------------------------------------------------------------------------

set_cols = st.columns(3)

for col, (set_key, set_label) in zip(set_cols, sets.items()):
    subset = df[df["set"] == set_key]
    with col:
        st.subheader(set_label)
        if len(subset) == 0:
            st.info("No data for this set.")
            continue
        passed_n = int(subset["passed"].sum())
        st.markdown(f"**{passed_n} / {len(subset)} passed**")
        conf_counts = subset["actual_confidence"].value_counts()
        st.bar_chart(conf_counts)

st.markdown("---")

# ---------------------------------------------------------------------------
# Filterable full table
# ---------------------------------------------------------------------------

st.subheader("All results")

filter_cols = st.columns([2, 1])
with filter_cols[0]:
    selected_sets = st.multiselect(
        "Filter by eval set",
        options=list(sets.keys()),
        default=list(sets.keys()),
        format_func=lambda k: sets.get(k, k),
    )
with filter_cols[1]:
    pass_filter = st.selectbox("Filter by result", ["All", "Passed", "Failed"])

filtered = df[df["set"].isin(selected_sets)] if selected_sets else df

if pass_filter == "Passed":
    filtered = filtered[filtered["passed"] == True]
elif pass_filter == "Failed":
    filtered = filtered[filtered["passed"] == False]

def style_confidence(val):
    colors = {"HIGH": "#28a745", "PARTIAL": "#e6a817", "LOW": "#dc3545"}
    color = colors.get(str(val), "#888")
    return f"color: {color}; font-weight: bold"

styled = filtered.style.map(style_confidence, subset=["actual_confidence"])
st.dataframe(styled, use_container_width=True, height=400)

st.markdown("---")

with st.expander("Why measure these three categories separately?", expanded=False):
    st.markdown(
        "A single accuracy number hides the system's failure modes. "
        "**Ground truth** measures coverage — can the system answer questions it should know? "
        "**Adversarial** measures hallucination risk — does it escalate when it has no data? "
        "**Contradictions** measures conflict surfacing — does PARTIAL fire when two sources disagree? "
        "\n\n"
        "Optimizing for one can degrade another: raising the confidence threshold "
        "improves adversarial but kills coverage. These three metrics together describe "
        "the product tradeoff, not just a number."
    )
