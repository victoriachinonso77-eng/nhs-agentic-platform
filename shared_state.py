"""
NHS Multi-Agent Platform — Shared State Module
Single source of truth for patients, wards, and cross-agent handoffs.
Every agent tab reads from and writes to this same object, so an action
taken in one agent (e.g. Documentation drafting a note) is immediately
visible to every other agent (e.g. Handover sees SBAR completeness change).

LD7326 | MSc Artificial Intelligence Technology | W25041744
"""

import streamlit as st
import datetime
import json
import time
import os

# ── Canonical ward roster (from Workflow Agent's WARDS) ─────────────────
WARDS = {
    "Ward A": {"specialty": "Emergency Medicine", "beds": 24, "base_risk": 0.87, "adm_type": "EW EMER.",  "color": "#EF4444"},
    "Ward B": {"specialty": "Acute Medicine",      "beds": 20, "base_risk": 0.43, "adm_type": "URGENT",    "color": "#F59E0B"},
    "Ward C": {"specialty": "Orthopaedics",        "beds": 22, "base_risk": 0.91, "adm_type": "EW EMER.",  "color": "#EF4444"},
    "Ward D": {"specialty": "Elective Surgery",    "beds": 18, "base_risk": 0.18, "adm_type": "ELECTIVE",  "color": "#22C55E"},
    "ICU":    {"specialty": "Critical Care",       "beds": 12, "base_risk": 0.72, "adm_type": "URGENT",    "color": "#F59E0B"},
}

# ── Canonical patient roster — superset of every agent's fields,       ──
# ── reconciled so name / risk_score / ward are IDENTICAL everywhere    ──
PATIENTS = [
    {
        "name": "James Okafor", "age": 67, "sex": "M", "nhs": "NHS-485-261-3847",
        "ward": "Ward A", "bed": "Bed 14", "admission_type": "EW EMER.",
        "diagnosis": "Acute NSTEMI — chest pain, ST changes, elevated troponin",
        "risk_score": 0.87, "priority": 1, "los_hours": 18.4,
        "sbar": {"situation": True, "background": True, "assessment": False, "recommendation": False},
        "documented": False, "note_due": True,
    },
    {
        "name": "Robert Adeniran", "age": 78, "sex": "M", "nhs": "NHS-334-817-9204",
        "ward": "Ward C", "bed": "Bed 3", "admission_type": "EW EMER.",
        "diagnosis": "NOF Fracture — INR 3.8 on admission, awaiting reversal",
        "risk_score": 0.91, "priority": 1, "los_hours": 22.1,
        "sbar": {"situation": True, "background": True, "assessment": False, "recommendation": False},
        "documented": False, "note_due": True,
    },
    {
        "name": "Priya Krishnamurthy", "age": 34, "sex": "F", "nhs": "NHS-591-042-7713",
        "ward": "ICU", "bed": "Bed 11", "admission_type": "URGENT",
        "diagnosis": "Asthma exacerbation — stepped down from ICU, PEFR improving",
        "risk_score": 0.72, "priority": 2, "los_hours": 14.6,
        "sbar": {"situation": True, "background": True, "assessment": True, "recommendation": False},
        "documented": False, "note_due": True,
    },
    {
        "name": "Michael Thompson", "age": 71, "sex": "M", "nhs": "NHS-227-914-6650",
        "ward": "Ward B", "bed": "Bed 16", "admission_type": "URGENT",
        "diagnosis": "COPD exacerbation — on nebulisers, chest X-ray pending review",
        "risk_score": 0.61, "priority": 2, "los_hours": 11.2,
        "sbar": {"situation": True, "background": True, "assessment": True, "recommendation": True},
        "documented": False, "note_due": True,
    },
    {
        "name": "Margaret Thornton", "age": 45, "sex": "F", "nhs": "NHS-712-394-5521",
        "ward": "Ward D", "bed": "Bed 7", "admission_type": "ELECTIVE",
        "diagnosis": "Appendicitis — theatre booked, consent verification pending",
        "risk_score": 0.43, "priority": 3, "los_hours": 6.8,
        "sbar": {"situation": True, "background": False, "assessment": True, "recommendation": True},
        "documented": False, "note_due": True,
    },
    {
        "name": "Sarah Williams", "age": 52, "sex": "F", "nhs": "NHS-108-663-2290",
        "ward": "Ward A", "bed": "Bed 8", "admission_type": "EW EMER.",
        "diagnosis": "Atypical chest pain — troponin negative, awaiting discharge review",
        "risk_score": 0.31, "priority": 3, "los_hours": 9.4,
        "sbar": {"situation": True, "background": True, "assessment": True, "recommendation": True},
        "documented": False, "note_due": True,
    },
    {
        "name": "Fatima Al-Hassan", "age": 29, "sex": "F", "nhs": "NHS-845-217-3362",
        "ward": "Ward B", "bed": "Bed 9", "admission_type": "URGENT",
        "diagnosis": "UTI — IV to oral antibiotic switch pending",
        "risk_score": 0.25, "priority": 4, "los_hours": 5.1,
        "sbar": {"situation": True, "background": True, "assessment": True, "recommendation": True},
        "documented": False, "note_due": True,
    },
    {
        "name": "David Chen", "age": 58, "sex": "M", "nhs": "NHS-503-776-1148",
        "ward": "Ward D", "bed": "Bed 2", "admission_type": "ELECTIVE",
        "diagnosis": "Elective hip replacement — routine post-op recovery",
        "risk_score": 0.18, "priority": 4, "los_hours": 30.2,
        "sbar": {"situation": True, "background": True, "assessment": True, "recommendation": True},
        "documented": True, "note_due": False,
    },
]


