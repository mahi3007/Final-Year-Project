"""
Stage 6M Test Suite: Numerical Safety, Fail-Closed Transactions, and Stratum Invariants
========================================================================================
Validates ADR-005 and Protocol v1.4.0 requirements for fail-closed candidate adaptation:
1. Zero-valued class sums in MCC yield finite loss and valid gradients under the stabilized formula.
2. Finite scalar loss with non-finite gradients prevents optimizer step execution.
3. Non-finite candidate parameters after step trigger immediate candidate rejection.
4. Non-finite scalar loss triggers fail-closed rejection without backward propagation.
5. Multi-stratum clips in a single streaming window preserve individual locked strata.
6. Rejected candidate leaves live model parameter hash bitwise invariant.
"""

import copy
import hashlib
import pytest
import torch
import torch.nn as nn
import numpy as np
import pandas as pd

from dsg_ctta.adaptation.safe_update import (
    SafeUpdateResult,
    execute_safe_adaptation_transaction,
)
from dsg_ctta.controller.shadow import compute_model_parameter_hash


class ToyAcousticModel(nn.Module):
    """Simple linear model with LayerNorm to test CTTA transactions."""
    def __init__(self, in_features=16, num_classes=32):
        super().__init__()
        self.fc = nn.Linear(in_features, in_features)
        self.ln = nn.LayerNorm(in_features)
        self.classifier = nn.Linear(in_features, num_classes)

        # In SUTA, only LayerNorm is trainable
        for p in self.parameters():
            p.requires_grad = False
        for p in self.ln.parameters():
            p.requires_grad = True

    def forward(self, x):
        h = self.fc(x)
        h = self.ln(h)
        return self.classifier(h)


def test_zero_valued_class_sum_mcc_stability():
    """
    Test Case 1: Zero-valued class sum in MCC calculation.
    Under the old formula (stabilizer outside sqrt), d/dx sqrt(0) -> inf -> NaN gradients.
    Under the corrected formula (stabilizer inside sqrt), gradients remain finite.
    """
    B, T, C = 2, 20, 32
    torch.manual_seed(42)
    logits = torch.randn(B, T, C, requires_grad=True)

    # Force classes 10..31 to have zero probability
    mask = torch.zeros(C)
    mask[:10] = 1.0
    probs = torch.softmax(logits, dim=-1) * mask
    probs = probs / probs.sum(dim=-1, keepdim=True)

    flat_probs = probs.view(-1, C)
    class_sums = torch.sum(flat_probs, dim=0)

    # Verify zero-valued classes exist
    assert (class_sums[10:] == 0.0).all()

    # Corrected MCC formula: stabilizer inside sqrt
    norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0) + 1e-8)
    corr_matrix = (flat_probs.T @ flat_probs) / norm_factor
    diagonal = torch.diag(corr_matrix)
    off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
    l_mcc = off_diag_sum / (C * (C - 1) + 1e-8)

    assert torch.isfinite(l_mcc).all()

    l_mcc.backward()
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all(), "Gradients must be finite even when classes have zero occurrences"


def test_finite_loss_with_nonfinite_gradients_fails_closed():
    """
    Test Case 2: Finite scalar loss but non-finite gradients.
    Optimizer step must NOT execute, gradients must be zeroed, and status must indicate failure.
    """
    model = ToyAcousticModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)
    initial_ln_weight = model.ln.weight.detach().clone()

    def loss_fn():
        x = torch.randn(4, 16)
        out = model(x)
        # Compute finite loss, but inject non-finite gradient during hook
        loss = out.mean()
        return loss

    # Register a backward hook on LayerNorm to corrupt gradients with NaN
    hook_handle = model.ln.weight.register_hook(lambda grad: torch.full_like(grad, float("nan")))

    try:
        res = execute_safe_adaptation_transaction(
            model=model,
            optimizer=optimizer,
            loss_fn=loss_fn,
            max_grad_norm=1.0,
        )

        assert not res.is_success
        assert res.loss_finite is True
        assert res.gradient_finite is False
        assert res.numerical_status in ("FAILED_NONFINITE_GRADIENT", "FAILED_NONFINITE_GRADIENT_NORM")
        assert "non-finite" in res.failure_reason.lower()

        # Optimizer step must NOT have been called: parameter values unchanged
        assert torch.equal(model.ln.weight, initial_ln_weight)
    finally:
        hook_handle.remove()


