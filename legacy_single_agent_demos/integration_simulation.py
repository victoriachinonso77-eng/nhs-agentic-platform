"""
NHS AI Platform — Integration Agent Live Simulation
Shows 5 systems queried simultaneously, conflicts found, time saved
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run integration_simulation.py
"""

import streamlit as st
import time
import datetime
import random
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Integration Agent",
    page_icon="🔗",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }
#MainMenu, footer { visibility: hidden; }

.system-card { background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 14px 16px; margin-bottom: 8px; transition: all 0.3s ease; }
.system-card.querying { border-color: #F59E0B; animation: pulse 0.8s infinite; }
.system-card.complete { border-color: #22C55E; }
.system-card.conflict { border-color: #EF4444; }
.system-card.idle     { border-color: #30363D; }

.conflict-card { background: #2D0A0A; border: 1.5px solid #EF4444; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; animation: fadeIn 0.5s ease; }
.conflict-title { font-size: 0.85rem; font-weight: 700; color: #FCA5A5; margin-bottom: 6px; }
.conflict-detail { font-size: 0.78rem; color: #FCA5A5; line-height: 1.5; }

.manual-step { background: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 10px 14px; margin-bottom: 6px; }
.manual-active { border-color: #F59E0B; background: #1A1200; }
.manual-done   { border-color: #22C55E; background: #0A2D1A; opacity: 0.7; }

.vs-card { background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 16px; text-align: center; }

.field-tag { display: inline-block; background: #21262D; border: 1px solid #30363D; border-radius: 4px; padding: 2px 8px; font-size: 0.7rem; color: #8B949E; margin: 2px; }
.field-tag.conflict { background: #2D0A0A; border-color: #EF4444; color: #FCA5A5; }
.field-tag.ok       { background: #0A2D1A; border-color: #22C55E; color: #86EFAC; }

.guide-step { display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; border-bottom: 1px solid #21262D; }
.guide-num  { background: #1F6FEB; color: #FFF; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 800; flex-shrink: 0; }

[data-testid="metric-container"] { background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 12px !important; }
[data-testid="metric-container"] label { color: #8B949E !important; font-size: 0.7rem !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.4rem !important; font-weight: 700 !important; }

.stButton > button { background: #1F6FEB !important; color: #FFF !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; width: 100% !important; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes pulse  { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
</style>
""", unsafe_allow_html=True)

# ── System definitions ────────────────────────────────────────────────
SYSTEMS = [
    {
        "name": "Electronic Patient Record (EPR)", "abbrev": "EPR", "icon": "🏥",
        "purpose": "Patient demographics, clinical history, medications",
        "manual_mins": 4,
        "data": {
            "Occupied beds": "108", "Patient name": "James Okafor",
            "Medications": "Metformin, Amlodipine, Aspirin", "Allergies": "NKDA",
            "Last obs": "14:32 — BP 142/88", "Consultant": "Dr. Mensah (Cardiology)",
        },
        "conflict_field": "Occupied beds", "conflict_value": "108",
    },
    {
        "name": "NHS Spine", "abbrev": "SPINE", "icon": "🔗",
        "purpose": "National patient demographics, GP details, transfers",
        "manual_mins": 5,
        "data": {
            "NHS Number": "NHS-485-261-3847", "GP Practice": "Whitechapel Health Centre",
            "Pending transfers": "6", "Summary Care Record": "Available", "Registered address": "Verified",
        },
        "conflict_field": "Pending transfers", "conflict_value": "6",
    },
    {
        "name": "Pharmacy System", "abbrev": "PHARM", "icon": "💊",
        "purpose": "Medication dispensing, drug interactions, stock",
        "manual_mins": 3,
        "data": {
            "Metformin 500mg": "Dispensed 09:00", "Amlodipine 5mg": "Dispensed 09:00",
            "Aspirin 75mg": "Dispensed 09:00", "Drug interactions": "None detected", "TTO status": "Pending",
        },
        "conflict_field": None, "conflict_value": None,
    },
    {
        "name": "Radiology Information System (RIS)", "abbrev": "RIS", "icon": "🩻",
        "purpose": "Imaging requests, results, reporting status",
        "manual_mins": 4,
        "data": {
            "CXR (14:10)": "Reported — mild pulmonary oedema",
            "ECG (13:45)": "ST changes II, III, aVF",
            "Echo": "Requested — booked 09:00 tomorrow", "CT pending": "None",
        },
        "conflict_field": None, "conflict_value": None,
    },
    {
        "name": "Laboratory Information System (LIS)", "abbrev": "LIS", "icon": "🧪",
        "purpose": "Blood results, cultures, pathology reports",
        "manual_mins": 4,
        "data": {
            "Troponin (13:30)": "2.4 ng/mL — ELEVATED",
            "Troponin (16:30)": "1.8 ng/mL — trending down",
            "WBC": "11.2 (mildly elevated)", "eGFR": "62 — normal",
            "INR": "1.1 — therapeutic", "ICU beds available": "3",
        },
        "conflict_field": "ICU beds available", "conflict_value": "3",
    },
]

CONFLICTS = [
    {
        "field": "Occupied beds", "system1": "EPR", "value1": "108 beds occupied",
        "system2": "NHS Spine", "value2": "110 beds occupied", "severity": "HIGH",
        "impact": "Bed count discrepancy may affect capacity planning and transfer decisions.",
        "action": "Verify actual bed count with ward manager before accepting new transfers.",
    },
    {
        "field": "Pending transfers", "system1": "NHS Spine", "value1": "6 pending transfers",
        "system2": "Ward state", "value2": "7 pending transfers", "severity": "MEDIUM",
        "impact": "One transfer not reflected in national record — patient may be unaccounted for.",
        "action": "Identify unrecorded transfer and update NHS Spine within 30 minutes.",
    },
]

PATIENTS_INT = [
    {
        "name": "James Okafor", "nhs": "NHS-485-261-3847",
        "query": "Full cardiac workup — pre-cath lab review",
        "systems_needed": ["EPR", "SPINE", "PHARM", "RIS", "LIS"],
        "key_findings": "Troponin 1.8 ng/mL trending down · Echo booked 09:00 · No drug interactions · ST changes resolving",
        "conflict": "EPR: 108 beds occupied vs NHS Spine: 110 beds occupied",
    },
    {
        "name": "Robert Adeniran", "nhs": "NHS-334-817-9204",
        "query": "Pre-op check — INR reversal status",
        "systems_needed": ["EPR", "PHARM", "LIS"],
        "key_findings": "INR now 2.1 (target <1.5) · Vitamin K given · FFP 2 units administered · Repeat INR due 22:00",
        "conflict": "Pharmacy: Warfarin listed as active · EPR: Warfarin held perioperatively — reconciliation needed",
    },
    {
        "name": "Priya Krishnamurthy", "nhs": "NHS-591-042-7713",
        "query": "Step-down assessment — PEFR trend",
        "systems_needed": ["EPR", "RIS", "LIS"],
        "key_findings": "PEFR 62% (was 38%) · O2 sats 97% on 2L · ABG normalising · 4-hourly neb due in 45 mins",
        "conflict": None,
    },
    {
        "name": "Margaret Thornton", "nhs": "NHS-712-394-5521",
        "query": "Pre-theatre check — consent and anaesthetic review",
        "systems_needed": ["EPR", "PHARM", "LIS"],
        "key_findings": "Consent signed · Anaesthetic review complete · WBC 14.2 · NBM since 13:00 · Theatre 22:00",
        "conflict": None,
    },
]

# ── Session state ─────────────────────────────────────────────────────
if "int_state"          not in st.session_state: st.session_state.int_state = "idle"
if "int_events"         not in st.session_state: st.session_state.int_events = []
if "int_systems"        not in st.session_state:
    st.session_state.int_systems = {s["abbrev"]: "idle" for s in SYSTEMS}
if "int_start"          not in st.session_state: st.session_state.int_start = None
if "int_end"            not in st.session_state: st.session_state.int_end = None
if "manual_step"        not in st.session_state: st.session_state.manual_step = 0
if "manual_start"       not in st.session_state: st.session_state.manual_start = None
if "conflicts_resolved" not in st.session_state: st.session_state.conflicts_resolved = set()
if "morning_query_done" not in st.session_state: st.session_state.morning_query_done = False
if "active_patient"     not in st.session_state: st.session_state.active_patient = 0
if "queried_patients"   not in st.session_state: st.session_state.queried_patients = set()
if "ai_demo_state"      not in st.session_state: st.session_state.ai_demo_state = "ready"
if "ai_demo_start"      not in st.session_state: st.session_state.ai_demo_start = None

def add_int_event(text, etype="info", shift_time=None):
    st.session_state.int_events.append({
        "time": shift_time or datetime.datetime.now().strftime("%H:%M:%S"),
        "text": text, "type": etype
    })

# Auto-run morning query
if not st.session_state.morning_query_done:
    st.session_state.int_state = "complete"
    st.session_state.int_end = datetime.datetime.now()
    st.session_state.int_start = datetime.datetime.now()
    for s in SYSTEMS:
        st.session_state.int_systems[s["abbrev"]] = "conflict" if s["conflict_field"] else "complete"
    add_int_event("🔗 Integration Agent: Morning query — all 5 systems queried simultaneously", "ai", "07:15")
    add_int_event("✅ All 5 systems integrated in 2.3s — 47 fields retrieved", "success", "07:15")
    add_int_event("⚠️ Conflict: EPR shows 108 beds, NHS Spine shows 110 — flagged", "critical", "07:15")
    st.session_state.morning_query_done = True

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            🔗 Integration Agent — Live Simulation
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            5 NHS systems queried simultaneously · Data conflicts detected · Time saved vs manual
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">
        Royal London Hospital · Patient: James Okafor<br>
        LD7326 · W25041744 · Northumbria University
    </div>
</div>
""", unsafe_allow_html=True)

# ── GUIDE PANEL ───────────────────────────────────────────────────────
with st.expander("📖 What is the Integration Agent? — Click to read before starting", expanded=True):
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("""
        **What this agent does**

        NHS hospitals run on 5 separate computer systems that do not talk to each other.
        Every time a clinician needs a full patient picture they must log into each one separately.

        The Integration Agent connects all 5 simultaneously, retrieves a complete picture
        in **2.3 seconds**, and flags any conflicts where two systems give different answers.
        """)
    with g2:
        st.markdown("""
        **What you will see on this page**

        **Left column** — Manual vs AI comparison
        - Click ▶ Start Manual to watch 20 minutes animate step by step
        - Click 🔗 Run AI Integration to watch 2.3 seconds

        **Middle column** — The 5 systems and their data
        - Green = clean data retrieved
        - Red = conflict detected between systems

        **Bottom** — Multi-patient panel showing all 4 patients queried
        """)
    with g3:
        st.markdown("""
        **How to use it — step by step**

        **①** Click **▶ Start Manual Process** and watch how long it takes manually

        **②** Click **🔗 Run AI Integration** and compare

        **③** Scroll the middle column to see what data was retrieved from each system

        **④** Scroll down to **Data Conflicts** — see what the agent flagged

        **⑤** Click **✅ Resolve** on each conflict as a clinician would

        **⑥** Use the **Multi-Patient** panel to query all 4 patients
        """)

# ── Morning query banner ──────────────────────────────────────────────
st.markdown("""
<div style="background:#0D1F33;border:1.5px solid #38BDF8;border-radius:8px;
padding:10px 16px;margin-bottom:10px;">
    <div style="font-size:0.82rem;font-weight:700;color:#38BDF8;">
        🔗 07:15 — Integration Agent activated automatically at shift start
    </div>
    <div style="font-size:0.76rem;color:#93C5FD;margin-top:3px;">
        Morning ward query complete · All 5 systems queried · 2 conflicts detected and flagged ·
        Now available for individual patient queries throughout the shift
    </div>
</div>""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#1A1A0A;border:1px solid #F59E0B;border-radius:6px;
padding:8px 14px;margin-bottom:12px;font-size:0.73rem;color:#D4A520;">
    ⚖️ <b>Research Simulation:</b> All patient data and system responses are fictional.
    No real NHS systems accessed. GDPR · DCB0129/DCB0160 · W25041744
</div>
""", unsafe_allow_html=True)

# ── Metrics ───────────────────────────────────────────────────────────
total_manual = sum(s["manual_mins"] for s in SYSTEMS)
ai_time_secs = 2.3
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Systems to Integrate", "5")
m2.metric("Manual Time", f"{total_manual} mins", "Without AI")
m3.metric("AI Integration Time", f"{ai_time_secs}s", "With AI")
m4.metric("Time Saved", f"{round(total_manual - ai_time_secs/60, 1)} mins", "Per query")
m5.metric("Conflicts Detected", "2", "Require review")

st.divider()

# ── Main layout ───────────────────────────────────────────────────────
left_col, mid_col, right_col = st.columns([1, 2, 1])

# ── LEFT: Manual vs AI ────────────────────────────────────────────────
with left_col:
    st.markdown("### ⏱ Manual vs AI")
    st.caption("The same data retrieval — two very different experiences")

    sum1, sum2 = st.columns(2)
    with sum1:
        st.markdown("""
        <div style="background:#2D0A0A;border:2px solid #EF4444;border-radius:8px;
        padding:12px;text-align:center;margin-bottom:10px;">
            <div style="font-size:0.7rem;font-weight:700;color:#EF4444;text-transform:uppercase;">❌ Without AI</div>
            <div style="font-size:1.8rem;font-weight:900;color:#FCA5A5;">20 mins</div>
            <div style="font-size:0.7rem;color:#FCA5A5;">per patient query</div>
        </div>""", unsafe_allow_html=True)
    with sum2:
        st.markdown("""
        <div style="background:#0A2D1A;border:2px solid #22C55E;border-radius:8px;
        padding:12px;text-align:center;margin-bottom:10px;">
            <div style="font-size:0.7rem;font-weight:700;color:#22C55E;text-transform:uppercase;">✅ With AI</div>
            <div style="font-size:1.8rem;font-weight:900;color:#86EFAC;">2.3s</div>
            <div style="font-size:0.7rem;color:#86EFAC;">per patient query</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.75rem;font-weight:700;color:#EF4444;
    text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">
        ❌ Step 1: Without AI — Manual Process
    </div>
    <div style="font-size:0.75rem;color:#8B949E;margin-bottom:8px;">
        Click the button below and watch what a doctor has to do manually
        every time they need a patient workup.
    </div>""", unsafe_allow_html=True)

    step_sim_mins = [0, 4, 4, 9, 9, 12, 12, 16, 16, 20]
    manual_steps = [
        ("Log into EPR", 4, "🏥"),
        ("Search patient record — type name, wait for results", 0, ""),
        ("Log into NHS Spine — separate login required", 5, "🔗"),
        ("Verify patient demographics — cross-reference manually", 0, ""),
        ("Log into Pharmacy System — third login", 3, "💊"),
        ("Check medication record — scroll through dispensing history", 0, ""),
        ("Log into Radiology (RIS) — fourth login", 4, "🩻"),
        ("Find imaging results — search by date and type", 0, ""),
        ("Log into Laboratory (LIS) — fifth login", 4, "🧪"),
        ("Retrieve lab results — manually note each value", 0, ""),
    ]

    if st.session_state.manual_start is None:
        if st.button("▶ Start Manual Process — feel the pain"):
            st.session_state.manual_start = datetime.datetime.now()
            st.rerun()
    else:
        elapsed_manual = (datetime.datetime.now() - st.session_state.manual_start).total_seconds()
        current_step = min(int(elapsed_manual / 2.5), len(manual_steps) - 1)
        sim_mins_elapsed = step_sim_mins[current_step]

        st.markdown(
            f'<div style="background:#2D0A0A;border:1px solid #EF4444;border-radius:6px;'
            f'padding:8px 14px;margin-bottom:8px;text-align:center;">'
            f'<span style="font-size:1.1rem;font-weight:900;color:#FCA5A5;">⏱ {sim_mins_elapsed} minutes elapsed</span>'
            f'<span style="font-size:0.75rem;color:#8B949E;margin-left:8px;">of ~{total_manual} minutes total</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        for i, (step, mins, icon) in enumerate(manual_steps):
            if i < current_step:   css, indicator = "manual-done",   "✅"
            elif i == current_step: css, indicator = "manual-active", "⏳"
            else:                   css, indicator = "manual-step",   "○"
            mins_badge = f' <b style="color:#EF4444;">+{mins} mins</b>' if mins > 0 else ''
            st.markdown(
                f'<div class="manual-step {css}">'
                f'<span style="font-size:0.78rem;color:#C9D1D9;">{indicator} {icon} {step}{mins_badge}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        if current_step >= len(manual_steps) - 1:
            st.markdown(
                f'<div style="background:#2D0A0A;border:2px solid #EF4444;border-radius:6px;'
                f'padding:12px;text-align:center;">'
                f'<div style="font-size:1.2rem;font-weight:900;color:#FCA5A5;">⏱ ~{total_manual} MINUTES WASTED</div>'
                f'<div style="font-size:0.78rem;color:#FCA5A5;margin-top:4px;">'
                f'Per patient. Per query. Every time.<br>Now watch the AI do it in 2.3 seconds.</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            time.sleep(0.4)
            st.rerun()

    st.divider()

    st.markdown("""
    <div style="font-size:0.75rem;font-weight:700;color:#22C55E;
    text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
        ✅ Step 2: With AI — Integration Agent
    </div>
    <div style="font-size:0.75rem;color:#8B949E;margin-bottom:8px;">
        Now click below and watch the AI query all 5 systems simultaneously
        in 2.3 seconds — then compare.
    </div>""", unsafe_allow_html=True)

    ai_state = st.session_state.get("ai_demo_state", "ready")

    if ai_state == "ready":
        if st.button("🔗 Run AI Integration — watch 2.3 seconds"):
            st.session_state.ai_demo_state = "running"
            st.session_state.ai_demo_start = datetime.datetime.now()
            st.rerun()

    elif ai_state == "running":
        elapsed_ai = (datetime.datetime.now() - st.session_state.ai_demo_start).total_seconds()
        progress_pct = min(int(elapsed_ai / 2.3 * 100), 100)
        st.markdown(
            f'<div style="background:#0D1F33;border:2px solid #38BDF8;border-radius:8px;padding:16px;margin-bottom:8px;">'
            f'<div style="font-size:0.85rem;font-weight:800;color:#38BDF8;margin-bottom:10px;">🔗 Querying all 5 systems simultaneously...</div>'
            f'<div style="background:#21262D;border-radius:6px;height:10px;margin-bottom:10px;">'
            f'<div style="width:{progress_pct}%;height:10px;background:#38BDF8;border-radius:6px;"></div></div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">'
            f'<div style="font-size:0.75rem;color:#93C5FD;">🏥 EPR — querying...</div>'
            f'<div style="font-size:0.75rem;color:#93C5FD;">🔗 NHS Spine — querying...</div>'
            f'<div style="font-size:0.75rem;color:#93C5FD;">💊 Pharmacy — querying...</div>'
            f'<div style="font-size:0.75rem;color:#93C5FD;">🩻 RIS — querying...</div>'
            f'<div style="font-size:0.75rem;color:#93C5FD;">🧪 LIS — querying...</div></div>'
            f'<div style="font-size:0.78rem;color:#8B949E;margin-top:8px;text-align:center;">{elapsed_ai:.1f}s elapsed of 2.3s total</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        if elapsed_ai >= 2.3:
            st.session_state.ai_demo_state = "complete"
            st.rerun()
        else:
            time.sleep(0.3)
            st.rerun()

    elif ai_state == "complete":
        st.markdown(
            '<div style="background:#0A2D1A;border:2px solid #22C55E;border-radius:8px;padding:14px;margin-bottom:8px;">'
            '<div style="font-size:0.95rem;font-weight:800;color:#86EFAC;margin-bottom:8px;">✅ Complete in 2.3 seconds</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">'
            '<div style="font-size:0.75rem;color:#86EFAC;">🏥 EPR ✅</div>'
            '<div style="font-size:0.75rem;color:#86EFAC;">🔗 NHS Spine ✅</div>'
            '<div style="font-size:0.75rem;color:#86EFAC;">💊 Pharmacy ✅</div>'
            '<div style="font-size:0.75rem;color:#86EFAC;">🩻 RIS ✅</div>'
            '<div style="font-size:0.75rem;color:#86EFAC;">🧪 LIS ✅</div></div>'
            '<div style="background:#0D2D1A;border:1px solid #22C55E;border-radius:6px;padding:8px;font-size:0.78rem;color:#86EFAC;">47 fields retrieved · 2 conflicts flagged · 0 fields missing</div>'
            '<div style="background:#2D0A0A;border:1px solid #EF4444;border-radius:6px;padding:8px;font-size:0.78rem;color:#FCA5A5;margin-top:6px;">'
            '⚠️ Conflict 1: EPR 108 beds vs NHS Spine 110 beds<br>'
            '⚠️ Conflict 2: Warfarin active in Pharmacy, held in EPR</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="background:#0D1F33;border:1px solid #38BDF8;border-radius:6px;'
            'padding:10px;text-align:center;font-size:0.82rem;color:#38BDF8;font-weight:700;">'
            '⏱ Manual: ~20 minutes &nbsp;|&nbsp; AI: 2.3 seconds &nbsp;|&nbsp; Time saved: 19.96 minutes'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button("🔄 Run Again"):
            st.session_state.ai_demo_state = "ready"
            st.rerun()

# ── MIDDLE: Systems ───────────────────────────────────────────────────
with mid_col:
    st.markdown("### 🖥️ System Integration Status")
    st.caption("Expand each system to see what data was retrieved — green = clean, red = conflict")

    for system in SYSTEMS:
        abbrev = system["abbrev"]
        status = st.session_state.int_systems.get(abbrev, "idle")
        status_icon  = {"idle":"○","querying":"⏳","complete":"✅","conflict":"⚠️"}.get(status,"○")
        status_color = {"idle":"#8B949E","querying":"#F59E0B","complete":"#22C55E","conflict":"#EF4444"}.get(status,"#8B949E")
        status_label = {"idle":"Waiting","querying":"Querying...","complete":"Retrieved","conflict":"Conflict detected"}.get(status,"Waiting")

        with st.expander(
            f"{system['icon']} {system['name']} — {status_label}",
            expanded=(status in ["conflict","complete"])
        ):
            st.markdown(
                f'<div style="font-size:0.9rem;font-weight:800;color:#E6EDF3;margin-bottom:2px;">'
                f'{system["icon"]} {system["name"]}</div>'
                f'<div style="font-size:0.75rem;color:#8B949E;margin-bottom:6px;">{system["purpose"]}</div>'
                f'<div style="font-size:0.72rem;font-weight:700;color:{status_color};margin-bottom:8px;">'
                f'{status_icon} {status_label}'
                f'{" · Manual time: ~" + str(system["manual_mins"]) + " mins" if status == "idle" else ""}'
                f'</div>',
                unsafe_allow_html=True
            )
            if status in ["complete", "conflict"]:
                fields_html = ""
                for field, value in system["data"].items():
                    is_conflict = field == system.get("conflict_field")
                    tag_class = "conflict" if is_conflict else "ok"
                    flag = " ⚠️ CONFLICT" if is_conflict else ""
                    fields_html += f'<span class="field-tag {tag_class}">{field}: {value}{flag}</span>'
                st.markdown(fields_html, unsafe_allow_html=True)

    if st.session_state.int_state == "complete":
        st.divider()
        st.markdown("### ⚠️ Data Conflicts — Clinician Review Required")
        st.caption("The AI found these discrepancies between systems — a clinician must verify before acting on this data")

        for i, conflict in enumerate(CONFLICTS):
            is_resolved = i in st.session_state.conflicts_resolved
            opacity = "opacity:0.6;" if is_resolved else ""
            resolved_label = "✅ RESOLVED" if is_resolved else "⚠️ CONFLICT"
            st.markdown(
                f'<div class="conflict-card" style="{opacity}">'
                f'<div class="conflict-title">{resolved_label} — {conflict["field"]} '
                f'<span style="font-size:0.72rem;font-weight:400;color:#FCA5A5;margin-left:8px;">{conflict["severity"]} severity</span></div>'
                f'<div class="conflict-detail">'
                f'<b>{conflict["system1"]}:</b> {conflict["value1"]}<br>'
                f'<b>{conflict["system2"]}:</b> {conflict["value2"]}<br>'
                f'<b>Impact:</b> {conflict["impact"]}<br>'
                f'<b>Action required:</b> {conflict["action"]}'
                f'</div></div>',
                unsafe_allow_html=True
            )
            if not is_resolved:
                if st.button(f"✅ Resolve — {conflict['field']}", key=f"res_{i}"):
                    st.session_state.conflicts_resolved.add(i)
                    add_int_event(f"✅ Conflict resolved: {conflict['field']}", "success")
                    st.rerun()

        if len(st.session_state.conflicts_resolved) == len(CONFLICTS):
            st.markdown(
                '<div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:8px;'
                'padding:12px;text-align:center;font-size:0.85rem;color:#86EFAC;font-weight:700;">'
                '✅ All conflicts resolved — data reconciled and safe to use'
                '</div>',
                unsafe_allow_html=True
            )

# ── RIGHT: Event feed ─────────────────────────────────────────────────
with right_col:
    st.markdown("### 📡 Live Event Feed")
    st.caption("Every query and conflict logged with shift time")

    colors = {"ai":"#A855F7","success":"#22C55E","critical":"#EF4444","warning":"#F59E0B","info":"#38BDF8"}
    if not st.session_state.int_events:
        st.markdown(
            '<div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;'
            'padding:20px;text-align:center;color:#8B949E;font-size:0.8rem;">No events yet</div>',
            unsafe_allow_html=True
        )
    else:
        for event in reversed(st.session_state.int_events):
            color = colors.get(event["type"], "#38BDF8")
            st.markdown(
                f'<div style="border-left:3px solid {color};background:#161B22;'
                f'padding:8px 12px;margin-bottom:6px;border-radius:0 6px 6px 0;font-size:0.78rem;">'
                f'<span style="color:#8B949E;font-weight:600;">{event["time"]}</span><br>'
                f'<span style="color:#C9D1D9;">{event["text"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown(
        '<div style="background:#2D1A00;border:1px solid #F59E0B;border-radius:8px;'
        'padding:10px 12px;font-size:0.75rem;color:#FCD34D;font-weight:600;">'
        '⚠️ CLINICIAN REVIEW REQUIRED for all flagged data conflicts before any clinical decision is made'
        '</div>',
        unsafe_allow_html=True
    )
    st.divider()
    st.markdown(
        '<div style="font-size:0.72rem;color:#8B949E;line-height:1.7;">'
        '<b>47 data fields retrieved</b> across 5 systems.<br>'
        '<b>Manual equivalent:</b> ~20 minutes.<br>'
        '<b>AI time:</b> 2.3 seconds.<br>'
        '<b>Time saved:</b> 19.96 minutes per query.'
        '</div>',
        unsafe_allow_html=True
    )

st.divider()

# ── Multi-patient panel ───────────────────────────────────────────────
st.markdown("### 👥 Multi-Patient Integration — Full Ward Query")
st.caption("Query all 4 patients one by one or simultaneously — watch time saved accumulate")

mp1, mp2 = st.columns([2, 2])

with mp1:
    st.markdown("**Select patient to query:**")
    for i, p in enumerate(PATIENTS_INT):
        is_queried = i in st.session_state.queried_patients
        border_col = "#22C55E" if is_queried else "#30363D"
        status_txt = "✅ Queried" if is_queried else "○ Pending"
        st.markdown(
            f'<div style="background:#161B22;border:1px solid {border_col};border-radius:8px;'
            f'padding:12px 14px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<div style="font-size:0.88rem;font-weight:700;color:#E6EDF3;">{p["name"]}</div>'
            f'<div style="font-size:0.72rem;color:#8B949E;">{p["nhs"]} · {p["query"]}</div>'
            f'<div style="font-size:0.7rem;color:#8B949E;margin-top:2px;">Systems: {" · ".join(p["systems_needed"])}</div>'
            f'</div>'
            f'<span style="font-size:0.72rem;font-weight:700;color:{border_col};">{status_txt}</span>'
            f'</div></div>',
            unsafe_allow_html=True
        )
        if not is_queried:
            if st.button(f"🔗 Query all systems — {p['name'].split()[0]}", key=f"query_p_{i}"):
                st.session_state.queried_patients.add(i)
                shift_times = ["11:00", "11:00", "15:00", "15:00"]
                stime = shift_times[i]
                add_int_event(f"{stime} — {p['name']}: {len(p['systems_needed'])} systems in 2.3s — {p['key_findings'][:50]}...", "success", stime)
                if p["conflict"]:
                    add_int_event(f"{stime} — {p['name']} conflict: {p['conflict'][:60]}...", "critical", stime)
                st.rerun()

with mp2:
    st.markdown("**Results for queried patients:**")
    if not st.session_state.queried_patients:
        st.markdown(
            '<div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;'
            'padding:20px;text-align:center;color:#8B949E;font-size:0.8rem;">'
            'Select a patient on the left to query their systems</div>',
            unsafe_allow_html=True
        )
    else:
        for i in sorted(st.session_state.queried_patients):
            p = PATIENTS_INT[i]
            has_conflict = p["conflict"] is not None
            border = "#EF4444" if has_conflict else "#22C55E"
            conflict_html = (
                f'<div style="background:#2D0A0A;border:1px solid #EF4444;border-radius:4px;'
                f'padding:6px 10px;font-size:0.74rem;color:#FCA5A5;">⚠️ Conflict: {p["conflict"]}</div>'
                if has_conflict else
                '<div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:4px;'
                'padding:6px 10px;font-size:0.74rem;color:#86EFAC;">✅ No conflicts — data consistent</div>'
            )
            st.markdown(
                f'<div style="background:#0D1117;border:1.5px solid {border};border-radius:8px;'
                f'padding:12px 14px;margin-bottom:8px;">'
                f'<div style="font-size:0.82rem;font-weight:800;color:#E6EDF3;margin-bottom:6px;">'
                f'✅ {p["name"]} — {len(p["systems_needed"])} systems · 2.3s</div>'
                f'<div style="font-size:0.76rem;color:#86EFAC;line-height:1.6;margin-bottom:6px;">{p["key_findings"]}</div>'
                f'{conflict_html}</div>',
                unsafe_allow_html=True
            )

        if len(st.session_state.queried_patients) > 1:
            t_manual = sum(len(PATIENTS_INT[i]["systems_needed"]) * 4 for i in st.session_state.queried_patients)
            t_ai     = round(len(st.session_state.queried_patients) * 2.3, 1)
            st.markdown(
                f'<div style="background:#0D1F33;border:1px solid #38BDF8;border-radius:8px;padding:12px 14px;margin-top:8px;">'
                f'<div style="font-size:0.82rem;font-weight:700;color:#38BDF8;margin-bottom:4px;">'
                f'Running total — {len(st.session_state.queried_patients)} patients queried</div>'
                f'<div style="font-size:0.78rem;color:#C9D1D9;">'
                f'Manual equivalent: ~{t_manual} minutes<br>'
                f'AI total time: {t_ai} seconds<br>'
                f'<b style="color:#22C55E;">Time saved: {round(t_manual - t_ai/60, 1)} minutes this shift</b>'
                f'</div></div>',
                unsafe_allow_html=True
            )

        if st.button("🔗 Query ALL 4 patients simultaneously"):
            for i in range(len(PATIENTS_INT)):
                if i not in st.session_state.queried_patients:
                    st.session_state.queried_patients.add(i)
                    p = PATIENTS_INT[i]
                    add_int_event(f"{p['name']}: queried in 2.3s", "success")
            st.rerun()

st.divider()
context_lines = [f"- Systems status: {st.session_state.int_state}"]
for i in st.session_state.queried_patients:
    p = PATIENTS_INT[i]
    conflict_note = f" — CONFLICT: {p['conflict']}" if p["conflict"] else " — no conflict"
    context_lines.append(f"- {p['name']}: {p['query']}{conflict_note}")
live_context = "\n".join(context_lines) if len(context_lines) > 1 else "No patients queried yet this session."
render_chatbot("Integration Agent", live_context, key_prefix="integration_agent")

st.divider()
st.markdown(
    '<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:6px 0;">'
    'NHS AI Platform — Integration Agent · LD7326 · W25041744 · Northumbria University · '
    'All system data fictional · No real NHS systems accessed · DCB0129/DCB0160 compliant'
    '</div>',
    unsafe_allow_html=True
)