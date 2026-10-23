#!/usr/bin/env python3
"""
scripts/run_stage6m_variable_clip_power_audit.py

Amended Statistical Power & Sensitivity Audit Package for Stage 6M Confirmatory Design.
======================================================================================
Standard: ADR-005
Protocol Version: v1.3.3-stage6m-reconciled-decision-pack
Supervisory Decision: Option 1B (Variable-Clip Reserve Policy within Common Voice 27.0)
Governance State: HOLD — STRICTLY NOT AUTHORIZED (execution_authorized = false)

Models the impact of variable-clip reserve replacements (C_s in [10, 14]) on within-speaker
estimation variance and confirmatory statistical power under Scenario 2 (Modest Disparity Drift:
delta = -0.85 pp, drift = +0.50 pp, UCB97.5 <= +1.40 pp).

Evaluates replacement scenarios:
- r = 0  (Baseline: 0 reserve replacements, all 78 Irish speakers have 15 clips)
- r = 5  (5 reserve replacements, C in {14, 13})
- r = 10 (10 reserve replacements, C in {14, 13, 12})
- r = 14 (14 reserve replacements, all available C >= 12 replacements drawn)
- r = 27 (27 reserve replacements, all available C in [10, 14] replacements drawn - stress test)

Generates reproducible artifact in reports/stage6m/variable_clip_power_audit_package/.
"""

import sys
import json
import math
import hashlib
import platform
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "reports" / "stage6m" / "variable_clip_power_audit_package"


