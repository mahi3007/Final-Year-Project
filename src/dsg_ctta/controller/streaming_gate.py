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
) -> np.ndarray:
    """
    Computes the exact, unclipped Lan-DeMets O'Brien-Fleming critical boundary schedule.
    
    The critical value schedule scales strictly with 1 / sqrt(t) where t = u / U is the
    information fraction. The critical constant C*(alpha) = Phi^{-1}(1 - alpha / 2)
    is derived directly from the reflection principle of standard Brownian motion:
        P(max_{k=1..U} B(t_k) >= C*) <= P(sup_{t in [0, 1]} B(t) >= C*) = 2(1 - Phi(C*)) = alpha.
    
    Because no artificial upper clipping is applied, for all k in {1..U}:
        Z(t_k) >= z_k  <=>  Z(t_k) >= C*(alpha) / sqrt(t_k)
                       <=>  sqrt(t_k) * Z(t_k) >= C*(alpha)
                       <=>  B(t_k) >= C*(alpha).
    Consequently, the sequential crossing event {exists k : Z(t_k) >= z_k} is IDENTICAL
    to {max_{k=1..U} B(t_k) >= C*(alpha)}, and its probability under the null hypothesis
    is rigorously bounded above by alpha_target for any number of looks U >= 1.
    
    For alpha=0.05, C* = 1.9600 (terminal bound z_U = 1.9600; initial bound z_1 = 29.33).
    For alpha=0.01, C* = 2.5758 (terminal bound z_U = 2.5758; initial bound z_1 = 38.55).
    """
    t_steps = np.arange(1, num_updates + 1)
    info_frac = t_steps / float(num_updates)
    c_star = float(stats.norm.ppf(1.0 - alpha_target / 2.0))
    return c_star / np.sqrt(info_frac)


def simulate_sequential_type1_error(
    num_updates: int = 224,
    num_trajectories: int = 50000,
    seed: int = 42,
    alpha_target: float = 0.05,
) -> Dict[str, Any]:
    """
    Monte Carlo simulation of cumulative family-wise Type-I error across all sequential looks
    under the canonical Gaussian random-walk null model underpinning Lan-DeMets alpha spending.
    
    Generates standardized Gaussian random walks under the null hypothesis (zero drift)
    and evaluates the empirical boundary crossing probability with an exact 95% Wilson
    score confidence interval.
    
    Epistemic Note:
    ---------------
    This simulation establishes strict boundary validity under the standard Gaussian random-walk
    model. In physical streaming ASR, successive updates and overlapping speaker data introduce
    empirical dependencies, which are evaluated via multi-criterion streaming simulations
    and physical acoustic streaming runs.
    """
    rng = np.random.default_rng(seed)
    sched = compute_calibrated_obf_schedule(
        num_updates=num_updates,
        alpha_target=alpha_target,
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
        "empirical_fwer": round(p_hat, 5),
        "ci_95": (round(ci_low, 5), round(ci_high, 5)),
        "statistically_controlled": bool(p_hat <= alpha_target and ci_high <= alpha_target),
    }


