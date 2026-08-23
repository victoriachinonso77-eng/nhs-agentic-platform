"""
NHS AI Platform — Full Shift Simulation (07:00–19:00)
All 7 agents activating at the right moment across one complete shift
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run full_shift_simulation.py
"""

import streamlit as st
import time
import datetime
import random
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Full Shift Simulation",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }
#MainMenu, footer { visibility: hidden; }

.shift-header {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
}
.agent-moment {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 8px;
    transition: all 0.3s ease;
    animation: fadeIn 0.5s ease;
}
.agent-moment.active   { border-color: #38BDF8; border-left: 4px solid #38BDF8; }
.agent-moment.complete { border-color: #22C55E; border-left: 4px solid #22C55E; opacity: 0.8; }
.agent-moment.upcoming { opacity: 0.4; }
.agent-moment.urgent   { border-color: #EF4444; border-left: 4px solid #EF4444; }

.timeline-bar {
    background: #21262D; border-radius: 6px; height: 8px;
    margin: 8px 0; position: relative; overflow: hidden;
}
.timeline-fill {
    height: 8px; border-radius: 6px;
    background: linear-gradient(90deg, #38BDF8, #A855F7);
    transition: width 1s ease;
}

.stat-box {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 8px; padding: 12px; text-align: center;
}
.stat-num   { font-size: 1.8rem; font-weight: 900; line-height: 1; }
.stat-label { font-size: 0.68rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 3px; }

.event-feed-item {
    border-left: 3px solid #30363D; padding: 7px 12px;
    margin-bottom: 5px; border-radius: 0 5px 5px 0;
    background: #161B22; font-size: 0.76rem;
    animation: fadeIn 0.3s ease;
}
.event-feed-item.ai       { border-left-color: #A855F7; }
.event-feed-item.clinical { border-left-color: #38BDF8; }
.event-feed-item.warning  { border-left-color: #F59E0B; }
.event-feed-item.critical { border-left-color: #EF4444; }
.event-feed-item.success  { border-left-color: #22C55E; }

[data-testid="metric-container"] {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 12px !important;
}
[data-testid="metric-container"] label { color: #8B949E !important; font-size: 0.7rem !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.3rem !important; font-weight: 700 !important; }

.stButton > button {
    background: #1F6FEB !important; color: #FFF !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse  { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.pulse { animation: pulse 1.5s infinite; }
</style>
""", unsafe_allow_html=True)

# ── Shift timeline definition ─────────────────────────────────────────
# Each entry: (sim_hour, sim_min, agent, icon, trigger, description, impact, color)
SHIFT_EVENTS = [
    (7,  0,  "shift_start",    "🌅", "Day shift begins",
     "Day team arrives. 108 patients. 120 beds. XGBoost scoring begins across all wards.",
     "Ward state loaded. AI platform activated.", "clinical"),

    (7, 15,  "integration",    "🔗", "Integration Agent — automatic",
     "5 NHS systems queried simultaneously. EPR, NHS Spine, Pharmacy, RIS, LIS all consolidated in 2.3 seconds. Data conflict found: EPR shows 108 beds, NHS Spine shows 110.",
     "47 fields retrieved. 2 conflicts flagged. ~20 mins manual retrieval saved.", "ai"),

    (7, 30,  "workflow",       "⚡", "Workflow Agent — Cycle 1",
     "XGBoost bottleneck scores calculated. Ward C 91%, Ward A 87%, ICU 72%. Priority list generated. LSTM forecast: demand rising 15→17.4/day.",
     "P1: Ward C. P2: Ward A. P3: ICU. Demand surge flagged.", "ai"),

    (8,  0,  "security",      "🔒", "Security Agent — continuous monitoring",
     "184 access events monitored since 07:00. All within normal baseline. AES-256 encryption active. Audit trail complete.",
     "0 anomalies. LOW threat level. DCB0129/DCB0160 compliant.", "ai"),

    (8, 30,  "coordination",  "📞", "Coordination Agent — first batch",
     "8 incoming queries received. 6 auto-resolved (bed availability, porter scheduling, catering). 2 escalated to clinician (medication query, patient deterioration).",
     "6 interruptions prevented. 18 mins clinician time saved.", "ai"),

    (9,  0,  "workflow",      "⚡", "Workflow Agent — Cycle 2",
     "Ward C risk increased to 94% — 2 new emergency admissions. Priority list updated: Ward C now CRITICAL. Immediate action required.",
     "⚠️ ALERT: Ward C escalated. Discharge planning expedited for 3 patients.", "urgent"),

    (9, 30,  "documentation", "📝", "Documentation Agent — morning trigger",
     "23 overdue notes from overnight shift. Agent auto-drafts 16 routine admission summaries and discharge letters. Flags 7 complex cases for clinician review.",
     "16 notes drafted. 7 flagged. 128 minutes saved.", "ai"),

    (10, 0,  "cognitive",     "🧠", "Cognitive Support Agent — threshold crossed",
     "NASA-TLX estimated at 72/100 — HIGH. Occupancy 90%, 23 overdue notes, 14 handovers. 3 scaffolds activated: auto-sort by acuity, delegate documentation to admin, flag top 3 urgent decisions.",
     "NASA-TLX HIGH (72/100). 3 scaffolds active. ~60 mins admin load removed.", "ai"),

    (11, 0,  "integration",  "🔗", "Integration Agent — consultant data request",
     "Cardiologist requests full patient workup for James Okafor. 5 systems queried: ECG, troponin trend, echo booking, medications, demographics. Delivered in 2.3s.",
     "Complete workup in 2.3s vs ~20 mins manual. Conflict: LIS shows INR 1.1, Pharmacy shows no anticoagulant — flagged.", "ai"),

    (11, 30, "coordination",  "📞", "Coordination Agent — mid-morning batch",
     "14 queries received. 10 auto-resolved. 4 escalated. Bed manager query auto-answered: 108/120, 3 discharges expected 15:00. Porter queries routed automatically.",
     "10 interruptions prevented. 30 mins saved.", "ai"),

    (12, 0,  "security",     "🔒", "Security Agent — anomaly detected",
     "⚠️ ANOMALY: Unrecognised IP address attempting bulk record access. 847 records at risk. AI flags immediately — no records accessed. IT Security notified. IP blocked in 4 seconds.",
     "🚨 Anomaly contained. IT Security alerted. No data breach.", "critical"),

    (12, 30, "workflow",     "⚡", "Workflow Agent — Cycle 3",
     "Ward C risk reduced to 78% — discharge planning working. Ward A still 87%. Demand forecast day 3: 16.6 admissions. ICU: 1 bed freed. Updated priority list.",
     "Ward C improving. Ward A remains P1. ICU capacity slightly improved.", "ai"),

    (13, 0,  "documentation","📝", "Documentation Agent — afternoon trigger",
     "11 new notes required from morning activity. 8 auto-drafted. 3 flagged (post-op patients, complex medication changes). Clinician reviews 3 complex notes in 12 minutes.",
     "8 drafted. 3 reviewed by clinician. 64 mins saved.", "ai"),

    (14, 0,  "cognitive",    "🧠", "Cognitive Support Agent — load reducing",
     "NASA-TLX now 61/100 — documentation delegated, morning surge passed. 2 scaffolds remain. Deferred tasks released for processing. Admin catching up on backlog.",
     "Load reducing. Scaffolds de-escalating. Staff coping capacity improving.", "ai"),

    (15, 0,  "integration",  "🔗", "Integration Agent — discharge preparation",
     "3 patients flagged for discharge. Systems queried for TTO, social care referrals, transport arrangements. All data consolidated. Conflict: transport booking not reflected in EPR.",
     "Discharge documentation prepared. 1 conflict flagged and resolved.", "ai"),

    (16, 0,  "workflow",     "⚡", "Workflow Agent — Cycle 4",
     "Afternoon update: Ward C 71% (improving significantly), Ward A 82%, Ward D 28% (elective pathway running smoothly). Day 5 forecast: 17.0 — approaching threshold.",
     "Ward C improving. Ward A still requires attention. Pre-position for tomorrow.", "ai"),

    (16, 30, "coordination", "📞", "Coordination Agent — afternoon batch",
     "19 queries received. 14 auto-resolved. 5 escalated (2 clinical concerns, 1 family meeting request, 1 safeguarding query, 1 consent issue).",
     "14 interruptions prevented. 42 mins saved this batch.", "ai"),

    (17, 30, "security",    "🔒", "Security Agent — end of day report",
     "Total: 514 access events monitored. 1 anomaly detected and contained. 47 integrity checks passed. All data encrypted. Full audit trail complete.",
     "Shift security summary complete. IT Security briefed. Incident logged.", "ai"),

    (18, 0,  "cognitive",   "🧠", "Cognitive Support Agent — end of shift",
     "NASA-TLX 58/100 — MODERATE. Staff fatigue building but manageable. Handover preparation scaffolding activated. Non-urgent tasks deferred to night team.",
     "Scaffolding supporting handover preparation. Staff protected for final tasks.", "ai"),

    (18, 5,  "handover",    "🤝", "Handover Agent — activated",
     "1 hour before shift end. SBAR compliance check for all 4 patients. James Okafor: missing Assessment and Recommendation. Robert Adeniran: missing Assessment and Recommendation. 2 of 4 handovers incomplete.",
     "⚠️ 2 handovers flagged. AI drafts missing sections. Clinicians review and confirm in 6 minutes.", "urgent"),

    (18, 15, "documentation","📝", "Documentation Agent — shift end",
     "Final documentation sweep. 6 remaining notes auto-drafted. 2 complex cases handed to night doctor for completion. Total notes drafted today: 39. Total flagged for clinician: 12.",
     "39 notes drafted. 12 reviewed by clinicians. Total time saved: 312 minutes.", "ai"),

    (18, 55, "handover",    "🤝", "Handover Agent — sign-off",
     "All 4 patient handovers now complete. SBAR compliance: 100%. Night team briefed. All outstanding tasks documented. Ward safe to hand over.",
     "✅ 100% SBAR compliance. Night team ready to accept all patients.", "success"),

    (19, 0,  "shift_end",   "🌙", "Day shift complete",
     "Night team arrives. All patients handed over safely. Audit trail complete. Platform continues monitoring in background.",
     "✅ Shift complete. All 7 agents active throughout. See impact summary below.", "success"),
]

# ── Session state ─────────────────────────────────────────────────────
if "shift_sim_start"  not in st.session_state: st.session_state.shift_sim_start = None
if "shift_running"    not in st.session_state: st.session_state.shift_running = False
if "shift_events"     not in st.session_state: st.session_state.shift_events = []
if "current_sim_mins" not in st.session_state: st.session_state.current_sim_mins = 0
if "shift_speed"      not in st.session_state: st.session_state.shift_speed = "Fast"

def get_sim_time(mins_elapsed):
    """Convert elapsed sim minutes to shift time."""
    shift_start = 7 * 60  # 07:00 in minutes
    return shift_start + mins_elapsed

def format_sim_time(total_mins):
    h = total_mins // 60
    m = total_mins % 60
    return f"{h:02d}:{m:02d}"

def get_events_at_time(sim_mins):
    """Return events that should have occurred by this sim time."""
    sim_total = 7 * 60 + sim_mins  # Convert to minutes from midnight
    triggered = []
    for ev in SHIFT_EVENTS:
        ev_mins = ev[0] * 60 + ev[1]
        if ev_mins <= sim_total:
            triggered.append(ev)
    return triggered

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            🏥 Full Shift Simulation — 07:00 to 19:00
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            All 7 agents · One complete NHS shift · Royal London Hospital · Emergency Assessment Unit
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">
        LD7326 · W25041744 · Northumbria University<br>
        Design, Development and Feasibility Evaluation
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#1A1A0A;border:1px solid #F59E0B;border-radius:6px;
padding:8px 14px;margin-bottom:12px;font-size:0.73rem;color:#D4A520;">
    ⚖️ <b>Research Simulation:</b> All scenarios, patients, and clinical events are entirely fictional.
    No real NHS data used. Sister Amara does not exist — this is a research demonstration.
    GDPR · NHS Act 2006 · DCB0129/DCB0160 compliant · W25041744
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    speed = st.select_slider(
        "Simulation speed",
        ["Slow", "Normal", "Fast", "Instant"],
        value="Fast"
    )
    st.session_state.shift_speed = speed

with c2:
    if not st.session_state.shift_running:
        if st.button("▶ Start Full Shift Simulation"):
            st.session_state.shift_sim_start = datetime.datetime.now()
            st.session_state.shift_running = True
            st.session_state.current_sim_mins = 0
            st.rerun()
    else:
        if st.button("⏸ Pause"):
            st.session_state.shift_running = False
            st.rerun()

with c3:
    if st.session_state.shift_running:
        if st.button("⏩ Skip to End"):
            st.session_state.current_sim_mins = 12 * 60
            st.session_state.shift_running = False
            st.rerun()

with c4:
    if st.button("🔄 Reset Simulation"):
        for key in ["shift_sim_start","shift_running","shift_events","current_sim_mins"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

st.divider()

# ── Compute current simulation time ──────────────────────────────────
speed_multiplier = {"Slow": 10, "Normal": 30, "Fast": 60, "Instant": 720}.get(speed, 60)

if st.session_state.shift_running and st.session_state.shift_sim_start:
    elapsed_real = (datetime.datetime.now() - st.session_state.shift_sim_start).total_seconds()
    sim_mins = min(int(elapsed_real * speed_multiplier / 60), 12 * 60)
    st.session_state.current_sim_mins = sim_mins
    if sim_mins >= 12 * 60:
        st.session_state.shift_running = False

sim_mins = st.session_state.current_sim_mins
sim_total_mins = 7 * 60 + sim_mins
sim_time_str   = format_sim_time(sim_total_mins)
shift_pct      = min(100, int(sim_mins / (12 * 60) * 100))
triggered_events = get_events_at_time(sim_mins)

# ── Shift progress bar ────────────────────────────────────────────────
st.markdown(f"""
<div class="shift-header">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div style="font-size:1rem;font-weight:800;color:#E6EDF3;">
            {'🟢 Day Shift Running' if st.session_state.shift_running else '⏸ Paused' if sim_mins > 0 and sim_mins < 720 else '✅ Shift Complete' if sim_mins >= 720 else '⏳ Not Started'}
        </div>
        <div style="font-size:1.3rem;font-weight:900;color:#38BDF8;">
            {sim_time_str}
        </div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#8B949E;margin-bottom:4px;">
        <span>07:00 Start</span>
        <span>10:00</span>
        <span>13:00</span>
        <span>16:00</span>
        <span>19:00 End</span>
    </div>
    <div class="timeline-bar">
        <div class="timeline-fill" style="width:{shift_pct}%;"></div>
    </div>
    <div style="font-size:0.72rem;color:#8B949E;text-align:right;">
        {shift_pct}% complete · {len(triggered_events)} agent activations
    </div>
</div>
""", unsafe_allow_html=True)

# ── Metrics ───────────────────────────────────────────────────────────
notes_drafted  = sum(1 for e in triggered_events if e[2] == "documentation") * 16
queries_resolved = sum(1 for e in triggered_events if e[2] == "coordination") * 10
mins_saved     = notes_drafted * 8 + queries_resolved * 3 + len(triggered_events) * 2
anomalies      = 1 if any(e[2] == "security" and "ANOMALY" in e[4] for e in triggered_events) else 0
handover_pct   = 100 if any(e[2] == "handover" and "sign-off" in e[4].lower() for e in triggered_events) else 50 if any(e[2] == "handover" for e in triggered_events) else 0

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Simulated Time",      sim_time_str)
m2.metric("Agent Activations",   str(len(triggered_events)))
m3.metric("Notes Auto-Drafted",  str(notes_drafted))
m4.metric("Queries Resolved",    str(queries_resolved))
m5.metric("Time Saved (est.)",   f"{mins_saved} mins")
m6.metric("SBAR Compliance",     f"{handover_pct}%")

st.divider()

# ── Layout ────────────────────────────────────────────────────────────
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("### 🕐 Shift Timeline — Agent Activations")
    st.caption("Each agent activates at its correct clinical trigger point")

    if sim_mins == 0:
        st.markdown(
            '<div style="background:#161B22;border:1px dashed #30363D;border-radius:10px;'
            'padding:40px;text-align:center;color:#8B949E;">'
            '<div style="font-size:2rem;margin-bottom:8px;">🏥</div>'
            '<div style="font-size:1rem;font-weight:600;color:#E6EDF3;margin-bottom:4px;">Ready to start</div>'
            '<div style="font-size:0.85rem;">Click ▶ Start Full Shift Simulation to follow Sister Amara\'s ward from 07:00 to 19:00</div>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        # Show all events — triggered ones shown fully, future ones dimmed
        for ev in SHIFT_EVENTS:
            ev_mins_total = ev[0] * 60 + ev[1]
            is_triggered  = ev_mins_total <= sim_total_mins
            is_current    = sim_total_mins - ev_mins_total < 30 and is_triggered
            is_urgent     = ev[7] in ["urgent", "critical"]
            is_success    = ev[7] == "success"

            if is_triggered and is_urgent:
                css = "urgent"
            elif is_triggered and is_success:
                css = "complete"
            elif is_triggered:
                css = "active"
            else:
                css = "upcoming"

            icon_color = {
                "urgent":   "#EF4444",
                "critical": "#EF4444",
                "success":  "#22C55E",
                "ai":       "#A855F7",
                "clinical": "#38BDF8",
            }.get(ev[7], "#38BDF8")

            agent_colors = {
                "documentation": "#38BDF8",
                "handover":      "#22C55E",
                "workflow":      "#F59E0B",
                "cognitive":     "#A855F7",
                "integration":   "#EF4444",
                "coordination":  "#F97316",
                "security":      "#6366F1",
                "shift_start":   "#38BDF8",
                "shift_end":     "#22C55E",
            }
            agent_color = agent_colors.get(ev[2], "#38BDF8")

            active_badge = '<span style="font-size:0.7rem;color:#F59E0B;font-weight:700;">⚡ ACTIVE NOW</span>' if is_current else ''
            done_check = '<div style="font-size:0.7rem;color:#22C55E;font-weight:700;">✅</div>' if is_triggered and not is_current else ''
            impact_box = (
                f'<div style="background:#0D1F33;border:1px solid {agent_color};border-radius:6px;'
                f'padding:6px 10px;margin-top:8px;font-size:0.75rem;color:#C9D1D9;font-weight:500;">'
                f'{ev[6]}</div>'
            ) if is_triggered else ''
            detail_display = 'display:none;' if not is_triggered else ''

            st.markdown(
                f'<div class="agent-moment {css}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div style="display:flex;gap:12px;align-items:flex-start;">'
                f'<div style="font-size:1.3rem;">{ev[3]}</div>'
                f'<div>'
                f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:3px;">'
                f'<span style="font-size:0.7rem;font-weight:700;background:#21262D;'
                f'border:1px solid {agent_color};color:{agent_color};padding:1px 7px;'
                f'border-radius:4px;">{ev[2].upper().replace("_"," ")}</span> '
                f'<span style="font-size:0.7rem;font-weight:700;color:#8B949E;">'
                f'{format_sim_time(ev[0]*60+ev[1])}</span> {active_badge}'
                f'</div>'
                f'<div style="font-size:0.82rem;font-weight:700;color:#E6EDF3;margin-bottom:3px;">{ev[4]}</div>'
                f'<div style="font-size:0.75rem;color:#8B949E;line-height:1.5;{detail_display}">{ev[5]}</div>'
                f'</div></div>{done_check}</div>{impact_box}</div>',
                unsafe_allow_html=True
            )

with right_col:
    st.markdown("### 📊 Running Impact")
    st.caption("Cumulative shift totals — updating in real time")

    # Agent activation counts
    agent_counts = {}
    for ev in triggered_events:
        agent = ev[2]
        agent_counts[agent] = agent_counts.get(agent, 0) + 1

    agent_display = [
        ("📝", "Documentation",  "documentation"),
        ("🤝", "Handover",       "handover"),
        ("⚡", "Workflow",       "workflow"),
        ("🧠", "Cognitive",      "cognitive"),
        ("🔗", "Integration",    "integration"),
        ("📞", "Coordination",   "coordination"),
        ("🔒", "Security",       "security"),
    ]

    for icon, name, key in agent_display:
        count = agent_counts.get(key, 0)
        color = "#22C55E" if count > 0 else "#30363D"
        status_text = ('✅ ' + str(count) + 'x') if count > 0 else '⏳ Waiting'
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:7px 12px;background:#161B22;border:1px solid {color};'
            f'border-radius:6px;margin-bottom:4px;">'
            f'<span style="font-size:0.82rem;">{icon} {name}</span>'
            f'<span style="font-size:0.82rem;font-weight:700;color:{color};">{status_text}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Cumulative stats
    st.markdown("**Cumulative Impact:**")
    stats = [
        ("Notes auto-drafted",    notes_drafted,    "#38BDF8"),
        ("Queries resolved",      queries_resolved,  "#22C55E"),
        ("Time saved (mins)",     mins_saved,        "#A855F7"),
        ("Anomalies caught",      anomalies,         "#EF4444" if anomalies > 0 else "#22C55E"),
        ("SBAR compliance",       f"{handover_pct}%", "#22C55E" if handover_pct == 100 else "#F59E0B"),
    ]
    for label, value, color in stats:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:5px 10px;'
            f'background:#161B22;border-radius:5px;margin-bottom:3px;">'
            f'<span style="font-size:0.75rem;color:#8B949E;">{label}</span>'
            f'<span style="font-size:0.82rem;font-weight:800;color:{color};">{value}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Shift complete summary
    if sim_mins >= 12 * 60:
        st.markdown(
            '<div style="background:#0A2D1A;border:2px solid #22C55E;border-radius:10px;'
            'padding:16px;text-align:center;">'
            '<div style="font-size:1.1rem;font-weight:800;color:#86EFAC;margin-bottom:6px;">✅ Shift Complete</div>'
            '<div style="font-size:0.78rem;color:#86EFAC;line-height:1.7;">'
            'All 7 agents ran successfully<br>'
            'Night team safely received all patients<br>'
            'Full audit trail maintained<br>'
            'DCB0129/DCB0160 compliant</div></div>',
            unsafe_allow_html=True
        )

        st.divider()
        st.markdown("**Final Shift Summary:**")
        final_stats = [
            ("Total agent activations",  str(len(triggered_events))),
            ("Total notes drafted",      "39"),
            ("Total queries resolved",   "48"),
            ("Total time saved",         "~312 mins (5.2 hrs)"),
            ("Security incidents",       "1 anomaly — contained"),
            ("SBAR compliance",          "100%"),
            ("Cognitive load reduction", "25.4% (NASA-TLX)"),
            ("ED wait improvement",      "-22.1%"),
        ]
        for label, val in final_stats:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:5px 10px;'
                f'background:#161B22;border-radius:5px;margin-bottom:3px;">'
                f'<span style="font-size:0.73rem;color:#8B949E;">{label}</span>'
                f'<span style="font-size:0.78rem;font-weight:700;color:#86EFAC;">{val}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── Chatbot ───────────────────────────────────────────────────────────
st.divider()
context_lines = [
    f"- Simulated shift time: {sim_time_str} ({shift_pct}% through the 07:00-19:00 shift)",
    f"- Agent activations so far: {len(triggered_events)}",
    f"- Notes auto-drafted: {notes_drafted}",
    f"- Queries resolved: {queries_resolved}",
    f"- Estimated time saved: {mins_saved} mins",
    f"- Security anomalies caught: {anomalies}",
    f"- SBAR compliance: {handover_pct}%",
]
if triggered_events:
    context_lines.append("Recent agent activations: " + "; ".join(
        f"{e[2]} at {format_sim_time(e[0]*60+e[1])}" for e in triggered_events[-5:]
    ))
live_context = "\n".join(context_lines)
render_chatbot("Full Shift Simulation (all 7 agents)", live_context, key_prefix="fullshift_agent")

# ── Auto-advance ──────────────────────────────────────────────────────
if st.session_state.shift_running:
    delay = {"Slow": 2.0, "Normal": 1.0, "Fast": 0.5, "Instant": 0.1}.get(speed, 0.5)
    time.sleep(delay)
    st.rerun()

st.divider()
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:6px 0;">
    NHS AI Platform — Full Shift Simulation · LD7326 · W25041744 · Northumbria University ·
    All scenarios fictional · 7 agents · 12-hour shift · DCB0129/DCB0160/GDPR compliant
</div>
""", unsafe_allow_html=True)