"""
Stage 6M: Shared Production Streaming Safety Gate Evaluator.
============================================================
Protocol: v1.3.4-stage6m-self-authorization-amendment | Standard: ADR-005

Implements the canonical tripartite Upper Confidence Bound (UCB) safety rules
for streaming test-time adaptation with:
1. Paired, speaker-cluster robust standard error for overall risk Delta_R.
2. Separate per-stratum cluster-robust standard errors and worst subgroup regression UCB_max_g.
3. Separate paired cluster-robust standard error for cross-stratum disparity change UCB_D.
4. Calibrated Lan-DeMets O'Brien-Fleming sequential alpha-spending boundary schedule.

Enforces:
ACCEPT iff UCB(Delta_R) <= epsilon_R
       and UCB_max_g <= epsilon_G
       and UCB(Delta_D) <= epsilon_D
       and Delta_R <= 0.00
Otherwise REJECT with live model parameter rollback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy import stats


def compute_calibrated_obf_schedule(
    num_updates: int = 224,
    alpha_target: float = 0.05,
    max_clip: float = 4.5,
) -> np.ndarray:
    """
    Computes the calibrated Lan-DeMets O'Brien-Fleming critical boundary schedule.
    
    The critical value schedule scales with 1 / sqrt(t) where t = u / U is the
    information fraction. The critical constant C*(alpha) = Phi^{-1}(1 - alpha / 2)
    is derived directly from the reflection principle of standard Brownian motion:
        P(max_{k=1..U} B(t_k) >= C*) <= P(sup_{t in [0, 1]} B(t) >= C*) = 2(1 - Phi(C*)) = alpha.
    
    For alpha=0.05, C* = 1.9600; for alpha=0.01, C* = 2.5758. The schedule scales
    strictly with the user's configured alpha_target, guaranteeing that cumulative
    Type-I error across all U looks is bounded above by alpha_target.
    """
    t_steps = np.arange(1, num_updates + 1)
    info_frac = t_steps / float(num_updates)
    
    c_star = float(stats.norm.ppf(1.0 - alpha_target / 2.0))
    min_clip = c_star
    raw_schedule = c_star / np.sqrt(info_frac)
    return np.clip(raw_schedule, min_clip, max_clip)


def simulate_sequential_type1_error(
    num_updates: int = 224,
    num_trajectories: int = 20000,
    seed: int = 42,
    alpha_target: float = 0.05,
    max_clip: float = 4.5,
) -> Dict[str, Any]:
    """
    Monte Carlo simulation of cumulative family-wise Type-I error across all sequential looks.
    Generates standardized Gaussian random walks under the null hypothesis (zero drift)
    and evaluates the empirical boundary crossing probability with a 95% Wilson score confidence interval.
    """
    rng = np.random.default_rng(seed)
    sched = compute_calibrated_obf_schedule(
        num_updates=num_updates,
        alpha_target=alpha_target,
        max_clip=max_clip,
    )
    increments = rng.standard_normal((num_trajectories, num_updates))
    scores = np.cumsum(increments, axis=1)
    k_vals = np.arange(1, num_updates + 1)
    z_vals = scores / np.sqrt(k_vals)
    crossings = np.any(z_vals >= sched, axis=1)
    k_cross = int(np.sum(crossings))
    p_hat = k_cross / float(num_trajectories)

    # 95% Wilson score confidence interval for binomial proportion
    z_crit = 1.95996
    denom = 1.0 + z_crit**2 / num_trajectories
    center = (p_hat + z_crit**2 / (2.0 * num_trajectories)) / denom
    half = z_crit * math.sqrt((p_hat * (1.0 - p_hat) + z_crit**2 / (4.0 * num_trajectories)) / num_trajectories) / denom
    ci_low = max(0.0, center - half)
    ci_high = min(1.0, center + half)

    return {
        "alpha_target": float(alpha_target),
        "c_star": round(float(stats.norm.ppf(1.0 - alpha_target / 2.0)), 4),
        "num_trajectories": int(num_trajectories),
        "crossings": k_cross,
        "empirical_fwer": round(p_hat, 4),
        "ci_95": (round(ci_low, 4), round(ci_high, 4)),
        "statistically_controlled": bool(p_hat <= alpha_target and ci_high <= alpha_target + 0.005),
    }


@dataclass(frozen=True)
class StreamingGateDecision:
    """Structured record for an online candidate gating decision."""
    window_id: int
    decision: str                      # "ACCEPT" or "REJECT"
    passed_gate: bool
    delta_r: float                     # Percentage points
    se_r: float                        # Paired speaker-cluster SE for Delta_R (pp)
    ucb_r: float                       # Delta_R + z_t * se_r (pp)
    max_delta_g: float                 # Worst empirical subgroup change (pp)
    ucb_max_group: float               # Worst subgroup UCB (pp)
    worst_group: str                   # Stratum with worst UCB_g
    delta_d: float                     # Disparity change (pp)
    se_d: float                        # Paired SE for Delta_D (pp)
    ucb_d: float                       # Delta_D + z_t * se_d (pp)
    z_obf: float                       # OBF critical multiplier
    epsilon_r: float                   # Tolerance for Delta_R (pp)
    epsilon_g: float                   # Tolerance for max_g Delta_g (pp)
    epsilon_d: float                   # Tolerance for Delta_D (pp)
    rejection_reasons: List[str]       # Specific constraints violated
    group_deltas: Dict[str, float]     # Per-group delta_g (pp)
    group_ucbs: Dict[str, float]       # Per-group ucb_g (pp)
    group_ses: Dict[str, float]        # Per-group se_g (pp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StreamingSentinelSafetyGate:
    """
    Canonical production gate evaluator used across all Stage 6M streaming runners.
    Ensures identical statistical decision rules across local and virtual GPU benchmarks.
    """

    def __init__(
        self,
        epsilon_r_pp: float = 0.0000,
        epsilon_g_pp: float = 2.0000,
        epsilon_d_pp: float = 2.0000,
        num_updates: int = 224,
        alpha_target: float = 0.05,
    ):
        self.epsilon_r = float(epsilon_r_pp)
        self.epsilon_g = float(epsilon_g_pp)
        self.epsilon_d = float(epsilon_d_pp)
        self.num_updates = int(num_updates)
        self.alpha_target = float(alpha_target)
        self.z_schedule = compute_calibrated_obf_schedule(num_updates, alpha_target)

    def evaluate_candidate(
        self,
        window_id: int,
        speaker_ids: List[str],
        stratum_groups: List[str],
        live_errors: List[int],
        cand_errors: List[int],
        ref_lengths: List[int],
    ) -> StreamingGateDecision:
        """
        Evaluates candidate update safety using paired speaker-cluster delta-method uncertainty.

        Parameters:
        -----------
        window_id: Current stream adaptation window index (0-indexed).
        speaker_ids: Speaker ID for each sentinel utterance.
        stratum_groups: Stratum label for each sentinel utterance.
        live_errors: Total edit distance errors (S+D+I) under live model.
        cand_errors: Total edit distance errors (S+D+I) under candidate model.
        ref_lengths: Reference word count for each utterance.
        """
        assert len(speaker_ids) == len(stratum_groups) == len(live_errors) == len(cand_errors) == len(ref_lengths)
        n_items = len(speaker_ids)
        if n_items == 0:
            raise ValueError("Sentinel evaluation inputs cannot be empty.")

        # Aggregate counts at the speaker level
        spk_data: Dict[str, Dict[str, Any]] = {}
        strata_words: Dict[str, int] = {}
        strata_live_err: Dict[str, int] = {}
        strata_cand_err: Dict[str, int] = {}

        for i in range(n_items):
            sid = str(speaker_ids[i])
            grp = str(stratum_groups[i])
            el = int(live_errors[i])
            ec = int(cand_errors[i])
            nw = int(ref_lengths[i])

            if sid not in spk_data:
                spk_data[sid] = {"group": grp, "live_err": 0, "cand_err": 0, "words": 0}
            spk_data[sid]["live_err"] += el
            spk_data[sid]["cand_err"] += ec
            spk_data[sid]["words"] += nw

            strata_words[grp] = strata_words.get(grp, 0) + nw
            strata_live_err[grp] = strata_live_err.get(grp, 0) + el
            strata_cand_err[grp] = strata_cand_err.get(grp, 0) + ec

        total_words = sum(strata_words.values())
        total_live_errors = sum(strata_live_err.values())
        total_cand_errors = sum(strata_cand_err.values())

        # 1. Overall Risk Change Delta_R and Paired Cluster SE
        delta_r_frac = (total_cand_errors - total_live_errors) / float(total_words) if total_words > 0 else 0.0
        delta_r = delta_r_frac * 100.0  # pp

        S = len(spk_data)
        if S > 1 and total_words > 0:
            u_r_sq = sum(
                ((v["cand_err"] - v["live_err"]) - delta_r_frac * v["words"]) ** 2
                for v in spk_data.values()
            )
            var_r = (float(S) / (S - 1)) * u_r_sq / (float(total_words) ** 2)
            se_r = math.sqrt(max(0.0, var_r)) * 100.0
        else:
            se_r = 0.0

        # OBF multiplier for current look
        look_idx = min(window_id, len(self.z_schedule) - 1)
        z_t = float(self.z_schedule[look_idx])
        ucb_r = delta_r + z_t * se_r

        # 2. Per-Stratum Risk Change Delta_g, SE_g, and Worst Subgroup UCB
        group_deltas: Dict[str, float] = {}
        group_ses: Dict[str, float] = {}
        group_ucbs: Dict[str, float] = {}
        strata_names = sorted(strata_words.keys())

        for g in strata_names:
            nw_g = strata_words[g]
            el_g = strata_live_err[g]
            ec_g = strata_cand_err[g]
            d_g_frac = (ec_g - el_g) / float(nw_g) if nw_g > 0 else 0.0
            d_g_pp = d_g_frac * 100.0
            group_deltas[g] = round(d_g_pp, 4)

            # Cluster SE within stratum g
            spks_in_g = [v for v in spk_data.values() if v["group"] == g]
            S_g = len(spks_in_g)
            if S_g > 1 and nw_g > 0:
                u_g_sq = sum(
                    ((v["cand_err"] - v["live_err"]) - d_g_frac * v["words"]) ** 2
                    for v in spks_in_g
                )
                var_g = (float(S_g) / (S_g - 1)) * u_g_sq / (float(nw_g) ** 2)
                se_g = math.sqrt(max(0.0, var_g)) * 100.0
            else:
                se_g = 0.0

            group_ses[g] = round(se_g, 4)
            group_ucbs[g] = round(d_g_pp + z_t * se_g, 4)

        max_delta_g = max(group_deltas.values()) if group_deltas else 0.0
        worst_group = max(group_ucbs, key=group_ucbs.get) if group_ucbs else "NONE"
        ucb_max_group = group_ucbs[worst_group] if group_ucbs else 0.0

        # 3. Disparity Change Delta_D and Stratified Paired Speaker-Cluster Bootstrap
        live_strata_wers = {g: (strata_live_err[g] / float(strata_words[g]) * 100.0) for g in strata_names}
        cand_strata_wers = {g: (strata_cand_err[g] / float(strata_words[g]) * 100.0) for g in strata_names}

        disp_live = max(live_strata_wers.values()) - min(live_strata_wers.values())
        disp_cand = max(cand_strata_wers.values()) - min(cand_strata_wers.values())
        delta_d = disp_cand - disp_live

        # If live and candidate model predictions are identical across all speakers, delta_d is identically 0.0 with 0.0 variance
        all_identical = all(v["cand_err"] == v["live_err"] for v in spk_data.values())
        if all_identical:
            se_d = 0.0
        else:
            # Stratified paired cluster bootstrap: resamples speakers within each stratum
            # Recomputes the complete disparity statistic (max_g - min_g) for each replicate,
            # correctly capturing shifts in the extreme strata and multi-stratum covariance
            spks_by_group = {g: [v for v in spk_data.values() if v["group"] == g] for g in strata_names}
            rng_boot = np.random.default_rng(12345 + window_id)
            B = 200
            boot_delta_d = []

            for _ in range(B):
                rep_live_wers = []
                rep_cand_wers = []
                for g in strata_names:
                    cluster = spks_by_group[g]
                    S_g = len(cluster)
                    if S_g > 0:
                        idxs = rng_boot.integers(0, S_g, size=S_g)
                        rep_live_err = sum(cluster[j]["live_err"] for j in idxs)
                        rep_cand_err = sum(cluster[j]["cand_err"] for j in idxs)
                        rep_words = sum(cluster[j]["words"] for j in idxs)
                        rep_live_wers.append((rep_live_err / float(rep_words) * 100.0) if rep_words > 0 else 0.0)
                        rep_cand_wers.append((rep_cand_err / float(rep_words) * 100.0) if rep_words > 0 else 0.0)
                    else:
                        rep_live_wers.append(0.0)
                        rep_cand_wers.append(0.0)

                rep_disp_live = max(rep_live_wers) - min(rep_live_wers)
                rep_disp_cand = max(rep_cand_wers) - min(rep_cand_wers)
                boot_delta_d.append(rep_disp_cand - rep_disp_live)

            se_d = float(np.std(boot_delta_d, ddof=1))

        ucb_d = delta_d + z_t * se_d

        # 4. Tripartite Decision Rule
        rejection_reasons: List[str] = []
        if ucb_r > self.epsilon_r:
            rejection_reasons.append(f"Overall risk violation: UCB(Delta_R) = {ucb_r:+.2f}% > epsilon_R ({self.epsilon_r:.2f}%)")
        if delta_r > 0.00:
            rejection_reasons.append(f"Point degradation: Delta_R = {delta_r:+.2f}% > 0.00%")
        if ucb_max_group > self.epsilon_g:
            rejection_reasons.append(f"Subgroup regression violation in [{worst_group}]: UCB_g = {ucb_max_group:+.2f}% > epsilon_G ({self.epsilon_g:.2f}%)")
        if ucb_d > self.epsilon_d:
            rejection_reasons.append(f"Disparity growth violation: UCB(Delta_D) = {ucb_d:+.2f}% > epsilon_D ({self.epsilon_d:.2f}%)")

        passed = len(rejection_reasons) == 0
        decision_str = "ACCEPT" if passed else "REJECT"

        return StreamingGateDecision(
            window_id=window_id,
            decision=decision_str,
            passed_gate=passed,
            delta_r=round(delta_r, 4),
            se_r=round(se_r, 4),
            ucb_r=round(ucb_r, 4),
            max_delta_g=round(max_delta_g, 4),
            ucb_max_group=round(ucb_max_group, 4),
            worst_group=worst_group,
            delta_d=round(delta_d, 4),
            se_d=round(se_d, 4),
            ucb_d=round(ucb_d, 4),
            z_obf=round(z_t, 3),
            epsilon_r=self.epsilon_r,
            epsilon_g=self.epsilon_g,
            epsilon_d=self.epsilon_d,
            rejection_reasons=rejection_reasons,
            group_deltas=group_deltas,
            group_ucbs=group_ucbs,
            group_ses=group_ses,
        )
