"""
tests/research_validity/test_stage6m_multi_corpus_feasibility_audit.py

Comprehensive Automated Test Suite for Stage 6M Multi-Corpus Feasibility Audit Utility
======================================================================================
Governing Standard: ADR-005
Protocol Reference: Protocol v1.4.0 (Confirmatory Decision Rule B)
Governance State: DRAFT_HOLD (Confirmatory Execution Strictly Blocked)

Test Dimensions:
  1. Master Capacity Matrix Forensic Schema (all 10 required fields present per cell).
  2. Corpus Registry Coverage (Mozilla Common Voice 27, EdAcc, VoxCeleb across 6 strata).
  3. VoxCeleb Methodological Inadmissibility (0 eligible speakers: no transcripts/dialect tags).
  4. EdAcc Sample Size Exhaustion (104 total speakers worldwide; <= 4 Irish speakers).
  5. Common Voice 27 Irish Historical Exposure Exhaustion (0 unexposed eligible remaining).
  6. Design Confounding & Collinearity Detection (uncrossed vs orthogonal crossed designs).
  7. Hierarchical Multi-Level Power Simulation Reproducibility & Monotonicity.
  8. Fail-Closed Scientific Disposition (INFEASIBLE under Rule B; no silent downsampling).
  9. Governance Preservation Invariants (DRAFT_HOLD, confirmatory_execution=False).
  10. CLI Execution and JSON/Markdown Artifact Generation.
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
    REQUIRED_CELL_FIELDS,
    TARGET_COHORT3_SPEAKERS_PER_STRATUM,
    TARGET_GATE_SPEAKERS_PER_STRATUM,
    TOTAL_REQUIRED_PER_STRATUM,
    build_accent_by_corpus_matrix,
    evaluate_design_confounding,
    run_multi_corpus_feasibility_audit,
    simulate_hierarchical_multicorpus_power,
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


# ==============================================================================
# 2. Candidate Corpus Specific Forensic Invariants
# ==============================================================================


def test_voxceleb_methodological_inadmissibility():
    """Verify VoxCeleb strictly evaluates to 0 eligible speakers due to missing transcripts and accent tags."""
    profile = CANDIDATE_CORPUS_PROFILES["VoxCeleb (VoxCeleb 1 & 2)"]
    assert "FATAL DEFECT" in profile["transcript_reliability"]
    assert "FATAL DEFECT" in profile["accent_label_source"]

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
    irish_cell = profile["strata_capacity"]["Irish English"]

    assert irish_cell["raw_speakers"] == 220
    assert irish_cell["eligible_speakers"] == 92
    assert irish_cell["historical_exposure"] == 93
    assert irish_cell["available_independent_speakers"] == 0
    assert irish_cell["status"] == "EXHAUSTED_ZERO"

    # Verify surplus for other 5 strata
    for accent in ["Australian English", "Canadian English", "England English", "South Asian English", "US English"]:
        assert profile["strata_capacity"][accent]["available_independent_speakers"] >= TOTAL_REQUIRED_PER_STRATUM
        assert profile["strata_capacity"][accent]["status"] == "SURPLUS"


# ==============================================================================
# 3. Confounding & Orthogonality Evaluation Tests
# ==============================================================================


def test_design_confounding_uncrossed_patchwork():
    """Verify an uncrossed allocation matrix correctly evaluates to COLLINEAR_CONFOUNDED."""
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
    assert result["confounding_verdict"] == "COLLINEAR_CONFOUNDED"
    assert result["is_fully_crossed"] is False
    assert "Irish English" in result["isolated_accents"]
    assert result["corpora_per_accent"]["Irish English"] == 1
    assert "linear mixed model" in result["mathematical_collinearity_explanation"].lower()


def test_design_confounding_orthogonal_crossed():
    """Verify a balanced crossed allocation matrix correctly evaluates to ORTHOGONAL_CROSSED."""
    crossed_matrix = {
        "Corpus_A": {
            "Australian English": 120,
            "Canadian English": 100,
            "England English": 140,
            "Irish English": 110,
            "South Asian English": 90,
            "US English": 130,
        },
        "Corpus_B": {
            "Australian English": 100,
            "Canadian English": 120,
            "England English": 80,
            "Irish English": 110,
            "South Asian English": 130,
            "US English": 90,
        },
    }
    result = evaluate_design_confounding(crossed_matrix)
    assert result["confounding_verdict"] == "ORTHOGONAL_CROSSED"
    assert result["is_fully_crossed"] is True
    assert len(result["isolated_accents"]) == 0
    assert result["matrix_rank"] == 2


# ==============================================================================
# 4. Hierarchical Power Simulation Tests
# ==============================================================================


def test_hierarchical_power_simulation_seed_reproducibility():
    """Verify that hierarchical power simulations with identical seeds produce bitwise identical results."""
    res1 = simulate_hierarchical_multicorpus_power(
        n_speakers_per_stratum=40,
        n_clips_per_speaker=15,
        n_trials=100,
        random_seed=42,
    )
    res2 = simulate_hierarchical_multicorpus_power(
        n_speakers_per_stratum=40,
        n_clips_per_speaker=15,
        n_trials=100,
        random_seed=42,
    )
    assert res1["power_results"]["joint_confirmatory_power"] == res2["power_results"]["joint_confirmatory_power"]
    assert res1["power_results"]["event_d_disparity_guard_power"] == res2["power_results"]["event_d_disparity_guard_power"]


def test_power_monotonicity_under_sample_size_rescaling():
    """
    Verify that joint confirmatory power severely drops as sample size is rescaled
    to match the Irish ceiling (Ng = 40 or 15), failing the 90% power target.
    """
    # Large cohort (Ng = 220)
    res_220 = simulate_hierarchical_multicorpus_power(
        n_speakers_per_stratum=220,
        n_clips_per_speaker=15,
        n_trials=500,
        random_seed=20261030,
    )
    # Rescaled cohort (Ng = 40)
    res_40 = simulate_hierarchical_multicorpus_power(
        n_speakers_per_stratum=40,
        n_clips_per_speaker=15,
        n_trials=500,
        random_seed=20261030,
    )
    # Minimal cohort (Ng = 15)
    res_15 = simulate_hierarchical_multicorpus_power(
        n_speakers_per_stratum=15,
        n_clips_per_speaker=15,
        n_trials=500,
        random_seed=20261030,
    )

    p_220 = res_220["power_results"]["joint_confirmatory_power"]
    p_40 = res_40["power_results"]["joint_confirmatory_power"]
    p_15 = res_15["power_results"]["joint_confirmatory_power"]

    # Monotonic degradation
    assert p_220 > p_40 > p_15
    assert p_220 >= 0.90
    assert p_40 < 0.90, f"Ng=40 must fail 90% power target, got {p_40}"
    assert p_15 < 0.50, f"Ng=15 must exhibit severe power collapse, got {p_15}"


# ==============================================================================
# 5. Scientific Feasibility Disposition & Governance Tests
# ==============================================================================


def test_scientific_feasibility_disposition_invariants():
    """Verify the overall disposition is strictly INFEASIBLE under Decision Rule B."""
    audit = run_multi_corpus_feasibility_audit(PROJECT_ROOT, n_trials=100, random_seed=123)

    assert audit["overall_disposition"] in ["FEASIBLE", "CONDITIONALLY_FEASIBLE", "INFEASIBLE"]
    assert audit["overall_disposition"] == "INFEASIBLE"
    assert audit["governance_status"] == "DRAFT_HOLD"
    assert audit["confirmatory_execution_authorized"] is False

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
    """Verify CLI execution generates valid JSON and Markdown reports."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "stage6m_multi_corpus_feasibility_audit.py"),
        "--reports-dir",
        str(tmp_path),
        "--trials",
        "50",
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

    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    assert "# Stage 6M Confirmatory Study — Multi-Corpus Feasibility" in md
    assert "`INFEASIBLE`" in md
