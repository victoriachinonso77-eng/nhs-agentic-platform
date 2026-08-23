"""
Feasibility Evaluation Simulation
NHS Agentic AI Platform | LD7326 | W25041744

Compares baseline vs AI-assisted workflows across N paired scenarios.
Pre-registered statistical tests: Shapiro-Wilk → Paired t / Wilcoxon
Effect size threshold: Cohen's d >= 0.5
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate Cohen's d effect size."""
    diff = np.mean(a) - np.mean(b)
    pooled = np.sqrt((np.std(a, ddof=1)**2 + np.std(b, ddof=1)**2) / 2)
    return abs(float(diff / pooled)) if pooled > 0 else 0.0


def run_statistical_test(baseline: np.ndarray, ai: np.ndarray,
                          metric_name: str, higher_better: bool = False) -> dict:
    """
    Pre-registered test protocol:
    1. Shapiro-Wilk normality test on paired differences
    2. Paired t-test if normal, Wilcoxon signed-rank if not
    3. Cohen's d effect size (threshold >= 0.5)
    """
    diff = baseline - ai
    _, p_norm = stats.shapiro(diff)

    if float(p_norm) > 0.05:
        _, p = stats.ttest_rel(baseline, ai)
        test = "Paired t-test"
    else:
        _, p = stats.wilcoxon(baseline, ai)
        test = "Wilcoxon signed-rank"

    d = cohens_d(baseline, ai)
    imp = (float(np.mean(baseline) - np.mean(ai)) if not higher_better
           else float(np.mean(ai) - np.mean(baseline)))
    imp_pct = imp / abs(float(np.mean(baseline))) * 100

    return {
        "metric":           metric_name,
        "baseline_mean":    round(float(np.mean(baseline)), 3),
        "ai_mean":          round(float(np.mean(ai)), 3),
        "improvement":      round(imp, 3),
        "improvement_pct":  round(imp_pct, 1),
        "test_used":        test,
        "p_value":          round(float(p), 6),
        "significant":      bool(float(p) < 0.05),
        "cohens_d":         round(d, 3),
        "practically_significant": bool(d >= 0.5),
        "verdict":          "FEASIBLE" if float(p) < 0.05 and d >= 0.5 else "NOT SIGNIFICANT"
    }


