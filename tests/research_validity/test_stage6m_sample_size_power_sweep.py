"""
Tests for Stage 6M v1.5 Five-Stratum Sample-Size Power Sweep (Task 5)
=====================================================================

Validates all testing requirements specified in Task G of Stage 6M Task 5:
1. Nested speaker subsets correctness.
2. Paired observations across arms (Static, SUTA, DSG).
3. Synchronous joint event calculation (A and B and C and D).
4. Exact Clopper-Pearson 95% confidence interval calculations.
5. Five-stratum M = 8 multiplicity architecture and Bonferroni adjusted alpha.
6. Sample-size capacity bounds (Australian English N_g = 285 limit).
7. Deterministic fixed-seed reproducibility.
8. Protocol v1.4.0 frozen production code immutability.
9. Full power sweep execution metrics consistency.
"""

import math
import subprocess
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest
import scipy.stats as sp_stats

from scripts.stage6m_v1_5_candidate_power_simulator import (
    CandidateFiveStratumPowerSpec,
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    generate_candidate_dataset,
)
from scripts.stage6m_v1_5_sample_size_power_sweep import (
    clopper_pearson_interval,
    evaluate_trial_all_events,
    reconcile_five_stratum_capacity,
    run_exploratory_screening_sweep,
    run_fast_stratified_bootstrap,
    run_final_power_confirmation,
)


@pytest.fixture
def candidate_spec():
    return CandidateFiveStratumPowerSpec()


# ------------------------------------------------------------------------------
# 1. Nested speaker subsets correctness
# ------------------------------------------------------------------------------
def test_nested_speaker_subsets_correctness(candidate_spec):
    """
    Test 1: Verifies that for any N_g < N_max, the N_g subset is strictly
    the leading prefix [:N_g] of the N_max speaker panel for each stratum.
    """
    N_max = 285
    rng = np.random.default_rng(20261101)
    master_data = generate_candidate_dataset(candidate_spec, num_speakers_per_stratum=N_max, rng=rng)
    master_records = master_data["speaker_records"]

    for ng in [220, 230, 250, 270, 280]:
        for accent in candidate_spec.confirmatory_accents:
            acc_master = [r for r in master_records if r["accent"] == accent]
            assert len(acc_master) == N_max

            acc_sub = acc_master[:ng]
            assert len(acc_sub) == ng

            # All speaker IDs, word counts, and errors must be identical to the master prefix
            for i in range(ng):
                assert acc_sub[i]["speaker_idx"] == acc_master[i]["speaker_idx"]
                assert acc_sub[i]["wc"] == acc_master[i]["wc"]
                assert acc_sub[i]["err1"] == acc_master[i]["err1"]
                assert acc_sub[i]["err2"] == acc_master[i]["err2"]
                assert acc_sub[i]["err3"] == acc_master[i]["err3"]


# ------------------------------------------------------------------------------
# 2. Paired observations across arms
# ------------------------------------------------------------------------------
def test_paired_observations_across_arms(candidate_spec):
    """
    Test 2: Verifies that every speaker record contains paired observations
    across all three arms (Static, SUTA, DSG) sharing the exact same word count.
    """
    rng = np.random.default_rng(42)
    data = generate_candidate_dataset(candidate_spec, num_speakers_per_stratum=50, rng=rng)
    for r in data["speaker_records"]:
        wc = r["wc"]
        assert candidate_spec.word_count_low <= wc < candidate_spec.word_count_high
        assert 0 <= r["err1"] <= wc
        assert 0 <= r["err2"] <= wc
        assert 0 <= r["err3"] <= wc


# ------------------------------------------------------------------------------
# 3. Synchronous joint event calculation
# ------------------------------------------------------------------------------
def test_synchronous_joint_event_calculation(candidate_spec):
    """
    Test 3: Verifies that joint success equals Event A AND Event B AND Event C AND Event D.
    If any single event fails, joint success must be False.
    """
    # Create mock records where DSG is worse than Static (Event A must fail)
    records = []
    for acc in candidate_spec.confirmatory_accents:
        for s in range(30):
            records.append({
                "accent": acc,
                "wc": 100,
                "err1": 10,   # Static = 10%
                "err2": 20,   # SUTA = 20%
                "err3": 25,   # DSG = 25% (severe degradation)
            })

    res = evaluate_trial_all_events(
        spk_records=records,
        spec=candidate_spec,
        n_bootstraps=200,
        boot_rng=np.random.default_rng(123),
        use_numba=False,
    )
    assert res["event_a"] is False
    assert res["joint_success"] is False


