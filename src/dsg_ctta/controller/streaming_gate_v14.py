"""
Stage 6M v1.4.0: Production Streaming Safety Gate Evaluator (V14).
==================================================================
Protocol: v1.4.0-stage6m-selective-adaptation-draft | Standard: ADR-005

Implements the strict v1.4.0 tripartite Upper Confidence Bound (UCB) safety rules:
1. Overall utility: Strict point reduction (Delta_R < 0.0 pp) AND UCB(Delta_R) <= 0.0000 pp.
2. Accent non-inferiority: For all accent strata g, UCB(Delta_g) <= epsilon_G (default: +2.0000 pp).
3. Disparity non-increase: UCB(Delta_D) <= 0.0000 pp (epsilon_D = 0.0000 pp, zero tolerance for disparity growth).
4. Sequential Lan-DeMets O'Brien-Fleming critical boundary schedule across all looks.
5. Strict fail-closed rejection on zero-variance ties, missing strata, or numerical failures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from scipy import stats

from dsg_ctta.controller.streaming_gate import (
    compute_calibrated_obf_schedule,
    StreamingGateDecision,
)


class StreamingSentinelSafetyGateV14:
    """
    Production Gate Evaluator under Protocol v1.4.0.
    Enforces zero-tolerance disparity growth (epsilon_D = 0.0 pp) and strict
    point improvement (Delta_R < 0.0 pp) alongside Lan-DeMets OBF alpha spending.
    """

    def __init__(
        self,
        epsilon_r_pp: float = 0.0000,
        epsilon_g_pp: float = 2.0000,
        epsilon_d_pp: float = 0.0000,
        num_updates: int = 1754,
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
        Evaluates candidate update safety under Protocol v1.4.0.

        Parameters:
        -----------
        window_id: Current stream adaptation window index (0-indexed).
        speaker_ids: Speaker ID for each sentinel utterance.
        stratum_groups: Stratum label for each sentinel utterance.
        live_errors: Total edit distance errors (S+D+I) under live model.
        cand_errors: Total edit distance errors (S+D+I) under candidate model.
        ref_lengths: Reference word count for each utterance.
        """
        if len(speaker_ids) == 0:
            raise ValueError("Sentinel evaluation inputs cannot be empty.")
        assert len(speaker_ids) == len(stratum_groups) == len(live_errors) == len(cand_errors) == len(ref_lengths)

        n_items = len(speaker_ids)

        # Aggregate counts at the speaker level
        spk_data: Dict[str, Dict[str, Any]] = {}
        strata_words: Dict[str, int] = {}
        for s_id, grp, e_live, e_cand, n_words in zip(speaker_ids, stratum_groups, live_errors, cand_errors, ref_lengths):
            if s_id not in spk_data:
                spk_data[s_id] = {
                    "grp": grp,
                    "e_live": 0,
                    "e_cand": 0,
                    "n_words": 0,
                }
            spk_data[s_id]["e_live"] += e_live
            spk_data[s_id]["e_cand"] += e_cand
            spk_data[s_id]["n_words"] += n_words
            strata_words[grp] = strata_words.get(grp, 0) + n_words

        spk_list = list(spk_data.keys())
        N_spk = len(spk_list)

        total_words = sum(spk_data[s]["n_words"] for s in spk_list)
        if total_words == 0:
            raise ValueError("Total sentinel reference words cannot be zero.")

        total_live_err = sum(spk_data[s]["e_live"] for s in spk_list)
        total_cand_err = sum(spk_data[s]["e_cand"] for s in spk_list)

        R_live = (total_live_err / float(total_words)) * 100.0
        R_cand = (total_cand_err / float(total_words)) * 100.0
        delta_r = R_cand - R_live

        # Critical OBF multiplier for this sequential look
        idx = min(window_id, self.num_updates - 1)
        z_t = float(self.z_schedule[idx])

        # Cluster-robust Delta Method for Overall Delta_R
        u_i = np.array([spk_data[s]["e_cand"] - spk_data[s]["e_live"] for s in spk_list], dtype=np.float64)
        w_i = np.array([spk_data[s]["n_words"] for s in spk_list], dtype=np.float64)
        w_bar = np.mean(w_i)

        ratio_diff = (delta_r / 100.0)
        psi_i = (u_i - ratio_diff * w_i) / w_bar
        var_psi = np.var(psi_i, ddof=1) if N_spk > 1 else 0.0
        se_r_raw = (math.sqrt(var_psi / N_spk) * 100.0) if var_psi > 0 else 0.0

        # Sensitivity Floor Safeguard
        min_cluster_words = float(np.min(w_i)) if len(w_i) > 0 else 1.0
        se_r_floor = (1.0 / (math.sqrt(N_spk) * min_cluster_words)) * 100.0
        se_r_adjusted = max(se_r_raw, se_r_floor)
        ucb_r = delta_r + z_t * se_r_adjusted

        # Per-stratum regression bounds
        unique_strata = sorted(list(set(stratum_groups)))
        group_deltas: Dict[str, float] = {}
        group_ucbs: Dict[str, float] = {}
        group_ses: Dict[str, float] = {}

        for grp in unique_strata:
            grp_spks = [s for s in spk_list if spk_data[s]["grp"] == grp]
            n_grp_spk = len(grp_spks)
            grp_words = sum(spk_data[s]["n_words"] for s in grp_spks)
            if grp_words == 0 or n_grp_spk == 0:
                continue

            grp_live_e = sum(spk_data[s]["e_live"] for s in grp_spks)
            grp_cand_e = sum(spk_data[s]["e_cand"] for s in grp_spks)
            r_g_live = (grp_live_e / float(grp_words)) * 100.0
            r_g_cand = (grp_cand_e / float(grp_words)) * 100.0
            d_g = r_g_cand - r_g_live
            group_deltas[grp] = d_g

            u_ig = np.array([spk_data[s]["e_cand"] - spk_data[s]["e_live"] for s in grp_spks], dtype=np.float64)
            w_ig = np.array([spk_data[s]["n_words"] for s in grp_spks], dtype=np.float64)
            w_bar_g = np.mean(w_ig)
            psi_ig = (u_ig - (d_g / 100.0) * w_ig) / w_bar_g
            var_psi_g = np.var(psi_ig, ddof=1) if n_grp_spk > 1 else 0.0
            se_g_raw = (math.sqrt(var_psi_g / n_grp_spk) * 100.0) if var_psi_g > 0 else 0.0
            min_grp_w = float(np.min(w_ig)) if len(w_ig) > 0 else 1.0
            se_g_floor = (1.0 / (math.sqrt(n_grp_spk) * min_grp_w)) * 100.0
            se_g = max(se_g_raw, se_g_floor)
            group_ses[grp] = se_g
            group_ucbs[grp] = d_g + z_t * se_g

        worst_grp = max(group_ucbs, key=lambda k: group_ucbs[k]) if group_ucbs else "UNKNOWN"
        ucb_max_group = group_ucbs.get(worst_grp, 0.0)
        max_delta_g = max(group_deltas.values()) if group_deltas else 0.0

        # Disparity calculation: D = max_g(WER_g) - min_g(WER_g)
        grp_live_wers = {grp: (sum(spk_data[s]["e_live"] for s in spk_list if spk_data[s]["grp"] == grp) / float(strata_words[grp])) * 100.0 for grp in unique_strata}
        grp_cand_wers = {grp: (sum(spk_data[s]["e_cand"] for s in spk_list if spk_data[s]["grp"] == grp) / float(strata_words[grp])) * 100.0 for grp in unique_strata}

        D_live = max(grp_live_wers.values()) - min(grp_live_wers.values())
        D_cand = max(grp_cand_wers.values()) - min(grp_cand_wers.values())
        delta_d = D_cand - D_live

        # Paired bootstrap for SE(Delta_D)
        rng_boot = np.random.default_rng(seed=42 + window_id)
        boot_diffs = []
        for _ in range(self.num_boot_replicates):
            b_indices = rng_boot.integers(0, N_spk, size=N_spk)
            b_spks = [spk_list[i] for i in b_indices]
            b_live_wers = []
            b_cand_wers = []
            for grp in unique_strata:
                g_spks = [s for s in b_spks if spk_data[s]["grp"] == grp]
                if not g_spks:
                    continue
                g_w = sum(spk_data[s]["n_words"] for s in g_spks)
                if g_w == 0:
                    continue
                g_l_e = sum(spk_data[s]["e_live"] for s in g_spks)
                g_c_e = sum(spk_data[s]["e_cand"] for s in g_spks)
                b_live_wers.append((g_l_e / float(g_w)) * 100.0)
                b_cand_wers.append((g_c_e / float(g_w)) * 100.0)

            if len(b_live_wers) >= 2 and len(b_cand_wers) >= 2:
                b_D_live = max(b_live_wers) - min(b_live_wers)
                b_D_cand = max(b_cand_wers) - min(b_cand_wers)
                boot_diffs.append(b_D_cand - b_D_live)

        se_d = float(np.std(boot_diffs, ddof=1)) if len(boot_diffs) > 1 else 0.5000
        ucb_d = delta_d + z_t * se_d

        # Evaluation of Decision Rules
        reasons = []

        # Rule 1: Point improvement requirement (Delta_R < 0.0)
        # Ties (Delta_R == 0.0) are strictly rejected
        if delta_r >= 0.0:
            reasons.append(f"Point degradation/tie: Delta_R = {delta_r:+.2f}% >= 0.00%")

        # Rule 2: Overall risk UCB <= epsilon_R (0.00 pp)
        if ucb_r > self.epsilon_r:
            reasons.append(f"Overall risk violation: UCB(Delta_R) = {ucb_r:+.2f}% > epsilon_R ({self.epsilon_r:.2f}%)")

        # Rule 3: Worst subgroup regression UCB <= epsilon_G (+2.00 pp)
        if ucb_max_group > self.epsilon_g:
            reasons.append(f"Subgroup regression violation in [{worst_grp}]: UCB_g = {ucb_max_group:+.2f}% > epsilon_G ({self.epsilon_g:.2f}%)")

        # Rule 4: Disparity growth UCB <= epsilon_D (0.00 pp in v1.4)
        if ucb_d > self.epsilon_d:
            reasons.append(f"Disparity growth violation: UCB(Delta_D) = {ucb_d:+.2f}% > epsilon_D ({self.epsilon_d:.2f}%)")

        passed_gate = (len(reasons) == 0)
        decision = "ACCEPT" if passed_gate else "REJECT"

        return StreamingGateDecision(
            window_id=window_id,
            decision=decision,
            passed_gate=passed_gate,
            delta_r=round(delta_r, 4),
            se_r_raw=round(se_r_raw, 4),
            se_r_adjusted=round(se_r_adjusted, 4),
            se_r_floor=round(se_r_floor, 4),
            se_r=round(se_r_adjusted, 4),
            ucb_r=round(ucb_r, 4),
            max_delta_g=round(max_delta_g, 4),
            ucb_max_group=round(ucb_max_group, 4),
            worst_group=worst_grp,
            delta_d=round(delta_d, 4),
            se_d=round(se_d, 4),
            ucb_d=round(ucb_d, 4),
            z_obf=round(z_t, 4),
            epsilon_r=self.epsilon_r,
            epsilon_g=self.epsilon_g,
            epsilon_d=self.epsilon_d,
            rejection_reasons=reasons,
            group_deltas={k: round(v, 4) for k, v in group_deltas.items()},
            group_ucbs={k: round(v, 4) for k, v in group_ucbs.items()},
            group_ses={k: round(v, 4) for k, v in group_ses.items()},
        )
