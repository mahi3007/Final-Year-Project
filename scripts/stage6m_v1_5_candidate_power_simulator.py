"""
Stage 6M — v1.5 Candidate Five-Stratum Power Simulator & Data-Generating Model
================================================================================

DOCUMENT STATUS: CANDIDATE DESIGN SPECIFICATION (Pre-Registration Draft)
GOVERNANCE: DRAFT_HOLD (Confirmatory Audio Materialization & Adaptation Strictly Blocked)
BASELINE PRESERVED: Protocol v1.4.0 Frozen Code & 6-Stratum Commit Identity Preserved

This module implements the calibrated data-generating model and candidate power simulator
for the proposed five-stratum confirmatory design (v1.5.0-Candidate).

ARCHITECTURAL AND GOVERNANCE SEPARATION:
1. Historical v1.4.0 Frozen Specification:
   - Evaluated 6 canonical accents (Australian, Canadian, England, Irish, South Asian, US).
   - Multiplicity family M = 9 (2 primary + 6 accent guards + 1 disparity).
   - Hardcoded in src/dsg_ctta/evaluation/paired_cluster_inference.py (IMMUTABLE).
2. Five-Stratum Candidate Assumptions (v1.5-Candidate):
   - Confirmatory Strata (K = 5): Australian, Canadian, England, South Asian, US English.
   - Exploratory Out-of-Domain Stratum (K_expl = 1): Irish English (strictly excluded
     from confirmatory hypothesis family and baseline calibration).
   - Multiplicity family M = 8 (2 primary + 5 accent guards + 1 disparity).
   - Multiplicity procedure: Fixed Single-Step Simultaneous Bonferroni (alpha_adj = 0.05 / 8 = 0.00625).
   - Authoritative Decision Engine: Simultaneous Upper Confidence Bounds (UCBs) at 99.375% confidence.
3. Empirically Supported Parameters:
   - Between-speaker WER standard deviation: sigma_between_speaker = 0.065 (6.5 pp).
   - Paired treatment-difference standard deviation: sigma_paired_diff = 0.032 (3.2 pp).
     Derived from CV27 development benchmarks and reconciled clip predictions.
     Direct speaker-level variability; NOT divided by sqrt(15).
   - Benchmark baseline WERs from Common Voice 27.0 development benchmarks.
4. Prespecified Scenario Assumptions:
   - Target primary DSG superiority vs Static: 3.5 pp (delta_static = -3.5 pp).
   - Target primary DSG superiority vs Corrected Ungated SUTA: 3.5 pp (delta_ungated = -3.5 pp).
   - Target population disparity reduction: -2.0 pp (Delta_D = -2.0 pp).
5. Sensitivity Analyses:
   - Accent effect mode: Primary design scenario treats the 5 named accents as FIXED strata.
     Optional sensitivity scenario models random accent variation (sigma_accent = 0.050).

NOTE ON PROTOCOL-EXACT STATUS:
This simulator represents the candidate design-stage data-generating model. It is NOT
called fully protocol-exact until parity has been formally established for its five-stratum
candidate inference path against independent reference implementations.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats as scipy_stats


# ------------------------------------------------------------------------------
# Canonical Constants & Strata Definitions
# ------------------------------------------------------------------------------

FIVE_STRATUM_CONFIRMATORY_ACCENTS: Tuple[str, ...] = (
    "Australian English",
    "Canadian English",
    "England English",
    "South Asian English",
    "US English",
)

EXPLORATORY_OUT_OF_DOMAIN_ACCENTS: Tuple[str, ...] = (
    "Irish English",
)

# Benchmark baseline WER values from empirical Common Voice 27 development benchmarks
CANONICAL_BENCHMARK_BASE_WERS: Dict[str, float] = {
    "Australian English": 0.193,   # 19.3 pp
    "Canadian English": 0.161,     # 16.1 pp
    "England English": 0.174,      # 17.4 pp
    "Irish English": 0.261,        # 26.1 pp (EXPLORATORY ONLY)
    "South Asian English": 0.235,  # 23.5 pp
    "US English": 0.142,           # 14.2 pp
}


# ------------------------------------------------------------------------------
# Specification Dataclass
# ------------------------------------------------------------------------------

@dataclass
class CandidateFiveStratumPowerSpec:
    """
    Design-stage simulation specification for the v1.5 Candidate 5-Stratum Protocol.

    Encapsulates all scenario targets, variance-covariance parameters, and
    multiplicity parameters for the 5-stratum candidate evaluation.
    """
    # Confirmatory Accent Strata (strictly 5, excluding Irish English)
    confirmatory_accents: Tuple[str, ...] = FIVE_STRATUM_CONFIRMATORY_ACCENTS

    # Empirical Variance Components (proportions)
    sigma_between_speaker: float = 0.065   # 6.5 pp between-speaker standard deviation
    sigma_paired_diff: float = 0.032       # 3.2 pp speaker-level paired difference standard deviation
    sigma_accent_sensitivity: float = 0.050 # 5.0 pp random accent standard deviation (sensitivity only)

    # Scenario Target Treatment Effects (percentage points)
    target_primary_effect_pp: float = 3.50   # 3.5 pp superiority over Static
    target_ungated_effect_pp: float = 3.50   # 3.5 pp superiority over Corrected Ungated SUTA
    target_disparity_effect_pp: float = -2.00 # -2.0 pp reduction in max-min disparity

    # Multiplicity Family & Governance (M = 8)
    alpha_family: float = 0.05
    m_hypotheses: int = 8                    # 2 primary + 5 accent safety guards + 1 disparity guard
    target_joint_power: float = 0.90
    require_lcb_threshold: bool = True

    # Audio & Word-Count Convention
    required_clips_per_speaker: int = 15
    word_count_low: int = 100
    word_count_high: int = 180              # Discrete Uniform[100, 180), matching DesignStagePowerSpec

    # Baseline WER dictionary (defaults to canonical benchmarks)
    baseline_wers: Dict[str, float] = field(default_factory=lambda: dict(CANONICAL_BENCHMARK_BASE_WERS))

    @property
    def adj_alpha(self) -> float:
        """Fixed Single-Step Simultaneous Bonferroni adjusted alpha per hypothesis."""
        return self.alpha_family / float(self.m_hypotheses)

    @property
    def simultaneous_percentile(self) -> float:
        """Simultaneous one-sided confidence percentile for UCBs (e.g. 99.375%)."""
        return 100.0 * (1.0 - self.adj_alpha)

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["adj_alpha"] = self.adj_alpha
        d["simultaneous_percentile"] = self.simultaneous_percentile
        return d


# ------------------------------------------------------------------------------
# Treatment Effect Derivation (Task B)
# ------------------------------------------------------------------------------

def derive_five_stratum_treatment_effects(
    spec: CandidateFiveStratumPowerSpec,
) -> Dict[str, Any]:
    """
    Derives the accent-specific DSG improvement delta_g from the baseline WER values
    strictly across the 5 confirmatory strata (excluding Irish English).

    Mathematical Formulation:
      Let mu_g be the baseline WER for confirmatory accent g.
      mu_bar = mean({mu_g : g in confirmatory_accents})
      mu_min = min({mu_g : g in confirmatory_accents})
      mu_max = max({mu_g : g in confirmatory_accents})
      mu_range = mu_max - mu_min

      delta_g = -target_primary_effect + ((mu_g - mu_bar) / mu_range) * target_disparity_effect

    Properties Guaranteed:
      1. Arithmetic mean of delta_g across the 5 strata equals -target_primary_effect (-3.5 pp).
      2. Population disparity change equals target_disparity_effect (-2.0 pp).
      3. Monotonic ordering of accents is strictly preserved.
      4. Irish English is completely excluded from all baseline statistics.
    """
    accents = list(spec.confirmatory_accents)
    if "Irish English" in accents:
        raise ValueError("Irish English cannot be included in confirmatory baseline calculations.")

    mu_vals = np.array([spec.baseline_wers[a] for a in accents], dtype=float)
    mu_bar = float(np.mean(mu_vals))
    mu_min = float(np.min(mu_vals))
    mu_max = float(np.max(mu_vals))
    mu_range = (mu_max - mu_min) if (mu_max > mu_min) else 1.0

    prim_eff = spec.target_primary_effect_pp / 100.0
    disp_eff = spec.target_disparity_effect_pp / 100.0

    accent_deltas: Dict[str, float] = {}
    accent_dsg_means: Dict[str, float] = {}
    for a_idx, accent in enumerate(accents):
        mu_g = mu_vals[a_idx]
        delta_g = -prim_eff + ((mu_g - mu_bar) / mu_range) * disp_eff
        accent_deltas[accent] = float(delta_g)
        accent_dsg_means[accent] = float(mu_g + delta_g)

    # Theoretical checks
    mean_delta = float(np.mean(list(accent_deltas.values())))
    static_disp = mu_max - mu_min
    dsg_disp = max(accent_dsg_means.values()) - min(accent_dsg_means.values())
    disp_reduction = dsg_disp - static_disp

    return {
        "confirmatory_accents": accents,
        "baseline_mu_vals": {a: spec.baseline_wers[a] for a in accents},
        "mu_bar": mu_bar,
        "mu_min": mu_min,
        "mu_max": mu_max,
        "mu_range": mu_range,
        "accent_deltas": accent_deltas,
        "accent_deltas_pp": {a: d * 100.0 for a, d in accent_deltas.items()},
        "accent_dsg_means": accent_dsg_means,
        "theoretical_mean_delta_pp": mean_delta * 100.0,
        "theoretical_static_disparity_pp": static_disp * 100.0,
        "theoretical_dsg_disparity_pp": dsg_disp * 100.0,
        "theoretical_disparity_reduction_pp": disp_reduction * 100.0,
    }


# ------------------------------------------------------------------------------
# Candidate Dataset Generator (Tasks A, C, D)
# ------------------------------------------------------------------------------

def generate_candidate_dataset(
    spec: CandidateFiveStratumPowerSpec,
    num_speakers_per_stratum: int,
    rng: np.random.Generator,
    accent_effect_mode: str = "fixed",
) -> Dict[str, Any]:
    """
    Generates a single simulated candidate study dataset containing both latent error
    probabilities and observed integer word/error counts.

    Data-Generating Equations:
      For accent g in {1, ..., 5} and speaker i in {1, ..., N_g}:
        1. Static Baseline Error Probability:
           p_{1,gi} = clip(mu_g + a_g + u_{gi}, 0.01, 0.99)
           where:
             u_{gi} ~ N(0, sigma_between_speaker^2)  [sigma_between_speaker = 0.065]
             a_g = 0 in "fixed" mode (primary design scenario)
             a_g ~ N(0, sigma_accent^2) in "random" mode (sensitivity scenario)

        2. DSG-CTTA Error Probability:
           p_{3,gi} = clip(p_{1,gi} + delta_g + epsilon_{3,gi}, 0.01, 0.99)
           where:
             epsilon_{3,gi} ~ N(0, sigma_paired_diff^2)  [sigma_paired_diff = 0.032]
             delta_g = accent-specific treatment effect from derive_five_stratum_treatment_effects()

        3. Corrected Ungated SUTA Error Probability:
           p_{2,gi} = clip(p_{3,gi} + delta_ungated + epsilon_{2,gi}, 0.01, 0.99)
           where:
             delta_ungated = +0.035 (target 3.5 pp higher error rate than DSG)
             epsilon_{2,gi} ~ N(0, sigma_paired_diff^2)  [sigma_paired_diff = 0.032]
             epsilon_{2,gi} and epsilon_{3,gi} are independently sampled.

        4. Word Counts (single draw per speaker, paired across all arms):
           wc_{gi} ~ Uniform_integer[100, 180)

        5. Integer Binomial Error Counts:
           e_{1,gi} ~ Binomial(wc_{gi}, p_{1,gi})
           e_{2,gi} ~ Binomial(wc_{gi}, p_{2,gi})
           e_{3,gi} ~ Binomial(wc_{gi}, p_{3,gi})
    """
    accents = list(spec.confirmatory_accents)
    n_accents = len(accents)
    derived = derive_five_stratum_treatment_effects(spec)
    accent_deltas = derived["accent_deltas"]
    ungated_eff = spec.target_ungated_effect_pp / 100.0

    # Accent random effects (0 for primary fixed scenario)
    if accent_effect_mode == "random":
        accent_effects = {a: float(rng.normal(0, spec.sigma_accent_sensitivity)) for a in accents}
    elif accent_effect_mode == "fixed":
        accent_effects = {a: 0.0 for a in accents}
    else:
        raise ValueError(f"Unknown accent_effect_mode '{accent_effect_mode}'; must be 'fixed' or 'random'.")

    speaker_records: List[Dict[str, Any]] = []
    latent_records: List[Dict[str, Any]] = []

    for a_idx, accent in enumerate(accents):
        base_wer = spec.baseline_wers[accent] + accent_effects[accent]
        delta_g = accent_deltas[accent]
        n_spk = num_speakers_per_stratum

        # Between-speaker variability
        u = rng.normal(0, spec.sigma_between_speaker, size=n_spk)

        # Latent unclipped probability terms
        p1_raw = base_wer + u
        p1 = np.clip(p1_raw, 0.01, 0.99)

        # Arm 3 (DSG) paired noise and probability
        eps3 = rng.normal(0, spec.sigma_paired_diff, size=n_spk)
        p3_raw = p1 + delta_g + eps3
        p3 = np.clip(p3_raw, 0.01, 0.99)

        # Arm 2 (Ungated SUTA) paired noise and probability
        eps2 = rng.normal(0, spec.sigma_paired_diff, size=n_spk)
        p2_raw = p3 + ungated_eff + eps2
        p2 = np.clip(p2_raw, 0.01, 0.99)

        # Integer word counts (single draw per speaker)
        wc = rng.integers(spec.word_count_low, spec.word_count_high, size=n_spk)

        # Integer binomial error counts
        e1 = rng.binomial(wc, p1)
        e2 = rng.binomial(wc, p2)
        e3 = rng.binomial(wc, p3)

        for k in range(n_spk):
            rec = {
                "speaker_idx": len(speaker_records),
                "accent_idx": a_idx,
                "accent": accent,
                "stratum": accent,
                "wc": int(wc[k]),
                "err1": int(e1[k]),
                "err2": int(e2[k]),
                "err3": int(e3[k]),
            }
            speaker_records.append(rec)

            lat_rec = {
                "speaker_idx": rec["speaker_idx"],
                "accent": accent,
                "base_wer": base_wer,
                "delta_g": delta_g,
                "u": float(u[k]),
                "eps3": float(eps3[k]),
                "eps2": float(eps2[k]),
                "p1_raw": float(p1_raw[k]),
                "p1": float(p1[k]),
                "p3_raw": float(p3_raw[k]),
                "p3": float(p3[k]),
                "p2_raw": float(p2_raw[k]),
                "p2": float(p2[k]),
                "diff_31_raw": float(p3_raw[k] - p1[k]),
                "diff_31_clipped": float(p3[k] - p1[k]),
                "diff_32_raw": float(p3[k] - p2_raw[k]),
                "diff_32_clipped": float(p3[k] - p2[k]),
            }
            latent_records.append(lat_rec)

    return {
        "speaker_records": speaker_records,
        "latent_records": latent_records,
        "accent_effects": accent_effects,
        "derived_parameters": derived,
        "num_speakers": len(speaker_records),
        "num_accents": n_accents,
        "accent_effect_mode": accent_effect_mode,
    }


# ------------------------------------------------------------------------------
# Monte Carlo Candidate Power Simulator (v1.5 Candidate)
# ------------------------------------------------------------------------------

def simulate_candidate_five_stratum_power(
    spec: CandidateFiveStratumPowerSpec,
    num_speakers_per_stratum: int = 220,
    n_trials: int = 1000,
    n_bootstraps: int = 2000,
    random_seed: int = 20261030,
    accent_effect_mode: str = "fixed",
) -> Dict[str, Any]:
    """
    Simulates the joint confirmatory power of the composite 8-criterion confirmatory analysis
    for the v1.5 Candidate 5-Stratum Protocol.

    Decision Rules (Fixed Single-Step Simultaneous Bonferroni, M = 8):
      adj_alpha = 0.05 / 8 = 0.00625
      percentile = (1 - adj_alpha) * 100 = 99.375%

      Event A: DSG vs Static baseline (linearized cluster-robust t-UCB < 0.0 pp)
      Event B: DSG vs Ungated SUTA (linearized cluster-robust t-UCB < 0.0 pp)
      Event C: Per-accent regression guard (linearized cluster-robust t-UCB <= +2.0 pp for all 5 strata)
      Event D: Disparity non-increase (stratified cluster bootstrap 99.375th percentile UCB <= 0.0 pp)

      Joint Success = Event A and Event B and Event C and Event D.
    """
    rng = np.random.default_rng(random_seed)
    accents = list(spec.confirmatory_accents)
    n_accents = len(accents)
    m_hypotheses = spec.m_hypotheses
    adj_alpha = spec.adj_alpha
    simultaneous_percentile = spec.simultaneous_percentile

    passed_a = passed_b = passed_c = passed_d = passed_joint = 0

    for trial_idx in range(n_trials):
        trial_seed = random_seed + trial_idx * 31337
        trial_rng = np.random.default_rng(trial_seed)

        data = generate_candidate_dataset(
            spec=spec,
            num_speakers_per_stratum=num_speakers_per_stratum,
            rng=trial_rng,
            accent_effect_mode=accent_effect_mode,
        )
        spk_records = data["speaker_records"]

        # Word-weighted corpus totals
        total_w = float(sum(r["wc"] for r in spk_records))
        total_e1 = float(sum(r["err1"] for r in spk_records))
        total_e2 = float(sum(r["err2"] for r in spk_records))
        total_e3 = float(sum(r["err3"] for r in spk_records))

        delta_static = ((total_e3 - total_e1) / total_w) * 100.0
        delta_ungated = ((total_e3 - total_e2) / total_w) * 100.0

        n_clust = len(spk_records)
        df_corp = max(1, n_clust - 1)
        all_wc = np.array([r["wc"] for r in spk_records], dtype=float)
        all_e1 = np.array([r["err1"] for r in spk_records], dtype=float)
        all_e2 = np.array([r["err2"] for r in spk_records], dtype=float)
        all_e3 = np.array([r["err3"] for r in spk_records], dtype=float)
        w_bar = float(np.mean(all_wc))
        t_crit = float(scipy_stats.t.ppf(1.0 - adj_alpha, df=df_corp))

        # Event A: DSG vs Static
        u_s = (all_e3 - all_e1) - (delta_static / 100.0) * all_wc
        se_s = (100.0 * float(np.std(u_s, ddof=1)) / math.sqrt(n_clust)) / w_bar if w_bar > 0 else 0.0
        event_a = bool(delta_static < 0.0 and (delta_static + t_crit * se_s) < 0.0)

        # Event B: DSG vs Ungated SUTA
        u_u = (all_e3 - all_e2) - (delta_ungated / 100.0) * all_wc
        se_u = (100.0 * float(np.std(u_u, ddof=1)) / math.sqrt(n_clust)) / w_bar if w_bar > 0 else 0.0
        event_b = bool(delta_ungated < 0.0 and (delta_ungated + t_crit * se_u) < 0.0)

        # Event C: Per-accent regression guard (<= +2.0 pp across all 5 strata)
        epsilon_g = 2.0
        accent_passes = True
        for a_idx in range(n_accents):
            acc_r = [r for r in spk_records if r["accent_idx"] == a_idx]
            n_g = len(acc_r)
            df_g = max(1, n_g - 1)
            t_g = float(scipy_stats.t.ppf(1.0 - adj_alpha, df=df_g))
            gw = np.array([r["wc"] for r in acc_r], dtype=float)
            ge1 = np.array([r["err1"] for r in acc_r], dtype=float)
            ge3 = np.array([r["err3"] for r in acc_r], dtype=float)
            d_g = ((float(np.sum(ge3)) - float(np.sum(ge1))) / float(np.sum(gw))) * 100.0
            u_g = (ge3 - ge1) - (d_g / 100.0) * gw
            wb_g = float(np.mean(gw))
            se_g = (100.0 * float(np.std(u_g, ddof=1)) / math.sqrt(n_g)) / wb_g if wb_g > 0 else 0.0
            if (d_g + t_g * se_g) > epsilon_g:
                accent_passes = False
                break
        event_c = accent_passes

        # Event D: Disparity non-increase via stratified paired bootstrap (99.375% UCB <= 0.0 pp)
        acc_wc_arr = {}
        acc_e1_arr = {}
        acc_e3_arr = {}
        for a_idx in range(n_accents):
            acc_r = [r for r in spk_records if r["accent_idx"] == a_idx]
            acc_wc_arr[a_idx] = np.array([r["wc"] for r in acc_r], dtype=float)
            acc_e1_arr[a_idx] = np.array([r["err1"] for r in acc_r], dtype=float)
            acc_e3_arr[a_idx] = np.array([r["err3"] for r in acc_r], dtype=float)

        boot_delta_ds = np.zeros(n_bootstraps, dtype=float)
        for b in range(n_bootstraps):
            bw1 = np.zeros(n_accents)
            bw3 = np.zeros(n_accents)
            for a_idx in range(n_accents):
                wc_a = acc_wc_arr[a_idx]
                n_a = len(wc_a)
                bi = trial_rng.integers(0, n_a, size=n_a)
                bw = float(np.sum(wc_a[bi]))
                if bw > 0:
                    bw1[a_idx] = (float(np.sum(acc_e1_arr[a_idx][bi])) / bw) * 100.0
                    bw3[a_idx] = (float(np.sum(acc_e3_arr[a_idx][bi])) / bw) * 100.0
            boot_delta_ds[b] = (np.max(bw3) - np.min(bw3)) - (np.max(bw1) - np.min(bw1))

        event_d = bool(float(np.percentile(boot_delta_ds, simultaneous_percentile)) <= 0.0)

        if event_a: passed_a += 1
        if event_b: passed_b += 1
        if event_c: passed_c += 1
        if event_d: passed_d += 1
        if event_a and event_b and event_c and event_d:
            passed_joint += 1

    p_a = passed_a / n_trials
    p_b = passed_b / n_trials
    p_c = passed_c / n_trials
    p_d = passed_d / n_trials
    jp = passed_joint / n_trials
    k, n = passed_joint, n_trials
    ci_low = float(scipy_stats.beta.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0
    ci_high = float(scipy_stats.beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0

    return {
        "simulation_parameters": {
            "model_version": "v1.5.0-Candidate",
            "evaluated_accents": accents,
            "evaluated_accents_count": n_accents,
            "speakers_per_stratum": num_speakers_per_stratum,
            "total_speakers": n_accents * num_speakers_per_stratum,
            "n_trials": n_trials,
            "n_bootstraps_per_trial": n_bootstraps,
            "m_simultaneous_hypotheses": m_hypotheses,
            "alpha_family": spec.alpha_family,
            "adj_alpha_per_hypothesis": adj_alpha,
            "simultaneous_ucb_percentile": simultaneous_percentile,
            "accent_effect_mode": accent_effect_mode,
            "sigma_between_speaker": spec.sigma_between_speaker,
            "sigma_paired_diff": spec.sigma_paired_diff,
            "sigma_accent_sensitivity": spec.sigma_accent_sensitivity,
        },
        "power_results": {
            "event_a_static_superiority_power": p_a,
            "event_b_suta_superiority_power": p_b,
            "event_c_accent_regression_guard_power": p_c,
            "event_d_disparity_guard_power": p_d,
            "joint_confirmatory_power": jp,
            "joint_power_95_ci": [round(ci_low, 4), round(ci_high, 4)],
            "target_90_power_achieved": bool(jp >= spec.target_joint_power),
            "lcb_90_power_achieved": bool(ci_low >= spec.target_joint_power),
        },
    }
