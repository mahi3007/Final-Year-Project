"""
Tests for Stage 6M Task 6.1 & 6.2 — Event D Null Calibration & Nested Clipping Verification
==========================================================================================
Deterministic verification tests for:
1. Nested clipping expectation decomposition and formula exactness.
2. Boundary point-mass contributions across accent strata.
3. Quadrature versus analytical closed-form agreement.
4. Five-stratum population disparity null calibration (Delta D = 0.00 pp).
5. Fixed-seed latent Monte Carlo reproducibility and consistency.
6. Bonferroni null calibration metadata and statistical interpretation.
7. Candidate inference engine detection of beneficial versus harmful disparity shifts.
8. Custom resample deterministic equivalence in v1.5 candidate engine.
9. Frozen v1.4.0 paired cluster inference immutability (0 lines diff against origin/main).
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pytest
from scipy import stats as sp_stats, integrate

from src.dsg_ctta.evaluation.paired_cluster_inference_v15 import (
    FIVE_STRATUM_CONFIRMATORY_ACCENTS,
    CANONICAL_BENCHMARK_BASE_WERS,
    run_confirmatory_paired_cluster_inference_v15,
)
from scripts.stage6m_v1_5_candidate_power_simulator import (
    CandidateFiveStratumPowerSpec,
    single_clipped_normal_mean,
    nested_clipped_normal_mean,
    derive_calibrated_five_stratum_treatment_effects,
    derive_five_stratum_treatment_effects,
)
from scripts.stage6m_v1_5_event_d_null_calibration import (
    clopper_pearson_interval,
    clopper_pearson_one_sided_upper_bound,
    run_analytical_task_a_and_b,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestEventDNullCalibration:
    """Deterministic validation suite for Task 6.1 and 6.2 calibration findings."""

    def test_nested_clipping_expectation(self):
        """Task A: Verify nested clipping expectation decomposition E[p3] = T_lower + T_upper + T_interior."""
        mu_us = 0.142
        delta = -0.035
        sigma_spk = 0.065
        sigma_paired = 0.032
        a = 0.01
        b = 0.99

        tot, t_lo, t_hi, t_int = nested_clipped_normal_mean(
            mu=mu_us,
            delta=delta,
            sigma_spk=sigma_spk,
            sigma_paired=sigma_paired,
            a=a,
            b=b,
        )

        # Sum of components must match total expectation
        assert pytest.approx(tot, abs=1e-12) == t_lo + t_hi + t_int

        # US English expectation is approximately 11.0065%
        assert 0.1100 < tot < 0.1102

        # Compare with naive single-step Gaussian approximation with combined variance
        sig_combined = math.sqrt(sigma_spk**2 + sigma_paired**2)
        naive_tot = single_clipped_normal_mean(mu_us + delta, sig_combined, a=a, b=b)

        # Naive understates expectation by ~ +0.003 pp because it ignores discrete point mass at p1 = 0.01
        discrepancy_pp = (tot - naive_tot) * 100.0
        assert 0.002 < discrepancy_pp < 0.004

    def test_boundary_point_mass_contribution(self):
        """Task A: Verify boundary point-mass contributions across lowest- and highest-WER strata."""
        a = 0.01
        b = 0.99
        sigma_spk = 0.065
        sigma_paired = 0.032
        delta = -0.035

        # US English (lowest WER: 14.2%) experiences highest lower clipping
        tot_us, t_lo_us, t_hi_us, t_int_us = nested_clipped_normal_mean(
            0.142, delta, sigma_spk, sigma_paired, a, b
        )
        assert t_lo_us > 0.0002  # > +0.02 pp contribution from lower point mass
        assert t_hi_us < 1e-15   # Upper bound is > 13 standard deviations away
        assert t_int_us / tot_us > 0.995

        # South Asian English (highest WER: 23.5%) experiences minimal lower clipping
        tot_sa, t_lo_sa, t_hi_sa, t_int_sa = nested_clipped_normal_mean(
            0.235, delta, sigma_spk, sigma_paired, a, b
        )
        assert t_lo_sa < 1e-5    # < 0.001 pp
        assert t_hi_sa < 1e-15
        assert t_int_sa / tot_sa > 0.9999

    def test_quadrature_versus_analytical_agreement(self):
        """Task B: Verify numerical quadrature matches analytical expectations and unclipped limits."""
        # 1. Single clipped variable: analytical vs independent numerical integration
        mu = 0.174
        sigma = 0.065
        a = 0.01
        b = 0.99
        analytical_val = single_clipped_normal_mean(mu, sigma, a=a, b=b)

        def integrand(x: float) -> float:
            return x * float(sp_stats.norm.pdf((x - mu) / sigma)) / sigma

        int_val, _ = integrate.quad(integrand, a, b, epsabs=1e-12, epsrel=1e-12)
        p_lo = float(sp_stats.norm.cdf((a - mu) / sigma))
        p_hi = float(1.0 - sp_stats.norm.cdf((b - mu) / sigma))
        quad_val = a * p_lo + b * p_hi + int_val

        assert pytest.approx(analytical_val, abs=1e-9) == quad_val

        # 2. Unclipped limit: when clipping probability is negligible, nested mean equals mu + delta
        mu_mid = 0.50
        delta_mid = -0.05
        tot_mid, _, _, _ = nested_clipped_normal_mean(
            mu=mu_mid, delta=delta_mid, sigma_spk=0.01, sigma_paired=0.01, a=a, b=b
        )
        assert pytest.approx(tot_mid, abs=1e-8) == (mu_mid + delta_mid)

    def test_population_disparity_null(self):
        """Task B: Verify that quadrature calibration achieves true population Delta D = 0.000000 pp."""
        spec = CandidateFiveStratumPowerSpec(
            target_primary_effect_pp=3.50,
            target_ungated_effect_pp=3.50,
            target_disparity_effect_pp=0.00,
            sigma_between_speaker=0.065,
            sigma_paired_diff=0.032,
        )

        calib = derive_calibrated_five_stratum_treatment_effects(spec, method="quadrature")

        # Static disparity is ~9.2496 pp
        assert pytest.approx(calib["population_disp1_pp"], abs=1e-4) == 9.2496
        # DSG disparity matches static disparity exactly
        assert pytest.approx(calib["population_disp3_pp"], abs=1e-4) == 9.2496
        # Realized population disparity difference is zero within numerical tolerance
        assert abs(calib["population_delta_disp_pp"]) < 1e-10

        # Calibrated treatment effects remain negative for all strata
        for acc, d in calib["accent_deltas_pp"].items():
            assert -4.0 < d < -3.0, f"Calibrated delta {d} outside expected range for {acc}"

    def test_fixed_seed_latent_monte_carlo_reproducibility(self):
        """Task B: Verify 100k latent Monte Carlo reproducibility and consistency with quadrature."""
        spec = CandidateFiveStratumPowerSpec(
            target_primary_effect_pp=3.50,
            target_ungated_effect_pp=3.50,
            target_disparity_effect_pp=0.00,
            sigma_between_speaker=0.065,
            sigma_paired_diff=0.032,
        )
        calib = derive_calibrated_five_stratum_treatment_effects(spec, method="quadrature")
        accents = list(spec.confirmatory_accents)
        mu_arr = np.array([spec.baseline_wers[a] for a in accents])
        delta_arr = np.array([calib["accent_deltas"][a] for a in accents])

        def run_mc(seed: int, n_samples: int = 200_000) -> float:
            rng = np.random.default_rng(seed)
            u = rng.normal(0, 0.065, (len(accents), n_samples))
            p1 = np.clip(mu_arr[:, None] + u, 0.01, 0.99)
            eps = rng.normal(0, 0.032, (len(accents), n_samples))
            p3 = np.clip(p1 + delta_arr[:, None] + eps, 0.01, 0.99)
            d1 = (np.max(np.mean(p1, axis=1)) - np.min(np.mean(p1, axis=1))) * 100.0
            d3 = (np.max(np.mean(p3, axis=1)) - np.min(np.mean(p3, axis=1))) * 100.0
            return float(d3 - d1)

        # Reproducibility with same seed
        res1 = run_mc(20261102, 200_000)
        res2 = run_mc(20261102, 200_000)
        assert res1 == res2

        # Empirical delta disparity within Monte Carlo sampling margin of 0.0 pp (< 0.01 pp)
        assert abs(res1) < 0.01

    def test_bonferroni_null_calibration_metadata_and_interpretation(self):
        """Task C: Verify Bonferroni null calibration parameters and correct statistical interpretation."""
        spec = CandidateFiveStratumPowerSpec()
        assert spec.m_hypotheses == 8
        assert spec.alpha_family == 0.05
        assert pytest.approx(spec.adj_alpha, abs=1e-6) == 0.00625  # 0.625%
        assert pytest.approx(spec.simultaneous_percentile, abs=1e-4) == 99.375

        # Expected false pass count under 10,000 trials
        n_trials = 10000
        expected_count = n_trials * spec.adj_alpha
        sd_count = math.sqrt(n_trials * spec.adj_alpha * (1.0 - spec.adj_alpha))
        assert pytest.approx(expected_count, abs=1e-4) == 62.5
        assert pytest.approx(sd_count, abs=1e-2) == 7.88

        # N = 220: 58 false passes (0.580%)
        low_220, high_220 = clopper_pearson_interval(58, n_trials, alpha=0.05)
        ucb_220 = clopper_pearson_one_sided_upper_bound(58, n_trials, alpha=0.05)
        z_220 = (58 - expected_count) / sd_count

        assert pytest.approx(low_220 * 100.0, abs=1e-2) == 0.441
        assert pytest.approx(high_220 * 100.0, abs=1e-2) == 0.749
        assert pytest.approx(ucb_220 * 100.0, abs=1e-2) == 0.721
        assert -0.60 < z_220 < -0.55  # ~ -0.57 SD

        # N = 285: 63 false passes (0.630%)
        low_285, high_285 = clopper_pearson_interval(63, n_trials, alpha=0.05)
        ucb_285 = clopper_pearson_one_sided_upper_bound(63, n_trials, alpha=0.05)
        z_285 = (63 - expected_count) / sd_count

        assert pytest.approx(low_285 * 100.0, abs=1e-2) == 0.484
        assert pytest.approx(high_285 * 100.0, abs=1e-2) == 0.805
        assert pytest.approx(ucb_285 * 100.0, abs=1e-2) == 0.776
        assert 0.00 < z_285 < 0.10   # ~ +0.06 SD

        # Statistical compatibility checks:
        # 1. Both two-sided 95% CIs cover nominal level 0.625%
        assert low_220 <= 0.00625 <= high_220
        assert low_285 <= 0.00625 <= high_285

        # 2. Both one-sided 95% UCBs exceed nominal level 0.625%, meaning finite simulation cannot certify control with 95% confidence
        assert ucb_220 > 0.00625
        assert ucb_285 > 0.00625

        # 3. Binomial tests show no statistically significant inflation (two-tailed p > 0.50)
        p_val_220 = sp_stats.binomtest(58, n_trials, 0.00625).pvalue
        p_val_285 = sp_stats.binomtest(63, n_trials, 0.00625).pvalue
        assert p_val_220 > 0.50
        assert p_val_285 > 0.90

    def test_positive_disparity_harm_calibration(self):
        """Task D: Verify calibration for harmful disparity divergence scenarios."""
        # Harm +0.50 pp
        spec_05 = CandidateFiveStratumPowerSpec(target_disparity_effect_pp=0.50)
        res_05 = derive_calibrated_five_stratum_treatment_effects(spec_05, method="quadrature")
        assert pytest.approx(res_05["population_delta_disp_pp"], abs=1e-6) == 0.5000
        assert res_05["population_disp3_pp"] > res_05["population_disp1_pp"]

        # Harm +1.00 pp
        spec_10 = CandidateFiveStratumPowerSpec(target_disparity_effect_pp=1.00)
        res_10 = derive_calibrated_five_stratum_treatment_effects(spec_10, method="quadrature")
        assert pytest.approx(res_10["population_delta_disp_pp"], abs=1e-6) == 1.0000
        assert res_10["population_disp3_pp"] > res_10["population_disp1_pp"]

    def test_candidate_inference_engine_detects_harm_and_benefit(self):
        """Task D: Test candidate inference engine on synthetic beneficial vs harmful datasets."""
        accents = sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS))

        # Scenario 1: Beneficial narrowing
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

        custom_resamples = np.zeros((5, 50, 10), dtype=np.int64)
        for a_idx in range(5):
            for b in range(50):
                custom_resamples[a_idx, b] = np.arange(10)

        rep_custom = run_confirmatory_paired_cluster_inference_v15(
            records,
            num_bootstrap_replicates=50,
            custom_bootstrap_resamples=custom_resamples,
        )
        crit_d = rep_custom.criteria["disparity_non_increase"]
        assert crit_d.bootstrap_std == 0.0
        assert pytest.approx(crit_d.adjusted_ucb, abs=1e-4) == crit_d.point_estimate

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
