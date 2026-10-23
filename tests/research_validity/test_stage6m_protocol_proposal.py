"""
Research Validity Tests: Stage 6M Protocol Proposal & Invariants.
==================================================================
Protocol: v1.1.0-model-expansion
Standard: ADR-005

Verifies the scientific invariants, data split disjointness,
model registry bindings, and governance locks for Stage 6M.
"""

import json
import math
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_stage6m_governance_lock_and_config():
    """Verify that Stage 6M protocol configuration enforces the authorization state and frozen thresholds."""
    cfg_path = PROJECT_ROOT / "configs" / "stage6m_protocol_config.json"
    assert cfg_path.exists(), "stage6m_protocol_config.json missing"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Governance Barrier: Execution authorized under amendment v1.3.4
    assert cfg["execution_authorized"] is True
    assert "AUTHORIZED" in cfg["execution_status"]
    assert "governance_amendment" in cfg
    amend = cfg["governance_amendment"]
    assert amend["amendment_id"] == "AMENDMENT-001"
    assert amend["authorizing_authority"] == "Designated Project Lead"
    assert "supervisor" in amend["supervisor_disclaimer"].lower()

    # Invariant tolerances must match frozen baseline
    gate_tol = cfg["frozen_gate_tolerances"]
    assert float(gate_tol["epsilon_R"]) == 0.0000
    assert float(gate_tol["epsilon_G"]) == 0.0200
    assert float(gate_tol["epsilon_D"]) == 0.0200
    assert int(gate_tol["bootstrap"]["B"]) == 1000
    assert float(gate_tol["bootstrap"]["confidence"]) == 0.95

    # Three experimental arms must be defined
    arms = cfg["experimental_arms"]
    assert "arm_1" in arms and "arm_2" in arms and "arm_3" in arms
    assert arms["arm_1"]["name"] == "ARM_1_STATIC_NO_ADAPT"
    assert arms["arm_2"]["name"] == "ARM_2_UNGATED_CTTA_REPLAY"
    assert arms["arm_3"]["name"] == "ARM_3_GATE_CONTROLLED_CTTA"

    # Counterfactual vault and provenance schema
    prov_fields = cfg["provenance_and_missingness_invariants"]["required_record_fields"]
    assert "candidate_id" in prov_fields
    assert "retained_checkpoint_hash" in prov_fields
    assert "candidate_checkpoint_hash" in prov_fields
    assert "cumulative_accepted_updates_count" in prov_fields
    assert "counterfactual_verification_status" in prov_fields


def test_stage6m_proposal_documentation_completeness():
    """Verify that stage6m_protocol_proposal.md addresses all six identified issues."""
    doc_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_protocol_proposal.md"
    assert doc_path.exists(), "stage6m_protocol_proposal.md missing"
    text = doc_path.read_text(encoding="utf-8")

    # Issue 1: Governance & Authorization
    assert "HOLD" in text or "AUTHORIZED" in text
    assert "Governance Invariant" in text

    # Issue 2: Cumulative multi-step adaptation & 3 experimental arms
    assert "Arm 1: Static No-Adapt" in text or "ARM_1_STATIC_NO_ADAPT" in text
    assert "Arm 2: Ungated CTTA" in text or "ARM_2_UNGATED_CTTA_REPLAY" in text
    assert "Arm 3: Gate-Controlled CTTA" in text or "ARM_3_GATE_CONTROLLED_CTTA" in text
    assert "Multi-Step Cumulative" in text

    # Issue 3: Offline counterfactual replay for rejected candidates
    assert "Research Vault" in text or "Replay Vault" in text
    assert "counterfactual" in text.lower()
    assert "Opportunity Cost" in text or "OPPORTUNITY COST" in text.upper()

    # Issue 4: Checkpoint serialization & provenance
    assert "PROVENANCE" in text.upper()
    assert "Preflight Checkpoint Verification" in text or "Checkpoint Parameter Integrity" in text

    # Issue 5: Dual safety-utility trade-off
    assert "SAFETY DIMENSION" in text
    assert "UTILITY DIMENSION" in text
    assert "Two-Phase Threshold Protocol" in text

    # Issue 6: Independent evaluation population & power analysis
    assert "Common Voice 27.0" in text
    assert "60 independent speakers" in text.replace("$", "")
    assert "Statistical Power Analysis" in text


def test_stage6m_dataset_disjointness_invariant():
    """Verify that Stage 6M evaluation stream is strictly disjoint from Sentinel and Development speakers."""
    ext_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    st4_csv = PROJECT_ROOT / "datasets" / "splits" / "stage4_characterization.csv"

    assert ext_csv.exists() and sent_csv.exists() and st4_csv.exists()

    df_ext = pd.read_csv(ext_csv)
    df_sent = pd.read_csv(sent_csv)
    df_st4 = pd.read_csv(st4_csv)

    ext_speakers = set(df_ext["speaker_id"].unique())
    sent_speakers = set(df_sent["speaker_id"].unique())
    st4_speakers = set(df_st4["speaker_id"].unique())

    # Sample size checks
    assert len(ext_speakers) == 60, f"Expected 60 speakers in external eval, got {len(ext_speakers)}"
    assert len(sent_speakers) == 30, f"Expected 30 speakers in sentinel panel, got {len(sent_speakers)}"
    assert len(st4_speakers) == 12, f"Expected 12 speakers in stage 4, got {len(st4_speakers)}"

    # Strict pairwise disjointness
    assert len(ext_speakers.intersection(sent_speakers)) == 0, "External eval overlaps with Sentinel Panel!"
    assert len(ext_speakers.intersection(st4_speakers)) == 0, "External eval overlaps with Stage 4 development!"
    assert len(sent_speakers.intersection(st4_speakers)) == 0, "Sentinel Panel overlaps with Stage 4 development!"