def run_feasibility_evaluation(n_scenarios: int = 100,
                                seed: int = 42) -> list:
    """
    Run the full feasibility evaluation across N paired simulation scenarios.
    Returns list of statistical test results for all 7 outcome measures.
    """
    np.random.seed(seed)
    N = n_scenarios

    # Baseline metrics — grounded in MIMIC-IV and NHS RTT findings
    baseline = {
        "task_completion_mins":  np.random.normal(47.3, 12.1, N),
        "documentation_errors":  np.random.poisson(3.2, N).astype(float),
        "sbar_compliance":       np.random.normal(61.4, 8.3, N),
        "ed_wait_hours":         np.random.normal(10.88, 3.2, N),
        "nasa_tlx":              np.random.normal(72.4, 9.1, N),
        "query_resolution_mins": np.random.normal(38.2, 7.4, N),
        "security_incidents":    np.random.poisson(1.8, N).astype(float),
    }

    # AI-assisted metrics
    ai = {
        "task_completion_mins":  baseline["task_completion_mins"] * np.random.uniform(0.55, 0.72, N),
        "documentation_errors":  np.maximum(0, baseline["documentation_errors"] - np.random.poisson(2.1, N).astype(float)),
        "sbar_compliance":       np.minimum(100, baseline["sbar_compliance"] + np.random.normal(17.2, 4.1, N)),
        "ed_wait_hours":         baseline["ed_wait_hours"] * np.random.uniform(0.71, 0.85, N),
        "nasa_tlx":              np.clip(baseline["nasa_tlx"] - np.random.normal(18.3, 5.2, N), 10, 100),
        "query_resolution_mins": baseline["query_resolution_mins"] * np.random.uniform(0.38, 0.52, N),
        "security_incidents":    np.maximum(0, baseline["security_incidents"] - np.random.poisson(1.2, N).astype(float)),
    }

    results = [
        run_statistical_test(baseline["task_completion_mins"],  ai["task_completion_mins"],  "Task Completion Time (mins)"),
        run_statistical_test(baseline["documentation_errors"],  ai["documentation_errors"],  "Documentation Errors (per shift)"),
        run_statistical_test(baseline["sbar_compliance"],       ai["sbar_compliance"],       "SBAR Compliance Rate (%)",    True),
        run_statistical_test(baseline["ed_wait_hours"],         ai["ed_wait_hours"],         "ED Wait Time (hours)"),
        run_statistical_test(baseline["nasa_tlx"],              ai["nasa_tlx"],              "Cognitive Load NASA-TLX (/100)"),
        run_statistical_test(baseline["query_resolution_mins"], ai["query_resolution_mins"], "Query Resolution Time (mins)"),
        run_statistical_test(baseline["security_incidents"],    ai["security_incidents"],    "Security Incidents (per shift)"),
    ]

    # Print results table
    print(f"\n{'='*100}")
    print(f"FEASIBILITY EVALUATION RESULTS (N={N} paired scenarios)")
    print(f"{'='*100}")
    print(f"{'Metric':<35} {'Base':>8} {'AI':>8} {'Improv%':>8} {'Test':>20} {'p-value':>10} {'d':>6}  Verdict")
    print("-" * 100)
    for r in results:
        print(f"{r['metric']:<35} {r['baseline_mean']:>8.2f} {r['ai_mean']:>8.2f} "
              f"{r['improvement_pct']:>7.1f}% {r['test_used']:>20} "
              f"{r['p_value']:>10.6f} {r['cohens_d']:>6.3f}  "
              f"{'✅ FEASIBLE' if r['verdict']=='FEASIBLE' else '❌'}")

    feasible = sum(1 for r in results if r['verdict'] == 'FEASIBLE')
    print(f"{'='*100}")
    print(f"VERDICT: {feasible}/{len(results)} outcomes — statistical AND practical significance (d≥0.5)")

    return results, baseline, ai


def plot_results(results: list, baseline: dict, ai: dict,
                 save_path: str = "outputs/figures/feasibility_evaluation.png") -> None:
    """Generate boxplot and effect size charts."""
    BLUE = '#2E75B6'
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    keys = list(baseline.keys())
    labels = ["Task Completion\nTime (mins)", "Documentation\nErrors",
              "SBAR Compliance\nRate (%)", "ED Wait\nTime (hrs)",
              "Cognitive Load\nNASA-TLX", "Query Resolution\nTime (mins)",
              "Security\nIncidents"]

    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    axes = axes.flatten()

    for idx in range(7):
        ax = axes[idx]
        ax.boxplot([baseline[keys[idx]], ai[keys[idx]]],
                   labels=['Baseline', 'AI-Assisted'],
                   patch_artist=True,
                   boxprops=dict(facecolor=BLUE, alpha=0.6),
                   medianprops=dict(color='red', linewidth=2))
        r = results[idx]
        ax.set_title(
            f"{labels[idx]}\np={r['p_value']:.4f}, d={r['cohens_d']:.3f}\n"
            f"{'✅ FEASIBLE' if r['verdict']=='FEASIBLE' else '❌'}",
            fontsize=8, fontweight='bold'
        )

    axes[7].axis('off')
    feasible = sum(1 for r in results if r['verdict'] == 'FEASIBLE')
    plt.suptitle(
        f'Feasibility Evaluation — Baseline vs AI-Assisted (N={len(list(baseline.values())[0])} paired scenarios)\n'
        f'Verdict: {feasible}/{len(results)} outcomes statistically AND practically significant (d≥0.5)',
        fontsize=10, fontweight='bold'
    )
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: {save_path}")


def save_results(results: list,
                 path: str = "outputs/results/feasibility_results.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved: {path}")


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    results, baseline, ai = run_feasibility_evaluation(n_scenarios=100, seed=42)
    plot_results(results, baseline, ai)
    save_results(results)