def get_git_revision() -> str:
    """Retrieve current git revision hash if available."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "UNKNOWN_OR_UNTRACKED"


def compute_bootstrap_means(
    err_u: np.ndarray,
    err_g: np.ndarray,
    ng: int,
    b_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Fast BLAS-accelerated bootstrap mean computation."""
    idx = np.random.randint(0, ng, size=(b_count, ng))
    w = np.zeros((ng, b_count), dtype=np.float64)
    for b in range(b_count):
        w[:, b] = np.bincount(idx[b], minlength=ng) / ng
    means_u = np.matmul(err_u, w)
    means_g = np.matmul(err_g, w)
    return means_u, means_g


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson Score confidence interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0)
    p_hat = k / n
    denom = 1.0 + (z ** 2) / n
    center = (p_hat + (z ** 2) / (2.0 * n)) / denom
    margin = (z * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z ** 2) / (4.0 * (n ** 2)))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def clopper_pearson_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Clopper-Pearson exact confidence interval using Beta distribution."""
    if n == 0:
        return 0.0, 0.0
    alpha = 1.0 - confidence
    lower = stats.beta.ppf(alpha / 2.0, k, n - k + 1) if k > 0 else 0.0
    upper = stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k) if k < n else 1.0
    return float(lower), float(upper)


def run_variable_clip_audit(
    cohort_n: int = 468,
    spk_per_stratum: int = 78,
    n_reserve_replacements: int = 0,
    n_simulations: int = 20000,
    bootstrap_b: int = 1000,
    seed: int = 42,
) -> dict:
    """Execute power simulation accounting for variable clips in reserve replacements."""
    np.random.seed(seed)
    n_strata = 6
    sigma_speaker = 3.80
    rho_paired = 0.88
    sigma_diff_base = math.sqrt(2.0 * (sigma_speaker ** 2) * (1.0 - rho_paired))  # ~1.862 pp
    sigma_noise_base = sigma_speaker * math.sqrt(1.0 - rho_paired)  # ~1.316 pp (baseline for 15 clips)

    mu_g = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])
    true_delta = -0.85
    true_disp = 0.50
    shift_vec = np.linspace(-true_disp / 2.0, true_disp / 2.0, n_strata)

    # Deterministic clip counts for the 27 reserve Irish speakers (in drawing priority order):
    # 4 with 14, 5 with 13, 5 with 12, 4 with 11, 9 with 10
    reserve_clip_counts = [14] * 4 + [13] * 5 + [12] * 5 + [11] * 4 + [10] * 9

    # Vector of clip counts for all 78 Irish speakers (Stratum 0 = Irish English):
    # Base 78 all have 15 clips. If r replacements occur, the last r speakers have reserve clips.
    irish_clips = np.full(spk_per_stratum, 15, dtype=int)
    if n_reserve_replacements > 0:
        actual_r = min(n_reserve_replacements, len(reserve_clip_counts), spk_per_stratum)
        irish_clips[-actual_r:] = reserve_clip_counts[:actual_r]

    # Non-Irish strata (Strata 1-5) all have 15 clips per speaker
    # Scaling factor for noise standard deviation: sqrt(15 / C_s)
    # Shape: (n_strata, spk_per_stratum)
    noise_scale = np.ones((n_strata, spk_per_stratum), dtype=np.float64)
    noise_scale[0, :] = np.sqrt(15.0 / irish_clips)

    # Speaker random effects: common across unadapted and adapted models
    spk_eff = np.random.normal(0.0, sigma_speaker, (n_simulations, n_strata, spk_per_stratum))

    # Within-speaker observation noise with variance scaled by clip count
    base_noise_u = np.random.normal(0.0, sigma_noise_base, (n_simulations, n_strata, spk_per_stratum))
    base_noise_g = np.random.normal(0.0, sigma_noise_base, (n_simulations, n_strata, spk_per_stratum))

    noise_u = base_noise_u * noise_scale[None, :, :]
    noise_g = base_noise_g * noise_scale[None, :, :]

    err_u = mu_g[None, :, None] + spk_eff + noise_u
    err_g = (mu_g + shift_vec)[None, :, None] + spk_eff + noise_g + true_delta

    # Event A: Accented WER Superiority (One-sided paired t-test against zero)
    diffs = (err_g - err_u).reshape(n_simulations, -1)
    mean_diff = diffs.mean(axis=1)
    se_diff_est = diffs.std(axis=1, ddof=1) / math.sqrt(cohort_n)
    t_vals = mean_diff / se_diff_est
    t_crit_lower = stats.t.ppf(0.05, df=cohort_n - 1)
    t_crit_upper = stats.t.ppf(0.95, df=cohort_n - 1)
    pass_a = (t_vals < t_crit_lower)

    # Event B: Clean Non-Degradation (Inferential Approach B, UCB95 <= +0.50 pp)
    true_clean_shift = -0.30
    clean_noise_scale = np.ones(cohort_n, dtype=np.float64)
    clean_noise_scale[:spk_per_stratum] = np.sqrt(15.0 / irish_clips)
    diffs_clean = np.random.normal(true_clean_shift, sigma_diff_base * clean_noise_scale, (n_simulations, cohort_n))
    mean_clean = diffs_clean.mean(axis=1)
    se_clean = diffs_clean.std(axis=1, ddof=1) / math.sqrt(cohort_n)
    ucb95_clean = mean_clean + t_crit_upper * se_clean
    pass_b_inferential = (ucb95_clean <= 0.50)

    # Event C: Disparity Safety (Bootstrap Adjusted UCB97.5 <= +1.40 pp)
    means_u, means_g = compute_bootstrap_means(err_u, err_g, spk_per_stratum, bootstrap_b)
    boot_deltas = (means_g.max(axis=1) - means_g.min(axis=1)) - (means_u.max(axis=1) - means_u.min(axis=1))
    u975 = np.percentile(boot_deltas, 97.5, axis=1)
    pass_c_975 = (u975 <= 1.40)

    # Joint Decision: Approach B Inferential (A and B_inf and C_975)
    joint_success = pass_a & pass_b_inferential & pass_c_975
    k_success = int(np.sum(joint_success))
    p_hat = k_success / n_simulations

    # Monte Carlo Standard Error & CIs
    mc_se = math.sqrt(p_hat * (1.0 - p_hat) / n_simulations)
    wald_lower = max(0.0, p_hat - 1.96 * mc_se)
    wald_upper = min(1.0, p_hat + 1.96 * mc_se)
    wilson_lower, wilson_upper = wilson_score_interval(k_success, n_simulations, 0.95)
    cp_lower, cp_upper = clopper_pearson_interval(k_success, n_simulations, 0.95)

    # Net audio stream sizing under this replacement count
    clip_shortfall = int(np.sum(15 - irish_clips))
    total_stream_clips = cohort_n * 15 - clip_shortfall
    total_windows = math.ceil(total_stream_clips / 4.0)
    remainder_clips = total_stream_clips % 4
    final_window_clips = 4 if remainder_clips == 0 else remainder_clips
    candidate_update_opportunities = total_windows - 1  # Terminal window is strictly prediction-only

    rule_a_pass = bool(p_hat >= 0.8500)
    rule_b_wald_pass = bool(wald_lower >= 0.8500)
    rule_b_wilson_pass = bool(wilson_lower >= 0.8500)

    return {
        "cohort_n": cohort_n,
        "speakers_per_stratum": spk_per_stratum,
        "reserve_replacements_r": n_reserve_replacements,
        "irish_clip_counts_summary": {
            "total_irish_speakers": spk_per_stratum,
            "speakers_with_15_clips": int(np.sum(irish_clips == 15)),
            "speakers_with_14_clips": int(np.sum(irish_clips == 14)),
            "speakers_with_13_clips": int(np.sum(irish_clips == 13)),
            "speakers_with_12_clips": int(np.sum(irish_clips == 12)),
            "speakers_with_11_clips": int(np.sum(irish_clips == 11)),
            "speakers_with_10_clips": int(np.sum(irish_clips == 10)),
            "total_irish_clips": int(np.sum(irish_clips)),
            "clip_shortfall_from_invariant": clip_shortfall,
        },
        "stream_geometry": {
            "total_stream_clips": total_stream_clips,
            "total_windows": total_windows,
            "final_window_policy": "terminal_window_strictly_prediction_only",
            "final_window_clips": final_window_clips,
            "candidate_update_opportunities": candidate_update_opportunities,
        },
        "simulations_s": n_simulations,
        "bootstrap_b": bootstrap_b,
        "seed": seed,
        "successes_k": k_success,
        "estimated_power_p_hat": round(p_hat, 6),
        "mc_se": round(mc_se, 6),
        "wald_95_ci": [round(wald_lower, 6), round(wald_upper, 6)],
        "wilson_95_ci": [round(wilson_lower, 6), round(wilson_upper, 6)],
        "clopper_pearson_95_ci": [round(cp_lower, 6), round(cp_upper, 6)],
        "rule_a_verdict": "PASS" if rule_a_pass else "FAIL",
        "rule_b_wald_verdict": "PASS" if rule_b_wald_pass else "FAIL",
        "rule_b_wilson_verdict": "PASS" if rule_b_wilson_pass else "FAIL",
    }


def main():
    start_time = datetime.now(timezone.utc).isoformat()
    git_rev = get_git_revision()

    print("=" * 90)
    print("STAGE 6M VARIABLE-CLIP STATISTICAL POWER & SENSITIVITY AUDIT (OPTION 1B)")
    print("=" * 90)
    print(f"Timestamp UTC: {start_time}")
    print(f"Git Revision:  {git_rev}")
    print(f"Python:        {sys.version.split()[0]} on {platform.system()} {platform.release()}")
    print("-" * 90)

    # Scenarios for reserve replacement counts: r in {0, 5, 10, 14, 27}
    scenarios = [
        {"r": 0, "s": 20000, "seed": 42101, "desc": "Baseline (0 replacements; 78 Irish @ 15 clips)"},
        {"r": 5, "s": 20000, "seed": 42102, "desc": "Modest Dropout (5 replacements; 4@14, 1@13)"},
        {"r": 10, "s": 20000, "seed": 42103, "desc": "Substantial Dropout (10 replacements; 4@14, 5@13, 1@12)"},
        {"r": 14, "s": 20000, "seed": 42104, "desc": "Full C>=12 Pool Exhausted (14 replacements; 4@14, 5@13, 5@12)"},
        {"r": 27, "s": 20000, "seed": 42105, "desc": "Extreme Stress Test (All 27 replacements drawn; down to C=10)"},
    ]

    results = []
    for sc in scenarios:
        res = run_variable_clip_audit(
            cohort_n=468,
            spk_per_stratum=78,
            n_reserve_replacements=sc["r"],
            n_simulations=sc["s"],
            seed=sc["seed"]
        )
        res["scenario_description"] = sc["desc"]
        results.append(res)

        p_pct = res["estimated_power_p_hat"] * 100
        se_pct = res["mc_se"] * 100
        wil_l = res["wilson_95_ci"][0] * 100
        wil_u = res["wilson_95_ci"][1] * 100
        clips = res["stream_geometry"]["total_stream_clips"]
        shortfall = res["irish_clip_counts_summary"]["clip_shortfall_from_invariant"]

        print(
            f"r={res['reserve_replacements_r']:2d} | "
            f"Clips: {clips:4d} (Delta: -{shortfall:2d}) | "
            f"Power: {p_pct:5.2f}% +/- {se_pct:4.2f}% | "
            f"Wilson 95% CI: [{wil_l:5.2f}%, {wil_u:5.2f}%] | "
            f"Rule A (>=85%): {res['rule_a_verdict']} | "
            f"Rule B: {res['rule_b_wilson_verdict']}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "audit_summary.json"

    package = {
        "metadata": {
            "protocol_version": "v1.3.3-stage6m-reconciled-decision-pack",
            "governing_standard": "ADR-005",
            "supervisory_decision": "Option 1B (Variable-Clip Reserve in Common Voice 27.0)",
            "streaming_architecture": "Option 2A (Full Continuous Stream Reference)",
            "sequential_error_control": "Lan-DeMets O'Brien-Fleming with Two-Stage Pre-Screen (Leading Candidate)",
            "execution_timestamp_utc": start_time,
            "git_revision": git_rev,
            "system_info": {
                "os": platform.system(),
                "release": platform.release(),
                "python_version": sys.version.split()[0],
                "numpy_version": np.__version__,
            },
            "monte_carlo_repetitions": "S = 20,000 trials per replacement condition (SE <= 0.25 pp)",
            "status": "Awaiting Supervisor Written Sign-Off in Section 11 of stage6m_protocol_proposal.md",
        },
        "variable_clip_power_audit_results": results,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)

    with open(out_file, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    print("-" * 90)
    print(f"Amended audit summary written to: {out_file}")
    print(f"SHA-256 Digest:                   {file_hash}")
    print("=" * 90)


if __name__ == "__main__":
    main()
