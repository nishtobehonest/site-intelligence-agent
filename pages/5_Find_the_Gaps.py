"""
pages/5_Find_the_Gaps.py
------------------------
Honesty Report / knowledge gap map for drone inspection records.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import streamlit as st
from src.ui.shared import render_next_step, render_walkthrough_banner, render_walkthrough_progress

st.set_page_config(page_title="Find the Gaps", page_icon="🧭", layout="wide")

DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "drone" / "inspection_records.json"

PROBLEM_TYPES = [
    "thermal-hotspot",
    "corrosion",
    "blockage",
    "overheating",
    "panel-hotspot",
    "refrigerant-leak",
    "exposed-wiring",
    "pipe-separation",
]


@st.cache_data
def load_records() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open() as f:
        return json.load(f)


records = load_records()
zones = ["Zone-A", "Zone-B", "Zone-C", "Zone-D", "Zone-E"]
coverage: dict[str, set[str]] = defaultdict(set)
for record in records:
    coverage[record["zone_id"]].add(record["anomaly_type"])

render_walkthrough_progress(5)

st.title("🧭 Find the Gaps")
st.caption("Step 5 · The Honesty Report")
render_walkthrough_banner(
    5,
    "You're seeing where the system chose silence over a guess.",
    "Every red cell is a place where a technician's question would trigger escalation instead of a hallucinated answer.",
)

st.markdown(
    """
    ### The Honesty Report

    These are the questions the system refused to answer rather than guess.
    Every red cell is a hallucination that did not happen.
    """
)

if not records:
    st.warning("Drone inspection records were not found. Add data/raw/drone/inspection_records.json to populate this page.")
else:
    selected_zone = st.session_state.get("walkthrough_zone")
    if selected_zone == "Zone-C":
        st.info("You just asked about Zone C. Its row is highlighted below.")

    header_cols = st.columns([1.25] + [1] * len(PROBLEM_TYPES))
    header_cols[0].markdown("**Inspection Zone**")
    for col, problem in zip(header_cols[1:], PROBLEM_TYPES):
        col.markdown(f"**{problem.replace('-', ' ')}**")

    clicked_key = "selected_gap_cell"
    for zone in zones:
        row_cols = st.columns([1.25] + [1] * len(PROBLEM_TYPES))
        label = f"**→ {zone}**" if zone == selected_zone else f"**{zone}**"
        row_cols[0].markdown(label)
        for col, problem in zip(row_cols[1:], PROBLEM_TYPES):
            has_data = problem in coverage[zone]
            if has_data:
                col.success("Covered")
            else:
                if col.button("Gap", key=f"gap_{zone}_{problem}", use_container_width=True):
                    st.session_state[clicked_key] = (zone, problem)

    selected = st.session_state.get(clicked_key)
    if selected:
        zone, problem = selected
        st.markdown("---")
        st.error(
            f"No records for **{problem.replace('-', ' ')}** in **{zone}**. "
            "A query here would return LOW — Escalate to supervisor. "
            "The system does not have sufficient documentation to answer this safely."
        )

render_next_step(
    "pages/6_Connect_the_Dots.py",
    "Next: Connect the Dots →",
    "Now see how the system connects inspections across time, zone, cause, and responsibility.",
)