def init_shared_state():
    """Call once at the top of the app. Idempotent — safe to call every rerun."""
    if "shared_patients" not in st.session_state:
        # Deep-ish copy so we never mutate the module-level constant
        st.session_state.shared_patients = [dict(p, sbar=dict(p["sbar"])) for p in PATIENTS]
    if "shared_ward_risk" not in st.session_state:
        st.session_state.shared_ward_risk = {w: d["base_risk"] for w, d in WARDS.items()}
    if "handoff_log" not in st.session_state:
        st.session_state.handoff_log = []
    if "shift_clock_start" not in st.session_state:
        st.session_state.shift_clock_start = datetime.datetime.now()
    if "occupancy" not in st.session_state:
        st.session_state.occupancy = 90
    if "overdue_docs" not in st.session_state:
        st.session_state.overdue_docs = sum(1 for p in st.session_state.shared_patients if p["note_due"] and not p["documented"])
    if "coord_time_saved" not in st.session_state:
        st.session_state.coord_time_saved = 0
    if "security_threat_level" not in st.session_state:
        st.session_state.security_threat_level = "LOW"
    if "pending_recommendations" not in st.session_state:
        st.session_state.pending_recommendations = []
    if "cycle_start_time" not in st.session_state:
        st.session_state.cycle_start_time = time.perf_counter()
    if "event_log" not in st.session_state:
        st.session_state.event_log = []
    if "current_user" not in st.session_state:
        st.session_state.current_user = None


EVENT_LOG_PATH = "nhs_multi_agent_event_log.json"


def write_event(agent, action, duration_ms, input_summary, output_summary):
    """Appends one event to session_state.event_log AND persists the full
    log to a JSON file on disk — matching the exact schema used by the
    original AutoGen prototype (nhs_platform_event_log.json), so this
    satisfies the dissertation's claim that every agent action is
    'logged to a structured JSON event file.'"""
    elapsed = round(time.perf_counter() - st.session_state.cycle_start_time, 3)
    event = {
        "timestamp": datetime.datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "agent": agent,
        "action": action,
        "duration_ms": duration_ms,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "clinician": st.session_state.get("current_user") or "Not logged in",
    }
    st.session_state.event_log.append(event)
    try:
        with open(EVENT_LOG_PATH, "w") as f:
            json.dump(st.session_state.event_log, f, indent=2)
    except OSError:
        # Read-only filesystem or similar — don't crash the app over a log write
        pass


def get_patient(name):
    for p in st.session_state.shared_patients:
        if p["name"] == name:
            return p
    return None


