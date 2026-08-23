"""
NHS Agentic AI Platform — AI-Powered Seven Agents
Uses OpenAI GPT-4o API for real LLM reasoning
LD7326 | MSc Artificial Intelligence Technology | W25041744

Setup:
    pip install openai
    Set OPENAI_API_KEY in your .env file or environment
"""

import os
import json
import time
import random
import datetime
from openai import OpenAI
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Initialise Anthropic client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"


# ── Event Logger ──────────────────────────────────────────────────────

class EventLogger:
    def __init__(self, session_id: str = None):
        self.events = []
        self.start_time = time.time()
        self.session_id = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(self, agent: str, action: str, input_data: Any,
            output: str, duration_ms: float):
        event = {
            "session_id":      self.session_id,
            "timestamp":       datetime.datetime.now().isoformat(),
            "elapsed_seconds": round(time.time() - self.start_time, 3),
            "agent":           agent,
            "action":          action,
            "duration_ms":     round(duration_ms, 2),
            "input_summary":   str(input_data)[:150],
            "output_summary":  output[:300]
        }
        self.events.append(event)
        print(f"  [{event['elapsed_seconds']:6.3f}s] [{agent:<25}] {output[:80]}")

    def save(self, path: str = "outputs/logs"):
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(f"{path}/event_log.json", "w") as f:
            json.dump(self.events, f, indent=2)
        print(f"\nEvent log saved ({len(self.events)} events)")


# ── Base AI Agent ─────────────────────────────────────────────────────

class NHSAIAgent:
    """
    Base class for AI-powered NHS agents.
    Each agent calls Claude API with a specialised system prompt
    and structured ward state / prediction data as context.
    """

    def __init__(self, name: str, role: str,
                 failure_point: str, rq: str,
                 system_prompt: str, logger: EventLogger):
        self.name          = name
        self.role          = role
        self.failure_point = failure_point
        self.rq            = rq
        self.system_prompt = system_prompt
        self.logger        = logger

    def _call_openai(self, user_message: str) -> str:
        """Call OpenAI API and return the text response."""
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=600,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content.strip()

    def act(self, inputs: Dict) -> Dict:
        raise NotImplementedError

    def _log(self, action: str, inputs: Any, output: str, duration_ms: float):
        self.logger.log(self.name, action, inputs, output, duration_ms)


# ── AGENT 1: DOCUMENTATION AGENT ─────────────────────────────────────

class DocumentationAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="DocumentationAgent",
            role="Clinical Documentation Automation",
            failure_point="Manual note-writing errors and omissions",
            rq="RQ1, RQ3",
            system_prompt=(
                "You are the Documentation Agent in an NHS AI platform. "
                "Your role is to analyse the current ward state and generate "
                "specific, actionable recommendations for automating clinical "
                "documentation. Always:\n"
                "- State how many notes can be auto-generated vs need review\n"
                "- Identify specific error types detected\n"
                "- Estimate time saved in minutes\n"
                "- End with: CLINICIAN REVIEW REQUIRED before any note is finalised.\n"
                "Keep response under 150 words. Be specific and clinical."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        ws = inputs["ward_state"]
        overdue = ws["overdue_documentation"]

        user_msg = (
            f"Current ward state:\n"
            f"- Overdue documentation: {overdue} notes\n"
            f"- Ward occupancy: {ws['occupancy_rate']:.0%}\n"
            f"- Staff on shift: {ws['staff_on_shift']}\n"
            f"- ED wait time: {ws['current_ed_wait_hours']} hours\n\n"
            f"Generate your documentation recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "overdue_documentation":     overdue,
            "auto_generated_estimate":   int(overdue * 0.70),
            "manual_review_estimate":    int(overdue * 0.30),
            "estimated_time_saved_mins": int(overdue * 0.70) * 8,
            "recommendation":            recommendation,
            "clinician_review_required": True
        }
        self._log("generate_documentation",
                  f"overdue={overdue}", recommendation, duration_ms)
        return output


# ── AGENT 2: HANDOVER AGENT ───────────────────────────────────────────

class HandoverAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="HandoverAgent",
            role="Handover Communication Support",
            failure_point="Handover communication failures",
            rq="RQ1, RQ3",
            system_prompt=(
                "You are the Handover Agent in an NHS AI platform. "
                "Your role is to validate SBAR handover compliance and "
                "flag high-risk patient transfers based on bottleneck predictions.\n"
                "Always:\n"
                "- Name the high-risk wards specifically\n"
                "- State the current SBAR compliance rate\n"
                "- Specify what SBAR elements are missing\n"
                "- End with: CLINICIAN REVIEW REQUIRED before any patient transfer.\n"
                "Keep response under 150 words."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        ws = inputs["ward_state"]
        predictions = inputs["bottleneck_predictions"]
        high_risk = [w for w, d in predictions.items()
                     if d["bottleneck_probability"] > 0.7]
        compliance = round((ws["pending_handovers"] - len(high_risk)) /
                           max(ws["pending_handovers"], 1) * 100, 1)

        user_msg = (
            f"Ward state:\n"
            f"- Pending handovers: {ws['pending_handovers']}\n"
            f"- Bottleneck predictions: {json.dumps(predictions, indent=2)}\n"
            f"- High-risk wards (prob >70%): {high_risk}\n\n"
            f"Generate your handover compliance recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "pending_handovers":       ws["pending_handovers"],
            "high_risk_wards":         high_risk,
            "sbar_compliance_rate":    compliance,
            "recommendation":          recommendation,
            "clinician_review_required": True
        }
        self._log("validate_handovers",
                  f"pending={ws['pending_handovers']}, high_risk={high_risk}",
                  recommendation, duration_ms)
        return output


# ── AGENT 3: WORKFLOW AGENT ───────────────────────────────────────────

class WorkflowAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="WorkflowAgent",
            role="Workflow Optimisation and Task Prioritisation",
            failure_point="Task bottlenecks and prioritisation failures",
            rq="RQ2, RQ3, RQ4",
            system_prompt=(
                "You are the Workflow Agent in an NHS AI platform. "
                "You receive XGBoost bottleneck predictions and LSTM demand "
                "forecasts and generate prioritised workflow recommendations.\n"
                "Always:\n"
                "- List priority actions in order (P1, P2, P3)\n"
                "- Reference the specific ward names and probabilities\n"
                "- Include the 7-day demand trend\n"
                "- End with: CLINICIAN REVIEW REQUIRED before resource reallocation.\n"
                "Keep response under 150 words."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        ws = inputs["ward_state"]
        predictions = inputs["bottleneck_predictions"]
        demand = inputs["demand_forecast"]
        critical = [(w, d["bottleneck_probability"]) for w, d in predictions.items()
                    if d["bottleneck_probability"] > 0.7]

        user_msg = (
            f"Ward state: occupancy {ws['occupancy_rate']:.0%}, "
            f"{ws['pending_transfers']} pending transfers\n"
            f"Bottleneck predictions: {json.dumps(predictions, indent=2)}\n"
            f"7-day demand forecast: {json.dumps(demand, indent=2)}\n\n"
            f"Generate your workflow prioritisation recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "critical_wards":   critical,
            "demand_forecast":  demand,
            "occupancy_rate":   ws["occupancy_rate"],
            "recommendation":   recommendation,
            "clinician_review_required": True
        }
        self._log("optimise_workflow",
                  f"critical={[w for w,_ in critical]}",
                  recommendation, duration_ms)
        return output


# ── AGENT 4: COGNITIVE SUPPORT AGENT ─────────────────────────────────

class CognitiveSupportAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="CognitiveSupportAgent",
            role="Cognitive Load Reduction and Decision Support",
            failure_point="Decision fatigue and cognitive overload",
            rq="RQ3",
            system_prompt=(
                "You are the Cognitive Support Agent in an NHS AI platform. "
                "You estimate cognitive load using a NASA-TLX proxy score "
                "and provide decision scaffolding to reduce clinician fatigue.\n"
                "Always:\n"
                "- State the NASA-TLX estimated score (0-100)\n"
                "- Label the load level (CRITICAL/HIGH/MODERATE)\n"
                "- List 3 specific scaffolding interventions\n"
                "- End with: CLINICIAN REVIEW REQUIRED for all clinical decisions.\n"
                "Keep response under 150 words."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        ws = inputs["ward_state"]
        occupancy = ws["occupancy_rate"]
        overdue = ws["overdue_documentation"]
        pending_ho = ws["pending_handovers"]

        nasa_tlx = min(100, round(
            occupancy * 40 +
            min(overdue / 30, 1) * 30 +
            min(pending_ho / 20, 1) * 30, 1
        ))

        user_msg = (
            f"Ward state:\n"
            f"- Occupancy: {occupancy:.0%}\n"
            f"- Overdue documentation: {overdue}\n"
            f"- Pending handovers: {pending_ho}\n"
            f"- Staff: {ws['staff_on_shift']}\n"
            f"- Estimated NASA-TLX: {nasa_tlx}/100\n\n"
            f"Generate your cognitive load assessment and scaffolding recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "nasa_tlx_estimated":   nasa_tlx,
            "cognitive_load_level": "CRITICAL" if nasa_tlx > 75 else "HIGH" if nasa_tlx > 50 else "MODERATE",
            "recommendation":       recommendation,
            "clinician_review_required": True
        }
        self._log("assess_cognitive_load",
                  f"nasa_tlx={nasa_tlx}",
                  recommendation, duration_ms)
        return output


# ── AGENT 5: INTEGRATION AGENT ────────────────────────────────────────

class IntegrationAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="IntegrationAgent",
            role="System Integration and Data Consolidation",
            failure_point="Fragmented system data retrieval",
            rq="RQ3",
            system_prompt=(
                "You are the Integration Agent in an NHS AI platform. "
                "You consolidate data from multiple NHS systems and flag conflicts.\n"
                "Always:\n"
                "- Name each system integrated\n"
                "- State time saved vs manual retrieval\n"
                "- Flag any data conflicts detected\n"
                "- End with: CLINICIAN REVIEW REQUIRED for flagged conflicts.\n"
                "Keep response under 150 words."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        systems = ["EPR", "NHS Spine", "Pharmacy", "RIS", "LIS"]
        conflicts = random.randint(1, 3)

        user_msg = (
            f"Systems to integrate: {systems}\n"
            f"Ward state: {json.dumps(inputs['ward_state'], indent=2)}\n"
            f"Data conflicts detected: {conflicts}\n\n"
            f"Generate your system integration recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "systems_integrated":        systems,
            "systems_count":             len(systems),
            "data_conflicts_detected":   conflicts,
            "time_saved_mins":           round(len(systems) * 4 - 2.3/60, 1),
            "recommendation":            recommendation,
            "clinician_review_required": True
        }
        self._log("integrate_systems",
                  f"systems={len(systems)}, conflicts={conflicts}",
                  recommendation, duration_ms)
        return output


# ── AGENT 6: COORDINATION AGENT ───────────────────────────────────────

class CoordinationAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="CoordinationAgent",
            role="Staff Coordination and Query Management",
            failure_point="Routine query interruptions",
            rq="RQ3, RQ4",
            system_prompt=(
                "You are the Coordination Agent in an NHS AI platform. "
                "You manage routine queries to reduce clinician interruptions.\n"
                "Always:\n"
                "- State how many queries were auto-resolved vs escalated\n"
                "- Give the auto-resolution rate as a percentage\n"
                "- Estimate clinician time saved in minutes\n"
                "- End with: ALL escalated queries require CLINICIAN REVIEW.\n"
                "Keep response under 150 words."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        total_queries = random.randint(20, 35)
        auto_resolved = int(total_queries * 0.704)
        escalated = total_queries - auto_resolved

        user_msg = (
            f"Incoming queries this shift: {total_queries}\n"
            f"Staff on shift: {inputs['ward_state']['staff_on_shift']}\n"
            f"Ward occupancy: {inputs['ward_state']['occupancy_rate']:.0%}\n\n"
            f"Auto-resolved: {auto_resolved}, Escalated: {escalated}\n\n"
            f"Generate your query coordination recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "total_queries":             total_queries,
            "auto_resolved":             auto_resolved,
            "escalated":                 escalated,
            "auto_resolution_rate":      round(auto_resolved / total_queries * 100, 1),
            "estimated_time_saved_mins": auto_resolved * 3,
            "recommendation":            recommendation,
            "clinician_review_required": True
        }
        self._log("coordinate_queries",
                  f"total={total_queries}, resolved={auto_resolved}",
                  recommendation, duration_ms)
        return output


# ── AGENT 7: SECURITY AGENT ───────────────────────────────────────────

class SecurityAgent(NHSAIAgent):
    def __init__(self, logger: EventLogger):
        super().__init__(
            name="SecurityAgent",
            role="Cybersecurity Monitoring and Data Integrity",
            failure_point="Cyber threats and data integrity failures",
            rq="RQ3, RQ4",
            system_prompt=(
                "You are the Security Agent in an NHS AI platform. "
                "You monitor access logs, detect anomalies, and verify data integrity.\n"
                "Always:\n"
                "- State the threat level (LOW/MEDIUM/HIGH)\n"
                "- Report number of access events monitored\n"
                "- Report anomalies detected\n"
                "- Confirm encryption and audit trail status\n"
                "- Reference DCB0129/DCB0160 compliance\n"
                "Keep response under 150 words."
            ),
            logger=logger
        )

    def act(self, inputs: Dict) -> Dict:
        start = time.time()
        access_events = random.randint(380, 520)
        anomalies = random.randint(0, 2)
        threat = "LOW" if anomalies == 0 else "MEDIUM" if anomalies == 1 else "HIGH"

        user_msg = (
            f"Security monitoring report:\n"
            f"- Access events this cycle: {access_events}\n"
            f"- Anomalies detected: {anomalies}\n"
            f"- Integrity checks run: 47\n"
            f"- Encryption: AES-256 active\n"
            f"- Threat level: {threat}\n\n"
            f"Generate your security status recommendation."
        )

        recommendation = self._call_openai(user_msg)
        duration_ms = (time.time() - start) * 1000

        output = {
            "access_events_monitored": access_events,
            "anomalies_detected":      anomalies,
            "threat_level":            threat,
            "integrity_checks":        47,
            "encryption_status":       "AES-256 active",
            "recommendation":          recommendation,
            "clinician_review_required": False
        }
        self._log("monitor_security",
                  f"events={access_events}, anomalies={anomalies}",
                  recommendation, duration_ms)
        return output


# ── ORCHESTRATOR ──────────────────────────────────────────────────────

class NHSAIPlatformOrchestrator:
    """Coordinates all seven AI-powered agents."""

    def __init__(self):
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = EventLogger(session_id=self.session_id)
        self.agents = {
            "documentation": DocumentationAgent(self.logger),
            "handover":       HandoverAgent(self.logger),
            "workflow":       WorkflowAgent(self.logger),
            "cognitive":      CognitiveSupportAgent(self.logger),
            "integration":    IntegrationAgent(self.logger),
            "coordination":   CoordinationAgent(self.logger),
            "security":       SecurityAgent(self.logger),
        }

    def run_cycle(self) -> Dict:
        print(f"\n{'='*65}")
        print(f"NHS AI PLATFORM — AI-POWERED SIMULATION")
        print(f"Model: {MODEL} | Session: {self.session_id}")
        print(f"{'='*65}")

        inputs = {
            "ward_state": {
                "timestamp":             datetime.datetime.now().isoformat(),
                "total_beds":            120,
                "occupied_beds":         108,
                "occupancy_rate":        0.90,
                "pending_handovers":     14,
                "overdue_documentation": 23,
                "staff_on_shift":        {"doctors": 8, "nurses": 22, "admin": 5},
                "pending_transfers":     7,
                "icu_available_beds":    3,
                "current_ed_wait_hours": 4.2
            },
            "bottleneck_predictions": {
                "ward_A": {"bottleneck_probability": 0.87, "predicted_los_hours": 156, "admission_type": "EW EMER."},
                "ward_B": {"bottleneck_probability": 0.43, "predicted_los_hours": 98,  "admission_type": "URGENT"},
                "ward_C": {"bottleneck_probability": 0.91, "predicted_los_hours": 189, "admission_type": "EW EMER."},
                "ward_D": {"bottleneck_probability": 0.21, "predicted_los_hours": 67,  "admission_type": "ELECTIVE"},
                "ICU":    {"bottleneck_probability": 0.72, "predicted_los_hours": 220, "admission_type": "DIRECT EMER."},
            },
            "demand_forecast": {f"day_{i+1}": round(15 + i*0.4, 1) for i in range(7)}
        }

        print(f"\n  Running all 7 AI-powered agents...")
        print(f"  {'-'*60}")
        results = {}
        t0 = time.time()
        for name, agent in self.agents.items():
            results[name] = agent.act(inputs)
        total = time.time() - t0
        print(f"  {'-'*60}")
        print(f"  All 7 agents completed in {total:.2f}s")

        summary = {
            "session_id":            self.session_id,
            "model_used":            MODEL,
            "duration_secs":         round(total, 2),
            "ward_occupancy":        inputs["ward_state"]["occupancy_rate"],
            "sbar_compliance_rate":  results["handover"]["sbar_compliance_rate"],
            "nasa_tlx_estimated":    results["cognitive"]["nasa_tlx_estimated"],
            "cognitive_load_level":  results["cognitive"]["cognitive_load_level"],
            "queries_auto_resolved": results["coordination"]["auto_resolved"],
            "security_threat_level": results["security"]["threat_level"],
            "clinician_review_required": True,
            "agent_recommendations": {n: r["recommendation"] for n, r in results.items()}
        }

        # Print full recommendations
        print(f"\n{'='*65}")
        print("AI-GENERATED RECOMMENDATIONS")
        print("⚠️  CLINICIAN REVIEW REQUIRED BEFORE ANY ACTION")
        print(f"{'='*65}")
        for name, r in results.items():
            print(f"\n[{name.upper()}]")
            print(f"  {r['recommendation']}")

        # Save outputs
        Path("outputs/logs").mkdir(parents=True, exist_ok=True)
        Path("outputs/results").mkdir(parents=True, exist_ok=True)
        self.logger.save("outputs/logs")
        with open("outputs/results/ai_platform_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return summary, results


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set.")
        print("Add it to your .env file: OPENAI_API_KEY=sk-ant-...")
        exit(1)

    orchestrator = NHSAIPlatformOrchestrator()
    summary, results = orchestrator.run_cycle()
    print(f"\nDone. Session: {summary['session_id']}")