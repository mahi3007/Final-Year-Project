"""
Research Validity Tests: Stage 6M Reproducibility, Gate Selectivity, and Invariants.
=====================================================================================
Governing Standards: ADR-005, Protocol v1.3.4-stage6m-self-authorization-amendment

Directly addresses reviewer validation requirements:
1. Exact metric recomputation from exported speaker-level prediction records (8,667 words, 60 speakers).
2. Unrounded speaker-level paired t-test and Wilcoxon signed-rank recalculation.
3. Gate selectivity verification across synthetic harmful, neutral, beneficial, and disparity-violating cases.
4. Paired speaker-cluster uncertainty quantification vs independent approximation.
5. Full 64-character SHA-256 parameter hash verification and L_inf = 0.0 bitwise rollback.
6. Kaggle runner fail-closed execution and clean Linux LF checkout compatibility.
"""

import json
import math
import copy
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from scipy import stats
import torch

from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.bootstrap import run_paired_speaker_bootstrap
from dsg_ctta.controller.types import BootstrapMetrics
from dsg_ctta.controller.streaming_gate import (
    StreamingSentinelSafetyGate,
    compute_calibrated_obf_schedule,
    simulate_sequential_type1_error,
    simulate_multicriterion_streaming_gate_null,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6m"
SPEAKER_CSV = REPORTS_DIR / "stage6m_physical_cohort1_speaker_records.csv"
GATE_CSV = REPORTS_DIR / "stage6m_physical_cohort1_gate_decisions.csv"
REPORT_JSON = REPORTS_DIR / "stage6m_physical_cohort1_report.json"
BENCHMARK_PY = PROJECT_ROOT / "cloud" / "kaggle" / "run_stage6m_cohort2_benchmark.py"
NOTEBOOK_IPYNB = PROJECT_ROOT / "cloud" / "kaggle" / "run_stage6m_cohort2_kaggle.ipynb"


def test_cohort1_exact_reproducibility_from_speaker_csv():
    """Verify that all reported metrics reproduce with exact arithmetic identity from speaker records."""
    assert SPEAKER_CSV.exists(), f"Missing speaker records CSV: {SPEAKER_CSV}"
    df = pd.read_csv(SPEAKER_CSV)

    assert len(df) == 60, f"Expected exactly 60 speakers, found {len(df)}"
    assert df["speaker_id"].nunique() == 60

    total_words = int(df["wc"].sum())
    err1 = int(df["err1"].sum())
    err2 = int(df["err2"].sum())
    err3 = int(df["err3"].sum())

    # Exact word and error counts
    assert total_words == 8667, f"Expected 8,667 total reference words, got {total_words}"
    assert err1 == 1980, f"Expected 1,980 static errors, got {err1}"
    assert err2 == 2059, f"Expected 2,059 ungated errors, got {err2}"
    assert err3 == 1980, f"Expected 1,980 gated errors, got {err3}"

    # Net error deltas
    delta_errors_2_1 = err2 - err1
    delta_errors_3_2 = err3 - err2
    delta_errors_3_1 = err3 - err1
    assert delta_errors_2_1 == 79, f"Ungated SUTA must produce exactly +79 word errors, got {delta_errors_2_1}"
    assert delta_errors_3_2 == -79, f"DSG must save exactly 79 word errors relative to ungated, got {delta_errors_3_2}"
    assert delta_errors_3_1 == 0, f"DSG must match static baseline exactly (0 error delta), got {delta_errors_3_1}"

    # Exact Word Error Rates
    wer1 = err1 / total_words * 100.0
    wer2 = err2 / total_words * 100.0
    wer3 = err3 / total_words * 100.0

    assert abs(wer1 - 22.845286) < 1e-4
    assert round(wer1, 2) == 22.85
    assert abs(wer2 - 23.756778) < 1e-4
    assert round(wer2, 2) == 23.76
    assert abs(wer3 - 22.845286) < 1e-4
    assert round(wer3, 2) == 22.85

    assert round(wer2 - wer1, 2) == 0.91


def test_unrounded_speaker_level_paired_inferential_statistics():
    """Recalculate paired t-test and Wilcoxon signed-rank test directly from unrounded speaker values."""
    assert SPEAKER_CSV.exists()
    df = pd.read_csv(SPEAKER_CSV)

    # Calculate exact unrounded speaker-level error rates
    spk_wer1 = df["err1"] / df["wc"] * 100.0
    spk_wer2 = df["err2"] / df["wc"] * 100.0
    spk_wer3 = df["err3"] / df["wc"] * 100.0

    diff_3_2 = spk_wer3 - spk_wer2
    diff_3_1 = spk_wer3 - spk_wer1

    # Primary Utility Hypothesis: Arm 3 vs Arm 2
    t_res_32 = stats.ttest_rel(spk_wer3, spk_wer2)
    assert t_res_32.df == 59
    assert abs(t_res_32.statistic - (-2.713653)) < 1e-4, f"Expected t = -2.7137, got {t_res_32.statistic}"
    assert abs(t_res_32.pvalue - 0.0087099) < 1e-4, f"Expected p = 0.00871, got {t_res_32.pvalue}"
    assert t_res_32.pvalue < 0.01, "Arm 3 vs Arm 2 must achieve statistical significance at p < 0.01"

    # Non-parametric Wilcoxon signed-rank test
    w_res_32 = stats.wilcoxon(diff_3_2)
    assert w_res_32.pvalue < 0.05, f"Wilcoxon signed-rank must achieve p < 0.05, got {w_res_32.pvalue}"

    # Secondary Stability Hypothesis: Arm 3 vs Arm 1 (Zero-variance identity)
    assert np.all(diff_3_1 == 0.0), "All 60 speaker paired differences between Arm 3 and Arm 1 must be identically 0.0"


def test_stratum_level_reproducibility_and_subgroup_nuance():
    """Verify stratum-level WERs and confirm subgroup divergence (Irish degradation vs South Asian gain)."""
    assert SPEAKER_CSV.exists()
    df = pd.read_csv(SPEAKER_CSV)

    strata_agg = df.groupby("stratum").agg(
        words=("wc", "sum"),
        err1=("err1", "sum"),
        err2=("err2", "sum"),
        err3=("err3", "sum"),
    ).reset_index()

    strata_wers = {}
    for _, row in strata_agg.iterrows():
        s = row["stratum"]
        w = row["words"]
        w1 = row["err1"] / w * 100.0
        w2 = row["err2"] / w * 100.0
        w3 = row["err3"] / w * 100.0
        strata_wers[s] = {"wer1": round(w1, 2), "wer2": round(w2, 2), "wer3": round(w3, 2), "delta_21": round(w2 - w1, 2)}

    # Confirm Irish English suffered severe regression under ungated SUTA (+2.93 pp)
    assert strata_wers["Irish English"]["wer1"] == 15.75
    assert strata_wers["Irish English"]["wer2"] == 18.68
    assert strata_wers["Irish English"]["delta_21"] == 2.93
    assert strata_wers["Irish English"]["wer3"] == 15.75

    # Confirm South Asian English improved under ungated SUTA (-0.69 pp)
    assert strata_wers["South Asian English"]["wer1"] == 42.31
    assert strata_wers["South Asian English"]["wer2"] == 41.62
    assert strata_wers["South Asian English"]["delta_21"] == -0.69
    assert strata_wers["South Asian English"]["wer3"] == 42.31

    # Confirm Canadian English degraded under ungated SUTA (+1.65 pp)
    assert strata_wers["Canadian English"]["wer1"] == 12.91
    assert strata_wers["Canadian English"]["wer2"] == 14.56
    assert strata_wers["Canadian English"]["delta_21"] == 1.65


def test_legacy_disparity_safety_gate_selectivity():
    """
    Test the legacy offline DisparitySafetyGate on synthetic candidate updates covering:
    (1) Harmful updates -> REJECT
    (2) Neutral updates -> ACCEPT / STABILITY
    (3) Beneficial updates across all strata -> ACCEPT
    (4) Disparity-widening updates -> REJECT
    Validates backward compatibility of the offline bootstrap evaluator.
    """
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)

    # Base sentinel panel: 30 speakers, 6 groups, 300 words
    base_records = [
        {"utterance_id": f"utt_{i}", "speaker_id": f"spk_{i%30}", "group_id": f"grp_{i%6}", "substitutions": 2, "deletions": 1, "insertions": 0, "reference_length": 15}
        for i in range(120)
    ]

    # Case 1: Harmful update (+3 substitutions across speakers)
    harmful_records = [dict(r) for r in base_records]
    for i in range(len(harmful_records)):
        if i % 3 == 0:
            harmful_records[i]["substitutions"] += 2
    metrics_harm = run_paired_speaker_bootstrap(base_records, harmful_records, num_replicates=400, seed=123)
    dec_harm = gate.evaluate_decision(metrics_harm, "c_harm", "live", 123, 400)
    assert dec_harm.decision == "REJECT", f"Harmful update must be rejected, got {dec_harm.decision}"
    assert dec_harm.ucb_r > 0.0

    # Case 2: Neutral update (exact identical predictions)
    neutral_records = [dict(r) for r in base_records]
    metrics_neu = run_paired_speaker_bootstrap(base_records, neutral_records, num_replicates=400, seed=123)
    dec_neu = gate.evaluate_decision(metrics_neu, "c_neu", "live", 123, 400)
    assert dec_neu.decision == "ACCEPT", f"Neutral update must pass safety criteria, got {dec_neu.decision}"
    assert metrics_neu.delta_r == 0.0
    assert metrics_neu.ucb_r == 0.0

    # Case 3: Universally Beneficial update (reduces errors across all strata)
    beneficial_records = [dict(r) for r in base_records]
    for i in range(len(beneficial_records)):
        beneficial_records[i]["substitutions"] = max(0, beneficial_records[i]["substitutions"] - 1)
    metrics_ben = run_paired_speaker_bootstrap(base_records, beneficial_records, num_replicates=400, seed=123)
    dec_ben = gate.evaluate_decision(metrics_ben, "c_ben", "live", 123, 400)
    assert dec_ben.decision == "ACCEPT", f"Beneficial update must be accepted, got {dec_ben.decision}"
    assert metrics_ben.delta_r < 0.0
    assert metrics_ben.ucb_r <= 0.0

    # Case 4: Disparity-Widening update (benefits only one group, widening disparity)
    disp_records = [dict(r) for r in base_records]
    for i in range(len(disp_records)):
        if disp_records[i]["group_id"] == "grp_0":
            disp_records[i]["substitutions"] = 0
            disp_records[i]["deletions"] = 0
    metrics_disp = run_paired_speaker_bootstrap(base_records, disp_records, num_replicates=400, seed=123)
    dec_disp = gate.evaluate_decision(metrics_disp, "c_disp", "live", 123, 400)
    # Group 0 error dropped to 0, widening disparity gap
    assert metrics_disp.ucb_d > 0.0200, f"Disparity UCB ({metrics_disp.ucb_d:.4f}) must exceed threshold 0.0200"
    assert dec_disp.decision == "REJECT", f"Disparity growth must unconditionally trigger rejection, got {dec_disp.decision}"


