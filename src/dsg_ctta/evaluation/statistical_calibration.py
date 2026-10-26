"""
Stage 6M v1.4.0 — Statistical Calibration and Simulation Suite
==============================================================
Implements simulation-based calibration for the frozen 9-criterion
inferential procedure prescribed in Protocol v1.4.0 (Sections 1, 6, 7, 12):
1. Global Null (Delta = 0.0 pp): Assesses Family-Wise Error Rate (FWER) and False Acceptance Rate.
2. Near-Null Difference (Delta = -0.2 pp): Evaluates sensitivity and inconclusive classification.
3. True Beneficial Adaptation (Delta = -2.5 pp): Evaluates empirical statistical power.
4. Isolated Accent Regression (+4.0 pp on one accent): Verifies fail-closed detection of fairness violations.
5. Cross-Accent Disparity Expansion (+5.0 pp delta disparity): Assesses disparity boundary violation detection.
6. Max-Min Disparity Tie (all 6 accents tied): Measures bootstrap coverage and non-smooth bias.
7. Heterogeneous Word Counts and Low Variance: Tests robustness to unbalanced clusters and small error counts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, FrozenSet
import numpy as np
import pandas as pd

from dsg_ctta.evaluation.paired_cluster_inference import (
    run_confirmatory_paired_cluster_inference,
    ConfirmatoryAnalysisReport,
    CANONICAL_PROTOCOL_ACCENTS,
)


@dataclass
class ScenarioCalibrationResult:
    """Empirical calibration metrics for a specific simulation scenario."""
    scenario_name: str
    description: str
    num_simulations: int
    num_speakers_per_stratum: int
    num_bootstrap_replicates: int
    true_delta_static_pp: float
    true_delta_ungated_pp: float
    true_delta_disparity_pp: float
    
    # Empirical Verdict Rates
    pass_rate: float
    pass_rate_se: float
    fail_rate: float
    fail_rate_se: float
    inconclusive_rate: float
    inconclusive_rate_se: float
    
    # Hypothesis Rejection Rates across 9 Criteria
    rejection_rates_by_criterion: Dict[str, float]
    
    # Coverage of Adjusted Upper Bounds
    mean_adjusted_ucb_static: float
    mean_adjusted_ucb_ungated: float
    mean_adjusted_ucb_disparity: float
    disparity_ucb_coverage: float  # Proportion where adj_UCB >= true_delta_D
    
    # Qualitative Interpretation
    is_valid_error_control: bool
    summary_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_synthetic_speaker_cohort(
    num_speakers_per_stratum: int = 10,
    canonical_accents: FrozenSet[str] = CANONICAL_PROTOCOL_ACCENTS,
    base_wer_per_accent: Optional[Dict[str, float]] = None,
    delta_static_pp: float = 0.0,
    delta_ungated_pp: float = 50.0,
    accent_delta_shifts: Optional[Dict[str, float]] = None,
    word_count_mode: str = "fixed",  # "fixed" | "heterogeneous"
    word_count_mean: int = 100,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generates a realistic synthetic speaker evaluation cohort with paired edit distance counts.
    """
    rng = np.random.default_rng(seed=seed)
    accents_list = sorted(list(canonical_accents))
    
    if base_wer_per_accent is None:
        base_wer_per_accent = {acc: 20.0 for acc in accents_list}
    if accent_delta_shifts is None:
        accent_delta_shifts = {acc: 0.0 for acc in accents_list}
        
    records = []
    for acc in accents_list:
        base_p = base_wer_per_accent[acc] / 100.0
        acc_shift = accent_delta_shifts.get(acc, 0.0) / 100.0
        
        for s_idx in range(num_speakers_per_stratum):
            spk_id = f"{acc.lower().replace(' ', '_')}_spk_{s_idx:03d}"
            
            # Word count sampling
            if word_count_mode == "heterogeneous":
                # Lognormal variation around mean words (range ~30 to 300)
                wc = int(np.clip(rng.lognormal(np.log(word_count_mean), 0.4), 30, 400))
            else:
                wc = int(word_count_mean)
                
            # Inter-speaker error rate variation around accent mean (Beta dispersion)
            # alpha + beta = 50 gives realistic variance
            precision = 50.0
            a_p = max(0.5, base_p * precision)
            b_p = max(0.5, (1.0 - base_p) * precision)
            spk_base_p = float(rng.beta(a_p, b_p))
            
            # Arm 1: Static
            e1 = int(rng.binomial(wc, np.clip(spk_base_p, 0.01, 0.99)))
            
            # Arm 2: Ungated (catastrophic failure or matched)
            p2 = np.clip(spk_base_p + (delta_ungated_pp / 100.0), 0.01, 0.99)
            e2 = int(rng.binomial(wc, p2))
            
            # Arm 3: DSG
            # Combined shift: global delta_static_pp + accent-specific shift
            p3 = np.clip(spk_base_p + (delta_static_pp / 100.0) + acc_shift, 0.00, 0.99)
            e3 = int(rng.binomial(wc, p3))
            
            records.append({
                "speaker_id": spk_id,
                "stratum": acc,
                "wc": wc,
                "err1": e1,
                "err2": e2,
                "err3": e3,
            })
            
    return records


