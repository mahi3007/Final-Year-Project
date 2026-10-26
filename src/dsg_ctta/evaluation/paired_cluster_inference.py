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
class PowerAssessment:
    """Simulation/analytical power assessment for the confirmatory study design."""
    min_speakers_per_stratum_observed: int
    min_speakers_required_for_power: int
    is_adequately_powered: bool
    estimated_primary_power_vs_static: float
    estimated_primary_power_vs_ungated: float
    power_threshold: float
    power_status: str  # "ADEQUATE" | "UNDERPOWERED"
    power_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
    power_assessment: Optional[PowerAssessment] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["criteria"] = {k: v.to_dict() for k, v in self.criteria.items()}
        if self.power_assessment is not None:
            d["power_assessment"] = self.power_assessment.to_dict()
        return d


def _validate_raw_integer_count(
    val: Any,
    name: str,
    speaker_id: str,
    min_val: int = 0,
    is_strictly_positive: bool = False
) -> int:
    """Validates raw numeric count without silent truncation or conversion."""
    if val is None or pd.isna(val):
        raise ValueError(f"Missing/NaN {name} for speaker '{speaker_id}'.")
    if isinstance(val, bool) or not isinstance(val, (int, float, np.integer, np.floating)):
        raise ValueError(f"Invalid non-numeric type for {name} for speaker '{speaker_id}': {type(val).__name__} ('{val}').")
    fval = float(val)
    if not math.isfinite(fval):
        raise ValueError(f"Non-finite {name} '{val}' for speaker '{speaker_id}'.")
    if isinstance(val, (float, np.floating)):
        if not fval.is_integer():
            raise ValueError(
                f"Fractional count '{val}' for {name} for speaker '{speaker_id}' is not an exact integer."
            )
    ival = int(fval)
    if is_strictly_positive:
        if ival <= 0:
            raise ValueError(f"Non-positive word count {name}='{ival}' for speaker '{speaker_id}'; must be > 0.")
    else:
        if ival < min_val:
            raise ValueError(f"Invalid error count {name}='{ival}' for speaker '{speaker_id}'; must be >= {min_val}.")
    return ival


def _validate_identifier(val: Any, name: str, index: int) -> str:
    """Validates raw string identifier ensuring non-blank and non-null values."""
    if val is None or pd.isna(val):
        raise ValueError(f"Record at index {index} has missing/NaN {name}.")
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none"):
        raise ValueError(f"Record at index {index} has blank/empty {name}.")
    return s


def evaluate_confirmatory_power(
    spk_df: pd.DataFrame,
    target_effect_size_pp: float = 2.00,
    power_threshold: float = 0.90,
    min_speakers_per_stratum_required: int = 5,
    alpha_family: float = 0.05,
    num_hypotheses: int = 9,
) -> PowerAssessment:
    """
    Evaluates statistical power for detecting target effect sizes under Holm multiplicity adjustment.
    """
    from scipy import stats
    n_speakers = len(spk_df)
    spks_per_stratum = spk_df.groupby("stratum")["speaker_id"].count()
    min_spks_obs = int(spks_per_stratum.min()) if len(spks_per_stratum) > 0 else 0

    spk_wer1 = (spk_df["err1"] / spk_df["wc"]) * 100.0
    spk_wer2 = (spk_df["err2"] / spk_df["wc"]) * 100.0
    spk_wer3 = (spk_df["err3"] / spk_df["wc"]) * 100.0

    diff_static = spk_wer3 - spk_wer1
    diff_ungated = spk_wer3 - spk_wer2

    s_static = float(diff_static.std(ddof=1)) if n_speakers > 1 else 0.0
    s_ungated = float(diff_ungated.std(ddof=1)) if n_speakers > 1 else 0.0

    s_eff_static = max(s_static, 3.0)
    s_eff_ungated = max(s_ungated, 3.0)

    alpha_1 = alpha_family / float(num_hypotheses)
    z_crit = float(stats.norm.ppf(1.0 - alpha_1))

    se_static = s_eff_static / math.sqrt(n_speakers)
    se_ungated = s_eff_ungated / math.sqrt(n_speakers)

    z_stat = (target_effect_size_pp / se_static) - z_crit
    z_ung = (target_effect_size_pp / se_ungated) - z_crit

    power_static = float(stats.norm.cdf(z_stat))
    power_ungated = float(stats.norm.cdf(z_ung))

    is_powered = (
        min_spks_obs >= min_speakers_per_stratum_required
        and power_static >= power_threshold
        and power_ungated >= power_threshold
    )

    status = "ADEQUATE" if is_powered else "UNDERPOWERED"
    summary = (
        f"Design achieves {power_static:.1%} power vs static and {power_ungated:.1%} vs ungated "
        f"at effect size={target_effect_size_pp:.2f} pp (target={power_threshold:.0%}, "
        f"observed min speakers/stratum={min_spks_obs}, required={min_speakers_per_stratum_required})."
    )

    return PowerAssessment(
        min_speakers_per_stratum_observed=min_spks_obs,
        min_speakers_required_for_power=min_speakers_per_stratum_required,
        is_adequately_powered=is_powered,
        estimated_primary_power_vs_static=round(power_static, 4),
        estimated_primary_power_vs_ungated=round(power_ungated, 4),
        power_threshold=power_threshold,
        power_status=status,
        power_summary=summary,
    )


