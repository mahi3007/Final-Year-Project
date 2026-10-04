"""
Stage 5D Phase 4: DSG Contract Validation Test Suite.
====================================================
Verifies that the DSG Controller formally distinguishes:
1. STATISTICAL_GATE_REJECTION (from empirical risk/regression/disparity violations)
2. FAIL_CLOSED_EVALUATOR_ERROR (from missing data, NaN/Inf, or runtime exceptions)
3. ACCEPTED (when candidate satisfies all tripartite bounds)

Controlled Fixtures:
A. All thresholds satisfied -> ACCEPT (decision_reason="ACCEPTED", rejection_category=None)
B. UCB_R > epsilon_R -> REJECT (decision_reason="STATISTICAL_GATE_REJECTION")
C. UCB_max_group > epsilon_G -> REJECT (decision_reason="STATISTICAL_GATE_REJECTION")
D. UCB_D > epsilon_D -> REJECT (decision_reason="STATISTICAL_GATE_REJECTION")
E. Evaluator exception -> REJECT (decision_reason="FAIL_CLOSED_EVALUATOR_ERROR")
"""

import pytest
import math
from typing import Dict, List, Any

from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.types import BootstrapMetrics, GateDecision
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator


def build_mock_bootstrap_metrics(
    delta_r: float = 0.0,
    max_delta_g: float = 0.0,
    delta_d: float = 0.0,
    ucb_r: float = 0.0,
    ucb_max_group: float = 0.01,
    ucb_d: float = 0.01,
    group_deltas: Dict[str, float] = None,
    group_ucbs: Dict[str, float] = None,
) -> BootstrapMetrics:
    if group_deltas is None:
        group_deltas = {"grp_a": delta_r, "grp_b": delta_r}
    if group_ucbs is None:
        group_ucbs = {"grp_a": ucb_r, "grp_b": ucb_r}
    return BootstrapMetrics(
        delta_r=delta_r,
        max_delta_g=max_delta_g,
        delta_d=delta_d,
        ucb_r=ucb_r,
        ucb_max_group=ucb_max_group,
        ucb_d=ucb_d,
        group_deltas=group_deltas,
        group_ucbs=group_ucbs,
        replicates_computed=1000,
        omitted_groups_count=0,
    )


# =============================================================================
# FIXTURE A: Safely Satisfies All Thresholds -> ACCEPT
# =============================================================================
def test_contract_fixture_a_accept():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = build_mock_bootstrap_metrics(
        delta_r=-0.0050,
        max_delta_g=0.0050,
        delta_d=0.0020,
        ucb_r=-0.0010,       # <= 0.0000 (Passes epsilon_R)
        ucb_max_group=0.0150, # <= 0.0200 (Passes epsilon_G)
        ucb_d=0.0120,         # <= 0.0200 (Passes epsilon_D)
    )

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="theta_prime_a",
        current_model_identifier="theta_t",
        bootstrap_seed=20261002,
        bootstrap_b=1000,
    )

    assert decision.decision == "ACCEPT"
    assert decision.accept is True
    assert decision.decision_reason == "ACCEPTED"
    assert decision.rejection_category is None
    assert len(decision.rejection_reasons) == 0


# =============================================================================
# FIXTURE B: UCB_R Exceeds epsilon_R -> STATISTICAL_GATE_REJECTION
# =============================================================================
def test_contract_fixture_b_overall_risk_rejection():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = build_mock_bootstrap_metrics(
        delta_r=0.0050,
        max_delta_g=0.0100,
        delta_d=0.0050,
        ucb_r=0.0080,         # > 0.0000 (Violates epsilon_R!)
        ucb_max_group=0.0150, # <= 0.0200
        ucb_d=0.0120,         # <= 0.0200
    )

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="theta_prime_b",
        current_model_identifier="theta_t",
        bootstrap_seed=20261002,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert decision.decision_reason == "STATISTICAL_GATE_REJECTION"
    assert decision.rejection_category == "STATISTICAL_GATE_REJECTION"
    assert any("Overall risk violation" in r for r in decision.rejection_reasons)
    assert not any("FAIL-CLOSED" in r for r in decision.rejection_reasons)


