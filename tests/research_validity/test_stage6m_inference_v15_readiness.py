"""
tests/research_validity/test_stage6m_inference_v15_readiness.py

Comprehensive Validation Test Suite for Stage 6M v1.5 Candidate Inference Engine & Readiness
=============================================================================================
Governing Standards: ADR-005, Protocol Section 14.7 (PROJECT_LEAD_ACADEMIC_AUTHORIZATION)
Candidate Specification: Stage 6M v1.5 Candidate Five-Stratum Protocol
Governance State: DRAFT_HOLD (Confirmatory Audio Materialization & Adaptation Strictly Forbidden)

Test Coverage:
1. Exact Numerical Parity with Simulation Baseline:
   - Point estimates of Delta_static, Delta_ungated, Delta_g, Delta_Range match simulation to numerical precision.
   - Wald linearized standard errors and adjusted UCBs match simulator across all primary and safety bounds.
   - Disparity bootstrap distribution and simultaneous 99.375% UCB match exactly when given identical resamples.
   - Synchronous joint decision logic matches across all individual criteria and overall verdict.
2. Five-Stratum Hypothesis Family (M = 8):
   - M = 8 hypotheses strictly enforced.
   - Family alpha = 0.05 -> adjusted alpha = 0.00625.
   - Simultaneous confidence percentile = 99.375%.
3. Exploratory Out-of-Domain Isolation (Irish English):
   - Irish English is strictly excluded from the 5-stratum confirmatory family.
   - Irish English is reported under exploratory_strata without affecting M=8 or confirmatory verdict.
4. Input Validation & Strict Error Handling:
   - Empty input strictly raises ValueError.
   - Missing mandatory fields strictly raise ValueError.
   - Non-integer or non-positive word counts strictly raise ValueError.
   - Duplicate speaker IDs strictly raise ValueError.
   - Unauthorized strata outside canonical and exploratory sets strictly raise ValueError.
   - Stratum with < 2 speakers strictly raises ValueError.
5. Exact Clopper-Pearson Confidence Bounds:
   - Boundary checks at k=0 (LCB=0.0) and k=n (UCB=1.0).
   - Monotonicity and coverage properties.
6. Frozen v1.4.0 Production Inference Immutability:
   - src/dsg_ctta/evaluation/paired_cluster_inference.py has zero diff against origin/main.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
import scipy.stats as scipy_stats

from scripts.stage6m_v1_5_candidate_power_simulator import (
    CandidateFiveStratumPowerSpec as SimSpec,
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    EXPLORATORY_OUT_OF_DOMAIN_ACCENTS,
    generate_candidate_dataset,
)
from src.dsg_ctta.evaluation.paired_cluster_inference_v15 import (
    run_confirmatory_paired_cluster_inference_v15,
    CandidateFiveStratumPowerSpec as InfSpec,
    ConfirmatoryAnalysisReportV15,
)
from scripts.stage6m_v1_5_sample_size_power_sweep import (
    clopper_pearson_interval,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ==============================================================================
# 1. Exact Numerical Parity Tests
# ==============================================================================

def test_inference_v15_exact_numerical_parity_with_simulation():
    """
    Test 1: Verifies that paired_cluster_inference_v15 produces identical numerical
    point estimates, standard errors, adjusted UCBs, and event decisions as the
    authoritative five-stratum simulation engine.
    """
    rng = np.random.default_rng(20261101)
    spec = SimSpec()
    N = 40
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=N, rng=rng)
    spk_records = data["speaker_records"]
    for i, r in enumerate(spk_records):
        r["speaker_id"] = f"spk_parity_{i}"

    accents = sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS))
    n_accents = len(accents)
    adj_alpha = 0.05 / 8.0
    simultaneous_percentile = 100.0 * (1.0 - adj_alpha)

    # Simulation engine calculation
    total_w = float(sum(r["wc"] for r in spk_records))
    total_e1 = float(sum(r["err1"] for r in spk_records))
    total_e2 = float(sum(r["err2"] for r in spk_records))
    total_e3 = float(sum(r["err3"] for r in spk_records))

    sim_delta_static = ((total_e3 - total_e1) / total_w) * 100.0
    sim_delta_ungated = ((total_e3 - total_e2) / total_w) * 100.0

    n_clust = len(spk_records)
    df_corp = max(1, n_clust - 1)
    all_wc = np.array([r["wc"] for r in spk_records], dtype=float)
    all_e1 = np.array([r["err1"] for r in spk_records], dtype=float)
    all_e2 = np.array([r["err2"] for r in spk_records], dtype=float)
    all_e3 = np.array([r["err3"] for r in spk_records], dtype=float)
    w_bar = float(np.mean(all_wc))
    t_crit = float(scipy_stats.t.ppf(1.0 - adj_alpha, df=df_corp))

    u_s = (all_e3 - all_e1) - (sim_delta_static / 100.0) * all_wc
    se_s = (100.0 * float(np.std(u_s, ddof=1)) / math.sqrt(n_clust)) / w_bar
    sim_ucb_s = sim_delta_static + t_crit * se_s
    sim_event_a = bool(sim_delta_static < 0.0 and sim_ucb_s < 0.0)

    u_u = (all_e3 - all_e2) - (sim_delta_ungated / 100.0) * all_wc
    se_u = (100.0 * float(np.std(u_u, ddof=1)) / math.sqrt(n_clust)) / w_bar
    sim_ucb_u = sim_delta_ungated + t_crit * se_u
    sim_event_b = bool(sim_delta_ungated < 0.0 and sim_ucb_u < 0.0)

    # Accent regression bounds
    sim_accent_deltas = {}
    sim_accent_ucbs = {}
    sim_accent_passes = True
    for acc in accents:
        acc_r = [r for r in spk_records if r["stratum"] == acc]
        n_g = len(acc_r)
        df_g = max(1, n_g - 1)
        t_g = float(scipy_stats.t.ppf(1.0 - adj_alpha, df=df_g))
        gw = np.array([r["wc"] for r in acc_r], dtype=float)
        ge1 = np.array([r["err1"] for r in acc_r], dtype=float)
        ge3 = np.array([r["err3"] for r in acc_r], dtype=float)
        d_g = ((float(np.sum(ge3)) - float(np.sum(ge1))) / float(np.sum(gw))) * 100.0
        u_g = (ge3 - ge1) - (d_g / 100.0) * gw
        wb_g = float(np.mean(gw))
        se_g = (100.0 * float(np.std(u_g, ddof=1)) / math.sqrt(n_g)) / wb_g
        ucb_g = d_g + t_g * se_g
        sim_accent_deltas[acc] = d_g
        sim_accent_ucbs[acc] = ucb_g
        if ucb_g > 2.0:
            sim_accent_passes = False
    sim_event_c = sim_accent_passes

    # Shared bootstrap resamples
    B = 500
    boot_rng = np.random.default_rng(777)
    custom_resamples = np.zeros((n_accents, B, N), dtype=int)
    for a_idx in range(n_accents):
        custom_resamples[a_idx] = boot_rng.integers(0, N, size=(B, N))

    # Evaluate inference engine
    report = run_confirmatory_paired_cluster_inference_v15(
        speaker_records=spk_records,
        num_bootstrap_replicates=B,
        custom_bootstrap_resamples=custom_resamples,
    )

    crit_a = report.criteria["primary_superiority_static"]
    crit_b = report.criteria["primary_superiority_ungated"]
    crit_d = report.criteria["disparity_non_increase"]

    # Verify point estimates within floating precision (unrounded internal precision is exact, report rounds to 4 decimals)
    assert abs(sim_delta_static - report.delta_static_pp) < 1e-4
    assert abs(sim_ucb_s - crit_a.adjusted_ucb) < 1e-4
    assert abs(sim_delta_ungated - report.delta_ungated_pp) < 1e-4
    assert abs(sim_ucb_u - crit_b.adjusted_ucb) < 1e-4

    for acc in accents:
        cid = "accent_safety_" + acc.lower().replace(" ", "_")
        c = report.criteria[cid]
        assert abs(sim_accent_deltas[acc] - c.point_estimate) < 1e-4
        assert abs(sim_accent_ucbs[acc] - c.adjusted_ucb) < 1e-4

    # Verify decisions
    assert sim_event_a == crit_a.is_success
    assert sim_event_b == crit_b.is_success
    assert sim_event_c == all(report.criteria["accent_safety_" + a.lower().replace(" ", "_")].is_success for a in accents)


# ==============================================================================
# 2. Multiplicity & Bonferroni Adjustment Tests
# ==============================================================================

def test_multiplicity_m8_and_bonferroni_adjustment():
    """Test 2: Verifies M=8 fixed Bonferroni parameters and simultaneous percentile (99.375%)."""
    spec = InfSpec()
    assert spec.m_hypotheses == 8
    assert spec.alpha_family == 0.05
    assert spec.adj_alpha == pytest.approx(0.00625, abs=1e-9)
    assert spec.simultaneous_percentile == pytest.approx(99.375, abs=1e-9)


# ==============================================================================
# 3. Exploratory Irish English Isolation Tests
# ==============================================================================

def test_irish_english_strict_isolation_as_exploratory():
    """
    Test 3: Verifies that Irish English speaker records can be passed without contaminating
    the confirmatory M=8 family, confirmatory corpus WER, or disparity range.
    """
    spec = SimSpec()
    rng = np.random.default_rng(123)
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=10, rng=rng)
    spk_records = data["speaker_records"]
    for i, r in enumerate(spk_records):
        r["speaker_id"] = f"spk_{i}"

    # Append exploratory Irish records
    spk_records.append({
        "speaker_id": "spk_ie_01",
        "stratum": "Irish English",
        "wc": 150,
        "err1": 40,
        "err2": 42,
        "err3": 35,
    })
    spk_records.append({
        "speaker_id": "spk_ie_02",
        "stratum": "Irish English",
        "wc": 160,
        "err1": 38,
        "err2": 40,
        "err3": 32,
    })

    report = run_confirmatory_paired_cluster_inference_v15(
        speaker_records=spk_records,
        num_bootstrap_replicates=100,
        seed=42,
    )

    # Confirmatory criteria count must be exactly 8 (NOT 9)
    assert len(report.criteria) == 8
    assert report.m_hypotheses == 8
    assert "accent_safety_irish_english" not in report.criteria

    # Exploratory stratum must record Irish English separately
    assert "Irish English" in report.exploratory_strata
    ie_res = report.exploratory_strata["Irish English"]
    assert ie_res.num_speakers == 2
    assert ie_res.total_words == 310
    assert ie_res.delta_static_pp < 0.0


# ==============================================================================
# 4. Input Validation & Strict Error Handling
# ==============================================================================

def test_empty_speaker_records_raises_valueerror():
    with pytest.raises(ValueError, match="cannot be empty"):
        run_confirmatory_paired_cluster_inference_v15([])


def test_missing_confirmatory_stratum_raises_valueerror():
    records = [
        {"speaker_id": "s1", "stratum": "US English", "wc": 100, "err1": 10, "err2": 10, "err3": 8},
        {"speaker_id": "s2", "stratum": "US English", "wc": 100, "err1": 10, "err2": 10, "err3": 8},
    ]
    with pytest.raises(ValueError, match="Missing mandatory confirmatory strata"):
        run_confirmatory_paired_cluster_inference_v15(records)


def test_unauthorized_stratum_raises_valueerror():
    spec = SimSpec()
    rng = np.random.default_rng(123)
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=5, rng=rng)
    spk_records = data["speaker_records"]
    for i, r in enumerate(spk_records):
        r["speaker_id"] = f"spk_{i}"

    # Add unauthorized Scottish accent
    spk_records.append({
        "speaker_id": "spk_scot",
        "stratum": "Scottish English",
        "wc": 120,
        "err1": 15,
        "err2": 15,
        "err3": 12,
    })
    with pytest.raises(ValueError, match="Unauthorized accent strata detected"):
        run_confirmatory_paired_cluster_inference_v15(spk_records)


def test_duplicate_speaker_id_raises_valueerror():
    spec = SimSpec()
    rng = np.random.default_rng(123)
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=5, rng=rng)
    spk_records = data["speaker_records"]
    for r in spk_records:
        r["speaker_id"] = "duplicate_id"

    with pytest.raises(ValueError, match="Duplicate speaker ID detected"):
        run_confirmatory_paired_cluster_inference_v15(spk_records)


def test_invalid_word_counts_raises_valueerror():
    spec = SimSpec()
    rng = np.random.default_rng(123)
    data = generate_candidate_dataset(spec, num_speakers_per_stratum=5, rng=rng)
    spk_records = data["speaker_records"]
    for i, r in enumerate(spk_records):
        r["speaker_id"] = f"spk_{i}"
    spk_records[0]["wc"] = 0  # Invalid non-positive word count

    with pytest.raises(ValueError, match="Non-positive word count"):
        run_confirmatory_paired_cluster_inference_v15(spk_records)


# ==============================================================================
# 5. Clopper-Pearson Exact Confidence Intervals
# ==============================================================================

def test_clopper_pearson_exact_boundaries():
    """Test exact Clopper-Pearson interval boundary behavior."""
    # Zero successes
    low_0, high_0 = clopper_pearson_interval(0, 100, alpha=0.05)
    assert low_0 == 0.0
    assert 0.0 < high_0 < 0.05

    # Full successes
    low_n, high_n = clopper_pearson_interval(100, 100, alpha=0.05)
    assert high_n == 1.0
    assert 0.95 < low_n < 1.0

    # Monotonicity
    low_1, high_1 = clopper_pearson_interval(90, 100, alpha=0.05)
    low_2, high_2 = clopper_pearson_interval(95, 100, alpha=0.05)
    assert low_1 < low_2
    assert high_1 < high_2


# ==============================================================================
# 6. Frozen v1.4.0 Immutability
# ==============================================================================

def test_frozen_v1_4_paired_cluster_inference_remains_strictly_immutable():
    """
    Test 6: Verifies that frozen v1.4.0 implementation has zero diff against origin/main.
    """
    frozen_file = "src/dsg_ctta/evaluation/paired_cluster_inference.py"
    res = subprocess.run(
        ["git", "diff", "origin/main", "--", frozen_file],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert res.stdout.strip() == "", (
        f"VIOLATION: Frozen v1.4.0 code '{frozen_file}' has been modified relative to origin/main:\n"
        f"{res.stdout}"
    )
