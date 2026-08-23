"""
NHS AI Platform — Workflow Agent Live Simulation
Shows priority list updating in real time as ward conditions change
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run workflow_simulation.py
"""

import streamlit as st
import time
import datetime
import random
import os
import numpy as np
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Workflow Agent Simulation",
    page_icon="⚡",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }
#MainMenu, footer { visibility: hidden; }

/* Priority cards */
.priority-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 10px;
    transition: all 0.3s ease;
    animation: slideIn 0.4s ease;
}
.priority-card.p1 {
    border-left: 5px solid #EF4444;
    background: linear-gradient(135deg, #1A0A0A 0%, #161B22 100%);
}
.priority-card.p2 {
    border-left: 5px solid #F59E0B;
    background: linear-gradient(135deg, #1A1200 0%, #161B22 100%);
}
.priority-card.p3 {
    border-left: 5px solid #38BDF8;
    background: linear-gradient(135deg, #001A2D 0%, #161B22 100%);
}
.priority-card.resolved {
    border-left: 5px solid #22C55E;
    background: linear-gradient(135deg, #0A2D1A 0%, #161B22 100%);
    opacity: 0.7;
}

.priority-number {
    font-size: 2rem;
    font-weight: 900;
    line-height: 1;
}
.p1 .priority-number { color: #EF4444; }
.p2 .priority-number { color: #F59E0B; }
.p3 .priority-number { color: #38BDF8; }

.ward-name {
    font-size: 1rem;
    font-weight: 800;
    color: #E6EDF3;
    margin-bottom: 2px;
}
.ward-meta {
    font-size: 0.75rem;
    color: #8B949E;
    margin-bottom: 8px;
}
.action-text {
    font-size: 0.88rem;
    font-weight: 600;
    color: #E6EDF3;
    margin-bottom: 6px;
    line-height: 1.4;
}
.reason-text {
    font-size: 0.78rem;
    color: #8B949E;
    line-height: 1.5;
}
.risk-bar-bg {
    background: #21262D;
    border-radius: 4px;
    height: 6px;
    margin: 6px 0;
}
.risk-bar-fill {
    height: 6px;
    border-radius: 4px;
}

/* Event feed */
.event-item {
    background: #161B22;
    border-left: 3px solid #30363D;
    padding: 8px 12px;
    margin-bottom: 6px;
    border-radius: 0 6px 6px 0;
    font-size: 0.78rem;
    animation: fadeIn 0.4s ease;
}
.event-item.critical { border-left-color: #EF4444; }
.event-item.warning  { border-left-color: #F59E0B; }
.event-item.success  { border-left-color: #22C55E; }
.event-item.ai       { border-left-color: #A855F7; }
.event-item.info     { border-left-color: #38BDF8; }

.event-time { color: #8B949E; font-weight: 600; }
.event-text { color: #C9D1D9; }

/* Forecast chart */
.forecast-bar {
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 80px;
    padding: 0 4px;
}
.forecast-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
}
.forecast-bar-inner {
    width: 100%;
    border-radius: 3px 3px 0 0;
    transition: height 0.5s ease;
}
.forecast-label {
    font-size: 0.6rem;
    color: #8B949E;
    text-align: center;
}
.forecast-value {
    font-size: 0.65rem;
    font-weight: 700;
    text-align: center;
}

/* Metrics */
[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 12px !important;
}
[data-testid="metric-container"] label {
    color: #8B949E !important;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}

.stButton > button {
    background: #1F6FEB !important;
    color: #FFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
}
.stButton > button:hover { background: #388BFD !important; }

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.5; }
}
.pulse { animation: pulse 1.5s infinite; }
</style>
""", unsafe_allow_html=True)

# ── Ward definitions ──────────────────────────────────────────────────
WARDS = {
    "Ward A": {
        "specialty":   "Emergency Medicine",
        "beds":        24,
        "base_risk":   0.87,
        "adm_type":    "EW EMER.",
        "color":       "#EF4444",
    },
    "Ward B": {
        "specialty":   "Acute Medicine",
        "beds":        20,
        "base_risk":   0.43,
        "adm_type":    "URGENT",
        "color":       "#F59E0B",
    },
    "Ward C": {
        "specialty":   "Emergency Surgery",
        "beds":        18,
        "base_risk":   0.91,
        "adm_type":    "EW EMER.",
        "color":       "#EF4444",
    },
    "Ward D": {
        "specialty":   "Elective Surgery",
        "beds":        22,
        "base_risk":   0.21,
        "adm_type":    "ELECTIVE",
        "color":       "#22C55E",
    },
    "ICU": {
        "specialty":   "Intensive Care",
        "beds":        12,
        "base_risk":   0.72,
        "adm_type":    "DIRECT EMER.",
        "color":       "#F59E0B",
    },
}

# Actions per priority level per ward
ACTIONS = {
    "Ward A": {
        "action":  "Expedite discharge planning — identify patients ready for home today",
        "reason":  "87% bottleneck risk. EW EMER. admission pattern. 4 patients LOS >134.9h threshold.",
        "steps":   ["Review discharge criteria for all 24 patients", "Contact family of 2 patients pending social care", "Flag 3 patients for morning ward round discharge"],
    },
    "Ward B": {
        "action":  "Pre-position staff — review pending transfers before afternoon surge",
        "reason":  "43% bottleneck risk. Demand forecast rising. 2 transfers pending from Ward A.",
        "steps":   ["Accept 2 step-down transfers from Ward A", "Ensure 4 beds available by 16:00", "Alert bed manager of incoming capacity"],
    },
    "Ward C": {
        "action":  "P1 — Immediate bed release required — coordinate with theatre team",
        "reason":  "91% bottleneck risk. Highest risk ward. 3 post-op patients blocking surgical beds.",
        "steps":   ["Expedite post-op step-down for Beds 4, 7, 12", "Notify Ward B of incoming step-down patients", "Alert theatre coordinator — 2 elective cases at risk"],
    },
    "Ward D": {
        "action":  "Monitor only — no immediate action required",
        "reason":  "21% bottleneck risk. Elective pathway running smoothly. Low demand pressure.",
        "steps":   ["Routine ward round as scheduled", "Continue standard discharge planning", "No escalation required"],
    },
    "ICU": {
        "action":  "Pre-position for demand surge — 7-day forecast shows increasing admissions",
        "reason":  "72% bottleneck risk. 3 available beds. Forecast: admissions rising 15→17.4/day.",
        "steps":   ["Review ICU step-down criteria for 2 patients", "Alert HDU of potential step-downs", "Brief consultant on 7-day surge forecast"],
    },
}

# ── Session state ─────────────────────────────────────────────────────
if "sim_start"        not in st.session_state:
    st.session_state.sim_start = datetime.datetime.now()
if "ward_risks"       not in st.session_state:
    st.session_state.ward_risks = {w: d["base_risk"] for w, d in WARDS.items()}
if "events"           not in st.session_state:
    st.session_state.events = []
if "cycle"            not in st.session_state:
    st.session_state.cycle = 1
if "resolved"         not in st.session_state:
    st.session_state.resolved = set()
if "actions_taken"    not in st.session_state:
    st.session_state.actions_taken = {}
if "last_cycle_time"  not in st.session_state:
    st.session_state.last_cycle_time = datetime.datetime.now()
if "auto_running"     not in st.session_state:
    st.session_state.auto_running = False
if "ignored_cycles"   not in st.session_state:
    st.session_state.ignored_cycles = {}

# ── Helper functions ──────────────────────────────────────────────────
def add_event(text, event_type="info"):
    st.session_state.events.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "text": text,
        "type": event_type
    })

def get_priority_list():
    """Rank wards by current risk score."""
    risks = {
        w: r for w, r in st.session_state.ward_risks.items()
        if w not in st.session_state.resolved
    }
    return sorted(risks.items(), key=lambda x: x[1], reverse=True)

def get_demand_forecast():
    """Generate 7-day LSTM-style demand forecast."""
    base = 15.0
    np.random.seed(st.session_state.cycle)
    return [round(base + i * 0.4 + np.random.uniform(-0.3, 0.3), 1)
            for i in range(7)]

def get_shift_time(cycle):
    """Map cycle number to simulated shift time starting at 07:30."""
    shift_start_mins = 7 * 60 + 30  # 07:30
    sim_mins = shift_start_mins + (cycle - 1) * 30
    h = sim_mins // 60
    m = sim_mins % 60
    return f"{h:02d}:{m:02d}"

def run_workflow_cycle():
    """Run one 30-minute workflow cycle."""
    st.session_state.cycle += 1
    st.session_state.last_cycle_time = datetime.datetime.now()
    shift_time = get_shift_time(st.session_state.cycle)

    # Track ignored P1 wards — risk escalates faster if ignored
    changes = {}
    for ward, risk in st.session_state.ward_risks.items():
        if ward in st.session_state.resolved:
            continue
        if ward in st.session_state.actions_taken:
            # Action taken — risk reduces
            delta = random.uniform(-0.08, -0.02)
        elif risk > 0.7:
            # P1 ward ignored — risk escalates faster
            ignored_cycles = st.session_state.get("ignored_cycles", {})
            ignored_cycles[ward] = ignored_cycles.get(ward, 0) + 1
            st.session_state.ignored_cycles = ignored_cycles
            delta = random.uniform(0.02, 0.08)  # worse each cycle
        else:
            delta = random.uniform(-0.03, 0.04)
        new_risk = max(0.05, min(0.99, risk + delta))
        changes[ward] = (risk, new_risk)
        st.session_state.ward_risks[ward] = new_risk

    # Log events with shift time
    add_event(f"⚡ {shift_time} — Cycle {st.session_state.cycle}: XGBoost scores recalculated", "ai")
    for ward, (old, new) in changes.items():
        if new > old + 0.05:
            add_event(f"⚠️ {shift_time} — {ward}: Risk ↑ {old:.0%} → {new:.0%}", "warning")
        elif new < old - 0.05:
            add_event(f"✅ {shift_time} — {ward}: Risk ↓ {old:.0%} → {new:.0%}", "success")

    # Escalation alert for ignored P1 wards
    ignored = st.session_state.get("ignored_cycles", {})
    for ward, count in ignored.items():
        if count >= 2 and ward not in st.session_state.actions_taken:
            add_event(
                f"🚨 {shift_time} — {ward} ESCALATING — ignored for {count} cycles. "
                f"Risk now {st.session_state.ward_risks[ward]:.0%}. IMMEDIATE ACTION REQUIRED.",
                "critical"
            )

    # Check if any ward resolved
    for ward, risk in st.session_state.ward_risks.items():
        if risk < 0.3 and ward in st.session_state.actions_taken:
            if ward not in st.session_state.resolved:
                st.session_state.resolved.add(ward)
                add_event(f"✅ {shift_time} — {ward}: Bottleneck resolved", "success")

# ── Header ────────────────────────────────────────────────────────────
now = datetime.datetime.now()
current_shift_time = get_shift_time(st.session_state.cycle)

st.markdown(f"""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            ⚡ Workflow Agent — Live Priority Simulation
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            XGBoost bottleneck predictions + LSTM 7-day forecast → Ranked priority actions
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">
        Royal London Hospital · Shift time: <b style="color:#38BDF8;">{current_shift_time}</b><br>
        Cycle {st.session_state.cycle} · Updated: {st.session_state.last_cycle_time.strftime("%H:%M:%S")}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Disclaimer ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1A1A0A;border:1px solid #F59E0B;border-radius:6px;
padding:8px 14px;margin-bottom:12px;font-size:0.73rem;color:#D4A520;">
    ⚖️ <b>Research Simulation:</b> All ward data and patient scenarios are fictional.
    No real NHS data used. GDPR · DCB0129/DCB0160 compliant · W25041744
</div>
""", unsafe_allow_html=True)

# ── Live alerts ───────────────────────────────────────────────────────
demand = get_demand_forecast()
priority_list = get_priority_list()

# Demand surge alert — fires when day 7 forecast exceeds 17.0
if demand[-1] >= 17.0:
    st.markdown(f"""
    <div style="background:#2D1A00;border:2px solid #F59E0B;border-radius:8px;
    padding:12px 18px;margin-bottom:8px;">
        <div style="font-size:0.9rem;font-weight:800;color:#FCD34D;">
            📈 DEMAND SURGE ALERT — LSTM Forecast
        </div>
        <div style="font-size:0.82rem;color:#FCD34D;margin-top:4px;">
            Day 7 forecast: <b>{demand[-1]} admissions/day</b> — exceeds surge threshold (17.0).
            Pre-position bank staff for Thursday. Review ICU step-down criteria today.
            Alert bed manager and site manager now.
        </div>
    </div>""", unsafe_allow_html=True)

# Ignored P1 ward escalation alert
ignored = st.session_state.get("ignored_cycles", {})
critical_ignored = [(w, c) for w, c in ignored.items()
                    if c >= 2 and w not in st.session_state.actions_taken
                    and w not in st.session_state.resolved]
if critical_ignored:
    names = ", ".join([f"{w} ({c} cycles ignored)" for w, c in critical_ignored])
    st.markdown(f"""
    <div style="background:#2D0A0A;border:2px solid #EF4444;border-radius:8px;
    padding:12px 18px;margin-bottom:8px;animation:pulse 1.5s infinite;">
        <div style="font-size:0.9rem;font-weight:800;color:#FCA5A5;">
            🚨 CRITICAL — P1 WARDS IGNORED AND ESCALATING
        </div>
        <div style="font-size:0.82rem;color:#FCA5A5;margin-top:4px;">
            {names} — risk increasing each cycle with no action taken.
            Bottleneck probability approaching critical threshold.
            Immediate clinical intervention required.
        </div>
    </div>""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 2])
with ctrl1:
    if st.button("⚡ Run Next 30-Min Cycle"):
        run_workflow_cycle()
        add_event("Manual cycle triggered by clinical team", "info")
        st.rerun()
with ctrl2:
    auto = st.toggle("🔄 Auto-run cycles", value=st.session_state.auto_running)
    st.session_state.auto_running = auto
with ctrl3:
    if st.button("🔄 Reset Simulation"):
        for key in ["ward_risks","events","cycle","resolved",
                    "actions_taken","last_cycle_time","sim_start","ignored_cycles"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
with ctrl4:
    speed = st.select_slider("Cycle speed", ["Slow (30s)", "Fast (10s)", "Instant"], value="Fast (10s)")

st.divider()

# ── Summary metrics ───────────────────────────────────────────────────

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Active Wards",    str(len(WARDS) - len(st.session_state.resolved)))
m2.metric("P1 Critical",     str(sum(1 for _, r in priority_list if r > 0.7)))
m3.metric("P2 High",         str(sum(1 for _, r in priority_list if 0.4 < r <= 0.7)))
m4.metric("Resolved",        str(len(st.session_state.resolved)))
m5.metric("Workflow Cycles", str(st.session_state.cycle))
m6.metric("Day 7 Forecast",  f"{demand[-1]}/day",
          f"{'↑' if demand[-1] > demand[0] else '↓'} from {demand[0]}/day")

st.divider()

# ── Main layout ───────────────────────────────────────────────────────
left_col, mid_col, right_col = st.columns([2, 2, 1])

# ── LEFT: Priority action list ────────────────────────────────────────
with left_col:
    st.markdown("### ⚡ Priority Action List")
    st.caption(f"Updated every 30 minutes · Cycle {st.session_state.cycle} · "
               f"Shift time: {current_shift_time}")

    if not priority_list and not st.session_state.resolved:
        st.info("No active wards — run first cycle")

    # Show active wards ranked by risk
    for rank, (ward, risk) in enumerate(priority_list):
        action_data = ACTIONS.get(ward, {})
        taken = ward in st.session_state.actions_taken

        if risk > 0.7:
            p_class, p_label, p_num = "p1", "P1 — CRITICAL", f"#{rank+1}"
        elif risk > 0.4:
            p_class, p_label, p_num = "p2", "P2 — HIGH", f"#{rank+1}"
        else:
            p_class, p_label, p_num = "p3", "P3 — MONITOR", f"#{rank+1}"

        bar_color = {"p1": "#EF4444", "p2": "#F59E0B", "p3": "#38BDF8"}.get(p_class)
        bar_width  = int(risk * 100)

        ignored_count = st.session_state.ignored_cycles.get(ward, 0)
        ignored_warning = ""
        if ignored_count >= 2 and not taken:
            ignored_warning = f'<div style="font-size:0.72rem;font-weight:700;color:#EF4444;margin-top:4px;">🚨 Ignored for {ignored_count} cycles — risk escalating</div>'

        st.markdown(f"""
        <div class="priority-card {p_class}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div class="priority-number">{p_num}</div>
                    <div>
                        <div class="ward-name">{ward}</div>
                        <div class="ward-meta">{WARDS[ward]['specialty']} · {WARDS[ward]['beds']} beds · {WARDS[ward]['adm_type']}</div>
                        <div style="font-size:0.68rem;color:#8B949E;margin-top:2px;">
                            Cycle {st.session_state.cycle} · {current_shift_time}
                        </div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.5rem;font-weight:800;color:{bar_color};">{risk:.0%}</div>
                    <div style="font-size:0.65rem;color:#8B949E;">Bottleneck Risk</div>
                    <div style="font-size:0.65rem;color:{'#22C55E' if taken else '#EF4444'};font-weight:700;">
                        {'✅ Action taken' if taken else '⚠️ Awaiting action'}
                    </div>
                </div>
            </div>
            <div class="risk-bar-bg">
                <div class="risk-bar-fill" style="width:{bar_width}%;background:{bar_color};"></div>
            </div>
            <div class="action-text" style="margin-top:8px;">
                🎯 {action_data.get('action', 'Review required')}
            </div>
            <div class="reason-text">{action_data.get('reason', '')}</div>
            {ignored_warning}
        </div>""", unsafe_allow_html=True)

        # Action steps and button
        with st.expander(f"📋 Action steps — {ward}", expanded=(rank == 0 and not taken)):
            steps = action_data.get("steps", [])
            for i, step in enumerate(steps):
                done = taken
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;padding:6px 0;
                border-bottom:1px solid #21262D;">
                    <span style="color:{'#22C55E' if done else '#8B949E'};font-size:1rem;">
                        {'✅' if done else '○'}
                    </span>
                    <span style="font-size:0.82rem;color:{'#C9D1D9' if not done else '#8B949E'};">
                        {step}
                    </span>
                </div>""", unsafe_allow_html=True)

            st.markdown("")
            if not taken:
                if st.button(f"✅ Mark Action Complete — {ward}",
                             key=f"action_{ward}"):
                    st.session_state.actions_taken[ward] = datetime.datetime.now().strftime("%H:%M:%S")
                    add_event(f"✅ Action completed for {ward} — risk reduction expected next cycle", "success")
                    st.rerun()
            else:
                st.markdown(f"""
                <div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:6px;
                padding:8px 12px;font-size:0.78rem;color:#86EFAC;font-weight:600;">
                    ✅ Action completed at {st.session_state.actions_taken[ward]} —
                    risk score will reduce next cycle
                </div>""", unsafe_allow_html=True)

    # Resolved wards
    if st.session_state.resolved:
        st.markdown("---")
        st.markdown("**✅ Resolved wards**")
        for ward in st.session_state.resolved:
            st.markdown(f"""
            <div class="priority-card resolved">
                <div style="display:flex;justify-content:space-between;">
                    <div>
                        <div class="ward-name" style="color:#8B949E;">{ward}</div>
                        <div class="ward-meta">Bottleneck resolved — removed from priority list</div>
                    </div>
                    <div style="font-size:1.2rem;font-weight:800;color:#22C55E;">
                        {st.session_state.ward_risks.get(ward, 0):.0%}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

# ── MIDDLE: Demand forecast + risk trend ─────────────────────────────
with mid_col:
    st.markdown("### 📈 LSTM 7-Day Demand Forecast")
    st.caption("Daily admission volume forecast · 14-day lookback window · MAPE = 7.26%")

    # Visual bar chart
    max_val = max(demand) + 2
    forecast_html = '<div style="display:flex;align-items:flex-end;gap:4px;height:100px;padding:0 4px;margin-bottom:4px;">'
    for i, val in enumerate(demand):
        pct   = int((val / max_val) * 100)
        color = "#EF4444" if val > 17 else "#F59E0B" if val > 16 else "#38BDF8"
        label = f"D{i+1}"
        forecast_html += f"""
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;">
            <div style="font-size:0.6rem;font-weight:700;color:{color};">{val}</div>
            <div style="width:100%;height:{pct}px;background:{color};border-radius:3px 3px 0 0;
            min-height:4px;transition:height 0.5s;"></div>
            <div style="font-size:0.6rem;color:#8B949E;">{label}</div>
        </div>"""
    forecast_html += '</div>'

    st.markdown(forecast_html, unsafe_allow_html=True)

    # Trend summary
    trend_up = demand[-1] > demand[0]
    trend_pct = round((demand[-1] - demand[0]) / demand[0] * 100, 1)
    trend_color = "#EF4444" if trend_up else "#22C55E"
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
    padding:12px 16px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:0.72rem;color:#8B949E;text-transform:uppercase;
                letter-spacing:0.05em;">7-Day Trend</div>
                <div style="font-size:1.2rem;font-weight:800;color:{trend_color};">
                    {'↑' if trend_up else '↓'} {abs(trend_pct)}% {'increase' if trend_up else 'decrease'}
                </div>
                <div style="font-size:0.75rem;color:#8B949E;">
                    {demand[0]}/day → {demand[-1]}/day admissions
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.72rem;color:#8B949E;">Recommendation</div>
                <div style="font-size:0.8rem;font-weight:600;color:{trend_color};">
                    {'Pre-position staff now' if trend_up else 'Standard resourcing'}
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # Ward risk comparison
    st.markdown("### 📊 Ward Risk Comparison")
    st.caption("Current XGBoost bottleneck probabilities")

    for ward, risk in sorted(st.session_state.ward_risks.items(),
                              key=lambda x: x[1], reverse=True):
        resolved = ward in st.session_state.resolved
        color = "#22C55E" if resolved else ("#EF4444" if risk > 0.7 else "#F59E0B" if risk > 0.4 else "#38BDF8")
        taken = ward in st.session_state.actions_taken

        # Show risk change indicator
        base = WARDS[ward]["base_risk"]
        change = risk - base
        change_str = f"{'↑' if change > 0.01 else '↓' if change < -0.01 else '→'} {abs(change):.0%}"
        change_color = "#EF4444" if change > 0.01 else "#22C55E" if change < -0.01 else "#8B949E"

        st.markdown(f"""
        <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
                <div style="font-size:0.82rem;font-weight:600;color:#E6EDF3;">{ward}</div>
                <div style="display:flex;gap:8px;align-items:center;">
                    <span style="font-size:0.7rem;color:{change_color};">{change_str}</span>
                    <span style="font-size:0.9rem;font-weight:800;color:{color};">{risk:.0%}</span>
                </div>
            </div>
            <div class="risk-bar-bg">
                <div class="risk-bar-fill" style="width:{int(risk*100)}%;background:{color};
                transition:width 0.5s ease;"></div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # What if scenario
    st.markdown("### 🔮 What-If Scenario")
    st.caption("Adjust a ward risk to see priority list update")
    scenario_ward = st.selectbox("Select ward", list(WARDS.keys()))
    new_val = st.slider(
        f"Set {scenario_ward} bottleneck risk",
        0.0, 1.0,
        float(st.session_state.ward_risks[scenario_ward]),
        0.01
    )
    if st.button(f"Apply — Set {scenario_ward} to {new_val:.0%}"):
        old_val = st.session_state.ward_risks[scenario_ward]
        st.session_state.ward_risks[scenario_ward] = new_val
        add_event(
            f"What-if: {scenario_ward} risk manually set {old_val:.0%} → {new_val:.0%}",
            "warning" if new_val > old_val else "success"
        )
        if scenario_ward in st.session_state.resolved and new_val > 0.3:
            st.session_state.resolved.discard(scenario_ward)
        st.rerun()

# ── RIGHT: Live event feed ────────────────────────────────────────────
with right_col:
    st.markdown("### 📡 Live Event Feed")
    st.caption(f"{len(st.session_state.events)} events")

    if not st.session_state.events:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:20px;text-align:center;color:#8B949E;font-size:0.8rem;">
            Run a cycle to see live events
        </div>""", unsafe_allow_html=True)
    else:
        for event in reversed(st.session_state.events[-20:]):
            st.markdown(f"""
            <div class="event-item {event['type']}">
                <span class="event-time">{event['time']}</span><br>
                <span class="event-text">{event['text']}</span>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # CLINICIAN REVIEW reminder
    st.markdown("""
    <div style="background:#2D1A00;border:1px solid #F59E0B;border-radius:8px;
    padding:10px 12px;font-size:0.75rem;color:#FCD34D;font-weight:600;">
        ⚠️ All priority recommendations require CLINICIAN REVIEW before any resource reallocation
    </div>""", unsafe_allow_html=True)

    st.divider()

    # Session summary
    if st.session_state.actions_taken:
        st.markdown("**✅ Actions taken this session**")
        for ward, t in st.session_state.actions_taken.items():
            st.markdown(f"""
            <div style="font-size:0.75rem;color:#86EFAC;padding:3px 0;">
                ✅ {ward} — {t}
            </div>""", unsafe_allow_html=True)

# ── Chatbot ───────────────────────────────────────────────────────────
st.divider()
context_lines = []
for ward, risk in sorted(st.session_state.ward_risks.items(), key=lambda x: x[1], reverse=True):
    status = "resolved" if ward in st.session_state.resolved else ("action taken" if ward in st.session_state.actions_taken else "awaiting action")
    context_lines.append(f"- {ward}: {risk:.0%} bottleneck risk, {status}")
live_context = (
    f"Workflow cycle {st.session_state.cycle}.\n"
    + "\n".join(context_lines)
)
render_chatbot("Workflow Agent", live_context, key_prefix="workflow_agent")

# ── Auto-run ──────────────────────────────────────────────────────────
if st.session_state.auto_running:
    delay = {"Slow (30s)": 30, "Fast (10s)": 10, "Instant": 2}.get(speed, 10)
    time.sleep(delay)
    run_workflow_cycle()
    st.rerun()

# ── Footer ────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:6px 0;">
    NHS AI Platform — Workflow Agent Simulation · LD7326 · W25041744 · Northumbria University ·
    All ward data fictional · XGBoost AUC=0.8542 · LSTM MAPE=7.26% · DCB0129/DCB0160 compliant
</div>
""", unsafe_allow_html=True)