"""
Tests for Stage 6M Task 6.3 — Primary Model and Power Consistency Audit
=======================================================================
Deterministic verification tests for:
1. Exact nested-clipping quadrature expectations for primary confirmatory scenario
   (3.50 pp mean improvement, -2.00 pp disparity narrowing).
2. Uncalibrated model disparity overshoot quantification (-2.1733 pp vs -2.0000 pp).
3. Monte Carlo standard error and 95% confidence interval for latent residual.
4. Multiplicity architecture preservation (M = 8, alpha_adj = 0.00625, percentile = 99.375%).
5. Exploratory sensitivity screening labeling and scientific limitation disclosures.
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

from src.dsg_ctta.evaluation.paired_cluster_inference_v15 import (
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    CANONICAL_BENCHMARK_BASE_WERS,
)
from scripts.stage6m_v1_5_candidate_power_simulator import (
    CandidateFiveStratumPowerSpec,
    single_clipped_normal_mean,
    nested_clipped_normal_mean,
    derive_five_stratum_treatment_effects,
    derive_calibrated_five_stratum_treatment_effects,
)
from scripts.stage6m_v1_5_primary_model_power_consistency import (
    audit_task_a_model_calibration,
    audit_task_c_sensitivity_provenance,
    audit_task_d_null_calibration_provenance,
    clopper_pearson_interval,
    clopper_pearson_one_sided_lower_bound,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPrimaryModelPowerConsistency:
    """Deterministic validation suite for Task 6.3 primary consistency findings."""

    def test_calibrated_primary_model_exact_expectations(self):
        """Task A: Verify that exact nested quadrature achieves strictly -3.5 pp mean and -2.0 pp disparity."""
        spec = CandidateFiveStratumPowerSpec(
            target_primary_effect_pp=3.50,
            target_ungated_effect_pp=3.50,
            target_disparity_effect_pp=-2.00,
            sigma_between_speaker=0.065,
            sigma_paired_diff=0.032,
        )

        calib = derive_calibrated_five_stratum_treatment_effects(spec, method="quadrature")

        # Static disparity is ~9.2496 pp
        assert pytest.approx(calib["population_disp1_pp"], abs=1e-4) == 9.2496
        # DSG disparity is ~7.2496 pp
        assert pytest.approx(calib["population_disp3_pp"], abs=1e-4) == 7.2496
        # Realized population disparity reduction is EXACTLY -2.000000 pp
        assert pytest.approx(calib["population_delta_disp_pp"], abs=1e-10) == -2.000000000000

        # Verify per-accent expectations under nested quadrature
        accents = list(spec.confirmatory_accents)
        p1_means = [single_clipped_normal_mean(spec.baseline_wers[a], 0.065) for a in accents]
        p3_means = [nested_clipped_normal_mean(spec.baseline_wers[a], calib["accent_deltas"][a])[0] for a in accents]
        mean_improvement = float(np.mean([p1 - p3 for p1, p3 in zip(p1_means, p3_means)]) * 100.0)

        # Realized mean improvement is EXACTLY 3.500000 pp
        assert pytest.approx(mean_improvement, abs=1e-10) == 3.500000000000

    def test_uncalibrated_model_disparity_overshoot(self):
        """Task A: Quantify the disparity overshoot in the historical Task 5 pre-clipping linear formula."""
        spec = CandidateFiveStratumPowerSpec()
        uncal = derive_five_stratum_treatment_effects(spec)
        accents = list(spec.confirmatory_accents)

        p1_means = [single_clipped_normal_mean(spec.baseline_wers[a], 0.065) for a in accents]
        p3_uncal_means = [nested_clipped_normal_mean(spec.baseline_wers[a], uncal["accent_deltas"][a])[0] for a in accents]

        disp1 = (max(p1_means) - min(p1_means)) * 100.0
        disp3 = (max(p3_uncal_means) - min(p3_uncal_means)) * 100.0
        delta_disp_uncal = disp3 - disp1
        mean_imp_uncal = float(np.mean([p1 - p3 for p1, p3 in zip(p1_means, p3_uncal_means)]) * 100.0)

        # Pre-clipping linear formula produced -2.1733 pp disparity narrowing (a 0.1733 pp overshoot)
        assert -2.20 < delta_disp_uncal < -2.15
        assert pytest.approx(delta_disp_uncal, abs=1e-3) == -2.1733

        # Mean improvement had a minor shortfall (3.4044 pp vs 3.5000 pp)
        assert 3.39 < mean_imp_uncal < 3.42
        assert pytest.approx(mean_imp_uncal, abs=1e-3) == 3.4044

    def test_monte_carlo_residual_and_confidence_interval(self):
        """Task D: Verify Monte Carlo standard error and confidence interval for 10M-sample residual."""
        res_d = audit_task_d_null_calibration_provenance()
        mc = res_d["latent_mc_10m_validation"]

        # Residual is -0.0024 pp
        assert pytest.approx(mc["residual_delta_disp_pp"], abs=1e-4) == -0.002432

        # Standard error is ~0.0041 pp
        assert pytest.approx(mc["mc_standard_error_pp"], abs=1e-4) == 0.004111

        # 95% MC CI covers 0.0000 pp
        low, high = mc["mc_95_ci_pp"]
        assert low < 0.0 < high
        assert abs(mc["z_score"]) < 1.0  # z ~ -0.59
        assert mc["p_value"] > 0.50     # p ~ 0.55

    def test_multiplicity_and_bonferroni_architecture(self):
        """Governance: Verify M=8 Bonferroni adjustment and 99.375% confidence percentile."""
        spec = CandidateFiveStratumPowerSpec()
        assert spec.m_hypotheses == 8
        assert spec.alpha_family == 0.05
        assert pytest.approx(spec.adj_alpha, abs=1e-6) == 0.00625
        assert pytest.approx(spec.simultaneous_percentile, abs=1e-4) == 99.375

    def test_clopper_pearson_power_bounds_logic(self):
        """Task B: Test Clopper-Pearson exact confidence intervals and lower bound calculations."""
        # Test confirmed 9,058 passes out of 10,000 trials (90.58% power)
        low, high = clopper_pearson_interval(9058, 10000, alpha=0.05)
        one_sided_lcb = clopper_pearson_one_sided_lower_bound(9058, 10000, alpha=0.05)

        assert 0.899 < low < 0.901   # 89.99%
        assert 0.910 < high < 0.913  # 91.15%
        assert one_sided_lcb >= 0.900 # 90.09% (Confirms that LCB >= 90.00% is satisfied!)

    def test_sensitivity_results_labeled_as_exploratory(self):
        """Task C: Verify that sensitivity results are flagged as exploratory estimates."""
        res_c = audit_task_c_sensitivity_provenance()
        assert res_c["exploratory_trials"] == 1000
        assert res_c["exploratory_bootstraps"] == 2000
        assert "exploratory" in res_c["note"].lower()
        assert "not 10,000-trial" in res_c["note"].lower()

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