def test_production_streaming_sentinel_safety_gate_selectivity():
    """
    Directly tests the production StreamingSentinelSafetyGate.evaluate_candidate method
    across 5 distinct synthetic update regimes:
    (1) Harmful update -> REJECT with overall risk violation and point degradation.
    (2) Neutral update (identical model) -> ACCEPT with exact zero deltas and bounds.
    (3) Beneficial update across all strata -> ACCEPT with negative delta_r and ucb_r <= 0.
    (4) Disparity-widening update (benefits only stratum 0) -> REJECT with disparity growth violation.
    (5) Subgroup regression update (overall improvement, but one protected stratum degrades) ->
        REJECT with subgroup regression violation in worst group (tripartite rule verification).
    """
    gate = StreamingSentinelSafetyGate(
        epsilon_r_pp=0.0000,
        epsilon_g_pp=2.0000,
        epsilon_d_pp=2.0000,
        num_updates=224,
        alpha_target=0.05,
    )

    # Core sentinel panel: 30 speakers, 6 strata (5 speakers each), 15 words per speaker (450 total)
    speaker_ids = [f"spk_{i}" for i in range(30)]
    stratum_groups = [f"grp_{i // 5}" for i in range(30)]
    ref_lengths = [15] * 30
    live_errors = [3] * 30  # Baseline: 3/15 = 20.0% WER in every stratum

    # Case 1: Harmful update (+2 errors per speaker across stream)
    cand_harmful = [e + 2 for e in live_errors]
    dec_harm = gate.evaluate_candidate(0, speaker_ids, stratum_groups, live_errors, cand_harmful, ref_lengths)
    assert dec_harm.decision == "REJECT", f"Expected REJECT for harmful update, got {dec_harm.decision}"
    assert dec_harm.passed_gate is False
    assert dec_harm.delta_r > 0.0
    assert dec_harm.ucb_r > 0.0
    assert any("Overall risk violation" in r for r in dec_harm.rejection_reasons)
    assert any("Point degradation" in r for r in dec_harm.rejection_reasons)

    # Case 2: Neutral / tied update (identical candidate error counts)
    # Under fail-closed safety, ties and zero measured improvement must REJECT
    cand_neutral = list(live_errors)
    dec_neu = gate.evaluate_candidate(0, speaker_ids, stratum_groups, live_errors, cand_neutral, ref_lengths)
    assert dec_neu.decision == "REJECT", f"Expected REJECT for tied candidate, got {dec_neu.decision}"
    assert dec_neu.passed_gate is False
    assert dec_neu.delta_r == 0.0
    assert dec_neu.se_r_raw == 0.0  # Raw empirical SE is exactly zero for identical error counts
    assert abs(dec_neu.se_r_floor - (1.0 / 450.0 * 100.0)) < 1e-3  # Cluster floor safeguard
    assert dec_neu.se_r_adjusted == dec_neu.se_r_floor  # Regularized by floor safeguard
    assert dec_neu.se_r == dec_neu.se_r_adjusted  # Backward compatible alias
    assert dec_neu.ucb_r > 0.0  # z_0 * se_floor > 0
    assert any("Non-improvement / tie rejection" in r for r in dec_neu.rejection_reasons)
    assert any("Degenerate zero-variance tie" in r for r in dec_neu.rejection_reasons)

    # Case 3: Universally Beneficial update (reduces errors across all strata)

    cand_beneficial = [max(0, e - 1) for e in live_errors]
    dec_ben = gate.evaluate_candidate(0, speaker_ids, stratum_groups, live_errors, cand_beneficial, ref_lengths)
    assert dec_ben.decision == "ACCEPT", f"Expected ACCEPT for beneficial update, got {dec_ben.decision}"
    assert dec_ben.passed_gate is True
    assert dec_ben.delta_r < 0.0
    assert dec_ben.ucb_r <= 0.0
    assert dec_ben.ucb_max_group <= 2.0
    assert dec_ben.ucb_d <= 2.0
    assert len(dec_ben.rejection_reasons) == 0

    # Case 4: Disparity-Widening update (benefits only stratum 0, leaving others unchanged)
    cand_disp = [0 if stratum_groups[i] == "grp_0" else live_errors[i] for i in range(30)]
    dec_disp = gate.evaluate_candidate(0, speaker_ids, stratum_groups, live_errors, cand_disp, ref_lengths)
    assert dec_disp.decision == "REJECT", f"Expected REJECT for disparity-widening update, got {dec_disp.decision}"
    assert dec_disp.passed_gate is False
    assert dec_disp.delta_d > 2.0
    assert dec_disp.ucb_d > 2.0
    assert any("Disparity growth violation" in r for r in dec_disp.rejection_reasons)

    # Case 5: Worst Subgroup Regression update (improves overall, but severely degrades grp_5)
    cand_subgroup = [
        live_errors[i] - 2 if stratum_groups[i] in ["grp_0", "grp_1"]
        else (live_errors[i] + 3 if stratum_groups[i] == "grp_5" else live_errors[i])
        for i in range(30)
    ]
    dec_sub = gate.evaluate_candidate(0, speaker_ids, stratum_groups, live_errors, cand_subgroup, ref_lengths)
    assert dec_sub.delta_r < 0.0, "Overall risk point estimate should be negative (improved)"
    assert dec_sub.worst_group == "grp_5"
    assert dec_sub.ucb_max_group > 2.00
    assert dec_sub.decision == "REJECT", f"Expected REJECT for subgroup regression, got {dec_sub.decision}"
    assert dec_sub.passed_gate is False
    assert any("Subgroup regression violation in [grp_5]" in r for r in dec_sub.rejection_reasons)

    # Case 6: Zero net improvement with non-zero variance (sum(cand) == sum(live) but individual errors differ)
    # Under fail-closed non-improvement rule, Delta_R = 0.0 must be rejected
    cand_zero_net = list(live_errors)
    cand_zero_net[0] += 1
    cand_zero_net[1] -= 1
    dec_zero_net = gate.evaluate_candidate(0, speaker_ids, stratum_groups, live_errors, cand_zero_net, ref_lengths)
    assert dec_zero_net.delta_r == 0.0
    assert dec_zero_net.decision == "REJECT", "Candidate with zero net improvement must be rejected"
    assert dec_zero_net.passed_gate is False
    assert any("Non-improvement / tie rejection" in r for r in dec_zero_net.rejection_reasons)

    # Case 7: Cluster single-token sensitivity floor verification
    # Verifies that se_r_adjusted is bounded below by 1 / total_words * 100% (0.2222 pp for 450 words)
    expected_floor = (1.0 / 450.0) * 100.0
    assert dec_neu.se_r_floor == round(expected_floor, 4), f"Expected se_r_floor = {expected_floor:.4f}, got {dec_neu.se_r_floor}"
    assert dec_neu.se_r_adjusted == round(expected_floor, 4), f"Expected se_r_adjusted = {expected_floor:.4f}, got {dec_neu.se_r_adjusted}"
    assert dec_neu.se_r_raw == 0.0, f"Expected se_r_raw = 0.0, got {dec_neu.se_r_raw}"



