"""
NHS AI Platform — Handover Agent Live Simulation
Simulates the full handover compliance check journey
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run handover_simulation.py
"""

import streamlit as st
import time
import datetime
import os
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Handover Agent Simulation",
    page_icon="🤝",
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

.timeline-container { padding-left: 28px; border-left: 2px solid #30363D; margin: 8px 0; }
.timeline-event {
    position: relative; margin-bottom: 14px;
    padding: 12px 16px; border-radius: 8px;
    background: #161B22; border: 1px solid #30363D;
    animation: fadeIn 0.5s ease;
}
.timeline-event::before {
    content: ''; position: absolute;
    left: -37px; top: 14px;
    width: 10px; height: 10px;
    border-radius: 50%; background: #38BDF8;
    border: 2px solid #0D1117;
}
.timeline-event.critical::before { background: #EF4444; }
.timeline-event.success::before  { background: #22C55E; }
.timeline-event.warning::before  { background: #F59E0B; }
.timeline-event.ai::before       { background: #A855F7; }

.event-time { font-size: 0.68rem; color: #8B949E; font-weight: 600; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.05em; }
.event-title { font-size: 0.88rem; font-weight: 700; color: #E6EDF3; margin-bottom: 3px; }
.event-detail { font-size: 0.78rem; color: #8B949E; line-height: 1.5; }

.source-badge {
    display: inline-block; font-size: 0.62rem; font-weight: 700;
    padding: 2px 6px; border-radius: 4px; margin-top: 4px;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.src-epr    { background: #1C2333; color: #58A6FF; border: 1px solid #1F6FEB; }
.src-ai     { background: #2D1A4A; color: #C084FC; border: 1px solid #A855F7; }
.src-nurse  { background: #0A2D1A; color: #86EFAC; border: 1px solid #22C55E; }
.src-doctor { background: #2D1A00; color: #FCD34D; border: 1px solid #F59E0B; }
.src-system { background: #1A1A2D; color: #93C5FD; border: 1px solid #38BDF8; }

.patient-card {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 12px; padding: 14px; margin-bottom: 10px;
    cursor: pointer; transition: border-color 0.2s;
}
.patient-card.selected  { border-color: #38BDF8; border-left: 4px solid #38BDF8; }
.patient-card.complete  { border-color: #22C55E; border-left: 4px solid #22C55E; }
.patient-card.critical  { border-color: #EF4444; border-left: 4px solid #EF4444; }
.patient-card.moderate  { border-color: #F59E0B; border-left: 4px solid #F59E0B; }

.sbar-check {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 16px; margin-top: 12px;
}
.sbar-element {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
}
.sbar-complete { background: #0A2D1A; border: 1px solid #22C55E; }
.sbar-missing  { background: #2D0A0A; border: 1px solid #EF4444; animation: pulse-red 2s infinite; }

@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.3); }
    50%       { box-shadow: 0 0 0 6px rgba(239,68,68,0); }
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

.handover-card {
    background: #0D1117; border-radius: 10px; padding: 16px; margin-top: 10px;
}
.priority-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.78rem; font-weight: 800; margin-bottom: 8px;
}
.p1 { background: #2D0A0A; color: #FCA5A5; border: 1px solid #EF4444; }
.p2 { background: #2D1A00; color: #FCD34D; border: 1px solid #F59E0B; }
.p3 { background: #0A2D1A; color: #86EFAC; border: 1px solid #22C55E; }

.progress-bar-bg {
    background: #21262D; border-radius: 4px; height: 8px; margin: 6px 0;
}
.progress-bar-fill {
    height: 8px; border-radius: 4px; transition: width 0.5s ease;
}

[data-testid="metric-container"] {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 12px !important;
}
[data-testid="metric-container"] label { color: #8B949E !important; font-size: 0.72rem !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.5rem !important; font-weight: 700 !important; }

.stButton > button {
    background: #1F6FEB !important; color: #FFFFFF !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
}
.stButton > button:hover { background: #388BFD !important; }
</style>
""", unsafe_allow_html=True)

# ── Patient data ──────────────────────────────────────────────────────
PATIENTS = [
    {
        "name":          "James Okafor",
        "age":           67, "sex": "M",
        "nhs":           "NHS-485-261-3847",
        "ward":          "Emergency Assessment Unit, Bed 14",
        "admission":     "EW EMER.",
        "diagnosis":     "Acute NSTEMI — chest pain, ST changes, elevated troponin",
        "los_hours":     18.4,
        "risk_score":    0.87,
        "priority":      1,
        "consultant":    "Dr. Mensah (Cardiology)",
        "nurse":         "Sister Clarke",
        "sbar": {
            "situation":     "Patient James Okafor, 67y M, admitted 18.4h ago via EW EMER. with acute chest pain. Diagnosis: NSTEMI confirmed. Currently haemodynamically stable but under cardiac monitoring.",
            "background":    "PMH: Type 2 diabetes, hypertension, previous MI 2019. Medications: Metformin, Amlodipine, Aspirin. Troponin peak 2.4 ng/mL. ECG: ST changes in II, III, aVF. Cardiology review completed.",
            "assessment":    None,  # MISSING
            "recommendation": None,  # MISSING
        },
        "assessment_text": "Patient currently stable. Troponin trending down. Echo booked for tomorrow. Risk of re-infarction remains elevated. Continuous cardiac monitoring ongoing. IV access patent.",
        "recommendation_text": "1. Continue cardiac monitoring overnight — alert SpR if any chest pain or ECG changes.\n2. Cardiology ward round at 08:00 — escalate if deterioration overnight.\n3. NPO from midnight — cath lab provisionally booked for 09:00 tomorrow.",
    },
    {
        "name":          "Margaret Thornton",
        "age":           45, "sex": "F",
        "nhs":           "NHS-712-394-5521",
        "ward":          "Surgical Assessment Unit, Bed 7",
        "admission":     "URGENT",
        "diagnosis":     "Acute appendicitis — CT confirmed, surgery planned",
        "los_hours":     6.2,
        "risk_score":    0.43,
        "priority":      3,
        "consultant":    "Mr. Okonkwo (General Surgery)",
        "nurse":         "Staff Nurse Davies",
        "sbar": {
            "situation":     "Patient Margaret Thornton, 45y F, admitted 6.2h ago via GP urgent referral with acute appendicitis CT confirmed.",
            "background":    None,  # MISSING
            "assessment":    "WBC 14.2, CRP 68. CT confirms acute appendicitis — no perforation. Patient currently nil by mouth. IV antibiotics commenced.",
            "recommendation": "1. Theatre booked for 22:00 tonight — consent signed.\n2. IV Co-amoxiclav 1.2g TDS — next dose at 21:00.\n3. Anaesthetic review completed — ASA grade 1.",
        },
        "background_text": "No significant PMH. No regular medications. No known drug allergies. Last ate at 13:00. Next of kin: husband (Michael Thornton) — contacted and aware.",
    },
    {
        "name":          "Robert Adeniran",
        "age":           78, "sex": "M",
        "nhs":           "NHS-334-817-9204",
        "ward":          "Orthopaedic Ward, Bed 3",
        "admission":     "DIRECT EMER.",
        "diagnosis":     "Neck of femur fracture — surgery pending, supratherapeutic INR",
        "los_hours":     11.6,
        "risk_score":    0.91,
        "priority":      1,
        "consultant":    "Mr. Patterson (Orthopaedics)",
        "nurse":         "Sister Adeyemi",
        "sbar": {
            "situation":     "Patient Robert Adeniran, 78y M, admitted 11.6h ago following fall at home. X-ray confirmed right neck of femur fracture. Surgery delayed pending INR reversal.",
            "background":    "PMH: Osteoporosis, atrial fibrillation, CKD stage 3. On Warfarin — INR 3.8 on admission (supratherapeutic). Haematology consulted. Bisoprolol held perioperatively.",
            "assessment":    None,  # MISSING
            "recommendation": None,  # MISSING
        },
        "assessment_text": "INR now 2.1 following Vitamin K 5mg IV and FFP 2 units. Repeat INR due at 22:00. Orthopaedics plan to proceed to theatre when INR <1.5. Patient in pain — morphine PCA in situ. Pressure area care ongoing.",
        "recommendation_text": "1. Repeat INR at 22:00 — if <1.5 alert on-call orthopaedic SpR to book emergency theatre.\n2. Continue morphine PCA — review pain score hourly.\n3. Pressure area care 2-hourly — high falls risk, bed rails up.",
    },
    {
        "name":          "Priya Krishnamurthy",
        "age":           34, "sex": "F",
        "nhs":           "NHS-591-042-7713",
        "ward":          "Respiratory Ward, Bed 11",
        "admission":     "EW EMER.",
        "diagnosis":     "Severe asthma exacerbation — responding to treatment",
        "los_hours":     8.3,
        "risk_score":    0.72,
        "priority":      2,
        "consultant":    "Dr. Osei (Respiratory Medicine)",
        "nurse":         "Staff Nurse Patel",
        "sbar": {
            "situation":     "Patient Priya Krishnamurthy, 34y F, admitted 8.3h ago with severe asthma exacerbation. PEFR 38% predicted on admission — now 62% following treatment.",
            "background":    "PMH: Asthma since childhood, eczema. Regular inhalers: Fostair, Salbutamol PRN, Montelukast. Trigger: possible viral URTI. No previous ITU admissions.",
            "assessment":    "Improving — PEFR 62% at last check. O2 sats 97% on 2L nasal specs. ABG normalising. Still requiring 4-hourly nebulisers. Not yet safe for discharge.",
            "recommendation": None,  # MISSING
        },
        "recommendation_text": "1. Continue 4-hourly salbutamol nebulisers — step down to inhaler when PEFR >75%.\n2. Prednisolone 40mg OD — continue for 5 days total.\n3. Respiratory SpR to review at 08:00 — discharge if PEFR >75% and stable.",
    },
]

# ── Session state ─────────────────────────────────────────────────────
if "active_patient"    not in st.session_state: st.session_state.active_patient = None
if "events_running"    not in st.session_state: st.session_state.events_running = {}
if "completed_sbar"    not in st.session_state: st.session_state.completed_sbar = {}
if "handover_done"     not in st.session_state: st.session_state.handover_done = set()
if "sim_started"       not in st.session_state: st.session_state.sim_started = False
if "events_shown"      not in st.session_state: st.session_state.events_shown = {}

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            🤝 Handover Agent — Live Simulation
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            Simulating: Shift end approaching → SBAR compliance check → Clinician completes → Safe handover
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">
        Royal London Hospital · 19:00 shift handover<br>
        LD7326 · W25041744 · Northumbria University
    </div>
</div>
""", unsafe_allow_html=True)

# ── Disclaimer ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1A1A0A;border:1.5px solid #F59E0B;border-radius:8px;
padding:10px 16px;margin-bottom:12px;font-size:0.75rem;color:#D4A520;">
    ⚖️ <b>Research Simulation:</b> All patient names, NHS numbers, and clinical details
    are entirely fictional and generated for research demonstration only.
    No real patient data is used. GDPR · NHS Act 2006 · DCB0129/DCB0160 compliant.
</div>
""", unsafe_allow_html=True)

# ── Shift end countdown ───────────────────────────────────────────────
now = datetime.datetime.now()
shift_end = now.replace(hour=19, minute=0, second=0) if now.hour < 19 else now.replace(hour=7, minute=0, second=0) + datetime.timedelta(days=1)
mins_to_end = max(0, int((shift_end - now).total_seconds() / 60))

# Simulate time — starts at 18:05 and counts up in real time
if "sim_start_real" not in st.session_state:
    st.session_state.sim_start_real = datetime.datetime.now()

elapsed_real = (datetime.datetime.now() - st.session_state.sim_start_real).total_seconds()
# 1 real second = 30 simulated seconds (so 110 real seconds = 55 sim minutes)
sim_elapsed_mins = elapsed_real * 0.5
sim_start = datetime.datetime(2026, 7, 16, 18, 5, 0)
sim_now = sim_start + datetime.timedelta(minutes=sim_elapsed_mins)
sim_end  = datetime.datetime(2026, 7, 16, 19, 0, 0)
sim_mins_left = max(0, int((sim_end - sim_now).total_seconds() / 60))
sim_secs_left = max(0, int((sim_end - sim_now).total_seconds() % 60))

# Check for P1 patients still incomplete
p1_incomplete = [
    p for p in PATIENTS
    if p["priority"] == 1
    and p["name"] not in st.session_state.handover_done
    and any(v is None and k not in st.session_state.completed_sbar.get(p["name"], set())
            for k, v in p["sbar"].items())
]

if sim_mins_left <= 0:
    alert_color = "#EF4444"
    urgency = "HANDOVER TIME — All outstanding items must be completed NOW"
elif sim_mins_left <= 10:
    alert_color = "#EF4444"
    urgency = f"CRITICAL — {sim_mins_left}m {sim_secs_left}s remaining"
elif sim_mins_left <= 20:
    alert_color = "#F59E0B"
    urgency = f"URGENT — {sim_mins_left}m {sim_secs_left}s remaining"
else:
    alert_color = "#22C55E"
    urgency = f"{sim_mins_left}m {sim_secs_left}s remaining"

# P1 alert if incomplete and time running out
if p1_incomplete and sim_mins_left <= 30:
    p1_names = ", ".join([p["name"].split()[0] for p in p1_incomplete])
    st.markdown(f"""
    <div style="background:#2D0A0A;border:2px solid #EF4444;border-radius:8px;
    padding:12px 18px;margin-bottom:8px;animation:pulse-red 1.5s infinite;">
        <div style="font-size:0.9rem;font-weight:800;color:#FCA5A5;">
            🚨 P1 ALERT — {p1_names}: Handover incomplete with {sim_mins_left} minutes to shift end.
            Complete SBAR immediately.
        </div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#161B22;border:1.5px solid {alert_color};border-radius:8px;
padding:12px 18px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:0.85rem;font-weight:700;color:{alert_color};">
        🕐 Shift ends 19:00 — Handover Agent active · Simulated time: {sim_now.strftime("%H:%M:%S")}
    </div>
    <div style="font-size:1rem;font-weight:800;color:{alert_color};">
        ⏱ {urgency}
    </div>
</div>""", unsafe_allow_html=True)

# ── Summary metrics ───────────────────────────────────────────────────
total = len(PATIENTS)
done  = len(st.session_state.handover_done)
high_risk = sum(1 for p in PATIENTS if p['priority'] == 1)
sbar_issues = sum(
    1 for p in PATIENTS
    if any(v is None for v in p['sbar'].values())
    and p['name'] not in st.session_state.handover_done
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Patients on Ward", str(total))
m2.metric("Handovers Pending", str(total - done), f"{done} complete")
m3.metric("High Priority (P1)", str(high_risk), "Immediate action")
m4.metric("SBAR Incomplete", str(sbar_issues), "Need clinician input")
m5.metric("SBAR Compliance", f"{done}/{total}", f"{round(done/total*100)}%")

st.divider()

# ── Layout ────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown("### 🏥 Patient Handover List")
    st.caption("Ranked by XGBoost bottleneck risk — highest priority first")

    sorted_patients = sorted(PATIENTS, key=lambda x: x['risk_score'], reverse=True)

    for p in sorted_patients:
        sbar = p['sbar']
        missing = [k for k, v in sbar.items() if v is None]
        is_done = p['name'] in st.session_state.handover_done
        is_active = st.session_state.active_patient == p['name']

        # Card styling
        if is_done:
            card_class = "complete"
            status_text = "✅ Handover Complete"
            status_color = "#22C55E"
        elif p['priority'] == 1:
            card_class = "critical"
            status_text = f"🔴 P1 CRITICAL — {len(missing)} SBAR missing"
            status_color = "#EF4444"
        elif p['priority'] == 2:
            card_class = "moderate"
            status_text = f"🟡 P2 HIGH — {len(missing)} SBAR missing"
            status_color = "#F59E0B"
        else:
            card_class = "patient-card"
            status_text = f"🟢 P3 ROUTINE — {len(missing)} SBAR missing"
            status_color = "#22C55E"

        if is_active:
            card_class += " selected"

        st.markdown(f"""
        <div class="patient-card {card_class}">
            <div style="font-size:0.95rem;font-weight:800;color:#E6EDF3;">{p['name']}</div>
            <div style="font-size:0.75rem;color:#8B949E;margin:2px 0;">
                {p['age']}y {p['sex']} · {p['ward']}<br>
                {p['diagnosis'][:50]}...
            </div>
            <div style="font-size:0.75rem;font-weight:700;color:{status_color};margin-top:4px;">
                {status_text}
            </div>
            <div style="margin-top:6px;">
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="
                        width:{round((4-len(missing))/4*100)}%;
                        background:{'#22C55E' if is_done else status_color};">
                    </div>
                </div>
                <div style="font-size:0.68rem;color:#8B949E;">
                    SBAR: {4-len(missing)}/4 complete
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        if not is_done:
            if st.button(f"🔍 Check Handover — {p['name'].split()[0]}",
                         key=f"select_{p['name']}"):
                st.session_state.active_patient = p['name']
                st.rerun()

    # Overall compliance bar
    st.divider()
    compliance = round(done / total * 100)
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px 16px;">
        <div style="font-size:0.72rem;font-weight:700;color:#8B949E;
        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
            Overall SBAR Compliance
        </div>
        <div style="font-size:1.5rem;font-weight:800;
        color:{'#22C55E' if compliance==100 else '#F59E0B' if compliance>=50 else '#EF4444'};">
            {compliance}%
        </div>
        <div class="progress-bar-bg" style="margin-top:6px;">
            <div class="progress-bar-fill" style="
                width:{compliance}%;
                background:{'#22C55E' if compliance==100 else '#F59E0B' if compliance>=50 else '#EF4444'};">
            </div>
        </div>
        <div style="font-size:0.72rem;color:#8B949E;margin-top:4px;">
            Target: 100% before 19:00 handover
        </div>
    </div>""", unsafe_allow_html=True)

with right_col:
    if not st.session_state.active_patient:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:10px;
        padding:60px 40px;text-align:center;color:#8B949E;margin-top:20px;">
            <div style="font-size:2rem;margin-bottom:8px;">🤝</div>
            <div style="font-weight:700;font-size:1rem;margin-bottom:6px;color:#E6EDF3;">
                Handover Agent Ready
            </div>
            <div style="font-size:0.85rem;line-height:1.6;">
                Select a patient from the list to see their SBAR handover check.<br>
                Start with <b>Priority 1</b> patients — highest bottleneck risk.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Find active patient
        p = next((x for x in PATIENTS if x['name'] == st.session_state.active_patient), None)
        if p:
            sbar = p['sbar']
            missing = [k for k, v in sbar.items() if v is None]
            complete = [k for k, v in sbar.items() if v is not None]
            is_done = p['name'] in st.session_state.handover_done

            priority_class = {1: "p1", 2: "p2", 3: "p3"}.get(p['priority'], "p3")
            priority_label = {1: "P1 — CRITICAL", 2: "P2 — HIGH", 3: "P3 — ROUTINE"}.get(p['priority'])
            risk_color = {1: "#EF4444", 2: "#F59E0B", 3: "#22C55E"}.get(p['priority'])

            # ── Patient header ────────────────────────────────────────
            st.markdown(f"""
            <div style="background:#161B22;border:1.5px solid {risk_color};
            border-radius:10px;padding:16px 20px;margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div style="font-size:1.1rem;font-weight:800;color:#E6EDF3;">
                            {p['name']}
                        </div>
                        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
                            {p['age']}y {p['sex']} · {p['nhs']} · {p['ward']}
                        </div>
                        <div style="font-size:0.82rem;color:#C9D1D9;margin-top:4px;">
                            {p['diagnosis']}
                        </div>
                        <div style="font-size:0.75rem;color:#8B949E;margin-top:3px;">
                            Consultant: {p['consultant']} · Nurse: {p['nurse']}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span class="priority-badge {priority_class}">{priority_label}</span><br>
                        <div style="font-size:1.2rem;font-weight:800;color:{risk_color};margin-top:4px;">
                            {p['risk_score']:.0%}
                        </div>
                        <div style="font-size:0.7rem;color:#8B949E;">Bottleneck Risk</div>
                        <div style="font-size:0.72rem;color:#8B949E;margin-top:2px;">
                            LOS: {p['los_hours']}h on ward
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # ── Live event timeline ───────────────────────────────────
            st.markdown("#### 📡 Handover Agent — Live Check")

            events = [
                ("ai",      f"18:05", "Handover Agent activated",
                 f"1 hour before shift end. Checking SBAR compliance for {p['name']} ({p['risk_score']:.0%} bottleneck risk). Priority {p['priority']} assigned.", "src-ai"),
                ("default", f"18:05", "EPR handover record retrieved",
                 f"Patient record loaded: {p['nhs']}. LOS: {p['los_hours']}h. Ward: {p['ward']}.", "src-epr"),
                ("warning" if missing else "success", f"18:05", f"SBAR check: {len(complete)}/4 elements complete",
                 f"Complete: {', '.join([k.upper() for k in complete])}. "
                 f"{'Missing: ' + ', '.join([k.upper() for k in missing]) + ' — clinician input required.' if missing else 'All elements present — handover cleared.'}", "src-ai"),
            ]

            if missing:
                events.append(("critical", "18:06",
                    f"⚠️ Handover incomplete — cannot transfer patient safely",
                    f"Missing SBAR elements must be completed by outgoing clinician before 19:00. "
                    f"{'PRIORITY 1 — complete within 30 minutes.' if p['priority']==1 else 'Complete before shift end.'}", "src-ai"))
            else:
                events.append(("success", "18:06",
                    "✅ Handover cleared — safe to transfer",
                    "All SBAR elements documented. Night team notified. Patient safe to hand over.", "src-ai"))

            st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
            for ev_color, ev_time, ev_title, ev_detail, ev_src in events:
                st.markdown(f"""
                <div class="timeline-event {ev_color}">
                    <div class="event-time">{ev_time}</div>
                    <div class="event-title">{ev_title}</div>
                    <div class="event-detail">{ev_detail}</div>
                    <span class="source-badge {ev_src}">
                        {'AI' if 'ai' in ev_src else 'EPR' if 'epr' in ev_src else 'SYSTEM'}
                    </span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── SBAR check display ────────────────────────────────────
            st.markdown("#### 📋 SBAR Handover Document")

            # Track which missing elements have been completed in session
            completed_in_session = st.session_state.completed_sbar.get(p['name'], set())

            for element in ['situation', 'background', 'assessment', 'recommendation']:
                content = sbar[element]
                is_complete = content is not None or element in completed_in_session

                if is_complete:
                    # Get the actual content
                    if content:
                        display_content = content
                    else:
                        # Was completed during this session
                        display_content = {
                            'assessment':    p.get('assessment_text', ''),
                            'background':    p.get('background_text', ''),
                            'recommendation': p.get('recommendation_text', ''),
                        }.get(element, '')

                    st.markdown(f"""
                    <div class="sbar-element sbar-complete">
                        <div style="font-size:1rem;">✅</div>
                        <div style="flex:1;">
                            <div style="font-size:0.68rem;font-weight:800;color:#22C55E;
                            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:3px;">
                                {element}
                            </div>
                            <div style="font-size:0.82rem;color:#C9D1D9;line-height:1.5;
                            white-space:pre-line;">{display_content}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    # Missing — show fill-in area
                    st.markdown(f"""
                    <div class="sbar-element sbar-missing">
                        <div style="font-size:1rem;">❌</div>
                        <div style="flex:1;">
                            <div style="font-size:0.68rem;font-weight:800;color:#EF4444;
                            text-transform:uppercase;letter-spacing:0.1em;margin-bottom:3px;">
                                {element} — MISSING
                            </div>
                            <div style="font-size:0.78rem;color:#FCA5A5;">
                                This section must be completed before handover.
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    # Show the pre-filled text and a complete button
                    prefill_key = f"prefill_{p['name']}_{element}"
                    prefill_text = {
                        'assessment':    p.get('assessment_text', ''),
                        'background':    p.get('background_text', ''),
                        'recommendation': p.get('recommendation_text', ''),
                        'situation':     '',
                    }.get(element, '')

                    st.markdown(f"""
                    <div style="background:#1A0A0A;border:1px solid #30363D;border-radius:6px;
                    padding:10px 14px;margin:4px 0 8px 0;font-size:0.78rem;color:#8B949E;">
                        💡 <b>AI suggestion</b> — clinician to review and confirm:<br>
                        <span style="color:#C9D1D9;font-style:italic;line-height:1.6;">
                        {prefill_text}
                        </span>
                    </div>""", unsafe_allow_html=True)

                    # AI Draft button
                    use_ai_draft = os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "sk-proj-your-key-here"
                    ai_draft_key = f"{p['name']}_{element}"

                    if use_ai_draft:
                        if st.button(f"🤖 Generate AI Draft for {element.upper()}",
                                     key=f"ai_{p['name']}_{element}"):
                            from openai import OpenAI
                            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                            prompt = (
                                f"Write a specific NHS SBAR {element} section. "
                                f"Use exact clinical values. 2-3 sentences. Clinical language.\n\n"
                                f"Patient: {p['name']}, {p['age']}y {p['sex']}\n"
                                f"Diagnosis: {p['diagnosis']}\n"
                                f"Ward: {p['ward']}, LOS: {p['los_hours']}h\n"
                                f"Context: {prefill_text}"
                            )
                            resp = OpenAI(api_key=os.getenv("OPENAI_API_KEY")).chat.completions.create(
                                model="gpt-4o", max_tokens=150,
                                messages=[
                                    {"role": "system", "content": "NHS clinical documentation assistant. Be specific. Use exact data."},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            if "ai_drafts" not in st.session_state:
                                st.session_state.ai_drafts = {}
                            st.session_state.ai_drafts[ai_draft_key] = resp.choices[0].message.content.strip()
                            st.rerun()

                        if "ai_drafts" in st.session_state and ai_draft_key in st.session_state.ai_drafts:
                            ai_text = st.session_state.ai_drafts[ai_draft_key]
                            st.markdown(f"""
                            <div style="background:#2D1A4A;border:1px solid #A855F7;border-radius:6px;
                            padding:10px 14px;margin:4px 0;font-size:0.82rem;color:#C9D1D9;">
                                🤖 <b style="color:#C084FC;">AI-Generated (GPT-4o):</b><br>{ai_text}
                            </div>""", unsafe_allow_html=True)

                    if st.button(f"✅ Confirm {element.upper()} — Add to Handover",
                                 key=f"add_{p['name']}_{element}"):
                        if p['name'] not in st.session_state.completed_sbar:
                            st.session_state.completed_sbar[p['name']] = set()
                        st.session_state.completed_sbar[p['name']].add(element)
                        st.rerun()

            # ── Check if all elements now complete ────────────────────
            all_complete = all(
                sbar[k] is not None or k in st.session_state.completed_sbar.get(p['name'], set())
                for k in ['situation', 'background', 'assessment', 'recommendation']
            )

            st.divider()

            if all_complete and p['name'] not in st.session_state.handover_done:
                st.markdown("""
                <div style="background:#0A2D1A;border:1.5px solid #22C55E;border-radius:8px;
                padding:12px 16px;font-size:0.85rem;font-weight:700;color:#86EFAC;margin-bottom:10px;">
                    ✅ All SBAR elements complete — ready for handover
                </div>""", unsafe_allow_html=True)

                if st.button(f"🤝 Sign Off Handover — {p['name']}", type="primary"):
                    st.session_state.handover_done.add(p['name'])
                    st.session_state.active_patient = None
                    st.success(f"Handover signed off for {p['name']} — night team notified")
                    st.rerun()

            elif p['name'] in st.session_state.handover_done:
                st.markdown(f"""
                <div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:8px;
                padding:12px 16px;font-size:0.85rem;font-weight:700;color:#86EFAC;">
                    ✅ Handover complete and signed — {p['name']} safely handed to night team
                </div>""", unsafe_allow_html=True)

            else:
                remaining = [
                    k for k in ['situation','background','assessment','recommendation']
                    if sbar[k] is None and k not in st.session_state.completed_sbar.get(p['name'], set())
                ]
                st.markdown(f"""
                <div style="background:#2D0A0A;border:1px solid #EF4444;border-radius:8px;
                padding:12px 16px;font-size:0.85rem;font-weight:600;color:#FCA5A5;">
                    ⚠️ Cannot hand over — {len(remaining)} SBAR element(s) still missing:
                    {', '.join([r.upper() for r in remaining])}.
                    Complete above before signing off.
                </div>""", unsafe_allow_html=True)

            st.markdown("""
            <div style="font-size:0.72rem;color:#6E7681;margin-top:8px;">
                ⚠️ CLINICIAN REVIEW REQUIRED — AI suggestions must be confirmed by outgoing clinician
                before becoming part of the official handover record · DCB0129/DCB0160
            </div>""", unsafe_allow_html=True)

# ── Night team acceptance screen ─────────────────────────────────────
if len(st.session_state.handover_done) == len(PATIENTS):
    st.divider()
    st.markdown("""
    <div style="background:#0D1117;border:2px solid #22C55E;border-radius:12px;
    padding:20px;margin-bottom:16px;text-align:center;">
        <div style="font-size:1.3rem;font-weight:800;color:#86EFAC;margin-bottom:4px;">
            ✅ All 4 handovers complete — Ward cleared for night team
        </div>
        <div style="font-size:0.85rem;color:#86EFAC;">
            SBAR compliance: 100% · Day team can safely leave · Night team accepting patients
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("### 🌙 Night Team — Patient Acceptance")
    st.caption("Night team receiving and acknowledging each patient handover")

    if "night_accepted" not in st.session_state:
        st.session_state.night_accepted = set()

    for p in sorted(PATIENTS, key=lambda x: x['risk_score'], reverse=True):
        is_accepted = p['name'] in st.session_state.night_accepted
        risk_color = {1: "#EF4444", 2: "#F59E0B", 3: "#22C55E"}.get(p['priority'])

        with st.expander(
            f"{'✅' if is_accepted else '⏳'} {p['name']} — "
            f"{'ACCEPTED' if is_accepted else 'PENDING ACCEPTANCE'}",
            expanded=not is_accepted
        ):
            # Show complete SBAR for night team
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid {risk_color};
            border-radius:8px;padding:14px;margin-bottom:10px;">
                <div style="font-size:0.75rem;font-weight:700;color:{risk_color};
                text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">
                    Night Team Handover — {p['name']} · {p['ward']}
                </div>""", unsafe_allow_html=True)

            for element in ['situation', 'background', 'assessment', 'recommendation']:
                content = p['sbar'][element]
                if content is None:
                    content = {
                        'assessment':     p.get('assessment_text', ''),
                        'background':     p.get('background_text', ''),
                        'recommendation': p.get('recommendation_text', ''),
                    }.get(element, '')
                    # Check AI draft
                    ai_key = f"{p['name']}_{element}"
                    if "ai_drafts" in st.session_state and ai_key in st.session_state.ai_drafts:
                        content = st.session_state.ai_drafts[ai_key]

                if content:
                    st.markdown(f"""
                    <div style="margin-bottom:8px;">
                        <div style="font-size:0.65rem;font-weight:800;color:{risk_color};
                        text-transform:uppercase;letter-spacing:0.1em;">{element}</div>
                        <div style="font-size:0.82rem;color:#C9D1D9;line-height:1.6;
                        white-space:pre-line;">{content}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Outstanding tasks for night team
            tasks = {
                "James Okafor":        "⚠️ Cardiac monitoring overnight · Alert SpR if chest pain or ECG changes · NPO from midnight · Cath lab 09:00",
                "Margaret Thornton":   "⚠️ Theatre 22:00 tonight · IV Co-amoxiclav at 21:00 · Check consent form signed",
                "Robert Adeniran":     "🚨 Repeat INR at 22:00 — if <1.5 call orthopaedic SpR for emergency theatre · Morphine PCA · 2-hourly turns",
                "Priya Krishnamurthy": "⚠️ 4-hourly nebulisers · Step down when PEFR >75% · Respiratory review 08:00",
            }.get(p['name'], "")

            if tasks:
                st.markdown(f"""
                <div style="background:#2D1A00;border:1px solid #F59E0B;border-radius:6px;
                padding:10px 14px;font-size:0.8rem;color:#FCD34D;font-weight:500;margin-bottom:10px;">
                    📋 Outstanding tasks for night team:<br>{tasks}
                </div>""", unsafe_allow_html=True)

            if not is_accepted:
                nc1, nc2 = st.columns(2)
                if nc1.button(f"✅ Accept Patient — {p['name'].split()[0]}",
                              key=f"night_accept_{p['name']}"):
                    st.session_state.night_accepted.add(p['name'])
                    st.rerun()
                nc2.button(f"❓ Query Handover — {p['name'].split()[0]}",
                           key=f"night_query_{p['name']}")
            else:
                st.markdown(f"""
                <div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:6px;
                padding:8px 14px;font-size:0.82rem;color:#86EFAC;font-weight:600;">
                    ✅ Accepted by night team — {datetime.datetime.now().strftime('%H:%M:%S')}
                    Patient now under night team care.
                </div>""", unsafe_allow_html=True)

    # Final ward clear message
    if len(st.session_state.night_accepted) == len(PATIENTS):
        st.markdown(f"""
        <div style="background:#0A2D1A;border:2px solid #22C55E;border-radius:12px;
        padding:20px;text-align:center;margin-top:16px;">
            <div style="font-size:1.5rem;font-weight:800;color:#86EFAC;">
                🌙 Ward Handed Over Successfully
            </div>
            <div style="font-size:0.9rem;color:#86EFAC;margin-top:6px;">
                All 4 patients accepted by night team at {datetime.datetime.now().strftime('%H:%M:%S')} ·
                Day team cleared to leave · Audit trail complete
            </div>
            <div style="font-size:0.8rem;color:#4ADE80;margin-top:8px;">
                SBAR compliance: 100% · Zero incomplete handovers · DCB0129/DCB0160 compliant
            </div>
        </div>""", unsafe_allow_html=True)

# ── Chatbot ───────────────────────────────────────────────────────────
st.divider()
context_lines = []
for p in PATIENTS:
    sbar = p["sbar"]
    missing = [k for k, v in sbar.items() if v is None and k not in st.session_state.completed_sbar.get(p["name"], set())]
    done = "signed off" if p["name"] in st.session_state.handover_done else f"missing: {', '.join(missing) if missing else 'none'}"
    context_lines.append(
        f"- {p['name']}, {p['age']}y {p['sex']}, {p['diagnosis']}, "
        f"bottleneck risk {p['risk_score']:.0%}, priority P{p['priority']}, SBAR status: {done}"
    )
live_context = (
    f"{len(st.session_state.handover_done)} of {len(PATIENTS)} handovers signed off.\n"
    + "\n".join(context_lines)
)
render_chatbot("Handover Agent", live_context, key_prefix="handover_agent")

# ── Footer ────────────────────────────────────────────────────────────
st.divider()

# Final status
if len(st.session_state.handover_done) == len(PATIENTS):
    st.markdown("""
    <div style="background:#0A2D1A;border:2px solid #22C55E;border-radius:10px;
    padding:16px;text-align:center;">
        <div style="font-size:1.2rem;font-weight:800;color:#86EFAC;">
            ✅ All 4 handovers complete — Ward cleared for night team
        </div>
        <div style="font-size:0.82rem;color:#86EFAC;margin-top:4px;">
            SBAR compliance: 100% · Night team can safely accept all patients
        </div>
    </div>""", unsafe_allow_html=True)

# Auto-refresh every 2 seconds so timer ticks live
if len(st.session_state.handover_done) < len(PATIENTS):
    time.sleep(2)
    st.rerun()

st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:8px 0;">
    NHS AI Platform — Handover Agent Simulation · LD7326 · W25041744 · Northumbria University ·
    All patient data fictional · Clinician-in-the-Loop enforced · DCB0129/DCB0160 compliant
</div>
""", unsafe_allow_html=True)