#!/usr/bin/env python3
"""
scripts/simulate_stage6m_trajectory_safety.py

Trajectory-Level Sequential Safety Gate Simulation Engine for Stage 6M.
=======================================================================
Standard: ADR-005
Protocol Version: v1.3.3-stage6m-reconciled-decision-pack
Governance State: HOLD — STRICTLY NOT AUTHORIZED (execution_authorized = false)

Simulates the complete 1,754-candidate adaptation stream to evaluate:
1. Global Trajectory Error Event:
   P(Accept at least one candidate where true Delta_G > tau_G or true Delta_D > tau_D)
2. Multiple Testing vs. Adaptive Overfitting:
   Evaluates impact of repeated screening against the SAME fixed 30-speaker Sentinel Panel
3. Comparative Error-Control Rules:
   - Nominal Uncorrected Step Gate (alpha_step = 0.025 / UCB97.5)
   - Bonferroni Trajectory Boundary (alpha_step = 0.05 / (1754 * 2) = 1.425e-5)
   - Lan-DeMets Alpha-Spending (O'Brien-Fleming boundary)
   - Two-Stage Hierarchical Gate (Unsupervised Entropy Pre-screen + Calibrated Sentinel Gate)
4. Rigorous Low-Event Confidence Intervals:
   - Wilson Score 95% Confidence Interval
   - Clopper-Pearson Exact 95% Binomial Interval
   - Exact one-sided 95% upper bound when zero events observed (1 - 0.05^(1/n))
5. Exact Workload Accounting:
   Reconciles Sentinel Panel invocations (1,754 vs 1,603 = 8.61% reduction in Regime 2)
   with full clip decodings (526,200 vs 480,900 clips).
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = PROJECT_ROOT / "reports" / "stage6m" / "trajectory_safety_simulation_results.json"


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


def evaluate_regime(
    regime_name: str,
    n_trajectories: int,
    n_updates: int,
    n_sentinel_speakers: int,
    clips_per_sentinel_speaker: int,
    unsafe_prob: float,
    sigma_speaker: float,
    sigma_noise: float,
    tau_g: float,
    tau_d: float,
    seed: int,
    is_borderline: bool = False,
):
    np.random.seed(seed)
    n_strata = 6
    speakers_per_stratum = n_sentinel_speakers // n_strata  # 5
    alpha_target = 0.05
    sentinel_clips_per_eval = n_sentinel_speakers * clips_per_sentinel_speaker  # 300

    z_nominal = stats.norm.ppf(0.975)  # 1.96
    alpha_bonf = alpha_target / (n_updates * 2.0)
    z_bonf = stats.norm.ppf(1.0 - alpha_bonf)  # ~4.18

    t_steps = np.arange(1, n_updates + 1)
    info_frac = t_steps / n_updates
    z_obf = np.clip(stats.norm.ppf(1.0 - alpha_target / 4.0) / np.sqrt(info_frac), 1.96, 5.0)

    strategies = [
        "nominal_uncorrected_ucb975",
        "bonferroni_trajectory_gate",
        "obrien_fleming_alpha_spending",
        "hierarchical_prescreen_obf",
    ]

    false_deployments = {s: 0 for s in strategies}
    safe_acceptances = {s: 0 for s in strategies}
    total_safe_candidates = 0
    total_unsafe_candidates = 0
    sentinel_evaluations_count = {s: 0 for s in strategies}

    for traj_idx in range(n_trajectories):
        sent_spk_intercepts = np.random.normal(0.0, sigma_speaker, (n_strata, speakers_per_stratum))
        deployed_unsafe = {s: False for s in strategies}

        for t in range(n_updates):
            is_unsafe = np.random.rand() < unsafe_prob

            if is_unsafe:
                total_unsafe_candidates += 1
                if is_borderline:
                    true_delta_g = np.random.uniform(0.51, 0.65)
                    true_delta_d = np.random.uniform(1.41, 1.65)
                    entropy_reduction = np.random.normal(-0.12, 0.08)
                else:
                    true_delta_g = np.random.uniform(0.65, 1.30)
                    true_delta_d = np.random.uniform(1.60, 2.50)
                    entropy_reduction = np.random.normal(0.05, 0.10)
            else:
                total_safe_candidates += 1
                true_delta_g = np.random.uniform(-0.60, 0.20)
                true_delta_d = np.random.uniform(-0.50, 0.80)
                entropy_reduction = np.random.normal(-0.25, 0.08)

            se_g = math.sqrt(2.0 * (sigma_noise ** 2) / sentinel_clips_per_eval)
            se_d = math.sqrt(2.0 * (sigma_noise ** 2) / (speakers_per_stratum * clips_per_sentinel_speaker))

            spk_distortion = float(np.mean(sent_spk_intercepts)) * 0.10
            meas_delta_g = true_delta_g + spk_distortion + np.random.normal(0.0, se_g)
            meas_delta_d = true_delta_d + spk_distortion + np.random.normal(0.0, se_d)

            # Strategy 1: Nominal Uncorrected UCB97.5
            sentinel_evaluations_count["nominal_uncorrected_ucb975"] += 1
            acc_nom = (meas_delta_g + z_nominal * se_g <= tau_g) and (meas_delta_d + z_nominal * se_d <= tau_d)
            if acc_nom:
                if is_unsafe:
                    deployed_unsafe["nominal_uncorrected_ucb975"] = True
                else:
                    safe_acceptances["nominal_uncorrected_ucb975"] += 1

            # Strategy 2: Bonferroni Boundary
            sentinel_evaluations_count["bonferroni_trajectory_gate"] += 1
            acc_bonf = (meas_delta_g + z_bonf * se_g <= tau_g) and (meas_delta_d + z_bonf * se_d <= tau_d)
            if acc_bonf:
                if is_unsafe:
                    deployed_unsafe["bonferroni_trajectory_gate"] = True
                else:
                    safe_acceptances["bonferroni_trajectory_gate"] += 1

            # Strategy 3: O'Brien-Fleming Alpha Spending
            sentinel_evaluations_count["obrien_fleming_alpha_spending"] += 1
            z_t = z_obf[t]
            acc_obf = (meas_delta_g + z_t * se_g <= tau_g) and (meas_delta_d + z_t * se_d <= tau_d)
            if acc_obf:
                if is_unsafe:
                    deployed_unsafe["obrien_fleming_alpha_spending"] = True
                else:
                    safe_acceptances["obrien_fleming_alpha_spending"] += 1

            # Strategy 4: Two-Stage Hierarchical Screening Gate
            if entropy_reduction <= -0.10:
                sentinel_evaluations_count["hierarchical_prescreen_obf"] += 1
                acc_h = (meas_delta_g + z_t * se_g <= tau_g) and (meas_delta_d + z_t * se_d <= tau_d)
            else:
                acc_h = False

            if acc_h:
                if is_unsafe:
                    deployed_unsafe["hierarchical_prescreen_obf"] = True
                else:
                    safe_acceptances["hierarchical_prescreen_obf"] += 1

        for s in strategies:
            if deployed_unsafe[s]:
                false_deployments[s] += 1

    regime_results = {}
    print(f"\n--- {regime_name.upper()} ---")
    print(f"{'Strategy':32s} | {'Events (k/N)':14s} | {'FWER':8s} | {'Wilson 95% CI':16s} | {'Clopper-Pearson 95% CI':23s} | {'Safe Acc':8s} | {'Invocations (Savings)'}")
    print("-" * 125)

    base_invocations = n_updates  # 1,754
    for s in strategies:
        k = false_deployments[s]
        fwer = k / n_trajectories
        safe_acc_rate = safe_acceptances[s] / total_safe_candidates if total_safe_candidates > 0 else 0.0
        avg_invocations = sentinel_evaluations_count[s] / n_trajectories
        invocation_reduction_pct = ((base_invocations - avg_invocations) / base_invocations) * 100.0
        clip_decodings = avg_invocations * sentinel_clips_per_eval

        # Wilson score interval
        w_low, w_high = wilson_score_interval(k, n_trajectories, 0.95)
        # Clopper-Pearson exact interval
        cp_low, cp_high = clopper_pearson_interval(k, n_trajectories, 0.95)
        # Exact one-sided 95% upper bound when zero events
        zero_event_upper = (1.0 - (0.05 ** (1.0 / n_trajectories))) if k == 0 else cp_high

        regime_results[s] = {
            "false_deployment_events_k": k,
            "total_trajectories_n": n_trajectories,
            "trajectory_fwer": round(fwer, 6),
            "wilson_score_95ci": [round(w_low, 6), round(w_high, 6)],
            "clopper_pearson_exact_95ci": [round(cp_low, 6), round(cp_high, 6)],
            "exact_one_sided_95_upper_bound": round(zero_event_upper, 6),
            "safe_candidate_acceptance_rate": round(safe_acc_rate, 4),
            "average_sentinel_invocations": round(avg_invocations, 1),
            "sentinel_invocation_reduction_pct": round(invocation_reduction_pct, 2),
            "full_panel_clip_decodings": round(clip_decodings, 0),
            "fwer_controlled_le_005": bool(fwer <= 0.05),
        }

        savings_str = f"{avg_invocations:,.0f} (-{invocation_reduction_pct:.2f}%)" if invocation_reduction_pct > 0 else f"{avg_invocations:,.0f} (Baseline)"
        print(
            f"{s:32s} | {k:3d} / {n_trajectories:3d}   | {fwer*100:5.2f}% | "
            f"[{w_low*100:4.2f}%, {w_high*100:4.2f}%] | "
            f"[{cp_low*100:4.2f}%, {cp_high*100:4.2f}%]       | "
            f"{safe_acc_rate*100:5.2f}% | {savings_str}"
        )

    return regime_results


def main():
    start_time = datetime.now(timezone.utc).isoformat()
    n_trajectories = 500
    n_updates = 1754
    n_sentinel_speakers = 30
    clips_per_sentinel_speaker = 10
    sigma_speaker = 3.80
    sigma_noise = 1.316
    tau_g = 0.50
    tau_d = 1.40

    print("=" * 125)
    print("STAGE 6M SEQUENTIAL TRAJECTORY SAFETY GATE SIMULATION (EXACT INTERVALS & RECONCILED WORKLOAD)")
    print("=" * 125)

    res_gross = evaluate_regime(
        regime_name="Regime 1: Gross Regressions",
        n_trajectories=n_trajectories,
        n_updates=n_updates,
        n_sentinel_speakers=n_sentinel_speakers,
        clips_per_sentinel_speaker=clips_per_sentinel_speaker,
        unsafe_prob=0.15,
        sigma_speaker=sigma_speaker,
        sigma_noise=sigma_noise,
        tau_g=tau_g,
        tau_d=tau_d,
        seed=20261017,
        is_borderline=False,
    )

    res_borderline = evaluate_regime(
        regime_name="Regime 2: Borderline Drift (Near-Boundary Harm)",
        n_trajectories=n_trajectories,
        n_updates=n_updates,
        n_sentinel_speakers=n_sentinel_speakers,
        clips_per_sentinel_speaker=clips_per_sentinel_speaker,
        unsafe_prob=0.15,
        sigma_speaker=sigma_speaker,
        sigma_noise=sigma_noise,
        tau_g=tau_g,
        tau_d=tau_d,
        seed=20261018,
        is_borderline=True,
    )

    output_payload = {
        "metadata": {
            "protocol_version": "v1.3.3-stage6m-reconciled-decision-pack",
            "governing_standard": "ADR-005",
            "timestamp_utc": start_time,
            "trajectories_evaluated": n_trajectories,
            "updates_per_trajectory": n_updates,
            "sentinel_speakers": n_sentinel_speakers,
            "clips_per_sentinel_speaker": clips_per_sentinel_speaker,
            "sentinel_clips_per_evaluation": n_sentinel_speakers * clips_per_sentinel_speaker,
            "global_safety_tolerances": {"tau_G_pp": tau_g, "tau_D_pp": tau_d},
            "confidence_interval_methods": ["Wilson Score (95%)", "Clopper-Pearson Exact (95%)", "Exact One-Sided Upper Bound (for k=0)"],
        },
        "regime_1_gross_regressions": res_gross,
        "regime_2_borderline_regressions": res_borderline,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print("\n" + "=" * 125)
    print(f"Results successfully serialized to: {OUT_JSON}")
    print("=" * 125)


if __name__ == "__main__":
    main()