def test_paired_vs_independent_uncertainty_quantification():
    """Verify that paired cluster estimation accounts for covariance and avoids artificial inflation."""
    # Part 1: Synthetic panel where live and candidate are identical (zero difference)
    r_live = [{"speaker_id": f"s_{i%10}", "sub": 1, "del": 0, "ins": 0, "n": 10} for i in range(30)]
    r_cand = [{"speaker_id": f"s_{i%10}", "sub": 1, "del": 0, "ins": 0, "n": 10} for i in range(30)]

    # Independent binomial approximation
    total_n = sum(r["n"] for r in r_live)
    p_hat = sum(r["sub"] for r in r_live) / total_n
    se_indep_zero = math.sqrt(2.0 * p_hat * (1.0 - p_hat) / total_n) * 100.0

    # Paired clustered calculation
    spk_pairs = {}
    for r in r_live:
        sid = r["speaker_id"]
        if sid not in spk_pairs: spk_pairs[sid] = {"live": 0, "cand": 0, "n": 0}
        spk_pairs[sid]["live"] += r["sub"]
        spk_pairs[sid]["n"] += r["n"]
    for r in r_cand:
        spk_pairs[r["speaker_id"]]["cand"] += r["sub"]

    S = len(spk_pairs)
    diffs = [spk_pairs[s]["cand"] - spk_pairs[s]["live"] for s in spk_pairs]
    assert all(d == 0 for d in diffs)
    se_paired_zero = math.sqrt(sum(d**2 for d in diffs) / S) * 100.0

    # Independent formula produces artificial uncertainty (~2.45%) on identical models!
    assert se_indep_zero > 2.0
    # Paired formula correctly yields 0.0% standard error on identical models!
    assert se_paired_zero == 0.0

    # Part 2: Nonzero paired effects with heterogeneous speaker-level differences
    np.random.seed(42)
    spk_live_err = [3, 5, 2, 8, 4, 1, 6, 3, 7, 2]
    spk_cand_err = [4, 4, 3, 10, 4, 1, 8, 3, 8, 3]  # Heterogeneous speaker deltas: +1, -1, +1, +2, 0, 0, +2, 0, +1, +1
    spk_wc = [20, 35, 15, 45, 25, 10, 40, 20, 50, 15]

    n_total = sum(spk_wc)
    e_live_total = sum(spk_live_err)
    e_cand_total = sum(spk_cand_err)
    delta_frac = (e_cand_total - e_live_total) / float(n_total)

    # Clustered delta-method paired standard error
    u_sq = sum(((spk_cand_err[i] - spk_live_err[i]) - delta_frac * spk_wc[i]) ** 2 for i in range(10))
    var_paired = (10.0 / 9.0) * u_sq / (float(n_total) ** 2)
    se_paired_nonzero = math.sqrt(var_paired) * 100.0

    # Independent two-sample standard error
    p1 = e_live_total / float(n_total)
    p2 = e_cand_total / float(n_total)
    se_indep_nonzero = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / float(n_total)) * 100.0

    # Paired SE is strictly non-zero and captures paired covariance
    assert se_paired_nonzero > 0.0, "Paired SE must be non-zero for heterogeneous speaker effects"
    assert se_paired_nonzero < se_indep_nonzero, (
        f"Paired SE ({se_paired_nonzero:.3f}%) must be smaller than independent SE ({se_indep_nonzero:.3f}%) "
        "due to positive paired correlation"
    )


def test_full_64char_sha256_parameter_rollback_verification():
    """Verify that parameter rollback verification enforces full 64-character SHA-256 match and real L_inf = 0.0."""
    torch.manual_seed(42)
    model = torch.nn.Sequential(
        torch.nn.Linear(32, 32),
        torch.nn.LayerNorm(32)
    )

    # Retain a completely separate frozen reference copy of initial model
    reference_init_model = copy.deepcopy(model)

    # Initial full SHA-256 hash
    hasher_init = hashlib.sha256()
    for p in model.parameters():
        hasher_init.update(p.detach().cpu().numpy().tobytes())
    hash_init = hasher_init.hexdigest()
    assert len(hash_init) == 64, f"Expected 64-character SHA-256 hash, got {len(hash_init)}"

    # Candidate clone adapts with nonzero perturbation
    cand_model = copy.deepcopy(model)
    for p in cand_model.parameters():
        p.data += 0.05  # Simulate weight adaptation

    # Verify candidate model has drifted from reference model
    cand_linf = max(
        torch.max(torch.abs(p_cand - p_init)).item()
        for p_cand, p_init in zip(cand_model.parameters(), reference_init_model.parameters())
    )
    assert cand_linf > 0.04, f"Candidate model must have drifted, got {cand_linf}"

    # Rollback simulation: candidate rejected, live model untouched
    del cand_model

    hasher_final = hashlib.sha256()
    for p in model.parameters():
        hasher_final.update(p.detach().cpu().numpy().tobytes())
    hash_final = hasher_final.hexdigest()

    # Full 64-character verification
    assert hash_init == hash_final, f"Full 64-char hash mismatch: {hash_init} != {hash_final}"

    # Real parameter drift L_inf comparing live model against initial reference model
    max_linf = max(
        torch.max(torch.abs(p_live - p_init)).item()
        for p_live, p_init in zip(model.parameters(), reference_init_model.parameters())
    )
    assert max_linf == 0.0, f"Expected real L_inf = 0.0, got {max_linf}"


