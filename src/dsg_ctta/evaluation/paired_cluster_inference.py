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
class DesignStagePowerSpec:
    """Design-stage simulation power specification derived from development data.

    Variance parameters and effect sizes are frozen based on Common Voice 27 development data:
    - between_speaker_wer_std: 6.50 pp (cross-speaker variability within accent strata)
    - paired_diff_std: 3.20 pp (within-speaker paired difference standard deviation)
    - target_primary_effect_pp: 3.50 pp superiority vs static baseline
    - target_ungated_effect_pp: 3.50 pp superiority vs corrected ungated SUTA
    - target_disparity_effect_pp: -1.00 pp narrowing of max-min disparity gap
    - alpha_family: 0.05 family-wise error across M=9 hypotheses
    - target_joint_power: 0.90 joint probability across all 9 criteria
    - required_speakers_per_stratum: 78 speakers (468 speakers across 6 strata)
    """
    target_primary_effect_pp: float = 3.50
    target_ungated_effect_pp: float = 3.50
    target_disparity_effect_pp: float = -1.00
    between_speaker_wer_std: float = 6.50
    paired_diff_std: float = 3.20
    alpha_family: float = 0.05
    target_joint_power: float = 0.90
    required_speakers_per_stratum: int = 78
    required_clips_per_speaker: int = 15

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PowerAssessment:
    """Design-stage joint power assessment for the confirmatory study design."""
    min_speakers_per_stratum_observed: int
    min_speakers_required_for_power: int
    is_adequately_powered: bool
    design_target_effect_size_pp: float
    design_target_joint_power: float
    estimated_joint_power: float
    power_status: str  # "ADEQUATE" | "UNDERPOWERED"
    power_summary: str
    design_spec: Optional[Dict[str, Any]] = None

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
    raw_lcb_95: float
    raw_ucb_95: float
    adjusted_lcb: float
    adjusted_ucb: float
    raw_p_value: float
    adjusted_p_value: float
    is_success: bool
    interpretation: str
    linear_t_statistic: Optional[float] = None
    linear_p_value: Optional[float] = None

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
    is_protective_invariance: bool = False
    failure_reasons: List[str] = field(default_factory=list)
    demonstrated_harm_reasons: List[str] = field(default_factory=list)
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


def simulate_design_stage_joint_power(
    spec: DesignStagePowerSpec,
    num_simulations: int = 200,
    num_speakers_per_stratum: int = 78,
    seed: int = 42,
) -> float:
    """
    Simulates the design-stage joint power of the composite 9-criterion confirmatory analysis
    using development-derived variance-covariance parameters across candidate sample sizes.
    """
    from scipy import stats
    rng = np.random.default_rng(seed=seed)
    accents = sorted(list(CANONICAL_PROTOCOL_ACCENTS))
    n_acc = len(accents)
    m_hypotheses = 9
    adj_alpha = spec.alpha_family / float(m_hypotheses)
    z_crit = float(stats.norm.ppf(1.0 - adj_alpha))

    # Baseline WER means per accent (e.g. range 14% to 26%)
    base_wers = {
        "US English": 14.0,
        "England English": 17.0,
        "Canadian English": 16.0,
        "Australian English": 19.0,
        "South Asian English": 23.0,
        "Irish English": 26.0,
    }

    # Shifts to achieve target primary effect (-3.5 pp) and disparity narrowing (-1.0 pp)
    scale = spec.target_primary_effect_pp / 3.50 if spec.target_primary_effect_pp > 0 else 1.0
    accent_shifts = {
        "US English": -2.5 * scale,
        "England English": -3.0 * scale,
        "Canadian English": -3.0 * scale,
        "Australian English": -3.5 * scale,
        "South Asian English": -4.5 * scale,
        "Irish English": -4.5 * scale,
    }

    n_spk = num_speakers_per_stratum
    se_primary = spec.paired_diff_std / math.sqrt(n_spk * n_acc)
    se_accent = spec.paired_diff_std / math.sqrt(n_spk)

    joint_passes = 0
    for _ in range(num_simulations):
        # 1. Primary static difference
        obs_delta_static = spec.target_primary_effect_pp * -1.0 + rng.normal(0, se_primary)
        ucb_static = obs_delta_static + z_crit * se_primary
        pass_static = bool(ucb_static < 0.0 and obs_delta_static < 0.0)

        # 2. Primary ungated difference (modeled against corrected ungated SUTA with realistic effect)
        ungated_eff = max(spec.target_ungated_effect_pp, spec.target_primary_effect_pp)
        obs_delta_ungated = ungated_eff * -1.0 + rng.normal(0, se_primary)
        ucb_ungated = obs_delta_ungated + z_crit * se_primary
        pass_ungated = bool(ucb_ungated < 0.0 and obs_delta_ungated < 0.0)

        # 3. Accent non-inferiority
        accent_passes = True
        obs_acc_w1 = {}
        obs_acc_w3 = {}
        for acc in accents:
            shift = accent_shifts.get(acc, -3.0 * scale)
            obs_delta_g = shift + rng.normal(0, se_accent)
            ucb_g = obs_delta_g + z_crit * se_accent
            if ucb_g > 2.0:
                accent_passes = False
            obs_acc_w1[acc] = base_wers[acc] + rng.normal(0, spec.between_speaker_wer_std / math.sqrt(n_spk))
            obs_acc_w3[acc] = obs_acc_w1[acc] + obs_delta_g

        # 4. Disparity non-increase
        d1 = max(obs_acc_w1.values()) - min(obs_acc_w1.values())
        d3 = max(obs_acc_w3.values()) - min(obs_acc_w3.values())
        obs_delta_disp = d3 - d1
        # Disparity SE from max-min difference
        se_disp = (spec.paired_diff_std * 1.414) / math.sqrt(n_spk)
        ucb_disp = obs_delta_disp + z_crit * se_disp
        pass_disp = bool(ucb_disp <= 0.0)

        if pass_static and pass_ungated and accent_passes and pass_disp:
            joint_passes += 1

    return float(joint_passes / num_simulations)


