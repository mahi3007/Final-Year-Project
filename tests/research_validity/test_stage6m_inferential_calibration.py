"""
Stage 6M Test Suite: Confirmatory Inferential Calibration Battery
=================================================================
Validates ADR-005 and Protocol v1.4.0 requirements for simulation-based
calibration of the frozen 9-criterion paired cluster inference procedure:
1. Global Null (Delta = 0.0 pp): Family-Wise Error Rate (FWER) control <= 0.05.
2. True Beneficial Adaptation (Delta = -3.0 pp): Demonstrates high empirical power.
3. Isolated Accent Regression (+4.0 pp net on Irish English): Strict 0% pass rate.
4. Cross-Accent Disparity Expansion (+5.0 pp delta disparity): Strict 0% pass rate.
5. Disparity Max-Min Tie (tied accent WERs): Valid bootstrap UCB coverage >= 0.90.
6. Heterogeneous Word Counts: Robust numerical stability under unbalanced clusters.
"""

import math
import pytest
import numpy as np

from dsg_ctta.evaluation.statistical_calibration import (
    run_scenario_monte_carlo_calibration,
    generate_synthetic_speaker_cohort,
    simulate_streaming_gate_trajectory_calibration,
    compute_clopper_pearson_interval,
    CANONICAL_PROTOCOL_ACCENTS,
)


def test_calibration_global_null_family_wise_error_control():
    """
    Test Case 1: Global Null (Delta = 0.0 pp).
    Verifies that when Arm 3 has no true advantage over Arm 1, the empirical
    false acceptance rate across the 9-criterion composite decision is <= alpha (0.05).
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Global Null",
        description="Assesses false acceptance rate under null difference",
        num_simulations=25,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=150,
        delta_static_pp=0.0,
        delta_ungated_pp=0.0,
        seed=101,
    )

    # Under global null, false acceptance rate must be strictly controlled (<= 0.05)
    assert res.pass_rate <= 0.05, f"False acceptance rate under null ({res.pass_rate:.1%}) exceeded alpha target 5%"
    assert res.is_valid_error_control
    # The vast majority of runs under null must be classified as INCONCLUSIVE or FAIL
    assert (res.inconclusive_rate + res.fail_rate) >= 0.95


def test_calibration_beneficial_adaptation_empirical_power():
    """
    Test Case 2: True Beneficial Adaptation (Delta = -4.0 pp, selective disparity reduction).
    Verifies that when Arm 3 has a genuine advantage across accents and narrows the disparity gap,
    and the cohort size is adequate (N=60/stratum), the empirical detection power is high (>= 80%).
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Beneficial Adaptation",
        description="Assesses power under true 4.0 pp WER reduction with disparity reduction",
        num_simulations=15,
        num_speakers_per_stratum=60,
        num_bootstrap_replicates=150,
        base_wer_per_accent={
            "US English": 15.0,
            "England English": 18.0,
            "South Asian English": 24.0,
            "Australian English": 20.0,
            "Canadian English": 17.0,
            "Irish English": 27.0,
        },
        delta_static_pp=-4.00,
        delta_ungated_pp=-1.0,
        accent_delta_shifts={
            "Irish English": -4.0,       # High WER accent improves by -8.0 pp
            "South Asian English": -3.0, # High WER accent improves by -7.0 pp
            "US English": +2.0,          # Low WER accent improves by -2.0 pp
        },
        seed=202,
        target_effect_size_pp=4.00,
        power_threshold=0.70,
        min_speakers_for_power=60,
    )

    # High empirical power to detect genuine improvement with disparity reduction
    assert res.pass_rate >= 0.80, f"Empirical power ({res.pass_rate:.1%}) was below target 80%"
    assert res.fail_rate == 0.0, "Zero runs should fail under true beneficial adaptation"


