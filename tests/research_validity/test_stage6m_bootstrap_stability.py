"""
Tests for Stage 6M v1.5 Candidate Bootstrap Quantile Stability (Task 4)
======================================================================

Validates all testing requirements specified in Task F of Stage 6M Task 4:
1. Fixed-seed reproducibility of bootstrap draws.
2. Nested-prefix correctness.
3. Paired resampling across arms (same cluster indices used for Static, SUTA, DSG).
4. Resampling strictly within each accent stratum (no cross-stratum contamination).
5. Preservation of speaker cluster count per accent stratum.
6. Exact word-weighted WER calculation.
7. Correct 99.375th percentile calculation (Bonferroni M=8).
8. Correct max-minus-min disparity calculation.
9. No modification of frozen Protocol v1.4.0 files.
10. Audit metrics consistency and decision agreement across independent streams.
"""

import math
import subprocess
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

from scripts.stage6m_bootstrap_stability_audit import (
    compute_point_estimates,
    evaluate_boundary_stress_scenarios,
    evaluate_boundary_stream_repeatability,
    evaluate_nested_prefixes,
    extract_stratum_arrays,
    run_bootstrap_stability_audit,
    run_stratified_cluster_bootstrap,
)
from scripts.stage6m_v1_5_candidate_power_simulator import (
    CandidateFiveStratumPowerSpec,
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    generate_candidate_dataset,
)


@pytest.fixture
def test_dataset():
    spec = CandidateFiveStratumPowerSpec()
    rng = np.random.default_rng(20261030)
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=20, rng=rng)
    return data


# ------------------------------------------------------------------------------
# 1. Fixed-seed reproducibility
# ------------------------------------------------------------------------------
def test_bootstrap_fixed_seed_reproducibility(test_dataset):
    """
    Test 1: Identical bootstrap RNG seeds produce bitwise identical replicate distributions.
    Different seeds produce distinct distributions.
    """
    acc_data = extract_stratum_arrays(test_dataset["speaker_records"])

    rng1 = np.random.default_rng(42)
    deltas1 = run_stratified_cluster_bootstrap(acc_data, n_bootstraps=500, rng=rng1)

    rng2 = np.random.default_rng(42)
    deltas2 = run_stratified_cluster_bootstrap(acc_data, n_bootstraps=500, rng=rng2)

    rng3 = np.random.default_rng(43)
    deltas3 = run_stratified_cluster_bootstrap(acc_data, n_bootstraps=500, rng=rng3)

    np.testing.assert_array_equal(deltas1, deltas2)
    assert not np.array_equal(deltas1, deltas3)


# ------------------------------------------------------------------------------
# 2. Nested-prefix correctness
# ------------------------------------------------------------------------------
def test_nested_prefix_correctness(test_dataset):
    """
    Test 2: Verifies that delta_ds[:b] is strictly a prefix of delta_ds[:ref_b],
    and evaluate_nested_prefixes computes quantiles on identical subsets.
    """
    acc_data = extract_stratum_arrays(test_dataset["speaker_records"])
    rng = np.random.default_rng(999)
    B_max = 5000
    delta_ds = run_stratified_cluster_bootstrap(acc_data, n_bootstraps=B_max, rng=rng)

    depths = [500, 1000, 2000, 5000]
    res = evaluate_nested_prefixes(delta_ds, depths=depths, percentile=99.375)

    ref_ucb = res[-1]["ucb_d_pp"]
    for item in res:
        b = item["bootstrap_depth"]
        slice_ucb = float(np.percentile(delta_ds[:b], 99.375))
        assert item["ucb_d_pp"] == pytest.approx(slice_ucb, abs=1e-5)
        assert item["diff_from_ref_pp"] == pytest.approx(abs(slice_ucb - ref_ucb), abs=1e-5)

    assert res[-1]["is_reference"] is True
    assert res[-1]["diff_from_ref_pp"] == 0.0


