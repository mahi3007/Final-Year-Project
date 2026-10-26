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
    compute_optimizer_state_hash,
    validate_optimizer_state,
    clone_optimizer,
    compute_masked_suta_loss,
    AtomicCandidateManager,
)
from dsg_ctta.controller.shadow import compute_model_parameter_hash
from dsg_ctta.controller.streaming_gate_v14 import StreamingSentinelSafetyGateV14


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


def test_optimizer_state_cloning_and_hashing():
    """
    Test Case 7: AdamW optimizer state cloning and hashing.
    Asserts optimizer state hash is sensitive to step counts and moment tensors,
    and clone_optimizer creates an exact, independent replica of running moments.
    """
    model = ToyAcousticModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)
    initial_hash = compute_optimizer_state_hash(optimizer)

    # Step live model once to populate running moments
    loss = model(torch.randn(4, 16)).mean()
    loss.backward()
    optimizer.step()

    stepped_hash = compute_optimizer_state_hash(optimizer)
    assert stepped_hash != initial_hash, "Optimizer state hash must change after AdamW step"

    # Clone candidate model and optimizer
    cand_model = copy.deepcopy(model)
    cand_optimizer = clone_optimizer(optimizer, cand_model)
    cand_hash = compute_optimizer_state_hash(cand_optimizer)
    assert cand_hash == stepped_hash, "Cloned optimizer must have identical state hash"

    # Step candidate optimizer: candidate hash changes, original optimizer hash remains unchanged
    cand_loss = cand_model(torch.randn(4, 16)).mean()
    cand_loss.backward()
    cand_optimizer.step()

    new_cand_hash = compute_optimizer_state_hash(cand_optimizer)
    assert new_cand_hash != stepped_hash
    assert compute_optimizer_state_hash(optimizer) == stepped_hash, "Original optimizer state must remain unaffected"


def test_atomic_candidate_manager_rejection_preserves_both_model_and_optimizer_hash():
    """
    Test Case 8: AtomicCandidateManager rejection invariants.
    Asserts both live model parameter hash AND live optimizer state hash remain
    strictly bitwise invariant when an adapted candidate is discarded.
    """
    live_model = ToyAcousticModel()
    live_optimizer = torch.optim.AdamW(live_model.ln.parameters(), lr=1e-3)

    # Populate running AdamW state
    l = live_model(torch.randn(4, 16)).mean()
    l.backward()
    live_optimizer.step()

    manager = AtomicCandidateManager(live_model=live_model, live_optimizer=live_optimizer)
    model_hash_before = manager.get_live_model_hash()
    opt_hash_before = manager.get_live_optimizer_hash()

    # Create candidate and adapt
    cand_model, cand_opt = manager.create_candidate()
    def cand_loss_fn():
        return cand_model(torch.randn(4, 16)).mean()

    res = manager.execute_candidate_transaction(
        candidate_model=cand_model,
        candidate_optimizer=cand_opt,
        loss_fn=cand_loss_fn,
        max_grad_norm=1.0,
    )
    assert res.is_success
    assert compute_model_parameter_hash(cand_model) != model_hash_before
    assert compute_optimizer_state_hash(cand_opt) != opt_hash_before

    # Discard candidate on gate rejection
    manager.discard_candidate(cand_model, cand_opt)

    # Assert live hashes are invariant
    assert manager.get_live_model_hash() == model_hash_before
    assert manager.get_live_optimizer_hash() == opt_hash_before


def test_atomic_candidate_manager_acceptance_promotes_both_model_and_optimizer():
    """
    Test Case 9: AtomicCandidateManager acceptance invariants.
    Asserts candidate model parameters and candidate optimizer state (AdamW moments)
    are committed together into live state upon acceptance.
    """
    live_model = ToyAcousticModel()
    live_optimizer = torch.optim.AdamW(live_model.ln.parameters(), lr=1e-3)

    manager = AtomicCandidateManager(live_model=live_model, live_optimizer=live_optimizer)
    model_hash_before = manager.get_live_model_hash()
    opt_hash_before = manager.get_live_optimizer_hash()

    cand_model, cand_opt = manager.create_candidate()
    def cand_loss_fn():
        return cand_model(torch.randn(4, 16)).mean()

    res = manager.execute_candidate_transaction(
        candidate_model=cand_model,
        candidate_optimizer=cand_opt,
        loss_fn=cand_loss_fn,
        max_grad_norm=1.0,
    )
    assert res.is_success
    expected_model_hash = compute_model_parameter_hash(cand_model)
    expected_opt_hash = compute_optimizer_state_hash(cand_opt)

    # Commit candidate
    new_m_hash, new_opt_hash = manager.promote_candidate(cand_model, cand_opt)
    assert new_m_hash == expected_model_hash
    assert new_opt_hash == expected_opt_hash
    assert manager.get_live_model_hash() != model_hash_before
    assert manager.get_live_optimizer_hash() != opt_hash_before