def test_calibration_isolated_accent_regression_detection():
    """
    Test Case 3: Isolated Accent Regression (Irish English regresses by +4.0 pp).
    Verifies that when 5 accents improve by -2.0 pp but 1 accent regresses by +4.0 pp,
    the composite procedure NEVER passes (0% false pass rate) and reliably flags the violation.
    Demonstrable harm is classified as FAIL, while imprecise bounds without demonstrable harm
    are classified as INCONCLUSIVE.
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Isolated Accent Regression",
        description="Assesses fairness protection under single accent regression",
        num_simulations=20,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=150,
        delta_static_pp=-2.0,
        delta_ungated_pp=-1.0,
        accent_delta_shifts={"Irish English": 6.0},  # Net +4.0 pp regression
        seed=303,
    )

    # Absolute safety guarantee: Composite procedure must NEVER pass
    assert res.pass_rate == 0.0, f"Pass rate must be 0% on accent regression, got {res.pass_rate}"
    assert (res.fail_rate + res.inconclusive_rate) == 1.0
    # The specific criterion for Irish English must reject in 100% of runs
    assert res.rejection_rates_by_criterion.get("accent_safety_irish_english", 0.0) == 1.0


def test_calibration_disparity_expansion_detection():
    """
    Test Case 4: Cross-Accent Disparity Expansion (+5.0 pp increase).
    Verifies that when cross-accent disparity expands from 10 pp to 15 pp,
    the composite procedure NEVER passes (0% false pass rate) and rejects the disparity criterion.
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Disparity Expansion",
        description="Assesses disparity non-increase enforcement",
        num_simulations=20,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=150,
        base_wer_per_accent={
            "US English": 15.0,
            "England English": 18.0,
            "South Asian English": 22.0,
            "Australian English": 20.0,
            "Canadian English": 17.0,
            "Irish English": 25.0,
        },
        delta_static_pp=0.0,
        delta_ungated_pp=0.0,
        accent_delta_shifts={
            "US English": -4.0,   # Best gets better: 11%
            "Irish English": +1.0 # Worst gets worse: 26% -> disparity delta = +5.0 pp
        },
        seed=404,
    )

    assert res.pass_rate == 0.0, f"Pass rate must be 0% on disparity expansion, got {res.pass_rate}"
    assert (res.fail_rate + res.inconclusive_rate) == 1.0
    assert res.rejection_rates_by_criterion.get("disparity_non_increase", 0.0) == 1.0


def test_calibration_max_min_tie_disparity_ucb_coverage():
    """
    Test Case 5: Max-Min Disparity Tie (All 6 accents tied at 20.0% WER).
    Assesses the non-smooth max-min bootstrap upper confidence bound at the tie boundary.
    Verifies that empirical coverage of the adjusted UCB for Delta_D is >= 90%.
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Max-Min Tie",
        description="Assesses bootstrap UCB coverage under tied accents",
        num_simulations=45,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=150,
        base_wer_per_accent={acc: 20.0 for acc in CANONICAL_PROTOCOL_ACCENTS},
        delta_static_pp=-2.0,
        delta_ungated_pp=-1.0,
        seed=505,
    )

    # 1-sided coverage of adjusted UCB: proportion where adj_UCB >= true_delta_D (0.0 pp)
    assert res.disparity_ucb_coverage >= 0.90, (
        f"Disparity UCB coverage at max-min tie ({res.disparity_ucb_coverage:.1%}) was below target 90%"
    )
    # Clopper-Pearson 95% lower bound must demonstrate true coverage >= 90%
    assert res.disparity_ucb_coverage_ci_lower >= 0.90, (
        f"Disparity UCB coverage lower 95% CI bound ({res.disparity_ucb_coverage_ci_lower:.1%}) below 90%"
    )


def test_calibration_heterogeneous_word_counts_numerical_robustness():
    """
    Test Case 6: Heterogeneous Word Counts & Low Baseline WER.
    Verifies that unbalanced clusters (30 to 400 words) and low error counts
    produce finite, valid metrics without numerical overflow or NaN.
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Heterogeneous Clusters",
        description="Assesses numerical stability on unbalanced clusters",
        num_simulations=15,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=150,
        base_wer_per_accent={acc: 8.0 for acc in CANONICAL_PROTOCOL_ACCENTS},
        delta_static_pp=-1.5,
        delta_ungated_pp=-0.5,
        word_count_mode="heterogeneous",
        word_count_mean=120,
        seed=606,
    )

    assert math.isfinite(res.mean_adjusted_ucb_static)
    assert math.isfinite(res.mean_adjusted_ucb_ungated)
    assert math.isfinite(res.mean_adjusted_ucb_disparity)
    assert res.is_valid_error_control


def test_calibration_near_null_differences():
    """
    Test Case 7: Near-Null Difference (Delta = -0.20 pp).
    Verifies that a marginal, sub-threshold difference within noise is properly
    classified as INCONCLUSIVE with 0% false pass rate, demonstrating sensitivity.
    """
    res = run_scenario_monte_carlo_calibration(
        scenario_name="Calibration: Near-Null Difference",
        description="Assesses behavior under sub-threshold shifts",
        num_simulations=20,
        num_speakers_per_stratum=10,
        num_bootstrap_replicates=150,
        delta_static_pp=-0.20,
        delta_ungated_pp=-0.20,
        seed=707,
    )

    # Must not falsely pass (0% pass rate)
    assert res.pass_rate == 0.0, f"Pass rate must be 0% for near-null, got {res.pass_rate}"
    assert res.inconclusive_rate >= 0.80, f"Expected predominantly INCONCLUSIVE, got {res.inconclusive_rate}"
    assert res.is_valid_error_control