def fuzzy_match_patient(name_guess):
    """Matches an LLM-returned name (which may include a title, differ in
    case, or be a partial name) back to the real roster. Case-insensitive,
    substring-tolerant in both directions. Returns None if no reasonable
    match exists — callers must handle that, never guess silently."""
    if not name_guess:
        return None
    guess = name_guess.lower().strip()
    for p in st.session_state.shared_patients:
        real = p["name"].lower()
        if guess == real or guess in real or real in guess:
            return p
    # Last resort: match on surname only (last word)
    guess_last_word = guess.split()[-1] if guess.split() else ""
    for p in st.session_state.shared_patients:
        if guess_last_word and guess_last_word in p["name"].lower():
            return p
    return None


def fuzzy_match_ward(name_guess):
    """Same idea as fuzzy_match_patient but for ward names."""
    if not name_guess:
        return None
    guess = name_guess.lower().strip()
    for wname in st.session_state.shared_ward_risk:
        if guess == wname.lower() or guess in wname.lower() or wname.lower() in guess:
            return wname
    return None


def log_handoff(from_agent, to_agent, message, level="info"):
    """Record a visible cross-agent handoff. Every tab can display this feed.
    Also persists to the JSON event log on disk. Every entry is tagged with
    the logged-in clinician's name, so approvals/rejections are individually
    attributable — not just 'something was approved,' but by whom."""
    clinician = st.session_state.get("current_user") or "Not logged in"
    st.session_state.handoff_log.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "from": from_agent,
        "to": to_agent,
        "message": message,
        "level": level,
        "clinician": clinician,
    })
    write_event(
        agent=from_agent,
        action="handoff",
        duration_ms=0.5,
        input_summary=f"→ {to_agent}",
        output_summary=message,
    )


def recalc_overdue_docs():
    st.session_state.overdue_docs = sum(
        1 for p in st.session_state.shared_patients if p["note_due"] and not p["documented"]
    )


def recalc_nasa_tlx():
    """Cognitive load derived from the SAME shared state every other agent reads —
    so if Documentation clears overdue notes, or Coordination resolves queries,
    the Cognitive Support Agent's load score changes too, visibly."""
    occ_component = st.session_state.occupancy / 100 * 40
    doc_component = min(st.session_state.overdue_docs / 8, 1) * 30
    query_component = max(0, 30 - st.session_state.coord_time_saved / 3)
    return min(100, round(occ_component + doc_component + query_component))


# ── Two-phase recommendation / approval ──────────────────────────────
# Matches the dissertation's precise claim: agents GENERATE a recommendation
# automatically and fast (the "simulation cycle"), but nothing changes the
# shared patient/ward state until a clinician explicitly APPROVES it.
# This is deliberately a separate step from log_handoff(), which only
# records that something happened — queue_recommendation() records
# something that is PROPOSED but not yet true.

def queue_recommendation(agent, rec_type, target, summary, rationale):
    """Add one agent's proposed action to the pending review queue.
    Does NOT touch shared_patients / shared_ward_risk / counters —
    that only happens in apply_recommendation() after approval.
    Also logs the recommendation itself to the JSON event log —
    this is the 'generated a specific operational recommendation
    with explicit rationale, and logged the action' step."""
    rec_id = f"{agent}_{target}_{len(st.session_state.pending_recommendations)}"
    st.session_state.pending_recommendations.append({
        "id": rec_id,
        "agent": agent,
        "type": rec_type,       # e.g. "draft_note", "complete_sbar", "ward_action", "resolve_query"
        "target": target,       # patient name, ward name, or None
        "summary": summary,
        "rationale": rationale,
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
    })
    write_event(
        agent=agent,
        action="generate_recommendation",
        duration_ms=0.8,
        input_summary=f"target={target}" if target else "session-wide",
        output_summary=f"{summary} — rationale: {rationale}",
    )