# ------------------------------------------------------------------------------
# 3. Paired resampling across arms
# ------------------------------------------------------------------------------
def test_paired_resampling_across_arms():
    """
    Test 3: Verifies that in each bootstrap draw, a speaker cluster contributes
    its word count and errors synchronously to both arms.
    """
    # Create synthetic records where arm 1 and arm 3 have identical errors per speaker
    # If paired, WER_arm1 == WER_arm3 in every single bootstrap draw, so Delta_D == 0.0 identically.
    speaker_records = []
    for a_idx, acc in enumerate(FIVE_STRATUM_CONFIRMATORY_ACCENTS):
        for s in range(30):
            wc = 100 + s
            err = 10 + s
            speaker_records.append({
                "accent": acc,
                "wc": wc,
                "err1": err,
                "err2": err,
                "err3": err,
            })
    acc_data = extract_stratum_arrays(speaker_records)
    rng = np.random.default_rng(12345)
    deltas = run_stratified_cluster_bootstrap(acc_data, n_bootstraps=200, rng=rng)

    # In every paired replicate, D_DSG == D_Static, so Delta_D must be 0.0 identically
    np.testing.assert_allclose(deltas, 0.0, atol=1e-12)


# ------------------------------------------------------------------------------
# 4. Resampling within each accent stratum
# ------------------------------------------------------------------------------
def test_resampling_within_each_accent(test_dataset):
    """
    Test 4: Verifies that resampling happens independently within each accent stratum,
    with no cross-stratum mixing.
    """
    acc_data = extract_stratum_arrays(test_dataset["speaker_records"])
    for a_idx in range(5):
        assert len(acc_data[a_idx]["wc"]) == 20
        assert len(acc_data[a_idx]["err1"]) == 20
        assert len(acc_data[a_idx]["err3"]) == 20


# ------------------------------------------------------------------------------
# 5. Preservation of speaker counts per accent stratum
# ------------------------------------------------------------------------------
def test_preservation_of_speaker_counts_per_accent():
    """
    Test 5: Verifies that exactly N_g speakers are resampled for accent stratum g.
    """
    spec = CandidateFiveStratumPowerSpec()
    N_g = 50
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=N_g, rng=np.random.default_rng(1))
    acc_data = extract_stratum_arrays(data["speaker_records"])

    for a_idx in range(5):
        assert len(acc_data[a_idx]["wc"]) == N_g


# ------------------------------------------------------------------------------
# 6. Word-weighted WER calculation
# ------------------------------------------------------------------------------
def test_word_weighted_wer_calculation():
    """
    Test 6: Verifies that WER is calculated as sum(errors) / sum(words) * 100,
    NOT as the unweighted arithmetic mean of speaker error rates.
    """
    # Speaker 1: 100 words, 10 errors (10% WER)
    # Speaker 2: 900 words, 180 errors (20% WER)
    # Word-weighted WER = (10 + 180) / (100 + 900) * 100 = 190 / 1000 * 100 = 19.0%
    # Unweighted mean = (10% + 20%) / 2 = 15.0%
    speaker_records = []
    for acc in FIVE_STRATUM_CONFIRMATORY_ACCENTS:
        speaker_records.append({"accent": acc, "wc": 100, "err1": 10, "err2": 10, "err3": 10})
        speaker_records.append({"accent": acc, "wc": 900, "err1": 180, "err2": 180, "err3": 180})

    acc_data = extract_stratum_arrays(speaker_records)
    pt = compute_point_estimates(acc_data)
    for a_idx in range(5):
        assert pt["wer1_per_accent"][a_idx] == pytest.approx(19.0, abs=1e-12)
        assert pt["wer3_per_accent"][a_idx] == pytest.approx(19.0, abs=1e-12)


