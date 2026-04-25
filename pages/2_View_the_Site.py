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

import streamlit as st
import streamlit.components.v1 as components
from src.ui.shared import render_next_step, render_walkthrough_banner, render_walkthrough_progress

st.set_page_config(page_title="View the Site", page_icon="🗺️", layout="wide")

DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "drone" / "inspection_records.json"
SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
SEVERITY_COLORS = {
    "HIGH": ("#b91c1c", "#fef2f2"),
    "MEDIUM": ("#b45309", "#fffbeb"),
    "LOW": ("#15803d", "#f0fdf4"),
}
MAP_COLORS = {
    "HIGH": ("#dc2626", "#fef2f2"),
    "MEDIUM": ("#d97706", "#fffbeb"),
    "LOW": ("#16a34a", "#f0fdf4"),
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


def marker_position(summary: dict, site_layout: dict[str, dict]) -> tuple[float, float]:
    """
    Position zones by site first, then fan out each site's zones.

    The synthetic records use real city coordinates, so Austin and Denver are
    hundreds of miles apart while zones within one site differ by only a few
    decimal places. A direct lat/lon projection collapses each site's zones
    into a single stack. This keeps the coordinate-derived site ordering while
    giving every zone a stable, visible slot inside its site cluster.
    """
    layout = site_layout[summary["site_id"]]
    zone_count = max(layout["zone_count"], 1)
    zone_index = layout["zone_order"].get(summary["zone"], 0)
    spread = min(46, 18 * max(zone_count - 1, 0))
    zone_offset = 0 if zone_count == 1 else -spread / 2 + (spread * zone_index / (zone_count - 1))
    return layout["x"], layout["y"] + zone_offset


def build_site_layout(summaries: list[dict]) -> dict[str, dict]:
    sites: dict[str, dict] = {}
    for summary in summaries:
        site = sites.setdefault(summary["site_id"], {"lats": [], "lons": [], "zones": set()})
        site["lats"].append(summary["lat"])
        site["lons"].append(summary["lon"])
        site["zones"].add(summary["zone"])

    site_points = []
    for site_id, site in sites.items():
        site_points.append(
            {
                "site_id": site_id,
                "lat": sum(site["lats"]) / len(site["lats"]),
                "lon": sum(site["lons"]) / len(site["lons"]),
                "zones": sorted(site["zones"]),
            }
        )

    lat_values = [site["lat"] for site in site_points]
    lon_values = [site["lon"] for site in site_points]
    lat_min, lat_max = min(lat_values), max(lat_values)
    lon_min, lon_max = min(lon_values), max(lon_values)
    lat_span = max(lat_max - lat_min, 0.0001)
    lon_span = max(lon_max - lon_min, 0.0001)

    layout = {}
    for site in site_points:
        x = 22 + ((site["lon"] - lon_min) / lon_span) * 56
        y = 72 - ((site["lat"] - lat_min) / lat_span) * 44
        layout[site["site_id"]] = {
            "x": x,
            "y": y,
            "zone_count": len(site["zones"]),
            "zone_order": {zone: index for index, zone in enumerate(site["zones"])},
        }
    return layout


def render_site_map(summaries: list[dict]) -> None:
    site_layout = build_site_layout(summaries)
    markers = []
    for summary in summaries:
        color, bg = MAP_COLORS[summary["severity"]]
        x, y = marker_position(summary, site_layout)
        selected = summary["zone"] == "Zone-C"
        border = "3px solid #1A1A2E" if selected else "2px solid white"
        shadow = "0 0 0 5px rgba(26,26,46,0.14)" if selected else "0 10px 24px rgba(15,23,42,0.14)"
        markers.append(
            dedent(f"""
            <div class="site-marker" style="--x:{x:.2f}%;--y:{y:.2f}%;
                        background:{bg};border:{border};box-shadow:{shadow};">
              <div style="display:flex;align-items:center;gap:0.45rem;">
                <span style="width:0.72rem;height:0.72rem;border-radius:999px;background:{color};
                             display:inline-block;"></span>
                <strong>{summary["zone"]}</strong>
              </div>
              <div style="font-size:0.78rem;color:#4B5563;margin-top:0.15rem;">
                {summary["site_id"]}<br>{summary["severity"]} · {summary["records"]} records
              </div>
            </div>
            """)
        )

    components.html(
        dedent(f"""
        <style>
        body {{
          margin: 0;
          font-family: "Source Sans Pro", sans-serif;
        }}
        .site-map {{
          position: relative;
          min-height: 520px;
          border: 1px solid #CBD5E1;
          border-radius: 12px;
          overflow: hidden;
          background:
            linear-gradient(90deg, rgba(148,163,184,0.26) 1px, transparent 1px),
            linear-gradient(rgba(148,163,184,0.26) 1px, transparent 1px),
            radial-gradient(circle at 18% 22%, rgba(20,184,166,0.22), transparent 18%),
            radial-gradient(circle at 78% 74%, rgba(14,165,233,0.18), transparent 22%),
            #F8FAFC;
          background-size: 48px 48px, 48px 48px, auto, auto, auto;
        }}
        .site-map::before {{
          content: "";
          position: absolute;
          inset: 54px 72px;
          border: 2px dashed rgba(71,85,105,0.24);
          border-radius: 38px;
          transform: rotate(-8deg);
        }}
        .site-map::after {{
          content: "Inspection site coordinate view";
          position: absolute;
          left: 1rem;
          bottom: 0.85rem;
          color: #64748B;
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }}
        .site-marker {{
          position: absolute;
          left: clamp(0.75rem, calc(var(--x) - 5.5rem), calc(100% - 11.75rem));
          top: clamp(0.75rem, calc(var(--y) - 2.4rem), calc(100% - 5.9rem));
          width: 11rem;
          box-sizing: border-box;
          border-radius: 8px;
          padding: 0.7rem 0.8rem;
          color: #1A1A2E;
          z-index: 1;
        }}
        .map-legend {{
          display: flex;
          flex-wrap: wrap;
          gap: 0.7rem;
          margin-top: 0.65rem;
          color: #4B5563;
          font-size: 0.86rem;
        }}
        </style>
        <div class="site-map">
          {''.join(markers)}
        </div>
        <div class="map-legend">
          <span><strong>Map basis:</strong> site-zone coordinates from inspection records</span>
          <span>Red = HIGH</span>
          <span>Amber = MEDIUM</span>
          <span>Green = LOW</span>
        </div>
        """),
        height=590,
    )


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
    summaries = [zone_summary(zone, by_zone[zone]) for zone in zones]
    map_summaries = site_zone_summaries(records)

    map_col, detail_col = st.columns([2.1, 1])
    with map_col:
        render_site_map(map_summaries)

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
