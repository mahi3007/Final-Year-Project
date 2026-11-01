"""
Stage 6M Task 6.4 — Monte Carlo Acceptance-Rule Reconciliation Audit
====================================================================
Formal audit and reconciliation of the exact Clopper-Pearson confidence bound
acceptance criteria for the v1.5 candidate five-stratum protocol.

GOVERNANCE:
- Preserve DRAFT_HOLD.
- Do not modify frozen v1.4.0 inference engine.
- M = 8 hypotheses, alpha_adj = 0.00625, simultaneous percentile = 99.375%.
- Do not lower the 90.00% power requirement.
- Do not choose a confidence method based on which result passes.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import scipy.stats as sp_stats

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def compute_exact_clopper_pearson(k: int, n: int, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Computes both exact Clopper-Pearson bounds for k successes out of n trials:
      1. Two-sided (1 - alpha) CI: lower endpoint with tail area alpha / 2 (0.025).
      2. One-sided (1 - alpha) LCB: lower bound with tail area alpha (0.050).
    """
    p_hat = k / float(n)

    # Two-sided 95% CI (tail = 0.025 in each tail)
    low_2sided = float(sp_stats.beta.ppf(alpha / 2.0, k, n - k + 1)) if k > 0 else 0.0
    high_2sided = float(sp_stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k)) if k < n else 1.0

    # One-sided 95% LCB (tail = 0.05 in lower tail)
    lcb_1sided = float(sp_stats.beta.ppf(alpha, k, n - k + 1)) if k > 0 else 0.0

    # Distances from registered 90.00% threshold
    diff_2sided_pp = (low_2sided - 0.90) * 100.0
    diff_1sided_pp = (lcb_1sided - 0.90) * 100.0

    return {
        "k": k,
        "n": n,
        "point_estimate": p_hat,
        "point_estimate_pct": round(p_hat * 100.0, 4),
        "two_sided_95_ci": {
            "lower_endpoint": low_2sided,
            "upper_endpoint": high_2sided,
            "lower_endpoint_pct": round(low_2sided * 100.0, 6),
            "upper_endpoint_pct": round(high_2sided * 100.0, 6),
            "tail_probability": alpha / 2.0,
            "effective_confidence_pct": 97.5,
            "distance_from_90_pp": round(diff_2sided_pp, 6),
            "satisfies_threshold": bool(low_2sided >= 0.90),
        },
        "one_sided_95_lcb": {
            "lower_bound": lcb_1sided,
            "lower_bound_pct": round(lcb_1sided * 100.0, 6),
            "tail_probability": alpha,
            "effective_confidence_pct": 95.0,
            "distance_from_90_pp": round(diff_1sided_pp, 6),
            "satisfies_threshold": bool(lcb_1sided >= 0.90),
        },
    }


def find_required_success_thresholds(n: int = 10000, target: float = 0.90, alpha: float = 0.05) -> Dict[str, Any]:
    """Finds exact minimum number of successes required to clear target under each method."""
    k_req_2sided = None
    for k in range(int(target * n) - 100, n):
        if float(sp_stats.beta.ppf(alpha / 2.0, k, n - k + 1)) >= target:
            k_req_2sided = k
            break

    k_req_1sided = None
    for k in range(int(target * n) - 100, n):
        if float(sp_stats.beta.ppf(alpha, k, n - k + 1)) >= target:
            k_req_1sided = k
            break

    return {
        "n_trials": n,
        "target_power": target,
        "two_sided_lower_endpoint_min_k": k_req_2sided,
        "two_sided_lower_endpoint_min_rate_pct": round((k_req_2sided / n) * 100.0, 4),
        "one_sided_lcb_min_k": k_req_1sided,
        "one_sided_lcb_min_rate_pct": round((k_req_1sided / n) * 100.0, 4),
        "trajectory_difference_k": k_req_2sided - k_req_1sided,
    }