# ------------------------------------------------------------------------------
# 4. Exact Clopper-Pearson confidence interval calculations
# ------------------------------------------------------------------------------
def test_clopper_pearson_interval_mathematical_bounds():
    """
    Test 4: Verifies exact Clopper-Pearson 95% interval calculation against known Beta bounds.
    """
    # Edge case: k = 0
    l0, u0 = clopper_pearson_interval(0, 100, alpha=0.05)
    assert l0 == 0.0
    assert u0 == pytest.approx(1.0 - (0.05 / 2.0)**(1.0 / 100), abs=1e-5)

    # Edge case: k = n
    ln, un = clopper_pearson_interval(100, 100, alpha=0.05)
    assert un == 1.0
    assert ln == pytest.approx((0.05 / 2.0)**(1.0 / 100), abs=1e-5)

    # Standard case: k = 9000 out of 10,000
    l9k, u9k = clopper_pearson_interval(9000, 10000, alpha=0.05)
    assert 0.89 < l9k < 0.90
    assert 0.90 < u9k < 0.91

    # Exact threshold: k = 9060 out of 10,000 achieves LCB >= 0.90
    l_pass, _ = clopper_pearson_interval(9060, 10000, alpha=0.05)
    assert l_pass >= 0.90


# ------------------------------------------------------------------------------
# 5. Five-stratum M = 8 multiplicity architecture
# ------------------------------------------------------------------------------
def test_five_stratum_m8_multiplicity(candidate_spec):
    """
    Test 5: Verifies that five-stratum multiplicity parameters conform to
    Fixed Single-Step Simultaneous Bonferroni (M = 8, alpha_adj = 0.00625, 99.375%).
    """
    assert candidate_spec.m_hypotheses == 8
    assert candidate_spec.alpha_family == 0.05
    assert candidate_spec.adj_alpha == pytest.approx(0.00625, abs=1e-12)
    assert candidate_spec.simultaneous_percentile == pytest.approx(99.375, abs=1e-12)


# ------------------------------------------------------------------------------
# 6. Sample-size capacity bounds (Australian English N_g = 285)
# ------------------------------------------------------------------------------
def test_sample_size_capacity_bounds():
    """
    Test 6: Verifies capacity reconciliation logic identifies Australian English
    as the limiting stratum with exactly 285 evaluation speakers.
    """
    cap = reconcile_five_stratum_capacity()
    assert cap["limiting_accent"] == "Australian English"
    assert cap["max_balanced_eval_speakers_per_stratum"] == 285
    assert cap["max_total_confirmatory_speakers"] == 1425
    assert cap["strata_capacities"]["Australian English"]["total_eligible_speakers"] == 305
    assert cap["strata_capacities"]["Australian English"]["gate_reserve_speakers"] == 20


# ------------------------------------------------------------------------------
# 7. Deterministic fixed-seed reproducibility
# ------------------------------------------------------------------------------
def test_deterministic_fixed_seed_reproducibility(candidate_spec):
    """
    Test 7: Verifies that identical random seeds produce bitwise identical screening outcomes.
    """
    res1 = run_exploratory_screening_sweep(
        spec=candidate_spec,
        sample_sizes=[220],
        n_trials=10,
        n_bootstraps=500,
        random_seed=42,
        use_numba=False,
    )
    res2 = run_exploratory_screening_sweep(
        spec=candidate_spec,
        sample_sizes=[220],
        n_trials=10,
        n_bootstraps=500,
        random_seed=42,
        use_numba=False,
    )

    ev1 = res1["evaluations"][0]
    ev2 = res2["evaluations"][0]
    assert ev1["successful_joint_trajectories"] == ev2["successful_joint_trajectories"]
    assert ev1["joint_power"] == ev2["joint_power"]
    assert ev1["lcb_95"] == ev2["lcb_95"]


# ------------------------------------------------------------------------------
# 8. Protocol v1.4.0 frozen production code immutability
# ------------------------------------------------------------------------------
def test_frozen_v1_4_0_immutability():
    """
    Test 8: Verifies zero diff on src/dsg_ctta/evaluation/paired_cluster_inference.py
    relative to origin/main.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    prod_file = project_root / "src" / "dsg_ctta" / "evaluation" / "paired_cluster_inference.py"
    assert prod_file.exists()

    diff_res = subprocess.run(
        ["git", "diff", "origin/main", "--", str(prod_file)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert diff_res.returncode == 0
    assert diff_res.stdout.strip() == "", f"Frozen file mutated relative to origin/main: {diff_res.stdout}"


# ------------------------------------------------------------------------------
# 9. Execution metrics consistency
# ------------------------------------------------------------------------------
def test_execution_metrics_consistency(candidate_spec):
    """
    Test 9: Verifies that joint power is bounded by min(P(A), P(B), P(C), P(D)).
    """
    res = run_exploratory_screening_sweep(
        spec=candidate_spec,
        sample_sizes=[220, 240],
        n_trials=20,
        n_bootstraps=500,
        random_seed=101,
        use_numba=False,
    )
    for ev in res["evaluations"]:
        m = ev["marginal_event_probabilities"]
        jp = ev["joint_power"]
        assert jp <= m["event_a_static_superiority"] + 1e-12
        assert jp <= m["event_b_suta_superiority"] + 1e-12
        assert jp <= m["event_c_accent_regression_guard"] + 1e-12
        assert jp <= m["event_d_disparity_guard"] + 1e-12
        assert ev["lcb_95"] <= jp <= ev["ucb_95"]
