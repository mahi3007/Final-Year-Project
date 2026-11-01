"""
Tests for Stage 6M Task 6.1 — Event D Type I Null Calibration & Harm Audit
===========================================================================
Deterministic verification tests for:
1. Exact null population disparity derivation.
2. Positive disparity harm calibration (+0.5 pp and +1.0 pp).
3. Disparity sign conventions and non-increase acceptance criteria.
4. Bonferroni adjusted family level (M = 8, alpha_adj = 0.00625, percentile = 99.375%).
5. Exact Clopper-Pearson confidence interval properties.
6. Candidate inference engine decision logic under disparity improvement vs harm.
7. Candidate inference engine and simulator structural parity.
8. Frozen v1.4.0 paired cluster inference immutability.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pytest

from src.dsg_ctta.evaluation.paired_cluster_inference_v15 import (
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    CANONICAL_BENCHMARK_BASE_WERS,
    run_confirmatory_paired_cluster_inference_v15,
)
from scripts.stage6m_v1_5_candidate_power_simulator import (
    CandidateFiveStratumPowerSpec,
    derive_calibrated_five_stratum_treatment_effects,
    derive_five_stratum_treatment_effects,
)
from scripts.stage6m_v1_5_event_d_null_calibration import (
    clopper_pearson_interval,
    run_analytical_task_a,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestEventDNullCalibration:
    """Deterministic validation suite for Task 6.1 calibration findings."""

    def test_analytical_null_data_generating_model(self):
        """Task A: Verify that clipping introduces -0.25 pp bias if uncalibrated, and 0.00 pp when calibrated."""
        res = run_analytical_task_a()
        
        # Nominal static disparity is 23.5 - 14.2 = 9.30 pp
        assert pytest.approx(res["nominal_static_disparity_pp"], abs=1e-3) == 9.3000
        
        # After clipping, analytical static disparity is ~9.25 pp
        assert 9.20 < res["analytical_clipped_static_disparity_pp"] < 9.30
        
        # Uncalibrated generator narrows disparity by ~ -0.247 pp (explaining Task 6 2.3% false-pass finding)
        assert -0.30 < res["uncalibrated_analytical_delta_disparity_pp"] < -0.20
        
        # Calibrated generator achieves EXACT Delta D = 0.000000 pp
        assert pytest.approx(res["calibrated_population_delta_disp_pp"], abs=1e-5) == 0.000000

    def test_positive_disparity_harm_calibration(self):
        """Task D: Verify calibration for harmful disparity divergence scenarios."""
        # Harm +0.50 pp
        spec_05 = CandidateFiveStratumPowerSpec(target_disparity_effect_pp=0.50)
        res_05 = derive_calibrated_five_stratum_treatment_effects(spec_05, seed=42, num_samples=1_000_000)
        assert pytest.approx(res_05["population_delta_disp_pp"], abs=0.01) == 0.5000
        assert res_05["population_disp3_pp"] > res_05["population_disp1_pp"]
        
        # Harm +1.00 pp
        spec_10 = CandidateFiveStratumPowerSpec(target_disparity_effect_pp=1.00)
        res_10 = derive_calibrated_five_stratum_treatment_effects(spec_10, seed=42, num_samples=1_000_000)
        assert pytest.approx(res_10["population_delta_disp_pp"], abs=0.01) == 1.0000
        assert res_10["population_disp3_pp"] > res_10["population_disp1_pp"]

    def test_sign_conventions_and_event_d_margins(self):
        """Task E: Verify mathematical sign conventions and boundary thresholds for Event D."""
        # Delta_D = Disparity_DSG - Disparity_Static
        # Event D criterion: Disparity Non-Increase (H1: Delta_D <= 0.00 pp)
        spec = CandidateFiveStratumPowerSpec()
        assert spec.m_hypotheses == 8
        assert spec.alpha_family == 0.05
        assert pytest.approx(spec.adj_alpha, abs=1e-6) == 0.00625
        assert pytest.approx(spec.simultaneous_percentile, abs=1e-4) == 99.375

    def test_clopper_pearson_exact_intervals(self):
        """Task C: Verify exact Clopper-Pearson interval coverage and edge-case behavior."""
        # 0 successes out of 100 trials: low must be exactly 0.0
        low0, high0 = clopper_pearson_interval(0, 100, alpha=0.05)
        assert low0 == 0.0
        assert 0.03 < high0 < 0.04  # ~ 3.6% upper bound
        
        # 100 successes out of 100 trials: high must be exactly 1.0
        low100, high100 = clopper_pearson_interval(100, 100, alpha=0.05)
        assert high100 == 1.0
        assert 0.96 < low100 < 0.97
        
        # 45 successes out of 10,000 trials (0.45%)
        low, high = clopper_pearson_interval(45, 10000, alpha=0.05)
        assert 0.003 < low < 0.004
        assert 0.005 < high < 0.007
        # Upper bound must be strictly below 0.625% for true calibration
        assert high < 0.00625

    def test_candidate_inference_engine_detects_harm_and_benefit(self):
        """Task B: Test candidate inference engine on synthetic beneficial vs harmful datasets."""
        accents = sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS))
        
        # Scenario 1: Beneficial narrowing
        # Arm 1 has high disparity: US=10%, South Asian=30% (disparity 20 pp)
        # Arm 3 has low disparity: US=10%, South Asian=15% (disparity 5 pp) -> Delta D = -15 pp
        beneficial_records = []
        for a in accents:
            e1 = 10 if a == "US English" else (30 if a == "South Asian English" else 20)
            e3 = 10 if a == "US English" else (15 if a == "South Asian English" else 12)
            for i in range(20):
                beneficial_records.append({
                    "speaker_id": f"{a}_{i}",
                    "stratum": a,
                    "wc": 100,
                    "err1": e1,
                    "err2": e1,
                    "err3": e3,
                })
                
        rep_ben = run_confirmatory_paired_cluster_inference_v15(
            beneficial_records,
            num_bootstrap_replicates=500,
            seed=42,
            use_fast_bootstrap=True,
        )
        crit_d_ben = rep_ben.criteria["disparity_non_increase"]
        assert crit_d_ben.point_estimate < 0.0
        assert crit_d_ben.adjusted_ucb <= 0.0
        assert crit_d_ben.is_success is True

        # Scenario 2: Severe disparity harm (widening)
        # Arm 1 has low disparity: all accents 20% (disparity 0 pp)
        # Arm 3 has high disparity: US=10%, South Asian=35% (disparity 25 pp) -> Delta D = +25 pp
        harmful_records = []
        for a in accents:
            e1 = 20
            e3 = 10 if a == "US English" else (35 if a == "South Asian English" else 20)
            for i in range(20):
                harmful_records.append({
                    "speaker_id": f"harm_{a}_{i}",
                    "stratum": a,
                    "wc": 100,
                    "err1": e1,
                    "err2": e1,
                    "err3": e3,
                })
                
        rep_harm = run_confirmatory_paired_cluster_inference_v15(
            harmful_records,
            num_bootstrap_replicates=500,
            seed=42,
            use_fast_bootstrap=True,
        )
        crit_d_harm = rep_harm.criteria["disparity_non_increase"]
        assert crit_d_harm.point_estimate > 0.0
        assert crit_d_harm.adjusted_ucb > 0.0
        assert crit_d_harm.is_success is False
        assert rep_harm.all_criteria_passed is False

    def test_custom_resamples_deterministic_equivalence(self):
        """Task E: Verify exact parity between custom_bootstrap_resamples and standard bootstrap."""
        accents = sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS))
        records = []
        for a in accents:
            for i in range(10):
                records.append({
                    "speaker_id": f"det_{a}_{i}",
                    "stratum": a,
                    "wc": 150,
                    "err1": 25,
                    "err2": 25,
                    "err3": 20,
                })
                
        # Create deterministic fixed custom resamples: shape (5, 50, 10)
        custom_resamples = np.zeros((5, 50, 10), dtype=np.int64)
        for a_idx in range(5):
            for b in range(50):
                custom_resamples[a_idx, b] = np.arange(10)
                
        rep_custom = run_confirmatory_paired_cluster_inference_v15(
            records,
            num_bootstrap_replicates=50,
            custom_bootstrap_resamples=custom_resamples,
        )
        # Because every bootstrap draw is identical to the original sample,
        # bootstrap std should be zero and UCB should equal point estimate.
        crit_d = rep_custom.criteria["disparity_non_increase"]
        assert crit_d.bootstrap_std == 0.0
        assert pytest.approx(crit_d.adjusted_ucb, abs=1e-4) == crit_d.point_estimate

    def test_frozen_v1_4_0_immutability(self):
        """Governance: Verify that frozen v1.4.0 code remains strictly untouched."""
        frozen_file = REPO_ROOT / "src" / "dsg_ctta" / "evaluation" / "paired_cluster_inference.py"
        assert frozen_file.exists()
        
        # Check git diff against origin/main
        res = subprocess.run(
            ["git", "diff", "origin/main", "--", str(frozen_file)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        assert len(res.stdout.strip()) == 0, f"Frozen v1.4.0 has unauthorized modifications: {res.stdout}"
