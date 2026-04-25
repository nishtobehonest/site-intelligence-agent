"""
pages/3_Inspect_a_Zone.py
-------------------------
Drone Site Intelligence Agent — multi-agent pipeline with session memory.
"""

import streamlit as st
from src.assistant import SiteIntelligenceAgent
from src.session_memory import SessionMemory
from src.ui.shared import (
    confidence_badge_html,
    render_escalation_warning,
    render_next_step,
    render_source_expander,
    render_walkthrough_banner,
    render_walkthrough_progress,
    render_why_it_matters,
)

st.set_page_config(page_title="Inspect a Zone", page_icon="🚁", layout="wide")

PRESETS = [
    {
        "label": "ANOMALY — Zone-C",
        "query": "What anomalies were found in Zone-C during the last inspection?",
    },
    {
        "label": "COMPLIANCE — Lockout/Tagout",
        "query": "What are the OSHA lockout tagout requirements for drone maintenance?",
    },
    {
        "label": "HISTORICAL — Zone-B drainage",
        "query": "Has Zone-B had recurring drainage issues over the past 3 months?",
    },
    {
        "label": "FOLLOW-UP — session memory",
        "query": "What about last month?",
    },
]


def _format_filter(where_filter: dict) -> str:
    """Convert the Chroma where filter into a readable demo label."""
    if not where_filter:
        return "No spatial filter; searched selected collections"

    zone_filter = where_filter.get("zone_id")
    if isinstance(zone_filter, dict) and "$eq" in zone_filter:
        return f"Restricted to {zone_filter['$eq']}"

    return "Spatial filter applied"


def _format_route(route_type: str) -> str:
    if route_type == "HIGH":
        return "HIGH confidence: answer with citations"
    if route_type == "PARTIAL":
        return "PARTIAL confidence: answer with uncertainty warning"
    return "LOW confidence: escalate instead of guessing"


def render_pipeline_trace(trace: dict, route_type: str, top_score: float) -> None:
    """Render the drone pipeline as a readable decision path for demos."""
    classification = trace.get("classification", {})
    query_type = classification.get("query_type", "Unknown")
    classifier_conf = classification.get("confidence", 0.0)
    via_llm = classification.get("via_llm", False)
    route = trace.get("route")

    st.markdown("### Pipeline decision path")

    if route == "OUT_OF_SCOPE_SHORT_CIRCUIT":
        st.info("1. Classified as out of scope, so retrieval and LLM generation were skipped.")
        st.warning("2. Routed to LOW confidence escalation.")
        return

    if route == "UNKNOWN_ZONE_LOW":
        zone = classification.get("zone") or "Unknown zone"
        st.info(f"1. Classified as `{query_type}` and detected `{zone}`.")
        st.warning("2. Zone is not in the site corpus, so retrieval and LLM generation were skipped.")
        return

    st.markdown(
        f"**1. Classify**  \n"
        f"`{query_type}` at {classifier_conf:.0%} confidence "
        f"using {'LLM classifier' if via_llm else 'rule-based fast path'}."
    )
    st.markdown(f"**2. Filter**  \n{_format_filter(trace.get('filter', {}))}.")

    filtered_count = trace.get("result_count_filtered", 0)
    fallback = trace.get("fallback")
    fallback_count = trace.get("result_count_fallback")
    if fallback:
        st.markdown(
            f"**3. Retrieve**  \n"
            f"Filtered search found {filtered_count} results, then fallback searched the full corpus "
            f"and found {fallback_count} results."
        )
    else:
        st.markdown(f"**3. Retrieve**  \nFound {filtered_count} relevant records.")

    conflict = trace.get("conflict", False)
    conflict_text = "conflict detected" if conflict else "no source conflict detected"
    st.markdown(
        f"**4. Score**  \n"
        f"Top similarity score `{top_score:.2f}`; routed as `{trace.get('confidence', route_type)}`; "
        f"{conflict_text}."
    )

    llm_text = "LLM called to generate a cited answer" if route_type in ("HIGH", "PARTIAL") else "LLM skipped to avoid hallucination"
    st.markdown(f"**5. Decide**  \n{_format_route(route_type)}. {llm_text}.")


@st.cache_resource(show_spinner="Loading drone inspection knowledge base...")
def load_agent():
    return SiteIntelligenceAgent()


if "drone_memory" not in st.session_state:
    st.session_state["drone_memory"] = SessionMemory()