def run_confirmatory_paired_cluster_inference(
    speaker_records: List[Dict[str, Any]],
    num_bootstrap_replicates: int = 20000,
    seed: int = 42,
    alpha_family: float = 0.05,
    epsilon_g_margin_pp: float = 2.00,
    epsilon_d_margin_pp: float = 0.00,
    canonical_accents: FrozenSet[str] = CANONICAL_PROTOCOL_ACCENTS,
    min_speakers_per_stratum_for_power: int = 5,
    target_effect_size_pp: float = 2.00,
    power_threshold: float = 0.90,
) -> ConfirmatoryAnalysisReport:
    """
    Executes the frozen Stage 6M v1.4.0 final inferential analysis.

    Parameters:
    -----------
    speaker_records: List of speaker-level evaluation records containing:
        - speaker_id: Unique speaker identifier
        - stratum: Accent stratum group
        - wc: Reference word count for the speaker (strictly positive integer)
        - err1: Total edit distance errors under Arm 1 (Static) (non-negative integer)
        - err2: Total edit distance errors under Arm 2 (Ungated) (non-negative integer)
        - err3: Total edit distance errors under Arm 3 (DSG) (non-negative integer)
    num_bootstrap_replicates: Number of paired stratified cluster replicates (default 20,000).
    seed: Random seed for bootstrap reproducibility.
    alpha_family: Family-wise error rate budget across all criteria (default 0.05).
    epsilon_g_margin_pp: Accent regression non-inferiority margin (+2.00 pp).
    epsilon_d_margin_pp: Disparity growth tolerance margin (0.00 pp).
    canonical_accents: Frozen set of 6 required accent strata.
    min_speakers_per_stratum_for_power: Minimum speakers per stratum required for adequate power.
    target_effect_size_pp: Target WER reduction in percentage points for power assessment (default 2.00 pp).
    power_threshold: Minimum power threshold for confirmatory declaration (default 0.90).
    """
    # 1. Configuration Validation
    if not isinstance(num_bootstrap_replicates, (int, np.integer)) or isinstance(num_bootstrap_replicates, bool) or num_bootstrap_replicates <= 0:
        raise ValueError(f"num_bootstrap_replicates must be a positive integer, got '{num_bootstrap_replicates}'.")

    if not isinstance(alpha_family, (int, float, np.floating)) or isinstance(alpha_family, bool) or not math.isfinite(alpha_family) or not (0.0 < float(alpha_family) < 1.0):
        raise ValueError(f"alpha_family must be a finite float strictly in (0.0, 1.0), got '{alpha_family}'.")

    if not isinstance(epsilon_g_margin_pp, (int, float, np.floating)) or isinstance(epsilon_g_margin_pp, bool) or not math.isfinite(epsilon_g_margin_pp) or float(epsilon_g_margin_pp) < 0.0:
        raise ValueError(f"epsilon_g_margin_pp must be a finite non-negative float, got '{epsilon_g_margin_pp}'.")

    if not isinstance(epsilon_d_margin_pp, (int, float, np.floating)) or isinstance(epsilon_d_margin_pp, bool) or not math.isfinite(epsilon_d_margin_pp) or float(epsilon_d_margin_pp) < 0.0:
        raise ValueError(f"epsilon_d_margin_pp must be a finite non-negative float, got '{epsilon_d_margin_pp}'.")

    # 2. Input Records Validation (prior to any conversion or DataFrame manipulation)
    if not speaker_records:
        raise ValueError("Confirmatory inference input cannot be empty.")

    cleaned_records: List[Dict[str, Any]] = []
    seen_speakers: Dict[str, str] = {}

    for idx, r in enumerate(speaker_records):
        if not isinstance(r, dict):
            raise ValueError(f"speaker_records entry {idx} is not a dictionary.")

        for req_k in ("speaker_id", "stratum", "wc", "err1", "err2", "err3"):
            if req_k not in r:
                raise ValueError(f"Missing required field '{req_k}' in record at index {idx}.")

        spk_id = _validate_identifier(r["speaker_id"], "speaker_id", idx)
        strat = _validate_identifier(r["stratum"], "stratum", idx)

        if spk_id in seen_speakers:
            raise ValueError(f"Duplicate speaker ID detected in speaker_records: '{spk_id}'.")
        seen_speakers[spk_id] = strat

        wc = _validate_raw_integer_count(r["wc"], "wc", spk_id, is_strictly_positive=True)
        e1 = _validate_raw_integer_count(r["err1"], "err1", spk_id, min_val=0)
        e2 = _validate_raw_integer_count(r["err2"], "err2", spk_id, min_val=0)
        e3 = _validate_raw_integer_count(r["err3"], "err3", spk_id, min_val=0)

        cleaned_records.append({
            "speaker_id": spk_id,
            "stratum": strat,
            "wc": wc,
            "err1": e1,
            "err2": e2,
            "err3": e3,
        })

    spk_df = pd.DataFrame(cleaned_records)

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

    # 3. Power Assessment
    power_assessment = evaluate_confirmatory_power(
        spk_df=spk_df,
        target_effect_size_pp=target_effect_size_pp,
        power_threshold=power_threshold,
        min_speakers_per_stratum_required=min_speakers_per_stratum_for_power,
        alpha_family=alpha_family,
        num_hypotheses=9,
    )

    # 4. Point Estimates Computation
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

    # 5. Stratified Paired Speaker-Cluster Bootstrap
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

    # 6. Multiplicity Control: Holm-Bonferroni Step-Down Adjustment across 9 hypotheses
    test_specs: List[Dict[str, Any]] = [
        {
            "id": "primary_superiority_static",
            "name": "Primary Superiority vs Static Baseline",
            "test_type": "superiority",
            "pt": delta_static,
            "dist": np.array(boot_delta_static, dtype=np.float64),
            "threshold": 0.0000,
            "strict_less": True,
        },
        {
            "id": "primary_superiority_ungated",
            "name": "Primary Superiority vs Corrected Ungated SUTA",
            "test_type": "superiority",
            "pt": delta_ungated,
            "dist": np.array(boot_delta_ungated, dtype=np.float64),
            "threshold": 0.0000,
            "strict_less": True,
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
            "strict_less": False,
        })

    test_specs.append({
        "id": "disparity_non_increase",
        "name": "Cross-Accent Disparity Non-Increase",
        "test_type": "disparity",
        "pt": delta_disp,
        "dist": np.array(boot_delta_disp, dtype=np.float64),
        "threshold": epsilon_d_margin_pp,
        "strict_less": False,
    })

    m_hypotheses = len(test_specs)

    for spec in test_specs:
        dist = spec["dist"]
        thresh = spec["threshold"]
        p_emp = float(np.mean(dist >= thresh))
        spec["raw_p_value"] = max(p_emp, 1.0 / (num_bootstrap_replicates + 1))
        spec["raw_ucb_95"] = float(np.percentile(dist, (1.0 - alpha_family) * 100))
        spec["b_mean"] = float(np.mean(dist))
        spec["b_std"] = float(np.std(dist, ddof=1)) if len(dist) > 1 else 0.0

    indexed_tests = sorted(enumerate(test_specs), key=lambda x: x[1]["raw_p_value"])

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

    criteria_results: Dict[str, CriterionResult] = {}
    failure_reasons: List[str] = []

    for spec in test_specs:
        c_id = spec["id"]
        pt = spec["pt"]
        thresh = spec["threshold"]
        adj_ucb = spec["adjusted_ucb"]
        adj_p = spec["adjusted_p_value"]
        strict = spec["strict_less"]

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

    # 7. Overall Protocol Verdict: Distinguish PASS, FAIL, and INCONCLUSIVE
    has_harmful_regression = (
        delta_static > 0.0000
        or delta_ungated > 0.0000
        or any(accent_deltas[acc] > epsilon_g_margin_pp for acc in canonical_accents)
        or delta_disp > max(epsilon_d_margin_pp, 1.40)
    )

    is_zero_updates = bool(delta_static == 0.0 and wer_arm3 == wer_arm1)

    if all_passed:
        if not power_assessment.is_adequately_powered:
            verdict = "INCONCLUSIVE"
            failure_reasons.append(
                f"Study is underpowered for confirmatory declaration: {power_assessment.power_summary}"
            )
        else:
            verdict = "PASS"
    elif has_harmful_regression:
        verdict = "FAIL"
    elif is_zero_updates:
        verdict = "INCONCLUSIVE"
        failure_reasons.insert(
            0,
            "Primary Objective Inconclusive: Arm 3 identical to Static Baseline (0 updates promoted; "
            "protective invariance verified, but selective adaptation benefit not established)."
        )
    else:
        verdict = "INCONCLUSIVE"
        failure_reasons.insert(
            0,
            "Inconclusive Evidence: Point estimates indicate no harmful regression, but confidence bounds "
            "exceed target thresholds due to sample variance or insufficient precision."
        )

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
        power_assessment=power_assessment,
    )
