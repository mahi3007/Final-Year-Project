#!/usr/bin/env python3
"""
scripts/run_stage6m_power_audit.py

Reproducible Statistical Power Audit Package for Stage 6M Confirmatory Design.
================================================================================
Standard: ADR-005
Protocol Version: v1.2.0-stage6m-proposal
Governance State: HOLD — STRICTLY NOT AUTHORIZED (execution_authorized = false)

Fulfills Reviewer Requirement for Correction 1:
- Prespecified Monte Carlo simulation repetition budget (S in {4,000, 10,000, 20,000})
- Fixed, prespecified pseudo-random seeds
- Multiple confidence interval methods:
    1. Normal Wald Approximation (Historical Baseline)
    2. Wilson Score Interval (Boundary-Consistent)
    3. Clopper-Pearson Exact Interval (Conservative Non-Asymptotic)
- Compares N=468 (Full Proposed Cohort, 78/stratum) vs N=420 (Reduced Cohort, 70/stratum)
- Evaluates Scenario 2 (Modest Disparity Drift: delta = -0.85 pp, drift = +0.50 pp, UCB97.5 <= +1.40 pp)
- Generates reproducible machine-readable summary artifact in reports/stage6m/reproducible_power_audit_package/
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
AUDIT_DIR = PROJECT_ROOT / "reports" / "stage6m" / "reproducible_power_audit_package"


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


def run_single_audit(
    cohort_n: int,
    spk_per_stratum: int,
    n_simulations: int,
    bootstrap_b: int = 1000,
    seed: int = 42,
) -> dict:
    """Execute single power audit condition under Scenario 2."""
    np.random.seed(seed)
    n_strata = 6
    sigma_speaker = 3.80
    rho_paired = 0.88
    sigma_diff = math.sqrt(2.0 * (sigma_speaker ** 2) * (1.0 - rho_paired))  # ~1.862 pp
    sigma_noise = sigma_speaker * math.sqrt(1.0 - rho_paired)  # ~1.316 pp
    mu_g = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])

    true_delta = -0.85
    true_disp = 0.50
    shift_vec = np.linspace(-true_disp / 2.0, true_disp / 2.0, n_strata)

    # Generate synthetic experimental observations
    spk_eff = np.random.normal(0.0, sigma_speaker, (n_simulations, n_strata, spk_per_stratum))
    noise_u = np.random.normal(0.0, sigma_noise, (n_simulations, n_strata, spk_per_stratum))
    noise_g = np.random.normal(0.0, sigma_noise, (n_simulations, n_strata, spk_per_stratum))

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
    diffs_clean = np.random.normal(true_clean_shift, sigma_diff, (n_simulations, cohort_n))
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

    # Monte Carlo Standard Error
    mc_se = math.sqrt(p_hat * (1.0 - p_hat) / n_simulations)

    # Confidence Intervals
    wald_lower = max(0.0, p_hat - 1.96 * mc_se)
    wald_upper = min(1.0, p_hat + 1.96 * mc_se)

    wilson_lower, wilson_upper = wilson_score_interval(k_success, n_simulations, 0.95)
    cp_lower, cp_upper = clopper_pearson_interval(k_success, n_simulations, 0.95)

    # Evaluation against Protocol Rules (Threshold = 0.8500)
    rule_a_pass = bool(p_hat >= 0.8500)
    rule_b_wald_pass = bool(wald_lower >= 0.8500)
    rule_b_wilson_pass = bool(wilson_lower >= 0.8500)
    rule_b_cp_pass = bool(cp_lower >= 0.8500)

    return {
        "cohort_n": cohort_n,
        "speakers_per_stratum": spk_per_stratum,
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
        "rule_b_cp_verdict": "PASS" if rule_b_cp_pass else "FAIL",
    }


def main():
    start_time = datetime.now(timezone.utc).isoformat()
    git_rev = get_git_revision()

    print("=" * 80)
    print("STAGE 6M REPRODUCIBLE STATISTICAL POWER AUDIT")
    print("=" * 80)
    print(f"Timestamp UTC: {start_time}")
    print(f"Git Revision:  {git_rev}")
    print(f"Python:        {sys.version.split()[0]} on {platform.system()} {platform.release()}")
    print("-" * 80)

    scenarios = [
        # N=468 (Full balanced proposed cohort: 78/stratum)
        {"cohort_n": 468, "ng": 78, "s": 4000, "seed": 42001},
        {"cohort_n": 468, "ng": 78, "s": 10000, "seed": 42002},
        {"cohort_n": 468, "ng": 78, "s": 20000, "seed": 42003},
        # N=420 (Reduced cohort: 70/stratum)
        {"cohort_n": 420, "ng": 70, "s": 4000, "seed": 42004},
        {"cohort_n": 420, "ng": 70, "s": 10000, "seed": 42005},
        {"cohort_n": 420, "ng": 70, "s": 20000, "seed": 42006},
    ]

    results = []
    for sc in scenarios:
        res = run_single_audit(
            cohort_n=sc["cohort_n"],
            spk_per_stratum=sc["ng"],
            n_simulations=sc["s"],
            seed=sc["seed"]
        )
        results.append(res)
        p_pct = res["estimated_power_p_hat"] * 100
        se_pct = res["mc_se"] * 100
        w_l = res["wald_95_ci"][0] * 100
        w_u = res["wald_95_ci"][1] * 100
        wil_l = res["wilson_95_ci"][0] * 100
        print(
            f"N={res['cohort_n']:3d} ({res['speakers_per_stratum']:2d}/stratum) | "
            f"S={res['simulations_s']:5d} | "
            f"Power: {p_pct:5.2f}% +/- {se_pct:4.2f}% | "
            f"Wald 95% CI: [{w_l:5.2f}%, {w_u:5.2f}%] | "
            f"Wilson Lower: {wil_l:5.2f}% | "
            f"Rule A: {res['rule_a_verdict']} | Rule B: {res['rule_b_wald_verdict']}"
        )

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = AUDIT_DIR / "audit_summary.json"

    package = {
        "metadata": {
            "protocol_version": "v1.2.0-stage6m-proposal",
            "governing_standard": "ADR-005",
            "execution_timestamp_utc": start_time,
            "git_revision": git_rev,
            "system_info": {
                "os": platform.system(),
                "release": platform.release(),
                "python_version": sys.version.split()[0],
                "numpy_version": np.__version__,
            },
            "investigation_focus": "Monte Carlo Precision vs. Statistical Power Distinction",
            "preregistered_monte_carlo_precision_budget": "S = 20,000 trials (Target Margin of Error <= 0.30 pp)",
            "status": "Simulation precision audit executed; physical study power contingent on real-world DGP alignment",
        },
        "audit_results": results,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)

    with open(out_file, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    print("-" * 80)
    print(f"Audit summary written to: {out_file}")
    print(f"SHA-256 Digest:           {file_hash}")
    print("=" * 80)


if __name__ == "__main__":
    main()