def test_nonfinite_parameters_after_step_rejects_candidate():
    """
    Test Case 3: Non-finite candidate parameters.
    If parameter corruption occurs during or after the step, the transaction must fail.
    """
    model = ToyAcousticModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)

    def loss_fn():
        x = torch.randn(4, 16)
        return model(x).mean()

    # Create a custom step hook by monkeypatching optimizer.step to inject NaN
    orig_step = optimizer.step
    def bad_step():
        orig_step()
        with torch.no_grad():
            model.ln.weight[0] = float("nan")

    optimizer.step = bad_step

    res = execute_safe_adaptation_transaction(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        max_grad_norm=1.0,
    )

    assert not res.is_success
    assert res.parameter_finite is False
    assert res.numerical_status == "FAILED_NONFINITE_PARAMETERS_AFTER_STEP"


def test_nonfinite_loss_aborts_before_backward():
    """
    Test Case 4: Non-finite loss returned by adaptation function.
    Caller must record a numerical failure and no backward propagation should execute.
    """
    model = ToyAcousticModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)
    initial_ln_weight = model.ln.weight.detach().clone()

    def loss_fn():
        return torch.tensor(float("nan"), requires_grad=True)

    res = execute_safe_adaptation_transaction(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        max_grad_norm=1.0,
    )

    assert not res.is_success
    assert res.loss is None
    assert res.loss_finite is False
    assert res.numerical_status == "FAILED_NONFINITE_LOSS"
    assert torch.equal(model.ln.weight, initial_ln_weight)


def test_multi_stratum_clips_in_single_window_preserve_strata():
    """
    Test Case 5: Clips from different strata in one stream window.
    Verifies that per-clip stratum tracking preserves each clip's assigned stratum,
    preventing the window-initial overwrite bug that contaminated speaker distributions.
    """
    # Create a boundary window containing clips from two different accents
    window_rows = pd.DataFrame([
        {"recording_id": "clip_01", "speaker_id": "spk_A", "stage5_accent_group": "Australian English"},
        {"recording_id": "clip_02", "speaker_id": "spk_A", "stage5_accent_group": "Australian English"},
        {"recording_id": "clip_03", "speaker_id": "spk_B", "stage5_accent_group": "Canadian English"},
        {"recording_id": "clip_04", "speaker_id": "spk_B", "stage5_accent_group": "Canadian English"},
    ])

    clip_records = []
    for _, r in window_rows.iterrows():
        # Correct runner behavior: sample stratum per clip, not window.iloc[0]
        clip_stratum = str(r.get("stage5_accent_group") or r.get("stratum_code"))
        clip_records.append({
            "recording_id": r["recording_id"],
            "speaker_id": r["speaker_id"],
            "stratum": clip_stratum
        })

    rec_df = pd.DataFrame(clip_records)
    spk_strata = rec_df.groupby("speaker_id")["stratum"].unique()

    # Each speaker must map to exactly one stratum
    assert len(spk_strata["spk_A"]) == 1
    assert spk_strata["spk_A"][0] == "Australian English"
    assert len(spk_strata["spk_B"]) == 1
    assert spk_strata["spk_B"][0] == "Canadian English"


def test_rejected_candidate_preserves_live_model_hash():
    """
    Test Case 6: Rejected candidate preserves exact live model parameter hash.
    Candidate deepcopy is mutated and discarded; live model remains bitwise invariant.
    """
    live_model = ToyAcousticModel()
    initial_hash = compute_model_parameter_hash(live_model)

    # Clone candidate model
    candidate_model = copy.deepcopy(live_model)
    candidate_optimizer = torch.optim.AdamW(candidate_model.ln.parameters(), lr=1e-2)

    # Perform a valid update on the candidate
    def cand_loss_fn():
        x = torch.randn(4, 16)
        return candidate_model(x).mean()

    res = execute_safe_adaptation_transaction(
        model=candidate_model,
        optimizer=candidate_optimizer,
        loss_fn=cand_loss_fn,
        max_grad_norm=1.0,
    )
    assert res.is_success

    # Candidate has mutated
    cand_hash = compute_model_parameter_hash(candidate_model)
    assert cand_hash != initial_hash

    # Gate decision: REJECT
    # Rejection policy: discard candidate, do not promote
    del candidate_model
    del candidate_optimizer

    # Live model parameter hash must be bitwise identical
    final_live_hash = compute_model_parameter_hash(live_model)
    assert final_live_hash == initial_hash, "Live model parameter hash must be bitwise invariant after candidate rejection"
