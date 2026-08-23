"""
NHS AI Platform — Cognitive Support Agent Live Simulation (v2)
Full rebuild with auto-pressure, before/after, visible consequences,
patient context, and recovery arc
LD7326 | MSc Artificial Intelligence Technology | W25041744

Run: streamlit run cognitive_simulation.py
"""

import streamlit as st
import time
import datetime
import random
from dotenv import load_dotenv
from chatbot_helper import render_chatbot

load_dotenv()

st.set_page_config(
    page_title="NHS AI — Cognitive Support Agent",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }
#MainMenu, footer { visibility: hidden; }

.gauge-box { background: #161B22; border: 2px solid #30363D; border-radius: 14px; padding: 24px 20px; text-align: center; transition: border-color 0.5s; }
.gauge-number { font-size: 4rem; font-weight: 900; line-height: 1; }
.gauge-label  { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; margin-top: 4px; }
.gauge-bar-bg { background: #21262D; border-radius: 8px; height: 14px; margin: 10px 0; overflow: hidden; }
.gauge-bar    { height: 14px; border-radius: 8px; transition: width 1s ease; }

.factor-row { background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; }
.factor-mini-bg { background: #21262D; border-radius: 4px; height: 6px; margin-top: 4px; }
.factor-mini    { height: 6px; border-radius: 4px; transition: width 0.8s ease; }

.scaffold { border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; border: 1px solid #30363D; transition: all 0.4s ease; }
.scaffold.waiting { background: #161B22; opacity: 0.45; }
.scaffold.active  { background: #0D1F33; border-color: #38BDF8; opacity: 1; }
.scaffold.done    { background: #0A2D1A; border-color: #22C55E; opacity: 0.85; }

.patient-row { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 7px; margin-bottom: 5px; border: 1px solid #30363D; background: #161B22; font-size: 0.8rem; transition: all 0.4s ease; }
.patient-row.p1 { border-left: 4px solid #EF4444; }
.patient-row.p2 { border-left: 4px solid #F59E0B; }
.patient-row.p3 { border-left: 4px solid #38BDF8; }
.patient-row.p4 { border-left: 4px solid #22C55E; }

.decision-item { padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; background: #161B22; border: 1px solid #30363D; font-size: 0.78rem; }
.decision-item.urgent   { border-color: #EF4444; background: #1A0A0A; }
.decision-item.queued   { opacity: 0.35; }
.decision-item.deferred { opacity: 0.2; color: #6E7681; }

.ba-card  { border-radius: 10px; padding: 14px 16px; border: 1.5px solid #30363D; background: #161B22; }
.ba-title { font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.ba-item  { font-size: 0.78rem; color: #C9D1D9; padding: 4px 0; border-bottom: 1px solid #21262D; }

.ev { border-left: 3px solid #30363D; padding: 7px 12px; margin-bottom: 5px; border-radius: 0 5px 5px 0; background: #161B22; font-size: 0.76rem; animation: fadeIn 0.4s ease; }
.ev.ai       { border-left-color: #A855F7; }
.ev.warning  { border-left-color: #F59E0B; }
.ev.critical { border-left-color: #EF4444; }
.ev.success  { border-left-color: #22C55E; }
.ev.info     { border-left-color: #38BDF8; }

[data-testid="metric-container"] { background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 12px !important; }
[data-testid="metric-container"] label { color: #8B949E !important; font-size: 0.7rem !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #E6EDF3 !important; font-size: 1.4rem !important; font-weight: 700 !important; }

.stButton > button { background: #1F6FEB !important; color: #FFF !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; width: 100% !important; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse  { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.pulse { animation: pulse 1.5s infinite; }
</style>
""", unsafe_allow_html=True)

PATIENTS = [
    {"name": "James Okafor",        "ward": "EA Unit Bed 14",  "diagnosis": "NSTEMI",               "risk": 0.87, "urgent": True,  "note_due": True,  "priority": "p1"},
    {"name": "Robert Adeniran",     "ward": "Ortho Ward Bed 3","diagnosis": "NOF Fracture",          "risk": 0.91, "urgent": True,  "note_due": True,  "priority": "p1"},
    {"name": "Priya Krishnamurthy", "ward": "Resp Ward Bed 11","diagnosis": "Asthma exacerbation",   "risk": 0.72, "urgent": True,  "note_due": True,  "priority": "p2"},
    {"name": "Michael Thompson",    "ward": "Ward A Bed 16",   "diagnosis": "COPD exacerbation",     "risk": 0.61, "urgent": False, "note_due": True,  "priority": "p2"},
    {"name": "Margaret Thornton",   "ward": "Surgical Bed 7",  "diagnosis": "Appendicitis",          "risk": 0.43, "urgent": False, "note_due": True,  "priority": "p3"},
    {"name": "Sarah Williams",      "ward": "EA Unit Bed 8",   "diagnosis": "Chest pain",            "risk": 0.31, "urgent": False, "note_due": True,  "priority": "p3"},
    {"name": "Fatima Al-Hassan",    "ward": "Ward B Bed 9",    "diagnosis": "UTI",                   "risk": 0.25, "urgent": False, "note_due": True,  "priority": "p4"},
    {"name": "David Chen",          "ward": "Ward D Bed 2",    "diagnosis": "Elective hip replace",  "risk": 0.18, "urgent": False, "note_due": False, "priority": "p4"},
]

DECISIONS_ALL = [
    {"text": "Robert Adeniran — INR result due at 22:00 — theatre decision",   "urgent": True},
    {"text": "James Okafor — troponin trend review before cath lab at 09:00",  "urgent": True},
    {"text": "Priya Krishnamurthy — PEFR check — step down to inhaler?",       "urgent": True},
    {"text": "Margaret Thornton — theatre consent to verify before 22:00",     "urgent": False},
    {"text": "Sarah Williams — discharge criteria assessment",                  "urgent": False},
    {"text": "Michael Thompson — chest X-ray result review",                   "urgent": False},
    {"text": "Ward C step-down coordination — 3 patients",                     "urgent": False},
    {"text": "Fatima Al-Hassan — IV to oral antibiotic switch",                "urgent": False},
    {"text": "Update ward teaching schedule for next week",                    "urgent": False},
    {"text": "Complete monthly equipment audit form",                          "urgent": False},
    {"text": "Reply to GP referral letters — 4 pending",                       "urgent": False},
    {"text": "Update staff rota for bank holiday",                             "urgent": False},
]

DELEGATABLE = [
    "Bed request form — Ward B (Margaret Thornton step-down)",
    "Appointment letter — James Okafor cardiology follow-up",
    "Supply requisition — Ward C catheter supplies",
    "Filing — 6 completed discharge summaries",
    "Catering update — Robert Adeniran NBM from midnight",
]

DEFERRABLE = [
    "Monthly audit report — due end of week",
    "Training record update — mandatory e-learning",
    "Equipment maintenance log",
    "GP correspondence — 4 non-urgent letters",
]

PRESSURE_EVENTS = [
    ("New EW EMER. admission — Ward C",           "occupancy",     7, "critical"),
    ("2 additional handovers flagged urgent",       "handover",      6, "warning"),
    ("Lab results delayed — 4 patients waiting",   "documentation", 5, "warning"),
    ("Bed manager requesting urgent bed review",    "occupancy",     6, "warning"),
    ("Night nurse calling in sick — short staffed","occupancy",     8, "critical"),
    ("8 more notes overdue from morning round",    "documentation", 8, "warning"),
    ("Family meeting request — 3 patients",        "handover",      5, "warning"),
    ("ICU escalation — patient deteriorating",     "occupancy",     9, "critical"),
    ("Registrar called to emergency — cover gap",  "handover",      7, "warning"),
    ("Pharmacy query — Warfarin dose change",      "documentation", 4, "warning"),
]

SCAFFOLDS = [
    {"name": "Auto-sort patients by acuity",         "trigger": 50, "icon": "📋", "time_saved": 15, "desc": "Patient list re-ranked by XGBoost risk. Highest risk shown first."},
    {"name": "Delegate routine admin to admin staff", "trigger": 60, "icon": "📝", "time_saved": 25, "desc": "Non-clinical tasks routed to admin. Clinician freed from paperwork."},
    {"name": "Filter to top 3 urgent decisions only", "trigger": 70, "icon": "⚡", "time_saved": 20, "desc": "Decision queue filtered. Only 3 most urgent shown. Rest queued."},
    {"name": "Defer all non-urgent admin until 14:00","trigger": 80, "icon": "⏰", "time_saved": 30, "desc": "Non-urgent tasks deferred to afternoon. Morning protected for clinical work."},
]

# Session state
if "factors" not in st.session_state:
    st.session_state.factors = {
        "Occupancy pressure":    {"value": 18, "max": 40, "color": "#38BDF8"},
        "Documentation backlog": {"value": 12, "max": 30, "color": "#F59E0B"},
        "Handover pressure":     {"value": 15, "max": 30, "color": "#EF4444"},
    }
for k, v in [("scaffolds_on",[]),("delegated",set()),("deferred",set()),
              ("events",[]),("history",[]),("auto_running",False),
              ("auto_start",None),("pressure_idx",0)]:
    if k not in st.session_state: st.session_state[k] = v

def add_event(text, etype="info"):
    # Map pressure index to shift time starting at 07:00
    shift_mins = 7 * 60 + st.session_state.get("pressure_idx", 0) * 8
    shift_h = min(shift_mins // 60, 18)
    shift_m = shift_mins % 60
    shift_time = f"{shift_h:02d}:{shift_m:02d}"
    st.session_state.events.append({
        "time": shift_time,
        "real_time": datetime.datetime.now().strftime("%H:%M:%S"),
        "text": text, "type": etype
    })

def recalc():
    return min(100, sum(f["value"] for f in st.session_state.factors.values()))

def apply_pressure():
    idx = st.session_state.pressure_idx % len(PRESSURE_EVENTS)
    ev  = PRESSURE_EVENTS[idx]
    st.session_state.pressure_idx += 1
    fm  = {"occupancy": "Occupancy pressure", "documentation": "Documentation backlog", "handover": "Handover pressure"}
    key = fm.get(ev[1], "Occupancy pressure")
    st.session_state.factors[key]["value"] = min(st.session_state.factors[key]["max"], st.session_state.factors[key]["value"] + ev[2])
    add_event(f"⚠️ {ev[0]}", ev[3])

def activate_scaffolds(nasa):
    new = [s for s in SCAFFOLDS if nasa >= s["trigger"] and s["name"] not in st.session_state.scaffolds_on]
    for s in new:
        st.session_state.scaffolds_on.append(s["name"])
        add_event(f"🤖 Scaffold activated: {s['name']} — saves ~{s['time_saved']} mins", "ai")

# Header
st.markdown("""
<div style="background:#161B22;border-bottom:1px solid #30363D;padding:14px 24px;margin:-1rem -1rem 1rem -1rem;display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;">🧠 Cognitive Support Agent — Live Simulation</div>
        <div style="font-size:0.78rem;color:#8B949E;margin-top:2px;">NASA-TLX builds automatically · Scaffolding activates at thresholds · Before/After visible · Recovery arc tracked</div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#8B949E;">Royal London Hospital · Sister Amara's Shift<br>LD7326 · W25041744 · Northumbria University</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""<div style="background:#1A1A0A;border:1px solid #F59E0B;border-radius:6px;padding:8px 14px;margin-bottom:12px;font-size:0.73rem;color:#D4A520;">
⚖️ <b>Research Simulation:</b> All patients and scenarios are fictional. No real NHS data used. GDPR · DCB0129/DCB0160 · W25041744
</div>""", unsafe_allow_html=True)

# Controls
c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    if st.button("📈 Add Pressure Event"):
        apply_pressure(); nasa=recalc(); activate_scaffolds(nasa); st.session_state.history.append(nasa); st.rerun()
with c2:
    auto = st.toggle("🔄 Auto-pressure", value=st.session_state.auto_running)
    if auto and not st.session_state.auto_running: st.session_state.auto_start = datetime.datetime.now()
    st.session_state.auto_running = auto
with c3:
    if st.button("✅ Reduce Load"):
        for k in st.session_state.factors:
            st.session_state.factors[k]["value"] = max(5, st.session_state.factors[k]["value"] - random.randint(6,12))
        nasa = recalc()
        st.session_state.history.append(nasa)
        add_event(f"✅ Load reduced — NASA-TLX now {nasa}/100", "success")
        # De-escalate scaffolds that are no longer needed
        to_remove = [s["name"] for s in SCAFFOLDS
                     if s["name"] in st.session_state.scaffolds_on and nasa < s["trigger"]]
        for name in to_remove:
            st.session_state.scaffolds_on.remove(name)
            add_event(f"📉 Scaffold de-activated: {name} — load below threshold", "info")
        st.rerun()
with c4:
    if st.button("🧠 Activate All Scaffolds"):
        nasa=recalc(); activate_scaffolds(max(nasa,85)); st.session_state.history.append(nasa); st.rerun()
with c5:
    if st.button("🔄 Reset"):
        for k in ["factors","scaffolds_on","delegated","deferred","events","history","auto_running","auto_start","pressure_idx"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

st.divider()

# Auto-pressure
if st.session_state.auto_running and st.session_state.auto_start:
    elapsed = (datetime.datetime.now() - st.session_state.auto_start).total_seconds()
    if int(elapsed/8) > st.session_state.pressure_idx:
        apply_pressure(); nasa=recalc(); activate_scaffolds(nasa); st.session_state.history.append(nasa)

# Current state
nasa = recalc()
if nasa > 75:   load_label,load_color = "CRITICAL","#EF4444"
elif nasa > 60: load_label,load_color = "HIGH","#F59E0B"
elif nasa > 40: load_label,load_color = "MODERATE","#38BDF8"
else:           load_label,load_color = "LOW","#22C55E"

scaffolds_active = [s for s in SCAFFOLDS if s["name"] in st.session_state.scaffolds_on]
sort_patients    = any(s["trigger"]==50 for s in scaffolds_active)
filter_decisions = any(s["trigger"]==70 for s in scaffolds_active)
defer_admin      = any(s["trigger"]==80 for s in scaffolds_active)
time_saved       = sum(s["time_saved"] for s in scaffolds_active) + len(st.session_state.delegated)*5 + len(st.session_state.deferred)*10

# Metrics
m1,m2,m3,m4,m5,m6 = st.columns(6)
m1.metric("NASA-TLX",      f"{nasa}/100",  load_label)
m2.metric("Scaffolds",     str(len(scaffolds_active)), f"of {len(SCAFFOLDS)}")
m3.metric("Delegated",     str(len(st.session_state.delegated)))
m4.metric("Deferred",      str(len(st.session_state.deferred)))
m5.metric("Time Saved",    f"{time_saved} mins")
m6.metric("Pressure Events",str(st.session_state.pressure_idx))

st.divider()

col_g,col_m,col_r = st.columns([1,2,1])

with col_g:
    st.markdown(f"""<div class="gauge-box" style="border-color:{load_color};">
        <div style="font-size:0.7rem;color:#8B949E;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">NASA Task Load Index</div>
        <div class="gauge-number" style="color:{load_color};">{nasa}</div>
        <div class="gauge-label" style="color:{load_color};">{load_label}</div>
        <div class="gauge-bar-bg"><div class="gauge-bar" style="width:{nasa}%;background:{load_color};"></div></div>
        <div style="font-size:0.7rem;color:#8B949E;">
            {'🚨 Scaffolding active' if scaffolds_active else '⚠️ Approaching threshold' if nasa>40 else '✅ Safe range'}
        </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("&nbsp;")

    st.markdown("**Contributing Factors:**")
    for name,data in st.session_state.factors.items():
        pct = int(data["value"]/data["max"]*100)
        st.markdown(f"""<div class="factor-row">
            <div style="display:flex;justify-content:space-between;">
                <span style="font-size:0.75rem;font-weight:600;color:#C9D1D9;">{name}</span>
                <span style="font-size:0.8rem;font-weight:800;color:{data['color']};">{data['value']}/{data['max']}</span>
            </div>
            <div class="factor-mini-bg"><div class="factor-mini" style="width:{pct}%;background:{data['color']};"></div></div>
        </div>""", unsafe_allow_html=True)

    if len(st.session_state.history) > 1:
        st.markdown("&nbsp;")
        st.markdown("**Recovery Arc:**")
        history = st.session_state.history[-20:]
        chart_html = '<div style="display:flex;align-items:flex-end;gap:2px;height:60px;padding:0 2px;">'
        for val in history:
            pct_h = int(val/100*100)
            color = "#EF4444" if val>75 else "#F59E0B" if val>60 else "#38BDF8" if val>40 else "#22C55E"
            chart_html += f'<div style="flex:1;height:{pct_h}%;background:{color};border-radius:2px 2px 0 0;min-height:3px;transition:height 0.5s;"></div>'
        chart_html += f'</div><div style="font-size:0.62rem;color:#6E7681;text-align:right;margin-top:2px;">Current: {nasa}/100</div>'
        st.markdown(chart_html, unsafe_allow_html=True)

with col_m:
    # Show dramatic banner when new scaffold fires
    if len(scaffolds_active) > 0:
        latest = scaffolds_active[-1]
        st.markdown(f"""
        <div style="background:#0D1F33;border:2px solid #38BDF8;border-radius:8px;
        padding:12px 16px;margin-bottom:10px;animation:fadeIn 0.5s ease;">
            <div style="font-size:0.85rem;font-weight:800;color:#38BDF8;">
                {latest['icon']} SCAFFOLD ACTIVATED — {latest['name'].upper()}
            </div>
            <div style="font-size:0.78rem;color:#93C5FD;margin-top:4px;">
                {latest['desc']} · Estimated {latest['time_saved']} minutes returned to clinical work.
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("### 👁 Before AI vs With AI")
    b1,b2 = st.columns(2)
    with b1:
        st.markdown(f"""<div class="ba-card" style="border-color:#EF4444;">
            <div class="ba-title" style="color:#EF4444;">❌ Without AI — NASA-TLX {nasa}/100</div>
            <div class="ba-item">🧠 Doctor carries all priorities in head</div>
            <div class="ba-item">📋 No sorting — manual re-prioritisation every time</div>
            <div class="ba-item">📝 All 12 decisions in one overwhelming queue</div>
            <div class="ba-item">⏰ Admin and clinical tasks mixed together</div>
            <div class="ba-item">📞 Every query reaches the doctor directly</div>
            <div class="ba-item" style="font-weight:800;color:#FCA5A5;border:none;margin-top:6px;">
                Result: {load_label} cognitive load · Errors more likely
            </div>
        </div>""", unsafe_allow_html=True)
    with b2:
        ai_nasa = max(20, nasa - time_saved//3)
        ai_label = "MODERATE" if ai_nasa <= 60 else "HIGH" if ai_nasa <= 75 else "CRITICAL"
        ai_color = "#22C55E" if ai_nasa <= 60 else "#F59E0B" if ai_nasa <= 75 else "#EF4444"
        sl = "✅ Auto-sorted by XGBoost risk" if sort_patients else f"⏳ Activates at NASA-TLX >50 (now {nasa})"
        fl = "✅ Filtered to 3 urgent items" if filter_decisions else f"⏳ Activates at NASA-TLX >70 (now {nasa})"
        dl = f"✅ {len(st.session_state.delegated)} tasks delegated to admin" if st.session_state.delegated else f"⏳ Activates at NASA-TLX >60 (now {nasa})"
        de = f"✅ {len(st.session_state.deferred)} tasks deferred to 14:00" if st.session_state.deferred else f"⏳ Activates at NASA-TLX >80 (now {nasa})"
        st.markdown(f"""<div class="ba-card" style="border-color:{ai_color};">
            <div class="ba-title" style="color:{ai_color};">✅ With AI — NASA-TLX ~{ai_nasa}/100</div>
            <div class="ba-item">{sl}</div>
            <div class="ba-item">{fl}</div>
            <div class="ba-item">{dl}</div>
            <div class="ba-item">{de}</div>
            <div class="ba-item">✅ Routine queries auto-resolved by Coordination Agent</div>
            <div class="ba-item" style="font-weight:800;color:{ai_color};border:none;margin-top:6px;">
                Result: {ai_label} cognitive load · {time_saved} mins saved
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown("### 👥 Patient List")
    if sort_patients:
        st.caption("✅ AI-sorted by XGBoost risk — highest risk at top")
        pts = sorted(PATIENTS, key=lambda x: x["risk"], reverse=True)
    else:
        st.caption("⏳ Default order — AI sorting activates at NASA-TLX >50")
        pts = PATIENTS
    for i,p in enumerate(pts):
        nf = "📝" if p["note_due"] else ""
        uf = "🚨" if p["urgent"] else ""
        rk = f"#{i+1}" if sort_patients else "•"
        rc = "#EF4444" if p["risk"]>0.7 else "#F59E0B" if p["risk"]>0.4 else "#22C55E"
        st.markdown(f"""<div class="patient-row {p['priority']}">
            <span style="font-weight:800;color:#8B949E;min-width:28px;">{rk}</span>
            <span style="font-weight:700;color:#E6EDF3;flex:1;">{p['name']}</span>
            <span style="font-size:0.72rem;color:#8B949E;">{p['ward']}</span>
            <span style="font-size:0.75rem;font-weight:700;color:{rc};">{p['risk']:.0%}</span>
            <span>{uf}{nf}</span>
        </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📋 Decision Queue")
    if filter_decisions:
        urgent_q  = [d for d in DECISIONS_ALL if d["urgent"]][:3]
        queued_q  = [d for d in DECISIONS_ALL if not d["urgent"] and not (defer_admin and any(kw in d["text"].lower() for kw in ["teaching","audit","equipment","gp","rota"]))]
        deferred_q= [d for d in DECISIONS_ALL if not d["urgent"] and defer_admin and any(kw in d["text"].lower() for kw in ["teaching","audit","equipment","gp","rota"])]
        st.caption(f"✅ Filtered — {len(urgent_q)} urgent · {len(queued_q)} queued · {len(deferred_q)} deferred")
    else:
        urgent_q   = [d for d in DECISIONS_ALL if d["urgent"]]
        queued_q   = [d for d in DECISIONS_ALL if not d["urgent"]]
        deferred_q = []
        st.caption("⏳ Full queue — AI filtering activates at NASA-TLX >70")

    if urgent_q:
        st.markdown("**🔴 Urgent — act now:**")
        for d in urgent_q: st.markdown(f'<div class="decision-item urgent">🔴 {d["text"]}</div>', unsafe_allow_html=True)
    if queued_q:
        st.markdown("**🔵 Queued:**")
        for d in queued_q[:4]: st.markdown(f'<div class="decision-item queued">○ {d["text"]}</div>', unsafe_allow_html=True)
    if deferred_q:
        st.markdown("**⏰ Deferred to 14:00:**")
        for d in deferred_q: st.markdown(f'<div class="decision-item deferred">⏰ {d["text"]}</div>', unsafe_allow_html=True)

with col_r:
    st.markdown("### ⚡ Scaffolding")
    for s in SCAFFOLDS:
        is_on = s["name"] in st.session_state.scaffolds_on
        css   = "active" if is_on else "waiting"
        color = "#38BDF8" if is_on else "#6E7681"
        st.markdown(f"""<div class="scaffold {css}">
            <div style="font-size:1rem;">{s['icon']}</div>
            <div style="font-size:0.78rem;font-weight:700;color:{'#E6EDF3' if is_on else '#8B949E'};margin:3px 0;">{s['name']}</div>
            <div style="font-size:0.68rem;color:{color};">{'✅ ACTIVE — saves ' + str(s['time_saved']) + ' mins' if is_on else 'Activates at >' + str(s['trigger'])}</div>
            {'<div style="font-size:0.68rem;color:#6E7681;margin-top:3px;">' + s['desc'] + '</div>' if is_on else ''}
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("**📤 Delegate:**")
    for task in DELEGATABLE:
        done = task in st.session_state.delegated
        tc,bc = st.columns([3,1])
        tc.markdown(f'<div style="font-size:0.72rem;color:{"#6E7681" if done else "#C9D1D9"};padding:3px 0;{"text-decoration:line-through;" if done else ""}">{"✅" if done else "○"} {task[:35]}...</div>', unsafe_allow_html=True)
        if not done:
            if bc.button("→", key=f"del_{task}"):
                st.session_state.delegated.add(task); add_event(f"✅ Delegated: {task[:30]}...","success"); st.rerun()

    st.divider()
    st.markdown("**⏰ Defer to 14:00:**")
    for task in DEFERRABLE:
        done = task in st.session_state.deferred
        tc,bc = st.columns([3,1])
        tc.markdown(f'<div style="font-size:0.72rem;color:{"#6E7681" if done else "#C9D1D9"};padding:3px 0;{"text-decoration:line-through;" if done else ""}">{"⏰" if done else "○"} {task}</div>', unsafe_allow_html=True)
        if not done:
            if bc.button("→", key=f"def_{task}"):
                st.session_state.deferred.add(task); add_event(f"⏰ Deferred: {task}","success"); st.rerun()

    st.divider()
    st.markdown("**📡 Events:**")
    colors = {"ai":"#A855F7","warning":"#F59E0B","critical":"#EF4444","success":"#22C55E","info":"#38BDF8"}
    if not st.session_state.events:
        st.caption("Add pressure to see events")
    else:
        for ev in reversed(st.session_state.events[-8:]):
            color = colors.get(ev["type"],"#38BDF8")
            st.markdown(f'<div class="ev {ev["type"]}"><span style="color:#8B949E;font-weight:600;">{ev["time"]}</span> <span style="color:#6E7681;font-size:0.65rem;">({ev.get("real_time","")})</span><br><span style="color:#C9D1D9;">{ev["text"]}</span></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""<div style="font-size:0.7rem;color:#8B949E;line-height:1.7;">
        <b>Feasibility result:</b><br>
        Load reduction: -25.4%<br>Cohen's d = 1.829<br>p &lt; 0.000001<br><br>
        <b>Arab et al. (2025):</b><br>NHS doctors: 17.9% patient time.<br>73% admin overhead. This agent targets that.
    </div>""", unsafe_allow_html=True)

if st.session_state.auto_running:
    time.sleep(2); st.rerun()

st.divider()
context_lines = [f"- NASA-TLX score: {nasa}/100 ({load_label})"]
for name, data in st.session_state.factors.items():
    context_lines.append(f"- {name}: {data['value']}/{data['max']}")
context_lines.append(f"- Scaffolds active: {len(scaffolds_active)} of {len(SCAFFOLDS)}")
context_lines.append(f"- Tasks delegated: {len(st.session_state.delegated)}, deferred: {len(st.session_state.deferred)}")
live_context = "\n".join(context_lines)
render_chatbot("Cognitive Support Agent", live_context, key_prefix="cognitive_agent")

st.divider()
st.markdown('<div style="text-align:center;font-size:0.72rem;color:#6E7681;padding:6px 0;">NHS AI Platform — Cognitive Support Agent v2 · LD7326 · W25041744 · Northumbria University · All scenarios fictional · DCB0129/DCB0160 compliant</div>', unsafe_allow_html=True)