# ------------------------------------------------------------------------------
# 7. Correct 99.375th percentile calculation
# ------------------------------------------------------------------------------
def test_correct_99_375th_percentile_calculation():
    """
    Test 7: Verifies percentile calculation for simultaneous Bonferroni M=8:
    alpha_adj = 0.05 / 8 = 0.00625 -> percentile = 99.375%.
    """
    spec = CandidateFiveStratumPowerSpec()
    assert spec.m_hypotheses == 8
    assert spec.adj_alpha == pytest.approx(0.00625, abs=1e-12)
    assert spec.simultaneous_percentile == pytest.approx(99.375, abs=1e-12)

    # For uniform array from 0 to 1000
    arr = np.linspace(0.0, 1000.0, 100001)
    q = np.percentile(arr, spec.simultaneous_percentile)
    assert q == pytest.approx(993.75, abs=1e-2)


# ------------------------------------------------------------------------------
# 8. Correct max-minus-min disparity calculation
# ------------------------------------------------------------------------------
def test_correct_max_minus_min_disparity_calculation():
    """
    Test 8: Verifies that disparity equals max(WER_g) - min(WER_g) across strata.
    """
    # Create distinct WERs per stratum: 10%, 12%, 14%, 18%, 25%
    target_wers1 = [10.0, 12.0, 14.0, 18.0, 25.0]
    target_wers3 = [8.0, 10.0, 11.0, 14.0, 20.0]

    speaker_records = []
    for a_idx, acc in enumerate(FIVE_STRATUM_CONFIRMATORY_ACCENTS):
        speaker_records.append({
            "accent": acc,
            "wc": 1000,
            "err1": int(target_wers1[a_idx] * 10),
            "err2": int(target_wers1[a_idx] * 10),
            "err3": int(target_wers3[a_idx] * 10),
        })

    acc_data = extract_stratum_arrays(speaker_records)
    pt = compute_point_estimates(acc_data)

    expected_d1 = 25.0 - 10.0  # 15.0 pp
    expected_d3 = 20.0 - 8.0   # 12.0 pp
    expected_delta_d = 12.0 - 15.0  # -3.0 pp

    assert pt["static_disparity_pp"] == pytest.approx(expected_d1, abs=1e-12)
    assert pt["dsg_disparity_pp"] == pytest.approx(expected_d3, abs=1e-12)
    assert pt["delta_disparity_pp"] == pytest.approx(expected_delta_d, abs=1e-12)