if st.session_state.get("walkthrough_arrived_from_zone") and st.session_state.get("walkthrough_zone_query"):
    st.session_state["drone_query"] = st.session_state["walkthrough_zone_query"]
    st.session_state["drone_input"] = st.session_state["walkthrough_zone_query"]
elif st.session_state.get("walkthrough_zone_query") and "drone_query" not in st.session_state:
    st.session_state["drone_query"] = st.session_state["walkthrough_zone_query"]

memory: SessionMemory = st.session_state["drone_memory"]

render_walkthrough_progress(3)

st.title("🚁 Inspect a Zone")
st.caption("Step 3 · Classifier agent + spatial filters + session memory")
render_walkthrough_banner(
    3,
    "You're headed to Zone C.",
    "The system searches inspection records, baselines, and compliance docs, then decides if it is confident enough to answer.",
)

if st.session_state.get("walkthrough_arrived_from_zone"):
    st.success("The map already knew where you were headed. Your query was pre-loaded from the zone you selected.")
    st.session_state["walkthrough_arrived_from_zone"] = False

with st.sidebar:
    st.markdown("### Session memory")
    ctx = memory.get_context()
    st.markdown(f"**Turn:** {ctx['turn_count']}")
    st.markdown(f"**Zone:** {ctx['last_zone'] or '—'}")
    st.markdown(f"**Equipment:** {ctx['last_equipment'] or '—'}")
    st.markdown(f"**Time ref:** {ctx['last_time_ref'] or '—'}")
    st.markdown(f"**Last query type:** {ctx['last_query_type'] or '—'}")
    if st.button("Reset session", use_container_width=True):
        memory.reset()
        st.rerun()
    st.markdown("---")
    render_why_it_matters("drone")

st.markdown("**Quick demos:**")
if "drone_input" not in st.session_state:
    st.session_state["drone_input"] = st.session_state.get("drone_query", "")

preset_query = None
btn_cols = st.columns(4)
for i, preset in enumerate(PRESETS):
    if btn_cols[i].button(preset["label"], use_container_width=True):
        preset_query = preset["query"]
        st.session_state["drone_query"] = preset_query
        st.session_state["drone_input"] = preset_query

st.markdown("")

col_in, col_mid, col_out = st.columns([2, 2, 3])

with col_in:
    query = st.text_area(
        "Inspector question",
        height=120,
        placeholder="Ask about inspection anomalies, OSHA compliance, or historical baselines...",
        key="drone_input",
    )
    submit = st.button("Ask", type="primary", use_container_width=True)

active_query = preset_query or (query if submit else "")

if active_query.strip():
    agent = load_agent()

    with st.spinner("Classifying and retrieving..."):
        result = agent.ask(active_query, session_memory=memory)

    trace = result.get("pipeline_trace", {})
    classification = trace.get("classification", {})

    with col_mid:
        st.markdown("### Classification")
        q_type = classification.get("query_type", "—")
        conf = classification.get("confidence", 0.0)
        zone = classification.get("zone") or "—"
        equipment = classification.get("equipment") or "—"
        time_ref = classification.get("time_ref") or "—"
        via_llm = classification.get("via_llm", False)

        st.metric("Query type", q_type)
        st.metric("Classifier confidence", f"{conf:.0%}")
        st.metric("Zone", zone)
        st.metric("Equipment", equipment)
        st.metric("Time reference", time_ref)
        st.caption("LLM path" if via_llm else "Rule-based (fast path)")

        render_pipeline_trace(trace, result["route_type"], result["top_score"])

    with col_out:
        st.markdown("### Answer")
        st.markdown(
            confidence_badge_html(result["confidence_level"], result["top_score"]),
            unsafe_allow_html=True,
        )
        st.markdown("")

        response_text = result["response"]
        if "\n\nSources:\n" in response_text:
            answer_text, _ = response_text.split("\n\nSources:\n", 1)
        else:
            answer_text = response_text
        st.markdown(answer_text)

        render_source_expander(result["sources"], result["route_type"])
        render_escalation_warning(result["route_type"])

else:
    with col_mid:
        st.markdown("### Classification")
        st.markdown("*Classification panel will populate after a query.*")
    with col_out:
        st.markdown("### Answer")
        st.markdown("*Results will appear here after you submit a query.*")

render_next_step(
    "pages/4_See_the_Proof.py",
    "Next: See the Proof →",
    "How do we know this system actually works?",
)
