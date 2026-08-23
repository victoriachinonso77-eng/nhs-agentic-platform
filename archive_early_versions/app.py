"""
NHS Agentic AI Platform — Streamlit Interface
LD7326 | MSc Artificial Intelligence Technology | W25041744
Run: streamlit run app.py
"""

import streamlit as st
import os
import json
import time
import random
import datetime
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="NHS Agentic AI Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0a1628; color: #e8edf5; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0d1f3c;
        border-right: 1px solid #1f4e79;
    }

    /* Headers */
    h1, h2, h3 { color: #4fc3f7 !important; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #0d1f3c;
        border: 1px solid #1f4e79;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="metric-container"] label { color: #90caf9 !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #4fc3f7 !important;
        font-size: 1.8rem !important;
    }

    /* Agent cards */
    .agent-card {
        background: #0d1f3c;
        border: 1px solid #1f4e79;
        border-left: 4px solid #4fc3f7;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    .agent-card.critical { border-left-color: #ef5350; }
    .agent-card.warning  { border-left-color: #ffa726; }
    .agent-card.success  { border-left-color: #66bb6a; }

    /* Buttons */
    .stButton > button {
        background: #1f4e79;
        color: white;
        border: 1px solid #4fc3f7;
        border-radius: 6px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        width: 100%;
    }
    .stButton > button:hover {
        background: #4fc3f7;
        color: #0a1628;
    }

    /* Warning banner */
    .clinician-banner {
        background: #7f1d1d;
        border: 1px solid #ef5350;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 12px 0;
        font-weight: 600;
        color: #ffcdd2;
        text-align: center;
    }

    /* Status badges */
    .badge-feasible {
        background: #1b5e20;
        color: #a5d6a7;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-critical {
        background: #7f1d1d;
        color: #ffcdd2;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Hide streamlit branding */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 NHS AI Platform")
    st.markdown("**MSc AI Technology | LD7326**")
    st.markdown("W25041744 | Northumbria University")
    st.divider()

    st.markdown("### ⚙️ Configuration")
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "sk-proj-your-key-here":
        st.success("✅ API Key loaded")
    else:
        st.error("❌ API Key not found")
        st.caption("Add OPENAI_API_KEY to your .env file")

    st.divider()
    st.markdown("### 🏥 Ward Configuration")
    total_beds     = st.slider("Total beds", 80, 200, 120)
    occupied_beds  = st.slider("Occupied beds", 60, total_beds, 108)
    overdue_docs   = st.slider("Overdue documentation", 0, 50, 23)
    pending_ho     = st.slider("Pending handovers", 0, 30, 14)
    ed_wait        = st.slider("ED wait time (hours)", 0.0, 20.0, 4.2)

    st.divider()
    st.markdown("### 🔬 Prediction Inputs")
    st.caption("XGBoost bottleneck probabilities")
    ward_a = st.slider("Ward A", 0.0, 1.0, 0.87)
    ward_b = st.slider("Ward B", 0.0, 1.0, 0.43)
    ward_c = st.slider("Ward C", 0.0, 1.0, 0.91)
    ward_d = st.slider("Ward D", 0.0, 1.0, 0.21)
    icu    = st.slider("ICU",    0.0, 1.0, 0.72)


# ── Main content ──────────────────────────────────────────────────────
st.markdown("# 🏥 NHS Agentic AI Platform")
st.markdown("**AI-powered operational bottleneck prediction and autonomous decision support**")
st.markdown('<div class="clinician-banner">⚠️ All recommendations require CLINICIAN REVIEW before any action is taken</div>',
            unsafe_allow_html=True)

# ── Ward status metrics ───────────────────────────────────────────────
occupancy = occupied_beds / total_beds
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Occupancy Rate", f"{occupancy:.0%}", f"{occupied_beds}/{total_beds} beds")
col2.metric("ED Wait Time", f"{ed_wait:.1f}h", "Current")
col3.metric("Overdue Docs", str(overdue_docs), "notes")
col4.metric("Pending Handovers", str(pending_ho), "patients")
critical_wards = sum(1 for p in [ward_a, ward_b, ward_c, ward_d, icu] if p > 0.7)
col5.metric("Critical Wards", str(critical_wards), "bottleneck risk >70%")

st.divider()

# ── Bottleneck predictions visual ─────────────────────────────────────
st.markdown("### 📊 XGBoost Bottleneck Predictions")
cols = st.columns(5)
wards = [("Ward A", ward_a), ("Ward B", ward_b), ("Ward C", ward_c),
         ("Ward D", ward_d), ("ICU", icu)]
for col, (name, prob) in zip(cols, wards):
    with col:
        color = "#ef5350" if prob > 0.7 else "#ffa726" if prob > 0.4 else "#66bb6a"
        label = "🔴 CRITICAL" if prob > 0.7 else "🟡 MODERATE" if prob > 0.4 else "🟢 LOW"
        st.markdown(f"""
        <div style="background:#0d1f3c;border:1px solid #1f4e79;border-top:4px solid {color};
        border-radius:8px;padding:12px;text-align:center;">
            <div style="font-size:1.8rem;font-weight:700;color:{color};">{prob:.0%}</div>
            <div style="color:#90caf9;font-size:0.9rem;">{name}</div>
            <div style="font-size:0.75rem;color:{color};">{label}</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Run simulation button ─────────────────────────────────────────────
st.markdown("### 🤖 Seven-Agent Simulation")

if st.button("▶  Run AI-Powered Platform Simulation", type="primary"):

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-proj-your-key-here":
        st.error("❌ Please add your OPENAI_API_KEY to the .env file first.")
        st.stop()

    # Build inputs
    inputs = {
        "ward_state": {
            "timestamp":             datetime.datetime.now().isoformat(),
            "total_beds":            total_beds,
            "occupied_beds":         occupied_beds,
            "occupancy_rate":        occupancy,
            "pending_handovers":     pending_ho,
            "overdue_documentation": overdue_docs,
            "staff_on_shift":        {"doctors": 8, "nurses": 22, "admin": 5},
            "pending_transfers":     7,
            "icu_available_beds":    3,
            "current_ed_wait_hours": ed_wait
        },
        "bottleneck_predictions": {
            "ward_A": {"bottleneck_probability": ward_a, "admission_type": "EW EMER."},
            "ward_B": {"bottleneck_probability": ward_b, "admission_type": "URGENT"},
            "ward_C": {"bottleneck_probability": ward_c, "admission_type": "EW EMER."},
            "ward_D": {"bottleneck_probability": ward_d, "admission_type": "ELECTIVE"},
            "ICU":    {"bottleneck_probability": icu,    "admission_type": "DIRECT EMER."},
        },
        "demand_forecast": {f"day_{i+1}": round(15 + i * 0.4, 1) for i in range(7)}
    }

    # Import and run agents
    from src.platform.ai_agents import NHSAIPlatformOrchestrator

    agent_names = [
        "Documentation Agent", "Handover Agent", "Workflow Agent",
        "Cognitive Support Agent", "Integration Agent",
        "Coordination Agent", "Security Agent"
    ]
    agent_icons = ["📝", "🤝", "⚡", "🧠", "🔗", "📞", "🔒"]

    progress = st.progress(0, text="Initialising agents...")
    status   = st.empty()

    results_container = st.container()

    with st.spinner("Running all 7 agents..."):
        orchestrator = NHSAIPlatformOrchestrator()
        orchestrator.agents["documentation"].logger = orchestrator.logger

        all_results = {}
        agent_keys  = list(orchestrator.agents.keys())

        for idx, (key, agent) in enumerate(orchestrator.agents.items()):
            progress.progress((idx + 1) / 7,
                              text=f"Running {agent_names[idx]}...")
            all_results[key] = agent.act(inputs)
            time.sleep(0.3)

        progress.progress(1.0, text="All agents complete ✅")

    # ── Display agent results ─────────────────────────────────────────
    st.markdown("### 📋 Agent Recommendations")
    st.markdown('<div class="clinician-banner">⚠️ CLINICIAN REVIEW REQUIRED before acting on any recommendation below</div>',
                unsafe_allow_html=True)

    for idx, (key, result) in enumerate(all_results.items()):
        rec = result.get("recommendation", "No recommendation generated.")
        card_class = "critical" if any(w in rec.upper() for w in ["CRITICAL", "HIGH RISK", "URGENT"]) else \
                     "warning"  if any(w in rec.upper() for w in ["FLAG", "REVIEW", "MONITOR"]) else "success"

        with st.expander(f"{agent_icons[idx]} {agent_names[idx]}", expanded=True):
            st.markdown(f'<div class="agent-card {card_class}">{rec}</div>',
                        unsafe_allow_html=True)

            # Show key metrics per agent
            metric_cols = st.columns(3)
            if key == "documentation":
                metric_cols[0].metric("Auto-generated", result.get("auto_generated_estimate", "-"))
                metric_cols[1].metric("For review", result.get("manual_review_estimate", "-"))
                metric_cols[2].metric("Time saved (mins)", result.get("estimated_time_saved_mins", "-"))
            elif key == "handover":
                metric_cols[0].metric("Pending handovers", result.get("pending_handovers", "-"))
                metric_cols[1].metric("High-risk wards", len(result.get("high_risk_wards", [])))
                metric_cols[2].metric("SBAR compliance", f"{result.get('sbar_compliance_rate', 0)}%")
            elif key == "cognitive":
                metric_cols[0].metric("NASA-TLX score", f"{result.get('nasa_tlx_estimated', 0)}/100")
                metric_cols[1].metric("Load level", result.get("cognitive_load_level", "-"))
                metric_cols[2].metric("Scaffolds activated", result.get("scaffolds_activated", "-"))
            elif key == "coordination":
                metric_cols[0].metric("Total queries", result.get("total_queries", "-"))
                metric_cols[1].metric("Auto-resolved", result.get("auto_resolved", "-"))
                metric_cols[2].metric("Time saved (mins)", result.get("estimated_time_saved_mins", "-"))
            elif key == "security":
                metric_cols[0].metric("Events monitored", result.get("access_events_monitored", "-"))
                metric_cols[1].metric("Anomalies", result.get("anomalies_detected", "-"))
                metric_cols[2].metric("Threat level", result.get("threat_level", "-"))

    # ── Summary metrics ───────────────────────────────────────────────
    st.divider()
    st.markdown("### 📈 Simulation Summary")

    time_saved = (
        all_results["documentation"].get("estimated_time_saved_mins", 0) +
        all_results["coordination"].get("estimated_time_saved_mins", 0) +
        all_results["integration"].get("time_saved_mins", 0)
    )

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Time Saved", f"{time_saved:.0f} mins", "per cycle")
    s2.metric("SBAR Compliance", f"{all_results['handover'].get('sbar_compliance_rate', 0)}%")
    s3.metric("Cognitive Load", f"{all_results['cognitive'].get('nasa_tlx_estimated', 0)}/100",
              all_results['cognitive'].get('cognitive_load_level', ''))
    s4.metric("Security Status", all_results['security'].get('threat_level', '-'))

    # Save outputs
    Path("outputs/logs").mkdir(parents=True, exist_ok=True)
    Path("outputs/results").mkdir(parents=True, exist_ok=True)
    orchestrator.logger.save("outputs/logs")

    summary = {
        "session_id":            orchestrator.session_id,
        "timestamp":             datetime.datetime.now().isoformat(),
        "total_time_saved_mins": round(time_saved, 1),
        "sbar_compliance":       all_results['handover'].get('sbar_compliance_rate', 0),
        "nasa_tlx":              all_results['cognitive'].get('nasa_tlx_estimated', 0),
        "security_threat":       all_results['security'].get('threat_level', '-'),
        "clinician_review_required": True,
        "agent_recommendations": {k: v.get("recommendation", "") for k, v in all_results.items()}
    }
    with open("outputs/results/ai_platform_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    st.success("✅ Simulation complete — outputs saved to outputs/ folder")

st.divider()

# ── Feasibility Evaluation Section ────────────────────────────────────
st.markdown("### 📊 Feasibility Evaluation Results")
st.caption("100 paired simulation scenarios — pre-registered statistical tests")

results_data = [
    ("Task Completion Time", 46.0, 29.2, "-36.7%", 1.830),
    ("Documentation Errors", 3.24, 1.61, "-50.3%", 0.835),
    ("SBAR Compliance Rate", 60.4, 78.6, "+30.0%", 1.994),
    ("ED Wait Time (hours)", 10.78, 8.40, "-22.1%", 0.841),
    ("Cognitive Load NASA-TLX", 71.8, 53.6, "-25.4%", 1.829),
    ("Query Resolution Time", 38.6, 17.6, "-54.4%", 3.846),
    ("Security Incidents", 1.82, 1.13, "-37.9%", 0.509),
]

cols = st.columns([3, 1.5, 1.5, 1.5, 1.5, 2])
cols[0].markdown("**Outcome Measure**")
cols[1].markdown("**Baseline**")
cols[2].markdown("**AI-Assisted**")
cols[3].markdown("**Improvement**")
cols[4].markdown("**Cohen's d**")
cols[5].markdown("**Verdict**")

for name, base, ai_val, improv, d in results_data:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5, 2])
    cols[0].write(name)
    cols[1].write(f"{base}")
    cols[2].write(f"{ai_val}")
    cols[3].write(improv)
    cols[4].write(f"{d:.3f}")
    cols[5].markdown('<span class="badge-feasible">✅ FEASIBLE</span>', unsafe_allow_html=True)

st.divider()
st.caption("NHS Agentic AI Platform | LD7326 | MSc Artificial Intelligence Technology | W25041744 | Northumbria University")