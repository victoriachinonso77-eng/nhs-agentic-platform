"""
NHS AI Platform — Coordination Agent Live Simulation
Shows query inbox, auto-resolved vs escalated, interruptions prevented
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run coordination_simulation.py
"""

import streamlit as st
import time
import datetime
import random
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Coordination Agent",
    page_icon="📞",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }
#MainMenu, footer { visibility: hidden; }

.query-card {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
    animation: slideIn 0.4s ease;
    transition: all 0.3s;
}
.query-card.incoming  { border-left: 4px solid #F59E0B; }
.query-card.resolved  { border-left: 4px solid #22C55E; opacity: 0.7; }
.query-card.escalated { border-left: 4px solid #EF4444; }
.query-card.processing { border-left: 4px solid #A855F7; animation: pulse 0.8s infinite; }

.query-from   { font-size: 0.68rem; font-weight: 700; color: #8B949E; text-transform: uppercase; letter-spacing: 0.05em; }
.query-text   { font-size: 0.85rem; font-weight: 600; color: #E6EDF3; margin: 3px 0; }
.query-detail { font-size: 0.75rem; color: #8B949E; line-height: 1.4; }
.query-answer { font-size: 0.78rem; color: #86EFAC; margin-top: 4px; line-height: 1.4; }
.query-time   { font-size: 0.65rem; color: #8B949E; margin-top: 4px; }

.stat-card {
    background: #161B22; border: 1px solid #30363D;
    border-radius: 10px; padding: 16px; text-align: center; margin-bottom: 8px;
}
.stat-number { font-size: 2.5rem; font-weight: 900; line-height: 1; }
.stat-label  { font-size: 0.72rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

.interrupt-card {
    background: #2D0A0A; border: 1px solid #EF4444;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;
}
.interrupt-prevented {
    background: #0A2D1A; border: 1px solid #22C55E;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;
    animation: fadeIn 0.5s ease;
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

@keyframes slideIn { from { opacity: 0; transform: translateX(10px); } to { opacity: 1; transform: translateX(0); } }
@keyframes fadeIn  { from { opacity: 0; } to { opacity: 1; } }
@keyframes pulse   { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
</style>
""", unsafe_allow_html=True)

# ── Query definitions ─────────────────────────────────────────────────
ROUTINE_QUERIES = [
    {"from": "Porter Service",       "text": "Which ward is bed 14 allocated to?",           "answer": "Bed 14 — Emergency Assessment Unit, Ward A. Patient: James Okafor.",           "time_saved": 3},
    {"from": "Ward B Nurse",         "text": "Is there availability for a step-down transfer?", "answer": "Ward B has 4 available beds. Step-down from Ward A approved — coordinate with bed manager.", "time_saved": 4},
    {"from": "Pharmacy",             "text": "Has patient MRN-485261 received their TTO?",   "answer": "TTO not yet prepared — patient still admitted. Discharge not expected today.",   "time_saved": 3},
    {"from": "Radiology",            "text": "Confirm patient details for morning echo list", "answer": "James Okafor, NHS-485-261-3847, DOB 14/03/1958. Echo booked 09:00 tomorrow.",  "time_saved": 3},
    {"from": "Admin — Ward C",       "text": "When is the next elective list cancellation deadline?", "answer": "Elective cancellation deadline: 16:00 today. Contact theatre coordinator.", "time_saved": 2},
    {"from": "Catering",             "text": "Confirm dietary requirements for bed 7",        "answer": "Bed 7 — Margaret Thornton. NBM from midnight — theatre tonight. No meal required.", "time_saved": 2},
    {"from": "Security",             "text": "Visitor query — James Okafor, family asking for update", "answer": "Redirect family to nurse in charge at Ward A reception. No clinical details to be shared by security.", "time_saved": 3},
    {"from": "IT Helpdesk",          "text": "EPR login issue — ward terminal 3",            "answer": "IT ticket raised — ref IT-2026-4471. Estimated resolution: 45 mins. Use terminal 5 as backup.", "time_saved": 4},
    {"from": "Medical Records",      "text": "Requesting discharge summary for audit",        "answer": "Patient not yet discharged. Request re-submitted to queue for post-discharge completion.", "time_saved": 3},
    {"from": "Bed Manager",          "text": "Current bed state for afternoon board round",   "answer": "108/120 occupied (90%). 12 available. 3 expected discharges by 15:00. 7 pending transfers.", "time_saved": 5},
    {"from": "Ward D Sister",        "text": "Is Ward C expecting any step-downs today?",    "answer": "Ward C planning 3 step-downs from post-op beds — expected 14:00-16:00. Ward D to confirm capacity.", "time_saved": 3},
    {"from": "Physiotherapy",        "text": "Confirm mobility assessment for Robert Adeniran", "answer": "Robert Adeniran on Orthopaedic Ward bed 3. Post-op mobilisation — physio review requested for tomorrow morning.", "time_saved": 4},
    {"from": "Occupational Therapy", "text": "Home assessment referral — discharge planning", "answer": "OT referral submitted for patient MRN-334817. Social care contact: Newham Council, ref NC-2026-8812.", "time_saved": 3},
    {"from": "Domestic Services",    "text": "Bed vacated — Ward C bed 12. Confirm clean?",  "answer": "Confirmed — bed 12 Ward C vacated. Deep clean requested. Expected turnaround: 45 mins.", "time_saved": 2},
    {"from": "Ambulance Control",    "text": "ETA for transfer patient from Whipps Cross",   "answer": "Transfer ETA: 16:40. Receiving ward: Emergency Assessment Unit. Alert charge nurse.", "time_saved": 4},
    {"from": "Supplies",             "text": "Stock request — Ward A catheter supplies",     "answer": "Stock request logged — ref SUP-4471. Delivery to Ward A by 15:00.", "time_saved": 2},
    {"from": "Chaplaincy",           "text": "Patient requesting pastoral support — bed 3",  "answer": "Chaplaincy request logged for Robert Adeniran, Orthopaedic Ward bed 3. Chaplain notified.", "time_saved": 3},
]

COMPLEX_QUERIES = [
    {"from": "Night Doctor",       "text": "Patient deteriorating — SpR review needed urgently",    "reason": "Clinical deterioration requires immediate medical assessment — cannot be auto-resolved."},
    {"from": "Family of patient",  "text": "Requesting update on father's prognosis",               "reason": "Prognosis discussion requires senior clinician involvement — clinical and ethical decision."},
    {"from": "ICU Consultant",     "text": "Discussing escalation of care for ICU patient",         "reason": "Escalation of care is a clinical and ethical decision requiring consultant-level input."},
    {"from": "Ward Sister",        "text": "Medication error reported — incident review needed",     "reason": "Medication error requires immediate clinical review and formal incident reporting process."},
    {"from": "Pharmacist",         "text": "Drug interaction concern — patient on Warfarin + new AB", "reason": "Drug interaction assessment requires prescribing clinician review before any medication change."},
    {"from": "Safeguarding team",  "text": "Safeguarding concern raised for patient on ward",       "reason": "Safeguarding concerns require designated officer involvement — cannot be resolved by AI."},
    {"from": "Patient",            "text": "Refusing treatment — needs consent discussion",          "reason": "Consent and capacity assessment is a clinical and legal responsibility requiring doctor involvement."},
    {"from": "Bed Manager",        "text": "Major incident declared — requesting capacity for 20 patients", "reason": "Major incident response requires senior clinical leadership decision-making."},
]

# ── Session state ─────────────────────────────────────────────────────
if "coord_queries"    not in st.session_state: st.session_state.coord_queries = []
if "coord_events"     not in st.session_state: st.session_state.coord_events = []
if "auto_coord"       not in st.session_state: st.session_state.auto_coord = False
if "interruptions"    not in st.session_state: st.session_state.interruptions = []
if "prevented"        not in st.session_state: st.session_state.prevented = []
if "coord_start"      not in st.session_state: st.session_state.coord_start = datetime.datetime.now()
if "auto_query_start" not in st.session_state: st.session_state.auto_query_start = None
if "auto_query_on"    not in st.session_state: st.session_state.auto_query_on = False
if "last_query_count" not in st.session_state: st.session_state.last_query_count = 0

def add_coord_event(text, etype="info"):
    st.session_state.coord_events.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "text": text, "type": etype
    })

def add_query(query_type="routine"):
    if query_type == "routine":
        # Pick unused routine query
        used = {q["text"] for q in st.session_state.coord_queries}
        available = [q for q in ROUTINE_QUERIES if q["text"] not in used]
        if not available:
            return
        q = random.choice(available)
        st.session_state.coord_queries.append({
            **q,
            "type":   "routine",
            "status": "incoming",
            "arrived": datetime.datetime.now().strftime("%H:%M:%S"),
        })
        add_coord_event(f"📞 New query from {q['from']}: {q['text'][:50]}...", "warning")
    else:
        used = {q["text"] for q in st.session_state.coord_queries}
        available = [q for q in COMPLEX_QUERIES if q["text"] not in used]
        if not available:
            return
        q = random.choice(available)
        st.session_state.coord_queries.append({
            **q,
            "type":   "complex",
            "status": "escalated",
            "arrived": datetime.datetime.now().strftime("%H:%M:%S"),
            "answer": None,
        })
        add_coord_event(f"🚨 Complex query escalated: {q['text'][:50]}...", "critical")
        st.session_state.interruptions.append(q)

def resolve_all_routine():
    for q in st.session_state.coord_queries:
        if q["type"] == "routine" and q["status"] == "incoming":
            q["status"] = "resolved"
            st.session_state.prevented.append(q)
            add_coord_event(f"✅ Auto-resolved: {q['from']} — {q['text'][:40]}...", "success")

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;
padding:14px 24px;margin:-1rem -1rem 1rem -1rem;
display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">
            📞 Coordination Agent — Live Simulation
        </div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">
            Query inbox · Auto-resolved vs escalated · Clinician interruptions prevented
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">
        Royal London Hospital · Day Shift<br>
        LD7326 · W25041744 · Northumbria University
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#1A1A0A;border:1px solid #F59E0B;border-radius:6px;
padding:8px 14px;margin-bottom:12px;font-size:0.73rem;color:#D4A520;">
    ⚖️ <b>Research Simulation:</b> All queries and scenarios are fictional.
    No real NHS data used. GDPR · DCB0129/DCB0160 · W25041744
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("📞 Add Routine Query"):
        add_query("routine")
        st.rerun()
with c2:
    if st.button("🚨 Add Complex Query"):
        add_query("complex")
        st.rerun()
with c3:
    if st.button("⚡ Auto-Resolve All Routine"):
        resolve_all_routine()
        st.rerun()
with c4:
    auto_q = st.toggle("🔄 Auto-arrive queries", value=st.session_state.auto_query_on)
    if auto_q and not st.session_state.auto_query_on:
        st.session_state.auto_query_start = datetime.datetime.now()
    st.session_state.auto_query_on = auto_q
with c5:
    if st.button("🔄 Reset"):
        for key in ["coord_queries","coord_events","auto_coord",
                    "interruptions","prevented","coord_start",
                    "auto_query_start","auto_query_on","last_query_count"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

# Auto-arrive logic — one query every 6 seconds, mix of routine and complex
if st.session_state.auto_query_on and st.session_state.auto_query_start:
    elapsed_auto = (datetime.datetime.now() - st.session_state.auto_query_start).total_seconds()
    expected_queries = int(elapsed_auto / 6)
    if expected_queries > st.session_state.last_query_count:
        # 80% routine, 20% complex
        query_type = "routine" if random.random() < 0.80 else "complex"
        add_query(query_type)
        # Auto-resolve routine ones immediately
        if query_type == "routine":
            for q in st.session_state.coord_queries:
                if q["status"] == "incoming" and q["type"] == "routine":
                    q["status"] = "resolved"
                    st.session_state.prevented.append(q)
                    add_coord_event(f"✅ Auto-resolved: {q['from']} — {q['text'][:40]}...", "success")
        st.session_state.last_query_count = expected_queries
    # NOTE: no rerun here — let the script finish rendering the full page first.
    # The refresh trigger lives at the very bottom of the file.

st.divider()

# ── Metrics ───────────────────────────────────────────────────────────
total_q   = len(st.session_state.coord_queries)
resolved  = sum(1 for q in st.session_state.coord_queries if q["status"] == "resolved")
escalated = sum(1 for q in st.session_state.coord_queries if q["status"] == "escalated")
incoming  = sum(1 for q in st.session_state.coord_queries if q["status"] == "incoming")
time_saved = sum(q.get("time_saved", 0) for q in st.session_state.coord_queries if q["status"] == "resolved")
resolution_rate = round(resolved / total_q * 100) if total_q > 0 else 0

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Queries",       str(total_q))
m2.metric("Auto-Resolved",       str(resolved),  f"{resolution_rate}%")
m3.metric("Escalated",           str(escalated), "Need clinician")
m4.metric("Pending",             str(incoming),  "In queue")
m5.metric("Time Saved",          f"{time_saved} mins", f"{resolved} queries × avg 3 mins")
m6.metric("Interruptions Prevented", str(len(st.session_state.prevented)), "Clinician protected")

st.divider()

# ── Layout ────────────────────────────────────────────────────────────
left_col, mid_col, right_col = st.columns([2, 2, 1])

# ── LEFT: Query inbox ─────────────────────────────────────────────────
with left_col:
    st.markdown("### 📥 Query Inbox")
    st.caption("All incoming queries — AI decides: auto-resolve or escalate")

    if not st.session_state.coord_queries:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:30px;text-align:center;color:#8B949E;">
            <div style="font-size:1.5rem;margin-bottom:6px;">📞</div>
            No queries yet — add routine or complex queries above
        </div>""", unsafe_allow_html=True)
    else:
        # Show in reverse (newest first)
        for q in reversed(st.session_state.coord_queries):
            status = q["status"]
            css = {"incoming": "incoming", "resolved": "resolved", "escalated": "escalated"}.get(status)
            status_icon  = {"incoming": "⏳", "resolved": "✅", "escalated": "🚨"}.get(status)
            status_color = {"incoming": "#F59E0B", "resolved": "#22C55E", "escalated": "#EF4444"}.get(status)
            type_badge   = "ROUTINE" if q["type"] == "routine" else "COMPLEX"
            type_color   = "#38BDF8" if q["type"] == "routine" else "#EF4444"

            # Build the inner result/reason content first
            if status == "resolved" and q.get("answer"):
                inner = (
                    f'<div style="background:#0A2D1A;border-radius:4px;padding:6px 10px;'
                    f'margin-top:6px;font-size:0.78rem;color:#86EFAC;">'
                    f'🤖 Auto-resolved: {q["answer"]}</div>'
                )
            elif status == "escalated" and q.get("reason"):
                inner = (
                    f'<div style="background:#2D0A0A;border-radius:4px;padding:6px 10px;'
                    f'margin-top:6px;font-size:0.78rem;color:#FCA5A5;">'
                    f'🚨 Escalated to clinician: {q["reason"]}</div>'
                )
            else:
                inner = ""

            # Single self-contained markdown call — fully closed
            st.markdown(
                f'<div class="query-card {css}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div>'
                f'<div class="query-from">{q["from"]}</div>'
                f'<div class="query-text">{q["text"]}</div>'
                f'<div class="query-time">Arrived: {q["arrived"]}</div>'
                f'</div>'
                f'<div style="text-align:right;">'
                f'<div style="font-size:0.65rem;font-weight:700;color:{type_color};'
                f'background:#161B22;border:1px solid {type_color};'
                f'padding:2px 6px;border-radius:4px;margin-bottom:4px;">{type_badge}</div>'
                f'<div style="font-size:0.72rem;font-weight:700;color:{status_color};">'
                f'{status_icon} {status.upper()}</div>'
                f'</div></div>{inner}</div>',
                unsafe_allow_html=True
            )

            if status == "incoming":
                rc1, rc2 = st.columns(2)
                if rc1.button("✅ Auto-Resolve", key=f"res_{q['text'][:20]}"):
                    q["status"] = "resolved"
                    st.session_state.prevented.append(q)
                    add_coord_event(f"✅ Auto-resolved: {q['from']}", "success")
                    st.rerun()
                if rc2.button("🚨 Escalate", key=f"esc_{q['text'][:20]}"):
                    q["status"] = "escalated"
                    st.session_state.interruptions.append(q)
                    add_coord_event(f"🚨 Escalated to clinician: {q['from']}", "critical")
                    st.rerun()

# ── MIDDLE: Impact visualisation ──────────────────────────────────────
with mid_col:
    st.markdown("### 🛡️ Clinician Protection")
    st.caption("Interruptions prevented vs escalated to clinical staff")

    # Before/After comparison
    col_b, col_a = st.columns(2)
    with col_b:
        st.markdown(f"""
        <div class="stat-card" style="border-color:#EF4444;">
            <div class="stat-number" style="color:#EF4444;">{total_q}</div>
            <div class="stat-label">Without AI<br>All interruptions reach clinician</div>
        </div>""", unsafe_allow_html=True)

    with col_a:
        st.markdown(f"""
        <div class="stat-card" style="border-color:#22C55E;">
            <div class="stat-number" style="color:#22C55E;">{escalated}</div>
            <div class="stat-label">With AI<br>Only complex queries reach clinician</div>
        </div>""", unsafe_allow_html=True)

    # Resolution bar
    if total_q > 0:
        st.markdown(f"""
        <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
        padding:14px;margin:12px 0;">
            <div style="font-size:0.72rem;font-weight:700;color:#8B949E;
            text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
                Resolution Rate
            </div>
            <div style="font-size:2rem;font-weight:800;color:#22C55E;">
                {resolution_rate}%
            </div>
            <div style="background:#21262D;border-radius:6px;height:12px;margin:8px 0;overflow:hidden;">
                <div style="width:{resolution_rate}%;height:12px;
                background:linear-gradient(90deg,#22C55E,#38BDF8);border-radius:6px;
                transition:width 0.5s;"></div>
            </div>
            <div style="font-size:0.75rem;color:#8B949E;">
                {resolved} auto-resolved · {escalated} escalated · {incoming} pending
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # Prevented interruptions
    st.markdown("### ✅ Interruptions Prevented")
    st.caption("Queries handled without disturbing clinical staff")

    if not st.session_state.prevented:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:16px;text-align:center;color:#8B949E;font-size:0.8rem;">
            No interruptions prevented yet
        </div>""", unsafe_allow_html=True)
    else:
        for q in reversed(st.session_state.prevented[-8:]):
            st.markdown(f"""
            <div class="interrupt-prevented">
                <div style="font-size:0.72rem;font-weight:700;color:#22C55E;">
                    ✅ {q['from']} — {q.get('time_saved', 3)} mins saved
                </div>
                <div style="font-size:0.75rem;color:#86EFAC;">{q['text']}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # Escalated (must reach clinician)
    st.markdown("### 🚨 Escalated to Clinician")
    st.caption("Queries that genuinely need clinical judgment")

    if not st.session_state.interruptions:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:16px;text-align:center;color:#8B949E;font-size:0.8rem;">
            No escalations yet
        </div>""", unsafe_allow_html=True)
    else:
        for q in reversed(st.session_state.interruptions[-5:]):
            st.markdown(f"""
            <div class="interrupt-card">
                <div style="font-size:0.72rem;font-weight:700;color:#EF4444;">
                    🚨 {q['from']}
                </div>
                <div style="font-size:0.78rem;color:#FCA5A5;">{q['text']}</div>
                <div style="font-size:0.72rem;color:#FCA5A5;margin-top:3px;">
                    {q.get('reason', 'Requires clinical judgment')}
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#2D1A00;border:1px solid #F59E0B;border-radius:8px;
    padding:10px;font-size:0.75rem;color:#FCD34D;font-weight:600;margin-top:8px;">
        ⚠️ ALL escalated queries require CLINICIAN REVIEW
    </div>""", unsafe_allow_html=True)

# ── RIGHT: Event feed ─────────────────────────────────────────────────
with right_col:
    st.markdown("### 📡 Live Feed")
    st.caption(f"{len(st.session_state.coord_events)} events")

    colors = {"ai": "#A855F7", "success": "#22C55E", "critical": "#EF4444", "warning": "#F59E0B", "info": "#38BDF8"}
    if not st.session_state.coord_events:
        st.markdown("""
        <div style="background:#161B22;border:1px dashed #30363D;border-radius:8px;
        padding:20px;text-align:center;color:#8B949E;font-size:0.8rem;">
            Add queries to see live feed
        </div>""", unsafe_allow_html=True)
    else:
        for event in reversed(st.session_state.coord_events[-15:]):
            color = colors.get(event["type"], "#38BDF8")
            st.markdown(f"""
            <div style="border-left:3px solid {color};background:#161B22;
            padding:7px 10px;margin-bottom:5px;border-radius:0 5px 5px 0;font-size:0.76rem;">
                <span style="color:#8B949E;font-weight:600;">{event['time']}</span><br>
                <span style="color:#C9D1D9;">{event['text']}</span>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style="font-size:0.72rem;color:#8B949E;line-height:1.7;">
        <b>Feasibility result:</b><br>
        Query resolution: -54.4%<br>
        Cohen's d = 3.846 (very large)<br>
        p < 0.000001<br><br>
        <b>Arab et al. (2025):</b><br>
        73% of NHS doctor time on non-clinical tasks.<br>
        Coordination Agent targets this directly.
    </div>""", unsafe_allow_html=True)

st.divider()
context_lines = [
    f"- Total queries this session: {total_q}",
    f"- Auto-resolved: {resolved} ({resolution_rate}%)",
    f"- Escalated to clinician: {escalated}",
    f"- Pending: {incoming}",
    f"- Estimated time saved: {time_saved} mins",
]
live_context = "\n".join(context_lines)
render_chatbot("Coordination Agent", live_context, key_prefix="coordination_agent")

st.divider()
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:6px 0;">
    NHS AI Platform — Coordination Agent · LD7326 · W25041744 · Northumbria University ·
    All queries fictional · Clinician-in-the-Loop enforced · DCB0129/DCB0160 compliant
</div>
""", unsafe_allow_html=True)

# ── Auto-refresh trigger — runs LAST, after the full page has rendered ──
if st.session_state.auto_query_on:
    time.sleep(1)
    st.rerun()