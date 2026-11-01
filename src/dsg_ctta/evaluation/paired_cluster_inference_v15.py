"""
Stage 6M v1.5 Candidate — Five-Stratum Confirmatory Paired Cluster Inference Module
====================================================================================
Implements the candidate inferential analysis prescribed in:
`stage6m_v1_5_candidate_five_stratum_protocol_spec.md` (Sections 1, 6, 7, 12, 13).

GOVERNANCE RESTRICTIONS:
- Dedicated to the v1.5 Five-Stratum Candidate.
- Frozen v1.4.0 execution code (`paired_cluster_inference.py`) remains strictly immutable.
- Status: CANDIDATE INFERENCE ENGINE (Pre-Registration Draft, DRAFT_HOLD).

Requirements Enforced:
1. Five Canonical Confirmatory Accents: Australian, Canadian, England, South Asian, US English.
2. Irish English is strictly excluded from confirmatory analysis; retained as exploratory out-of-domain.
3. Multiplicity Control: Fixed Single-Step Simultaneous Bonferroni across M = 8 hypotheses:
     alpha_family = 0.05
     alpha_adj = 0.05 / 8 = 0.00625
     Simultaneous one-sided confidence percentile = 99.375%.
4. Primary Criterion 1 (Event A): DSG superiority over Static Baseline
     H1: Delta_static < 0.00 pp (adjusted Wald linearized ratio UCB < 0.00 pp).
5. Primary Criterion 2 (Event B): DSG superiority over Corrected Ungated SUTA
     H1: Delta_ungated < 0.00 pp (adjusted Wald linearized ratio UCB < 0.00 pp).
6. Fairness Criterion 3 (Event C): Accent regression guards across all 5 confirmatory strata
     H1: Delta_g <= +2.00 pp (adjusted Wald linearized ratio UCB <= +2.00 pp for all 5 strata).
7. Fairness Criterion 4 (Event D): Disparity non-increase across 5 confirmatory strata
     H1: Delta_D <= 0.00 pp (stratified paired cluster bootstrap 99.375th percentile UCB <= 0.00 pp).
8. Synchronous Joint Decision: Event A and Event B and Event C and Event D.
9. Machine-readable overall verdict (PASS / FAIL / INCONCLUSIVE).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Tuple, FrozenSet
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

if HAS_NUMBA:
    @njit(parallel=True, fastmath=True)
    def _numba_stratified_bootstrap_v15(wc, err1, err3, n_spk_per_accent, n_accents, B):
        delta_ds = np.empty(B, dtype=np.float64)
        for b in prange(B):
            max1 = -1e9
            min1 = 1e9
            max3 = -1e9
            min3 = 1e9
            for a in range(n_accents):
                n_spk = n_spk_per_accent[a]
                w_sum = 0.0
                e1_sum = 0.0
                e3_sum = 0.0
                for i in range(n_spk):
                    idx = np.random.randint(0, n_spk)
                    w_sum += wc[a, idx]
                    e1_sum += err1[a, idx]
                    e3_sum += err3[a, idx]
                wer1 = (e1_sum / w_sum) * 100.0
                wer3 = (e3_sum / w_sum) * 100.0
                if wer1 > max1: max1 = wer1
                if wer1 < min1: min1 = wer1
                if wer3 > max3: max3 = wer3
                if wer3 < min3: min3 = wer3
            d1 = max1 - min1
            d3 = max3 - min3
            delta_ds[b] = d3 - d1
        return delta_ds


FIVE_STRATUM_CONFIRMATORY_ACCENTS: FrozenSet[str] = frozenset([
    "Australian English",
    "Canadian English",
    "England English",
    "South Asian English",
    "US English",
])

EXPLORATORY_OUT_OF_DOMAIN_ACCENTS: FrozenSet[str] = frozenset([
    "Irish English",
])

# Canonical baseline WER benchmarks from Common Voice 27.0 development benchmarks
CANONICAL_BENCHMARK_BASE_WERS: Dict[str, float] = {
    "Australian English": 19.3,
    "Canadian English": 16.1,
    "England English": 17.4,
    "South Asian English": 23.5,
    "US English": 14.2,
    "Irish English": 26.1,  # Retained for exploratory tracking
}


@dataclass
class CandidateFiveStratumPowerSpec:
    """Design-stage simulation power specification for the five-stratum candidate."""
    target_primary_effect_pp: float = 3.50
    target_ungated_effect_pp: float = 3.50
    target_disparity_effect_pp: float = -2.00
    between_speaker_wer_std: float = 6.50
    paired_diff_std: float = 3.20
    alpha_family: float = 0.05
    m_hypotheses: int = 8
    target_joint_power: float = 0.90
    required_speakers_per_stratum: int = 220
    recommended_speakers_per_stratum_for_90_power: int = 285
    required_clips_per_speaker: int = 15
    require_lcb_threshold: bool = True
    num_simulations: int = 2000
    baseline_wers: Optional[Dict[str, float]] = None

    @property
    def adj_alpha(self) -> float:
        return self.alpha_family / float(self.m_hypotheses)

    @property
    def simultaneous_percentile(self) -> float:
        return 100.0 * (1.0 - self.adj_alpha)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["adj_alpha"] = self.adj_alpha
        d["simultaneous_percentile"] = self.simultaneous_percentile
        return d


@dataclass
class CriterionResultV15:
    """Detailed inferential evaluation of a single confirmatory criterion under v1.5."""
    criterion_id: str
    criterion_name: str
    hypothesis_test: str
    null_threshold: float
    point_estimate: float
    raw_lcb_95: float
    raw_ucb_95: float
    adjusted_lcb: float
    adjusted_ucb: float
    raw_p_value: float
    adjusted_p_value: float
    is_success: bool
    interpretation: str
    linear_t_statistic: Optional[float] = None
    linear_se: Optional[float] = None
    bootstrap_mean: Optional[float] = None
    bootstrap_std: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExploratoryStratumResult:
    """Evaluation of an exploratory out-of-domain stratum (e.g. Irish English)."""
    stratum: str
    num_speakers: int
    total_words: int
    wer_arm1_static: float
    wer_arm2_ungated: float
    wer_arm3_dsg: float
    delta_static_pp: float
    delta_ungated_pp: float
    raw_ucb_95_static_pp: float
    raw_ucb_95_ungated_pp: float
    notes: str = "Exploratory out-of-domain evaluation. Strictly excluded from confirmatory M=8 family."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConfirmatoryAnalysisReportV15:
    """Comprehensive machine-readable verdict and inferential evidence report for v1.5 candidate."""
    verdict: str  # "PASS" | "FAIL" | "INCONCLUSIVE"
    protocol_version: str
    num_speakers: int
    num_confirmatory_strata: int
    num_bootstrap_replicates: int
    alpha_family: float
    alpha_adj: float
    m_hypotheses: int
    simultaneous_percentile: float
    epsilon_g_margin_pp: float
    epsilon_d_margin_pp: float

    # Point estimates across 5 confirmatory strata
    corpus_wer_arm1_static: float
    corpus_wer_arm2_ungated: float
    corpus_wer_arm3_dsg: float
    delta_static_pp: float
    delta_ungated_pp: float
    disparity_arm1_pp: float
    disparity_arm2_pp: float
    disparity_arm3_pp: float
    delta_disparity_pp: float

    # Stratum-level breakdown
    accent_wers_arm1: Dict[str, float]
    accent_wers_arm2: Dict[str, float]
    accent_wers_arm3: Dict[str, float]
    accent_deltas_pp: Dict[str, float]

    # Evaluated Criteria (M=8)
    criteria: Dict[str, CriterionResultV15]
    all_criteria_passed: bool

    # Exploratory strata (Irish English)
    exploratory_strata: Dict[str, ExploratoryStratumResult] = field(default_factory=dict)

    # Governance & Verdict diagnostics
    is_protective_invariance: bool = False
    failure_reasons: List[str] = field(default_factory=list)
    demonstrated_harm_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["criteria"] = {k: v.to_dict() for k, v in self.criteria.items()}
        d["exploratory_strata"] = {k: v.to_dict() for k, v in self.exploratory_strata.items()}
        return d


def _validate_raw_integer_count(
    val: Any,
    name: str,
    speaker_id: str,
    min_val: int = 0,
    is_strictly_positive: bool = False,
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


def run_confirmatory_paired_cluster_inference_v15(
    speaker_records: List[Dict[str, Any]],
    num_bootstrap_replicates: int = 20000,
    seed: int = 42,
    alpha_family: float = 0.05,
    epsilon_g_margin_pp: float = 2.00,
    epsilon_d_margin_pp: float = 0.00,
    confirmatory_accents: FrozenSet[str] = FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    exploratory_accents: FrozenSet[str] = EXPLORATORY_OUT_OF_DOMAIN_ACCENTS,
    custom_bootstrap_resamples: Optional[np.ndarray] = None,
    use_fast_bootstrap: bool = True,
) -> ConfirmatoryAnalysisReportV15:
    """
    Executes the v1.5 Candidate Five-Stratum confirmatory inferential analysis.

    Parameters:
      speaker_records: List of dicts with fields [speaker_id, stratum, wc, err1, err2, err3]
      num_bootstrap_replicates: Bootstrap resamples for Event D disparity UCB (default 20,000)
      seed: RNG seed for reproducible stratified cluster bootstrap
      alpha_family: Prespecified family-wise alpha (0.05)
      epsilon_g_margin_pp: Per-accent regression margin (+2.00 pp)
      epsilon_d_margin_pp: Disparity non-increase margin (0.00 pp)
      confirmatory_accents: Five confirmatory strata (Australian, Canadian, England, South Asian, US)
      exploratory_accents: Exploratory out-of-domain strata (Irish English)
      custom_bootstrap_resamples: Optional pre-generated 2D/3D integer index array for exact parity testing

    Returns:
      ConfirmatoryAnalysisReportV15 containing full hypothesis evidence and machine verdict.
    """
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

    # Validate configuration parameters
    if not isinstance(num_bootstrap_replicates, (int, np.integer)) or isinstance(num_bootstrap_replicates, bool) or num_bootstrap_replicates <= 0:
        raise ValueError(f"num_bootstrap_replicates must be a positive integer, got '{num_bootstrap_replicates}'.")

    if not isinstance(alpha_family, (int, float, np.floating)) or isinstance(alpha_family, bool) or not math.isfinite(alpha_family) or not (0.0 < float(alpha_family) < 1.0):
        raise ValueError(f"alpha_family must be a finite float strictly in (0.0, 1.0), got '{alpha_family}'.")

    if not isinstance(epsilon_g_margin_pp, (int, float, np.floating)) or isinstance(epsilon_g_margin_pp, bool) or not math.isfinite(epsilon_g_margin_pp) or float(epsilon_g_margin_pp) < 0.0:
        raise ValueError(f"epsilon_g_margin_pp must be a finite non-negative float, got '{epsilon_g_margin_pp}'.")

    if not isinstance(epsilon_d_margin_pp, (int, float, np.floating)) or isinstance(epsilon_d_margin_pp, bool) or not math.isfinite(epsilon_d_margin_pp) or float(epsilon_d_margin_pp) < 0.0:
        raise ValueError(f"epsilon_d_margin_pp must be a finite non-negative float, got '{epsilon_d_margin_pp}'.")

    spk_df = pd.DataFrame(cleaned_records)

    # Separate confirmatory and exploratory strata
    observed_strata = set(spk_df["stratum"].astype(str))
    missing_confirmatory = set(confirmatory_accents) - observed_strata
    if missing_confirmatory:
        raise ValueError(f"Missing mandatory confirmatory strata: {sorted(list(missing_confirmatory))}")

    # Check for unauthorized strata outside confirmatory and exploratory sets
    unauthorized_strata = observed_strata - set(confirmatory_accents) - set(exploratory_accents)
    if unauthorized_strata:
        raise ValueError(f"Unauthorized accent strata detected in evaluation cohort: {sorted(list(unauthorized_strata))}")

    # Check minimum 2 speakers per confirmatory stratum for cluster variance estimation
    for acc in sorted(list(confirmatory_accents)):
        cnt = int((spk_df["stratum"] == acc).sum())
        if cnt < 2:
            raise ValueError(f"Confirmatory stratum '{acc}' has only {cnt} speakers; minimum 2 required.")

    # Filter confirmatory dataframe
    conf_df = spk_df[spk_df["stratum"].isin(confirmatory_accents)].copy()
    n_conf_speakers = len(conf_df)

    # 4. Point Estimates Computation (strictly across the 5 confirmatory strata)
    total_words = float(conf_df["wc"].sum())
    total_e1 = float(conf_df["err1"].sum())
    total_e2 = float(conf_df["err2"].sum())
    total_e3 = float(conf_df["err3"].sum())

    wer_arm1 = (total_e1 / total_words) * 100.0
    wer_arm2 = (total_e2 / total_words) * 100.0
    wer_arm3 = (total_e3 / total_words) * 100.0

    delta_static = wer_arm3 - wer_arm1
    delta_ungated = wer_arm3 - wer_arm2

    # Accent-level WERs across 5 confirmatory strata
    accent_wers1: Dict[str, float] = {}
    accent_wers2: Dict[str, float] = {}
    accent_wers3: Dict[str, float] = {}
    accent_deltas: Dict[str, float] = {}

    for acc in sorted(list(confirmatory_accents)):
        sub = conf_df[conf_df["stratum"] == acc]
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

    # 5. Multiplicity Control: M = 8 Fixed Bonferroni
    m_hypotheses = 8
    adj_alpha = alpha_family / float(m_hypotheses)
    simultaneous_percentile = 100.0 * (1.0 - adj_alpha)
    nominal_95_percentile = 100.0 * (1.0 - alpha_family)

    df_corp = max(1, n_conf_speakers - 1)
    t_crit_corp = float(scipy_stats.t.ppf(1.0 - adj_alpha, df=df_corp))
    t_95_corp = float(scipy_stats.t.ppf(1.0 - alpha_family, df=df_corp))

    all_wc = conf_df["wc"].values.astype(float)
    all_e1 = conf_df["err1"].values.astype(float)
    all_e2 = conf_df["err2"].values.astype(float)
    all_e3 = conf_df["err3"].values.astype(float)
    w_bar_corp = float(np.mean(all_wc))

    criteria_results: Dict[str, CriterionResultV15] = {}
    failure_reasons: List[str] = []

    # Criterion 1: Primary Superiority vs Static Baseline (Event A)
    u_s = (all_e3 - all_e1) - (delta_static / 100.0) * all_wc
    s_u_s = float(np.std(u_s, ddof=1)) if n_conf_speakers > 1 else 0.0
    se_static = 100.0 * (s_u_s / math.sqrt(n_conf_speakers)) / w_bar_corp if w_bar_corp > 0 else 0.0
    t_stat_static = (delta_static / se_static) if se_static > 0 else (0.0 if delta_static == 0 else (-999.0 if delta_static < 0 else 999.0))
    p_raw_static = float(scipy_stats.t.cdf(t_stat_static, df=df_corp))
    p_adj_static = min(1.0, float(m_hypotheses) * p_raw_static)

    adj_ucb_static = delta_static + t_crit_corp * se_static
    adj_lcb_static = delta_static - t_crit_corp * se_static
    raw_ucb_static = delta_static + t_95_corp * se_static
    raw_lcb_static = delta_static - t_95_corp * se_static

    pass_static = bool(delta_static < 0.0000 and adj_ucb_static < 0.0000)
    if not pass_static:
        failure_reasons.append(
            f"Primary Superiority vs Static Baseline FAILED: estimate={delta_static:+.2f} pp, "
            f"simultaneous_UCB={adj_ucb_static:+.2f} pp (must be < 0.00 pp)"
        )
    criteria_results["primary_superiority_static"] = CriterionResultV15(
        criterion_id="primary_superiority_static",
        criterion_name="Primary Superiority vs Static Baseline",
        hypothesis_test="H1: Delta_static < 0.00 pp",
        null_threshold=0.0000,
        point_estimate=round(delta_static, 4),
        raw_lcb_95=round(raw_lcb_static, 4),
        raw_ucb_95=round(raw_ucb_static, 4),
        adjusted_lcb=round(adj_lcb_static, 4),
        adjusted_ucb=round(adj_ucb_static, 4),
        raw_p_value=round(p_raw_static, 6),
        adjusted_p_value=round(p_adj_static, 6),
        is_success=pass_static,
        interpretation=(
            f"Passed: estimate={delta_static:+.2f} pp, simultaneous_UCB={adj_ucb_static:+.2f} pp < 0.00 pp (adj_p={p_adj_static:.4f})"
            if pass_static else f"Violation: simultaneous_UCB={adj_ucb_static:+.2f} pp >= 0.00 pp"
        ),
        linear_t_statistic=round(t_stat_static, 4),
        linear_se=round(se_static, 4),
    )

    # Criterion 2: Primary Superiority vs Corrected Ungated SUTA (Event B)
    u_u = (all_e3 - all_e2) - (delta_ungated / 100.0) * all_wc
    s_u_u = float(np.std(u_u, ddof=1)) if n_conf_speakers > 1 else 0.0
    se_ungated = 100.0 * (s_u_u / math.sqrt(n_conf_speakers)) / w_bar_corp if w_bar_corp > 0 else 0.0
    t_stat_ungated = (delta_ungated / se_ungated) if se_ungated > 0 else (0.0 if delta_ungated == 0 else (-999.0 if delta_ungated < 0 else 999.0))
    p_raw_ungated = float(scipy_stats.t.cdf(t_stat_ungated, df=df_corp))
    p_adj_ungated = min(1.0, float(m_hypotheses) * p_raw_ungated)

    adj_ucb_ungated = delta_ungated + t_crit_corp * se_ungated
    adj_lcb_ungated = delta_ungated - t_crit_corp * se_ungated
    raw_ucb_ungated = delta_ungated + t_95_corp * se_ungated
    raw_lcb_ungated = delta_ungated - t_95_corp * se_ungated

    pass_ungated = bool(delta_ungated < 0.0000 and adj_ucb_ungated < 0.0000)
    if not pass_ungated:
        failure_reasons.append(
            f"Primary Superiority vs Ungated Baseline FAILED: estimate={delta_ungated:+.2f} pp, "
            f"simultaneous_UCB={adj_ucb_ungated:+.2f} pp (must be < 0.00 pp)"
        )
    criteria_results["primary_superiority_ungated"] = CriterionResultV15(
        criterion_id="primary_superiority_ungated",
        criterion_name="Primary Superiority vs Corrected Ungated SUTA",
        hypothesis_test="H1: Delta_ungated < 0.00 pp",
        null_threshold=0.0000,
        point_estimate=round(delta_ungated, 4),
        raw_lcb_95=round(raw_lcb_ungated, 4),
        raw_ucb_95=round(raw_ucb_ungated, 4),
        adjusted_lcb=round(adj_lcb_ungated, 4),
        adjusted_ucb=round(adj_ucb_ungated, 4),
        raw_p_value=round(p_raw_ungated, 6),
        adjusted_p_value=round(p_adj_ungated, 6),
        is_success=pass_ungated,
        interpretation=(
            f"Passed: estimate={delta_ungated:+.2f} pp, simultaneous_UCB={adj_ucb_ungated:+.2f} pp < 0.00 pp (adj_p={p_adj_ungated:.4f})"
            if pass_ungated else f"Violation: simultaneous_UCB={adj_ucb_ungated:+.2f} pp >= 0.00 pp"
        ),
        linear_t_statistic=round(t_stat_ungated, 4),
        linear_se=round(se_ungated, 4),
    )

    # Criteria 3-7: Accent-Specific Regression Bounds across 5 Confirmatory Strata (Event C)
    for acc in sorted(list(confirmatory_accents)):
        sub = conf_df[conf_df["stratum"] == acc]
        n_g = len(sub)
        df_g = max(1, n_g - 1)
        t_crit_g = float(scipy_stats.t.ppf(1.0 - adj_alpha, df=df_g))
        t_95_g = float(scipy_stats.t.ppf(1.0 - alpha_family, df=df_g))

        gw = sub["wc"].values.astype(float)
        ge1 = sub["err1"].values.astype(float)
        ge3 = sub["err3"].values.astype(float)
        d_g = accent_deltas[acc]

        u_g = (ge3 - ge1) - (d_g / 100.0) * gw
        s_u_g = float(np.std(u_g, ddof=1)) if n_g > 1 else 0.0
        w_bar_g = float(np.mean(gw))
        se_g = 100.0 * (s_u_g / math.sqrt(n_g)) / w_bar_g if w_bar_g > 0 else 0.0

        diff_from_margin = d_g - epsilon_g_margin_pp
        t_stat_g = (diff_from_margin / se_g) if se_g > 0 else (0.0 if diff_from_margin == 0 else (-999.0 if diff_from_margin < 0 else 999.0))
        p_raw_g = float(scipy_stats.t.cdf(t_stat_g, df=df_g))
        p_adj_g = min(1.0, float(m_hypotheses) * p_raw_g)

        adj_ucb_g = d_g + t_crit_g * se_g
        adj_lcb_g = d_g - t_crit_g * se_g
        raw_ucb_g = d_g + t_95_g * se_g
        raw_lcb_g = d_g - t_95_g * se_g

        pass_g = bool(adj_ucb_g <= epsilon_g_margin_pp)
        if not pass_g:
            failure_reasons.append(
                f"Accent Regression Bound [{acc}] FAILED: simultaneous_UCB={adj_ucb_g:+.2f} pp "
                f"exceeds margin ({epsilon_g_margin_pp:+.2f} pp)"
            )

        cid = f"accent_safety_{acc.lower().replace(' ', '_')}"
        criteria_results[cid] = CriterionResultV15(
            criterion_id=cid,
            criterion_name=f"Accent Regression Bound [{acc}]",
            hypothesis_test=f"H1: Delta_{acc} <= +{epsilon_g_margin_pp:.2f} pp",
            null_threshold=epsilon_g_margin_pp,
            point_estimate=round(d_g, 4),
            raw_lcb_95=round(raw_lcb_g, 4),
            raw_ucb_95=round(raw_ucb_g, 4),
            adjusted_lcb=round(adj_lcb_g, 4),
            adjusted_ucb=round(adj_ucb_g, 4),
            raw_p_value=round(p_raw_g, 6),
            adjusted_p_value=round(p_adj_g, 6),
            is_success=pass_g,
            interpretation=(
                f"Passed: estimate={d_g:+.2f} pp, simultaneous_UCB={adj_ucb_g:+.2f} pp <= {epsilon_g_margin_pp:+.2f} pp (adj_p={p_adj_g:.4f})"
                if pass_g else f"Violation: simultaneous_UCB={adj_ucb_g:+.2f} pp > {epsilon_g_margin_pp:+.2f} pp"
            ),
            linear_t_statistic=round(t_stat_g, 4),
            linear_se=round(se_g, 4),
        )

    # Criterion 8: Disparity Non-Increase via Stratified Paired Cluster Bootstrap (Event D)
    # Prepare stratified speaker arrays
    accents_sorted = sorted(list(confirmatory_accents))
    n_accents = len(accents_sorted)
    stratum_data: List[Dict[str, np.ndarray]] = []
    for acc in accents_sorted:
        sub = conf_df[conf_df["stratum"] == acc]
        stratum_data.append({
            "wc": sub["wc"].values.astype(float),
            "e1": sub["err1"].values.astype(float),
            "e3": sub["err3"].values.astype(float),
            "n": len(sub),
        })

    rng = np.random.default_rng(seed)
    boot_delta_disp = np.zeros(num_bootstrap_replicates, dtype=float)

    if custom_bootstrap_resamples is not None:
        # custom_bootstrap_resamples is assumed shape (n_accents, num_bootstrap_replicates, n_g)
        for b in range(num_bootstrap_replicates):
            bw1 = np.zeros(n_accents)
            bw3 = np.zeros(n_accents)
            for a_idx in range(n_accents):
                s = stratum_data[a_idx]
                bi = custom_bootstrap_resamples[a_idx, b]
                gw = float(np.sum(s["wc"][bi]))
                if gw > 0:
                    bw1[a_idx] = (float(np.sum(s["e1"][bi])) / gw) * 100.0
                    bw3[a_idx] = (float(np.sum(s["e3"][bi])) / gw) * 100.0
            boot_delta_disp[b] = (np.max(bw3) - np.min(bw3)) - (np.max(bw1) - np.min(bw1))
    elif use_fast_bootstrap and HAS_NUMBA:
        max_spk = max(s["n"] for s in stratum_data)
        wc_2d = np.zeros((n_accents, max_spk), dtype=float)
        err1_2d = np.zeros((n_accents, max_spk), dtype=float)
        err3_2d = np.zeros((n_accents, max_spk), dtype=float)
        n_spk_arr = np.array([s["n"] for s in stratum_data], dtype=np.int64)
        for a_idx, s in enumerate(stratum_data):
            n_g = s["n"]
            wc_2d[a_idx, :n_g] = s["wc"]
            err1_2d[a_idx, :n_g] = s["e1"]
            err3_2d[a_idx, :n_g] = s["e3"]
        boot_delta_disp = _numba_stratified_bootstrap_v15(
            wc_2d, err1_2d, err3_2d, n_spk_arr, n_accents, num_bootstrap_replicates
        )
    else:
        for b in range(num_bootstrap_replicates):
            bw1 = np.zeros(n_accents)
            bw3 = np.zeros(n_accents)
            for a_idx in range(n_accents):
                s = stratum_data[a_idx]
                n_g = s["n"]
                bi = rng.integers(0, n_g, size=n_g)
                gw = float(np.sum(s["wc"][bi]))
                if gw > 0:
                    bw1[a_idx] = (float(np.sum(s["e1"][bi])) / gw) * 100.0
                    bw3[a_idx] = (float(np.sum(s["e3"][bi])) / gw) * 100.0
            boot_delta_disp[b] = (np.max(bw3) - np.min(bw3)) - (np.max(bw1) - np.min(bw1))

    dist_mean = float(np.mean(boot_delta_disp))
    dist_std = float(np.std(boot_delta_disp, ddof=1)) if num_bootstrap_replicates > 1 else 0.0

    # Centered null bootstrap p-value
    dist_null = boot_delta_disp - dist_mean + epsilon_d_margin_pp
    p_raw_disp = float(np.mean(dist_null <= delta_disp))
    p_adj_disp = min(1.0, float(m_hypotheses) * p_raw_disp)

    adj_ucb_disp = float(np.percentile(boot_delta_disp, simultaneous_percentile))
    adj_lcb_disp = float(np.percentile(boot_delta_disp, adj_alpha * 100.0))
    raw_ucb_disp = float(np.percentile(boot_delta_disp, nominal_95_percentile))
    raw_lcb_disp = float(np.percentile(boot_delta_disp, alpha_family * 100.0))

    pass_disp = bool(adj_ucb_disp <= epsilon_d_margin_pp)
    if not pass_disp:
        failure_reasons.append(
            f"Disparity Non-Increase FAILED: simultaneous_UCB={adj_ucb_disp:+.2f} pp "
            f"exceeds margin ({epsilon_d_margin_pp:+.2f} pp)"
        )

    criteria_results["disparity_non_increase"] = CriterionResultV15(
        criterion_id="disparity_non_increase",
        criterion_name="Cross-Accent Disparity Non-Increase",
        hypothesis_test=f"H1: Delta_Range <= {epsilon_d_margin_pp:+.2f} pp",
        null_threshold=epsilon_d_margin_pp,
        point_estimate=round(delta_disp, 4),
        raw_lcb_95=round(raw_lcb_disp, 4),
        raw_ucb_95=round(raw_ucb_disp, 4),
        adjusted_lcb=round(adj_lcb_disp, 4),
        adjusted_ucb=round(adj_ucb_disp, 4),
        raw_p_value=round(p_raw_disp, 6),
        adjusted_p_value=round(p_adj_disp, 6),
        is_success=pass_disp,
        interpretation=(
            f"Passed: estimate={delta_disp:+.2f} pp, simultaneous_UCB={adj_ucb_disp:+.2f} pp <= {epsilon_d_margin_pp:+.2f} pp (adj_p={p_adj_disp:.4f})"
            if pass_disp else f"Violation: simultaneous_UCB={adj_ucb_disp:+.2f} pp > {epsilon_d_margin_pp:+.2f} pp"
        ),
        bootstrap_mean=round(dist_mean, 4),
        bootstrap_std=round(dist_std, 4),
    )

    all_passed = (len(failure_reasons) == 0)

    # 6. Evaluate Exploratory Strata (Irish English)
    exploratory_results: Dict[str, ExploratoryStratumResult] = {}
    for acc in sorted(list(exploratory_accents)):
        sub_e = spk_df[spk_df["stratum"] == acc]
        if len(sub_e) > 0:
            w_e = float(sub_e["wc"].sum())
            w1_e = (float(sub_e["err1"].sum()) / w_e) * 100.0 if w_e > 0 else 0.0
            w2_e = (float(sub_e["err2"].sum()) / w_e) * 100.0 if w_e > 0 else 0.0
            w3_e = (float(sub_e["err3"].sum()) / w_e) * 100.0 if w_e > 0 else 0.0
            d_s_e = w3_e - w1_e
            d_u_e = w3_e - w2_e

            n_e = len(sub_e)
            df_e = max(1, n_e - 1)
            t_95_e = float(scipy_stats.t.ppf(0.95, df=df_e))
            gw_e = sub_e["wc"].values.astype(float)
            ge1_e = sub_e["err1"].values.astype(float)
            ge2_e = sub_e["err2"].values.astype(float)
            ge3_e = sub_e["err3"].values.astype(float)

            u_se = (ge3_e - ge1_e) - (d_s_e / 100.0) * gw_e
            se_se = 100.0 * (float(np.std(u_se, ddof=1)) / math.sqrt(n_e)) / float(np.mean(gw_e)) if float(np.mean(gw_e)) > 0 else 0.0
            u_ue = (ge3_e - ge2_e) - (d_u_e / 100.0) * gw_e
            se_ue = 100.0 * (float(np.std(u_ue, ddof=1)) / math.sqrt(n_e)) / float(np.mean(gw_e)) if float(np.mean(gw_e)) > 0 else 0.0

            exploratory_results[acc] = ExploratoryStratumResult(
                stratum=acc,
                num_speakers=n_e,
                total_words=int(w_e),
                wer_arm1_static=round(w1_e, 4),
                wer_arm2_ungated=round(w2_e, 4),
                wer_arm3_dsg=round(w3_e, 4),
                delta_static_pp=round(d_s_e, 4),
                delta_ungated_pp=round(d_u_e, 4),
                raw_ucb_95_static_pp=round(d_s_e + t_95_e * se_se, 4),
                raw_ucb_95_ungated_pp=round(d_u_e + t_95_e * se_ue, 4),
            )

    # 7. Demonstrable Harm & Overall Protocol Verdict
    demonstrated_harm_reasons: List[str] = []
    if delta_static > 0.0000 and adj_lcb_static > 0.0000:
        demonstrated_harm_reasons.append(
            f"Statistically Demonstrable Harm vs Static Baseline: point={delta_static:+.2f} pp, simultaneous_LCB={adj_lcb_static:+.2f} pp > 0.00 pp"
        )
    if delta_ungated > 0.0000 and adj_lcb_ungated > 0.0000:
        demonstrated_harm_reasons.append(
            f"Statistically Demonstrable Harm vs Ungated Baseline: point={delta_ungated:+.2f} pp, simultaneous_LCB={adj_lcb_ungated:+.2f} pp > 0.00 pp"
        )
    for acc in sorted(list(confirmatory_accents)):
        cid = f"accent_safety_{acc.lower().replace(' ', '_')}"
        crit = criteria_results[cid]
        if accent_deltas[acc] > epsilon_g_margin_pp and crit.adjusted_lcb > epsilon_g_margin_pp:
            demonstrated_harm_reasons.append(
                f"Statistically Demonstrable Accent Regression on '{acc}': point={accent_deltas[acc]:+.2f} pp, simultaneous_LCB={crit.adjusted_lcb:+.2f} pp > {epsilon_g_margin_pp:+.2f} pp"
            )
    if delta_disp > epsilon_d_margin_pp and adj_lcb_disp > epsilon_d_margin_pp:
        demonstrated_harm_reasons.append(
            f"Statistically Demonstrable Disparity Growth: point={delta_disp:+.2f} pp, simultaneous_LCB={adj_lcb_disp:+.2f} pp > {epsilon_d_margin_pp:+.2f} pp"
        )

    has_demonstrated_harm = len(demonstrated_harm_reasons) > 0
    is_zero_updates = bool(delta_static == 0.0 and wer_arm3 == wer_arm1)

    if all_passed:
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

    return ConfirmatoryAnalysisReportV15(
        verdict=verdict,
        protocol_version="v1.5.0-Candidate",
        num_speakers=n_conf_speakers,
        num_confirmatory_strata=len(confirmatory_accents),
        num_bootstrap_replicates=num_bootstrap_replicates,
        alpha_family=alpha_family,
        alpha_adj=adj_alpha,
        m_hypotheses=m_hypotheses,
        simultaneous_percentile=simultaneous_percentile,
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
        exploratory_strata=exploratory_results,
        is_protective_invariance=is_zero_updates,
        failure_reasons=failure_reasons,
        demonstrated_harm_reasons=demonstrated_harm_reasons,
    )
