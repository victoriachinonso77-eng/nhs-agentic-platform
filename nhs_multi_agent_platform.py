"""
NHS AI Platform  Unified Multi-Agent System
All seven agents share ONE ward state. Actions in one agent are
immediately visible to the others via the Cross-Agent Handoff Log.

LD7326 | MSc Artificial Intelligence Technology | W25041744
Run: streamlit run nhs_multi_agent_platform.py
"""

import streamlit as st
import datetime
import time
import random
from dotenv import load_dotenv
from chatbot_helper import render_chatbot
from shared_state import (
    WARDS, init_shared_state, get_patient, log_handoff,
    recalc_overdue_docs, recalc_nasa_tlx,
    run_full_cycle, apply_recommendation
)
from ai_agents import run_full_cycle_ai

load_dotenv()

st.set_page_config(page_title="NHS AI  Multi-Agent Platform", page_icon="🏥", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700;900&family=Source+Sans+Pro:wght@400;600;700&display=swap');
* { font-family: 'Source Sans Pro', 'Segoe UI', sans-serif; box-sizing: border-box; }
h1, h2, h3, h4, .stApp b, .stMarkdown b { font-family: 'Merriweather', Georgia, serif; }
.stApp { background: #EAEFF5; color: #1A2332; }
[data-testid="stSidebar"] { background: #F3F6FA; border-right: 1px solid #D1D9E0; }
#MainMenu, footer { visibility: hidden; }

[data-testid="metric-container"] { background: #FFFEF9; border: 1px solid #D1D9E0; border-radius: 6px; padding: 12px !important; box-shadow: 0 1px 2px rgba(26,35,50,0.06); }
[data-testid="metric-container"] label { color: #5A6B7D !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.04em; }
[data-testid="metric-container"] label p { color: #5A6B7D !important; }
[data-testid="stMetricLabel"] p { color: #5A6B7D !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #1F4E79 !important; font-size: 1.4rem !important; font-weight: 700 !important; font-family: 'Merriweather', Georgia, serif !important; }
[data-testid="stMetricValue"] div { color: #1F4E79 !important; }

/* Widget labels (selectbox, text input, etc.)  same dark-theme-default
   issue: Streamlit wraps the label text in its own <p>, which needs to
   be targeted directly, not just the parent element. */
[data-testid="stWidgetLabel"] p { color: #1A2332 !important; font-weight: 600; }
.stSelectbox label, .stSelectbox label p { color: #1A2332 !important; }

/* Chat input  native Streamlit component, never styled, was retaining
   dark-theme defaults (dark fill, invisible dark-on-dark typed text). */
[data-testid="stChatInput"] { background: #FFFEF9 !important; border: 1px solid #D1D9E0 !important; border-radius: 6px !important; }
[data-testid="stChatInput"] textarea { background: #FFFEF9 !important; color: #1A2332 !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #7A8896 !important; }
[data-testid="stChatMessage"] { background: #FFFEF9 !important; border: 1px solid #D1D9E0 !important; border-radius: 6px !important; }
[data-testid="stChatMessage"] p { color: #1A2332 !important; }

.handoff-card { border-left: 3px solid #6B4E8C; background: #FFFEF9; border: 1px solid #D1D9E0; border-left-width: 3px; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 4px 4px 0; font-size: 0.78rem; box-shadow: 0 1px 2px rgba(26,35,50,0.05); animation: fadeIn 0.4s ease; }
.handoff-card.critical { border-left-color: #B91C1C; }
.handoff-card.success  { border-left-color: #1F7A4D; }
.ward-pill { display: inline-block; padding: 3px 10px; border-radius: 3px; font-size: 0.72rem; font-weight: 700; margin: 2px; }
.patient-card { background: #FFFEF9; border: 1px solid #D1D9E0; border-radius: 6px; padding: 10px 14px; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(26,35,50,0.05); }

.stButton > button { background: #1F4E79 !important; color: #FFF !important; border: none !important; border-radius: 4px !important; font-weight: 600 !important; }

/* Tabs Streamlit's defaults are styled for a dark theme and were
   invisible against the new light background. Force explicit colors
   for both the inactive and active tab states. */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { color: #5A6B7D !important; font-weight: 600; }
.stTabs [data-baseweb="tab"] p { color: #5A6B7D !important; }
.stTabs [aria-selected="true"] { color: #1F4E79 !important; }
.stTabs [aria-selected="true"] p { color: #1F4E79 !important; font-weight: 700; }

/* Expanders — same issue: default header background/text was designed
   for dark mode and rendered as an unreadable dark bar on light theme. */
[data-testid="stExpander"] { background: #FFFEF9; border: 1px solid #D1D9E0; border-radius: 6px; }
[data-testid="stExpander"] summary { background: #FFFEF9 !important; color: #1A2332 !important; }
[data-testid="stExpander"] summary p { color: #1A2332 !important; font-weight: 600; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { background: #FFFEF9; color: #1A2332; }

/* Sidebar — explicit text color safety net, same root cause as tabs/expanders */
[data-testid="stSidebar"] * { color: #1A2332; }
[data-testid="stSidebar"] .handoff-card span { color: inherit; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)

init_shared_state()

# ─Login gate ────────────────────────────────────────────────────────
# Not real NHS smartcard authentication a lightweight name-picker so
# every approval/rejection in the audit trail is attributable to a
# specific clinician, demonstrating the accountability principle the
# dissertation names, without building actual identity infrastructure.
NHS_STAFF_PINS = {
    "Dr. A. Okonkwo  Consultant": "4471",
    "Dr. R. Patel  SHO": "2839",
    "Sister A. Mbeki  Ward Sister": "9102",
    "Nurse J. Kowalski  Staff Nurse": "5566",
}
NHS_STAFF = list(NHS_STAFF_PINS.keys())

if "failed_login_attempts" not in st.session_state:
    st.session_state.failed_login_attempts = 0
if "login_step" not in st.session_state:
    st.session_state.login_step = "tap_card"   # "tap_card" -> "enter_pin"
if "tapped_card" not in st.session_state:
    st.session_state.tapped_card = None

if not st.session_state.current_user:
    st.markdown("""<div style="max-width:520px;margin:50px auto 0 auto;text-align:center;">
        <div style="font-size:1.4rem;font-weight:800;color:#1F4E79;font-family:'Merriweather',serif;">
            🏥 NHS AI Platform
        </div>
        <div style="font-size:0.85rem;color:#5A6B7D;margin-top:4px;margin-bottom:24px;">
            Royal London Hospital
        </div>
    </div>""", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2.4, 1])

    #  STEP 1: Tap NHS Smartcard ────────────────────────────────
    if st.session_state.login_step == "tap_card":
        with col_b:
            st.markdown("""<div style="text-align:center;margin-bottom:16px;">
                <span style="background:#EAF1F8;border:1px solid #1F4E79;border-radius:6px;
                padding:4px 12px;font-size:0.75rem;color:#1F4E79;font-weight:700;">
                    💳 STEP 1 OF 2  TAP SMARTCARD
                </span>
            </div>""", unsafe_allow_html=True)
            st.caption("Tap your NHS smartcard on the reader  select your card below.")
            for name in NHS_STAFF:
                role = name.split("—")[-1].strip()
                short = name.split("—")[0].strip()
                if st.button(f"💳  {short}  ·  {role}", key=f"tap_{name}", use_container_width=True):
                    with st.spinner("Reading smartcard..."):
                        time.sleep(0.9)
                    st.session_state.tapped_card = name
                    st.session_state.login_step = "enter_pin"
                    st.rerun()
            st.caption("⚠️ Demo simulation  no real smartcard reader hardware involved.")

    # ── STEP 2: Enter PIN ─────────────────────────────────────────
    else:
        with col_b:
            st.markdown("""<div style="text-align:center;margin-bottom:16px;">
                <span style="background:#EAF1F8;border:1px solid #1F4E79;border-radius:6px;
                padding:4px 12px;font-size:0.75rem;color:#1F4E79;font-weight:700;">
                    🔢 STEP 2 OF 2  ENTER PIN
                </span>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="background:#FFFEF9;border:1px solid #D1D9E0;border-radius:6px;
            padding:10px 14px;margin-bottom:14px;text-align:center;">
                💳 Card identified: <b style="color:#1F4E79;">{st.session_state.tapped_card}</b>
            </div>""", unsafe_allow_html=True)

            choice = st.session_state.tapped_card
            pin = st.text_input("PIN", type="password", max_chars=4)

            if st.session_state.failed_login_attempts >= 3:
                st.error("🔒 Account locked — too many failed attempts. Security Agent has been notified.")
                if st.button("🔧 Reset lockout (demo only)", use_container_width=True):
                    st.session_state.failed_login_attempts = 0
                    st.rerun()
            elif st.button("Sign in", use_container_width=True):
                if pin == NHS_STAFF_PINS.get(choice):
                    st.session_state.current_user = choice
                    st.session_state.failed_login_attempts = 0
                    st.session_state.login_step = "tap_card"
                    from shared_state import log_handoff
                    log_handoff("Login System", "Command Centre",
                                f"{choice} signed in successfully via smartcard + PIN", "success")
                    st.rerun()
                else:
                    st.session_state.failed_login_attempts += 1
                    remaining = 3 - st.session_state.failed_login_attempts
                    if remaining > 0:
                        st.error(f"❌ Incorrect PIN  {remaining} attempt(s) remaining before lockout")
                    else:
                        from shared_state import log_handoff
                        st.session_state.security_threat_level = "HIGH"
                        log_handoff("Security Agent", "Clinician Review Queue",
                                    f"⚠️ 3 failed sign-in attempts for '{choice}'  account locked, "
                                    f"possible unauthorised access attempt flagged for review", "critical")
                        st.rerun()

            if st.button("← Use a different card", use_container_width=True):
                st.session_state.login_step = "tap_card"
                st.session_state.tapped_card = None
                st.rerun()

            st.caption("⚠️ Demo login only  smartcard tap + PIN check, not real NHS cryptographic authentication.")
            with st.expander("Demo credentials (testing only)"):
                for name, demo_pin in NHS_STAFF_PINS.items():
                    st.caption(f"{name} — PIN: {demo_pin}")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#FFFFFF;border-bottom:1px solid #D1D9E0;padding:14px 24px;
margin:-1rem -1rem 1rem -1rem;display:flex;justify-content:space-between;align-items:center;">
    <div>
        <div style="font-size:1.3rem;font-weight:800;color:#1A2332;">🏥 NHS AI Platform — Unified Multi-Agent System</div>
        <div style="font-size:0.78rem;color:#5A6B7D;margin-top:2px;">
            Seven agents · One shared ward state · Every action visible across agents
        </div>
    </div>
    <div style="text-align:right;font-size:0.75rem;color:#5A6B7D;">
        Royal London Hospital · Live Shift<br>LD7326 · W25041744 · Northumbria University
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""<div style="background:#FEF3E2;border:2px solid #B45309;border-radius:6px;
padding:12px 16px;margin-bottom:14px;font-size:0.85rem;color:#7A4A05;font-weight:600;">
⚖️ RESEARCH SIMULATION  All patients and scenarios are fictional. No real NHS data is used at any stage.
GDPR · DCB0129/DCB0160 · W25041744
</div>""", unsafe_allow_html=True)

# ── Cross-agent handoff log — sidebar, visible from every tab ──────────
with st.sidebar:
    st.markdown(f"""<div style="background:#EAF1F8;border:1px solid #1F4E79;border-radius:6px;
    padding:8px 12px;margin-bottom:12px;font-size:0.78rem;">
        👤 <b>{st.session_state.current_user}</b>
    </div>""", unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()
    st.divider()

    st.markdown("### 🔗 Cross-Agent Handoff Log")
    st.caption("Actions from any agent, visible to all")
    if not st.session_state.handoff_log:
        st.caption("No handoffs yet interact with an agent tab")
    else:
        for h in reversed(st.session_state.handoff_log[-15:]):
            css = h["level"]
            st.markdown(
                f'<div class="handoff-card {css}">'
                f'<span style="color:#5A6B7D;">{h["time"]}</span> · '
                f'<span style="color:#1F4E79;font-weight:600;">👤 {h.get("clinician", "Not logged in")}</span><br>'
                f'<b>{h["from"]}</b> → <b>{h["to"]}</b><br>'
                f'{h["message"]}</div>',
                unsafe_allow_html=True
            )
    st.divider()
    st.metric("Total Handoffs", len(st.session_state.handoff_log))
    if st.button("🔄 Reset Entire Platform"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Tabs — one per agent, all reading the SAME shared state ───────────
tab_overview, tab_doc, tab_handover, tab_workflow, tab_cognitive, tab_integration, tab_coord, tab_security = st.tabs(
    ["🏠 Overview", "📝 Documentation", "🤝 Handover", "⚡ Workflow", "🧠 Cognitive Support",
     "🔗 Integration", "📞 Coordination", "🔒 Security"]
)

# ═══════════════════════════════════════════════════════════════════════
# OVERVIEW TAB — shared ward/patient state, the single source of truth
# ═══════════════════════════════════════════════════════════════════════
with tab_overview:
    st.markdown("### Command Centre")

    with st.expander("ℹ️ How the two run modes work"):
        st.caption(
            "**Deterministic**  instant, rule-based, matches the sub-second cycle tested in the dissertation.  \n"
            "**GPT-4o**  each agent reasons independently via a real API call, a few seconds, needs OPENAI_API_KEY."
        )

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("▶ Run Full Cycle  Deterministic", key="run_cycle", use_container_width=True):
            run_full_cycle()
            st.rerun()
    with bc2:
        if st.button("🤖 Run Full Cycle  GPT-4o", key="run_cycle_ai", use_container_width=True):
            with st.spinner("Calling GPT-4o for all 7 agents..."):
                succeeded, failed, elapsed = run_full_cycle_ai()
            if failed > 0:
                st.error(f"⚠️ {failed}/7 failed  {elapsed:.2f}s")
            else:
                st.success(f" 7/7 in {elapsed:.2f}s")
            st.rerun()

    if st.session_state.pending_recommendations:
        st.markdown(f"#### 📋 Pending Review ({len(st.session_state.pending_recommendations)})")
        for rec in list(st.session_state.pending_recommendations):
            st.markdown(f"""<div class="patient-card" style="border-color:#B45309;">
                <span style="font-size:0.68rem;color:#B45309;font-weight:700;text-transform:uppercase;">{rec['agent']}</span><br>
                <b style="font-size:0.95rem;">{rec['summary']}</b>
            </div>""", unsafe_allow_html=True)
            with st.expander("Why?", expanded=False):
                st.caption(rec["rationale"])
            rc1, rc2 = st.columns(2)
            if rc1.button(" Approve", key=f"approve_{rec['id']}", use_container_width=True):
                apply_recommendation(rec)
                st.session_state.pending_recommendations.remove(rec)
                st.rerun()
            if rc2.button("❌ Reject", key=f"reject_{rec['id']}", use_container_width=True):
                log_handoff(rec["agent"], "Clinician Review Queue",
                            f"[Rejected] {rec['summary']}", "critical")
                st.session_state.pending_recommendations.remove(rec)
                st.rerun()
        if st.button("✅ Approve All", use_container_width=True):
            for rec in list(st.session_state.pending_recommendations):
                apply_recommendation(rec)
            st.session_state.pending_recommendations = []
            st.rerun()

    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Occupancy", f"{st.session_state.occupancy}%")
    m2.metric("Overdue", st.session_state.overdue_docs)
    m3.metric("NASA-TLX", f"{recalc_nasa_tlx()}")
    m4.metric("Saved", f"{st.session_state.coord_time_saved}m")
    m5.metric("Threat", st.session_state.security_threat_level)

    st.divider()
    st.markdown("#### Ward Risk")
    st.caption("XGBoost bottleneck predictions (AUC-ROC 0.8542)")
    ward_cols = st.columns(len(WARDS))
    for i, (wname, wdata) in enumerate(WARDS.items()):
        risk = st.session_state.shared_ward_risk[wname]
        color = "#B91C1C" if risk > 0.7 else "#B45309" if risk > 0.4 else "#1F7A4D"
        with ward_cols[i]:
            st.markdown(f"""<div class="patient-card" style="border-color:{color};text-align:center;padding:8px 4px;">
                <div style="font-size:1.5rem;font-weight:800;color:{color};">{risk:.0%}</div>
                <div style="font-size:0.68rem;color:#5A6B7D;">{wname}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Patient Roster")
    for p in sorted(st.session_state.shared_patients, key=lambda x: x["priority"]):
        risk_color = "#B91C1C" if p["risk_score"] > 0.7 else "#B45309" if p["risk_score"] > 0.4 else "#1F7A4D"
        doc_icon = "✅" if p["documented"] else "📝"
        sbar_icon = "✅" if all(p["sbar"].values()) else "⚠️"
        st.markdown(f"""<div class="patient-card" style="padding:8px 12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <b>{p['name']}</b>
                    <span style="font-size:0.72rem;color:#5A6B7D;"> · {p['ward']} {p['bed']} · {doc_icon} {sbar_icon}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-weight:800;color:{risk_color};">{p['risk_score']:.0%}</span>
                    <span style="font-size:0.68rem;color:#5A6B7D;"> P{p['priority']}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    render_chatbot(
        "Command Centre (all 7 agents)",
        f"Occupancy: {st.session_state.occupancy}%. Overdue docs: {st.session_state.overdue_docs}. "
        f"NASA-TLX: {recalc_nasa_tlx()}/100. Total handoffs logged: {len(st.session_state.handoff_log)}.",
        key_prefix="overview_agent"
    )

# ═══════════════════════════════════════════════════════════════════════
# DOCUMENTATION AGENT  drafts SBAR notes, feeds Handover + Cognitive
# ═══════════════════════════════════════════════════════════════════════
with tab_doc:
    st.markdown("### 📝 Documentation Agent")
    st.caption("Updates the shared patient record")

    pending = [p for p in st.session_state.shared_patients if p["note_due"] and not p["documented"]]
    st.metric("Overdue Notes", len(pending))

    if not pending:
        st.success(" All notes up to date.")
    for p in pending:
        with st.container():
            st.markdown(f"""<div class="patient-card">
                <b>{p['name']}</b> — {p['ward']} {p['bed']} · Risk {p['risk_score']:.0%}<br>
                <span style="font-size:0.75rem;color:#5A6B7D;">{p['diagnosis'][:45]}...</span>
            </div>""", unsafe_allow_html=True)
            if st.button(f"🤖 Draft SBAR note  {p['name']}", key=f"doc_{p['name']}"):
                p["documented"] = True
                p["sbar"]["situation"] = True
                p["sbar"]["background"] = True
                recalc_overdue_docs()
                log_handoff("Documentation Agent", "Handover Agent",
                            f"Note drafted for {p['name']} Situation and Background sections now complete",
                            "success")
                log_handoff("Documentation Agent", "Cognitive Support Agent",
                            f"Overdue notes now {st.session_state.overdue_docs} cognitive load recalculated",
                            "info")
                st.rerun()

    st.divider()
    live_context = f"Overdue notes: {st.session_state.overdue_docs}. Pending patients: " + \
                   ", ".join(p["name"] for p in pending) if pending else "All notes up to date."
    render_chatbot("Documentation Agent", live_context, key_prefix="doc_agent_multi")

# ═══════════════════════════════════════════════════════════════════════
# HANDOVER AGENT  reads/completes the SAME sbar dict Documentation writes
# ═══════════════════════════════════════════════════════════════════════
with tab_handover:
    st.markdown("### 🤝 Handover Agent")
    st.caption("Shared SBAR data")

    for p in sorted(st.session_state.shared_patients, key=lambda x: x["priority"]):
        missing = [k for k, v in p["sbar"].items() if not v]
        complete = len(missing) == 0
        border = "#1F7A4D" if complete else "#B91C1C" if p["priority"] == 1 else "#B45309"
        st.markdown(f"""<div class="patient-card" style="border-color:{border};">
            <b>{p['name']}</b> — P{p['priority']} · Risk {p['risk_score']:.0%}<br>
            <span style="font-size:0.8rem;color:#5A6B7D;">
                {'✅ SBAR complete' if complete else '⚠️ Missing: ' + ', '.join(missing)}
            </span>
        </div>""", unsafe_allow_html=True)
        if not complete:
            if st.button(f"Complete remaining SBAR  {p['name']}", key=f"ho_{p['name']}"):
                for k in p["sbar"]:
                    p["sbar"][k] = True
                log_handoff("Handover Agent", "Documentation Agent",
                            f"SBAR for {p['name']} confirmed complete by outgoing clinician", "success")
                log_handoff("Handover Agent", "Workflow Agent",
                            f"{p['name']} handover risk resolved  ward priority may be re-ranked", "info")
                st.rerun()

    sbar_rate = round(100 * sum(1 for p in st.session_state.shared_patients if all(p["sbar"].values())) / len(st.session_state.shared_patients))
    st.divider()
    st.metric("SBAR Compliance", f"{sbar_rate}%")
    render_chatbot("Handover Agent", f"SBAR compliance: {sbar_rate}%.", key_prefix="handover_agent_multi")

# ═══════════════════════════════════════════════════════════════════════
# WORKFLOW AGENT — ward risk, feeds Cognitive + Coordination
# ═══════════════════════════════════════════════════════════════════════
with tab_workflow:
    st.markdown("### ⚡ Workflow Agent")
    st.caption("XGBoost-driven ward risk · shared data")

    ranked = sorted(st.session_state.shared_ward_risk.items(), key=lambda x: -x[1])
    for i, (wname, risk) in enumerate(ranked):
        priority = f"P{i+1}"
        color = "#B91C1C" if risk > 0.7 else "#B45309" if risk > 0.4 else "#1F7A4D"
        st.markdown(f"""<div class="patient-card" style="border-color:{color};">
            <b>{priority} — {wname}</b> ({WARDS[wname]['specialty']})<br>
            <span style="font-size:1.3rem;font-weight:800;color:{color};">{risk:.0%}</span>
        </div>""", unsafe_allow_html=True)
        if risk > 0.5:
            if st.button(f"Take action {wname}", key=f"wf_{wname}"):
                st.session_state.shared_ward_risk[wname] = max(0.15, risk - 0.25)
                log_handoff("Workflow Agent", "Cognitive Support Agent",
                            f"{wname} risk reduced to {st.session_state.shared_ward_risk[wname]:.0%} — bed pressure eased", "success")
                log_handoff("Workflow Agent", "Coordination Agent",
                            f"{wname} no longer critical fewer queries expected from this ward", "info")
                st.rerun()

    st.divider()
    render_chatbot("Workflow Agent", f"Ward risk: {st.session_state.shared_ward_risk}", key_prefix="workflow_agent_multi")

# ═══════════════════════════════════════════════════════════════════════
# COGNITIVE SUPPORT AGENT  computed LIVE from shared state, not isolated
# ═══════════════════════════════════════════════════════════════════════
with tab_cognitive:
    st.markdown("### 🧠 Cognitive Support Agent")
    st.caption("Calculated live from shared data")

    nasa = recalc_nasa_tlx()
    load_label = "CRITICAL" if nasa > 75 else "HIGH" if nasa > 60 else "MODERATE" if nasa > 40 else "LOW"
    load_color = "#B91C1C" if nasa > 75 else "#B45309" if nasa > 60 else "#1F4E79" if nasa > 40 else "#1F7A4D"

    st.markdown(f"""<div class="patient-card" style="text-align:center;border-color:{load_color};">
        <div style="font-size:0.75rem;color:#5A6B7D;">NASA TASK LOAD INDEX</div>
        <div style="font-size:3.5rem;font-weight:900;color:{load_color};">{nasa}</div>
        <div style="font-weight:700;color:{load_color};">{load_label}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    - Occupancy contribution: {st.session_state.occupancy}% ward occupancy
    - Documentation contribution: {st.session_state.overdue_docs} overdue notes
    - Coordination relief: {st.session_state.coord_time_saved} minutes already saved by Coordination Agent
    """)

    if nasa > 70:
        st.warning("⚡ Scaffolding active: decision queue filtered to top 3 urgent items")
    if nasa > 80:
        st.error("⏰ Scaffolding active: non-urgent admin deferred to 14:00")

    st.divider()
    render_chatbot("Cognitive Support Agent",
                    f"NASA-TLX: {nasa}/100 ({load_label}). Driven by {st.session_state.overdue_docs} overdue notes "
                    f"and {st.session_state.occupancy}% occupancy, offset by {st.session_state.coord_time_saved} min "
                    f"already saved by the Coordination Agent.",
                    key_prefix="cognitive_agent_multi")

# ═══════════════════════════════════════════════════════════════════════
# INTEGRATION AGENT  queries the SAME patient records, flags conflicts
# ═══════════════════════════════════════════════════════════════════════
with tab_integration:
    st.markdown("### 🔗 Integration Agent")
    st.caption("Shared patient roster")

    selected = st.selectbox("Select patient", [p["name"] for p in st.session_state.shared_patients], key="int_select")
    p = get_patient(selected)

    if st.button("Query 5 NHS systems", key="int_query"):
        with st.spinner("Querying EPR, NHS Spine, Pharmacy, RIS, LIS..."):
            time.sleep(0.8)
        st.success(f"{p['name']} data consolidated in 2.3 seconds")
        st.markdown(f"""
        - **EPR:** {p['diagnosis']}
        - **NHS Spine:** {p['nhs']}, DOB verified
        - **Pharmacy:** No interactions flagged
        - **RIS:** No imaging pending
        - **LIS:** Latest bloods within range
        """)
        if p["ward"] == "Ward A":
            st.error("⚠️ CONFLICT: EPR shows Ward A at 108 beds occupied vs NHS Spine showing 110")
            log_handoff("Integration Agent", "Workflow Agent",
                        f"Bed count conflict detected for {p['ward']} verify before reallocating", "critical")

    st.divider()
    render_chatbot("Integration Agent", f"Currently viewing: {selected}.", key_prefix="integration_agent_multi")

# ═══════════════════════════════════════════════════════════════════════
# COORDINATION AGENT  resolving queries reduces Cognitive Support's load
# ═══════════════════════════════════════════════════════════════════════
with tab_coord:
    st.markdown("### 📞 Coordination Agent")
    st.caption("Feeds into Cognitive Support's load score")

    st.metric("Time Saved This Session", f"{st.session_state.coord_time_saved} min")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📞 Auto-resolve routine query"):
            st.session_state.coord_time_saved += random.randint(2, 5)
            log_handoff("Coordination Agent", "Cognitive Support Agent",
                        f"Routine query auto-resolved  {st.session_state.coord_time_saved} min saved this session, load easing",
                        "success")
            st.rerun()
    with c2:
        if st.button("🚨 Escalate complex query"):
            log_handoff("Coordination Agent", "Command Centre",
                        "Complex query escalated  requires clinician judgment, not auto-resolvable", "critical")
            st.rerun()

    st.divider()
    render_chatbot("Coordination Agent", f"Time saved: {st.session_state.coord_time_saved} minutes.",
                    key_prefix="coordination_agent_multi")

# ═══════════════════════════════════════════════════════════════════════
# SECURITY AGENT — independent monitoring, escalates to Command Centre
# ═══════════════════════════════════════════════════════════════════════
with tab_security:
    st.markdown("### 🔒 Security Agent")
    st.caption("Runs continuously in the background")

    st.markdown(f"""<div class="patient-card" style="text-align:center;">
        <div style="font-size:0.75rem;color:#5A6B7D;">THREAT LEVEL</div>
        <div style="font-size:2.2rem;font-weight:800;color:{'#B91C1C' if st.session_state.security_threat_level != 'LOW' else '#1F7A4D'};">
            {st.session_state.security_threat_level}
        </div>
    </div>""", unsafe_allow_html=True)

    if st.button("Simulate anomaly detection"):
        st.session_state.security_threat_level = "HIGH"
        log_handoff("Security Agent", "Command Centre",
                    "CRITICAL anomaly detected  bulk download attempt blocked, IT Security notified. "
                    "CLINICIAN or Information Governance sign-off required before access is restored.",
                    "critical")
        st.rerun()
    if st.session_state.security_threat_level != "LOW":
        if st.button(" Clinician/IG sign-off  contain and restore"):
            st.session_state.security_threat_level = "LOW"
            log_handoff("Security Agent", "Command Centre", "Anomaly contained, access restored after sign-off", "success")
            st.rerun()

    st.divider()
    render_chatbot("Security Agent", f"Threat level: {st.session_state.security_threat_level}.",
                    key_prefix="security_agent_multi")

st.divider()
st.markdown('<div style="text-align:center;font-size:0.75rem;color:#5A6B7D;padding:4px 0;font-weight:600;">'
            '🔬 Powered by XGBoost (AUC-ROC 0.8542) and LSTM (MAPE 7.26%)  trained on 303,392 MIMIC-IV admissions'
            '</div>',
            unsafe_allow_html=True)
st.markdown('<div style="text-align:center;font-size:0.75rem;color:#7A8896;padding:4px 0 8px 0;">'
            'NHS AI Platform  Unified Multi-Agent System · LD7326 · W25041744 · Northumbria University · '
            '<b>All scenarios fictional</b> · Clinician-in-the-Loop enforced · DCB0129/DCB0160 compliant</div>',
            unsafe_allow_html=True)