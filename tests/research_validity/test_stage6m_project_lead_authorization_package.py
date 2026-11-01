"""
Stage 6M Task 6.5 — Project-Lead Authorization Package Validation Tests
======================================================================
Validates the structural, numerical, and governance integrity of the
Project-Lead Authorization Package for the v1.5 candidate five-stratum protocol.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import scipy.stats as sp_stats

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestProjectLeadAuthorizationPackage:
    """Verifies that the authorization package conforms to Protocol Section 14.7."""

    def test_authorization_package_files_exist(self):
        json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.json"
        md_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.md"
        assert json_path.is_file(), f"Missing {json_path}"
        assert md_path.is_file(), f"Missing {md_path}"
        assert json_path.stat().st_size > 1000
        assert md_path.stat().st_size > 2000

    def test_historical_protocol_prespecification_verification(self):
        json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        hist = data["monte_carlo_acceptance_reconciliation"]["historical_protocol_verification"]
        assert hist["prespecification_commit"].startswith("8f92b0b")
        assert hist["file_path"] == "reports/stage6m/stage6m_v1_5_candidate_five_stratum_protocol_spec.md"
        assert hist["predates_observed_power_result"] is True
        assert hist["commits_prior_to_confirmation"] == 9

        # Verify via git log that commit 8f92b0b introduced the wording
        cmd = [
            "git", "log", "--all", "--oneline", "-S",
            "exact Clopper-Pearson 95% lower confidence bound",
            "--", "reports/stage6m/stage6m_v1_5_candidate_five_stratum_protocol_spec.md"
        ]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert "8f92b0b" in res.stdout

    def test_exact_numerical_bounds_and_margins(self):
        json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rec = data["monte_carlo_acceptance_reconciliation"]
        opt1 = rec["option_1_one_sided_lcb"]
        opt2 = rec["option_2_two_sided_lower_endpoint"]

        # Recalculate independently
        k, n = 9058, 10000
        recalculated_opt1 = float(sp_stats.beta.ppf(0.05, k, n - k + 1))
        recalculated_opt2 = float(sp_stats.beta.ppf(0.025, k, n - k + 1))

        assert abs(opt1["exact_unrounded_value"] - recalculated_opt1) < 1e-12
        assert abs(opt2["exact_unrounded_value"] - recalculated_opt2) < 1e-12

        assert round(opt1["exact_percentage"], 6) == 90.085739
        assert round(opt2["exact_percentage"], 6) == 89.990601

        assert opt1["satisfies_threshold"] is True
        assert opt1["margin_trials_k"] == 8
        assert opt2["satisfies_threshold"] is False
        assert opt2["margin_trials_k"] == -1

    def test_sample_size_architecture_and_buffer(self):
        json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        arch = data["sample_size_architecture"]
        p = arch["primary_candidate_n220"]
        s = arch["supplemental_benchmark_n285"]

        assert p["sample_size_per_accent_ng"] == 220
        assert p["total_evaluation_speakers"] == 1100
        assert p["total_gate_speakers"] == 100
        assert p["australian_unexposed_required"] == 240
        assert p["australian_unexposed_available"] == 305
        assert p["australian_replacement_reserve_speakers"] == 65
        assert p["australian_reserve_margin_pct"] > 21.0
        assert p["status"] == "PRIMARY_RECOMMENDED_CANDIDATE"

        assert s["sample_size_per_accent_ng"] == 285
        assert s["total_evaluation_speakers"] == 1425
        assert s["australian_replacement_reserve_speakers"] == 0
        assert s["status"] == "SUPPLEMENTAL_CAPACITY_BENCHMARK_ONLY"

    def test_superseded_task_5_provenance(self):
        json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sup = data["superseded_historical_findings"]
        assert sup["task_5_uncalibrated_power_pct"] == 95.35
        assert "overshoot" in sup["supersession_rationale"]

    def test_frozen_v1_4_0_immutability(self):
        cmd = ["git", "diff", "origin/main", "--", "src/dsg_ctta/evaluation/paired_cluster_inference.py"]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert res.returncode == 0
        assert res.stdout.strip() == "", "Frozen v1.4.0 paired_cluster_inference.py has uncommitted changes against origin/main!"

    def test_project_lead_approval_decision_execution(self):
        json_path = REPO_ROOT / "reports" / "stage6m" / "stage6m_v1_5_project_lead_authorization_package.json"
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["authorization_metadata"]["governance_status"] == "AUTHORIZED_FOR_DATA_PREPARATION"
        assert data["authorization_metadata"]["governance_action"] == "PROJECT_LEAD_ACADEMIC_AUTHORIZATION_EXECUTED"

        dec = data["project_lead_decision_record"]
        assert dec["project_lead_verdict"] == "APPROVED"
        assert dec["sign_off_status"] == "EXECUTED"
        assert "Option 1" in dec["decision_1_monte_carlo_acceptance_rule"]
        assert "N_g = 220" in dec["decision_2_primary_sample_size"]
        assert "AUTHORIZED" in dec["decision_3_governance_scope"]

        caveat = data["power_assumptions_and_limitations"]["required_dissertation_caveat"]
        assert "conditional on the specified treatment-effect and disparity-reduction assumptions" in caveat
        assert "does not establish the physical performance of the DSG adaptation system" in caveat

