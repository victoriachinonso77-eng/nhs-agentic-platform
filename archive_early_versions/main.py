"""
NHS Agentic AI Platform — Main Entry Point (OpenAI Mode)
LD7326 | MSc Artificial Intelligence Technology | W25041744
Run: python main.py
Requires: OPENAI_API_KEY in .env file
"""

import os
from dotenv import load_dotenv
from src.platform.ai_agents import NHSAIPlatformOrchestrator
from src.platform.simulation import (
    run_feasibility_evaluation, plot_results, save_results
)

load_dotenv()

def main():
    # Check API key
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "sk-proj-your-key-here":
        print("\nERROR: OPENAI_API_KEY not found or not set.")
        print("1. Open your .env file")
        print("2. Add: OPENAI_API_KEY=sk-proj-yourrealkeyhere")
        print("3. Get your key from: https://platform.openai.com/api-keys")
        return

    print("\n" + "="*65)
    print("NHS AGENTIC AI PLATFORM — OpenAI GPT-4o MODE")
    print("MSc AI Technology | LD7326 | W25041744")
    print("="*65)

    # Phase 1: AI-powered platform simulation
    print("\n[PHASE 1] Running AI-powered 7-agent simulation...")
    orchestrator = NHSAIPlatformOrchestrator()
    summary, results = orchestrator.run_cycle()

    # Phase 2: Feasibility evaluation
    print("\n[PHASE 2] Running feasibility evaluation (100 scenarios)...")
    eval_results, baseline, ai = run_feasibility_evaluation(n_scenarios=100, seed=42)
    plot_results(eval_results, baseline, ai)
    save_results(eval_results)

    print("\n" + "="*65)
    print("COMPLETE — outputs saved to outputs/")
    print("="*65)

if __name__ == "__main__":
    main()