"""
NHS Multi-Agent Platform — AI-Driven Agent Reasoning
Each of the seven agents makes a genuine GPT-4o call to decide its own
recommendation, rather than the deterministic Python logic in
run_full_cycle(). Calls run in parallel (ThreadPoolExecutor) to keep
total wall-clock time as low as possible.

IMPORTANT: Streamlit's st.session_state is only accessible from the main
script thread. All session_state reads happen here BEFORE the thread
pool is spawned, and all session_state writes happen AFTER the thread
pool has finished and results are collected back on the main thread.
The worker threads only ever see plain Python strings — never
st.session_state directly.

LD7326 | MSc Artificial Intelligence Technology | W25041744
"""

import streamlit as st
import os
import json
import time
import concurrent.futures

AGENT_PERSONAS = {
    "Documentation Agent": (
        "You are the Documentation Agent in an NHS ward AI platform. Your job is to decide "
        "which ONE patient most urgently needs their SBAR clinical note drafted this cycle, "
        "based on risk score and whether a note is already overdue. "
        "Respond ONLY with JSON: {\"target\": \"<patient name>\", \"summary\": \"<one-line action>\", "
        "\"rationale\": \"<why this patient, this cycle>\"}"
    ),
    "Handover Agent": (
        "You are the Handover Agent in an NHS ward AI platform. Your job is to decide which "
        "ONE patient's incomplete SBAR handover most urgently needs completing this cycle, "
        "prioritising by clinical priority and how many SBAR sections are missing. "
        "Respond ONLY with JSON: {\"target\": \"<patient name>\", \"summary\": \"<one-line action>\", "
        "\"rationale\": \"<why this patient, this cycle>\"}"
    ),
    "Workflow Agent": (
        "You are the Workflow Agent in an NHS ward AI platform. Your job is to decide which "
        "ONE ward most urgently needs a resource reallocation this cycle, based on bottleneck risk. "
        "Respond ONLY with JSON: {\"target\": \"<ward name>\", \"summary\": \"<one-line action>\", "
        "\"rationale\": \"<why this ward, this cycle>\"}"
    ),
    "Cognitive Support Agent": (
        "You are the Cognitive Support Agent in an NHS ward AI platform. Based on the current "
        "NASA-TLX cognitive load score, decide whether decision-queue scaffolding should activate "
        "this cycle (threshold: >60). "
        "Respond ONLY with JSON: {\"target\": null, \"summary\": \"<one-line decision>\", "
        "\"rationale\": \"<why, referencing the actual NASA-TLX number>\"}"
    ),
    "Integration Agent": (
        "You are the Integration Agent in an NHS ward AI platform. Decide which ONE patient's "
        "record most needs cross-system verification this cycle (EPR, NHS Spine, Pharmacy, RIS, LIS), "
        "prioritising the highest-risk patient. "
        "Respond ONLY with JSON: {\"target\": \"<patient name>\", \"summary\": \"<one-line action>\", "
        "\"rationale\": \"<why this patient, this cycle>\"}"
    ),
    "Coordination Agent": (
        "You are the Coordination Agent in an NHS ward AI platform. Decide on ONE routine query "
        "this cycle that can be auto-resolved without clinician input. "
        "Respond ONLY with JSON: {\"target\": null, \"summary\": \"<one-line action>\", "
        "\"rationale\": \"<why this is safely auto-resolvable>\"}"
    ),
    "Security Agent": (
        "You are the Security Agent in an NHS ward AI platform, running continuous access "
        "monitoring. Decide on ONE routine security action for this cycle. "
        "Respond ONLY with JSON: {\"target\": null, \"summary\": \"<one-line action>\", "
        "\"rationale\": \"<brief justification>\"}"
    ),
}