def test_streaming_gate_trajectory_full_sequential_null_control():
    """
    Test Case 8A: Full Consecutive 1,754-Look Sequential Gate Null Trajectory Control (75 Trajectories).
    Evaluates all 1,754 consecutive update opportunities across full streaming adaptation trajectories
    with 120 reference speakers (20 per stratum) and independent reference panel resampling per trajectory replicate.
    Verifies that zero false acceptances occur across all 1,754 consecutive evaluation windows and that the
    exact Clopper-Pearson 95% upper confidence bound strictly satisfies <= 5.0%.
    """
    res = simulate_streaming_gate_trajectory_calibration(
        trajectory_type="null",
        num_trajectories=75,
        num_candidate_looks=1754,
        num_reference_speakers=120,
        seed=808,
        num_planned_updates=1754,
    )

    assert res.is_full_sequential_evaluation
    assert res.num_candidate_looks == 1754
    assert res.num_trajectories == 75
    assert res.num_reference_speakers == 120
    assert res.trajectory_false_acceptance_rate == 0.0
    assert res.trajectory_false_acceptance_ci_upper <= 0.05
    assert res.candidate_rejection_rate == 1.0
    assert res.is_safely_controlled


def test_streaming_gate_trajectory_null_control():
    """
    Test Case 8B: Repeated-Candidate Streaming Gate Null Trajectory Screening (75 Trajectories).
    Simulates sequential candidate evaluations across the production 1,754-look OBF schedule
    with independent reference panel resampling per trajectory replicate. Verifies that the
    trajectory-level false acceptance rate has an exact Clopper-Pearson 95% upper confidence limit <= 5.0%.
    """
    res = simulate_streaming_gate_trajectory_calibration(
        trajectory_type="null",
        num_trajectories=75,
        num_candidate_looks=10,
        num_reference_speakers=120,
        seed=808,
        num_planned_updates=1754,
    )

    assert res.trajectory_false_acceptance_rate == 0.0
    assert res.trajectory_false_acceptance_ci_upper <= 0.05
    assert res.is_safely_controlled
    assert res.candidate_rejection_rate == 1.0


def test_streaming_gate_trajectory_harm_rejection():
    """
    Test Case 9: Full Consecutive 1,754-Look Streaming Gate Harmful Trajectory Rejection (75 Trajectories).
    Simulates candidates introducing isolated regression or disparity expansion
    under the full consecutive 1,754-look schedule with 120 reference speakers and independent panel resampling.
    Verifies that false acceptance rate is 0.0% with Clopper-Pearson upper bound <= 5.0% across 75 trajectories.
    """
    res_regress = simulate_streaming_gate_trajectory_calibration(
        trajectory_type="harmful_accent",
        num_trajectories=75,
        num_candidate_looks=1754,
        num_reference_speakers=120,
        seed=909,
        num_planned_updates=1754,
    )
    assert res_regress.is_full_sequential_evaluation
    assert res_regress.num_candidate_looks == 1754
    assert res_regress.trajectory_false_acceptance_rate == 0.0
    assert res_regress.trajectory_false_acceptance_ci_upper <= 0.05
    assert res_regress.candidate_rejection_rate == 1.0
    assert res_regress.is_safely_controlled

    res_disp = simulate_streaming_gate_trajectory_calibration(
        trajectory_type="disparity_expansion",
        num_trajectories=75,
        num_candidate_looks=1754,
        num_reference_speakers=120,
        seed=910,
        num_planned_updates=1754,
    )
    assert res_disp.is_full_sequential_evaluation
    assert res_disp.num_candidate_looks == 1754
    assert res_disp.trajectory_false_acceptance_rate == 0.0
    assert res_disp.trajectory_false_acceptance_ci_upper <= 0.05
    assert res_disp.candidate_rejection_rate == 1.0
    assert res_disp.is_safely_controlled


def test_streaming_gate_trajectory_production_length_beneficial_control():
    """
    Test Case 10: Full Consecutive 1,754-Look Streaming Gate Beneficial Trajectory Acceptance.
    Verifies that under the full consecutive 1,754-look schedule with 120 reference speakers,
    genuine multi-accent improvements are accepted by the sequential gate with positive mean update rate,
    while zero interleaved harmful perturbations are falsely accepted.
    """
    res = simulate_streaming_gate_trajectory_calibration(
        trajectory_type="beneficial",
        num_trajectories=15,
        num_candidate_looks=1754,
        num_reference_speakers=120,
        seed=911,
        num_planned_updates=1754,
    )
    assert res.is_full_sequential_evaluation
    assert res.num_candidate_looks == 1754
    assert res.accepted_updates_mean > 0.0
    assert res.adaptation_uptake_demonstrated is True
    assert res.is_safely_controlled is True
    assert res.trajectory_false_acceptance_rate == 0.0