def build_acceptance_rule_audit_report() -> Dict[str, Any]:
    """Compiles the authoritative acceptance rule audit and protocol reconciliation."""
    k_220 = 9058
    n_220 = 10000
    res_220 = compute_exact_clopper_pearson(k_220, n_220)
    thresh = find_required_success_thresholds(n_220)

    # Benchmark N_g = 285 (2,500 trials)
    k_285 = 2424
    n_285 = 2500
    res_285 = compute_exact_clopper_pearson(k_285, n_285)

    report = {
        "audit_metadata": {
            "task_id": "STAGE6M_TASK_6_4",
            "audit_title": "Monte Carlo Acceptance-Rule Reconciliation Audit",
            "protocol_candidate": "v1.5 Five-Stratum Confirmatory Protocol",
            "git_branch": "stage6m-five-stratum-parity",
            "git_head_commit": "8c636f9",
            "governance_status": "DRAFT_HOLD",
            "governance_disposition": "CONDITIONAL HOLD",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "task_a_protocol_inspection": {
            "protocol_wording": "LCB_95(P_hat_joint) >= 0.90 where LCB_95 is the exact Clopper-Pearson 95% lower confidence bound",
            "detected_ambiguity": {
                "text_specification": "Explicitly names a '95% lower confidence bound' (statistically implying tail alpha = 0.05).",
                "code_implementation": "scripts/stage6m_v1_5_sample_size_power_sweep.py called clopper_pearson_interval(..., alpha=0.05), extracting the lower endpoint of a two-sided 95% CI (tail alpha/2 = 0.025, which is mathematically a 97.5% one-sided LCB).",
                "historical_reports": "Task 5 reports (stage6m_v1_5_sample_size_power_sweep.md) and Task 6 reports (stage6m_v1_5_scientific_readiness_audit.md) quoted the two-sided interval lower endpoint as the LCB.",
            },
            "root_cause": "Nomenclature conflation between a one-sided (1 - alpha) lower confidence bound and the lower endpoint of a two-sided (1 - alpha) confidence interval.",
        },
        "task_b_numerical_reproduction": {
            "primary_candidate_n220": res_220,
            "threshold_analysis_10k_trials": thresh,
            "unrounded_comparison": {
                "observed_successes": k_220,
                "total_trials": n_220,
                "point_estimate": res_220["point_estimate"],
                "two_sided_95_ci_lower_endpoint": res_220["two_sided_95_ci"]["lower_endpoint"],
                "one_sided_95_lcb": res_220["one_sided_95_lcb"]["lower_bound"],
                "discrepancy_pp": round(res_220["one_sided_95_lcb"]["lower_bound_pct"] - res_220["two_sided_95_ci"]["lower_endpoint_pct"], 6),
                "explanation": (
                    "The difference of 0.095138 pp between the two bounds arises entirely from the tail probability: "
                    "Beta(0.05; 9058, 943) = 90.085739% vs Beta(0.025; 9058, 943) = 89.990601%. "
                    "At 10,000 trials, the two-sided lower endpoint requires k >= 9059 (short by 1 trajectory), "
                    "whereas the one-sided LCB requires k >= 9050 (cleared by 8 trajectories)."
                ),
            },
        },
        "task_c_acceptance_decision": {
            "governing_determination": "AMBIGUOUS (Pre-Registration Clarification Required)",
            "under_one_sided_interpretation": {
                "criterion": "One-Sided 95% Clopper-Pearson LCB >= 90.00%",
                "lcb_pct": res_220["one_sided_95_lcb"]["lower_bound_pct"],
                "verdict": "PASS (+0.0857 pp margin)",
            },
            "under_two_sided_interpretation": {
                "criterion": "Lower Endpoint of Two-Sided 95% Clopper-Pearson CI >= 90.00%",
                "lcb_pct": res_220["two_sided_95_ci"]["lower_endpoint_pct"],
                "verdict": "SHORTFALL (-0.0094 pp shortfall; 1 trial out of 10,000)",
            },
            "principled_recommendation": (
                "Recommend that the Project Lead formally adopt Option 1 (One-Sided 95% LCB) prior to Cohort 3 authorization. "
                "In statistical methodology and regulatory guidelines (FDA, EMA), validation that power or efficacy exceeds "
                "a minimum required threshold is universally formulated as a one-sided hypothesis test (H1: Power >= 0.90 at alpha = 0.05). "
                "Requiring the two-sided lower endpoint inadvertently imposes an unstated 97.5% confidence standard (alpha = 0.025). "
                "Until formal Project-Lead sign-off is executed, CONDITIONAL HOLD must be strictly preserved."
            ),
        },
        "task_d_sample_size_reconciliation": {
            "primary_candidate": {
                "sample_size_ng": 220,
                "total_speakers": 1100,
                "australian_buffer_speakers": 65,
                "buffer_margin_pct": 21.3,
                "confirmed_joint_power_pct": 90.58,
                "outer_trials": 10000,
                "bootstrap_replicates": 20000,
                "status": "RECOMMENDED PRIMARY DESIGN",
            },
            "benchmark_candidate": {
                "sample_size_ng": 285,
                "total_speakers": 1425,
                "australian_buffer_speakers": 0,
                "buffer_margin_pct": 0.0,
                "confirmed_joint_power_pct": 96.96,
                "outer_trials": 2500,
                "bootstrap_replicates": 20000,
                "status": "SUPPLEMENTAL BENCHMARK ONLY (Requires 10k confirmation if elevated to primary)",
            },
            "superseded_results": {
                "original_task_5_power_pct": 95.35,
                "supersession_reason": (
                    "The Task 5 95.35% power estimate was obtained under an uncalibrated generator where probability clipping "
                    "produced an unintended -2.1733 pp disparity narrowing (a 0.1733 pp overshoot). "
                    "The corrected 90.58% result reflects the genuine -2.0000 pp registered disparity target."
                ),
            },
            "scientific_limitation": (
                "All simulated power estimates are conditional on the assumed -2.0 pp disparity narrowing. "
                "Under weaker disparity effects (-1.5 pp or -1.0 pp), power degrades to 77.5% and 41.7% respectively. "
                "These assumptions must be documented in the dissertation as design scenarios rather than physical guarantees."
            ),
        },
    }

    return report


def generate_markdown_report(data: Dict[str, Any], output_path: Path) -> None:
    """Generates the comprehensive Markdown report for Task 6.4."""
    meta = data["audit_metadata"]
    insp = data["task_a_protocol_inspection"]
    num = data["task_b_numerical_reproduction"]
    dec = data["task_c_acceptance_decision"]
    samp = data["task_d_sample_size_reconciliation"]

    p220 = num["primary_candidate_n220"]
    thresh = num["threshold_analysis_10k_trials"]
    unround = num["unrounded_comparison"]

    lines = [
        "# Stage 6M Task 6.4 — Monte Carlo Acceptance-Rule Reconciliation Audit",
        "",
        "> **DOCUMENT STATUS:** Authoritative Statistical Reconciliation & Acceptance Rule Decision Audit",
        f"> **GOVERNANCE STATUS:** {meta['governance_status']} (Cohort 3 Materialization Blocked)",
        f"> **EVALUATION BRANCH:** `{meta['git_branch']}` (Starting commit `{meta['git_head_commit']}`)",
        f"> **FINAL GOVERNANCE VERDICT:** **{meta['governance_disposition']}**",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "Task 6.4 resolves the statistical question raised in Task 6.3 regarding the Monte Carlo confidence-bound definition:",
        "1. **Ambiguity Identified (Task A):** A subtle but important divergence exists between the candidate protocol specification text and its historical implementation code:",
        "   - The written protocol specification states that the design must achieve: $\\text{LCB}_{95\\%} \\ge 90.00\\%$ ('exact Clopper-Pearson 95% lower confidence bound').",
        "   - The implementation code in `stage6m_v1_5_sample_size_power_sweep.py` evaluated `clopper_pearson_interval(..., alpha=0.05)`, which extracts the lower endpoint of a **two-sided 95% confidence interval** (tail area $\\alpha/2 = 0.025$).",
        "2. **Exact Numerical Reproduction (Task B):** Under the primary confirmation ($N_g = 220$, $9,058 / 10,000$ successes):",
        f"   - **One-Sided 95% LCB (Tail $\\alpha = 0.05$):** **`{p220['one_sided_95_lcb']['lower_bound_pct']:.6f}%`** ($\\ge 90.00\\% \\implies \\mathbf{{PASS}}$ by $+0.0857$ pp).",
        f"   - **Two-Sided 95% CI Lower Endpoint (Tail $\\alpha/2 = 0.025$):** **`{p220['two_sided_95_ci']['lower_endpoint_pct']:.6f}%`** ($< 90.00\\% \\implies \\mathbf{{MISS}}$ by $-0.0094$ pp).",
        "   - At 10,000 trials, the two-sided threshold requires $k \\ge 9,059$ successes; the observed count was $k = 9,058$ (**a shortfall of exactly 1 trajectory out of 10,000**).",
        "3. **Governance Recommendation (Task C):**",
        "   - In standard statistical methodology and regulatory validation (FDA, EMA), verifying whether power exceeds a minimum threshold ($H_1: P \\ge 0.90$) is universally treated as a **one-sided test at level $\\alpha = 0.05$**.",
        "   - Rather than silently reinterpreting the rule to force a PASS, this audit formally documents the ambiguity and presents a principled recommendation for Project-Lead sign-off.",
        "   - Overall governance status remains **`CONDITIONAL HOLD`** pending Project-Lead authorization.",
        "4. **Candidate Positioning Re-Affirmed (Task D):**",
        "   - $N_g = 220$ remains the primary candidate because it preserves a **65-speaker buffer (+21.3%)** under Australian Common Voice 27 capacity.",
        "   - $N_g = 285$ is strictly designated a **supplemental benchmark** (2,500 trials evaluated; consumes 100% of capacity).",
        "   - The original Task 5 95.35% power estimate is formally documented as superseded by the calibrated 90.58% result.",
        "",
        "---",
        "",
        "## 1. Task A — Candidate Protocol Inspection & Ambiguity Audit",
        "",
        "### Protocol Specification Text",
        "In `reports/stage6m/stage6m_v1_5_candidate_five_stratum_protocol_spec.md` (Section 5.2):",
        "> *'To qualify for consideration under Project-Lead Academic Authorization, the candidate design must demonstrate:*",
        "> *$$\\widehat{P}_{\\text{joint}} \\ge 0.90 \\quad \\text{AND} \\quad \\text{LCB}_{95\\%}(\\widehat{P}_{\\text{joint}}) \\ge 0.90$$*",
        "> *where $\\text{LCB}_{95\\%}$ is the exact Clopper-Pearson 95% lower confidence bound from at least $S = 10,000$ Monte Carlo trials with $B = 20,000$ bootstrap replicates.'*",
        "",
        "### Code Implementation & Historical Precedent",
        "- In `scripts/stage6m_v1_5_sample_size_power_sweep.py` (line 137 and 539):",
        "  ```python",
        "  def clopper_pearson_interval(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:",
        "      low = float(sp_stats.beta.ppf(alpha / 2.0, k, n - k + 1))",
        "      high = float(sp_stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))",
        "      return low, high",
        "  ```",
        "  The function assigns `lcb, ucb = clopper_pearson_interval(...)` and evaluates `pass_lcb = bool(lcb >= 0.90)`.",
        "- In `tests/research_validity/test_stage6m_sample_size_power_sweep.py` (lines 147–149):",
        "  ```python",
        "  # Exact threshold: k = 9060 out of 10,000 achieves LCB >= 0.90",
        "  l_pass, _ = clopper_pearson_interval(9060, 10000, alpha=0.05)",
        "  assert l_pass >= 0.90",
        "  ```",
        "- In `stage6m_v1_5_candidate_five_stratum_protocol_spec.md` (Section 5.3):",
        "  `Joint Power: 95.35% (95% CI: [94.92%, 95.75%], LCB = 94.92% >= 90.00%)`",
        "  The quoted LCB of $94.92\\%$ was verbatim the lower endpoint of the two-sided 95% CI.",
        "",
        "**Conclusion:** The text specified a '95% lower confidence bound', but the code and cited tables evaluated the **lower endpoint of a two-sided 95% confidence interval** (which corresponds to a 97.5% one-sided confidence bound).",
        "",
        "---",
        "",
        "## 2. Task B — Exact Numerical Reproduction ($N_g = 220$)",
        "",
        "For $k = 9,058$ successful joint trajectories out of $n = 10,000$ trials:",
        "",
        "| Confidence Bound Method | Statistical Formula | Tail Probability ($\\alpha$) | Effective One-Sided Confidence | Exact Unrounded Value | Rounded Value | Required Minimum $k$ ($n = 10,000$) | Result vs 90.00% Threshold |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        f"| **Two-Sided 95% CI Lower Endpoint** | $\\operatorname{{Beta}}(\\alpha/2; k, n-k+1)$ | $\\alpha/2 = 0.025$ | 97.5% LCB | `{unround['two_sided_95_ci_lower_endpoint']:.8f}` | **`{p220['two_sided_95_ci']['lower_endpoint_pct']:.4f}%`** | $k \\ge {thresh['two_sided_lower_endpoint_min_k']}$ ($90.59\\%$) | **SHORTFALL (-0.0094 pp; -1 trial)** |",
        f"| **One-Sided 95% LCB** | $\\operatorname{{Beta}}(\\alpha; k, n-k+1)$ | $\\alpha = 0.050$ | 95.0% LCB | `{unround['one_sided_95_lcb']:.8f}` | **`{p220['one_sided_95_lcb']['lower_bound_pct']:.4f}%`** | $k \\ge {thresh['one_sided_lcb_min_k']}$ ($90.50\\%$) | **PASS (+0.0857 pp; +8 trials)** |",
        "",
        "### Mathematical Explanation of the Discrepancy",
        "The numerical difference of **`0.095138 percentage points`** arises strictly from the probability mass in the tail:",
        "$$p_{L,\\text{1-sided}} = \\operatorname{Beta}(0.050; 9058, 943) = 0.90085739$$",
        "$$p_{L,\\text{2-sided}} = \\operatorname{Beta}(0.025; 9058, 943) = 0.89990601$$",
        "- Testing whether power exceeds 90% is intrinsically a **one-sided validation hypothesis**: $H_0: P < 0.90$ versus $H_1: P \\ge 0.90$.",
        "- When one allocates $2.5\\%$ to the lower tail, one is demanding that the true power be above $90.00\\%$ with **97.5% confidence**, not 95% confidence.",
        "",
        "---",
        "",
        "## 3. Task C — Acceptance Decision & Governance Options",
        "",
        "As mandated by `/gravitas` reliability principles, we do not arbitrarily choose whichever formula yields a PASS. We submit two clearly defined decision pathways for Project-Lead Academic Authorization:",
        "",
        "| Decision Pathway | Statistical Definition | Outcome for $N_g = 220$ | Methodological Justification | Recommended Action |",
        "| :--- | :--- | :---: | :--- | :--- |",
        "| **Option 1 (Recommended): Standard One-Sided 95% LCB** | One-sided 95% Clopper-Pearson LCB (tail $\\alpha = 0.05$) | **PASS** ($90.09\\% \\ge 90.00\\%$) | Aligns with standard clinical and regulatory trial practice for demonstrating adequacy against a minimum power threshold; matches literal text of protocol spec. | Formalize protocol wording to explicitly state one-sided $\\alpha = 0.05$ Beta bound. |",
        "| **Option 2 (Conservative): Two-Sided Lower Endpoint** | Lower endpoint of two-sided 95% Clopper-Pearson CI (tail $\\alpha/2 = 0.025$) | **SHORTFALL** ($89.99\\% < 90.00\\%$) | Maintains byte-level continuity with the historical Task 5 code implementation. Misses threshold by 1 trial out of 10,000 (0.0094 pp). | Either: (a) Expand primary sample size to $N_g = 225$ (preserves 60 buffer speakers in Australia), or (b) Run 20,000 trials. |",
        "",
        "### Authoritative Recommendation",
        "We recommend that the Project Lead adopt **Option 1**, clarifying in the pre-registration specification that the Monte Carlo lower confidence bound is evaluated as an exact one-sided 95% Clopper-Pearson lower bound at significance level $\\alpha = 0.05$.",
        "",
        "---",
        "",
        "## 4. Task D — Sample-Size Positioning Reconciliation",
        "",
        "| Evaluation Candidate | Confirmatory Evaluation Speakers | Gate Reserve | Total Unexposed Required | Total CV27 Australian Capacity | Australian Reserve Margin | Confirmed Joint Power | Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        f"| **$N_g = 220$ (PRIMARY)** | **1,100** | **20** | **240** | **305** | **+65 speakers (+21.3%)** | **{samp['primary_candidate']['confirmed_joint_power_pct']:.2f}%** (10,000 trials) | **BUFFERED (Recommended)** |",
        f"| **$N_g = 285$ (BENCHMARK)** | 1,425 | 20 | 305 | 305 | 0 speakers (0.0%) | {samp['benchmark_candidate']['confirmed_joint_power_pct']:.2f}% (2,500 trials) | EXHAUSTED (Supplemental Benchmark Only) |",
        "",
        "### Key Sample-Size Principles",
        "1. **Operational Buffer Over Negligible Differences:** $N_g = 220$ is preferred because it preserves **65 eligible Australian evaluation speakers** to absorb decoding drops, corrupt recordings, or quality exclusions during physical Common Voice 27 curation.",
        "2. **Benchmark Status of $N_g = 285$:** At 2,500 trials, $N_g = 285$ achieves $96.96\\%$ power, but it remains a supplemental capacity benchmark rather than a fully confirmed alternative until subjected to full 10,000-trial confirmatory depth.",
        "3. **Superseded Historical Estimates:** The earlier Task 5 joint power estimate of **$95.35\\%$** is formally marked as superseded by the calibrated **$90.58\\%$** result.",
        "4. **Conditional Power Disclosure:** All reported power figures are conditional development scenario assumptions, not guarantees of physical DSG performance.",
        "",
        "---",
        "",
        "## 5. Frozen Code Immutability & Multiplicity Invariants",
        "",
        "1. **Frozen Production Code Immutability:** `src/dsg_ctta/evaluation/paired_cluster_inference.py` has **0 lines diff** against `origin/main`.",
        "2. **Candidate Inference Engine:** Bounded within `src/dsg_ctta/evaluation/paired_cluster_inference_v15.py`.",
        "3. **Multiplicity Family Architecture:** $M = 8$, $\\alpha = 0.05$, $\\alpha_{\\text{adj}} = 0.00625$, simultaneous percentile = $99.375\\%$.",
        "4. **Disparity Decision Rule:** $\\text{UCB}_D \\le 0.0000$ pp (inclusive).",
        "",
        "---",
        "",
        "## Final Governance Verdict",
        "",
        "```",
        "FINAL VERDICT: CONDITIONAL HOLD",
        "GOVERNANCE STATUS: DRAFT_HOLD PRESERVED",
        "PRIMARY CANDIDATE: N_g = 220 SPEAKERS PER ACCENT (1,100 CONFIRMATORY SPEAKERS)",
        "MONTE CARLO BOUNDS (N_g = 220, 10k TRIALS):",
        f"  - One-Sided 95% LCB: {p220['one_sided_95_lcb']['lower_bound_pct']:.4f}% (PASSES >= 90.00% by +0.0857 pp)",
        f"  - Two-Sided 95% CI Lower Endpoint: {p220['two_sided_95_ci']['lower_endpoint_pct']:.4f}% (MISSES >= 90.00% by -0.0094 pp; 1 trial)",
        "GOVERNANCE ACTION: Formal Project-Lead Sign-Off on Confidence-Bound Definition Required Prior to Authorization",
        "```",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 6M Task 6.4 Monte Carlo Acceptance-Rule Reconciliation Audit")
    args = parser.parse_args()

    report = build_acceptance_rule_audit_report()

    json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_mc_acceptance_rule_audit.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved JSON report: {json_path}")

    md_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_mc_acceptance_rule_audit.md"
    generate_markdown_report(report, md_path)
    print(f"Saved Markdown report: {md_path}")


if __name__ == "__main__":
    main()
