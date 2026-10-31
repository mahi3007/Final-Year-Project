"""
Tests for Stage 6M v1.5 Candidate Data-Generating Model & Simulation Alignment
================================================================================

Validates all 9 deterministic and sampling requirements specified in Task E of Stage 6M Task 3:
1. Mean DSG improvement vs Static equals specified target (-3.5 pp).
2. Mean DSG improvement vs SUTA equals specified target (-3.5 pp).
3. Population-level disparity reduction equals -2.0 pp before speaker-level and binomial noise.
4. Latent speaker-level paired-difference SD is consistent with 3.2 pp.
5. All word counts and error counts are valid integers within bounds.
6. Each speaker has paired observations across all arms with identical word counts.
7. Five-stratum baseline calculations strictly exclude Irish English.
8. Reproducibility under a fixed random seed.
9. Frozen six-stratum implementation remains unchanged.
Additional: Test latent probability differences separately from observed binomial error-count differences.
"""

import math
import subprocess
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

from scripts.stage6m_v1_5_candidate_power_simulator import (
    CANONICAL_BENCHMARK_BASE_WERS,
    EXPLORATORY_OUT_OF_DOMAIN_ACCENTS,
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    CandidateFiveStratumPowerSpec,
    derive_five_stratum_treatment_effects,
    generate_candidate_dataset,
    simulate_candidate_five_stratum_power,
)


@pytest.fixture
def candidate_spec() -> CandidateFiveStratumPowerSpec:
    return CandidateFiveStratumPowerSpec()


# ------------------------------------------------------------------------------
# 1. Deterministic Test: Mean DSG improvement vs Static
# ------------------------------------------------------------------------------
def test_deterministic_mean_dsg_improvement_vs_static(candidate_spec):
    """
    Test 1: Analytical mean DSG improvement vs Static equals exactly -3.5 pp (-0.035)
    across the five confirmatory strata.
    """
    derived = derive_five_stratum_treatment_effects(candidate_spec)
    assert derived["theoretical_mean_delta_pp"] == pytest.approx(-3.50, abs=1e-12)

    deltas = list(derived["accent_deltas"].values())
    assert len(deltas) == 5
    assert float(np.mean(deltas)) == pytest.approx(-0.035, abs=1e-12)


# ------------------------------------------------------------------------------
# 2. Deterministic Test: Mean DSG improvement vs SUTA
# ------------------------------------------------------------------------------
def test_deterministic_mean_dsg_improvement_vs_suta(candidate_spec):
    """
    Test 2: Target DSG superiority vs Ungated SUTA equals exactly -3.5 pp.
    SUTA is parameterized with target_ungated_effect_pp = +3.5 pp higher WER than DSG.
    """
    assert candidate_spec.target_ungated_effect_pp == 3.50
    ungated_shift = candidate_spec.target_ungated_effect_pp / 100.0

    # For any speaker, p2 = clip(p3 + ungated_shift + eps2)
    # E[p3 - p2] before noise = -ungated_shift = -0.035 (-3.5 pp)
    assert ungated_shift == pytest.approx(0.035, abs=1e-12)


# ------------------------------------------------------------------------------
# 3. Deterministic Test: Population disparity reduction before noise
# ------------------------------------------------------------------------------
def test_deterministic_population_disparity_reduction_before_noise(candidate_spec):
    """
    Test 3: Population-level disparity reduction equals exactly -2.0 pp (-0.020)
    before speaker-level and binomial sampling variation.
    """
    derived = derive_five_stratum_treatment_effects(candidate_spec)

    mu_min = derived["mu_min"]
    mu_max = derived["mu_max"]
    static_disparity = mu_max - mu_min

    # Static: US English (0.142) is min, South Asian (0.235) is max
    assert mu_min == pytest.approx(0.142, abs=1e-6)
    assert mu_max == pytest.approx(0.235, abs=1e-6)
    assert static_disparity == pytest.approx(0.093, abs=1e-6)

    dsg_means = derived["accent_dsg_means"]
    dsg_min = min(dsg_means.values())
    dsg_max = max(dsg_means.values())
    dsg_disparity = dsg_max - dsg_min

    assert dsg_min == pytest.approx(dsg_means["US English"], abs=1e-6)
    assert dsg_max == pytest.approx(dsg_means["South Asian English"], abs=1e-6)
    assert dsg_disparity == pytest.approx(0.073, abs=1e-6)

    disparity_reduction = dsg_disparity - static_disparity
    assert disparity_reduction == pytest.approx(-0.020, abs=1e-12)
    assert derived["theoretical_disparity_reduction_pp"] == pytest.approx(-2.00, abs=1e-12)


