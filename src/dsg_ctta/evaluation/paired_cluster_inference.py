"""
Stage 6M v1.4.0 — Confirmatory Paired Cluster Inference Module
==============================================================
Implements the frozen inferential analysis prescribed in:
`stage6m_v1_4_selective_adaptation_protocol.md` (Sections 1, 6, 7, 12, 13).

Requirements Enforced:
1. Primary Criterion 1: DSG superiority over Static Baseline (Delta_static < 0.0 pp, adjusted UCB < 0.00 pp).
2. Primary Criterion 2: DSG superiority over Corrected Ungated SUTA (Delta_ungated < 0.0 pp, adjusted UCB < 0.00 pp).
3. Fairness Criterion 3: Every accent regression within frozen margin (Delta_g <= epsilon_G, adjusted UCB <= +2.00 pp).
4. Fairness Criterion 4: Disparity non-increase (Delta_D <= 0.0 pp, adjusted UCB <= 0.00 pp).
5. Stratified paired speaker-cluster bootstrap (re-sampling within each accent independently).
6. Holm-Bonferroni multiplicity control across all simultaneous confirmatory hypotheses.
7. Machine-readable overall decision (PASS / FAIL / INCONCLUSIVE).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Tuple, FrozenSet
import numpy as np
import pandas as pd


CANONICAL_PROTOCOL_ACCENTS: FrozenSet[str] = frozenset([
    "US English",
    "England English",
    "South Asian English",
    "Australian English",
    "Canadian English",
    "Irish English",
])


@dataclass
class CriterionResult:
    """Detailed inferential evaluation of a single confirmatory criterion."""
    criterion_id: str
    criterion_name: str
    hypothesis_test: str
    null_threshold: float
    point_estimate: float
    bootstrap_mean: float
    bootstrap_std: float
    raw_ucb_95: float
    adjusted_ucb: float
    raw_p_value: float
    adjusted_p_value: float
    is_success: bool
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConfirmatoryAnalysisReport:
    """Comprehensive machine-readable verdict and inferential evidence report."""
    verdict: str  # "PASS" | "FAIL" | "INCONCLUSIVE"
    protocol_version: str
    num_speakers: int
    num_strata: int
    num_bootstrap_replicates: int
    alpha_target: float
    epsilon_g_margin_pp: float
    epsilon_d_margin_pp: float

    # Point estimates
    corpus_wer_arm1_static: float
    corpus_wer_arm2_ungated: float
    corpus_wer_arm3_dsg: float
    delta_static_pp: float
    delta_ungated_pp: float
    disparity_arm1_pp: float
    disparity_arm2_pp: float
    disparity_arm3_pp: float
    delta_disparity_pp: float

    # Accent-level breakdown
    accent_wers_arm1: Dict[str, float]
    accent_wers_arm2: Dict[str, float]
    accent_wers_arm3: Dict[str, float]
    accent_deltas_pp: Dict[str, float]

    # Evaluated Criteria
    criteria: Dict[str, CriterionResult]
    all_criteria_passed: bool
    failure_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["criteria"] = {k: v.to_dict() for k, v in self.criteria.items()}
        return d


def run_confirmatory_paired_cluster_inference(
    speaker_records: List[Dict[str, Any]],
    num_bootstrap_replicates: int = 20000,
    seed: int = 42,
    alpha_family: float = 0.05,
    epsilon_g_margin_pp: float = 2.00,
    epsilon_d_margin_pp: float = 0.00,
    canonical_accents: FrozenSet[str] = CANONICAL_PROTOCOL_ACCENTS,
) -> ConfirmatoryAnalysisReport:
    """
    Executes the frozen Stage 6M v1.4.0 final inferential analysis.

    Parameters:
    -----------
    speaker_records: List of speaker-level evaluation records containing:
        - speaker_id: Unique speaker identifier
        - stratum: Accent stratum group
        - wc: Reference word count for the speaker
        - err1: Total edit distance errors under Arm 1 (Static)
        - err2: Total edit distance errors under Arm 2 (Ungated)
        - err3: Total edit distance errors under Arm 3 (DSG)
    num_bootstrap_replicates: Number of paired stratified cluster replicates (default 20,000).
    seed: Random seed for bootstrap reproducibility.
    alpha_family: Family-wise error rate budget across all criteria (default 0.05).
    epsilon_g_margin_pp: Accent regression non-inferiority margin (+2.00 pp).
    epsilon_d_margin_pp: Disparity growth tolerance margin (0.00 pp).
    canonical_accents: Frozen set of 6 required accent strata.
    """
    # 1. Input Validation
    if not speaker_records:
        raise ValueError("Confirmatory inference input cannot be empty.")

    spk_df = pd.DataFrame(speaker_records)
    required_cols = {"speaker_id", "stratum", "wc", "err1", "err2", "err3"}
    missing_cols = required_cols - set(spk_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in speaker_records: {sorted(list(missing_cols))}")

    # Check for duplicate speaker entries
    if spk_df["speaker_id"].duplicated().any():
        dups = spk_df[spk_df["speaker_id"].duplicated()]["speaker_id"].tolist()
        raise ValueError(f"Duplicate speaker IDs detected in speaker_records: {dups[:5]}")

    # Validate non-negativity and positive word counts
    for idx, r in spk_df.iterrows():
        wc = int(r["wc"])
        e1, e2, e3 = int(r["err1"]), int(r["err2"]), int(r["err3"])
        if wc <= 0 or not math.isfinite(wc):
            raise ValueError(f"Invalid reference word count '{wc}' for speaker '{r['speaker_id']}'.")
        if e1 < 0 or e2 < 0 or e3 < 0:
            raise ValueError(f"Negative error counts for speaker '{r['speaker_id']}': err1={e1}, err2={e2}, err3={e3}.")

    # Validate accent set against canonical protocol
    observed_accents = set(spk_df["stratum"].astype(str))
    missing_accents = set(canonical_accents) - observed_accents
    if missing_accents:
        raise ValueError(f"Missing canonical protocol accents in evaluation cohort: {sorted(list(missing_accents))}")
    unexpected_accents = observed_accents - set(canonical_accents)
    if unexpected_accents:
        raise ValueError(f"Unexpected accent strata in evaluation cohort: {sorted(list(unexpected_accents))}")

    # Check that each accent has at least 2 speakers for variance estimation
    for acc in sorted(list(canonical_accents)):
        spk_cnt = int((spk_df["stratum"] == acc).sum())
        if spk_cnt < 2:
            raise ValueError(f"Stratum '{acc}' has only {spk_cnt} speakers; minimum 2 required for cluster bootstrap.")

    # 2. Point Estimates Computation
    total_words = float(spk_df["wc"].sum())
    total_e1 = float(spk_df["err1"].sum())
    total_e2 = float(spk_df["err2"].sum())
    total_e3 = float(spk_df["err3"].sum())

    wer_arm1 = (total_e1 / total_words) * 100.0
    wer_arm2 = (total_e2 / total_words) * 100.0
    wer_arm3 = (total_e3 / total_words) * 100.0

    delta_static = wer_arm3 - wer_arm1
    delta_ungated = wer_arm3 - wer_arm2

    # Accent-level WERs
    accent_wers1: Dict[str, float] = {}
    accent_wers2: Dict[str, float] = {}
    accent_wers3: Dict[str, float] = {}
    accent_deltas: Dict[str, float] = {}

    for acc in sorted(list(canonical_accents)):
        sub = spk_df[spk_df["stratum"] == acc]
        w_g = float(sub["wc"].sum())
        w1 = (float(sub["err1"].sum()) / w_g) * 100.0
        w2 = (float(sub["err2"].sum()) / w_g) * 100.0
        w3 = (float(sub["err3"].sum()) / w_g) * 100.0
        accent_wers1[acc] = w1
        accent_wers2[acc] = w2
        accent_wers3[acc] = w3
        accent_deltas[acc] = w3 - w1

    disp1 = max(accent_wers1.values()) - min(accent_wers1.values())
    disp2 = max(accent_wers2.values()) - min(accent_wers2.values())
    disp3 = max(accent_wers3.values()) - min(accent_wers3.values())
    delta_disp = disp3 - disp1

    # 3. Stratified Paired Speaker-Cluster Bootstrap
    # Pre-index speaker records by accent stratum
    stratum_speakers: Dict[str, List[Dict[str, Any]]] = {
        acc: spk_df[spk_df["stratum"] == acc].to_dict(orient="records")
        for acc in sorted(list(canonical_accents))
    }

    rng = np.random.default_rng(seed=seed)

    boot_delta_static: List[float] = []
    boot_delta_ungated: List[float] = []
    boot_accent_deltas: Dict[str, List[float]] = {acc: [] for acc in canonical_accents}
    boot_delta_disp: List[float] = []

    for _ in range(num_bootstrap_replicates):
        b_w1_accents = {}
        b_w3_accents = {}

        b_tot_w = 0.0
        b_tot_e1 = 0.0
        b_tot_e2 = 0.0
        b_tot_e3 = 0.0

        for acc in sorted(list(canonical_accents)):
            spk_pool = stratum_speakers[acc]
            n_spk = len(spk_pool)
            idx_sampled = rng.integers(0, n_spk, size=n_spk)

            gw = sum(spk_pool[i]["wc"] for i in idx_sampled)
            ge1 = sum(spk_pool[i]["err1"] for i in idx_sampled)
            ge2 = sum(spk_pool[i]["err2"] for i in idx_sampled)
            ge3 = sum(spk_pool[i]["err3"] for i in idx_sampled)

            b_tot_w += gw
            b_tot_e1 += ge1
            b_tot_e2 += ge2
            b_tot_e3 += ge3

            gw1 = (ge1 / float(gw)) * 100.0
            gw3 = (ge3 / float(gw)) * 100.0
            b_w1_accents[acc] = gw1
            b_w3_accents[acc] = gw3
            boot_accent_deltas[acc].append(gw3 - gw1)

        b_wer1 = (b_tot_e1 / b_tot_w) * 100.0
        b_wer2 = (b_tot_e2 / b_tot_w) * 100.0
        b_wer3 = (b_tot_e3 / b_tot_w) * 100.0

        boot_delta_static.append(b_wer3 - b_wer1)
        boot_delta_ungated.append(b_wer3 - b_wer2)

        b_disp1 = max(b_w1_accents.values()) - min(b_w1_accents.values())
        b_disp3 = max(b_w3_accents.values()) - min(b_w3_accents.values())
        boot_delta_disp.append(b_disp3 - b_disp1)

    # 4. Multiplicity Control: Holm-Bonferroni Step-Down Adjustment across 9 hypotheses
    # The family of 9 hypotheses:
    # 1. Delta_static < 0 (Superiority vs Static)
    # 2. Delta_ungated < 0 (Superiority vs Ungated)
    # 3-8. Delta_g <= +2.00 pp for each of 6 accents
    # 9. Delta_D <= 0.00 pp (Disparity Non-increase)
    test_specs: List[Dict[str, Any]] = [
        {
            "id": "primary_superiority_static",
            "name": "Primary Superiority vs Static Baseline",
            "test_type": "superiority",
            "pt": delta_static,
            "dist": np.array(boot_delta_static, dtype=np.float64),
            "threshold": 0.0000,
            "strict_less": True,  # Must be strictly < 0.0
        },
        {
            "id": "primary_superiority_ungated",
            "name": "Primary Superiority vs Corrected Ungated SUTA",
            "test_type": "superiority",
            "pt": delta_ungated,
            "dist": np.array(boot_delta_ungated, dtype=np.float64),
            "threshold": 0.0000,
            "strict_less": True,  # Must be strictly < 0.0
        },
    ]

    for acc in sorted(list(canonical_accents)):
        test_specs.append({
            "id": f"accent_safety_{acc.lower().replace(' ', '_')}",
            "name": f"Accent Regression Bound [{acc}]",
            "test_type": "non_inferiority",
            "pt": accent_deltas[acc],
            "dist": np.array(boot_accent_deltas[acc], dtype=np.float64),
            "threshold": epsilon_g_margin_pp,
            "strict_less": False,  # UCB <= margin
        })

    test_specs.append({
        "id": "disparity_non_increase",
        "name": "Cross-Accent Disparity Non-Increase",
        "test_type": "disparity",
        "pt": delta_disp,
        "dist": np.array(boot_delta_disp, dtype=np.float64),
        "threshold": epsilon_d_margin_pp,
        "strict_less": False,  # UCB <= 0.0
    })

    m_hypotheses = len(test_specs)  # 9 hypotheses

    # Compute unadjusted empirical one-sided p-values:
    # For H0: theta >= threshold vs H1: theta < threshold (or <= threshold)
    # p = proportion of bootstrap replicates where replicate >= threshold
    for spec in test_specs:
        dist = spec["dist"]
        thresh = spec["threshold"]
        # Empirical p-value under the bootstrap distribution
        p_emp = float(np.mean(dist >= thresh))
        # Ensure finite non-zero floor for numerical reporting
        spec["raw_p_value"] = max(p_emp, 1.0 / (num_bootstrap_replicates + 1))
        spec["raw_ucb_95"] = float(np.percentile(dist, (1.0 - alpha_family) * 100))
        spec["b_mean"] = float(np.mean(dist))
        spec["b_std"] = float(np.std(dist, ddof=1)) if len(dist) > 1 else 0.0

    # Sort tests by raw p-value ascending for Holm-Bonferroni step-down
    indexed_tests = sorted(enumerate(test_specs), key=lambda x: x[1]["raw_p_value"])

    # Holm-Bonferroni correction
    # Rank k = 1..m: adjusted_alpha_k = alpha / (m - k + 1)
    # adjusted_p_value_k = min(1.0, max(prev_adj_p, p_k * (m - k + 1)))
    prev_adj_p = 0.0
    for rank_idx, (orig_idx, spec) in enumerate(indexed_tests):
        k = rank_idx + 1
        m_k = m_hypotheses - k + 1
        adj_alpha_k = alpha_family / float(m_k)
        raw_p = spec["raw_p_value"]
        adj_p = min(1.0, max(prev_adj_p, raw_p * m_k))
        prev_adj_p = adj_p

        spec["adjusted_alpha"] = adj_alpha_k
        spec["adjusted_p_value"] = adj_p
        spec["adjusted_ucb"] = float(np.percentile(spec["dist"], (1.0 - adj_alpha_k) * 100))

    # Evaluate each criterion against frozen decision rules
    criteria_results: Dict[str, CriterionResult] = {}
    failure_reasons: List[str] = []

    for spec in test_specs:
        c_id = spec["id"]
        pt = spec["pt"]
        thresh = spec["threshold"]
        adj_ucb = spec["adjusted_ucb"]
        adj_p = spec["adjusted_p_value"]
        strict = spec["strict_less"]

        # Decision rule:
        # Superiority requires point improvement (pt < 0) AND adjusted UCB < 0.00
        # Non-inferiority requires adjusted UCB <= margin
        if strict:
            passed = bool(pt < thresh and adj_ucb < thresh)
        else:
            passed = bool(adj_ucb <= thresh)

        if not passed:
            if strict:
                reason = f"{spec['name']} FAILED: point estimate={pt:+.2f} pp, adj_UCB={adj_ucb:+.2f} pp (must be < {thresh:.2f} pp)"
            else:
                reason = f"{spec['name']} FAILED: adj_UCB={adj_ucb:+.2f} pp exceeds margin ({thresh:+.2f} pp)"
            failure_reasons.append(reason)
            interp = f"Violation: {reason}"
        else:
            interp = f"Passed: estimate={pt:+.2f} pp, adj_UCB={adj_ucb:+.2f} pp <= {thresh:+.2f} pp (adj_p={adj_p:.4f})"

        criteria_results[c_id] = CriterionResult(
            criterion_id=c_id,
            criterion_name=spec["name"],
            hypothesis_test=f"H1: {c_id} {'<' if strict else '<='} {thresh:+.2f} pp",
            null_threshold=thresh,
            point_estimate=round(pt, 4),
            bootstrap_mean=round(spec["b_mean"], 4),
            bootstrap_std=round(spec["b_std"], 4),
            raw_ucb_95=round(spec["raw_ucb_95"], 4),
            adjusted_ucb=round(adj_ucb, 4),
            raw_p_value=round(spec["raw_p_value"], 6),
            adjusted_p_value=round(adj_p, 6),
            is_success=passed,
            interpretation=interp,
        )

    all_passed = len(failure_reasons) == 0

    # Determine overall protocol verdict
    if all_passed:
        verdict = "PASS"
    elif delta_static == 0.0 and wer_arm3 == wer_arm1:
        # Zero accepted updates / exact replication of baseline
        verdict = "FAIL"
        failure_reasons.insert(0, "Primary Objective Failed: Arm 3 identical to Static Baseline (0 updates promoted).")
    else:
        verdict = "FAIL"

    return ConfirmatoryAnalysisReport(
        verdict=verdict,
        protocol_version="v1.4.0-stage6m-selective-adaptation-draft",
        num_speakers=len(spk_df),
        num_strata=len(canonical_accents),
        num_bootstrap_replicates=num_bootstrap_replicates,
        alpha_target=alpha_family,
        epsilon_g_margin_pp=epsilon_g_margin_pp,
        epsilon_d_margin_pp=epsilon_d_margin_pp,
        corpus_wer_arm1_static=round(wer_arm1, 4),
        corpus_wer_arm2_ungated=round(wer_arm2, 4),
        corpus_wer_arm3_dsg=round(wer_arm3, 4),
        delta_static_pp=round(delta_static, 4),
        delta_ungated_pp=round(delta_ungated, 4),
        disparity_arm1_pp=round(disp1, 4),
        disparity_arm2_pp=round(disp2, 4),
        disparity_arm3_pp=round(disp3, 4),
        delta_disparity_pp=round(delta_disp, 4),
        accent_wers_arm1={k: round(v, 4) for k, v in accent_wers1.items()},
        accent_wers_arm2={k: round(v, 4) for k, v in accent_wers2.items()},
        accent_wers_arm3={k: round(v, 4) for k, v in accent_wers3.items()},
        accent_deltas_pp={k: round(v, 4) for k, v in accent_deltas.items()},
        criteria=criteria_results,
        all_criteria_passed=all_passed,
        failure_reasons=failure_reasons,
    )