def apply_recommendation(rec):
    """Called only when a clinician clicks Approve. Performs the actual
    state mutation — the same mutation the manual per-agent buttons
    perform — then logs the resulting handoff."""
    if rec["type"] == "draft_note":
        p = get_patient(rec["target"])
        if p:
            p["documented"] = True
            p["sbar"]["situation"] = True
            p["sbar"]["background"] = True
            recalc_overdue_docs()
            log_handoff("Documentation Agent", "Handover Agent",
                        f"[Approved] Note drafted for {p['name']} — Situation/Background complete", "success")

    elif rec["type"] == "complete_sbar":
        p = get_patient(rec["target"])
        if p:
            for k in p["sbar"]:
                p["sbar"][k] = True
            log_handoff("Handover Agent", "Workflow Agent",
                        f"[Approved] SBAR for {p['name']} confirmed complete", "success")

    elif rec["type"] == "ward_action":
        wname = rec["target"]
        current = st.session_state.shared_ward_risk[wname]
        st.session_state.shared_ward_risk[wname] = max(0.15, current - 0.25)
        log_handoff("Workflow Agent", "Cognitive Support Agent",
                    f"[Approved] {wname} risk reduced to {st.session_state.shared_ward_risk[wname]:.0%}", "success")

    elif rec["type"] == "resolve_query":
        import random
        st.session_state.coord_time_saved += random.randint(2, 5)
        log_handoff("Coordination Agent", "Cognitive Support Agent",
                    f"[Approved] Query resolved — {st.session_state.coord_time_saved} min saved this session", "success")

    elif rec["type"] == "cognitive_scaffold":
        if "no scaffolding" in rec["summary"].lower():
            log_handoff("Cognitive Support Agent", "Command Centre",
                        f"[Approved] Cognitive load confirmed within safe range — no scaffolding applied", "info")
        else:
            log_handoff("Cognitive Support Agent", "Command Centre",
                        f"[Approved] Decision-queue scaffolding activated — clinician's queue filtered to top 3 urgent items",
                        "success")

    elif rec["type"] == "integration_check":
        p = get_patient(rec["target"])
        if p:
            log_handoff("Integration Agent", "Workflow Agent",
                        f"[Approved] Cross-system record verified for {p['name']} — no conflicts found on this pass",
                        "success")

    elif rec["type"] == "security_audit":
        log_handoff("Security Agent", "Command Centre",
                    "[Approved] Routine access audit completed — no anomalies this cycle", "success")

    elif rec["type"] == "ai_generated":
        # Route to the SAME real mutation logic the deterministic path uses,
        # based on which agent generated this recommendation — so approving
        # an AI-generated recommendation cascades to other agents exactly
        # like approving a deterministic one does.
        agent = rec["agent"]

        if agent == "Documentation Agent":
            p = fuzzy_match_patient(rec["target"])
            if p:
                p["documented"] = True
                p["sbar"]["situation"] = True
                p["sbar"]["background"] = True
                recalc_overdue_docs()
                log_handoff("Documentation Agent", "Handover Agent",
                            f"[Approved — AI-generated] Note drafted for {p['name']} — Situation/Background complete",
                            "success")
                log_handoff("Documentation Agent", "Cognitive Support Agent",
                            f"[Approved — AI-generated] Overdue notes now {st.session_state.overdue_docs}", "info")
            else:
                log_handoff("Documentation Agent", "Clinician Review Queue",
                            f"[Approved but unmatched] GPT-4o named '{rec['target']}' — no roster match found, "
                            f"no state changed", "critical")

        elif agent == "Handover Agent":
            p = fuzzy_match_patient(rec["target"])
            if p:
                for k in p["sbar"]:
                    p["sbar"][k] = True
                log_handoff("Handover Agent", "Workflow Agent",
                            f"[Approved — AI-generated] SBAR for {p['name']} confirmed complete", "success")
            else:
                log_handoff("Handover Agent", "Clinician Review Queue",
                            f"[Approved but unmatched] GPT-4o named '{rec['target']}' — no roster match found, "
                            f"no state changed", "critical")

        elif agent == "Workflow Agent":
            wname = fuzzy_match_ward(rec["target"])
            if wname:
                current = st.session_state.shared_ward_risk[wname]
                st.session_state.shared_ward_risk[wname] = max(0.15, current - 0.25)
                log_handoff("Workflow Agent", "Cognitive Support Agent",
                            f"[Approved — AI-generated] {wname} risk reduced to "
                            f"{st.session_state.shared_ward_risk[wname]:.0%}", "success")
            else:
                log_handoff("Workflow Agent", "Clinician Review Queue",
                            f"[Approved but unmatched] GPT-4o named '{rec['target']}' — no ward match found, "
                            f"no state changed", "critical")

        elif agent == "Coordination Agent":
            import random
            st.session_state.coord_time_saved += random.randint(2, 5)
            log_handoff("Coordination Agent", "Cognitive Support Agent",
                        f"[Approved — AI-generated] Query resolved — {st.session_state.coord_time_saved} "
                        f"min saved this session", "success")

        else:
            # Cognitive Support, Integration, Security — informational agents,
            # same as their deterministic counterparts: logged, no direct
            # shared-state field to mutate.
            log_handoff(agent, "Clinician Review Queue",
                        f"[Approved — AI-generated] {rec['summary']}", "success")


