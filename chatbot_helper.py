"""
NHS AI Platform — Shared Chatbot Component
Drop this file (chatbot_helper.py) into the same folder as your simulation files,
then call render_chatbot() from any simulation to add a Q&A chat box.

LD7326 | MSc Artificial Intelligence Technology | W25041744
"""

import streamlit as st
import os

# ── Dissertation baseline knowledge — shared across every simulation ──
DISSERTATION_CONTEXT = """
You are answering questions about an NHS Agentic AI Platform research prototype,
built for an MSc dissertation (LD7326, W25041744, Northumbria University).

CORE FACTS ABOUT THE PLATFORM:
- Two-layer architecture: XGBoost bottleneck classifier (AUC-ROC = 0.8542, trained on
  303,392 MIMIC-IV admissions) + LSTM demand forecaster (MAPE = 7.26%, 7-day horizon).
- Seven agents: Documentation, Handover, Workflow, Cognitive Support, Integration,
  Coordination, Security.
- Feasibility evaluation: 7 of 7 outcome measures statistically significant (p < 0.000001)
  and practically significant (Cohen's d >= 0.5), across a 100-scenario simulation.
- Governance: every agent output is a RECOMMENDATION requiring explicit clinician
  sign-off before any action affects a patient. Full audit trail maintained.
  Designed against DCB0129, DCB0160, UK GDPR, NHS AI Strategy — NOT yet certified;
  certification is scoped as the PhD-phase clinical safety case.
- Bias audit: demographic-stratified fairness audit run across 526,518 MIMIC-IV
  admissions. Found a 6.4 percentage-point recall gap by race and an 18 percentage-point
  recall gap by insurance type — reported honestly as a limitation, not hidden.
- Data: MIMIC-IV accessed under PhysioNet Credentialled Health Data Licence (W25041744).
  All simulation patients (James Okafor, Robert Adeniran, Margaret Thornton, Priya
  Krishnamurthy, etc.) are entirely FICTIONAL — invented for demonstration only.
- This is a RESEARCH PROTOTYPE, not a deployed clinical system. It has not been used
  on any real patient and is not connected to any real NHS system.

RULES FOR YOUR ANSWERS:
1. Answer only using the platform context above and the live simulation data provided
   with each question — do not invent statistics or claims beyond what's given.
2. Never give real clinical advice, a real diagnosis, or a real treatment recommendation
   — you are explaining what a RESEARCH SIMULATION shows, not treating a patient.
3. If asked about a real patient's care, redirect: "This is a research simulation with
   fictional data — I can explain what the simulation shows, not give clinical advice."
4. Keep answers concise — 2-4 sentences unless the question needs more detail.
5. If you don't know something from the context given, say so plainly rather than guessing.
6. Never claim the platform is deployed, certified, or approved for clinical use.
"""


def render_chatbot(agent_name: str, live_context: str, key_prefix: str = "chat"):
    """
    Renders a chat interface grounded in the current simulation's live data.

    Args:
        agent_name: e.g. "Documentation Agent", "Handover Agent"
        live_context: a plain-text summary of what's currently on screen —
                      the specific numbers, patients, or state visible right now.
        key_prefix: unique prefix so multiple chat instances don't collide
                    if this is ever called twice on one page.
    """
    history_key = f"{key_prefix}_history"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    st.markdown(
        f"""
        <div style="background:#F3F6FA;border:1px solid #D1D9E0;border-radius:10px;
        padding:14px 18px;margin-top:16px;">
            <div style="font-size:0.85rem;font-weight:700;color:#1F4E79;margin-bottom:2px;font-family:'Merriweather',Georgia,serif;">
                💬 Ask about the {agent_name}
            </div>
            <div style="font-size:0.75rem;color:#5A6B7D;">
                Ask a specific question about what's shown on this screen
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render existing history
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input(f"Ask a question about the {agent_name}...", key=f"{key_prefix}_input")

    if question:
        st.session_state[history_key].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "sk-proj-your-key-here":
            answer = (
                "⚠️ No OpenAI API key found in .env — add OPENAI_API_KEY to enable "
                "live answers. (This chatbot uses the same key as the agent simulations.)"
            )
        else:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)

                system_prompt = (
                    DISSERTATION_CONTEXT
                    + f"\n\nCURRENT SCREEN — {agent_name}:\n{live_context}\n\n"
                    + "Answer the user's question using only the information above."
                )

                response = client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=300,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ],
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                answer = f"⚠️ Couldn't reach the API: {e}"

        st.session_state[history_key].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

        st.markdown(
            """
            <div style="font-size:0.68rem;color:#7A8896;margin-top:4px;">
                ⚠️ Research simulation — not clinical advice. All patient data fictional.
            </div>
            """,
            unsafe_allow_html=True,
        )