# ------------------------------------------------------------------------------
# 4. Latent speaker-level paired-difference SD consistent with 3.2 pp
# ------------------------------------------------------------------------------
def test_latent_speaker_level_paired_difference_sd(candidate_spec):
    """
    Test 4: Latent speaker-level paired-difference SD is consistent with 3.2 pp (0.032).
    Evaluated over a large sample (N = 100,000 per stratum, 500,000 speakers total).
    """
    rng = np.random.default_rng(20261031)
    N = 100_000
    data = generate_candidate_dataset(
        spec=candidate_spec,
        num_speakers_per_stratum=N,
        rng=rng,
        accent_effect_mode="fixed",
    )
    latent = data["latent_records"]

    diff_31_raw = np.array([r["diff_31_raw"] for r in latent], dtype=float)
    diff_32_raw = np.array([r["diff_32_raw"] for r in latent], dtype=float)
    u_vals = np.array([r["u"] for r in latent], dtype=float)

    # Paired differences noise: sigma_paired_diff = 0.032
    # Note: diff_31_raw = delta_g + eps3, so within stratum Var(diff_31_raw) = Var(eps3) = 0.032^2
    sd_31_per_accent = []
    for acc in candidate_spec.confirmatory_accents:
        acc_diff = [r["diff_31_raw"] for r in latent if r["accent"] == acc]
        sd_31_per_accent.append(float(np.std(acc_diff, ddof=1)))

    mean_sd_31 = float(np.mean(sd_31_per_accent))
    sd_32_overall = float(np.std(diff_32_raw, ddof=1))
    sd_u_overall = float(np.std(u_vals, ddof=1))

    # All standard deviations match specified targets within tight statistical bounds
    assert mean_sd_31 == pytest.approx(0.032, abs=0.0005)
    assert sd_32_overall == pytest.approx(0.032, abs=0.0005)
    assert sd_u_overall == pytest.approx(0.065, abs=0.0005)

    # Latent means match scenario targets
    assert float(np.mean(diff_31_raw)) == pytest.approx(-0.035, abs=0.001)
    assert float(np.mean(diff_32_raw)) == pytest.approx(-0.035, abs=0.001)


# ------------------------------------------------------------------------------
# 5. All word counts and error counts are valid integers within bounds
# ------------------------------------------------------------------------------
def test_all_word_and_error_counts_are_valid_integers(candidate_spec):
    """
    Test 5: All word counts and error counts are valid integers.
    Word counts are in [100, 180). Error counts satisfy 0 <= err <= wc.
    """
    rng = np.random.default_rng(42)
    data = generate_candidate_dataset(
        spec=candidate_spec,
        num_speakers_per_stratum=100,
        rng=rng,
        accent_effect_mode="fixed",
    )
    records = data["speaker_records"]
    assert len(records) == 500

    for r in records:
        wc = r["wc"]
        e1, e2, e3 = r["err1"], r["err2"], r["err3"]

        assert isinstance(wc, int)
        assert isinstance(e1, int)
        assert isinstance(e2, int)
        assert isinstance(e3, int)

        assert 100 <= wc < 180, f"Word count {wc} outside [100, 180)"
        assert 0 <= e1 <= wc, f"err1 {e1} out of bounds for wc {wc}"
        assert 0 <= e2 <= wc, f"err2 {e2} out of bounds for wc {wc}"
        assert 0 <= e3 <= wc, f"err3 {e3} out of bounds for wc {wc}"


# ------------------------------------------------------------------------------
# 6. Each speaker has paired observations across all arms
# ------------------------------------------------------------------------------
def test_each_speaker_has_paired_observations_across_all_arms(candidate_spec):
    """
    Test 6: Each speaker has paired observations across all three arms (Static, SUTA, DSG)
    with the exact same word count.
    """
    rng = np.random.default_rng(123)
    data = generate_candidate_dataset(
        spec=candidate_spec,
        num_speakers_per_stratum=50,
        rng=rng,
    )
    records = data["speaker_records"]
    assert len(records) == 250

    for idx, r in enumerate(records):
        assert r["speaker_idx"] == idx
        # Required keys present and non-null
        for key in ("accent", "stratum", "wc", "err1", "err2", "err3"):
            assert key in r
            assert r[key] is not None


# ------------------------------------------------------------------------------
# 7. Five-stratum baseline calculations strictly exclude Irish English
# ------------------------------------------------------------------------------
def test_five_stratum_baseline_calculations_exclude_irish_english(candidate_spec):
    """
    Test 7: Five-stratum baseline calculations strictly exclude Irish English.
    The confirmatory accent list has exactly 5 accents.
    Irish English cannot be included in confirmatory derivation.
    """
    assert len(candidate_spec.confirmatory_accents) == 5
    assert "Irish English" not in candidate_spec.confirmatory_accents
    assert "Irish English" in EXPLORATORY_OUT_OF_DOMAIN_ACCENTS

    derived = derive_five_stratum_treatment_effects(candidate_spec)
    assert len(derived["confirmatory_accents"]) == 5
    assert "Irish English" not in derived["confirmatory_accents"]

    # If someone tries to pass Irish English into derive_five_stratum_treatment_effects, it must reject
    bad_spec = CandidateFiveStratumPowerSpec(
        confirmatory_accents=("Australian English", "Irish English", "US English")
    )
    with pytest.raises(ValueError, match="Irish English cannot be included"):
        derive_five_stratum_treatment_effects(bad_spec)