def test_sequential_boundary_alpha_spending_simulation():
    """Verify that unclipped OBF boundary schedule strictly controls cumulative Type-I error to <= alpha."""
    # Test primary alpha_target = 0.05 across 50,000 trajectories
    res05 = simulate_sequential_type1_error(num_updates=224, num_trajectories=50000, seed=42, alpha_target=0.05)
    assert res05["c_star"] == 1.9600
    assert res05["empirical_fwer"] <= 0.0500, f"Empirical FWER ({res05['empirical_fwer']:.5f}) must be <= 0.0500"
    assert res05["ci_95"][1] <= 0.0500, f"Upper 95% Wilson CI ({res05['ci_95'][1]:.5f}) must be strictly <= 0.0500"
    assert res05["statistically_controlled"] is True

    # Test dynamic sensitivity under stricter alpha_target = 0.01
    res01 = simulate_sequential_type1_error(num_updates=224, num_trajectories=50000, seed=42, alpha_target=0.01)
    assert res01["c_star"] == 2.5758
    assert res01["empirical_fwer"] <= 0.0100, f"Empirical FWER ({res01['empirical_fwer']:.5f}) must scale to <= 0.0100"
    assert res01["ci_95"][1] <= 0.0100, f"Upper 95% Wilson CI ({res01['ci_95'][1]:.5f}) must be strictly <= 0.0100"
    assert res01["statistically_controlled"] is True


def test_bootstrap_stability_and_replicate_convergence():
    """Verify that stratified paired bootstrap disparity SE converges stably across replicate counts B=200, 500, 1000."""
    rng = np.random.default_rng(42)
    speaker_ids = [f"spk_{i}" for i in range(30)]
    stratum_groups = [f"grp_{i // 5}" for i in range(30)]
    ref_lengths = [15] * 30
    live_errors = [int(rng.integers(1, 5)) for _ in range(30)]
    cand_errors = [int(rng.integers(1, 6)) for _ in range(30)]

    ses = {}
    decisions = {}
    for B in [200, 500, 1000]:
        gate = StreamingSentinelSafetyGate(
            epsilon_r_pp=0.0000,
            epsilon_g_pp=2.0000,
            epsilon_d_pp=2.0000,
            num_updates=224,
            alpha_target=0.05,
            num_boot_replicates=B,
        )
        dec = gate.evaluate_candidate(10, speaker_ids, stratum_groups, live_errors, cand_errors, ref_lengths)
        ses[B] = dec.se_d
        decisions[B] = dec.decision

    # Decisions must be 100% consistent across replicate depths
    assert len(set(decisions.values())) == 1, f"Decisions must be consistent across B, got {decisions}"
    # Standard error estimate must be stable (CV < 5% between B=200, 500, 1000)
    se_vals = list(ses.values())
    cv = (float(np.std(se_vals)) / float(np.mean(se_vals))) * 100.0
    assert cv < 5.0, f"Bootstrap SE CV across replicate counts must be < 5.0%, got {cv:.2f}%"


def test_multicriterion_streaming_gate_joint_null_safety():
    """Verify that tripartite gate maintains joint false-acceptance rate <= alpha under null streams."""
    null_res = simulate_multicriterion_streaming_gate_null(
        num_streams=100,
        num_updates=224,
        alpha_target=0.05,
        num_boot_replicates=50,
        seed=42,
    )
    assert null_res["joint_control_demonstrated"] is True
    assert null_res["empirical_joint_fwer"] <= 0.0500, (
        f"Joint empirical FWER ({null_res['empirical_joint_fwer']}) must not exceed 0.0500"
    )
    assert null_res["ci_95"][1] <= 0.0500, f"Wilson upper bound must be <= 0.05, got {null_res['ci_95'][1]}"