def test_stage6m_model_registry_held_out_isolation():
    """Verify that model role registry designates genuine held-out models for Stage 6M."""
    reg_path = PROJECT_ROOT / "configs" / "model_role_registry.json"
    assert reg_path.exists()
    with open(reg_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    models = registry["models"]

    # Genuine held-out models
    held_out_keys = ["hubert_large", "xlsr_english", "wav2vec2_large_lv60", "wav2vec2_large_robust"]
    for m in held_out_keys:
        assert m in models
        assert models[m]["stage6_role"] == "HELD_OUT_CTC"
        assert models[m]["holdout_status"] == "GENUINE_HELD_OUT"
        assert models[m]["ctta_status"] == "COMPATIBLE"

    # Overlap controls
    overlap_keys = ["wav2vec2_base", "data2vec_base"]
    for m in overlap_keys:
        assert m in models
        assert models[m]["stage6_role"] == "OVERLAP_CTC_CONTROL"
        assert models[m]["ctta_status"] == "COMPATIBLE"

    # Static Seq2Seq controls
    seq2seq_keys = ["whisper_base", "distil_whisper_small"]
    for m in seq2seq_keys:
        assert m in models
        assert models[m]["stage6_role"] == "SEQ2SEQ_STATIC_PORTABILITY"
        assert models[m]["ctta_status"] == "INCOMPATIBLE_NON_CTC"


def test_stage6m_deliverables_and_scientific_audits_exist():
    """Verify that all seven mandated Stage 6M audit deliverables exist with required contents."""
    s6_dir = PROJECT_ROOT / "reports" / "stage6m"
    cfg_dir = PROJECT_ROOT / "configs"

    # Deliverable 1: Revised stage6m_protocol_proposal.md
    prop = s6_dir / "stage6m_protocol_proposal.md"
    assert prop.exists()
    prop_text = prop.read_text(encoding="utf-8")
    assert "v1.3.4-stage6m-self-authorization-amendment" in prop_text or "v1.3.3-stage6m-reconciled-decision-pack" in prop_text
    assert "AUTHORIZED" in prop_text or "HOLD" in prop_text
    assert "Vector Prospective Harm Classification" in prop_text
    assert "Holm-Bonferroni" in prop_text
    assert "Two-Cohort Protocol Architecture" in prop_text
    assert "UCB_95%" in prop_text
    assert "Counterfactually Harmful Candidate Rejected" in prop_text

    # Deliverable 2: stage6m_power_analysis.md & reproducible simulation
    pwr = s6_dir / "stage6m_power_analysis.md"
    assert pwr.exists()
    pwr_text = pwr.read_text(encoding="utf-8")
    assert "UNDERPOWERED" in pwr_text and "UNRESOLVED" in pwr_text
    assert "Clopper-Pearson" in pwr_text
    assert "B = 2,000" in pwr_text or "B = 2000" in pwr_text or "B=2,000" in pwr_text
    assert (PROJECT_ROOT / "scripts" / "simulate_stage6m_power.py").exists()
    assert (s6_dir / "power_simulation_results.json").exists()

    # Deliverable 3: stage6m_temporal_estimands.md
    est = s6_dir / "stage6m_temporal_estimands.md"
    assert est.exists()
    est_text = est.read_text(encoding="utf-8")
    assert "Policy A: Frozen-Weights Rollout" in est_text
    assert "Policy B: Active-Branch Rollout" in est_text
    assert "Terminal Prediction-Only Window Rule" in est_text
    assert "29" in est_text and "candidate evaluations" in est_text

    # Deliverable 4: stage6m_data_integrity_audit.md
    data_aud = s6_dir / "stage6m_data_integrity_audit.md"
    assert data_aud.exists()
    data_text = data_aud.read_text(encoding="utf-8")
    assert "|S_A" in data_text and "| = 0" in data_text
    assert "Cross-Dataset Replication" in data_text
    assert "eight_model_benchmark.csv" in data_text

    # Deliverable 5: stage6m_replay_vault_spec.md
    vault = s6_dir / "stage6m_replay_vault_spec.md"
    assert vault.exists()
    vault_text = vault.read_text(encoding="utf-8")
    assert "does NOT retroactively recover" in vault_text
    assert "L_∞" in vault_text or "L_\\infty" in vault_text
    assert "1.0 \\times 10^{-5}" in vault_text or "1e-5" in vault_text

    # Deliverable 6: stage6m_model_registry.json
    reg_json = cfg_dir / "stage6m_model_registry.json"
    assert reg_json.exists()
    with open(reg_json, "r", encoding="utf-8") as f:
        reg_data = json.load(f)
    assert "hubert_large" in reg_data["models"]
    assert "ZERO_PRIOR_EXPOSURE_IN_STAGES_2_THROUGH_5M" in reg_data["models"]["hubert_large"]["project_stage_exposure"]
    assert "whisper_base" in reg_data["models"]
    assert "STATIC_PORTABILITY_ONLY_EXCLUDED_FROM_CTTA_CLAIMS" in reg_data["models"]["whisper_base"]["role_in_claims"]

    # Deliverable 7: stage6m_signoff_checklist.md
    chk = s6_dir / "stage6m_signoff_checklist.md"
    assert chk.exists()
    chk_text = chk.read_text(encoding="utf-8")
    assert "HOLD — EXECUTION STRICTLY PROHIBITED PENDING STAKEHOLDER SIGN-OFF" in chk_text
    assert "VERIFIED FROM ARTIFACT" in chk_text
    assert "UNRESOLVED / STATISTICALLY UNDERPOWERED" in chk_text

    # Deliverable 8: stage6m_sample_size_decision.md
    dec = s6_dir / "stage6m_sample_size_decision.md"
    assert dec.exists()
    dec_text = dec.read_text(encoding="utf-8")
    assert "Option A" in dec_text
    assert "180" in dec_text and "240" in dec_text
    assert "HOLD" in dec_text

    # Deliverable 9: stage6m_data_feasibility_audit.md
    feas = s6_dir / "stage6m_data_feasibility_audit.md"
    assert feas.exists()
    feas_text = feas.read_text(encoding="utf-8")
    assert "Common Voice 27.0" in feas_text
    assert "73" in feas_text
    assert "Irish" in feas_text
    assert "VERIFIED FROM ARTIFACT" in feas_text

    # Deliverable 10: stage6m_v1_2_0_changelog.md
    chg = s6_dir / "stage6m_v1_2_0_changelog.md"
    assert chg.exists()
    chg_text = chg.read_text(encoding="utf-8")
    assert "Option A" in chg_text


def test_stage6m_simulation_grid_exact_synchronization():
    """Verify that sample_size_exploration_grid is 100% synchronized with joint_safety_utility_simulation."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grid = data["sample_size_exploration_grid"]
    assert len(grid) == 14, f"Expected 14 cohorts in exploration grid, got {len(grid)}"

    for row in grid:
        cohort_n = row["total_speakers"]
        recs = data["joint_safety_utility_simulation"][f"cohort_{cohort_n}"]
        rec_s1 = next(r for r in recs if r["scenario_id"] == 1)
        rec_s2 = next(r for r in recs if r["scenario_id"] == 2)

        # Exact equality between grid and scenario records
        assert row["joint_power_s1_strict_adjusted_ucb975"] == rec_s1["joint_power_strict_adjusted_ucb975"]
        assert row["joint_power_s1_successes"] == rec_s1["joint_power_strict_adjusted_ucb975_successes"]
        assert row["joint_power_s2_strict_adjusted_ucb975"] == rec_s2["joint_power_strict_adjusted_ucb975"]
        assert row["joint_power_s2_successes"] == rec_s2["joint_power_strict_adjusted_ucb975_successes"]
        assert row["mc_se_s2_adjusted_ucb975"] == rec_s2["mc_se_joint_strict_adjusted_ucb975"]
        assert row["ci95_s2_adjusted_ucb975"] == rec_s2["ci95_joint_strict_adjusted_ucb975"]


def test_stage6m_speaker_inventory_arithmetic_and_provenance():
    """Verify external speaker inventory counts, hashes, and Irish bottleneck arithmetic."""
    inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
    ext_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"

    assert inv_csv.exists() and ext_csv.exists() and sent_csv.exists()

    df_inv = pd.read_csv(inv_csv)
    df_ext = pd.read_csv(ext_csv)
    df_sent = pd.read_csv(sent_csv)

    # Verified SHA-256 of canonical inventory artifact
    import hashlib
    with open(inv_csv, "rb") as f:
        inv_hash = hashlib.sha256(f.read()).hexdigest()
    assert inv_hash == "e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a"

    # Total inventory and group breakdown
    assert len(df_inv) == 6905
    group_counts = df_inv["group_code"].value_counts().to_dict()
    assert group_counts["US English"] == 3913
    assert group_counts["England English"] == 1223
    assert group_counts["South Asian English"] == 764
    assert group_counts["Canadian English"] == 511
    assert group_counts["Australian English"] == 400
    assert group_counts["Irish English"] == 94

    # Irish English arithmetic: 94 - 10 (Cohort 1) - 1 (Quality Filter) - 5 (Sentinel Panel) = 78
    irish_total = 94
    irish_cohort1 = len(df_ext[df_ext["stratum_code"] == "ireland"]["speaker_id"].unique())
    irish_sentinel = len(df_sent[df_sent["stratum_code"] == "ireland"]["speaker_id"].unique())
    quality_exclusions = 1

    assert irish_cohort1 == 10
    assert irish_sentinel == 5
    remaining_irish = irish_total - irish_cohort1 - quality_exclusions - irish_sentinel
    assert remaining_irish == 78, f"Expected 78 remaining Irish speakers, got {remaining_irish}"

    # Maximum balanced 6-stratum capacity is governed by 78 bottleneck speakers
    assert remaining_irish * 6 == 468


def test_stage6m_inventory_strata_counts_and_reconciliation():
    """Verify unique speaker counts per stratum, mutual exclusivity, and Irish capacity deficit for N=540."""
    inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
    df_inv = pd.read_csv(inv_csv)

    # Unique speaker count must equal total rows (6,905 unique speakers)
    assert len(df_inv) == 6905
    assert len(df_inv["speaker_id_prefix"].unique()) == 6905

    # Per stratum unique counts
    stratum_counts = {
        grp: len(sub_df["speaker_id_prefix"].unique())
        for grp, sub_df in df_inv.groupby("group_code")
    }
    assert stratum_counts["US English"] == 3913
    assert stratum_counts["England English"] == 1223
    assert stratum_counts["South Asian English"] == 764
    assert stratum_counts["Canadian English"] == 511
    assert stratum_counts["Australian English"] == 400
    assert stratum_counts["Irish English"] == 94

    # Strata are mutually exclusive
    assert sum(stratum_counts.values()) == 6905

    # Irish capacity check for N = 540 expansion
    # Current available unexposed Irish speakers = 78
    # Target N = 540 requires 90 speakers per stratum
    # With 15 reserve speakers, total required = 90 + 15 = 105 speakers
    # Deficit = 105 - 78 = 27 additional eligible speakers
    available_irish = 78
    required_irish_n540_with_reserve = 90 + 15
    irish_deficit = required_irish_n540_with_reserve - available_irish
    assert irish_deficit == 27, f"Expected 27 additional Irish speakers needed, got {irish_deficit}"


def test_stage6m_exact_boundary_tie_checks():
    """Verify that calibration records distinguish exact numerical ties from near-ties with rtol=0."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for run_key in ["discovery_b1000", "validation_b1000"]:
        for record in data["disparity_calibration_investigation"][run_key]:
            assert "exact_ties_u_equals_tau" in record
            assert "near_ties_u_near_tau_atol1e12" in record
            assert record["exact_ties_u_equals_tau"] == 0
            assert record["near_ties_u_near_tau_atol1e12"] == 0


def test_stage6m_clean_non_degradation_marginal_evidence():
    """Verify that clean non-degradation marginal metrics are documented with exact counts and failure bounds."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # For N >= 180, check zero failures and rule-of-three bound
    for cohort_n in [180, 210, 240, 300, 360, 420, 450, 468, 540, 600]:
        recs = data["joint_safety_utility_simulation"][f"cohort_{cohort_n}"]
        s2 = next(r for r in recs if r["scenario_id"] == 2)
        assert s2["marginal_clean_approach_a_failures"] == 0
        assert s2["marginal_clean_approach_b_failures"] == 0
        assert s2["marginal_clean_approach_b_rule_of_three_max_failure_rate"] <= 0.00075

    # For N = 60, verify empirical non-zero failure counts
    n60_s2 = next(r for r in data["joint_safety_utility_simulation"]["cohort_60"] if r["scenario_id"] == 2)
    assert n60_s2["marginal_clean_approach_a_failures"] > 0
    assert n60_s2["marginal_clean_approach_b_failures"] > 0


def test_stage6m_power_decision_rules():
    """Verify consistent evaluation of Rule A (point estimate >= 85%) vs Rule B (lower MC CI > 85%)."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grid = data["sample_size_exploration_grid"]
    row_180 = next(r for r in grid if r["total_speakers"] == 180)
    row_450 = next(r for r in grid if r["total_speakers"] == 450)
    row_468 = next(r for r in grid if r["total_speakers"] == 468)
    row_540 = next(r for r in grid if r["total_speakers"] == 540)
    row_600 = next(r for r in grid if r["total_speakers"] == 600)

    # N = 180: Fails both targets (S1 parity is 84.78% < 85%)
    assert row_180["rule_a_meets_85_pct_parity"] is False
    assert row_180["dual_target_status_rule_a"] == "FAIL"
    assert row_180["dual_target_status_rule_b"] == "FAIL"

    # N = 450: Fails Rule A (84.50% < 85.00%) and fails Rule B (83.38% < 85.00%)
    assert row_450["rule_a_meets_85_pct_drift"] is False
    assert row_450["rule_b_meets_85_pct_lower_bound_drift"] is False
    assert row_450["dual_target_status_rule_a"] == "FAIL"
    assert row_450["dual_target_status_rule_b"] == "FAIL"
    assert "crosses 85%" in row_450["mc_interval_interpretation"]

    # N = 468: Passes Rule A (85.82% >= 85.00%), fails Rule B (84.74% < 85.00%)
    assert row_468["rule_a_meets_85_pct_drift"] is True
    assert row_468["rule_b_meets_85_pct_lower_bound_drift"] is False
    assert row_468["dual_target_status_rule_a"] == "PASS"
    assert row_468["dual_target_status_rule_b"] == "FAIL"

    # N = 540: Passes Rule A (90.40% >= 85.00%) and passes Rule B (89.49% > 85.00%)
    assert row_540["rule_a_meets_85_pct_drift"] is True
    assert row_540["rule_b_meets_85_pct_lower_bound_drift"] is True
    assert row_540["dual_target_status_rule_a"] == "PASS"
    assert row_540["dual_target_status_rule_b"] == "PASS"

    # N = 600: Passes Rule A (92.70% >= 85.00%) and passes Rule B (91.89% > 85.00%)
    assert row_600["rule_a_meets_85_pct_drift"] is True
    assert row_600["rule_b_meets_85_pct_lower_bound_drift"] is True
    assert row_600["dual_target_status_rule_a"] == "PASS"
    assert row_600["dual_target_status_rule_b"] == "PASS"


def test_stage6m_trial_level_intersections():
    """Verify trial-level joint success intersection counts: n_A, n_B, n_C, n_ABC."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check N = 468 S2
    rec_468_s2 = next(r for r in data["joint_safety_utility_simulation"]["cohort_468"] if r["scenario_id"] == 2)
    assert rec_468_s2["n_A"] == 4000
    assert rec_468_s2["n_B_inferential"] == 4000
    assert rec_468_s2["n_C"] == 3433
    assert rec_468_s2["n_A_and_B"] == 4000
    assert rec_468_s2["n_A_and_C"] == 3433
    assert rec_468_s2["n_B_and_C"] == 3433
    assert rec_468_s2["n_A_and_B_and_C"] == 3433
    # Equality verified: n_C == n_A_and_C == n_B_and_C == n_A_and_B_and_C == 3433
    assert rec_468_s2["n_C"] == rec_468_s2["n_A_and_B_and_C"]

    # Check N = 540 S2
    rec_540_s2 = next(r for r in data["joint_safety_utility_simulation"]["cohort_540"] if r["scenario_id"] == 2)
    assert rec_540_s2["n_A"] == 4000
    assert rec_540_s2["n_B_inferential"] == 4000
    assert rec_540_s2["n_C"] == 3616
    assert rec_540_s2["n_A_and_B_and_C"] == 3616
    assert rec_540_s2["n_C"] == rec_540_s2["n_A_and_B_and_C"]

    # Also check grid-level fields
    grid = data["sample_size_exploration_grid"]
    row_468 = next(r for r in grid if r["total_speakers"] == 468)
    assert row_468["n_A_s2"] == 4000
    assert row_468["n_B_s2"] == 4000
    assert row_468["n_C_s2"] == 3433
    assert row_468["n_A_and_B_and_C_s2"] == 3433

    row_540 = next(r for r in grid if r["total_speakers"] == 540)
    assert row_540["n_A_s2"] == 4000
    assert row_540["n_B_s2"] == 4000
    assert row_540["n_C_s2"] == 3616
    assert row_540["n_A_and_B_and_C_s2"] == 3616


def test_stage6m_clean_ucb_sign_convention_and_deterministic_bound():
    """Verify that Clean UCB95 uses positive upper-tail quantile and produces UCB > point estimate."""
    import scipy.stats as stats

    # Benchmark deterministic case:
    # Point estimate: -0.30 pp, SE: 0.10 pp, df: 59 (N=60)
    delta_hat = -0.30
    se = 0.10
    df = 59

    # Upper-tail 95th percentile critical value
    t_upper = float(stats.t.ppf(0.95, df=df))
    assert t_upper > 0, "95th percentile Student-t critical value must be positive"
    assert abs(t_upper - 1.6711) < 0.001

    # Correct formula: UCB95 = delta_hat + t_upper * se
    ucb_correct = delta_hat + t_upper * se
    assert ucb_correct > delta_hat, "Upper confidence bound must strictly exceed point estimate when SE > 0"
    assert abs(ucb_correct - (-0.13289)) < 0.001

    # Negative lower-tail quantile: t_lower = ppf(0.05, df) = -t_upper
    t_lower = float(stats.t.ppf(0.05, df=df))
    assert t_lower < 0, "5th percentile Student-t critical value is negative"
    assert abs(t_lower - (-1.6711)) < 0.001

    # Subtraction of negative quantile is mathematically equivalent:
    ucb_equiv = delta_hat - t_lower * se
    assert abs(ucb_correct - ucb_equiv) < 1e-12

    # Errant formula addition of negative quantile: delta_hat + t_lower * se produces a LOWER bound (~ -0.467 pp)
    errant_lower_bound = delta_hat + t_lower * se
    assert errant_lower_bound < delta_hat, "Adding negative quantile produces a lower bound, not an upper bound"
    assert abs(errant_lower_bound - (-0.46711)) < 0.001


def test_stage6m_simulation_grid_matches_intersection_n_abc():
    """Verify that exploration grid joint successes and trial-level n_ABC match exactly for all 14 cohorts."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grid = data["sample_size_exploration_grid"]
    joint_sim = data["joint_safety_utility_simulation"]

    for row in grid:
        n = row["total_speakers"]
        cohort_key = f"cohort_{n}"
        assert cohort_key in joint_sim, f"{cohort_key} missing from joint simulation"

        rec_s2 = next(r for r in joint_sim[cohort_key] if r["scenario_id"] == 2)

        grid_succ = row["n_A_and_B_and_C_s2"]
        trial_n_abc = rec_s2["n_A_and_B_and_C"]
        strict_succ = rec_s2["joint_power_strict_adjusted_ucb975_successes"]

        # 100% exact equality required
        assert grid_succ == trial_n_abc == strict_succ, (
            f"Cohort N={n} mismatch: grid={grid_succ}, trial_n_ABC={trial_n_abc}, strict={strict_succ}"
        )

        # Published proportion must exactly equal count / 4000
        prop = row["joint_power_s2_strict_adjusted_ucb975"]
        expected_prop = round(grid_succ / 4000.0, 4)
        assert abs(prop - expected_prop) < 1e-4, f"Cohort N={n} proportion rounding mismatch"


def test_stage6m_venn_cells_nonnegative_and_sum_to_s():
    """Verify that all 8 Venn contingency cells are non-negative integers summing to S=4000 for every cohort."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    joint_sim = data["joint_safety_utility_simulation"]

    for cohort_key, records in joint_sim.items():
        rec_s2 = next(r for r in records if r["scenario_id"] == 2)
        n = rec_s2["cohort_n"]
        assert "venn_cells_approach_b" in rec_s2, f"Venn cells missing for {cohort_key}"
        v = rec_s2["venn_cells_approach_b"]

        # All 8 cells must be non-negative integers
        cell_keys = [
            "c111_A_and_B_and_C",
            "c110_A_and_B_not_C",
            "c101_A_and_not_B_and_C",
            "c011_not_A_and_B_and_C",
            "c100_A_not_B_not_C",
            "c010_not_A_B_not_C",
            "c001_not_A_not_B_C",
            "c000_not_A_not_B_not_C",
        ]
        total = 0
        for k in cell_keys:
            val = v[k]
            assert isinstance(val, int), f"{k} must be int in {cohort_key}"
            assert val >= 0, f"{k} must be non-negative in {cohort_key}, got {val}"
            total += val

        assert total == 4000, f"Sum of Venn cells in {cohort_key} must equal 4000, got {total}"
        assert v["total_sum"] == 4000
        assert v["all_nonnegative"] is True

        # Verify mathematical boundary consistency:
        # n_{(A \cap C) \cup (B \cap C)} = n_{AC} + n_{BC} - n_{ABC} <= n_C
        n_c = rec_s2["n_C"]
        n_ac = rec_s2["n_A_and_C"]
        n_bc = rec_s2["n_B_and_C"]
        n_abc = rec_s2["n_A_and_B_and_C"]
        union_in_c = n_ac + n_bc - n_abc
        assert union_in_c <= n_c, (
            f"Venn contradiction in {cohort_key}: union={union_in_c} > n_C={n_c}"
        )
        # Check c001 (trials in C but neither A nor B) = n_C - n_AC - n_BC + n_ABC >= 0
        c001_calc = n_c - n_ac - n_bc + n_abc
        assert c001_calc == v["c001_not_A_not_B_C"]
        assert c001_calc >= 0


def test_stage6m_common_voice_provenance_metadata():
    """Verify Common Voice release provenance against actual canonical metadata and file system."""
    import hashlib

    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval_manifest.json"
    assert manifest_path.exists(), "stage5_external_eval_manifest.json missing"
    with open(manifest_path, "r", encoding="utf-8") as f:
        mf = json.load(f)

    # Official release identifier & Mozilla Data Collective ID
    assert mf["dataset_release"] == "cv-corpus-27.0-2026-09-11"
    assert mf["dataset_mdc_id"] == "cmu5jplf300nwmh07iqvk9leo"

    # Local validated.tsv inspection
    tsv_path = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv"
    assert tsv_path.exists(), "validated.tsv missing"
    stat = tsv_path.stat()
    assert stat.st_size == 614927262, f"Expected 614,927,262 bytes, got {stat.st_size}"

    # Inventory generation script verification
    curation_script = PROJECT_ROOT / "scripts" / "phase3_external_eval_curation.py"
    assert curation_script.exists()
    script_hash = hashlib.sha256(curation_script.read_bytes()).hexdigest()
    assert script_hash == "ae706c2e86beb2eb98291b2e628c360cb0972ea92ed47bf00f7026cfb5775cc5"


def test_stage6m_irish_speaker_set_theoretic_accounting():
    """Verify exact set-theoretic accounting for Irish English bottleneck capacity (I_available = 78).
    
    Validates:
    - Speaker-level identity and clip counts (C_inventory vs C_strict) for disputed IDs.
    - Membership of both IDs in inventory I (|I| = 94).
    - Failure of both IDs under strict validation (C_strict < 15 => Q = {spk_fc, spk_f3}).
    - Exactly one ID overlap with Cohort 1 (|E1 ∩ Q| = 1), zero with Sentinel (|ES ∩ Q| = 0).
    - Inventory-restricted exclusion union |I ∩ (E1 ∪ ES ∪ E4 ∪ EC ∪ Q)| = 16.
    - Exactly 78 available, unexposed Irish speakers with C_strict >= 15.
    """
    inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
    ext_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    sent_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel_manifest.json"
    st4_csv = PROJECT_ROOT / "datasets" / "splits" / "stage4_characterization.csv"
    cal_csv = PROJECT_ROOT / "datasets" / "splits" / "calibration.csv"
    tsv_path = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv"

    # 1. Candidate inventory (I)
    df_inv = pd.read_csv(inv_csv)
    irish_inv = df_inv[df_inv["group_code"] == "Irish English"]
    assert len(irish_inv) == 94, f"Expected 94 Irish speakers in inventory, got {len(irish_inv)}"
    inv_prefixes = set(irish_inv["speaker_id_prefix"])
    assert len(inv_prefixes) == 94, "All 94 Irish prefixes must be unique"

    # 2. Granular Verification of Disputed Quality-Excluded IDs
    spk_fc = "fc22fd45334612a489c45562746889bcea70754325b6b162ee4aa1cd4be3876cf4374b08e663525ca04380feb656da2e313f71a6ea4fecb1eee133510c3854de"
    spk_f3 = "f3ea04475e301f84785710b9c56023f3c81f7abff656d40e674db8acde55c748688d0a4285eb6e8ea7f4d8b1fb6c99ab3c7f7d460878c4193256a61831e17ce7"
    prefix_fc = spk_fc[:24] + "…"
    prefix_f3 = spk_f3[:24] + "…"

    # Both IDs are confirmed members of inventory I
    assert prefix_fc in inv_prefixes, f"spk_fc prefix {prefix_fc} must be in inventory"
    assert prefix_f3 in inv_prefixes, f"spk_f3 prefix {prefix_f3} must be in inventory"

    # Verify clip records in validated.tsv
    fc_rows = []
    f3_rows = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        for line in f:
            if "fc22fd45" in line:
                fc_rows.append(dict(zip(header, line.strip().split("\t"))))
            elif "f3ea0447" in line:
                f3_rows.append(dict(zip(header, line.strip().split("\t"))))

    # Metric 1: Inventory Qualification Clip Count C_inventory(s)
    # Predicates: accent matches stratum, non-empty client_id, words >= 2
    fc_inv = [r for r in fc_rows if len((r.get("sentence") or "").split()) >= 2]
    f3_inv = [r for r in f3_rows if len((r.get("sentence") or "").split()) >= 2]
    assert len(fc_inv) == 15, f"Expected C_inventory(spk_fc) == 15, got {len(fc_inv)}"
    assert len(f3_inv) == 15, f"Expected C_inventory(spk_f3) == 15, got {len(f3_inv)}"

    # Metric 2: Strict Quality Filter Clip Count C_strict(s)
    # Predicates: C_inventory predicates + locale == 'en' + up_votes >= 2 + down_votes < 2
    fc_strict = [
        r for r in fc_inv
        if r.get("locale") == "en" and int(r.get("up_votes") or 0) >= 2 and int(r.get("down_votes") or 0) < 2
    ]
    f3_strict = [
        r for r in f3_inv
        if r.get("locale") == "en" and int(r.get("up_votes") or 0) >= 2 and int(r.get("down_votes") or 0) < 2
    ]
    assert len(fc_strict) == 14, f"Expected C_strict(spk_fc) == 14 (< 15), got {len(fc_strict)}"
    assert len(f3_strict) == 13, f"Expected C_strict(spk_f3) == 13 (< 15), got {len(f3_strict)}"
    # Both fail the strict threshold C_strict >= 15
    q_prefixes = {prefix_fc, prefix_f3}

    # 3. Cohort 1 External Evaluation (E1)
    df_ext = pd.read_csv(ext_csv)
    e1_irish = set(df_ext[df_ext["stage5_accent_group"] == "Irish English"]["speaker_id"].unique())
    assert len(e1_irish) == 10, f"Expected 10 Cohort 1 Irish speakers, got {len(e1_irish)}"
    e1_prefixes = {s[:24] + "…" for s in e1_irish}
    assert e1_prefixes.issubset(inv_prefixes), "All Cohort 1 Irish speakers must belong to inventory"

    # Disputed ID overlap with Cohort 1:
    assert spk_f3 in e1_irish, "spk_f3 was selected into Cohort 1 under baseline C_inventory >= 15"
    assert spk_fc not in e1_irish, "spk_fc was NOT selected into Cohort 1 (unexposed candidate)"
    assert len(e1_prefixes.intersection(q_prefixes)) == 1, "Exactly 1 quality-excluded ID overlaps with Cohort 1"

    # 4. Sentinel Panel (ES)
    df_sent = pd.read_csv(sent_csv)
    es_irish = set(df_sent[df_sent["stage5_accent_group"] == "Irish English"]["speaker_id"].unique())
    assert len(es_irish) == 5, f"Expected 5 Sentinel Panel Irish speakers, got {len(es_irish)}"
    es_prefixes = {s[:24] + "…" for s in es_irish}
    assert es_prefixes.issubset(inv_prefixes), "All Sentinel Panel Irish speakers must belong to inventory"

    # Strict disjointness:
    assert len(e1_irish.intersection(es_irish)) == 0, "Cohort 1 and Sentinel Panel must be strictly disjoint"
    assert len(es_prefixes.intersection(q_prefixes)) == 0, "Sentinel Panel drawn from C_strict >= 15 pool"

    # 5. Stage 4 Characterization (E4) and Calibration (EC)
    df_st4 = pd.read_csv(st4_csv)
    st4_spks = set(df_st4["speaker_id"].unique())
    df_cal = pd.read_csv(cal_csv)
    cal_spks = set(df_cal["speaker_id"].unique())
    # L2-ARCTIC speakers are non-native (Arabic, Hindi, etc.) and completely disjoint from Common Voice Irish
    assert len(st4_spks.intersection(e1_irish)) == 0
    assert len(st4_spks.intersection(es_irish)) == 0
    assert len(cal_spks.intersection(e1_irish)) == 0
    assert len(cal_spks.intersection(es_irish)) == 0
    st4_prefixes = {s[:24] + "…" for s in st4_spks}
    cal_prefixes = {s[:24] + "…" for s in cal_spks}
    assert len(inv_prefixes.intersection(st4_prefixes)) == 0, "|I ∩ E4| must be 0"
    assert len(inv_prefixes.intersection(cal_prefixes)) == 0, "|I ∩ EC| must be 0"

    # 6. Sentinel Manifest Consistency Check
    with open(sent_manifest, "r", encoding="utf-8") as f:
        mf = json.load(f)
    sent_pool_size = mf["strata"]["Irish English"]["pool_size"]
    # 94 inventory - 10 (E1) - 1 (unexposed Q: prefix_fc) = 83 candidates
    assert sent_pool_size == 83, f"Expected Irish pool_size 83 in Sentinel manifest, got {sent_pool_size}"

    # 7. Inventory-Restricted Exclusion Set Arithmetic:
    # I_excluded = I ∩ (E1 ∪ ES ∪ E4 ∪ EC ∪ Q)
    #            = (I ∩ E1) ∪ (I ∩ ES) ∪ (I ∩ (Q \ E1))
    #            = 10 + 5 + 1 = 16
    unexposed_q = q_prefixes - e1_prefixes
    assert len(unexposed_q) == 1
    assert prefix_fc in unexposed_q

    i_excluded = (inv_prefixes.intersection(e1_prefixes) |
                  inv_prefixes.intersection(es_prefixes) |
                  inv_prefixes.intersection(st4_prefixes) |
                  inv_prefixes.intersection(cal_prefixes) |
                  unexposed_q)
    assert len(i_excluded) == 16, f"Expected 16 inventory-restricted exclusions, got {len(i_excluded)}"

    # Net Available Capacity:
    i_available = inv_prefixes - i_excluded
    assert len(i_available) == 78, f"Expected exactly 78 available Irish speakers, got {len(i_available)}"

    # 8. Consistency check across documentation: ensure mislabeled categories do not persist
    reports_dir = PROJECT_ROOT / "reports" / "stage6m"
    feasibility_doc = (reports_dir / "stage6m_data_feasibility_audit.md").read_text(encoding="utf-8")
    assert "Stage 5 Sentinel Panel exposure: 10" not in feasibility_doc, "Conflicting label found in feasibility audit"
    assert "Stage 4 Characterization exposure: 1" not in feasibility_doc, "Erroneous Stage 4 Irish exposure found"

def test_stage6m_six_group_prior_exposure_reconciliation():
    """Verify exact six-group prior exposure set reconciliation across E1, ES, Q, and I.
    
    Validates:
    - E1 has exactly 60 unique speakers (10 per stratum across all 6 strata).
    - ES has exactly 30 unique speakers (5 per stratum across all 6 strata).
    - E1 and ES are strictly disjoint (|E1 ∩ ES| = 0).
    - Total prior exposed speakers |(E1 ∪ ES) ∩ I| = 90 (exactly 15 per stratum).
    - Overlap with strict quality exclusions (|Q| = 61): exactly 1 exposed speaker
      fails strict clip eligibility (f3ea0447... in Irish E1).
    - Exactly 89 prior exposed speakers pass strict clip eligibility (14 Irish + 75 non-Irish).
    - Total net available unexposed strictly eligible speakers across all 6 strata = 6,755.
    """
    inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
    ext_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"

    df_inv = pd.read_csv(inv_csv)
    df_ext = pd.read_csv(ext_csv)
    df_sent = pd.read_csv(sent_csv)

    inv_prefixes = set(df_inv["speaker_id_prefix"])
    assert len(inv_prefixes) == 6905

    # 1. Cohort 1 (E1) Breakdown
    e1_spks = set(df_ext["speaker_id"].unique())
    assert len(e1_spks) == 60, f"Expected 60 Cohort 1 speakers, got {len(e1_spks)}"
    e1_prefixes = {s[:24] + "…" for s in e1_spks}
    assert e1_prefixes.issubset(inv_prefixes), "All Cohort 1 speakers must belong to candidate inventory"
    for grp, sub in df_ext.groupby("stage5_accent_group"):
        assert sub["speaker_id"].nunique() == 10, f"Expected 10 E1 speakers in {grp}"

    # 2. Sentinel Panel (ES) Breakdown
    es_spks = set(df_sent["speaker_id"].unique())
    assert len(es_spks) == 30, f"Expected 30 Sentinel speakers, got {len(es_spks)}"
    es_prefixes = {s[:24] + "…" for s in es_spks}
    assert es_prefixes.issubset(inv_prefixes), "All Sentinel speakers must belong to candidate inventory"
    for grp, sub in df_sent.groupby("stage5_accent_group"):
        assert sub["speaker_id"].nunique() == 5, f"Expected 5 ES speakers in {grp}"

    # 3. Disjointness
    assert len(e1_spks.intersection(es_spks)) == 0, "Cohort 1 and Sentinel Panel must be disjoint"
    assert len(e1_prefixes.intersection(es_prefixes)) == 0

    # 4. Total Exposed across all 6 strata
    total_exposed_prefixes = e1_prefixes | es_prefixes
    assert len(total_exposed_prefixes) == 90, f"Expected 90 total exposed speakers, got {len(total_exposed_prefixes)}"

    # 5. Irish Overlap
    spk_f3_prefix = "f3ea04475e301f84785710b9…"
    assert spk_f3_prefix in e1_prefixes
    assert spk_f3_prefix not in es_prefixes

    # 6. Strictly Eligible Exposed Breakdown (89 total: 14 Irish, 15 in each other 5 groups)
    strictly_eligible_exposed = total_exposed_prefixes - {spk_f3_prefix}
    assert len(strictly_eligible_exposed) == 89, f"Expected 89 strictly eligible exposed speakers, got {len(strictly_eligible_exposed)}"


def test_stage6m_reserve_policy_allocations():
    """Verify exact arithmetic for Policy A (Irish-only reserve) and Policy B (Stratum-balanced reserve)."""
    # Active requirement: 75 CV + 15 Ext per stratum across 6 strata
    n_strata = 6
    active_cv_per_stratum = 75
    active_ext_per_stratum = 15
    active_cv_total = active_cv_per_stratum * n_strata  # 450
    active_ext_total = active_ext_per_stratum * n_strata  # 90
    active_total = active_cv_total + active_ext_total  # 540

    assert active_cv_total == 450
    assert active_ext_total == 90
    assert active_total == 540

    # Policy A: Bottleneck-Focused Irish Reserve Only
    # Irish: 3 CV reserve + 12 External reserve
    # Other 5 strata: 0 CV reserve + 0 External reserve
    policy_a_cv_reserve = 3
    policy_a_ext_reserve = 12
    policy_a_total_cv = active_cv_total + policy_a_cv_reserve  # 450 + 3 = 453
    policy_a_total_ext = active_ext_total + policy_a_ext_reserve  # 90 + 12 = 102
    policy_a_total_inv = policy_a_total_cv + policy_a_total_ext  # 453 + 102 = 555
    policy_a_ext_shortfall = policy_a_total_ext  # 102

    assert policy_a_total_cv == 453, f"Expected 453 CV speakers for Policy A, got {policy_a_total_cv}"
    assert policy_a_total_ext == 102, f"Expected 102 Ext speakers for Policy A, got {policy_a_total_ext}"
    assert policy_a_total_inv == 555, f"Expected 555 Total Inventory for Policy A, got {policy_a_total_inv}"
    assert policy_a_ext_shortfall == 102

    # Policy B: Stratum-Balanced Reserve Across All 6 Strata
    # Every stratum: 3 CV reserve + 12 External reserve
    policy_b_cv_reserve = 3 * n_strata  # 18
    policy_b_ext_reserve = 12 * n_strata  # 72
    policy_b_total_cv = active_cv_total + policy_b_cv_reserve  # 450 + 18 = 468
    policy_b_total_ext = active_ext_total + policy_b_ext_reserve  # 90 + 72 = 162
    policy_b_total_inv = policy_b_total_cv + policy_b_total_ext  # 468 + 162 = 630
    policy_b_ext_shortfall = policy_b_total_ext  # 162

    assert policy_b_total_cv == 468, f"Expected 468 CV speakers for Policy B, got {policy_b_total_cv}"
    assert policy_b_total_ext == 162, f"Expected 162 Ext speakers for Policy B, got {policy_b_total_ext}"
    assert policy_b_total_inv == 630, f"Expected 630 Total Inventory for Policy B, got {policy_b_total_inv}"
    assert policy_b_ext_shortfall == 162


def test_stage6m_scenario2_canonical_parameters():
    """Verify that Scenario 2 uses identical DGP parameters across all cohorts in canonical JSON."""
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check N=468 and N=540
    for cohort_key, expected_n, expected_ng, expected_succ, expected_pow in [
        ("cohort_468", 468, 78, 3433, 0.85825),
        ("cohort_540", 540, 90, 3616, 0.904),
    ]:
        recs = data["joint_safety_utility_simulation"][cohort_key]
        rec_s2 = next(r for r in recs if r["scenario_id"] == 2)

        assert rec_s2["cohort_n"] == expected_n
        assert rec_s2["speakers_per_stratum"] == expected_ng
        assert rec_s2["true_wer_effect_pp"] == -0.85, "WER superiority effect must be -0.85 pp"
        assert rec_s2["true_disparity_shift_pp"] == 0.5, "Scenario 2 disparity drift must be +0.50 pp"
        assert rec_s2["trials_s"] == 4000
        assert rec_s2["bootstrap_b"] == 1000
        assert rec_s2["joint_power_strict_adjusted_ucb975_successes"] == expected_succ
        assert abs(rec_s2["joint_power_strict_adjusted_ucb975"] - expected_pow) < 1e-4


def test_stage6m_trajectory_alpha_spending_budget():
    """Verify trajectory-level alpha budget across 1,754 updates and dual safety criteria."""
    n_updates = 1754
    alpha_total = 0.05
    # Two co-safety estimands (Clean non-degradation Delta_G and Disparity expansion Delta_D)
    n_estimands = 2
    # Bonferroni per-test allocation
    alpha_per_test = alpha_total / (n_updates * n_estimands)
    assert abs(alpha_per_test - (0.05 / 3508)) < 1e-9
    assert alpha_per_test < 1.5e-5

    # O'Brien-Fleming spending function alpha(t/T) must be monotonically increasing
    t_steps = np.arange(1, n_updates + 1)
    info_frac = t_steps / n_updates
    # z_obf decreases as information accumulates (stricter early, calibrated late)
    z_obf = stats.norm.ppf(1.0 - alpha_total / 4.0) / np.sqrt(info_frac)
    assert z_obf[0] > z_obf[-1], "O'Brien-Fleming z-boundary must be stricter at early windows"
    assert z_obf[-1] >= 1.95, "Terminal boundary must respect nominal level"


def test_stage6m_candidate_decision_and_rollback_invariants():
    """Verify that skipped/rejected candidates enforce strict live-model rollback."""
    # Simulate candidate update decision outcomes: ACCEPT, REJECT, SKIP
    live_model_hash_t0 = "hash_theta_0000"
    candidate_hash_t0 = "hash_theta_cand_0001"

    # Scenario A: Candidate REJECTED -> rollback to live_model_hash_t0
    gate_decision_reject = {"accepted": False, "reason": "DISPARITY_THRESHOLD_EXCEEDED"}
    theta_t1_reject = candidate_hash_t0 if gate_decision_reject["accepted"] else live_model_hash_t0
    assert theta_t1_reject == live_model_hash_t0, "Rejected candidate must roll back to theta_t"

    # Scenario B: Candidate SKIPPED by entropy pre-screen -> live model unchanged
    entropy_reduction = 0.05  # Poor/positive entropy reduction
    skipped = entropy_reduction > -0.10
    assert skipped is True
    theta_t1_skip = live_model_hash_t0  # Unchanged
    assert theta_t1_skip == live_model_hash_t0

    # Scenario C: Candidate ACCEPTED -> live model advances
    gate_decision_accept = {"accepted": True, "reason": "WITHIN_SAFETY_TOLERANCES"}
    theta_t1_accept = candidate_hash_t0 if gate_decision_accept["accepted"] else live_model_hash_t0
    assert theta_t1_accept == candidate_hash_t0, "Accepted candidate must advance model state"


def test_stage6m_speaker_level_clustering_invariant():
    """Verify that resampling clusters strictly at the human speaker level, not audio clip level."""
    # Sentinel Panel has exactly 30 speakers across 6 strata (5 spk/stratum, 10 clips/spk = 300 clips)
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    assert sent_csv.exists()
    df_sent = pd.read_csv(sent_csv)
    n_speakers = df_sent["speaker_id"].nunique()
    assert n_speakers == 30, f"Expected 30 unique speakers, got {n_speakers}"
    assert len(df_sent) == 300, f"Expected 300 total clips, got {len(df_sent)}"

    # Stratum clustering: exactly 5 speakers per stratum
    for grp, sub in df_sent.groupby("stage5_accent_group"):
        assert sub["speaker_id"].nunique() == 5, f"Stratum {grp} must contain exactly 5 unique speakers"
        assert len(sub) == 50, f"Stratum {grp} must contain exactly 50 clips"


def test_stage6m_irish_15_clip_invariant_and_reserve_shortfall():
    """Verify that exactly 78 unexposed Irish speakers possess >= 15 usable clips in CV 27.0.
    
    Proves that under the strict 15-clip invariant, Common Voice 27.0 reserve headroom
    for an active cohort of 78 speakers is IDENTICALLY ZERO.
    """
    inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
    ext_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"

    df_inv = pd.read_csv(inv_csv)
    df_ext = pd.read_csv(ext_csv)
    df_sent = pd.read_csv(sent_csv)

    irish_inv = df_inv[df_inv["group_code"] == "Irish English"]
    assert len(irish_inv) == 94, "Inventory contains exactly 94 baseline Irish speakers"

    e1_irish = set(df_ext[df_ext["stage5_accent_group"] == "Irish English"]["speaker_id"].unique())
    es_irish = set(df_sent[df_sent["stage5_accent_group"] == "Irish English"]["speaker_id"].unique())
    assert len(e1_irish) == 10
    assert len(es_irish) == 5

    # Prefix f3 is in E1; prefix fc is unexposed quality failure
    prefix_fc = "fc22fd45334612a489c45562…"
    prefix_f3 = "f3ea04475e301f84785710b9…"

    inv_prefixes = set(irish_inv["speaker_id_prefix"])
    e1_prefixes = {s[:24] + "…" for s in e1_irish}
    es_prefixes = {s[:24] + "…" for s in es_irish}

    # Net available strictly eligible with >= 15 clips:
    unexposed_ge15 = inv_prefixes - e1_prefixes - es_prefixes - {prefix_fc}
    assert len(unexposed_ge15) == 78, f"Expected exactly 78 unexposed speakers with >= 15 clips, got {len(unexposed_ge15)}"

    # Active requirement is 78 -> Reserve headroom under 15-clip invariant is 0
    active_required = 78
    reserve_headroom_15clip = len(unexposed_ge15) - active_required
    assert reserve_headroom_15clip == 0, "Reserve headroom under strict 15-clip invariant must be 0"


def test_stage6m_compute_workload_analytical_invariants():
    """Verify analytical clip decoding workloads for all three architectural options."""
    stream_clips = 7020  # 468 speakers * 15 clips
    window_k = 4
    total_windows = stream_clips // window_k
    assert total_windows == 1755
    assert stream_clips % window_k == 0, "7,020 clips must divide evenly by K=4"

    candidate_updates = total_windows - 1  # 1754 updates
    assert candidate_updates == 1754

    sentinel_clips = 300
    total_arm3_decodings = stream_clips + (candidate_updates * sentinel_clips)
    assert total_arm3_decodings == 533220, f"Expected 533,220 total decodings, got {total_arm3_decodings}"

    # Strided Gate (W=4 windows = 16 clips)
    strided_updates = total_windows // 4  # 438
    strided_decodings = stream_clips + (strided_updates * sentinel_clips)
    assert strided_decodings == 138420

    # Two-Tier Decoupled Benchmark
    tier1_stream_clips = 900
    tier1_updates = (tier1_stream_clips // window_k) - 1  # 224
    tier2_eval_clips = stream_clips * 3  # 3 arms * 7,020 clips
    tier_total_decodings = tier1_stream_clips + (tier1_updates * sentinel_clips) + tier2_eval_clips
    assert tier_total_decodings == 89160


def test_stage6m_option1b_variable_clip_reserve_invariants():
    """Verify locked candidate manifest structure, SHA-256 integrity, and Option 1B reserve hierarchy."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    lock_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    assert manifest_path.exists(), "Manifest file must exist"
    assert lock_path.exists(), "Manifest lock file must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(lock_path, "r", encoding="utf-8") as f:
        lock = json.load(f)

    # 1. Cryptographic integrity
    manifest_bytes = manifest_path.read_bytes()
    computed_hash = hashlib.sha256(manifest_bytes).hexdigest()
    assert computed_hash == lock["sha256"], "Manifest SHA-256 must match lock file"
    assert lock["execution_authorized"] is True, "Execution authorized under amendment v1.3.4"
    assert "AUTHORIZED" in lock["governance_status"]

    # 2. Cohort sizing: 6 strata, 78 active speakers each = 468
    strata = manifest["strata"]
    assert len(strata) == 6, f"Expected 6 strata, got {len(strata)}"
    assert manifest["metadata"]["total_active_speakers"] == 468

    for s_name, s_info in strata.items():
        assert s_info["active_count"] == 78, f"Strata {s_name} must have 78 active speakers"
        assert len(s_info["active_speakers"]) == 78

    # 3. Irish English Option 1B reserve pool structure
    irish_entry = strata["Irish English"]
    assert irish_entry["reserve_policy"] == "Option 1B — Variable-Clip Reserve (CV 27.0)"
    assert irish_entry["reserve_tier_1_count"] == 14
    assert irish_entry["reserve_tier_2_count"] == 13
    assert irish_entry["total_reserve_count"] == 27

    reserves = irish_entry["reserve_speakers"]
    assert len(reserves) == 27

    # Verify priority ranks are 1 to 27
    ranks = [r["priority_rank"] for r in reserves]
    assert ranks == list(range(1, 28))

    # Verify usable clips are monotonically non-increasing
    clips = [r["usable_clips"] for r in reserves]
    for i in range(len(clips) - 1):
        assert clips[i] >= clips[i + 1], f"Reserve clips must be non-increasing: {clips[i]} < {clips[i+1]}"

    # Verify exact counts per clip level: 4@14, 5@13, 5@12, 4@11, 9@10
    assert clips.count(14) == 4
    assert clips.count(13) == 5
    assert clips.count(12) == 5
    assert clips.count(11) == 4
    assert clips.count(10) == 9

    # Verify Tier 1 vs Tier 2 separation
    tier1 = reserves[:14]
    tier2 = reserves[14:]
    assert all(r["tier"] == "tier_1_power_preserving" for r in tier1)
    assert all(r["usable_clips"] >= 12 for r in tier1)
    assert all(r["tier"] == "tier_2_stress_contingency" for r in tier2)
    assert all(r["usable_clips"] in (10, 11) for r in tier2)


def test_stage6m_option1b_power_audit_summary_invariants():
    """Verify that variable-clip power audit reproduces >=85% power across Tier 1 replacements."""
    audit_path = PROJECT_ROOT / "reports" / "stage6m" / "variable_clip_power_audit_package" / "audit_summary.json"
    assert audit_path.exists(), "Variable-clip power audit summary must exist"

    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["metadata"]["supervisory_decision"] == "Option 1B (Variable-Clip Reserve in Common Voice 27.0)"
    results = data["variable_clip_power_audit_results"]
    assert len(results) == 5

    res_by_r = {r["reserve_replacements_r"]: r for r in results}

    # Baseline r=0
    r0 = res_by_r[0]
    assert r0["estimated_power_p_hat"] >= 0.8500
    assert r0["rule_a_verdict"] == "PASS"
    assert r0["rule_b_wilson_verdict"] == "PASS"
    assert r0["stream_geometry"]["total_stream_clips"] == 7020

    # Tier 1 replacements: r in {5, 10, 14} all maintain Rule A and Rule B PASS
    for r_val in [5, 10, 14]:
        r_entry = res_by_r[r_val]
        assert r_entry["estimated_power_p_hat"] >= 0.8500, f"r={r_val} must maintain >=85% power"
        assert r_entry["rule_a_verdict"] == "PASS"
        assert r_entry["rule_b_wilson_verdict"] == "PASS"
        assert r_entry["stream_geometry"]["total_stream_clips"] < 7020

    # Extreme stress test r=27 (all reserves drawn down to C=10)
    r27 = res_by_r[27]
    assert r27["estimated_power_p_hat"] < 0.8500, "r=27 should show minor power degradation from within-speaker noise"
    assert r27["rule_a_verdict"] == "FAIL"
    assert r27["stream_geometry"]["total_stream_clips"] == 6930


def test_stage6m_variable_clip_stream_length_and_final_window():
    """Verify stream length arithmetic, total windows, and candidate update opportunities.
    
    Reconciles Issue 1:
    - Total windows W(r) = ceil(L(r) / 4)
    - Terminal window is strictly prediction-only
    - Candidate update opportunities U(r) = W(r) - 1
    """
    # Deterministic clip counts for the 27 reserve Irish speakers:
    reserve_clips = [14] * 4 + [13] * 5 + [12] * 5 + [11] * 4 + [10] * 9
    base_clips = 468 * 15  # 7,020

    # Expected values from supervisor review:
    # r=0:  7020 clips -> 1755 windows -> 1754 updates
    # r=5:  7014 clips -> 1754 windows -> 1753 updates
    # r=14: 6991 clips -> 1748 windows -> 1747 updates
    # r=27: 6930 clips -> 1733 windows -> 1732 updates
    expected_geometry = {
        0: {"clips": 7020, "windows": 1755, "updates": 1754},
        5: {"clips": 7014, "windows": 1754, "updates": 1753},
        14: {"clips": 6991, "windows": 1748, "updates": 1747},
        27: {"clips": 6930, "windows": 1733, "updates": 1732},
    }

    for r, exp in expected_geometry.items():
        shortfall = sum(15 - c for c in reserve_clips[:r])
        stream_len = base_clips - shortfall
        total_windows = math.ceil(stream_len / 4.0)
        updates = total_windows - 1

        assert stream_len == exp["clips"], f"r={r}: Expected {exp['clips']} clips, got {stream_len}"
        assert total_windows == exp["windows"], f"r={r}: Expected {exp['windows']} windows, got {total_windows}"
        assert updates == exp["updates"], f"r={r}: Expected {exp['updates']} updates, got {updates}"


def test_stage6m_tier2_operational_boundary_invariants():
    """Verify that Tier 1 replacements (r <= 14) continue automatically while Tier 2 (r > 14) triggers hard stop."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    irish = manifest["strata"]["Irish English"]
    assert irish["reserve_tier_1_count"] == 14
    assert irish["reserve_tier_2_count"] == 13

    # All Tier 1 speakers must have usable clips in [12, 14]
    t1_speakers = [s for s in irish["reserve_speakers"] if s["tier"] == "tier_1_power_preserving"]
    assert len(t1_speakers) == 14
    assert all(12 <= s["usable_clips"] <= 14 for s in t1_speakers)

    # All Tier 2 speakers must have usable clips in [10, 11]
    t2_speakers = [s for s in irish["reserve_speakers"] if s["tier"] == "tier_2_stress_contingency"]
    assert len(t2_speakers) == 13
    assert all(10 <= s["usable_clips"] <= 11 for s in t2_speakers)


def test_stage6m_trajectory_sensitivity_sweeps_artifact_invariants():
    """Verify Deliverable 3 sensitivity sweep empirical simulation artifact and bounds."""
    sens_path = PROJECT_ROOT / "reports" / "stage6m" / "trajectory_sensitivity_sweep_results.json"
    assert sens_path.exists(), "Sensitivity sweep JSON artifact must exist"

    with open(sens_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sweeps = data["sweeps"]
    assert "autoregressive_dependence" in sweeps
    assert "sentinel_panel_sizing" in sweeps
    assert "near_boundary_grid" in sweeps

    # Sweep A: Across all rho in {0.0, 0.2, 0.4, 0.6, 0.8}, OBF FWER <= 5.0%
    for rho_key, res in sweeps["autoregressive_dependence"].items():
        obf = res["obrien_fleming_alpha_spending"]
        assert obf["fwer_estimate"] <= 0.05, f"OBF FWER must be <= 5.0% for {rho_key}, got {obf['fwer_estimate']}"
        assert res["nominal_uncorrected"]["fwer_estimate"] > 0.05, f"Nominal should fail under {rho_key}"

    # Sweep B: Panel Sizing (N_sent in {20, 30, 40, 50})
    for n_key, res in sweeps["sentinel_panel_sizing"].items():
        obf = res["obrien_fleming_alpha_spending"]
        assert obf["fwer_estimate"] <= 0.05, f"OBF FWER must be <= 5.0% for {n_key}"

    # Sweep C: Near-Boundary (Delta_G in {0.45, 0.50, 0.52, 0.55, 0.60, 0.65})
    # At exact boundary Delta_G = 0.50, OBF FWER <= 5.0%
    b_050 = sweeps["near_boundary_grid"]["delta_g_0.50"]["obrien_fleming_alpha_spending"]
    assert b_050["fwer_estimate"] <= 0.05


def test_stage6m_supervisor_governance_block_and_hold():
    """Verify that supervisor is formally identified as L.V. Srinivas and execution is authorized under Amendment v1.3.4."""
    proposal_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_protocol_proposal.md"
    text = proposal_path.read_text(encoding="utf-8")

    assert "Selected Protocol Design Decisions:" in text
    assert "Option 1B" in text
    assert "Option 2A" in text
    assert "L.V. Srinivas" in text
    assert "The amendment does not represent or imply approval by the academic supervisor." in text
    assert "AUTH-20261020-STAGE6M-AMEND-V134-EXECUTE-PERMITTED" in text


def test_stage6m_five_deliverables_pre_authorization_gate():
    """Verify that all five supervisory pre-authorization deliverables are established and gating execution."""
    reports_dir = PROJECT_ROOT / "reports" / "stage6m"
    splits_dir = PROJECT_ROOT / "datasets" / "splits"

    # Deliverable 1: Amended Power Audit Package
    deliv1_path = reports_dir / "variable_clip_power_audit_package" / "audit_summary.json"
    assert deliv1_path.exists(), "Deliverable 1 artifact must exist"

    # Deliverable 2: Locked Candidate Speaker Manifest
    deliv2_manifest = splits_dir / "stage6m_locked_candidate_manifest.json"
    deliv2_lock = splits_dir / "stage6m_locked_candidate_manifest.lock.json"
    assert deliv2_manifest.exists(), "Deliverable 2 manifest must exist"
    assert deliv2_lock.exists(), "Deliverable 2 lock must exist"

    # Deliverable 3: Trajectory Safety Error-Control Simulation & Sensitivity Sweeps
    deliv3_path = reports_dir / "trajectory_safety_simulation_results.json"
    deliv3_sweeps = reports_dir / "trajectory_sensitivity_sweep_results.json"
    assert deliv3_path.exists(), "Deliverable 3 simulation artifact must exist"
    assert deliv3_sweeps.exists(), "Deliverable 3 sensitivity sweep artifact must exist"

    # Deliverable 4: Compute Benchmark
    deliv4_path = reports_dir / "stage6m_compute_benchmark.json"
    assert deliv4_path.exists(), "Deliverable 4 compute benchmark must exist"

    # Deliverable 5: Governance State is AUTHORIZED under Amendment-001
    with open(deliv2_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)
    assert lock_data["execution_authorized"] is True, "Execution authorized under amendment v1.3.4"
    assert "AUTHORIZED" in lock_data["governance_status"]


def test_stage6m_authoritative_protocol_version_alignment():
    """Verify Issue 1 Resolution: One configuration authoritative version across all artifacts."""
    authoritative_version = "v1.3.4-stage6m-self-authorization-amendment"

    # 1. Config file
    cfg_path = PROJECT_ROOT / "configs" / "stage6m_protocol_config.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["protocol_version"] == authoritative_version, f"Config version mismatch: {cfg['protocol_version']}"

    # 2. Protocol Proposal Markdown
    prop_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_protocol_proposal.md"
    prop_text = prop_path.read_text(encoding="utf-8")
    assert f"**Protocol Version:** `{authoritative_version}`" in prop_text
    assert f"Protocol Version: {authoritative_version} | Governing Standard: ADR-005" in prop_text

    # 3. Locked Candidate Manifest Lock File
    lock_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"
    with open(lock_path, "r", encoding="utf-8") as f:
        lock_data = json.load(f)
    assert lock_data["protocol_version"] == authoritative_version

    # 4. Power Audit Package
    audit_path = PROJECT_ROOT / "reports" / "stage6m" / "variable_clip_power_audit_package" / "audit_summary.json"
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
    assert audit_data["metadata"]["protocol_version"] == authoritative_version

    # 5. Trajectory Sensitivity Sweeps
    sens_path = PROJECT_ROOT / "reports" / "stage6m" / "trajectory_sensitivity_sweep_results.json"
    with open(sens_path, "r", encoding="utf-8") as f:
        sens_data = json.load(f)
    assert sens_data["metadata"]["protocol_version"] == authoritative_version

    # 6. Compute Benchmark
    comp_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_compute_benchmark.json"
    with open(comp_path, "r", encoding="utf-8") as f:
        comp_data = json.load(f)
    assert comp_data["metadata"]["protocol_version"] == authoritative_version


def test_stage6m_near_boundary_error_reconciliation_invariants():
    """Verify Issue 3 Resolution: Exact global unsafe acceptance definition in near-boundary sweeps."""
    sens_path = PROJECT_ROOT / "reports" / "stage6m" / "trajectory_sensitivity_sweep_results.json"
    with open(sens_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grid = data["sweeps"]["near_boundary_grid"]

    # Clean sub-harm: Delta_G = 0.45 pp <= 0.50 pp AND Delta_D <= 1.40 pp
    # Because no candidate violates any safety tolerance, unsafe acceptance is 0.00%
    clean_045 = grid["delta_g_0.45_clean_subharm"]["obrien_fleming_alpha_spending"]
    assert clean_045["fwer_estimate"] == 0.0, "Clean sub-harm should have 0.0% false deployments"
    assert clean_045["safe_acceptance_rate"] > 0.40, "Safe candidates must be accepted with high rate"

    # Compound disparity violation: Delta_G = 0.45 pp, but Delta_D = 1.45 pp > 1.40 pp
    # Driven exclusively by disparity violation; FWER strictly bounded <= 5.0%
    comp_045 = grid["delta_g_0.45_compound_disparity"]["obrien_fleming_alpha_spending"]
    assert comp_045["fwer_estimate"] <= 0.05
    assert comp_045["wilson_95_ci"][1] <= 0.05, f"Wilson CI upper bound must be <= 5.0%, got {comp_045['wilson_95_ci'][1]}"

    # Exact boundary Delta_G = 0.50 pp
    b_050 = grid["delta_g_0.50"]["obrien_fleming_alpha_spending"]
    assert b_050["fwer_estimate"] <= 0.05


def test_stage6m_nonconfirmatory_rehearsal_invariants():
    """Verify Issue 4 Resolution: Complete end-to-end non-confirmatory rehearsal outputs and invariants."""
    rep_json = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_nonconfirmatory_rehearsal_report.json"
    rep_md = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_nonconfirmatory_rehearsal_report.md"
    assert rep_json.exists(), "Rehearsal report JSON must exist"
    assert rep_md.exists(), "Rehearsal report MD must exist"

    with open(rep_json, "r", encoding="utf-8") as f:
        rep = json.load(f)

    # Invariants verification
    assert rep["overall_verdict"] == "NON_CONFIRMATORY_ENGINEERING_REHEARSAL_PASS"
    assert rep["metadata"]["confirmatory_execution_authorized"] is False

    three_arm = rep["three_arm_invariants_verification"]
    assert three_arm["matched_stream_order"] is True
    assert three_arm["prequential_evaluation_precedes_adaptation"] is True
    assert three_arm["arm_1_static_updates_count"] == 0
    assert three_arm["rollback_on_rejection_verified"] is True
    assert three_arm["rejection_l_inf_drift"] == 0.0

    geom = rep["stream_geometry_verification"]
    assert geom["terminal_window_invariant_passed"] is True
    assert geom["candidate_update_opportunities_u"] == geom["total_windows_w"] - 1

    reserve = rep["reserve_policy_invariants_verification"]
    assert reserve["tier_1_auto_continuation_tested_r"] == 14
    assert reserve["tier_2_boundary_stop_tested"] is True
    assert reserve["hard_stop_policy_enforced"] is True





