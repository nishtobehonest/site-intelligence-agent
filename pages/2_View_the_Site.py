"""
pages/2_View_the_Site.py
------------------------
Site overview page for the walkthrough.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import streamlit as st
from src.ui.shared import render_next_step, render_walkthrough_banner, render_walkthrough_progress

st.set_page_config(page_title="View the Site", page_icon="🗺️", layout="wide")

DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "drone" / "inspection_records.json"
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
SEVERITY_COLORS = {
    "HIGH": ("#b91c1c", "#fef2f2"),
    "MEDIUM": ("#b45309", "#fffbeb"),
    "LOW": ("#15803d", "#f0fdf4"),
}


@st.cache_data
def load_records() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open() as f:
        return json.load(f)


def worst_severity(records: list[dict]) -> str:
    if not records:
        return "LOW"
    return max((r["severity"] for r in records), key=lambda s: SEVERITY_RANK.get(s, 0))


records = load_records()
by_zone: dict[str, list[dict]] = defaultdict(list)
for record in records:
    by_zone[record["zone_id"]].append(record)

render_walkthrough_progress(2)

st.title("🗺️ View the Site")
st.caption("Step 2 · Zoom out from one unit to the whole inspection site")
render_walkthrough_banner(
    2,
    "You're looking at your site.",
    "Every zone is color-coded by the worst anomaly found there. Zone C is flagged HIGH.",
)

if not records:
    st.warning("Drone inspection records were not found. Add data/raw/drone/inspection_records.json to populate this page.")
else:
    zones = sorted(by_zone)
    cols = st.columns(len(zones))
    for col, zone in zip(cols, zones):
        zone_records = by_zone[zone]
        severity = worst_severity(zone_records)
        color, bg = SEVERITY_COLORS[severity]
        counts = Counter(r["severity"] for r in zone_records)
        border = "3px solid #1A1A2E" if zone == "Zone-C" else f"1.5px solid {color}"
        with col:
            st.markdown(
                f"""
                <div style="background:{bg};border:{border};border-radius:14px;padding:1rem;
                            min-height:190px;">
                  <p style="margin:0;color:#6B7280;font-size:0.75rem;font-weight:800;
                            letter-spacing:0.08em;text-transform:uppercase;">Inspection Zone</p>
                  <h3 style="margin:0.25rem 0 0.6rem 0;color:#1A1A2E;">{zone}</h3>
                  <p style="margin:0 0 0.7rem 0;color:{color};font-weight:800;">{severity} risk</p>
                  <p style="margin:0;color:#4B5563;font-size:0.9rem;line-height:1.45;">
                    {len(zone_records)} records<br>
                    HIGH: {counts.get("HIGH", 0)} · MEDIUM: {counts.get("MEDIUM", 0)} · LOW: {counts.get("LOW", 0)}
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    zone_c_records = sorted(by_zone.get("Zone-C", []), key=lambda r: r["flight_date"], reverse=True)
    st.subheader("Zone C is the walkthrough hotspot")
    if zone_c_records:
        latest = zone_c_records[0]
        st.markdown(
            f"""
            **Latest Zone C finding:** `{latest["record_id"]}` · `{latest["flight_date"]}` ·
            `{latest["equipment_type"]}` · `{latest["anomaly_type"]}` · **{latest["severity"]}**

            {latest["inspector_notes"][:520]}...
            """
        )

    if st.button("Investigate Zone C →", type="primary", use_container_width=True):
        st.session_state["walkthrough_zone"] = "Zone-C"
        st.session_state["walkthrough_zone_query"] = "What anomalies were found in Zone-C during the last inspection?"
        st.session_state["walkthrough_arrived_from_zone"] = True
        if hasattr(st, "switch_page"):
            st.switch_page("pages/3_Inspect_a_Zone.py")
        else:
            st.success("Zone C selected. Continue to Inspect a Zone from the sidebar.")

render_next_step(
    "pages/3_Inspect_a_Zone.py",
    "Next: Inspect a Zone →",
    "Ask the system what you're walking into before you dispatch yourself to Zone C.",
)