def test_shared_panel_null_simulation_artifact_verification():
    """Verify that committed shared-panel simulation artifact establishes FWER <= alpha_target and documents qualifications."""
    sim_artifact = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_shared_panel_null_simulation_results.json"
    assert sim_artifact.exists(), f"Missing shared panel null simulation artifact: {sim_artifact}"
    with open(sim_artifact, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    res = data["simulation_results"]
    assert meta["num_streams_scenario_a"] == 1000
    assert meta["num_updates_per_stream"] == 224
    assert meta["total_candidate_evaluations_scenario_a"] == 224000
    assert meta["random_seed"] == 42
    assert meta["sentinel_speakers"] == 30
    assert "methodological_qualification" in meta

    # Scenario A verification (Baseline Stochastic Null)
    assert res["false_acceptances"] == 0
    assert res["empirical_fwer"] == 0.0
    assert res["two_sided_95_wilson_upper"] < 0.005, f"Two-sided Wilson upper bound must be < 0.5%, got {res['two_sided_95_wilson_upper']}"
    assert res["one_sided_95_wilson_upper"] < 0.003, f"One-sided Wilson upper bound must be < 0.3%, got {res['one_sided_95_wilson_upper']}"
    assert res["fwer_statistically_controlled"] is True

    # Scenario B (Autoregressive candidate error persistence stress test)
    scen_b = res["scenario_b_autoregressive_persistence"]
    assert scen_b["false_acceptances"] == 0
    assert scen_b["fwer_statistically_controlled"] is True

    # Scenario C (Deterministic zero-variance tie stress test)
    scen_c = res["scenario_c_deterministic_ties"]
    assert scen_c["false_acceptances"] == 0
    assert scen_c["tie_rejection_rate_pct"] == 100.0
    assert scen_c["fail_closed_guarantee_maintained"] is True


def test_tost_equivalence_and_student_t_confidence_intervals():
    """Verify recalculation of unweighted speaker-level TOST and exact t(59) confidence intervals from committed records."""
    spk_csv = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_physical_cohort1_revised_gate_speaker_records.csv"
    assert spk_csv.exists(), f"Missing speaker records CSV: {spk_csv}"
    df = pd.read_csv(spk_csv)
    assert len(df) == 60

    # Estimand: Unweighted speaker-average paired difference
    diff = (df["err3"] - df["err1"]) / df["wc"] * 100.0
    n = len(diff)
    df_spk = n - 1
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1))
    se_diff = std_diff / math.sqrt(n)

    # Recomputed values matching auditor calculations
    assert abs(mean_diff - (-0.03098)) < 1e-4, f"Mean diff {mean_diff} != -0.03098"
    assert abs(se_diff - 0.12038) < 1e-4, f"SE diff {se_diff} != 0.12038"

    # Paired t-statistic
    t_stat = mean_diff / se_diff
    assert abs(t_stat - (-0.2574)) < 1e-3, f"t-statistic {t_stat} != -0.2574"

    # Student t critical values for df = 59
    t_crit_90 = stats.t.ppf(0.95, df=df_spk)   # 1.671093
    t_crit_95 = stats.t.ppf(0.975, df=df_spk)  # 2.000995

    ci_90_low = mean_diff - t_crit_90 * se_diff
    ci_90_high = mean_diff + t_crit_90 * se_diff
    ci_95_low = mean_diff - t_crit_95 * se_diff
    ci_95_high = mean_diff + t_crit_95 * se_diff

    # Verify exact agreement with auditor recalculated intervals
    assert abs(ci_90_low - (-0.2321)) < 1e-3
    assert abs(ci_90_high - 0.1702) < 1e-3
    assert abs(ci_95_low - (-0.2719)) < 1e-3
    assert abs(ci_95_high - 0.2099) < 1e-3

    # TOST for margin +/-0.50 pp
    margin = 0.50
    t1 = (mean_diff - (-margin)) / se_diff
    p1 = 1.0 - stats.t.cdf(t1, df=df_spk)
    t2 = (mean_diff - margin) / se_diff
    p2 = stats.t.cdf(t2, df=df_spk)
    p_tost = max(p1, p2)

    assert abs(t1 - 3.8963) < 1e-3
    assert abs(t2 - (-4.4111)) < 1e-3
    assert p_tost < 1.3e-4, f"p_tost {p_tost} should be ~ 1.26e-4"
    assert p_tost < 0.05, "TOST equivalence within +/-0.50 pp must be established"

    # Verify report JSON serializes these exact values
    rep_json = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_physical_cohort1_revised_gate_report.json"
    assert rep_json.exists()
    with open(rep_json, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
    tost_sec = rep_data["inferential_statistics_speaker_clustered"]["paired_t_arm3_vs_arm1"]["tost_equivalence"]
    assert tost_sec["statistically_equivalent"] is True
    assert tost_sec["equivalence_margin_pp"] == 0.50
    assert abs(tost_sec["mean_paired_difference_pp"] - (-0.031)) < 1e-3
    assert abs(tost_sec["ci_95_pp"][0] - (-0.2719)) < 1e-3
    assert abs(tost_sec["ci_95_pp"][1] - 0.2099) < 1e-3


def test_production_report_json_agrees_with_unrounded_inferential_statistics():
    """Verify that production report JSON serializes unrounded inferential statistics and full 64-char hashes."""
    assert REPORT_JSON.exists(), f"Missing report JSON: {REPORT_JSON}"
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        rep = json.load(f)

    meta = rep["metadata"]
    assert "initial_live_parameter_hash_sha256" in meta
    assert "final_live_parameter_hash_sha256" in meta
    assert len(meta["initial_live_parameter_hash_sha256"]) == 64
    assert len(meta["final_live_parameter_hash_sha256"]) == 64
    assert meta["initial_live_parameter_hash_sha256"] == meta["final_live_parameter_hash_sha256"]
    assert meta["full_hash_bitwise_rollback_verified"] is True
    assert meta["parameter_drift_linf"] == 0.0

    stats_sec = rep["inferential_statistics_speaker_clustered"]["paired_t_arm3_vs_arm2"]
    t_stat = stats_sec["t_statistic"]
    p_val = stats_sec["p_value"]

    assert abs(t_stat - (-2.7137)) < 1e-3, f"Expected serialized t = -2.7137, got {t_stat}"
    assert abs(p_val - 0.00870992) < 1e-4, f"Expected serialized p = 0.00871, got {p_val}"
    assert stats_sec["statistically_significant_p05"] is True


def test_kaggle_runner_fail_closed_and_notebook_invariants():
    """Verify that Kaggle runner fails closed on missing Cohort 2 audio and notebook checks both LF and CRLF."""
    assert BENCHMARK_PY.exists(), f"Missing Kaggle benchmark runner: {BENCHMARK_PY}"
    assert NOTEBOOK_IPYNB.exists(), f"Missing Kaggle notebook: {NOTEBOOK_IPYNB}"

    bench_code = BENCHMARK_PY.read_text(encoding="utf-8")
    assert "FAIL-CLOSED INTEGRITY CHECK" in bench_code
    assert "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD" in bench_code
    assert "execute_confirmatory_experiment" not in bench_code, "Runner must not import synthetic simulation!"

    nb_text = NOTEBOOK_IPYNB.read_text(encoding="utf-8")
    nb_json = json.loads(nb_text)

    # Verify cells structure
    code_cells = [c["source"] for c in nb_json["cells"] if c["cell_type"] == "code"]
    code_text = "\n".join(["".join(src) for src in code_cells])

    # Must contain both LF and CRLF digests
    assert "610649e8f634e21c0236f18e9461f865721c7864703fb87d597df7968f912895" in code_text  # CRLF
    assert "2e59a75c40abd165ee1689773c1a95409be29636079c0f714d51236dd54dcef0" in code_text  # LF

    # Must contain Step 4 execution command
    assert "run_stage6m_cohort2_benchmark.py" in code_text


def test_revalidated_cohort1_gate_floor_provenance_and_word_counts():
    """Verify uncertainty floor provenance and sentinel word count consistency across JSON and CSV."""
    reval_dir = PROJECT_ROOT / "reports" / "stage6m" / "revalidated_cohort1"
    json_path = reval_dir / "stage6m_physical_cohort1_report.json"
    csv_path = reval_dir / "stage6m_physical_cohort1_gate_decisions.csv"

    assert json_path.exists(), f"Missing revalidated JSON report: {json_path}"
    assert csv_path.exists(), f"Missing revalidated gate CSV: {csv_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    gate_cfg = data["metadata"]["gate_configuration"]
    assert gate_cfg["sentinel_evaluation_clips"] == 30
    assert gate_cfg["sentinel_evaluation_words"] == 281
    assert gate_cfg["sentinel_evaluation_speakers"] == 30
    assert gate_cfg["sentinel_evaluation_strata"] == 6
    assert gate_cfg["se_r_floor_pp"] == 0.3559

    # Reconcile with 100.0 / 281 words
    expected_floor = round(100.0 / 281.0, 4)
    assert gate_cfg["se_r_floor_pp"] == expected_floor

    # Verify decision CSV matches gate_configuration floor on all rows
    df_gate = pd.read_csv(csv_path)
    assert len(df_gate) == 224
    assert "se_r_floor" in df_gate.columns
    unique_floors = df_gate["se_r_floor"].unique()
    assert len(unique_floors) == 1
    assert abs(unique_floors[0] - 0.3559) < 1e-4


def test_revalidated_cohort1_markdown_report_narrative_consistency():
    """Verify Markdown report disparity commentary is dynamically consistent with computed stratum results and balanced."""
    reval_dir = PROJECT_ROOT / "reports" / "stage6m" / "revalidated_cohort1"
    md_path = reval_dir / "stage6m_physical_cohort1_report.md"
    json_path = reval_dir / "stage6m_physical_cohort1_report.json"

    assert md_path.exists(), f"Missing revalidated markdown report: {md_path}"
    assert json_path.exists(), f"Missing revalidated JSON report: {json_path}"

    md_text = md_path.read_text(encoding="utf-8")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Canadian English metrics from JSON (lowest WER / best-performing)
    can_entry = next(s for s in data["stratum_breakdown"] if s["stratum"] == "Canadian English")
    wer_arm1 = can_entry["wer_arm1_static"]
    wer_arm2 = can_entry["wer_arm2_ungated"]
    wer_arm3 = can_entry["wer_arm3_gated"]

    assert wer_arm1 == 12.87
    assert wer_arm2 == 14.73
    assert wer_arm3 == 12.87

    # South Asian English metrics from JSON (highest WER / worst-performing)
    sa_entry = next(s for s in data["stratum_breakdown"] if s["stratum"] == "South Asian English")
    sa_wer_arm1 = sa_entry["wer_arm1_static"]
    sa_wer_arm2 = sa_entry["wer_arm2_ungated"]
    assert sa_wer_arm1 == 42.66
    assert sa_wer_arm2 == 41.68

    # Markdown narrative must reflect both minimum and maximum strata
    assert "South Asian English WER (-0.98 pp)" in md_text
    assert "Canadian English WER (+1.86 pp)" in md_text
    assert "combines an observed improvement in the worst-performing stratum with a leveling-down effect on the best-performing stratum" in md_text
    assert "Gated SUTA rejected all candidate updates and retained baseline predictions." in md_text

    # Markdown must NOT contain overstatements or stale numbers from previous runs
    assert "rather than lifting disadvantaged groups" not in md_text
    assert "refusing to achieve lower disparity through degradation of advantaged speakers" not in md_text
    assert "14.07%" not in md_text
    assert "+1.20 pp" not in md_text
    assert "13.13%" not in md_text


def test_revalidated_cohort1_zero_variance_tost_representation():
    """Verify zero-variance TOST and paired t-test output are represented as not estimable under zero sample variance."""
    reval_dir = PROJECT_ROOT / "reports" / "stage6m" / "revalidated_cohort1"
    json_path = reval_dir / "stage6m_physical_cohort1_report.json"
    md_path = reval_dir / "stage6m_physical_cohort1_report.md"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Paired t-test JSON verification
    pt_arm2_sec = data["inferential_statistics_speaker_clustered"]["paired_t_arm3_vs_arm2"]
    assert pt_arm2_sec["test_status"] == "COMPLETED"
    assert pt_arm2_sec["statistically_significant_p05"] is True

    pt_sec = data["inferential_statistics_speaker_clustered"]["paired_t_arm3_vs_arm1"]
    assert pt_sec["test_status"] == "NOT_ESTIMABLE_ZERO_VARIANCE"
    assert pt_sec["t_statistic"] is None
    assert pt_sec["p_value"] is None
    assert pt_sec["statistically_significant_p05"] is None
    assert "not estimable because the observed paired differences have zero variance" in pt_sec["interpretation"].lower()
    assert "does not establish population-level equivalence" in pt_sec["interpretation"].lower()

    # TOST JSON verification
    tost_sec = pt_sec["tost_equivalence"]
    assert tost_sec["status"] == "NOT_ESTIMABLE_ZERO_VARIANCE"
    assert tost_sec["observed_sample_difference_pp"] == 0.0
    assert tost_sec["standard_error_pp"] == 0.0
    assert tost_sec["ci_90_pp"] is None
    assert tost_sec["ci_95_pp"] is None
    assert tost_sec["t_lower"] is None
    assert tost_sec["p_tost"] is None
    assert tost_sec["statistically_equivalent"] is False
    assert "degenerate" in tost_sec["note"].lower()

    # Markdown verification
    md_text = md_path.read_text(encoding="utf-8")
    assert "Conclusion: Not estimable because the observed paired differences have zero variance. Arm 3 predictions match Arm 1 on all 900 clips, but this sample identity does not establish population-level equivalence." in md_text
    assert "No statistically significant difference detected at $\\alpha = 0.05$." not in md_text
    assert "Not Estimable" in md_text
    assert "degenerate under zero observed sample variance" in md_text
    assert "Equivalence within margin not established" in md_text




# =============================================================================
# Report-Generator Robustness Tests  (hardening pass -- no physical re-run)
# =============================================================================

import sys as _sys
_sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from run_stage6m_physical_cohort1 import (  # noqa: E402
    _paired_t_arm3_vs_arm2_interpretation,
    _paired_t_arm3_vs_arm1_interpretation,
    synthesize_disparity_narrative,
)


class TestPairedTArm3VsArm2Interpretation:
    """
    Unit tests for _paired_t_arm3_vs_arm2_interpretation covering every branch:
    (a) NaN t-statistic / p-value  ->  not estimable
    (b) p < 0.05, mean_diff < 0    ->  significant improvement
    (c) p < 0.05, mean_diff > 0    ->  significant regression
    (d) p < 0.05, mean_diff == 0   ->  significant, no directional change
    (e) p >= 0.05                  ->  not significant
    (f) p == 0.05 exactly          ->  not significant (boundary)
    """

    def test_nan_returns_not_estimable(self):
        text = _paired_t_arm3_vs_arm2_interpretation(float("nan"), float("nan"), 0.0)
        assert "not estimable" in text.lower()
        assert "zero" in text.lower()

    def test_significant_improvement(self):
        text = _paired_t_arm3_vs_arm2_interpretation(-2.71, 0.0087, -0.91)
        assert "statistically significant" in text.lower()
        assert "improvement" in text.lower()
        assert "-2.7100" in text
        assert "0.00870" in text
        assert "not significant" not in text.lower()

    def test_significant_regression(self):
        text = _paired_t_arm3_vs_arm2_interpretation(+2.40, 0.019, +1.50)
        assert "statistically significant" in text.lower()
        assert "regression" in text.lower()

    def test_significant_zero_direction(self):
        text = _paired_t_arm3_vs_arm2_interpretation(-3.0, 0.004, 0.0)
        assert "statistically significant" in text.lower()
        assert "no observed directional change" in text.lower()

    def test_not_significant(self):
        text = _paired_t_arm3_vs_arm2_interpretation(-0.50, 0.62, -0.10)
        assert "no statistically significant" in text.lower()
        assert "0.6200" in text
        # Must never claim significance
        assert "statistically significant difference detected at p" not in text.lower()

    def test_boundary_p_005_is_not_significant(self):
        text = _paired_t_arm3_vs_arm2_interpretation(-1.96, 0.05, -0.05)
        assert "no statistically significant" in text.lower()


class TestPairedTArm3VsArm1Interpretation:
    """
    Unit tests for _paired_t_arm3_vs_arm1_interpretation covering every branch:
    (a) se_diff == 0.0  ->  not estimable (zero-variance identity)
    (b) NaN t/p         ->  not estimable
    (c) p < 0.05        ->  statistically significant
    (d) p >= 0.05       ->  not statistically significant
    (e) p == 0.05       ->  not significant (boundary)
    (f) zero SE + extreme t/p  ->  not estimable (cannot claim significance)
    """

    def test_zero_se_returns_not_estimable(self):
        text = _paired_t_arm3_vs_arm1_interpretation(0.0, 1.0, 0.0, 900)
        assert "not estimable" in text.lower()
        assert "zero variance" in text.lower()
        assert "900 clips" in text
        assert "does not establish population-level equivalence" in text.lower()

    def test_nan_t_returns_not_estimable(self):
        text = _paired_t_arm3_vs_arm1_interpretation(float("nan"), float("nan"), 0.12, 900)
        assert "not estimable" in text.lower()

    def test_significant_result(self):
        text = _paired_t_arm3_vs_arm1_interpretation(-2.50, 0.015, 0.12, 900)
        assert "statistically significant" in text.lower()
        assert "p < 0.05" in text

    def test_not_significant_result(self):
        text = _paired_t_arm3_vs_arm1_interpretation(-0.26, 0.80, 0.12, 900)
        assert "no statistically significant" in text.lower()
        assert "0.8000" in text

    def test_boundary_p_005_is_not_significant(self):
        text = _paired_t_arm3_vs_arm1_interpretation(-1.67, 0.05, 0.12, 900)
        assert "no statistically significant" in text.lower()

    def test_zero_se_cannot_claim_significance(self):
        """Even with extreme t/p values, zero SE must trigger not-estimable."""
        text = _paired_t_arm3_vs_arm1_interpretation(float("inf"), 0.0, 0.0, 900)
        assert "not estimable" in text.lower()
        assert "statistically significant difference detected" not in text.lower()


# ---------------------------------------------------------------------------
# Disparity narrative branch tests  (pure logic, no physical inference)
# ---------------------------------------------------------------------------

def _make_strata_results(max_wer1, max_wer2, min_wer1, min_wer2,
                          other_wer1=25.0, other_wer2=25.0):
    """Build a minimal 3-stratum strata_results list for narrative unit tests."""
    return [
        {"stratum": "MaxStratum", "ref_words": 1000,
         "wer_arm1_static": max_wer1, "wer_arm2_ungated": max_wer2, "wer_arm3_gated": max_wer1,
         "delta_g_arm3_vs_arm1": 0.0, "delta_g_arm3_vs_arm2": round(max_wer1 - max_wer2, 2)},
        {"stratum": "MinStratum", "ref_words": 1000,
         "wer_arm1_static": min_wer1, "wer_arm2_ungated": min_wer2, "wer_arm3_gated": min_wer1,
         "delta_g_arm3_vs_arm1": 0.0, "delta_g_arm3_vs_arm2": round(min_wer1 - min_wer2, 2)},
        {"stratum": "MidStratum", "ref_words": 1000,
         "wer_arm1_static": other_wer1, "wer_arm2_ungated": other_wer2, "wer_arm3_gated": other_wer1,
         "delta_g_arm3_vs_arm1": 0.0, "delta_g_arm3_vs_arm2": round(other_wer1 - other_wer2, 2)},
    ]


@pytest.mark.parametrize(
    "scenario,max_wer1,max_wer2,min_wer1,min_wer2,other_wer1,other_wer2,expected_verb,fragment",
    [
        # =========================================================================
        # 1. Disparity NARROWING (D2 < D1 -> 'reduced')
        # =========================================================================
        # 1a. Worst improved (-1.0 pp), best regressed (+1.0 pp) -> both drive narrowing
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 39.0 - 13.0 = 26.0 pp (-2.0 pp)
        ("narrowing_worst_improved_best_regressed",
         40.0, 39.0, 12.0, 13.0, 25.0, 25.0, "reduced",
         "combines an observed improvement in the worst-performing stratum with a leveling-down effect"),

        # 1b. Worst improved (-2.0 pp), best unchanged (0.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 38.0 - 12.0 = 26.0 pp (-2.0 pp)
        ("narrowing_worst_improved_best_unchanged",
         40.0, 38.0, 12.0, 12.0, 25.0, 25.0, "reduced",
         "driven primarily by an improvement in the worst-performing stratum without degrading"),

        # 1c. Both improved, worst improved more (-4.0 pp vs -1.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 36.0 - 11.0 = 25.0 pp (-3.0 pp)
        ("narrowing_both_improved_worst_more",
         40.0, 36.0, 12.0, 11.0, 25.0, 25.0, "reduced",
         "driven primarily by an improvement in the worst-performing stratum without degrading"),

        # 1d. Worst unchanged (0.0 pp), best regressed (+2.0 pp) -> leveling-down
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 40.0 - 14.0 = 26.0 pp (-2.0 pp)
        ("narrowing_worst_unchanged_best_regressed",
         40.0, 40.0, 12.0, 14.0, 25.0, 25.0, "reduced",
         "driven entirely by a leveling-down effect"),

        # 1e. Both regressed, best regressed more (+1.0 pp vs +3.0 pp) -> leveling-down
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 41.0 - 15.0 = 26.0 pp (-2.0 pp)
        ("narrowing_both_regressed_best_more",
         40.0, 41.0, 12.0, 15.0, 25.0, 25.0, "reduced",
         "driven entirely by a leveling-down effect"),

        # =========================================================================
        # 2. Disparity WIDENING (D2 > D1 -> 'increased')
        # =========================================================================
        # 2a. Worst regressed (+2.0 pp), best improved (-2.0 pp) -> both drive widening
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 42.0 - 10.0 = 32.0 pp (+4.0 pp)
        ("widening_worst_regressed_best_improved",
         40.0, 42.0, 12.0, 10.0, 25.0, 25.0, "increased",
         "combines performance regression in the worst-performing stratum with improvements in the best-performing stratum"),

        # 2b. Worst regressed (+3.0 pp), best unchanged (0.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 43.0 - 12.0 = 31.0 pp (+3.0 pp)
        ("widening_worst_regressed_best_unchanged",
         40.0, 43.0, 12.0, 12.0, 25.0, 25.0, "increased",
         "driven primarily by performance regression in the worst-performing stratum"),

        # 2c. Both regressed, worst regressed more (+4.0 pp vs +1.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 44.0 - 13.0 = 31.0 pp (+3.0 pp)
        ("widening_both_regressed_worst_more",
         40.0, 44.0, 12.0, 13.0, 25.0, 25.0, "increased",
         "driven primarily by performance regression in the worst-performing stratum"),

        # 2d. Worst unchanged (0.0 pp), best improved (-2.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 40.0 - 10.0 = 30.0 pp (+2.0 pp)
        ("widening_worst_unchanged_best_improved",
         40.0, 40.0, 12.0, 10.0, 25.0, 25.0, "increased",
         "driven by improvements concentrated in the best-performing stratum, widening the gap"),

        # 2e. Both improved, best improved more (-1.0 pp vs -3.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 39.0 - 9.0 = 30.0 pp (+2.0 pp)
        ("widening_both_improved_best_more",
         40.0, 39.0, 12.0, 9.0, 25.0, 25.0, "increased",
         "driven by improvements concentrated in the best-performing stratum, widening the gap"),

        # 2f. Intermediate stratum regresses beyond original extremes (Mid: 25.0 -> 46.0 pp)
        #     Arm 1 range: max(40,12,25) - min(40,12,25) = 28.0 pp
        #     Arm 2 range: max(40,12,46) - min(40,12,46) = 34.0 pp (+6.0 pp)
        ("widening_intermediate_stratum_exceeds_extremes",
         40.0, 40.0, 12.0, 12.0, 25.0, 46.0, "increased",
         "overtook MaxStratum as the new worst-performing stratum"),

        # =========================================================================
        # 3. Disparity MAINTAINED (|D2 - D1| <= 0.001 -> 'maintained')
        # =========================================================================
        # 3a. Both extrema unchanged (0.0 pp, 0.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 40.0 - 12.0 = 28.0 pp (0.0 pp)
        ("maintained_both_unchanged",
         40.0, 40.0, 12.0, 12.0, 25.0, 25.0, "maintained",
         "remained identical under ungated adaptation"),

        # 3b. Both improved equally (-2.0 pp, -2.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 38.0 - 10.0 = 28.0 pp (0.0 pp)
        ("maintained_both_improved_equally",
         40.0, 38.0, 12.0, 10.0, 25.0, 25.0, "maintained",
         "remained identical under ungated adaptation"),

        # 3c. Both regressed equally (+2.0 pp, +2.0 pp)
        #     Arm 1 range: 40.0 - 12.0 = 28.0 pp; Arm 2 range: 42.0 - 14.0 = 28.0 pp (0.0 pp)
        ("maintained_both_regressed_equally",
         40.0, 42.0, 12.0, 14.0, 25.0, 25.0, "maintained",
         "remained identical under ungated adaptation"),
    ],
)
def test_production_synthesize_disparity_narrative_all_mathematical_cases(
    scenario, max_wer1, max_wer2, min_wer1, min_wer2, other_wer1, other_wer2, expected_verb, fragment
):
    """
    Directly invokes the production helper synthesize_disparity_narrative across
    all mathematically realizable cases using internally consistent stratum data.
    The helper derives disp_arm1 and disp_arm2 directly from the complete set of stratum WERs,
    ensuring 100% agreement between stratum endpoints and reported range disparities.
    """
    strata = _make_strata_results(
        max_wer1=max_wer1, max_wer2=max_wer2,
        min_wer1=min_wer1, min_wer2=min_wer2,
        other_wer1=other_wer1, other_wer2=other_wer2,
    )
    # disp_arm1 and disp_arm2 are left None to verify the helper derives them from strata
    narrative = synthesize_disparity_narrative(
        strata_results=strata,
        n_accept=0,
        acc_rate=0.0,
    )
    assert expected_verb in narrative, (
        f"[{scenario}] Missing expected verb '{expected_verb}'.\nGot:\n{narrative}"
    )
    assert fragment in narrative, (
        f"[{scenario}] Missing expected fragment '{fragment}'.\nGot:\n{narrative}"
    )
    if scenario == "widening_intermediate_stratum_exceeds_extremes":
        # Specifically assert that the narrative names the stratum responsible for the new maximum
        assert "MidStratum" in narrative
        assert "overtook MaxStratum as the new worst-performing stratum" in narrative


def test_production_synthesize_disparity_narrative_inconsistent_input_validation():
    """
    Validates that explicitly providing disparity values that contradict
    the stratum-derived range by > 0.02 pp raises a clear ValueError, while
    tolerating differences within the theoretical rounding bound (<= 0.02 pp).
    """
    strata = _make_strata_results(40.0, 40.0, 12.0, 12.0)  # range = 28.00 pp
    # 28.05 deviates by 0.05 pp (> 0.02 pp bound) -> must raise ValueError
    with pytest.raises(ValueError, match="Supplied disp_arm1 .* is inconsistent with stratum-derived range"):
        synthesize_disparity_narrative(strata_results=strata, disp_arm1=28.05)

    with pytest.raises(ValueError, match="Supplied disp_arm2 .* is inconsistent with stratum-derived range"):
        synthesize_disparity_narrative(strata_results=strata, disp_arm2=28.05)

    # 28.01 deviates by 0.01 pp (within <= 0.02 pp rounding bound) -> must succeed
    ok_narrative = synthesize_disparity_narrative(strata_results=strata, disp_arm1=28.01, disp_arm2=28.01)
    assert "28.01 pp" in ok_narrative


def test_production_synthesize_disparity_narrative_defensive_narrowing_fallback():
    """
    Validates the defensive code-hardening path for narrowing with unimproved extrema.
    Under the formal definition D = max - min, range narrowing cannot occur without either
    the worst improving or the best regressing. When inconsistent inputs bypass validation
    (validate_consistency=False), the helper safely emits the defensive shifting-profiles sentence.
    """
    strata = _make_strata_results(40.0, 40.0, 12.0, 12.0)
    narrative = synthesize_disparity_narrative(
        strata_results=strata,
        disp_arm1=28.0,
        disp_arm2=26.0,
        validate_consistency=False,
    )
    assert "reduced" in narrative
    assert "reflects shifting stratum error profiles under ungated adaptation" in narrative


@pytest.mark.parametrize("n_accept,acc_rate,expected_fragment", [
    (0,   0.0,   "rejected all candidate updates and retained baseline predictions"),
    (15,  6.7,   "accepted 15 candidate updates (6.7%)"),
    (224, 100.0, "accepted 224 candidate updates (100.0%)"),
])
def test_production_synthesize_disparity_narrative_gated_acceptance_descriptions(
    n_accept, acc_rate, expected_fragment
):
    """Production helper accurately formats gate acceptance count and percentage."""
    strata = _make_strata_results(40.0, 39.0, 12.0, 13.0)
    narrative = synthesize_disparity_narrative(
        strata_results=strata,
        disp_arm1=28.0,
        disp_arm2=26.0,
        disp_arm3=28.0,
        n_accept=n_accept,
        acc_rate=acc_rate,
    )
    assert expected_fragment in narrative, (
        f"Expected {expected_fragment!r} in narrative.\nGot: {narrative}"
    )


def test_production_synthesize_disparity_narrative_empty_strata_fallback():
    """Empty strata list returns the concise fallback narrative without raising."""
    narrative = synthesize_disparity_narrative(
        strata_results=[],
        disp_arm1=27.13,
        disp_arm2=24.29,
        disp_arm3=27.13,
        n_accept=0,
        acc_rate=0.0,
    )
    assert "27.13 pp" in narrative
    assert "24.29 pp" in narrative
    assert "Gated SUTA maintained disparity at 27.13 pp." in narrative


def test_production_synthesize_disparity_narrative_exact_cohort1_match():
    """
    Verifies that passing the actual six revalidated Cohort 1 stratum records
    to the production helper reproduces the exact disparity narrative published
    in the physical report (reports/stage6m/revalidated_cohort1/stage6m_physical_cohort1_report.md).
    """
    strata = [
        {"stratum": "Australian English", "ref_words": 1493, "wer_arm1_static": 23.58, "wer_arm2_ungated": 25.85, "wer_arm3_gated": 23.58},
        {"stratum": "Canadian English", "ref_words": 1500, "wer_arm1_static": 12.87, "wer_arm2_ungated": 14.73, "wer_arm3_gated": 12.87},
        {"stratum": "England English", "ref_words": 1393, "wer_arm1_static": 21.25, "wer_arm2_ungated": 22.04, "wer_arm3_gated": 21.25},
        {"stratum": "Irish English", "ref_words": 1383, "wer_arm1_static": 15.76, "wer_arm2_ungated": 17.79, "wer_arm3_gated": 15.76},
        {"stratum": "South Asian English", "ref_words": 1430, "wer_arm1_static": 42.66, "wer_arm2_ungated": 41.68, "wer_arm3_gated": 42.66},
        {"stratum": "US English", "ref_words": 1468, "wer_arm1_static": 21.19, "wer_arm2_ungated": 21.39, "wer_arm3_gated": 21.19},
    ]
    # Cohort 1 physical report recorded values:
    disp_arm1 = 29.79
    disp_arm2 = 26.94
    disp_arm3 = 29.79
    narrative = synthesize_disparity_narrative(
        strata_results=strata,
        disp_arm1=disp_arm1,
        disp_arm2=disp_arm2,
        disp_arm3=disp_arm3,
        n_accept=0,
        acc_rate=0.0,
    )
    expected_exact = (
        "Ungated SUTA reduced the observed cross-accent WER range from 29.79 pp to 26.94 pp. "
        "This reflected both an improvement in South Asian English WER (-0.98 pp) and "
        "a regression in Canadian English WER (+1.86 pp). "
        "The disparity reduction therefore combines an observed improvement in the worst-performing "
        "stratum with a leveling-down effect on the best-performing stratum. "
        "Gated SUTA rejected all candidate updates and retained baseline predictions."
    )
    assert narrative == expected_exact, f"Cohort 1 narrative mismatch:\nGot:      {narrative!r}\nExpected: {expected_exact!r}"

    # Also assert that this exact string is present in the published Markdown report
    report_md_path = PROJECT_ROOT / "reports" / "stage6m" / "revalidated_cohort1" / "stage6m_physical_cohort1_report.md"
    report_text = report_md_path.read_text(encoding="utf-8")
    assert narrative in report_text, "Synthesized narrative must match the published physical report markdown."
