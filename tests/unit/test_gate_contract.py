"""
Unit and Contract Tests for Disparity Safety Gate Decision Logic.
=================================================================
Validates the canonical tripartite UCB decision rule and synthetic contract cases (Cases 1-7).
"""

import pytest
import math
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.types import BootstrapMetrics, GateDecision


def create_mock_metrics(
    ucb_r: float = 0.0000,
    ucb_max_group: float = 0.0100,
    ucb_d: float = 0.0100,
    delta_r: float = 0.0,
    max_delta_g: float = 0.01,
    delta_d: float = 0.01,
    group_deltas: dict = None,
) -> BootstrapMetrics:
    if group_deltas is None:
        group_deltas = {"group_A": 0.005, "group_B": 0.010}
    return BootstrapMetrics(
        delta_r=delta_r,
        max_delta_g=max_delta_g,
        delta_d=delta_d,
        ucb_r=ucb_r,
        ucb_max_group=ucb_max_group,
        ucb_d=ucb_d,
        group_deltas=group_deltas,
        group_ucbs={g: d + 0.005 for g, d in group_deltas.items()},
        replicates_computed=1000,
        omitted_groups_count=0,
    )


def test_gate_accept_when_all_constraints_satisfied():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=0.0000, ucb_max_group=0.0150, ucb_d=0.0120)

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="cand_01",
        current_model_identifier="live_01",
        bootstrap_seed=42,
        bootstrap_b=1000,
    )

    assert decision.decision == "ACCEPT"
    assert decision.accept is True
    assert len(decision.rejection_reasons) == 0


def test_gate_reject_when_ucb_r_exceeds_epsilon_r():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=0.0001, ucb_max_group=0.0100, ucb_d=0.0100)

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="cand_02",
        current_model_identifier="live_01",
        bootstrap_seed=42,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("Overall risk violation" in r for r in decision.rejection_reasons)


def test_gate_reject_when_max_group_ucb_exceeds_epsilon_g():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=-0.0100, ucb_max_group=0.0201, ucb_d=0.0100)

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="cand_03",
        current_model_identifier="live_01",
        bootstrap_seed=42,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("Subgroup regression violation" in r for r in decision.rejection_reasons)


def test_gate_reject_when_disparity_ucb_exceeds_epsilon_d():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=-0.0100, ucb_max_group=0.0100, ucb_d=0.0205)

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="cand_04",
        current_model_identifier="live_01",
        bootstrap_seed=42,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("Disparity growth violation" in r for r in decision.rejection_reasons)


def test_gate_reject_when_multiple_constraints_fail():
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=0.0050, ucb_max_group=0.0300, ucb_d=0.0400)

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="cand_05",
        current_model_identifier="live_01",
        bootstrap_seed=42,
        bootstrap_b=1000,
    )

    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert len(decision.rejection_reasons) == 3


def test_exact_boundary_equality_passes():
    """UCB == epsilon must PASS (less-than-or-equal condition)."""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=0.0000, ucb_max_group=0.0200, ucb_d=0.0200)

    decision = gate.evaluate_decision(
        bootstrap_metrics=metrics,
        candidate_identifier="cand_boundary",
        current_model_identifier="live_01",
        bootstrap_seed=42,
        bootstrap_b=1000,
    )

    assert decision.decision == "ACCEPT"
    assert decision.accept is True


# =========================================================================
# PHASE G: SYNTHETIC CONTRACT CASES (Cases 1-7)
# =========================================================================

def test_synthetic_case_1_no_regression_no_disparity():
    """CASE 1: No regression, no disparity increase -> ACCEPT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=-0.0050, ucb_max_group=0.0000, ucb_d=0.0000)
    d = gate.evaluate_decision(metrics, "c1", "l1", 42, 1000)
    assert d.decision == "ACCEPT"


def test_synthetic_case_2_overall_regression_exceeds():
    """CASE 2: Overall regression > 0, UCB_R > epsilon_R -> REJECT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=0.0050, ucb_max_group=0.0100, ucb_d=0.0100)
    d = gate.evaluate_decision(metrics, "c2", "l1", 42, 1000)
    assert d.decision == "REJECT"
    assert any("Overall risk" in r for r in d.rejection_reasons)


def test_synthetic_case_3_subgroup_regresses_beyond_epsilon_g():
    """CASE 3: One subgroup regresses beyond epsilon_G -> REJECT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(
        ucb_r=-0.0010,
        ucb_max_group=0.0350,
        ucb_d=0.0150,
        group_deltas={"group_A": -0.01, "group_B": 0.03},
    )
    d = gate.evaluate_decision(metrics, "c3", "l1", 42, 1000)
    assert d.decision == "REJECT"
    assert any("Subgroup regression" in r for r in d.rejection_reasons)


def test_synthetic_case_4_overall_improves_but_subgroup_regresses():
    """CASE 4: Overall WER improves, but one subgroup regresses enough -> REJECT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(
        ucb_r=-0.0500,  # Great overall improvement!
        ucb_max_group=0.0250,  # But one group regressed > 0.0200
        ucb_d=0.0100,
        group_deltas={"group_A": -0.08, "group_B": 0.022},
    )
    d = gate.evaluate_decision(metrics, "c4", "l1", 42, 1000)
    assert d.decision == "REJECT"
    assert any("Subgroup regression" in r for r in d.rejection_reasons)


def test_synthetic_case_5_disparity_flat_but_subgroup_regresses():
    """CASE 5: Whole-group disparity does not increase, but subgroup regression violates epsilon_G -> REJECT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(
        ucb_r=0.0000,
        ucb_max_group=0.0250,
        ucb_d=-0.0100,  # Disparity actually shrunk!
        group_deltas={"group_A": 0.022, "group_B": 0.015},
    )
    d = gate.evaluate_decision(metrics, "c5", "l1", 42, 1000)
    assert d.decision == "REJECT"
    assert any("Subgroup regression" in r for r in d.rejection_reasons)


def test_synthetic_case_6_all_metrics_within_thresholds():
    """CASE 6: All metrics within thresholds -> ACCEPT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(
        ucb_r=-0.0020,
        ucb_max_group=0.0180,
        ucb_d=0.0190,
    )
    d = gate.evaluate_decision(metrics, "c6", "l1", 42, 1000)
    assert d.decision == "ACCEPT"


def test_synthetic_case_7_nan_in_metric_rejects():
    """CASE 7: NaN in one metric -> REJECT"""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(
        ucb_r=float("nan"),
        ucb_max_group=0.0100,
        ucb_d=0.0100,
    )
    d = gate.evaluate_decision(metrics, "c7", "l1", 42, 1000)
    assert d.decision == "REJECT"
    assert any("NaN" in r for r in d.rejection_reasons)


def test_decision_serialization_deterministic():
    """Verify deterministic JSON and dictionary serialization."""
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    metrics = create_mock_metrics(ucb_r=0.0000, ucb_max_group=0.0150, ucb_d=0.0120)
    d = gate.evaluate_decision(metrics, "cand_ser", "live_ser", 20261002, 1000)

    json_str_1 = d.to_json()
    json_str_2 = d.to_json()
    assert json_str_1 == json_str_2
    assert "ACCEPT" in json_str_1
    assert "epsilon_r" in json_str_1
