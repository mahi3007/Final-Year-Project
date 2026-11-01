"""
Tests for Stage 6M Task 6.4 — Monte Carlo Acceptance-Rule Reconciliation
========================================================================
Deterministic verification tests for:
1. One-sided vs two-sided Clopper-Pearson exact Beta bounds for k=9058, n=10000.
2. Exact minimum success thresholds to achieve LCB >= 0.900000.
3. Protocol specification vs code implementation ambiguity reconciliation.
4. Operational buffer preservation for N_g = 220 (+65 Australian speakers).
5. Formal supersession tracking of Task 5 95.35% estimate.
6. Frozen v1.4.0 paired cluster inference immutability (0 lines diff against origin/main).
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pytest
import scipy.stats as sp_stats

from scripts.stage6m_v1_5_mc_acceptance_rule_audit import (
    compute_exact_clopper_pearson,
    find_required_success_thresholds,
    build_acceptance_rule_audit_report,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMonteCarloAcceptanceRuleAudit:
    """Deterministic validation suite for Task 6.4 acceptance rule findings."""

    def test_clopper_pearson_one_sided_vs_two_sided_exact_bounds(self):
        """Task B: Verify exact unrounded Clopper-Pearson bounds for k = 9,058 out of 10,000."""
        res = compute_exact_clopper_pearson(9058, 10000, alpha=0.05)

        p_hat = res["point_estimate"]
        assert p_hat == 0.9058

        # Two-sided 95% CI lower endpoint (tail = 0.025)
        low_2sided = res["two_sided_95_ci"]["lower_endpoint"]
        assert pytest.approx(low_2sided, abs=1e-8) == 0.89990601
        assert low_2sided < 0.900000
        # Shortfall is 0.0094 pp
        assert pytest.approx(res["two_sided_95_ci"]["distance_from_90_pp"], abs=1e-4) == -0.0094

        # One-sided 95% LCB (tail = 0.050)
        lcb_1sided = res["one_sided_95_lcb"]["lower_bound"]
        assert pytest.approx(lcb_1sided, abs=1e-8) == 0.90085739
        assert lcb_1sided >= 0.900000
        # Margin is +0.0857 pp
        assert pytest.approx(res["one_sided_95_lcb"]["distance_from_90_pp"], abs=1e-4) == +0.0857

        # Discrepancy between the two bounds is exactly 0.095138 pp
        diff_pp = (lcb_1sided - low_2sided) * 100.0
        assert pytest.approx(diff_pp, abs=1e-5) == 0.095138

    def test_success_count_thresholds_for_90_percent_power(self):
        """Task B: Verify exact minimum successes required to clear 90.0000% under each definition."""
        thresh = find_required_success_thresholds(10000, target=0.90, alpha=0.05)

        # Two-sided lower endpoint >= 0.90 requires k >= 9059
        assert thresh["two_sided_lower_endpoint_min_k"] == 9059
        assert thresh["two_sided_lower_endpoint_min_rate_pct"] == 90.59

        # One-sided LCB >= 0.90 requires k >= 9050
        assert thresh["one_sided_lcb_min_k"] == 9050
        assert thresh["one_sided_lcb_min_rate_pct"] == 90.50

        # Discrepancy in trajectory count is exactly 9 trials
        assert thresh["trajectory_difference_k"] == 9

        # Confirm boundary transition for k = 9058 vs 9059
        low_9058 = float(sp_stats.beta.ppf(0.025, 9058, 10000 - 9058 + 1))
        low_9059 = float(sp_stats.beta.ppf(0.025, 9059, 10000 - 9059 + 1))
        assert low_9058 < 0.900000
        assert low_9059 >= 0.900000

    def test_protocol_ambiguity_reconciliation(self):
        """Task A & C: Verify documented protocol ambiguity and governance recommendations."""
        rep = build_acceptance_rule_audit_report()

        amb = rep["task_a_protocol_inspection"]["detected_ambiguity"]
        assert "95% lower confidence bound" in amb["text_specification"]
        assert "clopper_pearson_interval" in amb["code_implementation"]

        dec = rep["task_c_acceptance_decision"]
        assert dec["governing_determination"] == "AMBIGUOUS (Pre-Registration Clarification Required)"
        assert "PASS" in dec["under_one_sided_interpretation"]["verdict"]
        assert "SHORTFALL" in dec["under_two_sided_interpretation"]["verdict"]
        assert "CONDITIONAL HOLD" in dec["principled_recommendation"]

    def test_sample_size_positioning_and_reserve_buffer(self):
        """Task D: Verify primary candidate vs benchmark candidate positioning."""
        rep = build_acceptance_rule_audit_report()
        samp = rep["task_d_sample_size_reconciliation"]

        prim = samp["primary_candidate"]
        bench = samp["benchmark_candidate"]

        assert prim["sample_size_ng"] == 220
        assert prim["australian_buffer_speakers"] == 65
        assert prim["buffer_margin_pct"] == 21.3
        assert prim["confirmed_joint_power_pct"] == 90.58

        assert bench["sample_size_ng"] == 285
        assert bench["australian_buffer_speakers"] == 0
        assert "SUPPLEMENTAL BENCHMARK" in bench["status"]

    def test_superseded_task_5_power_estimate_identification(self):
        """Task D: Verify that Task 5 95.35% estimate is formally marked as superseded."""
        rep = build_acceptance_rule_audit_report()
        sup = rep["task_d_sample_size_reconciliation"]["superseded_results"]

        assert sup["original_task_5_power_pct"] == 95.35
        assert "uncalibrated" in sup["supersession_reason"].lower()
        assert "overshoot" in sup["supersession_reason"].lower()

    def test_frozen_v1_4_0_immutability(self):
        """Governance: Verify that frozen v1.4.0 code remains strictly untouched."""
        frozen_file = REPO_ROOT / "src" / "dsg_ctta" / "evaluation" / "paired_cluster_inference.py"
        assert frozen_file.exists()

        res = subprocess.run(
            ["git", "diff", "origin/main", "--", str(frozen_file)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        assert len(res.stdout.strip()) == 0, f"Frozen v1.4.0 has unauthorized modifications: {res.stdout}"