def _build_all_contexts():
    """Runs on the MAIN thread only — reads st.session_state and builds
    a plain dict of {agent_name: context_string}. Nothing here is passed
    a Streamlit object; only plain strings leave this function."""
    patients = st.session_state.shared_patients
    contexts = {}

    pending = [p for p in patients if p["note_due"] and not p["documented"]]
    contexts["Documentation Agent"] = (
        "Patients with overdue notes: " + "; ".join(
            f"{p['name']} (risk {p['risk_score']:.0%})" for p in pending
        ) if pending else "No overdue notes."
    )

    incomplete = [p for p in patients if not all(p["sbar"].values())]
    contexts["Handover Agent"] = (
        "Patients with incomplete SBAR: " + "; ".join(
            f"{p['name']} (priority {p['priority']}, missing {[k for k,v in p['sbar'].items() if not v]})"
            for p in incomplete
        ) if incomplete else "All SBAR complete."
    )

    contexts["Workflow Agent"] = "Ward risk: " + "; ".join(
        f"{w} ({r:.0%})" for w, r in st.session_state.shared_ward_risk.items()
    )

    from shared_state import recalc_nasa_tlx
    contexts["Cognitive Support Agent"] = (
        f"Current NASA-TLX: {recalc_nasa_tlx()}/100. Overdue docs: {st.session_state.overdue_docs}."
    )

    contexts["Integration Agent"] = "Patients by risk: " + "; ".join(
        f"{p['name']} ({p['risk_score']:.0%})" for p in sorted(patients, key=lambda x: -x["risk_score"])
    )

    contexts["Coordination Agent"] = f"Time saved so far this session: {st.session_state.coord_time_saved} min."
    contexts["Security Agent"] = f"Current threat level: {st.session_state.security_threat_level}."

    return contexts


def _call_one_agent(agent_name, context, api_key):
    """Runs inside a worker thread. Receives only plain strings — NEVER
    touches st.session_state, so it's safe to run off the main thread."""
    if not api_key or api_key.startswith("sk-proj-your-key"):
        return {"agent": agent_name, "error": "No OPENAI_API_KEY configured"}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=200,
            temperature=0.3,
            messages=[
                {"role": "system", "content": AGENT_PERSONAS[agent_name]},
                {"role": "user", "content": f"Current ward data:\n{context}\n\nDecide your recommendation now."},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        return {
            "agent": agent_name,
            "target": parsed.get("target"),
            "summary": parsed.get("summary", "(no summary returned)"),
            "rationale": parsed.get("rationale", "(no rationale returned)"),
        }
    except Exception as e:
        return {"agent": agent_name, "error": str(e)}


def run_full_cycle_ai():
    """Main-thread orchestration: build contexts (needs session_state) →
    fire off worker threads (plain strings only, no session_state) →
    collect results back on the main thread → write to session_state
    (queue_recommendation / log_handoff / write_event all happen here,
    safely on the main thread)."""
    from shared_state import queue_recommendation, log_handoff, write_event

    start = time.perf_counter()
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "")
    contexts = _build_all_contexts()  # main thread — safe
    agent_names = list(AGENT_PERSONAS.keys())

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        futures = [
            executor.submit(_call_one_agent, name, contexts[name], api_key)
            for name in agent_names
        ]
        results = [f.result() for f in futures]  # blocks on main thread until all done

    elapsed = time.perf_counter() - start
    succeeded, failed = 0, 0

    # Everything below is back on the main thread — safe to touch session_state
    for r in results:
        if "error" in r:
            failed += 1
            st.error(f"DEBUG — {r['agent']}: {r['error']}")
            write_event(
                agent=r["agent"], action="ai_generation_failed", duration_ms=round(elapsed * 1000, 1),
                input_summary="GPT-4o call", output_summary=f"Error: {r['error']}",
            )
            continue
        succeeded += 1
        queue_recommendation(r["agent"], "ai_generated", r["target"], r["summary"], r["rationale"])

    log_handoff("AutoGen-style Orchestrator (GPT-4o)", "Clinician Review Queue",
                f"AI-driven cycle complete in {elapsed:.2f}s — {succeeded} recommendations generated, "
                f"{failed} failed (check API key / network)", "info" if failed == 0 else "critical")

    return succeeded, failed, elapsed