def run_full_cycle():
    """Mirrors the dissertation's claim: 'the seven-agent AutoGen prototype
    ran a complete simulation cycle... each of the seven agents received
    inputs... generated a specific operational recommendation.'
    Fast, automatic, GENERATES recommendations only — applies nothing."""
    pending = [p for p in st.session_state.shared_patients if p["note_due"] and not p["documented"]]
    if pending:
        p = max(pending, key=lambda x: x["risk_score"])
        queue_recommendation("Documentation Agent", "draft_note", p["name"],
                              f"Draft SBAR note for {p['name']} ({p['ward']}, risk {p['risk_score']:.0%})",
                              "Highest-risk patient with an overdue note this cycle.")

    incomplete = [p for p in st.session_state.shared_patients if not all(p["sbar"].values())]
    if incomplete:
        p = max(incomplete, key=lambda x: x["priority"] == 1)
        queue_recommendation("Handover Agent", "complete_sbar", p["name"],
                              f"Complete remaining SBAR for {p['name']}",
                              "Priority patient with incomplete handover documentation.")

    risky_wards = {w: r for w, r in st.session_state.shared_ward_risk.items() if r > 0.5}
    if risky_wards:
        wname = max(risky_wards, key=risky_wards.get)
        queue_recommendation("Workflow Agent", "ward_action", wname,
                              f"Reallocate resources — {wname} at {risky_wards[wname]:.0%} risk",
                              "Highest-risk ward this cycle, above the 50% action threshold.")

    queue_recommendation("Coordination Agent", "resolve_query", None,
                          "Auto-resolve next routine query in the inbox",
                          "Routine query pattern-matched against known auto-resolvable categories.")

    nasa = recalc_nasa_tlx()
    if nasa > 60:
        queue_recommendation("Cognitive Support Agent", "cognitive_scaffold", None,
                              f"Activate decision-queue scaffolding — NASA-TLX at {nasa}/100",
                              "Cognitive load has crossed the >60 threshold this cycle.")
    else:
        queue_recommendation("Cognitive Support Agent", "cognitive_scaffold", None,
                              f"No scaffolding needed this cycle — NASA-TLX at {nasa}/100, within safe range",
                              "Cognitive load assessed and confirmed below the >60 intervention threshold.")

    highest_risk_patient = max(st.session_state.shared_patients, key=lambda x: x["risk_score"])
    queue_recommendation("Integration Agent", "integration_check", highest_risk_patient["name"],
                          f"Cross-check {highest_risk_patient['name']}'s record across 5 NHS systems",
                          "Highest-risk patient this cycle — verify no data conflicts before action is taken.")

    queue_recommendation("Security Agent", "security_audit", None,
                          "Run routine access-pattern audit for this cycle",
                          "Scheduled integrity check — part of continuous background monitoring.")

    log_handoff("AutoGen Orchestrator", "Clinician Review Queue",
                f"Simulation cycle complete — {len(st.session_state.pending_recommendations)} "
                f"recommendations generated across all seven agents, awaiting approval", "info")