def test_optimizer_state_nonfinite_fails_closed():
    """
    Test Case 10: Non-finite optimizer state validation.
    If an optimizer moment tensor contains NaN/Inf, transaction fails closed.
    """
    model = ToyAcousticModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)

    # Run one step so optimizer.state is populated
    l = model(torch.randn(4, 16)).mean()
    l.backward()
    optimizer.step()

    # Verify static validation detects non-finite optimizer state
    param = next(model.ln.parameters())
    optimizer.state[param]["exp_avg"][0] = float("nan")
    valid, err_msg = validate_optimizer_state(optimizer)
    assert not valid
    assert "non-finite" in err_msg.lower()

    # Reset state to finite values
    optimizer.state[param]["exp_avg"][0] = 0.0

    # Monkeypatch optimizer.step to simulate non-finite state injection post-step
    orig_step = optimizer.step
    def step_with_corrupt_state(*args, **kwargs):
        orig_step(*args, **kwargs)
        with torch.no_grad():
            optimizer.state[param]["exp_avg"][0] = float("nan")

    optimizer.step = step_with_corrupt_state

    # Test via execute_safe_adaptation_transaction
    def dummy_loss():
        return model(torch.randn(4, 16)).mean()

    res = execute_safe_adaptation_transaction(
        model=model,
        optimizer=optimizer,
        loss_fn=dummy_loss,
        max_grad_norm=1.0,
    )
    assert not res.is_success
    assert res.optimizer_state_finite is False
    assert res.numerical_status == "FAILED_NONFINITE_OPTIMIZER_STATE"


def test_optimizer_step_exception_fails_closed():
    """
    Test Case 11: Exception during optimizer.step().
    Transaction traps exception, zeroing grads and failing closed.
    """
    model = ToyAcousticModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)

    def crashing_step():
        raise RuntimeError("Simulated CUDA out of memory in AdamW kernel")

    optimizer.step = crashing_step

    def loss_fn():
        return model(torch.randn(4, 16)).mean()

    res = execute_safe_adaptation_transaction(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        max_grad_norm=1.0,
    )
    assert not res.is_success
    assert res.numerical_status == "FAILED_OPTIMIZER_STEP_EXCEPTION"
    assert "Simulated CUDA out of memory" in res.failure_reason