def simulate_multicriterion_streaming_gate_null(
    num_streams: int = 1000,
    num_updates: int = 224,
    alpha_target: float = 0.05,
    num_boot_replicates: int = 100,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Simulates complete multi-criterion streaming trajectories under the deployed shared-sentinel null process.
    Models repeated evaluations on a fixed 30-speaker sentinel panel across 6 strata (5 speakers/stratum).
    Captures speaker-level baseline error rates, fixed sentinel observations for the live model,
    stochastic candidate updates under the null, and joint tripartite decision rules (overall risk,
    subgroup UCBs, and disparity change).
    
    Demonstrates family-wise false-acceptance control (FWER <= alpha_target) with Wilson score confidence bounds.
    """
    gate = StreamingSentinelSafetyGate(
        epsilon_r_pp=0.0000,
        epsilon_g_pp=2.0000,
        epsilon_d_pp=2.0000,
        num_updates=num_updates,
        alpha_target=alpha_target,
        num_boot_replicates=num_boot_replicates,
    )
    rng = np.random.default_rng(seed)
    speaker_ids = [f"spk_{i}" for i in range(30)]
    stratum_groups = [f"grp_{i // 5}" for i in range(30)]
    ref_lengths = [15] * 30

    false_accepts = 0
    for _ in range(num_streams):
        # Fixed speaker error rate profile across the entire stream
        base_probs = rng.uniform(0.12, 0.28, size=30)
        # Fixed sentinel observations for live model across repeated looks
        live_err = [int(rng.binomial(15, p)) for p in base_probs]
        accepted = False
        for u in range(num_updates):
            # Candidate updates under the null: identical underlying speaker error distribution
            cand_err = [int(rng.binomial(15, p)) for p in base_probs]
            dec = gate.evaluate_candidate(u, speaker_ids, stratum_groups, live_err, cand_err, ref_lengths)
            if dec.passed_gate:
                accepted = True
                break
        if accepted:
            false_accepts += 1

    p_hat = false_accepts / float(num_streams)
    # 95% Wilson score confidence interval
    z_crit = 1.95996
    denom = 1.0 + z_crit**2 / num_streams
    center = (p_hat + z_crit**2 / (2.0 * num_streams)) / denom
    half = z_crit * math.sqrt((p_hat * (1.0 - p_hat) + z_crit**2 / (4.0 * num_streams)) / num_streams) / denom
    ci_low = max(0.0, center - half)
    ci_high = min(1.0, center + half)

    return {
        "num_streams": int(num_streams),
        "num_updates_per_stream": int(num_updates),
        "false_accepts": false_accepts,
        "empirical_joint_fwer": round(p_hat, 5),
        "ci_95": (round(ci_low, 5), round(ci_high, 5)),
        "alpha_target": float(alpha_target),
        "joint_control_demonstrated": bool(p_hat <= alpha_target and ci_high <= alpha_target),
    }


@dataclass(frozen=True)
class StreamingGateDecision:
    """Structured record for an online candidate gating decision."""
    window_id: int
    decision: str                      # "ACCEPT" or "REJECT"
    passed_gate: bool
    delta_r: float                     # Percentage points
    se_r_raw: float                    # Unadjusted empirical cluster SE for Delta_R (pp)
    se_r_adjusted: float               # Regularized cluster SE with sensitivity floor applied (pp)
    se_r_floor: float                  # Cluster single-token sensitivity floor safeguard (pp)
    se_r: float                        # Regularized cluster SE (alias to se_r_adjusted for backward compatibility)
    ucb_r: float                       # Delta_R + z_t * se_r_adjusted (pp)
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
        num_boot_replicates: int = 500,
    ):
        self.epsilon_r = float(epsilon_r_pp)
        self.epsilon_g = float(epsilon_g_pp)
        self.epsilon_d = float(epsilon_d_pp)
        self.num_updates = int(num_updates)
        self.alpha_target = float(alpha_target)
        self.num_boot_replicates = int(num_boot_replicates)
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
            se_r_raw = math.sqrt(max(0.0, var_r)) * 100.0
        else:
            se_r_raw = 0.0

        # Conservative engineering safeguard:
        # Minimum physical resolution of 1 edit distance error across the clustered panel.
        # Regularizes the standard error to prevent finite-sample sample SE from collapsing to zero
        # when candidate hypotheses differ from live hypotheses.
        # NOTE: This floor is an engineering safeguard, not a statistically derived standard error
        # of a paired, speaker-clustered WER difference.
        se_r_floor = (1.0 / float(total_words)) * 100.0 if total_words > 0 else 0.0
        se_r_adjusted = max(se_r_raw, se_r_floor)

        # OBF multiplier for current look
        look_idx = min(window_id, len(self.z_schedule) - 1)
        z_t = float(self.z_schedule[look_idx])
        ucb_r = delta_r + z_t * se_r_adjusted

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

        # If candidate and live error counts are identical across all speakers
        all_identical = all(v["cand_err"] == v["live_err"] for v in spk_data.values())
        if all_identical:
            se_d = 0.0
        else:
            # Stratified paired cluster bootstrap with vectorized multi-stratum sampling
            spks_by_group = {g: [v for v in spk_data.values() if v["group"] == g] for g in strata_names}
            rng_boot = np.random.default_rng(12345 + window_id)
            B = self.num_boot_replicates
            num_strata = len(strata_names)
            boot_live_wers = np.zeros((B, num_strata))
            boot_cand_wers = np.zeros((B, num_strata))

            for g_idx, g in enumerate(strata_names):
                cluster = spks_by_group[g]
                S_g = len(cluster)
                if S_g > 0:
                    live_arr = np.array([c["live_err"] for c in cluster], dtype=float)
                    cand_arr = np.array([c["cand_err"] for c in cluster], dtype=float)
                    words_arr = np.array([c["words"] for c in cluster], dtype=float)
                    idxs = rng_boot.integers(0, S_g, size=(B, S_g))
                    rep_live = np.take(live_arr, idxs).sum(axis=1)
                    rep_cand = np.take(cand_arr, idxs).sum(axis=1)
                    rep_w = np.take(words_arr, idxs).sum(axis=1)
                    boot_live_wers[:, g_idx] = (rep_live / rep_w) * 100.0
                    boot_cand_wers[:, g_idx] = (rep_cand / rep_w) * 100.0

            rep_disp_live = boot_live_wers.max(axis=1) - boot_live_wers.min(axis=1)
            rep_disp_cand = boot_cand_wers.max(axis=1) - boot_cand_wers.min(axis=1)
            boot_delta_d = rep_disp_cand - rep_disp_live
            se_d = float(np.std(boot_delta_d, ddof=1))

        ucb_d = delta_d + z_t * se_d

        # 4. Tripartite Decision Rule with Fail-Closed Non-Improvement and Tie Handling
        rejection_reasons: List[str] = []

        # Rule 1: Fail-closed strict improvement requirement
        # Candidate updates must demonstrate strictly negative risk change (Delta_R < 0.0000 pp)
        # on the sentinel panel to warrant moving model weights away from the calibrated live state.
        if delta_r > 0.00:
            rejection_reasons.append(f"Point degradation: Delta_R = {delta_r:+.2f}% > 0.00%")
        elif delta_r == 0.00:
            rejection_reasons.append(
                f"Non-improvement / tie rejection: Delta_R = {delta_r:+.4f}% >= 0.0000% (fail-closed rule requires demonstrable reduction in word errors)"
            )
        if all_identical:
            rejection_reasons.append(
                "Degenerate zero-variance tie: candidate and live error counts are identical across all sentinel speakers (Delta_R = 0, SE = 0)"
            )


        # Rule 2: Overall risk bound check
        if ucb_r > self.epsilon_r:
            rejection_reasons.append(
                f"Overall risk violation: UCB(Delta_R) = {ucb_r:+.2f}% > epsilon_R ({self.epsilon_r:.2f}%)"
            )

        # Rule 3: Subgroup regression bound check
        if ucb_max_group > self.epsilon_g:
            rejection_reasons.append(
                f"Subgroup regression violation in [{worst_group}]: UCB_g = {ucb_max_group:+.2f}% > epsilon_G ({self.epsilon_g:.2f}%)"
            )

        # Rule 4: Disparity growth bound check
        if ucb_d > self.epsilon_d:
            rejection_reasons.append(
                f"Disparity growth violation: UCB(Delta_D) = {ucb_d:+.2f}% > epsilon_D ({self.epsilon_d:.2f}%)"
            )

        passed = len(rejection_reasons) == 0
        decision_str = "ACCEPT" if passed else "REJECT"

        return StreamingGateDecision(
            window_id=window_id,
            decision=decision_str,
            passed_gate=passed,
            delta_r=round(delta_r, 4),
            se_r_raw=round(se_r_raw, 4),
            se_r_adjusted=round(se_r_adjusted, 4),
            se_r_floor=round(se_r_floor, 4),
            se_r=round(se_r_adjusted, 4),
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

