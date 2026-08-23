"""
NHS AI Platform — Real-Time Patient Journey Simulation
Simulates the full EPR → AI → Documentation pipeline
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run simulation_live.py
"""

import streamlit as st
import time
import random
import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Live Patient Simulation",
    page_icon="🏥",
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

/* Timeline */
.timeline-container {
    position: relative;
    padding-left: 30px;
    border-left: 2px solid #30363D;
    margin: 10px 0;
}
.timeline-event {
    position: relative;
    margin-bottom: 16px;
    padding: 12px 16px;
    border-radius: 8px;
    background: #161B22;
    border: 1px solid #30363D;
    animation: fadeIn 0.5s ease;
}
.timeline-event::before {
    content: '';
    position: absolute;
    left: -39px;
    top: 16px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #38BDF8;
    border: 2px solid #0D1117;
}
.timeline-event.critical::before { background: #EF4444; }
.timeline-event.success::before  { background: #22C55E; }
.timeline-event.warning::before  { background: #F59E0B; }
.timeline-event.ai::before       { background: #A855F7; }

.event-time {
    font-size: 0.7rem;
    color: #8B949E;
    font-weight: 600;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.event-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #E6EDF3;
    margin-bottom: 4px;
}
.event-detail {
    font-size: 0.8rem;
    color: #8B949E;
    line-height: 1.5;
}
.event-source {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.source-epr  { background: #1C2333; color: #58A6FF; border: 1px solid #1F6FEB; }
.source-ai   { background: #2D1A4A; color: #C084FC; border: 1px solid #A855F7; }
.source-nurse { background: #0A2D1A; color: #86EFAC; border: 1px solid #22C55E; }
.source-doctor { background: #2D1A00; color: #FCD34D; border: 1px solid #F59E0B; }
.source-lab  { background: #1A1A2D; color: #93C5FD; border: 1px solid #38BDF8; }

/* Patient card */
.patient-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.patient-card.active { border-color: #38BDF8; }
.patient-card.complete { border-color: #22C55E; }
.patient-card.critical { border-color: #EF4444; }

.patient-name {
    font-size: 1rem;
    font-weight: 800;
    color: #E6EDF3;
    margin-bottom: 2px;
}
.patient-meta {
    font-size: 0.75rem;
    color: #8B949E;
    margin-bottom: 8px;
}
.status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
}
.badge-registered { background: #1C2333; color: #58A6FF; }
.badge-triage     { background: #2D1E00; color: #FCD34D; }
.badge-assessment { background: #2D1A00; color: #FCD34D; }
.badge-treatment  { background: #0D1F33; color: #93C5FD; }
.badge-drafted    { background: #2D1A4A; color: #C084FC; }
.badge-complete   { background: #0A2D1A; color: #86EFAC; }
.badge-critical   { background: #2D0A0A; color: #FCA5A5; }

/* SBAR note */
.sbar-note {
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 16px;
    margin-top: 10px;
    animation: fadeIn 0.8s ease;
}
.sbar-label {
    font-size: 0.65rem;
    font-weight: 800;
    color: #A855F7;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 3px;
}
.sbar-text {
    font-size: 0.82rem;
    color: #C9D1D9;
    line-height: 1.6;
    margin-bottom: 10px;
}
.ai-drafted-banner {
    background: #2D1A4A;
    border: 1px solid #A855F7;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.78rem;
    color: #C084FC;
    font-weight: 600;
    margin-top: 8px;
}
.clinician-banner {
    background: #2D1A00;
    border: 1px solid #F59E0B;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.78rem;
    color: #FCD34D;
    font-weight: 600;
    margin-top: 6px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.pulse {
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 12px !important;
}
[data-testid="metric-container"] label {
    color: #8B949E !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}
.stButton > button {
    background: #1F6FEB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
}
.stButton > button:hover { background: #388BFD !important; }
</style>
""", unsafe_allow_html=True)

# ── Simulated patient pool ────────────────────────────────────────────
# Handover status per patient — which SBAR elements are missing
HANDOVER_STATUS = {
    "James Okafor": {
        "situation":     True,
        "background":    True,
        "assessment":    False,   # Missing
        "recommendation": False,  # Missing
        "risk_score":    0.87,
        "priority":      1,
    },
    "Margaret Thornton": {
        "situation":     True,
        "background":    False,   # Missing
        "assessment":    True,
        "recommendation": True,
        "risk_score":    0.43,
        "priority":      3,
    },
    "Robert Adeniran": {
        "situation":     True,
        "background":    True,
        "assessment":    False,   # Missing
        "recommendation": False,  # Missing
        "risk_score":    0.91,
        "priority":      1,
    },
    "Priya Krishnamurthy": {
        "situation":     True,
        "background":    True,
        "assessment":    True,
        "recommendation": False,  # Missing
        "risk_score":    0.72,
        "priority":      2,
    },
}

PATIENT_POOL = [
    {
        "name": "James Okafor",
        "age": 67, "sex": "M", "dob": "14/03/1958",
        "nhs_number": "NHS-485-261-3847",
        "gp": "Dr. Singh, Whitechapel Health Centre",
        "reason": "Chest pain and shortness of breath",
        "admission_type": "EW EMER.",
        "risk": "high",
        "obs": {"bp": "158/94", "hr": 102, "temp": 37.8, "o2": 94, "rr": 22},
        "history": "Type 2 diabetes, hypertension, previous MI 2019",
        "medications": ["Metformin 500mg BD", "Amlodipine 5mg OD", "Aspirin 75mg OD"],
        "tests": ["ECG — ST elevation in leads II, III, aVF", "Troponin — elevated at 2.4 ng/mL", "CXR — mild pulmonary oedema"],
        "los_hours": 187.4,
        "transfers": 3,
        "had_icu": True, "icu_days": 2.1,
    },
    {
        "name": "Margaret Thornton",
        "age": 45, "sex": "F", "dob": "22/09/1980",
        "nhs_number": "NHS-712-394-5521",
        "gp": "Dr. Ahmed, Mile End Surgery",
        "reason": "Appendicitis — referred by GP",
        "admission_type": "URGENT",
        "risk": "low",
        "obs": {"bp": "122/78", "hr": 88, "temp": 37.9, "o2": 98, "rr": 16},
        "history": "No significant past medical history",
        "medications": ["None regular"],
        "tests": ["CT abdomen — acute appendicitis confirmed", "WBC — 14.2 (elevated)", "CRP — 68"],
        "los_hours": 52.3,
        "transfers": 2,
        "had_icu": False, "icu_days": 0,
    },
    {
        "name": "Robert Adeniran",
        "age": 78, "sex": "M", "dob": "05/11/1947",
        "nhs_number": "NHS-334-817-9204",
        "gp": "Dr. Patel, Stepney Green Practice",
        "reason": "Fall at home — hip fracture suspected",
        "admission_type": "DIRECT EMER.",
        "risk": "high",
        "obs": {"bp": "142/88", "hr": 96, "temp": 36.8, "o2": 96, "rr": 18},
        "history": "Osteoporosis, atrial fibrillation, chronic kidney disease stage 3",
        "medications": ["Warfarin 3mg OD", "Bisoprolol 2.5mg OD", "Calcium + Vit D OD"],
        "tests": ["X-ray hip — NOF fracture confirmed", "INR — 3.8 (supratherapeutic)", "Renal function — eGFR 38"],
        "los_hours": 264.6,
        "transfers": 5,
        "had_icu": False, "icu_days": 0,
    },
    {
        "name": "Priya Krishnamurthy",
        "age": 34, "sex": "F", "dob": "18/06/1991",
        "nhs_number": "NHS-591-042-7713",
        "gp": "Dr. Williams, Bethnal Green Surgery",
        "reason": "Severe asthma exacerbation",
        "admission_type": "EW EMER.",
        "risk": "low",
        "obs": {"bp": "118/72", "hr": 112, "temp": 37.2, "o2": 91, "rr": 28},
        "history": "Asthma since childhood, eczema",
        "medications": ["Salbutamol inhaler PRN", "Fostair 100/6 BD", "Montelukast 10mg OD"],
        "tests": ["PEFR — 38% predicted", "ABG — mild type 1 respiratory failure", "CXR — hyperinflation, no consolidation"],
        "los_hours": 43.5,
        "transfers": 2,
        "had_icu": False, "icu_days": 0,
    },
]

# Clinical event timelines per patient
def get_events(patient, base_time):
    """Generate realistic clinical event timeline for a patient."""
    t = base_time
    events = []

    def add(mins, event_type, title, detail, source, color="default"):
        nonlocal t
        event_time = t + datetime.timedelta(minutes=mins)
        events.append({
            "time": event_time,
            "time_str": event_time.strftime("%H:%M"),
            "type": event_type,
            "title": title,
            "detail": detail,
            "source": source,
            "color": color
        })
        return event_time

    add(0, "registration", f"Patient registered at reception",
        f"{patient['name']}, {patient['age']}y {patient['sex']}. "
        f"DOB: {patient['dob']}. NHS: {patient['nhs_number']}. "
        f"GP: {patient['gp']}. Reason: {patient['reason']}.",
        "EPR", "default")

    add(0.5, "ai_signal", "AI platform notified via FHIR API",
        f"New patient signal received. Tracking initiated for {patient['nhs_number']}. "
        f"Admission type: {patient['admission_type']}. Building clinical picture.",
        "AI", "ai")

    add(8, "triage", "Triage nurse assessment",
        f"BP {patient['obs']['bp']} mmHg · HR {patient['obs']['hr']} bpm · "
        f"Temp {patient['obs']['temp']}°C · O2 {patient['obs']['o2']}% · "
        f"RR {patient['obs']['rr']}/min. "
        f"Triage category: {'1 — Immediate' if patient['risk']=='high' else '3 — Urgent'}.",
        "NURSE", "warning" if patient['risk']=='high' else "default")

    add(8.5, "ai_obs", "AI records observations automatically",
        f"Observations logged to patient record. "
        f"{'⚠️ HR {hr} and RR {rr} flagged as abnormal — XGBoost risk score updating.'.format(hr=patient['obs']['hr'], rr=patient['obs']['rr']) if patient['risk']=='high' else 'Observations within acceptable range.'}",
        "AI", "ai")

    add(25, "doctor", "Doctor assessment",
        f"History taken. PMH: {patient['history']}. "
        f"Medications: {', '.join(patient['medications'][:2])}. "
        f"Clinical impression: {patient['reason']}. Tests ordered.",
        "DOCTOR", "warning")

    for i, test in enumerate(patient['tests']):
        add(45 + i*15, "lab", f"Result received: {test.split(' — ')[0]}",
            test, "LAB", "default")

    add(100, "ai_draft", "Documentation Agent drafts SBAR note",
        f"Sufficient clinical data now available. SBAR note auto-drafted from EPR data. "
        f"{'HIGH BOTTLENECK RISK flagged — LOS prediction {los}h exceeds threshold.'.format(los=patient['los_hours']) if patient['risk']=='high' else 'LOW RISK — routine note ready for sign-off.'}",
        "AI", "ai")

    add(420, "handover_check", "Handover Agent activated — 1 hour before shift end",
        f"Checking SBAR compliance for all {patient['name']} handover documentation. "
        f"Cross-referencing XGBoost bottleneck score ({HANDOVER_STATUS.get(patient['name'], {}).get('risk_score', 0):.0%}) to prioritise.",
        "AI", "ai")

    hs = HANDOVER_STATUS.get(patient["name"], {})
    missing = [k.upper() for k in ["situation","background","assessment","recommendation"] if not hs.get(k, True)]
    complete = [k.upper() for k in ["situation","background","assessment","recommendation"] if hs.get(k, True)]
    if missing:
        add(421, "handover_flag", f"SBAR incomplete — {len(missing)} element(s) missing",
            f"Missing: {', '.join(missing)}. Complete: {', '.join(complete)}. "
            f"Priority {hs.get('priority', 3)} — must complete before handover.",
            "AI", "critical" if hs.get("priority", 3) == 1 else "warning")
    else:
        add(421, "handover_ok", "SBAR handover complete — all elements present",
            f"Situation, Background, Assessment, Recommendation all documented. "
            f"Handover cleared for patient transfer.",
            "AI", "success")

    return sorted(events, key=lambda x: x["time"])


def draft_sbar(patient, use_ai=False):
    """Draft SBAR note for a patient."""
    p = patient
    icu_text = f"Required {p['icu_days']} days ICU-level care. " if p['had_icu'] else ""

    if use_ai and os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = (
            f"Draft a concise NHS SBAR clinical note. Be SPECIFIC — use exact data provided.\n\n"
            f"PATIENT: {p['name']}, {p['age']}y {p['sex']}\n"
            f"NHS Number: {p['nhs_number']}\n"
            f"Admission: {p['admission_type']} — {p['reason']}\n"
            f"Observations: BP {p['obs']['bp']}, HR {p['obs']['hr']}, Temp {p['obs']['temp']}°C, "
            f"O2 {p['obs']['o2']}%, RR {p['obs']['rr']}\n"
            f"History: {p['history']}\n"
            f"Medications: {', '.join(p['medications'])}\n"
            f"Test results: {'; '.join(p['tests'])}\n"
            f"LOS so far: {p['los_hours']}h | Transfers: {p['transfers']} | "
            f"ICU: {'Yes — ' + str(p['icu_days']) + ' days' if p['had_icu'] else 'No'}\n"
            f"Risk: {'HIGH BOTTLENECK' if p['risk']=='high' else 'LOW RISK'}\n\n"
            f"Format:\nSITUATION: ...\nBACKGROUND: ...\nASSESSMENT: ...\nRECOMMENDATION: 1. ... 2. ... 3. ..."
        )
        resp = client.chat.completions.create(
            model="gpt-4o", max_tokens=400,
            messages=[
                {"role": "system", "content": "Clinical documentation assistant. Use exact patient data. Be specific."},
                {"role": "user", "content": prompt}
            ]
        )
        text = resp.choices[0].message.content.strip()
        sections = {"SITUATION": "", "BACKGROUND": "", "ASSESSMENT": "", "RECOMMENDATION": ""}
        current = None
        for line in text.split("\n"):
            for key in sections:
                if line.upper().startswith(key):
                    current = key
                    sections[key] = line.split(":", 1)[-1].strip()
                    break
            else:
                if current and line.strip():
                    sections[current] += " " + line.strip()
        return sections
    else:
        # Template SBAR using real patient data
        return {
            "SITUATION": (
                f"Patient {p['name']}, {p['age']}y {p['sex']}, NHS {p['nhs_number']}. "
                f"Admitted via {p['admission_type']} presenting with {p['reason']}. "
                f"LOS: {p['los_hours']}h. "
                f"{'XGBoost flags HIGH BOTTLENECK RISK — expedited consultant review required.' if p['risk']=='high' else 'XGBoost — LOW RISK. Routine note auto-drafted.'}"
            ),
            "BACKGROUND": (
                f"GP: {p['gp']}. PMH: {p['history']}. "
                f"Regular medications: {', '.join(p['medications'])}. "
                f"{icu_text}"
                f"{p['transfers']} ward transfers this admission."
            ),
            "ASSESSMENT": (
                f"Observations on admission: BP {p['obs']['bp']} mmHg, HR {p['obs']['hr']} bpm, "
                f"Temp {p['obs']['temp']}°C, O2 sat {p['obs']['o2']}%, RR {p['obs']['rr']}/min. "
                f"Investigations: {'; '.join(p['tests'])}. "
                f"{'LOS {los}h exceeds 75th percentile threshold (134.9h). Complex pathway confirmed.'.format(los=p['los_hours']) if p['risk']=='high' else 'LOS {los}h within normal range. Trajectory consistent with timely discharge.'.format(los=p['los_hours'])}"
            ),
            "RECOMMENDATION": (
                f"{'1. Expedite specialist review within 4 hours given HIGH RISK classification.\n2. Notify bed manager — capacity pressure at current occupancy.\n3. Ensure all outstanding results reviewed before any transfer or discharge.' if p['risk']=='high' else '1. Continue current management plan — review at next ward round.\n2. Complete discharge summary when clinically appropriate.\n3. Ensure handover documentation completed before shift end.'}"
            )
        }


# ── Session state ─────────────────────────────────────────────────────
if "sim_patients"  not in st.session_state: st.session_state.sim_patients = []
if "sim_running"   not in st.session_state: st.session_state.sim_running = False
if "notes_drafted" not in st.session_state: st.session_state.notes_drafted = {}
if "approved"      not in st.session_state: st.session_state.approved = set()
if "total_arrived" not in st.session_state: st.session_state.total_arrived = 0
if "total_drafted" not in st.session_state: st.session_state.total_drafted = 0
if "time_saved"    not in st.session_state: st.session_state.time_saved = 0

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1.5rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            📝 Documentation Agent — Live Patient Journey Simulation
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            How the Documentation Agent works: Patient registers → EPR notifies AI → Clinical events logged → SBAR note auto-drafted → Clinician reviews
        </div>
    </div>
    <div style="font-size:0.78rem;color:#8B949E;text-align:right;">
        Royal London Hospital · Emergency Assessment Unit<br>
        LD7326 · W25041744 · Northumbria University
    </div>
</div>
""", unsafe_allow_html=True)

# ── Legal Disclaimer ─────────────────────────────────────────────────
st.markdown("""
<div style="background:#1A1A0A;border:1.5px solid #F59E0B;border-radius:8px;
padding:12px 18px;margin-bottom:16px;">
    <div style="font-size:0.78rem;font-weight:700;color:#FCD34D;margin-bottom:4px;">
        ⚖️ Research Simulation Disclaimer
    </div>
    <div style="font-size:0.76rem;color:#D4A520;line-height:1.6;">
        All patient names, NHS numbers, GP details, and clinical data shown in this simulation
        are <b>entirely fictional</b> and generated solely for research demonstration purposes.
        No real patient data is used at any point. James Okafor, Margaret Thornton,
        Robert Adeniran, and Priya Krishnamurthy do not exist — their details are invented.
        MIMIC-IV data referenced elsewhere in this platform was accessed under PhysioNet
        Credentialled Health Data Licence (W25041744) and is fully de-identified by MIT
        before access — no patient re-identification is possible or attempted.
        This platform is a research prototype only and is not deployed in any clinical setting.
        <b>GDPR · NHS Act 2006 · Computer Misuse Act 1990 · DCB0129/DCB0160 compliant.</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 2])
with ctrl1:
    use_ai = st.toggle("🤖 AI-powered notes (GPT-4o)", value=False)
with ctrl2:
    speed = st.select_slider(
        "Simulation speed",
        options=["Slow", "Normal", "Fast", "Instant"],
        value="Fast"
    )
with ctrl3:
    sim_mode = st.radio(
        "Mode",
        ["Manual — add patients one by one",
         "Auto — simulate full shift"],
        index=0,
        horizontal=False
    )

speed_map = {"Slow": 1.5, "Normal": 0.8, "Fast": 0.3, "Instant": 0.0}
delay = speed_map[speed]

st.divider()

# ── Layout: Left = patient queue, Right = live timeline ──────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown("### 👥 Patient Queue")
    st.caption("Patients arriving at reception")

    # Add patient button
    if len(st.session_state.sim_patients) < len(PATIENT_POOL):
        next_patient = PATIENT_POOL[len(st.session_state.sim_patients)]
        if st.button(f"➕ Register: {next_patient['name']}"):
            base_time = datetime.datetime.now()
            patient_data = {
                **next_patient,
                "arrival_time": base_time,
                "events": get_events(next_patient, base_time),
                "status": "registered",
                "events_shown": 0,
                "note_drafted": False,
            }
            st.session_state.sim_patients.append(patient_data)
            st.session_state.total_arrived += 1
            st.rerun()

    elif st.button("🔄 Reset Simulation"):
        st.session_state.sim_patients = []
        st.session_state.notes_drafted = {}
        st.session_state.approved = set()
        st.session_state.total_arrived = 0
        st.session_state.total_drafted = 0
        st.session_state.time_saved = 0
        st.rerun()

    st.divider()

    # Patient cards
    for idx, p in enumerate(st.session_state.sim_patients):
        status = p.get("status", "registered")
        note_done = p["name"] in st.session_state.notes_drafted
        approved = p["name"] in st.session_state.approved

        if approved:
            card_class, badge_class, badge_text = "complete", "badge-complete", "✅ Note Approved"
        elif note_done:
            card_class, badge_class, badge_text = "active", "badge-drafted", "📝 Note Drafted — Review"
        elif p["risk"] == "high":
            card_class, badge_class, badge_text = "critical", "badge-critical", "🔴 High Risk"
        else:
            card_class, badge_class, badge_text = "active", "badge-triage", "🟡 In Progress"

        st.markdown(f"""
        <div class="patient-card {card_class}">
            <div class="patient-name">{p['name']}</div>
            <div class="patient-meta">
                {p['age']}y {p['sex']} · {p['nhs_number']}<br>
                {p['reason']}<br>
                Arrived: {p['arrival_time'].strftime('%H:%M:%S')}
            </div>
            <span class="status-badge {badge_class}">{badge_text}</span>
        </div>""", unsafe_allow_html=True)

    # Summary metrics
    if st.session_state.sim_patients:
        st.divider()
        st.metric("Patients Registered", st.session_state.total_arrived)
        st.metric("Notes Auto-Drafted", st.session_state.total_drafted)
        st.metric("Time Saved (est.)", f"{st.session_state.time_saved} mins")
        high_risk = sum(1 for p in st.session_state.sim_patients if p['risk']=='high')
        st.metric("High Risk Flagged", str(high_risk))

with right_col:
    st.markdown("### 📡 Live Clinical Event Feed")
    st.caption("Real-time events as they happen — EPR, clinical staff, AI")

    if not st.session_state.sim_patients:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:10px;
        padding:40px;text-align:center;color:#8B949E;">
            <div style="font-size:2rem;margin-bottom:8px;">🏥</div>
            <div style="font-weight:600;margin-bottom:4px;">No patients yet</div>
            <div style="font-size:0.82rem;">Click "Register" to admit a patient and watch the AI platform respond in real time</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Show events for all patients
        for p_idx, p in enumerate(st.session_state.sim_patients):

            # Show patient separator
            risk_color = "#EF4444" if p["risk"] == "high" else "#22C55E"
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid {risk_color};border-radius:8px;
            padding:10px 14px;margin:12px 0 8px 0;">
                <span style="font-weight:800;color:{risk_color};">
                    {'🔴' if p['risk']=='high' else '🟢'} {p['name']}
                </span>
                <span style="font-size:0.75rem;color:#8B949E;margin-left:8px;">
                    {p['age']}y · {p['admission_type']} · Arrived {p['arrival_time'].strftime('%H:%M:%S')}
                </span>
            </div>""", unsafe_allow_html=True)

            # Determine how many events to show
            total_events = len(p["events"])
            if speed == "Instant":
                events_to_show = total_events
            else:
                # Show events progressively based on time elapsed
                elapsed = (datetime.datetime.now() - p["arrival_time"]).total_seconds()
                # Scale: 1 real second = 5 simulated minutes
                sim_minutes = elapsed * 5
                events_to_show = sum(
                    1 for e in p["events"]
                    if (e["time"] - p["arrival_time"]).total_seconds() / 60 <= sim_minutes
                )

            events_to_show = max(1, min(events_to_show, total_events))

            # Display events
            st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
            for event in p["events"][:events_to_show]:
                source_class = {
                    "EPR": "source-epr", "AI": "source-ai",
                    "NURSE": "source-nurse", "DOCTOR": "source-doctor",
                    "LAB": "source-lab"
                }.get(event["source"], "source-epr")
                color_class = event.get("color", "default")

                st.markdown(f"""
                <div class="timeline-event {color_class}">
                    <div class="event-time">{event['time_str']}</div>
                    <div class="event-title">{event['title']}</div>
                    <div class="event-detail">{event['detail']}</div>
                    <span class="event-source {source_class}">{event['source']}</span>
                </div>""", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # Check if Documentation Agent event has been reached
            ai_draft_reached = any(
                e["type"] == "ai_draft"
                for e in p["events"][:events_to_show]
            )

            # Draft and show note
            if ai_draft_reached and p["name"] not in st.session_state.notes_drafted:
                with st.spinner(f"Documentation Agent drafting note for {p['name']}..."):
                    if delay > 0:
                        time.sleep(delay)
                    sbar = draft_sbar(p, use_ai=use_ai)
                    st.session_state.notes_drafted[p["name"]] = sbar
                    st.session_state.total_drafted += 1
                    st.session_state.time_saved += 8

            if p["name"] in st.session_state.notes_drafted:
                sbar = st.session_state.notes_drafted[p["name"]]
                risk_col = "#EF4444" if p["risk"] == "high" else "#22C55E"
                risk_label = "⚠️ HIGH BOTTLENECK RISK — Expedited review required" if p["risk"] == "high" else "✅ LOW RISK — Auto-drafted, sign-off required"

                st.markdown(f"""
                <div class="sbar-note" style="border-color:{risk_col};">
                    <div style="font-size:0.8rem;font-weight:700;color:#A855F7;margin-bottom:10px;">
                        🤖 Documentation Agent — Auto-drafted SBAR Note
                        <span style="font-size:0.65rem;color:#8B949E;margin-left:8px;font-weight:400;">
                            Generated from EPR data · No clinician input required
                        </span>
                    </div>
                """, unsafe_allow_html=True)

                for section, content in sbar.items():
                    if content.strip():
                        st.markdown(f"""
                        <div style="margin-bottom:8px;">
                            <div class="sbar-label">{section}</div>
                            <div class="sbar-text">{content}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="ai-drafted-banner">
                        🤖 Auto-drafted by Documentation Agent from EPR data at {datetime.datetime.now().strftime('%H:%M:%S')}
                    </div>
                    <div class="clinician-banner">
                        ⚠️ {risk_label} — CLINICIAN REVIEW AND SIGN-OFF REQUIRED
                    </div>
                </div>""", unsafe_allow_html=True)

                # Approve/Edit/Reject
                if p["name"] not in st.session_state.approved:
                    b1, b2, b3 = st.columns(3)
                    if b1.button(f"✅ Approve & Sign — {p['name'].split()[0]}",
                                  key=f"approve_{p_idx}"):
                        st.session_state.approved.add(p["name"])
                        st.success(f"Note approved for {p['name']} — added to medical record")
                        st.rerun()
                    b2.button(f"✏️ Edit — {p['name'].split()[0]}", key=f"edit_{p_idx}")
                    b3.button(f"❌ Reject — {p['name'].split()[0]}", key=f"reject_{p_idx}")
                else:
                    st.success(f"✅ Note approved and signed — {p['name']} · {datetime.datetime.now().strftime('%H:%M:%S')}")

            # ── Handover Agent check ──────────────────────────────────
            handover_reached = any(
                e["type"] in ["handover_check", "handover_flag", "handover_ok"]
                for e in p["events"][:events_to_show]
            )

            if handover_reached:
                hs = HANDOVER_STATUS.get(p["name"], {})
                missing = [k for k in ["situation","background","assessment","recommendation"] if not hs.get(k, True)]
                complete = [k for k in ["situation","background","assessment","recommendation"] if hs.get(k, True)]
                priority = hs.get("priority", 3)
                risk_score = hs.get("risk_score", 0)
                sbar_pct = round(len(complete) / 4 * 100)

                priority_color = {1: "#EF4444", 2: "#F59E0B", 3: "#22C55E"}.get(priority, "#8B949E")
                priority_label = {1: "P1 — CRITICAL", 2: "P2 — HIGH", 3: "P3 — ROUTINE"}.get(priority, "P3")

                st.markdown(f"""
                <div style="background:#0D1117;border:1.5px solid {priority_color};
                border-radius:10px;padding:16px;margin-top:12px;">
                    <div style="font-size:0.8rem;font-weight:700;color:#A855F7;margin-bottom:10px;">
                        🤝 Handover Agent — SBAR Compliance Check
                        <span style="font-size:0.65rem;color:#8B949E;margin-left:8px;font-weight:400;">
                            Triggered 1 hour before shift end · {datetime.datetime.now().strftime('%H:%M:%S')}
                        </span>
                    </div>

                    <div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap;">
                        <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;text-align:center;">
                            <div style="font-size:1.3rem;font-weight:800;color:{priority_color};">
                                {priority_label}
                            </div>
                            <div style="font-size:0.7rem;color:#8B949E;">Handover Priority</div>
                        </div>
                        <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;text-align:center;">
                            <div style="font-size:1.3rem;font-weight:800;color:{priority_color};">{risk_score:.0%}</div>
                            <div style="font-size:0.7rem;color:#8B949E;">Bottleneck Risk</div>
                        </div>
                        <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;text-align:center;">
                            <div style="font-size:1.3rem;font-weight:800;color:{'#22C55E' if sbar_pct==100 else '#F59E0B' if sbar_pct>=50 else '#EF4444'};">
                                {sbar_pct}%
                            </div>
                            <div style="font-size:0.7rem;color:#8B949E;">SBAR Complete</div>
                        </div>
                    </div>

                    <div style="margin-bottom:10px;">
                        <div style="font-size:0.72rem;font-weight:700;color:#8B949E;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
                            SBAR Element Status
                        </div>
                        <div style="display:flex;gap:8px;flex-wrap:wrap;">
                """, unsafe_allow_html=True)

                for element in ["situation", "background", "assessment", "recommendation"]:
                    is_complete = hs.get(element, True)
                    bg = "#0A2D1A" if is_complete else "#2D0A0A"
                    color = "#86EFAC" if is_complete else "#FCA5A5"
                    border = "#22C55E" if is_complete else "#EF4444"
                    icon = "✅" if is_complete else "❌"
                    st.markdown(f"""
                    <div style="background:{bg};border:1px solid {border};border-radius:6px;
                    padding:6px 12px;font-size:0.78rem;font-weight:700;color:{color};">
                        {icon} {element.upper()}
                    </div>""", unsafe_allow_html=True)

                st.markdown("</div></div>", unsafe_allow_html=True)

                if missing:
                    missing_str = ", ".join([m.upper() for m in missing])
                    st.markdown(f"""
                    <div style="background:#2D0A0A;border:1px solid #EF4444;border-radius:6px;
                    padding:10px 14px;font-size:0.82rem;color:#FCA5A5;font-weight:600;margin-bottom:8px;">
                        ⚠️ ACTION REQUIRED: Complete {missing_str} before handover.
                        Outgoing clinician must add missing sections before shift end.
                    </div>""", unsafe_allow_html=True)

                    # Complete handover button
                    hov_key = f"handover_done_{p_idx}"
                    if hov_key not in st.session_state:
                        st.session_state[hov_key] = False

                    if not st.session_state[hov_key]:
                        if st.button(f"✅ Mark Handover Complete — {p['name'].split()[0]}",
                                     key=f"hbtn_{p_idx}"):
                            st.session_state[hov_key] = True
                            st.rerun()
                    else:
                        st.markdown("""
                        <div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:6px;
                        padding:10px 14px;font-size:0.82rem;color:#86EFAC;font-weight:600;">
                            ✅ Handover marked complete — all SBAR elements now documented.
                            Night team can safely accept this patient.
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:#0A2D1A;border:1px solid #22C55E;border-radius:6px;
                    padding:10px 14px;font-size:0.82rem;color:#86EFAC;font-weight:600;">
                        ✅ SBAR handover complete — all four elements documented.
                        Safe to transfer to night team.
                    </div>""", unsafe_allow_html=True)

                st.markdown("""
                <div style="font-size:0.72rem;color:#8B949E;margin-top:6px;">
                    ⚠️ CLINICIAN REVIEW REQUIRED before any patient transfer · DCB0129/DCB0160
                </div></div>""", unsafe_allow_html=True)

        # Auto-refresh if simulation is running
        if any(
            p["name"] not in st.session_state.notes_drafted
            for p in st.session_state.sim_patients
        ) and speed != "Instant":
            time.sleep(delay if delay > 0 else 0.1)
            st.rerun()

# ── Chatbot ───────────────────────────────────────────────────────────
st.divider()
if st.session_state.sim_patients:
    context_lines = []
    for p in st.session_state.sim_patients:
        note_status = "note drafted" if p["name"] in st.session_state.notes_drafted else "no note yet"
        approved = " (approved)" if p["name"] in st.session_state.approved else ""
        context_lines.append(
            f"- {p['name']}, {p['age']}y {p['sex']}, {p['admission_type']}, "
            f"reason: {p['reason']}, risk: {p['risk']}, {note_status}{approved}"
        )
    live_context = (
        f"{len(st.session_state.sim_patients)} patients registered this session.\n"
        + "\n".join(context_lines)
    )
else:
    live_context = "No patients registered yet in this session."

render_chatbot("Documentation Agent", live_context, key_prefix="doc_agent")

# ── Footer ────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:8px 0;">
    NHS AI Platform — Live Simulation · LD7326 · W25041744 · Northumbria University ·
    Clinician-in-the-Loop enforced · DCB0129/DCB0160 compliant
</div>
""", unsafe_allow_html=True)