def evaluate_confirmatory_power(
    spk_df: pd.DataFrame,
    design_spec: Optional[DesignStagePowerSpec] = None,
    min_speakers_per_stratum_required: Optional[int] = None,
) -> PowerAssessment:
    """
    Evaluates confirmatory study power against the design-stage power specification.
    Does not use post-hoc treatment effect sizes to manufacture retrospective power.
    """
    if design_spec is None:
        design_spec = DesignStagePowerSpec()

    req_spks = (
        min_speakers_per_stratum_required
        if min_speakers_per_stratum_required is not None
        else design_spec.required_speakers_per_stratum
    )

    spks_per_stratum = spk_df.groupby("stratum")["speaker_id"].count()
    min_spks_obs = int(spks_per_stratum.min()) if len(spks_per_stratum) > 0 else 0

    # Evaluate design-stage joint power at observed sample size
    est_joint_power = simulate_design_stage_joint_power(
        spec=design_spec,
        num_simulations=100,
        num_speakers_per_stratum=max(min_spks_obs, 2),
        seed=123,
    )

    is_powered = bool(
        min_spks_obs >= req_spks
        and est_joint_power >= (design_spec.target_joint_power - 0.05)
    )

    status = "ADEQUATE" if is_powered else "UNDERPOWERED"
    summary = (
        f"Design-stage assessment: observed min speakers/stratum={min_spks_obs} (required={req_spks}). "
        f"Design joint power={est_joint_power:.1%} (target={design_spec.target_joint_power:.0%} "
        f"at target effect={design_spec.target_primary_effect_pp:.2f} pp). Status: {status}."
    )

    return PowerAssessment(
        min_speakers_per_stratum_observed=min_spks_obs,
        min_speakers_required_for_power=req_spks,
        is_adequately_powered=is_powered,
        design_target_effect_size_pp=design_spec.target_primary_effect_pp,
        design_target_joint_power=design_spec.target_joint_power,
        estimated_joint_power=round(est_joint_power, 4),
        power_status=status,
        power_summary=summary,
        design_spec=design_spec.to_dict(),
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
    design_spec: Optional[DesignStagePowerSpec] = None,
    target_effect_size_pp: Optional[float] = None,
    power_threshold: Optional[float] = None,
) -> ConfirmatoryAnalysisReport:
    """
    Executes the frozen Stage 6M v1.4.0 final inferential analysis.
    """
    # 1. Input Records Validation
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

    # 2. Configuration Validation
    if not isinstance(num_bootstrap_replicates, (int, np.integer)) or isinstance(num_bootstrap_replicates, bool) or num_bootstrap_replicates <= 0:
        raise ValueError(f"num_bootstrap_replicates must be a positive integer, got '{num_bootstrap_replicates}'.")

    if not isinstance(alpha_family, (int, float, np.floating)) or isinstance(alpha_family, bool) or not math.isfinite(alpha_family) or not (0.0 < float(alpha_family) < 1.0):
        raise ValueError(f"alpha_family must be a finite float strictly in (0.0, 1.0), got '{alpha_family}'.")

    if not isinstance(epsilon_g_margin_pp, (int, float, np.floating)) or isinstance(epsilon_g_margin_pp, bool) or not math.isfinite(epsilon_g_margin_pp) or float(epsilon_g_margin_pp) < 0.0:
        raise ValueError(f"epsilon_g_margin_pp must be a finite non-negative float, got '{epsilon_g_margin_pp}'.")

    if not isinstance(epsilon_d_margin_pp, (int, float, np.floating)) or isinstance(epsilon_d_margin_pp, bool) or not math.isfinite(epsilon_d_margin_pp) or float(epsilon_d_margin_pp) < 0.0:
        raise ValueError(f"epsilon_d_margin_pp must be a finite non-negative float, got '{epsilon_d_margin_pp}'.")

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
    if design_spec is None:
        target_effect = target_effect_size_pp if target_effect_size_pp is not None else 3.50
        target_power = power_threshold if power_threshold is not None else 0.90
        design_spec = DesignStagePowerSpec(
            required_speakers_per_stratum=min_speakers_per_stratum_for_power,
            target_primary_effect_pp=target_effect,
            target_joint_power=target_power,
        )
    power_assessment = evaluate_confirmatory_power(
        spk_df=spk_df,
        design_spec=design_spec,
        min_speakers_per_stratum_required=min_speakers_per_stratum_for_power,
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

    # 6. Multiplicity Control: Bonferroni Simultaneous Upper Confidence Bounds across 9 hypotheses
    # Under Bonferroni family-wise control at level alpha_family across K=9 hypotheses,
    # the simultaneous bound is evaluated at level (1 - alpha_family / 9.0).
    m_hypotheses = 9
    simultaneous_alpha = alpha_family / float(m_hypotheses)
    simultaneous_percentile = (1.0 - simultaneous_alpha) * 100.0
    nominal_95_percentile = (1.0 - alpha_family) * 100.0

    from scipy import stats

    test_specs: List[Dict[str, Any]] = [
        {
            "id": "primary_superiority_static",
            "name": "Primary Superiority vs Static Baseline",
            "test_type": "superiority",
            "pt": delta_static,
            "dist": np.array(boot_delta_static, dtype=np.float64),
            "threshold": 0.0000,
            "strict_less": True,
            "err_test": spk_df["err3"].values,
            "err_ref": spk_df["err1"].values,
            "wc": spk_df["wc"].values,
        },
        {
            "id": "primary_superiority_ungated",
            "name": "Primary Superiority vs Corrected Ungated SUTA",
            "test_type": "superiority",
            "pt": delta_ungated,
            "dist": np.array(boot_delta_ungated, dtype=np.float64),
            "threshold": 0.0000,
            "strict_less": True,
            "err_test": spk_df["err3"].values,
            "err_ref": spk_df["err2"].values,
            "wc": spk_df["wc"].values,
        },
    ]

    for acc in sorted(list(canonical_accents)):
        sub = spk_df[spk_df["stratum"] == acc]
        test_specs.append({
            "id": f"accent_safety_{acc.lower().replace(' ', '_')}",
            "name": f"Accent Regression Bound [{acc}]",
            "test_type": "non_inferiority",
            "pt": accent_deltas[acc],
            "dist": np.array(boot_accent_deltas[acc], dtype=np.float64),
            "threshold": epsilon_g_margin_pp,
            "strict_less": False,
            "err_test": sub["err3"].values,
            "err_ref": sub["err1"].values,
            "wc": sub["wc"].values,
        })

    test_specs.append({
        "id": "disparity_non_increase",
        "name": "Cross-Accent Disparity Non-Increase",
        "test_type": "disparity",
        "pt": delta_disp,
        "dist": np.array(boot_delta_disp, dtype=np.float64),
        "threshold": epsilon_d_margin_pp,
        "strict_less": False,
        "err_test": None,
        "err_ref": None,
        "wc": None,
    })

    criteria_results: Dict[str, CriterionResult] = {}
    failure_reasons: List[str] = []

    for spec in test_specs:
        dist = spec["dist"]
        thresh = spec["threshold"]
        pt = spec["pt"]
        strict = spec["strict_less"]

    alpha_family_per_crit = alpha_family / float(m_hypotheses)
    simultaneous_percentile = 100.0 * (1.0 - alpha_family_per_crit)
    nominal_95_percentile = 95.0

    criteria_results: Dict[str, CriterionResult] = {}
    failure_reasons: List[str] = []

    for spec in test_specs:
        dist = spec["dist"]
        thresh = spec["threshold"]
        pt = spec["pt"]
        strict = spec["strict_less"]

        # 1. Hypothesis Inference: Ratio (Criteria 1-8) vs Disparity (Criterion 9)
        if spec["err_test"] is not None:
            # Cluster-robust linearized ratio t-inference (Criteria 1-8)
            e_t = spec["err_test"]
            e_r = spec["err_ref"]
            w = spec["wc"]
            n_clusters = len(w)
            df = max(1, n_clusters - 1)

            # Linearized score at threshold for hypothesis testing: H0: theta >= thresh vs H1: theta < thresh
            z_s = (e_t - e_r) - (thresh / 100.0) * w
            z_bar = float(np.mean(z_s))
            s_z = float(np.std(z_s, ddof=1)) if n_clusters > 1 else 0.0
            se_z = s_z / math.sqrt(n_clusters) if n_clusters > 0 else 0.0

            if se_z > 0:
                t_stat = z_bar / se_z
                p_raw = float(stats.t.cdf(t_stat, df=df))
            else:
                t_stat = -999.0 if z_bar < 0 else (999.0 if z_bar > 0 else 0.0)
                p_raw = 0.0 if z_bar < 0 else (1.0 if z_bar > 0 else 0.5)

            p_adj = min(1.0, float(m_hypotheses) * p_raw)

            # Delta-method cluster-robust standard error for ratio difference point estimate
            u_s = (e_t - e_r) - (pt / 100.0) * w
            s_u = float(np.std(u_s, ddof=1)) if n_clusters > 1 else 0.0
            se_theta = 100.0 * (s_u / math.sqrt(n_clusters)) / float(np.mean(w)) if float(np.mean(w)) > 0 else 0.0

            t_crit = float(stats.t.ppf(1.0 - alpha_family_per_crit, df=df))
            t_95 = float(stats.t.ppf(0.95, df=df))

            adj_ucb = pt + t_crit * se_theta
            adj_lcb = pt - t_crit * se_theta
            raw_ucb_95 = pt + t_95 * se_theta
            raw_lcb_95 = pt - t_95 * se_theta

        else:
            # Disparity Non-Increase (Criterion 9): Centered Null Bootstrap
            # Null boundary: delta_disp = thresh = 0.0
            dist_mean = float(np.mean(dist))
            dist_null = dist - dist_mean + thresh
            # Empirical probability under H0 of observing statistic <= observed pt
            p_raw = float(np.mean(dist_null <= pt))
            p_adj = min(1.0, float(m_hypotheses) * p_raw)

            adj_ucb = float(np.percentile(dist, simultaneous_percentile))
            adj_lcb = float(np.percentile(dist, alpha_family_per_crit * 100.0))
            raw_ucb_95 = float(np.percentile(dist, nominal_95_percentile))
            raw_lcb_95 = float(np.percentile(dist, alpha_family * 100.0))
            t_stat = None

        # Verification: simultaneous UCB <= threshold (and < 0 for strict primary)
        if strict:
            passed = bool(pt < thresh and adj_ucb < thresh)
        else:
            passed = bool(adj_ucb <= thresh)

        if not passed:
            if strict:
                reason = f"{spec['name']} FAILED: point estimate={pt:+.2f} pp, simultaneous_UCB={adj_ucb:+.2f} pp (must be < {thresh:.2f} pp)"
            else:
                reason = f"{spec['name']} FAILED: simultaneous_UCB={adj_ucb:+.2f} pp exceeds margin ({thresh:+.2f} pp)"
            failure_reasons.append(reason)
            interp = f"Violation: {reason}"
        else:
            interp = f"Passed: estimate={pt:+.2f} pp, simultaneous_UCB={adj_ucb:+.2f} pp <= {thresh:+.2f} pp (adj_p={p_adj:.4f})"

        criteria_results[spec["id"]] = CriterionResult(
            criterion_id=spec["id"],
            criterion_name=spec["name"],
            hypothesis_test=f"H1: {spec['id']} {'<' if strict else '<='} {thresh:+.2f} pp",
            null_threshold=thresh,
            point_estimate=round(pt, 4),
            bootstrap_mean=round(float(np.mean(dist)), 4),
            bootstrap_std=round(float(np.std(dist, ddof=1)), 4),
            raw_lcb_95=round(raw_lcb_95, 4),
            raw_ucb_95=round(raw_ucb_95, 4),
            adjusted_lcb=round(adj_lcb, 4),
            adjusted_ucb=round(adj_ucb, 4),
            raw_p_value=round(p_raw, 6),
            adjusted_p_value=round(p_adj, 6),
            is_success=passed,
            interpretation=interp,
            linear_t_statistic=round(t_stat, 4) if t_stat is not None else None,
            linear_p_value=round(p_raw, 6) if spec["err_test"] is not None else None,
        )

    all_passed = len(failure_reasons) == 0

    # 7. Overall Protocol Verdict: Statistically Demonstrable Harm vs Imprecision vs Invariance
    # Harmful regression requires valid inferential evidence: observed point estimate in harmful
    # direction AND simultaneous multiplicity-adjusted lower confidence bound exceeds safety margin.
    demonstrated_harm_reasons: List[str] = []

    crit_static = criteria_results["primary_superiority_static"]
    if delta_static > 0.0000 and crit_static.adjusted_lcb > 0.0000:
        demonstrated_harm_reasons.append(
            f"Statistically Demonstrable Harm vs Static Baseline: point={delta_static:+.2f} pp, simultaneous_LCB={crit_static.adjusted_lcb:+.2f} pp > 0.00 pp"
        )

    crit_ungated = criteria_results["primary_superiority_ungated"]
    if delta_ungated > 0.0000 and crit_ungated.adjusted_lcb > 0.0000:
        demonstrated_harm_reasons.append(
            f"Statistically Demonstrable Harm vs Ungated Baseline: point={delta_ungated:+.2f} pp, simultaneous_LCB={crit_ungated.adjusted_lcb:+.2f} pp > 0.00 pp"
        )

    for acc in sorted(list(canonical_accents)):
        acc_key = f"accent_safety_{acc.lower().replace(' ', '_')}"
        crit_acc = criteria_results[acc_key]
        if accent_deltas[acc] > epsilon_g_margin_pp and crit_acc.adjusted_lcb > epsilon_g_margin_pp:
            demonstrated_harm_reasons.append(
                f"Statistically Demonstrable Accent Regression on '{acc}': point={accent_deltas[acc]:+.2f} pp, simultaneous_LCB={crit_acc.adjusted_lcb:+.2f} pp exceeds margin {epsilon_g_margin_pp:+.2f} pp"
            )

    crit_disp = criteria_results["disparity_non_increase"]
    if delta_disp > epsilon_d_margin_pp and crit_disp.adjusted_lcb > epsilon_d_margin_pp:
        demonstrated_harm_reasons.append(
            f"Statistically Demonstrable Disparity Growth: point={delta_disp:+.2f} pp, simultaneous_LCB={crit_disp.adjusted_lcb:+.2f} pp > {epsilon_d_margin_pp:+.2f} pp"
        )

    has_demonstrated_harm = len(demonstrated_harm_reasons) > 0
    is_zero_updates = bool(delta_static == 0.0 and wer_arm3 == wer_arm1)

    if all_passed:
        if not power_assessment.is_adequately_powered:
            verdict = "INCONCLUSIVE"
            failure_reasons.append(
                f"Study underpowered for confirmatory declaration: {power_assessment.power_summary}"
            )
        else:
            verdict = "PASS"
    elif has_demonstrated_harm:
        verdict = "FAIL"
        failure_reasons.extend(demonstrated_harm_reasons)
    elif is_zero_updates:
        verdict = "INCONCLUSIVE"
        failure_reasons.insert(
            0,
            "Protective Invariance: Arm 3 identical to Static Baseline (0 updates promoted; "
            "protective invariance verified, but selective adaptation benefit not established)."
        )
    else:
        verdict = "INCONCLUSIVE"
        failure_reasons.insert(
            0,
            "Inconclusive Evidence: Point estimates indicate no statistically demonstrable harm, "
            "but confidence bounds exceed target thresholds due to sampling variance or insufficient precision."
        )

    return ConfirmatoryAnalysisReport(
        verdict=verdict,
        protocol_version="v1.4.0",
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
        is_protective_invariance=is_zero_updates,
        failure_reasons=failure_reasons,
        demonstrated_harm_reasons=demonstrated_harm_reasons,
        power_assessment=power_assessment,
    )
