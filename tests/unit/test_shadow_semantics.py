"""
Unit Tests for Shadow Candidate Architecture and Immutability Semantics.
========================================================================
Validates that:
1. Live model theta_t is never mutated during candidate adaptation or evaluation.
2. REJECT strictly preserves theta_t bit-for-bit (SHA-256 identical).
3. ACCEPT correctly promotes candidate theta' to live model.
4. REJECT discards candidate without rolling back to theta_(t-1).
"""

import copy
import pytest
import torch
import torch.nn as nn

from dsg_ctta.controller.shadow import (
    ShadowCandidateManager,
    compute_model_parameter_hash,
)
from dsg_ctta.controller.types import GateDecision


class SimpleAdapterModule(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(16, 16)
        self.bias = nn.Parameter(torch.zeros(16))

    def forward(self, x):
        return self.fc(x) + self.bias


def create_mock_decision(accept: bool) -> GateDecision:
    return GateDecision(
        decision="ACCEPT" if accept else "REJECT",
        accept=accept,
        delta_r=0.0,
        delta_g={},
        max_delta_g=0.0,
        delta_d=0.0,
        ucb_r=0.0,
        ucb_max_group=0.0,
        ucb_d=0.0,
        epsilon_r=0.0,
        epsilon_g=0.02,
        epsilon_d=0.02,
        rejection_reasons=[] if accept else ["Violation"],
        candidate_identifier="cand",
        current_model_identifier="live",
        bootstrap_seed=42,
        bootstrap_b=1000,
        timestamp="2026-10-02T20:00:00Z",
    )


def test_reject_preserves_live_model_bit_for_bit():
    """REJECT must return live model theta_t with bit-for-bit identical parameter hash."""
    torch.manual_seed(42)
    live_model = SimpleAdapterModule()
    pre_hash = compute_model_parameter_hash(live_model)

    # Create candidate clone and adapt it
    candidate = ShadowCandidateManager.create_candidate_clone(live_model)
    with torch.no_grad():
        candidate.bias.add_(1.0)  # Mutate candidate

    cand_hash = compute_model_parameter_hash(candidate)
    assert pre_hash != cand_hash, "Candidate must differ from live model"

    # Gate decision: REJECT
    reject_decision = create_mock_decision(accept=False)

    next_model = ShadowCandidateManager.apply_transition(
        live_model=live_model,
        candidate_model=candidate,
        decision=reject_decision,
        pre_adaptation_hash=pre_hash,
    )

    post_hash = compute_model_parameter_hash(next_model)
    assert post_hash == pre_hash, "Live model parameter hash must be bit-for-bit preserved"
    assert next_model is live_model, "Live model reference must be retained on REJECT"


def test_accept_installs_candidate_exactly():
    """ACCEPT must install candidate theta' as the next model."""
    torch.manual_seed(42)
    live_model = SimpleAdapterModule()
    pre_hash = compute_model_parameter_hash(live_model)

    candidate = ShadowCandidateManager.create_candidate_clone(live_model)
    with torch.no_grad():
        candidate.bias.add_(2.5)

    cand_hash = compute_model_parameter_hash(candidate)

    accept_decision = create_mock_decision(accept=True)

    next_model = ShadowCandidateManager.apply_transition(
        live_model=live_model,
        candidate_model=candidate,
        decision=accept_decision,
        pre_adaptation_hash=pre_hash,
    )

    next_hash = compute_model_parameter_hash(next_model)
    assert next_hash == cand_hash, "Next model must match candidate parameter hash exactly"
    assert next_model is candidate, "Candidate model reference must be returned on ACCEPT"


def test_rejection_never_rolls_back_to_t_minus_1():
    """
    Sequence of 3 windows:
    Window 1: Accept -> theta_1 installed
    Window 2: Reject -> theta_2 = theta_1 (retains theta_1, NEVER rolls back to theta_0)
    """
    torch.manual_seed(100)
    theta_0 = SimpleAdapterModule()
    hash_0 = compute_model_parameter_hash(theta_0)

    # Window 1: Accept
    cand_1 = ShadowCandidateManager.create_candidate_clone(theta_0)
    with torch.no_grad():
        cand_1.bias.add_(0.5)
    hash_1 = compute_model_parameter_hash(cand_1)

    theta_1 = ShadowCandidateManager.apply_transition(theta_0, cand_1, create_mock_decision(True), hash_0)
    assert compute_model_parameter_hash(theta_1) == hash_1

    # Window 2: Candidate adapted from theta_1 is rejected
    cand_2 = ShadowCandidateManager.create_candidate_clone(theta_1)
    with torch.no_grad():
        cand_2.bias.add_(5.0)  # Bad update

    theta_2 = ShadowCandidateManager.apply_transition(theta_1, cand_2, create_mock_decision(False), hash_1)
    hash_2 = compute_model_parameter_hash(theta_2)

    # Must be theta_1, NOT theta_0!
    assert hash_2 == hash_1, "Rejection must retain theta_t, not revert to theta_{t-1}"
    assert hash_2 != hash_0, "Rejection must not erase earlier accepted updates"


def test_immutability_assertion_fails_if_live_model_mutated():
    """If someone accidentally mutates live_model in-place, assertion must trip."""
    live_model = SimpleAdapterModule()
    pre_hash = compute_model_parameter_hash(live_model)

    # Malicious or buggy in-place mutation
    with torch.no_grad():
        live_model.bias.add_(999.0)

    with pytest.raises(AssertionError, match="CRITICAL IMMUTABILITY BREACH"):
        ShadowCandidateManager.apply_transition(
            live_model=live_model,
            candidate_model=live_model,
            decision=create_mock_decision(False),
            pre_adaptation_hash=pre_hash,
        )
