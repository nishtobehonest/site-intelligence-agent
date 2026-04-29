"""
pages/2_View_the_Site.py
------------------------
Site overview page for the walkthrough.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from textwrap import dedent

import plotly.graph_objects as go
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
SEV_MARKER_COLORS = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a"}
SEV_MARKER_SIZES  = {"HIGH": 22, "MEDIUM": 18, "LOW": 16}


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


def parse_coordinates(value: str) -> tuple[float, float] | None:
    match = re.search(r"([\d.]+)°\s*([NS]),\s*([\d.]+)°\s*([EW])", value or "")
    if not match:
        return None
    lat = float(match.group(1)) * (-1 if match.group(2) == "S" else 1)
    lon = float(match.group(3)) * (-1 if match.group(4) == "W" else 1)
    return lat, lon


def zone_summary(zone: str, zone_records: list[dict]) -> dict:
    severity = worst_severity(zone_records)
    counts = Counter(r["severity"] for r in zone_records)
    latest = max(zone_records, key=lambda r: r["flight_date"]) if zone_records else {}
    parsed_points = [parse_coordinates(r.get("coordinates", "")) for r in zone_records]
    points = [point for point in parsed_points if point is not None]
    lat = sum(point[0] for point in points) / len(points) if points else 0
    lon = sum(point[1] for point in points) / len(points) if points else 0
    site_counts = Counter(r["site_id"] for r in zone_records)
    site_id = site_counts.most_common(1)[0][0] if site_counts else "Unknown site"

    return {
        "zone": zone,
        "records": len(zone_records),
        "severity": severity,
        "counts": counts,
        "latest": latest,
        "lat": lat,
        "lon": lon,
        "site_id": site_id,
    }


def site_zone_summaries(all_records: list[dict]) -> list[dict]:
    by_site_zone: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in all_records:
        by_site_zone[(record["site_id"], record["zone_id"])].append(record)

    summaries = []
    for (site_id, zone), site_zone_records in sorted(by_site_zone.items()):
        summary = zone_summary(zone, site_zone_records)
        summary["site_id"] = site_id
        summaries.append(summary)
    return summaries


def render_site_map_interactive(summaries: list[dict]) -> str | None:
    """Render an interactive Plotly mapbox map. Returns the clicked zone name or None."""
    fig = go.Figure()

    for sev in ["HIGH", "MEDIUM", "LOW"]:
        rows = [s for s in summaries if s["severity"] == sev]
        if not rows:
            continue
        fig.add_trace(go.Scattermapbox(
            lat=[s["lat"] for s in rows],
            lon=[s["lon"] for s in rows],
            mode="markers",
            marker=dict(
                size=SEV_MARKER_SIZES[sev],
                color=SEV_MARKER_COLORS[sev],
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b>  ·  %{customdata[1]}<br>"
                "Severity: <b>%{customdata[2]}</b><br>"
                "Records: %{customdata[3]}<br>"
                "HIGH: %{customdata[4]}  MED: %{customdata[5]}  LOW: %{customdata[6]}"
                "<extra></extra>"
            ),
            customdata=[
                [
                    s["zone"], s["site_id"], s["severity"],
                    s["records"],
                    s["counts"].get("HIGH", 0),
                    s["counts"].get("MEDIUM", 0),
                    s["counts"].get("LOW", 0),
                ]
                for s in rows
            ],
            name=sev,
            selected=dict(marker=dict(size=30)),
            unselected=dict(marker=dict(opacity=0.45)),
        ))

    lats = [s["lat"] for s in summaries]
    lons = [s["lon"] for s in summaries]
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=sum(lats) / len(lats), lon=sum(lons) / len(lons)),
            zoom=5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=520,
        legend=dict(
            title=dict(text="Severity"),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#CBD5E1",
            borderwidth=1,
        ),
        clickmode="event+select",
    )

    event = st.plotly_chart(
        fig,
        on_select="rerun",
        selection_mode="points",
        use_container_width=True,
    )

    if event and event.selection and event.selection.points:
        return event.selection.points[0]["customdata"][0]
    return None


records = load_records()
by_zone: dict[str, list[dict]] = defaultdict(list)
for record in records:
    by_zone[record["zone_id"]].append(record)

render_walkthrough_progress(2)

st.title("🗺️ View the Site")
st.caption("Step 2 · Zoom out from one unit to the whole inspection site")
render_walkthrough_banner(
    2,
    "🗺️ Here's your whole inspection site at a glance.",
    "Every zone is color-coded by the worst problem found there — 🟢 all clear, 🟡 worth watching, 🔴 needs attention now. Zone C is in the red.",
)

if not records:
    st.warning("Drone inspection records were not found. Add data/raw/drone/inspection_records.json to populate this page.")
else:
    zones = sorted(by_zone)
    summaries = [zone_summary(zone, by_zone[zone]) for zone in zones]
    map_summaries = site_zone_summaries(records)

    map_col, detail_col = st.columns([2.1, 1])

    with map_col:
        selected_zone = render_site_map_interactive(map_summaries)

        # Persist selection across reruns
        if selected_zone:
            st.session_state["map_selected_zone"] = selected_zone
        current_selection = st.session_state.get("map_selected_zone")

        if current_selection:
            sel = next((s for s in map_summaries if s["zone"] == current_selection), None)
            if sel:
                color, bg = SEVERITY_COLORS[sel["severity"]]
                st.markdown(
                    dedent(f"""
                    <div style="background:{bg};border:2px solid {color};border-radius:8px;
                                padding:0.75rem 1rem;margin-top:0.5rem;">
                      <strong style="font-size:1rem;color:#1A1A2E;">{sel["zone"]}</strong>
                      <span style="float:right;color:{color};font-weight:800;">{sel["severity"]}</span><br>
                      <span style="color:#4B5563;font-size:0.85rem;">
                        {sel["site_id"]} · {sel["records"]} records ·
                        HIGH: {sel["counts"].get("HIGH", 0)}
                        MED: {sel["counts"].get("MEDIUM", 0)}
                        LOW: {sel["counts"].get("LOW", 0)}
                      </span>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
                st.markdown("")
                if st.button(f"Investigate {current_selection} →", type="primary", use_container_width=True):
                    st.session_state["walkthrough_zone"] = current_selection
                    st.session_state["walkthrough_zone_query"] = (
                        f"What anomalies were found in {current_selection} during the last inspection?"
                    )
                    st.session_state["walkthrough_arrived_from_zone"] = True
                    if hasattr(st, "switch_page"):
                        st.switch_page("pages/3_Inspect_a_Zone.py")
                    else:
                        st.success(f"{current_selection} selected. Continue to Inspect a Zone from the sidebar.")
        else:
            st.caption("Click any zone marker to select it and investigate.")

    with detail_col:
        st.subheader("Zone risk rollup")
        for summary in summaries:
            severity = summary["severity"]
            color, bg = SEVERITY_COLORS[severity]
            counts = summary["counts"]
            border = "3px solid #1A1A2E" if summary["zone"] == "Zone-C" else f"1.5px solid {color}"
            st.markdown(
                dedent(f"""
                <div style="background:{bg};border:{border};border-radius:8px;padding:0.7rem 0.85rem;
                            margin-bottom:0.65rem;">
                  <div style="display:flex;justify-content:space-between;gap:0.8rem;align-items:flex-start;">
                    <strong style="color:#1A1A2E;font-size:1rem;">{summary["zone"]}</strong>
                    <span style="color:{color};font-weight:800;font-size:0.82rem;">{severity}</span>
                  </div>
                  <p style="margin:0.35rem 0 0;color:#4B5563;font-size:0.83rem;line-height:1.35;">
                    {summary["records"]} records · {summary["site_id"]}<br>
                    HIGH: {counts.get("HIGH", 0)} · MEDIUM: {counts.get("MEDIUM", 0)} · LOW: {counts.get("LOW", 0)}
                  </p>
                </div>
                """),
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("Zone C is the walkthrough hotspot")

    zone_c_records = sorted(by_zone.get("Zone-C", []), key=lambda r: r["flight_date"], reverse=True)
    c1, c2, c3 = st.columns(3)
    zone_c_counts = Counter(r["severity"] for r in zone_c_records)
    c1.metric("Zone C records", len(zone_c_records))
    c2.metric("HIGH findings", zone_c_counts.get("HIGH", 0))
    c3.metric("Sites represented", len({r["site_id"] for r in zone_c_records}))

    if zone_c_records:
        latest = zone_c_records[0]
        severity = latest["severity"]
        color, bg = SEVERITY_COLORS[severity]
        st.markdown(
            dedent(f"""
            <div style="background:{bg};border:1.5px solid {color};border-radius:8px;padding:1rem;margin-top:0.6rem;">
              <p style="margin:0 0 0.35rem 0;color:#6B7280;font-size:0.75rem;font-weight:800;
                        letter-spacing:0.08em;text-transform:uppercase;">Latest Zone C finding</p>
              <h4 style="margin:0;color:#1A1A2E;">{latest["record_id"]} · {latest["flight_date"]} · {latest["equipment_type"]}</h4>
              <p style="margin:0.4rem 0;color:{color};font-weight:800;">{latest["anomaly_type"]} · {severity}</p>
              <p style="margin:0;color:#4B5563;font-size:0.9rem;line-height:1.45;">
                {latest["inspector_notes"][:520]}...
              </p>
            </div>
            """),
            unsafe_allow_html=True,
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