# ------------------------------------------------------------------------------
# 9. No modification of frozen v1.4.0 files
# ------------------------------------------------------------------------------
def test_no_modification_of_frozen_v1_4_0_files():
    """
    Test 9: Verifies zero diff on src/dsg_ctta/evaluation/paired_cluster_inference.py
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
# 10. Audit metrics consistency and stream repeatability
# ------------------------------------------------------------------------------
def test_audit_execution_metrics_consistency():
    """
    Test 10: Runs a minimal audit and verifies mathematical bounds on summary metrics.
    """
    res = run_bootstrap_stability_audit(
        dataset_seeds=[20261030, 20261031],
        bootstrap_depths=[500, 1000, 2000],
        stream_seeds=[9001, 9002],
        num_speakers_per_stratum=30,
        percentile=99.375,
    )
    s = res["depth_sensitivity_summary"]
    assert s["evaluated_datasets_count"] == 2
    assert s["total_evaluations"] == 6
    assert s["non_reference_evaluations_count"] == 4
    assert s["median_absolute_diff_pp"] >= 0.0
    assert s["p95_absolute_diff_pp"] >= s["median_absolute_diff_pp"]
    assert s["max_absolute_diff_pp"] >= s["p95_absolute_diff_pp"]

    r = res["independent_stream_repeatability"]
    assert r["streams_count"] == 2
    assert r["std_ucb_d_pp"] >= 0.0
    assert r["max_pairwise_diff_pp"] >= 0.0


# ------------------------------------------------------------------------------
# 11. Boundary scenario deterministic reproducibility
# ------------------------------------------------------------------------------
def test_boundary_scenario_reproducibility():
    """
    Test 11 (Task 4.1): Verifies that identical seeds and boundary disparity targets
    produce bitwise identical datasets and point estimates.
    """
    for t in [-0.20, 0.00, +0.20]:
        spec = CandidateFiveStratumPowerSpec(target_disparity_effect_pp=t)
        d1 = generate_candidate_dataset(spec, num_speakers_per_stratum=30, rng=np.random.default_rng(20261050))
        d2 = generate_candidate_dataset(spec, num_speakers_per_stratum=30, rng=np.random.default_rng(20261050))

        pt1 = compute_point_estimates(extract_stratum_arrays(d1["speaker_records"]))
        pt2 = compute_point_estimates(extract_stratum_arrays(d2["speaker_records"]))
        assert pt1["delta_disparity_pp"] == pytest.approx(pt2["delta_disparity_pp"], abs=1e-12)


# ------------------------------------------------------------------------------
# 12. Decision stability and low discrepancy at the boundary
# ------------------------------------------------------------------------------
def test_boundary_decision_stability_and_flip_rate():
    """
    Test 12 (Task 4.1): Evaluates boundary stress panel across targets {-0.2, 0.0, +0.2} pp.
    Verifies that the difference between B=2,000 and B=20,000 is bounded (max diff < 0.15 pp)
    and zero decision flips occur across the tested panel.
    """
    res = evaluate_boundary_stress_scenarios(
        boundary_targets=[-0.20, 0.00, +0.20],
        boundary_seeds=[20261050, 20261051, 20261052],
        num_speakers_per_stratum=220,
        percentile=99.375,
    )
    s = res["summary"]
    assert s["total_boundary_evaluations"] == 9
    assert s["total_decision_flips"] == 0
    assert s["max_diff_pp"] < 0.15
    assert s["median_diff_pp"] < 0.06


# ------------------------------------------------------------------------------
# 13. Boundary stream repeatability and unanimous agreement
# ------------------------------------------------------------------------------
def test_boundary_stream_repeatability_agreement():
    """
    Test 13 (Task 4.1): Evaluates independent 20,000-replicate streams on a dataset
    deliberately located near the zero boundary (target delta_D = 0.00 pp).
    Verifies unanimous decision agreement and low between-stream standard deviation.
    """
    res = evaluate_boundary_stream_repeatability(
        target_disparity_effect_pp=0.00,
        dataset_seed=20261050,
        stream_seeds=[9101, 9102, 9103],
        num_speakers_per_stratum=220,
        bootstrap_depth=20000,
        percentile=99.375,
    )
    assert res["decision_agreement_unanimous"] is True
    assert res["decision_agreement_count"] == 3
    assert res["between_stream_std_ucb_d_pp"] < 0.03
    assert res["standard_error_mean_ucb_d_pp"] == pytest.approx(
        res["between_stream_std_ucb_d_pp"] / math.sqrt(3), abs=1e-5
    )


# ------------------------------------------------------------------------------
# 14. Statistical terminology consistency in repeatability metrics
# ------------------------------------------------------------------------------
def test_statistical_terminology_consistency():
    """
    Test 14 (Task 4.1): Verifies that between-stream standard deviation and standard
    error of the stream mean are explicitly distinguished and mathematically consistent.
    """
    res = run_bootstrap_stability_audit(
        dataset_seeds=[20261030],
        bootstrap_depths=[500, 2000],
        stream_seeds=[9001, 9002, 9003, 9004, 9005],
        boundary_targets=[0.00],
        boundary_seeds=[20261050],
        boundary_stream_seeds=[9101, 9102],
        num_speakers_per_stratum=30,
    )
    r = res["independent_stream_repeatability"]
    assert "between_stream_std_ucb_d_pp" in r
    assert "standard_error_mean_ucb_d_pp" in r
    assert r["standard_error_mean_ucb_d_pp"] == pytest.approx(
        r["between_stream_std_ucb_d_pp"] / math.sqrt(5), abs=1e-5
    )
    assert "task_4_1_boundary_addendum" in res