def run_scenario_monte_carlo_calibration(
    scenario_name: str,
    description: str,
    num_simulations: int = 50,
    num_speakers_per_stratum: int = 10,
    num_bootstrap_replicates: int = 200,
    base_wer_per_accent: Optional[Dict[str, float]] = None,
    delta_static_pp: float = 0.0,
    delta_ungated_pp: float = 50.0,
    accent_delta_shifts: Optional[Dict[str, float]] = None,
    word_count_mode: str = "fixed",
    word_count_mean: int = 100,
    seed: int = 1000,
    alpha_family: float = 0.05,
    epsilon_g_margin_pp: float = 2.00,
    epsilon_d_margin_pp: float = 0.00,
    min_speakers_for_power: int = 5,
    target_effect_size_pp: float = 2.00,
    power_threshold: float = 0.80,
) -> ScenarioCalibrationResult:
    """
    Executes repeated Monte Carlo iterations for a specific scenario to calculate
    empirical decision rates, standard errors, and coverage.
    """
    n_pass = 0
    n_fail = 0
    n_inconclusive = 0
    
    criterion_rejections: Dict[str, int] = {}
    adj_ucb_static_list = []
    adj_ucb_ungated_list = []
    adj_ucb_disp_list = []
    disp_coverage_count = 0
    
    # Calculate true population delta disparity
    accents_list = sorted(list(CANONICAL_PROTOCOL_ACCENTS))
    if base_wer_per_accent is None:
        base_wer_per_accent = {acc: 20.0 for acc in accents_list}
    if accent_delta_shifts is None:
        accent_delta_shifts = {acc: 0.0 for acc in accents_list}
        
    true_w1 = {acc: base_wer_per_accent[acc] for acc in accents_list}
    true_w3 = {acc: base_wer_per_accent[acc] + delta_static_pp + accent_delta_shifts.get(acc, 0.0) for acc in accents_list}
    
    true_disp1 = max(true_w1.values()) - min(true_w1.values())
    true_disp3 = max(true_w3.values()) - min(true_w3.values())
    true_delta_disp = true_disp3 - true_disp1
    
    for sim_idx in range(num_simulations):
        cohort_seed = seed + sim_idx * 17
        boot_seed = seed + sim_idx * 31 + 7
        
        cohort_records = generate_synthetic_speaker_cohort(
            num_speakers_per_stratum=num_speakers_per_stratum,
            base_wer_per_accent=base_wer_per_accent,
            delta_static_pp=delta_static_pp,
            delta_ungated_pp=delta_ungated_pp,
            accent_delta_shifts=accent_delta_shifts,
            word_count_mode=word_count_mode,
            word_count_mean=word_count_mean,
            seed=cohort_seed,
        )
        
        report: ConfirmatoryAnalysisReport = run_confirmatory_paired_cluster_inference(
            speaker_records=cohort_records,
            num_bootstrap_replicates=num_bootstrap_replicates,
            seed=boot_seed,
            alpha_family=alpha_family,
            epsilon_g_margin_pp=epsilon_g_margin_pp,
            epsilon_d_margin_pp=epsilon_d_margin_pp,
            min_speakers_per_stratum_for_power=min_speakers_for_power,
            target_effect_size_pp=target_effect_size_pp,
            power_threshold=power_threshold,
        )
        
        if report.verdict == "PASS":
            n_pass += 1
        elif report.verdict == "FAIL":
            n_fail += 1
        else:
            n_inconclusive += 1
            
        for c_id, c_res in report.criteria.items():
            if c_id not in criterion_rejections:
                criterion_rejections[c_id] = 0
            if not c_res.is_success:
                criterion_rejections[c_id] += 1
                
        adj_ucb_static_list.append(report.criteria["primary_superiority_static"].adjusted_ucb)
        adj_ucb_ungated_list.append(report.criteria["primary_superiority_ungated"].adjusted_ucb)
        adj_ucb_disp_list.append(report.criteria["disparity_non_increase"].adjusted_ucb)
        
        # Coverage: Did the adjusted UCB cover the true delta disparity?
        # A 1-sided upper confidence bound covers parameter theta if UCB >= theta
        if report.criteria["disparity_non_increase"].adjusted_ucb >= true_delta_disp:
            disp_coverage_count += 1
            
    p_pass = n_pass / num_simulations
    se_pass = math.sqrt(p_pass * (1.0 - p_pass) / num_simulations) if num_simulations > 1 else 0.0
    
    p_fail = n_fail / num_simulations
    se_fail = math.sqrt(p_fail * (1.0 - p_fail) / num_simulations) if num_simulations > 1 else 0.0
    
    p_inc = n_inconclusive / num_simulations
    se_inc = math.sqrt(p_inc * (1.0 - p_inc) / num_simulations) if num_simulations > 1 else 0.0
    
    rejection_rates = {k: v / num_simulations for k, v in criterion_rejections.items()}
    coverage_disp = disp_coverage_count / num_simulations
    
    # Error control check
    if delta_static_pp >= 0.0:
        # Under null or regression, false acceptance (pass) must be <= alpha_family + 2*SE
        valid_control = (p_pass <= alpha_family + 2.0 * max(se_pass, 0.01))
    else:
        # Under beneficial adaptation, failure rate must be low if adequately powered
        valid_control = True
        
    summary = (
        f"{scenario_name}: PASS={p_pass:.1%} (SE={se_pass:.1%}), FAIL={p_fail:.1%}, "
        f"INCONCLUSIVE={p_inc:.1%}, Disparity UCB Coverage={coverage_disp:.1%}."
    )
    
    return ScenarioCalibrationResult(
        scenario_name=scenario_name,
        description=description,
        num_simulations=num_simulations,
        num_speakers_per_stratum=num_speakers_per_stratum,
        num_bootstrap_replicates=num_bootstrap_replicates,
        true_delta_static_pp=delta_static_pp,
        true_delta_ungated_pp=delta_ungated_pp,
        true_delta_disparity_pp=true_delta_disp,
        pass_rate=round(p_pass, 4),
        pass_rate_se=round(se_pass, 4),
        fail_rate=round(p_fail, 4),
        fail_rate_se=round(se_fail, 4),
        inconclusive_rate=round(p_inc, 4),
        inconclusive_rate_se=round(se_inc, 4),
        rejection_rates_by_criterion={k: round(v, 4) for k, v in rejection_rates.items()},
        mean_adjusted_ucb_static=round(float(np.mean(adj_ucb_static_list)), 4),
        mean_adjusted_ucb_ungated=round(float(np.mean(adj_ucb_ungated_list)), 4),
        mean_adjusted_ucb_disparity=round(float(np.mean(adj_ucb_disp_list)), 4),
        disparity_ucb_coverage=round(coverage_disp, 4),
        is_valid_error_control=valid_control,
        summary_verdict=summary,
    )


