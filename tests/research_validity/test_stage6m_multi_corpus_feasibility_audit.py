"""
tests/research_validity/test_stage6m_multi_corpus_feasibility_audit.py

Comprehensive Automated Test Suite for Stage 6M Multi-Corpus Feasibility Audit Utility
======================================================================================
Governing Standard: ADR-005
Protocol Reference: Protocol v1.4.0 (Confirmatory Decision Rule B)
Governance State: DRAFT_HOLD (Confirmatory Execution Strictly Blocked)
Authorization Standard: Protocol Section 14.7 (PROJECT_LEAD_ACADEMIC_AUTHORIZATION)

Test Coverage:
  1. Master Capacity Matrix Forensic Schema (all 10 required fields present per cell).
  2. Corpus Registry Coverage (Common Voice 27, EdAcc, VoxCeleb across 6 strata).
  3. VoxCeleb Methodological Inadmissibility (0 eligible speakers: no transcripts/dialect tags).
  4. EdAcc Sample Size Exhaustion (104 total speakers worldwide; <= 4 Irish speakers).
  5. Common Voice 27 Irish Historical Exposure Exhaustion (0 unexposed eligible remaining).
  6. Model-Matrix Rank & Connectivity Engine (DISCONNECTED_CONFOUNDED vs ORTHOGONAL_BALANCED).
  7. Interaction Model Identifiability & Cell Coverage Testing.
  8. Calibrated Stratified Cluster-Bootstrap Power Simulation Reproducibility & Monotonicity.
  9. Formal 5-Stratum Power Evaluation (Pathway 1 confirmatory feasibility).
  10. Fail-Closed Scientific Disposition (INFEASIBLE under Rule B; no silent downsampling).
  11. Governance Preservation Invariants (DRAFT_HOLD, confirmatory_execution=False).
  12. CLI Execution and JSON/Markdown Artifact Generation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage6m_multi_corpus_feasibility_audit import (
    CANDIDATE_CORPUS_PROFILES,
    CANONICAL_PROTOCOL_ACCENTS,
    FIVE_STRATUM_ACCENTS,
    REQUIRED_CELL_FIELDS,
    TARGET_COHORT3_SPEAKERS_PER_STRATUM,
    TARGET_GATE_SPEAKERS_PER_STRATUM,
    TOTAL_REQUIRED_PER_STRATUM,
    build_accent_by_corpus_matrix,
    evaluate_design_confounding,
    run_multi_corpus_feasibility_audit,
    simulate_hierarchical_power,
)


# ==============================================================================
# 1. Forensic Schema & Matrix Completeness Tests
# ==============================================================================


def test_capacity_matrix_schema_all_ten_dimensions_present():
    """Verify that every cell in the capacity matrix contains all 10 required forensic dimensions."""
    matrix_by_accent, matrix_by_corpus, independent_matrix = build_accent_by_corpus_matrix()

    for accent in CANONICAL_PROTOCOL_ACCENTS:
        assert accent in matrix_by_accent, f"Missing accent '{accent}' in matrix_by_accent"
        for c_id in ["CV27", "EdAcc", "VoxCeleb"]:
            assert c_id in matrix_by_accent[accent], f"Missing corpus '{c_id}' for accent '{accent}'"
            cell = matrix_by_accent[accent][c_id]
            for field in REQUIRED_CELL_FIELDS:
                assert field in cell, f"Cell [{accent}][{c_id}] missing required field '{field}'"
                assert cell[field] is not None, f"Cell [{accent}][{c_id}] field '{field}' is None"

            # Check integer non-negativity
            assert cell["raw_speakers"] >= 0
            assert cell["eligible_speakers"] >= 0
            assert cell["available_independent_speakers"] >= 0
            assert cell["historical_exposure"] >= 0
            assert cell["available_independent_speakers"] <= cell["eligible_speakers"]


def test_candidate_corpora_registry_coverage():
    """Verify all 6 canonical strata are evaluated for Common Voice, EdAcc, and VoxCeleb."""
    assert len(CANONICAL_PROTOCOL_ACCENTS) == 6
    assert TOTAL_REQUIRED_PER_STRATUM == 240
    assert TARGET_COHORT3_SPEAKERS_PER_STRATUM == 220
    assert TARGET_GATE_SPEAKERS_PER_STRATUM == 20

    registered_ids = {p["corpus_id"] for p in CANDIDATE_CORPUS_PROFILES.values()}
    assert "CV27" in registered_ids
    assert "EdAcc" in registered_ids
    assert "VoxCeleb" in registered_ids
    assert "OpenSLR83" in registered_ids
    assert "AusTalk" in registered_ids
    assert "IndicTIMIT" in registered_ids


# ==============================================================================
# 2. Candidate Corpus Specific Forensic Invariants
# ==============================================================================


def test_voxceleb_methodological_inadmissibility():
    """Verify VoxCeleb strictly evaluates to 0 eligible speakers due to missing transcripts and accent tags."""
    profile = CANDIDATE_CORPUS_PROFILES["VoxCeleb (VoxCeleb 1 & 2)"]
    assert "FATAL DEFECT" in profile["transcript_reliability"]
    assert "FATAL DEFECT" in profile["accent_label_source"]
    assert profile["provenance_status"] == "DOCUMENTED_ASSUMPTION_UNVERIFIED"

    for accent in CANONICAL_PROTOCOL_ACCENTS:
        cell = profile["strata_capacity"][accent]
        assert cell["eligible_speakers"] == 0, f"VoxCeleb must have 0 eligible speakers for {accent}"
        assert cell["available_independent_speakers"] == 0
        assert cell["status"] == "INADMISSIBLE_NO_TRANSCRIPTS"
        assert "lacks" in cell["exclusion_rationale"].lower() or "zero" in cell["exclusion_rationale"].lower()


def test_edacc_structural_sample_size_exhaustion():
    """Verify EdAcc contains only 104 speakers worldwide and cannot supply 240 speakers for any stratum."""
    profile = CANDIDATE_CORPUS_PROFILES["Edinburgh Accent Corpus (EdAcc)"]
    assert "104" in profile["speaker_id_confidence"]
    assert profile["provenance_status"] == "DOCUMENTED_ASSUMPTION_UNVERIFIED"

    irish_cell = profile["strata_capacity"]["Irish English"]
    assert irish_cell["raw_speakers"] == 4
    assert irish_cell["eligible_speakers"] == 3
    assert irish_cell["available_independent_speakers"] == 3
    assert irish_cell["status"] == "CRITICAL_DEFICIT"
    assert irish_cell["available_independent_speakers"] < TOTAL_REQUIRED_PER_STRATUM

    # All strata must fail the 240 requirement in EdAcc
    for accent in CANONICAL_PROTOCOL_ACCENTS:
        assert profile["strata_capacity"][accent]["available_independent_speakers"] < 20


def test_cv27_irish_exposure_zero_unexposed_capacity():
    """Verify Common Voice 27 has exactly 0 unexposed eligible Irish speakers remaining."""
    profile = CANDIDATE_CORPUS_PROFILES["Mozilla Common Voice 27.0"]
    assert profile["provenance_status"] == "EMPIRICALLY_VERIFIED_WORKSPACE_SCAN"
    irish_cell = profile["strata_capacity"]["Irish English"]

    assert irish_cell["raw_speakers"] == 220
    assert irish_cell["eligible_speakers"] == 92
    assert irish_cell["historical_exposure"] == 93
    assert irish_cell["available_independent_speakers"] == 0
    assert irish_cell["status"] == "EXHAUSTED_ZERO"

    # Verify surplus for other 5 strata
    for accent in FIVE_STRATUM_ACCENTS:
        assert profile["strata_capacity"][accent]["available_independent_speakers"] >= TOTAL_REQUIRED_PER_STRATUM
        assert profile["strata_capacity"][accent]["status"] == "SURPLUS"


# ==============================================================================
# 3. Model-Matrix Rank, Connectivity, and Confounding Tests
# ==============================================================================


def test_design_confounding_disconnected_patchwork():
    """Verify an uncrossed allocation matrix correctly evaluates to DISCONNECTED_CONFOUNDED via model matrix rank."""
    # Simulated patchwork: Irish from EdAcc only, others from CV27 only
    uncrossed_matrix = {
        "CV27": {
            "Australian English": 240,
            "Canadian English": 240,
            "England English": 240,
            "Irish English": 0,
            "South Asian English": 240,
            "US English": 240,
        },
        "EdAcc": {
            "Australian English": 0,
            "Canadian English": 0,
            "England English": 0,
            "Irish English": 3,
            "South Asian English": 0,
            "US English": 0,
        },
    }
    result = evaluate_design_confounding(uncrossed_matrix)
    assert result["confounding_verdict"] == "DISCONNECTED_CONFOUNDED"
    assert result["is_fully_crossed"] is False
    assert result["connected_components_count"] == 2  # Disconnected into 2 bipartite components
    # Max rank for 6 accents + 2 corpora = 6 + 2 - 1 = 7.
    # Disconnected into 2 components -> Rank = 6 + 2 - 2 = 6
    assert result["additive_model_rank"] == 6
    assert result["max_possible_additive_rank"] == 7
    assert result["additive_model_rank"] < result["max_possible_additive_rank"]
    assert "Irish English" in result["isolated_accents"]
    assert "linear model theory" in result["mathematical_collinearity_explanation"].lower()


def test_design_confounding_connected_unbalanced():
    """Verify a connected design with missing interaction cells evaluates to CONNECTED_UNBALANCED_NO_INTERACTION."""
    # Connected design: Corpus_A has 6 accents, Corpus_B has 3 accents -> connected (c=1), but K_obs < 12
    connected_unbalanced = {
        "Corpus_A": {acc: 100 for acc in CANONICAL_PROTOCOL_ACCENTS},
        "Corpus_B": {
            "Australian English": 50,
            "Canadian English": 50,
            "England English": 50,
            "Irish English": 0,
            "South Asian English": 0,
            "US English": 0,
        },
    }
    result = evaluate_design_confounding(connected_unbalanced)
    assert result["confounding_verdict"] == "CONNECTED_UNBALANCED_NO_INTERACTION"
    assert result["connected_components_count"] == 1
    assert result["additive_model_rank"] == 7
    assert result["max_possible_additive_rank"] == 7
    assert result["interaction_cells_observed"] == 9
    assert result["total_possible_interaction_cells"] == 12
    assert result["is_interaction_identifiable"] is False


def test_design_confounding_orthogonal_balanced():
    """Verify a balanced crossed allocation matrix evaluates to ORTHOGONAL_BALANCED with full rank."""
    balanced_matrix = {
        "Corpus_A": {acc: 110 for acc in CANONICAL_PROTOCOL_ACCENTS},
        "Corpus_B": {acc: 110 for acc in CANONICAL_PROTOCOL_ACCENTS},
    }
    result = evaluate_design_confounding(balanced_matrix)
    assert result["confounding_verdict"] == "ORTHOGONAL_BALANCED"
    assert result["is_fully_crossed"] is True
    assert result["connected_components_count"] == 1
    assert result["additive_model_rank"] == 7
    assert result["max_possible_additive_rank"] == 7
    assert result["is_interaction_identifiable"] is True
    assert result["is_strictly_orthogonal"] is True
    assert len(result["isolated_accents"]) == 0


# ==============================================================================
# 4. Hierarchical Power Simulation Tests
# ==============================================================================


def test_hierarchical_power_simulation_seed_reproducibility():
    """Verify that hierarchical power simulations with identical seeds produce bitwise identical results."""
    alloc = {
        "Corpus_A": {acc: 20 for acc in CANONICAL_PROTOCOL_ACCENTS},
        "Corpus_B": {acc: 20 for acc in CANONICAL_PROTOCOL_ACCENTS},
    }
    res1 = simulate_hierarchical_power(
        accents=CANONICAL_PROTOCOL_ACCENTS,
        allocation_matrix=alloc,
        n_clips_per_speaker=15,
        n_trials=50,
        n_bootstraps=30,
        random_seed=42,
    )
    res2 = simulate_hierarchical_power(
        accents=CANONICAL_PROTOCOL_ACCENTS,
        allocation_matrix=alloc,
        n_clips_per_speaker=15,
        n_trials=50,
        n_bootstraps=30,
        random_seed=42,
    )
    assert res1["power_results"]["joint_confirmatory_power"] == res2["power_results"]["joint_confirmatory_power"]
    assert res1["power_results"]["event_d_disparity_guard_power"] == res2["power_results"]["event_d_disparity_guard_power"]


def test_power_monotonicity_under_sample_size_rescaling():
    """
    Verify that joint confirmatory power severely drops as sample size is rescaled
    to match the Irish ceiling (Ng = 40 or 15), failing the 90% power target.
    """
    alloc_220 = {
        "Corpus_A": {acc: 110 for acc in CANONICAL_PROTOCOL_ACCENTS},
        "Corpus_B": {acc: 110 for acc in CANONICAL_PROTOCOL_ACCENTS},
    }
    alloc_40 = {
        "Corpus_A": {acc: 20 for acc in CANONICAL_PROTOCOL_ACCENTS},
        "Corpus_B": {acc: 20 for acc in CANONICAL_PROTOCOL_ACCENTS},
    }
    alloc_15 = {
        "Corpus_A": {acc: 8 for acc in CANONICAL_PROTOCOL_ACCENTS},
        "Corpus_B": {acc: 7 for acc in CANONICAL_PROTOCOL_ACCENTS},
    }

    res_220 = simulate_hierarchical_power(
        accents=CANONICAL_PROTOCOL_ACCENTS,
        allocation_matrix=alloc_220,
        n_clips_per_speaker=15,
        n_trials=100,
        n_bootstraps=40,
        random_seed=20261030,
    )
    res_40 = simulate_hierarchical_power(
        accents=CANONICAL_PROTOCOL_ACCENTS,
        allocation_matrix=alloc_40,
        n_clips_per_speaker=15,
        n_trials=100,
        n_bootstraps=40,
        random_seed=20261030,
    )
    res_15 = simulate_hierarchical_power(
        accents=CANONICAL_PROTOCOL_ACCENTS,
        allocation_matrix=alloc_15,
        n_clips_per_speaker=15,
        n_trials=100,
        n_bootstraps=40,
        random_seed=20261030,
    )

    p_220 = res_220["power_results"]["joint_confirmatory_power"]
    p_40 = res_40["power_results"]["joint_confirmatory_power"]
    p_15 = res_15["power_results"]["joint_confirmatory_power"]

    # Monotonic degradation as sample size shrinks
    assert p_220 > p_40 >= p_15
    assert p_40 < 0.90, f"Ng=40 must fail 90% target under cluster bootstrap, got {p_40}"


def test_five_stratum_pathway_1_power_simulation():
    """
    Verify that the 5-stratum single-corpus design achieves high superiority and regression
    guard power, while confirming that under protocol-exact Bonferroni inference (M=8, 99.375% UCB),
    joint power LCB does not reach 90%, thereby retaining DRAFT_HOLD governance status.
    """
    alloc_5s = {
        "CV27": {acc: 220 for acc in FIVE_STRATUM_ACCENTS},
    }
    res_5s = simulate_hierarchical_power(
        accents=FIVE_STRATUM_ACCENTS,
        allocation_matrix=alloc_5s,
        n_clips_per_speaker=15,
        n_trials=100,
        n_bootstraps=40,
        random_seed=20261030,
    )
    assert res_5s["simulation_parameters"]["evaluated_accents_count"] == 5
    assert res_5s["simulation_parameters"]["total_speakers"] == 1100
    assert res_5s["simulation_parameters"]["m_simultaneous_hypotheses"] == 8
    assert res_5s["simulation_parameters"]["simultaneous_ucb_percentile"] == 99.375
    assert "Protocol-exact" in res_5s["simulation_parameters"]["inference_procedure"]

    assert res_5s["power_results"]["event_a_static_superiority_power"] >= 0.95
    assert res_5s["power_results"]["event_b_suta_superiority_power"] >= 0.95
    assert res_5s["power_results"]["event_c_accent_regression_guard_power"] >= 0.95
    assert "target_90_power_achieved" in res_5s["power_results"]
    assert "lcb_90_power_achieved" in res_5s["power_results"]
    # Pathway 1 joint power LCB fails 90% target, justifying DRAFT_HOLD
    assert res_5s["power_results"]["lcb_90_power_achieved"] is False


def test_protocol_exact_inference_parameters_and_multiplicity():
    """
    Verify protocol-exact multiplicity adjustment (M = 2 + n_accents + 1)
    and Bonferroni simultaneous UCB percentile calculation for 6-stratum and 5-stratum designs.
    """
    # 6-stratum design: M = 2 + 6 + 1 = 9 hypotheses
    alloc_6s = {"Corpus_A": {acc: 10 for acc in CANONICAL_PROTOCOL_ACCENTS}}
    res_6s = simulate_hierarchical_power(
        accents=CANONICAL_PROTOCOL_ACCENTS,
        allocation_matrix=alloc_6s,
        n_clips_per_speaker=5,
        n_trials=20,
        n_bootstraps=10,
        random_seed=42,
    )
    sim_params_6s = res_6s["simulation_parameters"]
    assert sim_params_6s["m_simultaneous_hypotheses"] == 9
    assert abs(sim_params_6s["adj_alpha_per_hypothesis"] - (0.05 / 9.0)) < 1e-6
    assert abs(sim_params_6s["simultaneous_ucb_percentile"] - (100.0 * (1.0 - 0.05 / 9.0))) < 1e-4

    # 5-stratum design: M = 2 + 5 + 1 = 8 hypotheses
    alloc_5s = {"Corpus_A": {acc: 10 for acc in FIVE_STRATUM_ACCENTS}}
    res_5s = simulate_hierarchical_power(
        accents=FIVE_STRATUM_ACCENTS,
        allocation_matrix=alloc_5s,
        n_clips_per_speaker=5,
        n_trials=20,
        n_bootstraps=10,
        random_seed=42,
    )
    sim_params_5s = res_5s["simulation_parameters"]
    assert sim_params_5s["m_simultaneous_hypotheses"] == 8
    assert abs(sim_params_5s["adj_alpha_per_hypothesis"] - (0.05 / 8.0)) < 1e-6
    assert abs(sim_params_5s["simultaneous_ucb_percentile"] - 99.375) < 1e-4

    # Confidence interval bounds validity
    ci_low, ci_high = res_6s["power_results"]["joint_power_95_ci"]
    jp = res_6s["power_results"]["joint_confirmatory_power"]
    assert 0.0 <= ci_low <= jp <= ci_high <= 1.0


# ==============================================================================
# 5. Scientific Feasibility Disposition & Governance Tests
# ==============================================================================


def test_scientific_feasibility_disposition_invariants():
    """Verify the overall disposition is strictly INFEASIBLE under Decision Rule B."""
    audit = run_multi_corpus_feasibility_audit(PROJECT_ROOT, n_trials=50, n_bootstraps=20, random_seed=123)

    assert audit["overall_disposition"] in ["FEASIBLE", "CONDITIONALLY_FEASIBLE", "INFEASIBLE"]
    assert audit["overall_disposition"] == "INFEASIBLE"
    assert audit["governance_status"] == "DRAFT_HOLD"
    assert audit["authorization_standard"] == "Protocol Section 14.7 (PROJECT_LEAD_ACADEMIC_AUTHORIZATION)"
    assert audit["confirmatory_execution_authorized"] is False

    # Check provenance ledger fields
    prov = audit["audit_script_provenance"]
    assert "script_sha256" in prov
    assert len(prov["git_commit_sha"]) == 40
    assert "git_working_tree_clean" in prov

    # Check shortfall in summary
    irish_sum = audit["stratum_capacity_summary"]["Irish English"]
    assert irish_sum["status"] == "CRITICAL_SHORTFALL"
    assert irish_sum["shortfall"] > 200
    assert irish_sum["total_available_across_all_corpora"] <= 20


def test_governance_approval_record_preservation():
    """Verify governance record preserves DRAFT_HOLD, frozen commit, and code digest."""
    gov_file = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_v1_4_governance_approval_record.json"
    assert gov_file.exists(), f"Missing governance approval record at {gov_file}"

    with open(gov_file, "r", encoding="utf-8") as f:
        gov = json.load(f)

    assert gov["governance_status"] == "DRAFT_HOLD"
    assert gov["frozen_code_commit_sha"].startswith("a7a3b79")
    assert gov["frozen_code_digest"] == "8bec4fe8634474a243110753da182eab578460c66681b4eec38bc4dd70fcbce6"
    assert gov["authorization_mode"] == "PROJECT_LEAD_ACADEMIC_AUTHORIZATION"


def test_cli_execution_generates_reports(tmp_path):
    """Verify CLI execution generates valid JSON and Markdown reports with provenance."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "stage6m_multi_corpus_feasibility_audit.py"),
        "--reports-dir",
        str(tmp_path),
        "--trials",
        "20",
        "--bootstraps",
        "15",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert res.returncode == 0
    assert "MULTI-CORPUS AUDIT DISPOSITION: INFEASIBLE" in res.stdout

    json_path = tmp_path / "stage6m_multi_corpus_feasibility_report.json"
    md_path = tmp_path / "stage6m_multi_corpus_feasibility_report.md"

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["overall_disposition"] == "INFEASIBLE"
    assert data["governance_status"] == "DRAFT_HOLD"
    assert "audit_script_provenance" in data
    assert "pathway_1_five_stratum_confirmatory_n1100" in data["hierarchical_power_simulations"]

    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    assert "# Stage 6M Confirmatory Study — Multi-Corpus Feasibility" in md
    assert "`INFEASIBLE`" in md
    assert "Pathway 1: 5-Stratum Confirmatory" in md