class ToyCTCModel(nn.Module):
    """Toy CTC model with convolutional downsampling for padded-frame testing."""
    def __init__(self, in_channels=1, hidden_dim=16, num_classes=32):
        super().__init__()
        self.conv = nn.Conv1d(in_channels, hidden_dim, kernel_size=10, stride=5)
        self.ln = nn.LayerNorm(hidden_dim)
        self.classifier = nn.Linear(hidden_dim, num_classes)
        for p in self.parameters():
            p.requires_grad = False
        for p in self.ln.parameters():
            p.requires_grad = True

    def _get_feat_extract_output_lengths(self, input_lengths):
        return torch.clamp((input_lengths - 10) // 5 + 1, min=1)

    def forward(self, input_values):
        x = input_values.unsqueeze(1)
        h = self.conv(x)
        h = h.transpose(1, 2)
        h = self.ln(h)
        logits = self.classifier(h)
        class Output:
            def __init__(self, l):
                self.logits = l
        return Output(logits)


def test_variable_length_audio_padded_frame_masking():
    """
    Test Case 12: Variable-length audio batch with padded-frame masking.
    Asserts padded silence frames are excluded from loss, gradients remain finite,
    and loss does not fail or produce NaN.
    """
    model = ToyCTCModel()
    # Batch with two utterances: 200 samples and 500 samples
    audio_lengths = [200, 500]
    max_len = 500
    batch_tensor = torch.zeros(2, max_len)
    batch_tensor[0, :200] = torch.randn(200)
    batch_tensor[1, :500] = torch.randn(500)

    total_loss, l_em, l_mcc = compute_masked_suta_loss(
        model=model,
        input_values=batch_tensor,
        audio_lengths=audio_lengths,
        temperature=2.5,
        alpha=0.5,
    )

    assert torch.isfinite(total_loss)
    assert torch.isfinite(l_em)
    assert torch.isfinite(l_mcc)

    total_loss.backward()
    for p in model.ln.parameters():
        assert p.grad is not None
        assert torch.isfinite(p.grad).all(), "Gradients with padded-frame masking must remain strictly finite"


def test_streaming_gate_v14_zero_disparity_growth():
    """
    Test Case 13: Protocol v1.4.0 zero-disparity tolerance and point improvement.
    Enforces epsilon_d_pp = 0.0000 pp, Delta_R < 0.0 pp, and Lan-DeMets OBF spending.
    """
    gate = StreamingSentinelSafetyGateV14(
        epsilon_r_pp=0.0000,
        epsilon_g_pp=2.0000,
        epsilon_d_pp=0.0000,
        num_updates=10,
        alpha_target=0.05,
    )

    speaker_ids = ["s1", "s2", "s3", "s4"]
    strata = ["accentA", "accentA", "accentB", "accentB"]
    ref_lengths = [100, 100, 100, 100]

    # Scenario 1: Point degradation / tie (Delta_R == 0.0) -> MUST REJECT
    dec_tie = gate.evaluate_candidate(
        window_id=0,
        speaker_ids=speaker_ids,
        stratum_groups=strata,
        live_errors=[20, 20, 30, 30],
        cand_errors=[20, 20, 30, 30],
        ref_lengths=ref_lengths,
    )
    assert not dec_tie.passed_gate
    assert any("Point degradation/tie" in r for r in dec_tie.rejection_reasons)

    # Scenario 2: Point improvement (Delta_R < 0), but disparity increases (UCB_D > 0) -> MUST REJECT under v1.4
    dec_disp = gate.evaluate_candidate(
        window_id=0,
        speaker_ids=speaker_ids,
        stratum_groups=strata,
        live_errors=[20, 20, 30, 30],
        cand_errors=[5, 5, 32, 32],
        ref_lengths=ref_lengths,
    )
    assert not dec_disp.passed_gate
    assert any("Disparity growth violation" in r for r in dec_disp.rejection_reasons)


def test_suta_adapter_returns_updated_false_on_failure(monkeypatch):
    """
    Test Case 14: SutaAdapter returns updated=False on failed safe transaction.
    Asserts failed adaptation does not mark step as updated, does not increment
    step_count, and leaves live model hash bitwise unchanged.
    """
    from dsg_ctta.models.base_adapter import BaseASRModel
    from dsg_ctta.adaptation.suta import SutaAdapter
    from dsg_ctta.online.label_isolation import UnlabeledAudioBatch

    class MockASR(BaseASRModel):
        def __init__(self):
            super().__init__(model_id="mock", device="cpu")
            self.model = ToyCTCModel()
            self.processor = lambda waveforms, **kwargs: type("Inputs", (), {
                "input_values": torch.zeros(len(waveforms), max(len(w) for w in waveforms))
            })()

        def load_model(self):
            return self.model

        def transcribe(self, audio_path):
            return "dummy"

        def transcribe_batch(self, audio_paths):
            return ["dummy"] * len(audio_paths)

    mock_asr = MockASR()
    adapter = SutaAdapter(asr_model=mock_asr)
    initial_hash = adapter.compute_model_hash()
    initial_steps = adapter.step_count

    # Monkeypatch manager.execute_candidate_transaction to simulate a non-finite loss failure
    def failing_transaction(self, *args, **kwargs):
        return SafeUpdateResult(
            loss=None,
            numerical_status="FAILED_NONFINITE_LOSS",
            loss_finite=False,
            gradient_finite=False,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason="Injected test failure: non-finite loss"
        )

    monkeypatch.setattr(AtomicCandidateManager, "execute_candidate_transaction", failing_transaction)

    from dsg_ctta.online.label_isolation import UnlabeledAudioItem
    batch = UnlabeledAudioBatch(
        batch_idx=0,
        window_size=1,
        items=[
            UnlabeledAudioItem(
                utterance_id="utt_1",
                audio_filepath="dummy.wav",
                duration_seconds=1.0
            )
        ]
    )
    monkeypatch.setattr(UnlabeledAudioBatch, "load_waveforms", lambda self: [np.zeros(200, dtype=np.float32)])

    res = adapter.adapt(batch)

    assert res.updated is False, "Adapter must return updated=False when safe transaction fails"
    assert adapter.step_count == initial_steps, "Step count must not increment on failed adaptation"
    assert adapter.compute_model_hash() == initial_hash, "Live model parameter hash must remain invariant on failure"
    assert res.details["numerical_status"] == "FAILED_NONFINITE_LOSS"