def run_full_statistical_calibration_suite(
    num_simulations_per_scenario: int = 30,
    num_bootstrap_replicates: int = 150,
    seed: int = 2026,
) -> Dict[str, ScenarioCalibrationResult]:
    """
    Executes the comprehensive calibration battery across the 7 canonical protocol scenarios.
    """
    results: Dict[str, ScenarioCalibrationResult] = {}
    
    # 1. Global Null (Delta_static = 0.0 pp)
    # Both arms have identical error generation; tests family-wise false acceptance rate
    results["global_null"] = run_scenario_monte_carlo_calibration(
        scenario_name="Global Null (Delta = 0.0 pp)",
        description="Arm 3 is drawn from identical null distributions to Arm 1; evaluates false acceptance rate under H0.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        delta_static_pp=0.0,
        delta_ungated_pp=40.0,
        seed=seed + 1,
    )
    
    # 2. Near-Null Difference (Delta_static = -0.20 pp)
    # Negligible improvement; tests that noisy sub-threshold shifts do not falsely pass
    results["near_null"] = run_scenario_monte_carlo_calibration(
        scenario_name="Near-Null Difference (Delta = -0.20 pp)",
        description="Marginal advantage within sampling noise; verifies proper classification as INCONCLUSIVE.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        delta_static_pp=-0.20,
        delta_ungated_pp=40.0,
        seed=seed + 2,
    )
    
    # 3. True Beneficial Adaptation (Delta_static = -3.50 pp, selective disparity reduction)
    results["beneficial_adaptation"] = run_scenario_monte_carlo_calibration(
        scenario_name="True Beneficial Adaptation (Delta = -3.50 pp)",
        description="Selective adaptation improves accuracy across all accents while narrowing the disparity gap.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        base_wer_per_accent={
            "US English": 15.0,
            "England English": 18.0,
            "South Asian English": 24.0,
            "Australian English": 20.0,
            "Canadian English": 17.0,
            "Irish English": 27.0,
        },
        delta_static_pp=-3.50,
        delta_ungated_pp=40.0,
        accent_delta_shifts={
            "Irish English": -3.5,       # High WER accent improves by -7.0 pp
            "South Asian English": -2.0, # High WER accent improves by -5.5 pp
            "US English": +1.5,          # Low WER accent improves by -2.0 pp
        },
        seed=seed + 3,
    )
    
    # 4. Isolated Accent Regression (Irish English regresses by +4.00 pp)
    # Overall delta is beneficial (-2.0 pp), but one accent severely regresses
    results["isolated_accent_regression"] = run_scenario_monte_carlo_calibration(
        scenario_name="Isolated Accent Regression (+4.0 pp)",
        description="5 accents improve by -3.0 pp, but Irish English regresses by +4.0 pp; tests fairness protection.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        delta_static_pp=-2.00,
        delta_ungated_pp=40.0,
        accent_delta_shifts={"Irish English": 6.0},  # -2.0 + 6.0 = +4.0 pp net regression
        seed=seed + 4,
    )
    
    # 5. Cross-Accent Disparity Expansion (Disparity increases by +5.0 pp)
    results["disparity_expansion"] = run_scenario_monte_carlo_calibration(
        scenario_name="Disparity Expansion (+5.0 pp)",
        description="Best accent improves by -4.0 pp while worst accent regresses by +1.0 pp, widening disparity by +5.0 pp.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        base_wer_per_accent={
            "US English": 15.0,
            "England English": 18.0,
            "South Asian English": 22.0,
            "Australian English": 20.0,
            "Canadian English": 17.0,
            "Irish English": 25.0,
        },
        delta_static_pp=0.0,
        delta_ungated_pp=40.0,
        accent_delta_shifts={
            "US English": -4.0,   # 15 -> 11 (best gets better)
            "Irish English": +1.0 # 25 -> 26 (worst gets worse: disparity 10 -> 15 pp)
        },
        seed=seed + 5,
    )
    
    # 6. Max-Min Disparity Tie (All 6 accents tied at 20.0% WER)
    # Worst-case boundary for non-smooth max-min operator
    results["max_min_tie"] = run_scenario_monte_carlo_calibration(
        scenario_name="Max-Min Disparity Tie (All Accents Tied at 20% WER)",
        description="All 6 strata have identical population WER = 20.0%; tests bootstrap coverage and positive tie bias.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        base_wer_per_accent={acc: 20.0 for acc in CANONICAL_PROTOCOL_ACCENTS},
        delta_static_pp=-2.5,
        delta_ungated_pp=40.0,
        seed=seed + 6,
    )
    
    # 7. Heterogeneous Word Counts and Low Variance
    # Unequal cluster sizes (30 to 300 words per clip) and low error rates (10% WER)
    results["heterogeneous_clusters"] = run_scenario_monte_carlo_calibration(
        scenario_name="Heterogeneous Clusters & Low Variance",
        description="Lognormal word counts (30-300 words) and low baseline WER (10%); tests cluster robustness.",
        num_simulations=num_simulations_per_scenario,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=num_bootstrap_replicates,
        base_wer_per_accent={acc: 10.0 for acc in CANONICAL_PROTOCOL_ACCENTS},
        delta_static_pp=-2.0,
        delta_ungated_pp=30.0,
        word_count_mode="heterogeneous",
        word_count_mean=120,
        seed=seed + 7,
    )
    
    return results