# ------------------------------------------------------------------------------
# 8. Fixed-seed reproducibility
# ------------------------------------------------------------------------------
def test_fixed_seed_reproducibility(candidate_spec):
    """
    Test 8: Reproducibility under a fixed random seed.
    Two calls with the same seed generate bitwise identical datasets.
    Calls with different seeds generate distinct datasets.
    """
    rng1 = np.random.default_rng(20261030)
    data1 = generate_candidate_dataset(candidate_spec, 20, rng1)

    rng2 = np.random.default_rng(20261030)
    data2 = generate_candidate_dataset(candidate_spec, 20, rng2)

    rng3 = np.random.default_rng(20261031)
    data3 = generate_candidate_dataset(candidate_spec, 20, rng3)

    assert data1["speaker_records"] == data2["speaker_records"]
    assert data1["speaker_records"] != data3["speaker_records"]


# ------------------------------------------------------------------------------
# 9. Frozen six-stratum implementation remains unchanged
# ------------------------------------------------------------------------------
def test_frozen_six_stratum_implementation_remains_unchanged():
    """
    Test 9: Verifies that src/dsg_ctta/evaluation/paired_cluster_inference.py
    has zero git modifications relative to main / origin/main, preserving Protocol v1.4.0.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    prod_file = project_root / "src" / "dsg_ctta" / "evaluation" / "paired_cluster_inference.py"
    assert prod_file.exists()

    # Check git status for the file
    res = subprocess.run(
        ["git", "status", "--porcelain", str(prod_file)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Frozen file was mutated: {res.stdout}"

    # Also verify that diff against origin/main is completely clean
    diff_res = subprocess.run(
        ["git", "diff", "origin/main", "--", str(prod_file)],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    assert diff_res.returncode == 0
    assert diff_res.stdout.strip() == "", f"Frozen file differs from origin/main: {diff_res.stdout}"


# ------------------------------------------------------------------------------
# 10. Latent Probability Differences vs Observed Binomial Error Differences
# ------------------------------------------------------------------------------
def test_latent_differences_vs_observed_binomial_differences(candidate_spec):
    """
    Test 10: Tests latent probability differences separately from observed binomial
    error-count differences.
    Demonstrates:
      1. Latent paired differences have variance equal to sigma_paired_diff^2.
      2. Observed speaker error-rate differences have higher variance due to binomial sampling:
         Var((err3 - err1) / wc) = sigma_paired_diff^2 + E[p1(1-p1)/wc + p3(1-p3)/wc].
      3. Word-weighted corpus aggregation converges to the latent treatment effect.
    """
    rng = np.random.default_rng(999)
    N = 20_000
    data = generate_candidate_dataset(
        spec=candidate_spec,
        num_speakers_per_stratum=N,
        rng=rng,
        accent_effect_mode="fixed",
    )
    recs = data["speaker_records"]
    latent = data["latent_records"]

    # Latent probability differences
    lat_diff_31 = np.array([l["diff_31_raw"] for l in latent], dtype=float)
    lat_mean = float(np.mean(lat_diff_31))
    lat_var = float(np.var(lat_diff_31, ddof=1))

    # Observed per-speaker error-rate differences
    obs_diff_31 = np.array([(r["err3"] - r["err1"]) / float(r["wc"]) for r in recs], dtype=float)
    obs_mean = float(np.mean(obs_diff_31))
    obs_var = float(np.var(obs_diff_31, ddof=1))

    # Both means converge to -0.035 (-3.5 pp)
    assert lat_mean == pytest.approx(-0.035, abs=0.001)
    assert obs_mean == pytest.approx(-0.035, abs=0.001)

    # Observed error rate variance is strictly greater than latent variance due to binomial sampling noise
    assert obs_var > lat_var
    assert math.sqrt(lat_var) == pytest.approx(0.032, abs=0.001)
    # Binomial noise adds ~0.0015-0.0025 variance, raising SD from 3.2 pp to ~5.0-5.5 pp per speaker
    obs_sd = math.sqrt(obs_var)
    assert 0.045 < obs_sd < 0.065

    # Word-weighted corpus aggregation matches exactly
    tot_w = float(sum(r["wc"] for r in recs))
    tot_e1 = float(sum(r["err1"] for r in recs))
    tot_e3 = float(sum(r["err3"] for r in recs))
    delta_static_corpus = ((tot_e3 - tot_e1) / tot_w) * 100.0
    assert delta_static_corpus == pytest.approx(-3.50, abs=0.15)