# =============================================================================
# FIXTURE C: UCB_max_group Exceeds epsilon_G -> STATISTICAL_GATE_REJECTION
# =============================================================================
def test_contract_fixture_c_subgroup_regression_rejection():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = build_mock_bootstrap_metrics(
        delta_r=-0.0020,
        max_delta_g=0.0250,
        delta_d=0.0100,
        ucb_r=-0.0005,        # <= 0.0000
        ucb_max_group=0.0350, # > 0.0200 (Violates epsilon_G!)
        ucb_d=0.0150,         # <= 0.0200
    )

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="theta_prime_c",
        current_model_identifier="theta_t",
        bootstrap_seed=20261002,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert decision.decision_reason == "STATISTICAL_GATE_REJECTION"
    assert decision.rejection_category == "STATISTICAL_GATE_REJECTION"
    assert any("Subgroup regression violation" in r for r in decision.rejection_reasons)
    assert not any("FAIL-CLOSED" in r for r in decision.rejection_reasons)


# =============================================================================
# FIXTURE D: UCB_D Exceeds epsilon_D -> STATISTICAL_GATE_REJECTION
# =============================================================================
def test_contract_fixture_d_disparity_growth_rejection():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = build_mock_bootstrap_metrics(
        delta_r=-0.0010,
        max_delta_g=0.0100,
        delta_d=0.0220,
        ucb_r=-0.0001,        # <= 0.0000
        ucb_max_group=0.0180, # <= 0.0200
        ucb_d=0.0310,         # > 0.0200 (Violates epsilon_D!)
    )

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="theta_prime_d",
        current_model_identifier="theta_t",
        bootstrap_seed=20261002,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert decision.decision_reason == "STATISTICAL_GATE_REJECTION"
    assert decision.rejection_category == "STATISTICAL_GATE_REJECTION"
    assert any("Disparity growth violation" in r for r in decision.rejection_reasons)
    assert not any("FAIL-CLOSED" in r for r in decision.rejection_reasons)


# =============================================================================
# FIXTURE E: Evaluator Exception -> FAIL_CLOSED_EVALUATOR_ERROR
# =============================================================================
def test_contract_fixture_e_evaluator_exception():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)

    decision = gate.evaluate_decision(
        bootstrap_metrics=None,
        candidate_identifier="theta_prime_e",
        current_model_identifier="theta_t",
        bootstrap_seed=20261002,
        bootstrap_b=1000,
        exception_msg="Audio file not found: common_voice_en_33001339.mp3",
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert decision.decision_reason == "FAIL_CLOSED_EVALUATOR_ERROR"
    assert decision.rejection_category == "FAIL_CLOSED_EVALUATOR_ERROR"
    assert any("FAIL-CLOSED: Evaluator exception occurred" in r for r in decision.rejection_reasons)
    assert math.isnan(decision.delta_r)
    assert math.isinf(decision.ucb_r)


def test_contract_fixture_e_numerical_nan_error():
    """NaN in bootstrap metrics must be classified as FAIL_CLOSED_EVALUATOR_ERROR, not statistical."""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = build_mock_bootstrap_metrics(
        delta_r=float("nan"),  # Numerical corruption!
        ucb_r=float("nan"),
    )

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="theta_prime_nan",
        current_model_identifier="theta_t",
        bootstrap_seed=20261002,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert decision.decision_reason == "FAIL_CLOSED_EVALUATOR_ERROR"
    assert decision.rejection_category == "FAIL_CLOSED_EVALUATOR_ERROR"
    assert any("Metric 'delta_r' is NaN" in r for r in decision.rejection_reasons)
