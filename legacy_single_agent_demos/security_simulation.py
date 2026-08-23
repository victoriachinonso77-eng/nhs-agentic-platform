"""
NHS AI Platform — Security Agent Live Simulation
Shows access monitoring, anomaly detection, audit trail
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run security_simulation.py
"""

import streamlit as st
import time
import datetime
import random
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Security Agent",
    page_icon="🔒",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }
#MainMenu, footer { visibility: hidden; }

.access-event {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;
    font-size: 0.78rem; animation: fadeIn 0.3s ease;
}
.access-normal  { background: #161B22; border: 1px solid #30363D; }
.access-anomaly { background: #2D0A0A; border: 1px solid #EF4444; animation: pulse-red 1.5s infinite; }
.access-flagged { background: #2D1A00; border: 1px solid #F59E0B; }

.anomaly-card {
    background: #2D0A0A; border: 2px solid #EF4444;
    border-radius: 10px; padding: 16px; margin-bottom: 10px;
    animation: pulse-red 2s infinite;
}
.anomaly-title { font-size: 0.95rem; font-weight: 800; color: #FCA5A5; margin-bottom: 6px; }
.anomaly-detail { font-size: 0.8rem; color: #FCA5A5; line-height: 1.6; }

.integrity-check {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;
    background: #161B22; border: 1px solid #30363D;
    font-size: 0.78rem;
}
.integrity-ok     { border-color: #22C55E; }
.integrity-failed { border-color: #EF4444; background: #2D0A0A; }

.threat-gauge {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 12px;
}

[data-testid="metric-container"] {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 12px !important;
}
[data-testid="metric-container"] label { color: #8B949E !important; font-size: 0.7rem !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.4rem !important; font-weight: 700 !important; }

.stButton > button {
    background: #1F6FEB !important; color: #FFF !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
}

@keyframes fadeIn   { from { opacity: 0; } to { opacity: 1; } }
@keyframes pulse-red { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.3); } 50% { box-shadow: 0 0 0 6px rgba(239,68,68,0); } }
@keyframes pulse     { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.pulse { animation: pulse 1.5s infinite; }
</style>
""", unsafe_allow_html=True)

# ── Access event templates ────────────────────────────────────────────
NORMAL_EVENTS = [
    ("Dr. Mensah",       "Read",   "Patient record — James Okafor",         "Cardiology ward round"),
    ("Sister Clarke",    "Write",  "Nursing note — Ward A, Bed 14",         "Routine shift update"),
    ("Staff Nurse Patel","Read",   "Medication chart — Priya Krishnamurthy","Pre-administration check"),
    ("Radiographer",     "Read",   "Imaging request — Echo booking",        "Procedure scheduling"),
    ("Pharmacist",       "Update", "TTO list — Ward C",                     "Discharge preparation"),
    ("Dr. Osei",         "Read",   "Patient record — Priya Krishnamurthy",  "Respiratory review"),
    ("Admin — Ward B",   "Read",   "Bed state report",                      "Board round preparation"),
    ("Sister Adeyemi",   "Write",  "Nursing note — Robert Adeniran",        "Post-op observations"),
    ("Bed Manager",      "Read",   "Capacity dashboard",                    "Afternoon board round"),
    ("Mr. Patterson",    "Read",   "Orthopaedic referral — Robert Adeniran","Pre-op assessment"),
    ("Lab Technician",   "Write",  "INR result — Robert Adeniran",          "Result upload"),
    ("IT Support",       "Read",   "System logs — terminal 3",              "Fault diagnosis"),
]

ANOMALY_EVENTS = [
    {
        "user":     "Unknown — IP 10.42.17.83",
        "action":   "Read",
        "target":   "ALL patient records — bulk download attempt",
        "context":  "Unrecognised IP address. No active session. Outside working hours.",
        "severity": "CRITICAL",
        "threat":   "Possible data exfiltration attempt. 847 records at risk.",
        "action_required": "Immediately block IP 10.42.17.83. Notify IT Security. Review logs.",
    },
    {
        "user":     "Former employee — Jane Smith (account deactivated 01/03/2026)",
        "action":   "Login attempt",
        "target":   "EPR System",
        "context":  "Account marked inactive. 14 failed login attempts in 3 minutes.",
        "severity": "HIGH",
        "threat":   "Possible credential misuse by former staff member.",
        "action_required": "Confirm account deactivated. Report to HR and IT Security.",
    },
    {
        "user":     "Dr. Ahmed (GP)",
        "action":   "Read",
        "target":   "Patient records outside registered patient list",
        "context":  "GP accessing records for patients not registered at their practice.",
        "severity": "MEDIUM",
        "threat":   "Possible inappropriate access. May be legitimate cross-referral.",
        "action_required": "Contact GP practice to verify clinical justification for access.",
    },
]

INTEGRITY_CHECKS = [
    ("AES-256 encryption — all data transfers",     True),
    ("Database integrity — no corruption detected",  True),
    ("Audit log completeness — all sessions logged", True),
    ("User authentication — MFA active",             True),
    ("Access control — role-based permissions",      True),
    ("Data backup — last backup 02:00 today",        True),
    ("Network firewall — all rules active",          True),
    ("Session timeout — enforced at 15 minutes",     True),
    ("SQL injection protection — active",            True),
    ("DCB0129 clinical safety checks",               True),
    ("DCB0160 deployment safety checks",             True),
    ("GDPR data minimisation compliance",            True),
]

# ── Session state ─────────────────────────────────────────────────────
if "sec_events"     not in st.session_state: st.session_state.sec_events = []
if "sec_anomalies"  not in st.session_state: st.session_state.sec_anomalies = []
if "sec_resolved"   not in st.session_state: st.session_state.sec_resolved = set()
if "sec_start"      not in st.session_state: st.session_state.sec_start = datetime.datetime.now()
if "auto_monitor"   not in st.session_state: st.session_state.auto_monitor = False
if "total_monitored" not in st.session_state: st.session_state.total_monitored = 0

def add_sec_event(event_type="normal"):
    if event_type == "normal":
        ev = random.choice(NORMAL_EVENTS)
        st.session_state.sec_events.append({
            "time":    datetime.datetime.now().strftime("%H:%M:%S"),
            "user":    ev[0],
            "action":  ev[1],
            "target":  ev[2],
            "context": ev[3],
            "type":    "normal",
        })
        st.session_state.total_monitored += 1
    elif event_type == "anomaly":
        used = {a["user"] for a in st.session_state.sec_anomalies}
        available = [a for a in ANOMALY_EVENTS if a["user"] not in used]
        if not available:
            return
        anomaly = random.choice(available)
        st.session_state.sec_anomalies.append({
            **anomaly,
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "resolved": False,
        })
        st.session_state.sec_events.append({
            "time":    datetime.datetime.now().strftime("%H:%M:%S"),
            "user":    anomaly["user"],
            "action":  anomaly["action"],
            "target":  anomaly["target"],
            "context": "⚠️ ANOMALY DETECTED",
            "type":    "anomaly",
        })
        st.session_state.total_monitored += 1

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            🔒 Security Agent — Live Simulation
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            Continuous access monitoring · Anomaly detection · DCB0129/DCB0160 compliance
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">
        Royal London Hospital · IT Security Dashboard<br>
        LD7326 · W25041744 · Northumbria University
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#1A1A0A;border:1px solid #F59E0B;border-radius:6px;
padding:8px 14px;margin-bottom:12px;font-size:0.73rem;color:#D4A520;">
    ⚖️ <b>Research Simulation:</b> All access events and users are fictional.
    No real NHS systems or user data accessed. GDPR · DCB0129/DCB0160 · W25041744
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("📊 Add Normal Access Event"):
        for _ in range(random.randint(3, 6)):
            add_sec_event("normal")
        st.rerun()
with c2:
    if st.button("🚨 Inject Anomaly"):
        add_sec_event("anomaly")
        st.rerun()
with c3:
    auto = st.toggle("🔄 Auto-monitor", value=st.session_state.auto_monitor)
    st.session_state.auto_monitor = auto
with c4:
    if st.button("🔄 Reset"):
        for key in ["sec_events","sec_anomalies","sec_resolved","sec_start","total_monitored"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

st.divider()

# ── Metrics ───────────────────────────────────────────────────────────
n_anomalies  = len(st.session_state.sec_anomalies)
n_resolved   = sum(1 for a in st.session_state.sec_anomalies if a.get("resolved"))
n_unresolved = n_anomalies - n_resolved
threat_level = "HIGH" if n_unresolved > 1 else "MEDIUM" if n_unresolved == 1 else "LOW"
threat_color = {"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#22C55E"}[threat_level]

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Events Monitored",    str(st.session_state.total_monitored))
m2.metric("Anomalies Detected",  str(n_anomalies))
m3.metric("Resolved",            str(n_resolved))
m4.metric("Unresolved",          str(n_unresolved))
m5.metric("Integrity Checks",    f"{len(INTEGRITY_CHECKS)}/12", "All passed")
m6.metric("Threat Level",        threat_level)

st.divider()

# ── Layout ────────────────────────────────────────────────────────────
left_col, mid_col, right_col = st.columns([2, 1, 1])

# ── LEFT: Access event feed ───────────────────────────────────────────
with left_col:
    st.markdown("### 📡 Live Access Event Monitor")
    st.caption("Every system access logged in real time")

    # Threat level display
    st.markdown(f"""
    <div class="threat-gauge" style="border-color:{threat_color};">
        <div style="font-size:2rem;font-weight:900;color:{threat_color};">
            {threat_level}
        </div>
        <div style="font-size:0.72rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.1em;">
            Current Threat Level
        </div>
        <div style="font-size:0.78rem;color:{threat_color};margin-top:4px;font-weight:600;">
            {'🚨 ' + str(n_unresolved) + ' unresolved anomalies' if n_unresolved > 0 else '✅ No active threats'}
        </div>
    </div>""", unsafe_allow_html=True)

    # Access events
    if not st.session_state.sec_events:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:30px;text-align:center;color:#8B949E;">
            <div style="font-size:1.5rem;margin-bottom:6px;">🔒</div>
            Add normal events or inject anomaly to see monitoring in action
        </div>""", unsafe_allow_html=True)
    else:
        for event in reversed(st.session_state.sec_events[-20:]):
            css = {"normal": "access-normal", "anomaly": "access-anomaly", "flagged": "access-flagged"}.get(event["type"], "access-normal")
            icon = {"normal": "✅", "anomaly": "🚨", "flagged": "⚠️"}.get(event["type"], "✅")
            color = {"normal": "#22C55E", "anomaly": "#EF4444", "flagged": "#F59E0B"}.get(event["type"], "#22C55E")

            st.markdown(f"""
            <div class="access-event {css}">
                <span style="font-size:1rem;">{icon}</span>
                <div style="flex:1;">
                    <div style="font-weight:700;color:{color};">{event['user']}</div>
                    <div style="color:#8B949E;">{event['action']} — {event['target']}</div>
                    <div style="color:#6E7681;font-size:0.7rem;">{event['time']} · {event['context']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

# ── MIDDLE: Anomalies ─────────────────────────────────────────────────
with mid_col:
    st.markdown("### 🚨 Anomalies Detected")
    st.caption("Flagged for immediate investigation")

    if not st.session_state.sec_anomalies:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:20px;text-align:center;color:#8B949E;font-size:0.8rem;">
            No anomalies detected
        </div>""", unsafe_allow_html=True)
    else:
        for i, anomaly in enumerate(st.session_state.sec_anomalies):
            is_resolved = anomaly.get("resolved", False)
            sev_color = {"CRITICAL": "#EF4444", "HIGH": "#F59E0B", "MEDIUM": "#F59E0B"}.get(anomaly["severity"], "#EF4444")

            st.markdown(f"""
            <div class="anomaly-card" style="{'opacity:0.5;' if is_resolved else ''}border-color:{sev_color};">
                <div class="anomaly-title" style="color:{sev_color};">
                    {'✅ RESOLVED' if is_resolved else f'🚨 {anomaly["severity"]} ANOMALY'}
                </div>
                <div class="anomaly-detail" style="color:{sev_color};">
                    <b>Time:</b> {anomaly['time']}<br>
                    <b>User:</b> {anomaly['user']}<br>
                    <b>Action:</b> {anomaly['action']}<br>
                    <b>Target:</b> {anomaly['target']}<br>
                    <b>Context:</b> {anomaly['context']}<br>
                    <b>Threat:</b> {anomaly['threat']}<br>
                    <b>Required:</b> {anomaly['action_required']}
                </div>
            </div>""", unsafe_allow_html=True)

            if not is_resolved:
                if st.button(f"✅ Resolve — {anomaly['severity']}", key=f"resolve_anomaly_{i}"):
                    st.session_state.sec_anomalies[i]["resolved"] = True
                    st.rerun()

    st.divider()

    # Integrity checks
    st.markdown("### ✅ Integrity Checks")
    st.caption(f"{len(INTEGRITY_CHECKS)}/12 passed")

    for check, passed in INTEGRITY_CHECKS:
        css = "integrity-ok" if passed else "integrity-failed"
        icon = "✅" if passed else "❌"
        color = "#86EFAC" if passed else "#FCA5A5"
        st.markdown(f"""
        <div class="integrity-check {css}">
            <span style="font-size:0.75rem;color:{color};">{check}</span>
            <span>{icon}</span>
        </div>""", unsafe_allow_html=True)

# ── RIGHT: Governance + audit ─────────────────────────────────────────
with right_col:
    st.markdown("### 🔒 Governance")

    standards = [
        ("DCB0129", "Clinical risk management — manufacturer", "✅"),
        ("DCB0160", "Clinical risk management — deployer",     "✅"),
        ("GDPR Art.5", "Data minimisation principle",          "✅"),
        ("GDPR Art.32", "Security of processing",              "✅"),
        ("NHS DSPT",  "Data Security Protection Toolkit",      "✅"),
        ("Cyber Essentials+", "Government security standard",  "✅"),
        ("AES-256",   "Encryption — all data transfers",       "✅"),
        ("ISO 27001", "Information security management",       "✅"),
    ]

    for std, desc, status in standards:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
        padding:6px 10px;background:#161B22;border-radius:6px;margin-bottom:4px;">
            <div>
                <div style="font-size:0.75rem;font-weight:700;color:#E6EDF3;">{std}</div>
                <div style="font-size:0.65rem;color:#8B949E;">{desc}</div>
            </div>
            <span style="color:#22C55E;font-size:0.85rem;">{status}</span>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 Audit Trail")
    st.caption("Complete session log — GDPR compliant")

    elapsed = (datetime.datetime.now() - st.session_state.sec_start).total_seconds()
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px;">
        <div style="font-size:0.75rem;color:#8B949E;line-height:1.8;">
            <b style="color:#E6EDF3;">Session started:</b> {st.session_state.sec_start.strftime('%H:%M:%S')}<br>
            <b style="color:#E6EDF3;">Duration:</b> {int(elapsed/60)}m {int(elapsed%60)}s<br>
            <b style="color:#E6EDF3;">Events logged:</b> {st.session_state.total_monitored}<br>
            <b style="color:#E6EDF3;">Anomalies:</b> {n_anomalies}<br>
            <b style="color:#E6EDF3;">Resolved:</b> {n_resolved}<br>
            <b style="color:#E6EDF3;">Encryption:</b> AES-256 active<br>
            <b style="color:#E6EDF3;">Log integrity:</b> ✅ Verified<br>
            <b style="color:#E6EDF3;">Retention:</b> 7 years (NHS policy)
        </div>
    </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<div style="background:#2D0A0A;border:1px solid #EF4444;border-radius:8px;'
        'padding:10px;font-size:0.75rem;color:#FCA5A5;font-weight:600;">'
        '🔒 Security Agent runs continuously in background — no clinical staff action required '
        'unless anomaly detected. All CRITICAL and HIGH anomalies require CLINICIAN or '
        'Information Governance sign-off before access is restored — the agent flags and '
        'contains, it does not unilaterally resolve incidents involving patient data.'
        '</div>',
        unsafe_allow_html=True
    )

# ── Auto-monitor ──────────────────────────────────────────────────────
st.divider()
n_unresolved_ctx = sum(1 for a in st.session_state.sec_anomalies if not a.get("resolved"))
context_lines = [
    f"- Total access events monitored: {st.session_state.total_monitored}",
    f"- Anomalies detected: {len(st.session_state.sec_anomalies)}",
    f"- Unresolved anomalies: {n_unresolved_ctx}",
    f"- Threat level: {threat_level}",
]
for a in st.session_state.sec_anomalies:
    status = "resolved" if a.get("resolved") else "UNRESOLVED"
    context_lines.append(f"- {a['severity']} anomaly: {a['user']} — {a['threat']} ({status})")
live_context = "\n".join(context_lines)
render_chatbot("Security Agent", live_context, key_prefix="security_agent")

st.divider()
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:6px 0;">
    NHS AI Platform — Security Agent · LD7326 · W25041744 · Northumbria University ·
    All events fictional · No real NHS systems · DCB0129/DCB0160/GDPR compliant
</div>
""", unsafe_allow_html=True)

if st.session_state.auto_monitor:
    time.sleep(3)
    for _ in range(random.randint(2, 4)):
        add_sec_event("normal")
    if random.random() < 0.05:  # 5% chance of anomaly
        add_sec_event("anomaly")
    st.rerun()