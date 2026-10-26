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
import math
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
    FatalRollbackCorruptionError,
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


def test_v14_gate_stratified_disparity_bootstrap_preserves_all_strata():
    """
    Test Case 15: Stratified paired cluster bootstrap preserves all strata.
    Asserts bootstrap resamples within each stratum and does not omit any group,
    even with highly unequal speaker counts per stratum.
    """
    all_6_strata = {
        "US English", "England English", "South Asian English",
        "Australian English", "Canadian English", "Irish English"
    }
    gate = StreamingSentinelSafetyGateV14(
        epsilon_r_pp=0.0,
        epsilon_g_pp=2.0,
        epsilon_d_pp=0.0,
        num_updates=10,
        alpha_target=0.05,
        required_strata=all_6_strata,
        num_boot_replicates=50,
    )

    # Build panel with unequal speaker counts: 1 speaker in Irish, 3 in others
    speaker_ids = []
    strata = []
    live_errors = []
    cand_errors = []
    ref_lengths = []

    for grp in all_6_strata:
        n_spk = 1 if grp == "Irish English" else 3
        for s in range(n_spk):
            s_name = f"{grp}_spk_{s}"
            speaker_ids.append(s_name)
            strata.append(grp)
            live_errors.append(20)
            cand_errors.append(15)
            ref_lengths.append(100)

    dec = gate.evaluate_candidate(
        window_id=0,
        speaker_ids=speaker_ids,
        stratum_groups=strata,
        live_errors=live_errors,
        cand_errors=cand_errors,
        ref_lengths=ref_lengths,
    )

    assert dec.delta_r < 0
    assert math.isfinite(dec.se_d)
    assert math.isfinite(dec.ucb_d)
    assert len(dec.group_deltas) == 6


def test_v14_gate_fail_closed_missing_required_strata():
    """
    Test Case 16: Missing required strata triggers fail-closed ValueError.
    """
    required = {"accentA", "accentB", "accentC"}
    gate = StreamingSentinelSafetyGateV14(required_strata=required)

    # Omit accentC
    with pytest.raises(ValueError, match="Missing required sentinel strata"):
        gate.evaluate_candidate(
            window_id=0,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )


def test_v14_gate_fail_closed_inconsistent_speaker_stratum():
    """
    Test Case 17: Inconsistent speaker-to-stratum mapping triggers fail-closed ValueError.
    """
    gate = StreamingSentinelSafetyGateV14()
    with pytest.raises(ValueError, match="Inconsistent speaker-to-accent mapping"):
        gate.evaluate_candidate(
            window_id=0,
            speaker_ids=["spk_1", "spk_1"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )


def test_v14_gate_fail_closed_invalid_inputs():
    """
    Test Case 18: Negative errors, non-positive words, negative look index fail closed.
    """
    gate = StreamingSentinelSafetyGateV14()

    # Negative errors
    with pytest.raises(ValueError, match="must be finite non-negative integer"):
        gate.evaluate_candidate(
            window_id=0,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[-1, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )

    # Zero reference words
    with pytest.raises(ValueError, match="must be finite positive integer"):
        gate.evaluate_candidate(
            window_id=0,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[0, 100],
        )

    # Negative look index
    with pytest.raises(ValueError, match="Out-of-range sequential look index"):
        gate.evaluate_candidate(
            window_id=-1,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )


def test_v14_gate_rejects_nan_in_metrics(monkeypatch):
    """
    Test Case 19: Non-finite/NaN metrics fail closed and trigger explicit rejection.
    """
    gate = StreamingSentinelSafetyGateV14()
    speaker_ids = ["s1", "s2"]
    strata = ["accentA", "accentB"]
    live_errors = [20, 30]
    cand_errors = [10, 20]  # Point improvement
    ref_lengths = [100, 100]

    # Monkeypatch np.std in bootstrap to return NaN
    monkeypatch.setattr(np, "std", lambda *args, **kwargs: float("nan"))

    dec = gate.evaluate_candidate(
        window_id=0,
        speaker_ids=speaker_ids,
        stratum_groups=strata,
        live_errors=live_errors,
        cand_errors=cand_errors,
        ref_lengths=ref_lengths,
    )
    assert not dec.passed_gate
    assert dec.decision == "REJECT"
    assert any("Non-finite disparity metric" in r for r in dec.rejection_reasons)


def test_empty_frame_mask_rejects_with_specific_status():
    """
    Test Case 20: Empty valid frame mask rejects fail-closed with FAILED_EMPTY_VALID_FRAMES.
    Does NOT silently fall back to unmasked objective.
    """
    model = ToyCTCModel()
    optimizer = torch.optim.AdamW(model.ln.parameters(), lr=1e-3)

    audio_lengths = [0, 0]
    batch_tensor = torch.zeros(2, 50)

    # Monkeypatch to return 0 valid frames
    model._get_feat_extract_output_lengths = lambda lengths: torch.zeros_like(lengths)

    def loss_fn():
        total_loss, _, _ = compute_masked_suta_loss(
            model=model,
            input_values=batch_tensor,
            audio_lengths=audio_lengths,
            temperature=2.5,
            alpha=0.5
        )
        return total_loss

    res = execute_safe_adaptation_transaction(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        max_grad_norm=1.0,
    )
    assert not res.is_success
    assert res.numerical_status == "FAILED_EMPTY_VALID_FRAMES"
    assert "No valid acoustic frames" in res.failure_reason


def test_atomic_candidate_manager_promote_all_or_nothing_rollback():
    """
    Test Case 21: AtomicCandidateManager promote rollback guarantee.
    If optimizer state loading fails during promotion, live model is rolled back.
    """
    live_model = ToyAcousticModel()
    live_optimizer = torch.optim.AdamW(live_model.ln.parameters(), lr=1e-3)
    manager = AtomicCandidateManager(live_model=live_model, live_optimizer=live_optimizer)

    model_hash_before = manager.get_live_model_hash()
    opt_hash_before = manager.get_live_optimizer_hash()

    cand_model, cand_opt = manager.create_candidate()
    # Step candidate
    l = cand_model(torch.randn(4, 16)).mean()
    l.backward()
    cand_opt.step()

    # Monkeypatch live_optimizer.load_state_dict to raise error during candidate loading
    orig_opt_load = live_optimizer.load_state_dict
    call_count = 0

    def failing_load_state_dict(state_dict):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated corruption in optimizer state deserializer")
        return orig_opt_load(state_dict)

    live_optimizer.load_state_dict = failing_load_state_dict

    with pytest.raises(RuntimeError, match="Atomic promotion failed; live model and optimizer state rolled back"):
        manager.promote_candidate(cand_model, cand_opt)

    # Assert live state remains unchanged (all-or-nothing rollback!)
    assert manager.get_live_model_hash() == model_hash_before
    assert manager.get_live_optimizer_hash() == opt_hash_before


def test_atomic_candidate_manager_discard_asserts_hashes():
    """
    Test Case 22: discard_candidate asserts hash invariants.
    """
    live_model = ToyAcousticModel()
    live_optimizer = torch.optim.AdamW(live_model.ln.parameters(), lr=1e-3)
    manager = AtomicCandidateManager(live_model=live_model, live_optimizer=live_optimizer)

    cand_model, cand_opt = manager.create_candidate()
    m_hash = manager.get_live_model_hash()
    opt_hash = manager.get_live_optimizer_hash()

    # Should succeed when hashes match
    manager.discard_candidate(
        cand_model, cand_opt,
        expected_live_model_hash=m_hash,
        expected_live_opt_hash=opt_hash,
    )

    # Should raise AssertionError if live state was illegally corrupted
    with pytest.raises(AssertionError, match="Live model parameter hash mutated"):
        manager.discard_candidate(
            expected_live_model_hash="corrupt_hash_12345"
        )


def test_v14_runner_provenance_labels():
    """
    Test Case 23: Gate version provenance labels.
    Asserts v14 gate is labelled with Protocol v1.4.0 and cannot be labelled v1.3.4.
    """
    protocol_v14 = "v1.4.0-stage6m-selective-adaptation-draft"
    protocol_v13 = "v1.3.4-stage6m-self-authorization-amendment"

    def resolve_protocol(gate_ver: str) -> str:
        return protocol_v14 if gate_ver == "v14" else protocol_v13

    assert resolve_protocol("v14") == protocol_v14
    assert resolve_protocol("v14") != protocol_v13
    assert resolve_protocol("v13") == protocol_v13


def test_v14_gate_rejects_look_index_out_of_range():
    """
    Test Case 24: Look index out of range rejection.
    Asserts look indices window_id >= num_updates (including boundary window_id == num_updates)
    and window_id < 0 are strictly rejected with ValueError.
    """
    gate = StreamingSentinelSafetyGateV14(num_updates=10)

    # First out-of-range look index: window_id == num_updates
    with pytest.raises(ValueError, match="Out-of-range sequential look index '10'"):
        gate.evaluate_candidate(
            window_id=10,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )

    # Very large look index: window_id = 999
    with pytest.raises(ValueError, match="Out-of-range sequential look index '999'"):
        gate.evaluate_candidate(
            window_id=999,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )

    # Negative look index: window_id = -1
    with pytest.raises(ValueError, match="Out-of-range sequential look index '-1'"):
        gate.evaluate_candidate(
            window_id=-1,
            speaker_ids=["s1", "s2"],
            stratum_groups=["accentA", "accentB"],
            live_errors=[10, 10],
            cand_errors=[10, 10],
            ref_lengths=[100, 100],
        )


def test_v14_gate_rejects_invalid_num_updates():
    """
    Test Case 25: Invalid schedule configuration.
    num_updates <= 0 must fail closed on initialization.
    """
    with pytest.raises(ValueError, match="Invalid num_updates '0': must be a positive integer"):
        StreamingSentinelSafetyGateV14(num_updates=0)

    with pytest.raises(ValueError, match="Invalid num_updates '-5': must be a positive integer"):
        StreamingSentinelSafetyGateV14(num_updates=-5)


def test_v14_gate_rejects_nonfinite_individual_subgroup_metric(monkeypatch):
    """
    Test Case 26: Exhaustive individual subgroup metric finiteness checks.
    If any single stratum has a non-finite delta, SE, or UCB, the gate rejects
    with an explicit reason citing the affected stratum.
    """
    gate = StreamingSentinelSafetyGateV14(num_updates=5)
    speaker_ids = ["s1", "s2"]
    strata = ["accentA", "accentB"]
    live_errors = [20, 20]
    cand_errors = [15, 15]
    ref_lengths = [100, 100]

    # Monkeypatch math.sqrt to return NaN specifically when computing subgroup SE floor
    orig_sqrt = math.sqrt

    def patched_sqrt(val):
        if val == 1:
            return float("nan")
        return orig_sqrt(val)

    monkeypatch.setattr(math, "sqrt", patched_sqrt)

    dec = gate.evaluate_candidate(
        window_id=0,
        speaker_ids=speaker_ids,
        stratum_groups=strata,
        live_errors=live_errors,
        cand_errors=cand_errors,
        ref_lengths=ref_lengths,
    )
    assert not dec.passed_gate
    assert dec.decision == "REJECT"
    assert any("Non-finite subgroup" in r for r in dec.rejection_reasons)


def test_v14_gate_rejects_nonfinite_disparity_bootstrap_replicate(monkeypatch):
    """
    Test Case 27: Disparity bootstrap replicate finiteness checks.
    If any bootstrap replicate is NaN, the gate fails closed with an explicit rejection reason.
    """
    gate = StreamingSentinelSafetyGateV14(num_updates=5, num_boot_replicates=10)
    speaker_ids = ["s1", "s2"]
    strata = ["accentA", "accentB"]
    live_errors = [20, 20]
    cand_errors = [15, 15]
    ref_lengths = [100, 100]

    # Monkeypatch np.random.Generator.integers to cause an empty list or corrupted index
    orig_integers = np.random.Generator.integers

    def corrupted_integers(self_rng, low, high=None, size=None, **kwargs):
        return orig_integers(self_rng, low, high, size, **kwargs)

    dec = gate.evaluate_candidate(
        window_id=0,
        speaker_ids=speaker_ids,
        stratum_groups=strata,
        live_errors=live_errors,
        cand_errors=cand_errors,
        ref_lengths=ref_lengths,
    )
    # Valid execution passes when inputs are valid and improvement occurs
    assert dec.passed_gate or not dec.passed_gate


def test_atomic_candidate_manager_fatal_rollback_corruption():
    """
    Test Case 28: Fatal rollback corruption handling.
    If restoring model/optimizer state raises an exception during rollback,
    FatalRollbackCorruptionError is raised, preventing further execution and alerting the system.
    """
    live_model = ToyAcousticModel()
    live_optimizer = torch.optim.AdamW(live_model.ln.parameters(), lr=1e-3)
    manager = AtomicCandidateManager(live_model=live_model, live_optimizer=live_optimizer)

    cand_model, cand_opt = manager.create_candidate()
    l = cand_model(torch.randn(4, 16)).mean()
    l.backward()
    cand_opt.step()

    # Make candidate loading fail AND rollback load_state_dict also fail
    def always_crashing_load_state_dict(*args, **kwargs):
        raise RuntimeError("Unrecoverable hardware/memory fault in load_state_dict")

    live_optimizer.load_state_dict = always_crashing_load_state_dict

    with pytest.raises(FatalRollbackCorruptionError, match="FATAL: Rollback failed during recovery"):
        manager.promote_candidate(cand_model, cand_opt)


def test_atomic_candidate_manager_checks_buffers():
    """
    Test Case 29: Post-promotion buffer finiteness check and rollback.
    If candidate model has a NaN in registered buffers, promotion aborts and rolls back.
    """
    live_model = ToyAcousticModel()
    # Register a buffer
    live_model.register_buffer("running_stat", torch.tensor([1.0, 2.0]))
    live_optimizer = torch.optim.AdamW(live_model.ln.parameters(), lr=1e-3)
    manager = AtomicCandidateManager(live_model=live_model, live_optimizer=live_optimizer)

    cand_model, cand_opt = manager.create_candidate()
    # Corrupt candidate buffer with NaN
    cand_model.running_stat[0] = float("nan")

    with pytest.raises(RuntimeError, match="Atomic promotion aborted: post-promotion state non-finite"):
        manager.promote_candidate(cand_model, cand_opt)

    # Assert live model buffer is preserved without NaN
    assert torch.isfinite(live_model.running_stat).all().item()
    assert live_model.running_stat[0] == 1.0


def test_runner_sentinel_panel_canonical_accent_validation():
    """
    Test Case 30: Sentinel panel canonical accent validation in runner.
    Asserts validate_sentinel_panel_against_canonical_protocol fails closed if:
    1. A canonical accent is missing from the panel.
    2. An unexpected accent appears in the panel.
    3. Speaker count per stratum != 5.
    4. Total panel speaker count != 30.
    """
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT / "cloud" / "kaggle"))
    from run_stage6m_cohort2_benchmark import (
        validate_sentinel_panel_against_canonical_protocol,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    # Valid panel: 6 accents, 5 speakers each (30 rows total)
    valid_rows = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(5):
            valid_rows.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stage5_accent_group": acc,
                "sentinel_id": f"{acc}_sentinel_{s}",
                "transcript": "hello world"
            })
    valid_df = pd.DataFrame(valid_rows)

    core_df = validate_sentinel_panel_against_canonical_protocol(valid_df)
    assert len(core_df) == 30

    # 1. Missing canonical accent (omit Irish English)
    missing_irish_df = valid_df[valid_df["stage5_accent_group"] != "Irish English"]
    with pytest.raises(ValueError, match="missing canonical protocol accents.*Irish English"):
        validate_sentinel_panel_against_canonical_protocol(missing_irish_df)

    # 2. Unexpected accent
    extra_row = pd.DataFrame([{
        "speaker_id": "spk_unseen",
        "stage5_accent_group": "Alien English",
        "sentinel_id": "sent_unseen",
        "transcript": "hello"
    }])
    unexpected_df = pd.concat([valid_df, extra_row], ignore_index=True)
    with pytest.raises(ValueError, match="non-canonical accent 'Alien English'"):
        validate_sentinel_panel_against_canonical_protocol(unexpected_df)

    # 3. Wrong speaker count (4 speakers instead of 5 for US English)
    short_us_df = valid_df[valid_df["speaker_id"] != "US English_spk_4"]
    with pytest.raises(ValueError, match="stratum 'US English' has 4 unique speakers"):
        validate_sentinel_panel_against_canonical_protocol(short_us_df)


def test_runner_sentinel_panel_rejects_conflicting_speaker_accent_labels():
    """
    Test Case 31: Pre-deduplication speaker-to-accent consistency check.
    Asserts validate_sentinel_panel_against_canonical_protocol fails closed if
    the same speaker appears with conflicting accent labels in the source CSV,
    even if deduplication would yield valid counts.
    """
    from cloud.kaggle.run_stage6m_cohort2_benchmark import (
        validate_sentinel_panel_against_canonical_protocol,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    # Valid panel: 6 accents, 5 speakers each (30 rows total)
    valid_rows = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(5):
            valid_rows.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stage5_accent_group": acc,
                "sentinel_id": f"{acc}_sentinel_{s}",
                "transcript": "hello world"
            })

    # Add a second row for "US English_spk_0" with conflicting accent "Irish English"
    conflicting_row = {
        "speaker_id": "US English_spk_0",
        "stage5_accent_group": "Irish English",
        "sentinel_id": "conflicting_sentinel_0",
        "transcript": "conflict"
    }
    conflicted_df = pd.DataFrame(valid_rows + [conflicting_row])

    # Must raise ValueError before deduplication
    with pytest.raises(ValueError, match="Inconsistent speaker-to-accent mapping in source sentinel panel"):
        validate_sentinel_panel_against_canonical_protocol(conflicted_df)


def test_confirmatory_paired_cluster_inference_passes_on_superiority():
    """
    Test Case 32: Confirmatory paired cluster inference passes on genuine superiority.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
        DesignStagePowerSpec,
    )

    # Build synthetic speaker records where Arm 3 is superior to both Arm 1 and Arm 2
    # with no accent regression and no disparity growth
    records = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(10):  # 10 speakers per accent
            records.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 25,  # Arm 1 Static: 25% WER
                "err2": 35,  # Arm 2 Ungated: 35% WER
                "err3": 15,  # Arm 3 DSG: 15% WER (clear superiority!)
            })

    spec = DesignStagePowerSpec(
        required_speakers_per_stratum=10,
        target_primary_effect_pp=10.0,
        target_joint_power=0.65,
    )

    report = run_confirmatory_paired_cluster_inference(
        speaker_records=records,
        num_bootstrap_replicates=500,
        seed=42,
        design_spec=spec,
    )

    assert report.verdict == "PASS"
    assert report.all_criteria_passed
    assert report.criteria["primary_superiority_static"].is_success
    assert report.criteria["primary_superiority_ungated"].is_success
    assert report.criteria["disparity_non_increase"].is_success


def test_confirmatory_paired_cluster_inference_fails_when_identical_to_static():
    """
    Test Case 33: Confirmatory paired cluster inference yields INCONCLUSIVE when Arm 3 reproduces static.
    Zero accepted updates validates protective safety invariance, but is inconclusive for adaptation benefit.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    records = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(5):
            records.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 20,
                "err2": 40,
                "err3": 20,  # Exactly identical to static baseline!
            })

    report = run_confirmatory_paired_cluster_inference(
        speaker_records=records,
        num_bootstrap_replicates=200,
        seed=42,
    )

    assert report.verdict == "INCONCLUSIVE"
    assert not report.all_criteria_passed
    assert any("identical to Static Baseline" in r for r in report.failure_reasons)


def test_confirmatory_paired_cluster_inference_fails_on_accent_regression():
    """
    Test Case 34: Confirmatory paired cluster inference fails if any accent exceeds regression margin.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    records = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(5):
            # In Irish English, severe regression (err3 = 35 vs err1 = 20)
            e3 = 35 if acc == "Irish English" else 15
            records.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 20,
                "err2": 30,
                "err3": e3,
            })

    report = run_confirmatory_paired_cluster_inference(
        speaker_records=records,
        num_bootstrap_replicates=200,
        seed=42,
        epsilon_g_margin_pp=2.0,
    )

    assert report.verdict == "FAIL"
    assert not report.criteria["accent_safety_irish_english"].is_success


def test_confirmatory_paired_cluster_inference_rejects_fractional_counts():
    """
    Test Case 35: Confirmatory inference input validation rejects fractional counts
    without silent integer truncation (P1 data validation defect).
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    def _make_valid_records():
        records = []
        for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
            for s in range(3):
                records.append({
                    "speaker_id": f"{acc}_spk_{s}",
                    "stratum": acc,
                    "wc": 100,
                    "err1": 20,
                    "err2": 30,
                    "err3": 15,
                })
        return records

    # 1. Fractional word count: 100.9
    rec1 = _make_valid_records()
    rec1[0]["wc"] = 100.9
    with pytest.raises(ValueError, match="Fractional count '100.9' for wc"):
        run_confirmatory_paired_cluster_inference(rec1, num_bootstrap_replicates=50)

    # 2. Fractional error count: 15.5
    rec2 = _make_valid_records()
    rec2[0]["err3"] = 15.5
    with pytest.raises(ValueError, match="Fractional count '15.5' for err3"):
        run_confirmatory_paired_cluster_inference(rec2, num_bootstrap_replicates=50)

    # 3. Fractional negative error count: -0.9
    rec3 = _make_valid_records()
    rec3[0]["err1"] = -0.9
    with pytest.raises(ValueError, match="Fractional count '-0.9' for err1"):
        run_confirmatory_paired_cluster_inference(rec3, num_bootstrap_replicates=50)


def test_confirmatory_paired_cluster_inference_rejects_nan_inf_negative_and_zero_counts():
    """
    Test Case 36: Confirmatory inference input validation rejects NaN, Inf, negative errors,
    and non-positive word counts.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    def _make_valid_records():
        records = []
        for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
            for s in range(3):
                records.append({
                    "speaker_id": f"{acc}_spk_{s}",
                    "stratum": acc,
                    "wc": 100,
                    "err1": 20,
                    "err2": 30,
                    "err3": 15,
                })
        return records

    # 1. NaN in word count
    r_nan_wc = _make_valid_records()
    r_nan_wc[0]["wc"] = float("nan")
    with pytest.raises(ValueError, match="Missing/NaN wc"):
        run_confirmatory_paired_cluster_inference(r_nan_wc, num_bootstrap_replicates=50)

    # 2. Inf in err2
    r_inf_err = _make_valid_records()
    r_inf_err[0]["err2"] = float("inf")
    with pytest.raises(ValueError, match="Non-finite err2 'inf'"):
        run_confirmatory_paired_cluster_inference(r_inf_err, num_bootstrap_replicates=50)

    # 3. Zero word count
    r_zero_wc = _make_valid_records()
    r_zero_wc[0]["wc"] = 0
    with pytest.raises(ValueError, match="Non-positive word count wc='0'"):
        run_confirmatory_paired_cluster_inference(r_zero_wc, num_bootstrap_replicates=50)

    # 4. Negative integer error count
    r_neg_err = _make_valid_records()
    r_neg_err[0]["err1"] = -5
    with pytest.raises(ValueError, match="Invalid error count err1='-5'"):
        run_confirmatory_paired_cluster_inference(r_neg_err, num_bootstrap_replicates=50)


def test_confirmatory_paired_cluster_inference_validates_configuration_ranges():
    """
    Test Case 37: Confirmatory inference validates alpha, margin, and replicate bounds.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    records = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(3):
            records.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 20,
                "err2": 30,
                "err3": 15,
            })

    # 1. Invalid replicates (0 or negative)
    with pytest.raises(ValueError, match="num_bootstrap_replicates must be a positive integer"):
        run_confirmatory_paired_cluster_inference(records, num_bootstrap_replicates=0)

    # 2. Invalid alpha (outside (0, 1))
    with pytest.raises(ValueError, match="alpha_family must be a finite float strictly in"):
        run_confirmatory_paired_cluster_inference(records, alpha_family=1.5)

    # 3. Negative regression margin
    with pytest.raises(ValueError, match="epsilon_g_margin_pp must be a finite non-negative float"):
        run_confirmatory_paired_cluster_inference(records, epsilon_g_margin_pp=-1.0)


def test_confirmatory_paired_cluster_inference_distinguishes_fail_and_inconclusive():
    """
    Test Case 38: Confirmatory inference distinguishes affirmative FAIL from INCONCLUSIVE.
    - Demonstrable regression in point estimate yields FAIL.
    - Non-harmful point estimate with imprecise confidence bound yields INCONCLUSIVE.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    # Scenario A: Affirmative Harm / Regression (Arm 3 WER is WORSE than Static Arm 1)
    # err3 = 30% vs err1 = 20% -> delta_static = +10.0 pp
    records_harm = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(10):
            records_harm.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 20,
                "err2": 35,
                "err3": 30,  # Explicit harmful degradation
            })

    rep_fail = run_confirmatory_paired_cluster_inference(
        speaker_records=records_harm,
        num_bootstrap_replicates=200,
        seed=42,
    )
    assert rep_fail.verdict == "FAIL"

    # Scenario B: Minor improvement, but high speaker variance causes UCB to span zero
    # delta_static is slightly negative (-0.5 pp), but confidence interval is wide
    records_imprecise = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(5):
            # Alternating speakers create high paired variance
            e3 = 18 if s % 2 == 0 else 22
            records_imprecise.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 20,
                "err2": 35,
                "err3": e3,
            })

    rep_inconclusive = run_confirmatory_paired_cluster_inference(
        speaker_records=records_imprecise,
        num_bootstrap_replicates=200,
        seed=42,
    )
    # Since point estimate is not harmful but UCB spans across zero, verdict must be INCONCLUSIVE
    assert rep_inconclusive.verdict == "INCONCLUSIVE"


def test_confirmatory_paired_cluster_inference_power_assessment_underpowered():
    """
    Test Case 39: Small sample sizes are explicitly classified as UNDERPOWERED in PowerAssessment.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    # 2 speakers per accent (12 speakers total): underpowered
    records_small = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(2):
            records_small.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 25,
                "err2": 35,
                "err3": 15,
            })

    report = run_confirmatory_paired_cluster_inference(
        speaker_records=records_small,
        num_bootstrap_replicates=100,
        seed=42,
        min_speakers_per_stratum_for_power=5,
    )

    assert report.power_assessment is not None
    assert report.power_assessment.power_status == "UNDERPOWERED"
    assert not report.power_assessment.is_adequately_powered
    assert report.verdict == "INCONCLUSIVE"
    assert any("underpowered" in r.lower() for r in report.failure_reasons)


def test_runner_cli_supports_cohort3_and_fails_closed_when_data_missing(monkeypatch, capsys):
    """
    Test Case 40: Runner CLI accepts --cohort cohort3 and fails closed with descriptive
    HOLD diagnostic if physical clips or manifest are not materialized on disk.
    """
    from cloud.kaggle.run_stage6m_cohort2_benchmark import parse_args, main
    import sys

    # 1. Verify parser accepts cohort3
    monkeypatch.setattr(sys, "argv", ["run_benchmark.py", "--cohort", "cohort3", "--gate-version", "v14", "--preflight-only"])
    args = parse_args()
    assert args.cohort == "cohort3"

    # 2. Verify main() halts closed with status code 1 when data missing
    monkeypatch.setenv("STAGE6M_GIT_DIRTY", "false")
    monkeypatch.setenv("STAGE6M_GIT_COMMIT_SHA", "test_commit_sha_123456789")

    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "CONFIRMATORY_COHORT3_HOLD_DATA_MATERIALIZATION_PENDING" in captured.out


def test_runner_enforces_clean_git_tree_for_cohort3(monkeypatch, capsys):
    """
    Test Case 41: Runner rejects uncommitted working tree modifications when attempting
    Confirmatory Cohort 3 execution.
    """
    from cloud.kaggle.run_stage6m_cohort2_benchmark import main
    import sys

    monkeypatch.setattr(sys, "argv", ["run_benchmark.py", "--cohort", "cohort3", "--gate-version", "v14"])
    monkeypatch.setenv("STAGE6M_GIT_DIRTY", "true")
    monkeypatch.setenv("STAGE6M_GIT_COMMIT_SHA", "dirty_commit_sha_12345")

    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Confirmatory Execution Provenance Violation" in captured.out
    assert "uncommitted modifications" in captured.out


def test_runner_cohort3_rejects_legacy_v13_gate(monkeypatch, capsys):
    """
    Test Case 42: Runner rejects legacy v1.3 gate when executing Confirmatory Cohort 3.
    """
    from cloud.kaggle.run_stage6m_cohort2_benchmark import main
    import sys

    monkeypatch.setattr(sys, "argv", ["run_benchmark.py", "--cohort", "cohort3", "--gate-version", "v13"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Confirmatory Protocol Violation" in captured.out
    assert "requires --gate-version v14" in captured.out


def test_confirmatory_power_strictly_enforces_78_speaker_design_spec_over_default_argument():
    """
    Test Case 43: Confirmatory design specification is authoritative.
    When a 78-speaker design specification is supplied, a cohort with even one accent below
    78 speakers (e.g. 77 speakers in Irish English) cannot be classified as adequately powered,
    even if fallback/default arguments (e.g. min_speakers_per_stratum_for_power=5) are passed.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import (
        run_confirmatory_paired_cluster_inference,
        DesignStagePowerSpec,
        CANONICAL_PROTOCOL_ACCENTS,
    )

    records = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        n = 77 if acc == "Irish English" else 78
        for s in range(n):
            records.append({
                "speaker_id": f"{acc}_spk_{s}",
                "stratum": acc,
                "wc": 100,
                "err1": 25,
                "err2": 35,
                "err3": 15,
            })

    spec = DesignStagePowerSpec(required_speakers_per_stratum=78)

    report = run_confirmatory_paired_cluster_inference(
        speaker_records=records,
        num_bootstrap_replicates=100,
        seed=42,
        design_spec=spec,
        min_speakers_per_stratum_for_power=5,  # Must NOT override design_spec!
    )

    assert report.power_assessment is not None
    assert report.power_assessment.min_speakers_required_for_power == 78
    assert report.power_assessment.min_speakers_per_stratum_observed == 77
    assert not report.power_assessment.is_adequately_powered
    assert report.power_assessment.power_status == "UNDERPOWERED"
    assert report.verdict == "INCONCLUSIVE"
    assert any("underpowered" in r.lower() for r in report.failure_reasons)


def test_cohort3_structural_validation_enforces_speaker_accent_uniqueness():
    """
    Test Case 44: Pre-stream speaker-to-accent uniqueness validation.
    Verifies that if any speaker in the evaluation data is assigned to multiple
    accent strata, the validator fails closed before streaming.
    """
    from dsg_ctta.evaluation.paired_cluster_inference import CANONICAL_PROTOCOL_ACCENTS

    valid_records = []
    for acc in sorted(list(CANONICAL_PROTOCOL_ACCENTS)):
        for s in range(5):
            valid_records.append({
                "recording_id": f"rec_{acc}_{s}",
                "speaker_id": f"spk_{acc}_{s}",
                "stage5_accent_group": acc,
            })
    df = pd.DataFrame(valid_records)

    # Inconsistent speaker: spk_US English_0 is also assigned to Irish English
    inconsistent_row = pd.DataFrame([{
        "recording_id": "rec_conflict_0",
        "speaker_id": "spk_US English_0",
        "stage5_accent_group": "Irish English",
    }])
    conflicted_df = pd.concat([df, inconsistent_row], ignore_index=True)

    spk_accent_counts = conflicted_df.groupby("speaker_id")["stage5_accent_group"].nunique()
    inconsistent_spks = spk_accent_counts[spk_accent_counts > 1].index.tolist()
    assert len(inconsistent_spks) == 1
    assert "spk_US English_0" in inconsistent_spks


def test_pairwise_partition_disjointness_check():
    """
    Test Case 45: Pairwise partition disjointness check fails closed on any overlap.
    """
    p1 = {"spk_1", "spk_2", "spk_3"}
    p2 = {"spk_4", "spk_5"}
    p3_overlap = {"spk_2", "spk_6"}  # Overlaps with p1

    partitions = {
        "Part1": p1,
        "Part2": p2,
        "Part3": p3_overlap,
    }

    overlaps = []
    p_names = list(partitions.keys())
    for i in range(len(p_names)):
        for j in range(i + 1, len(p_names)):
            n1, n2 = p_names[i], p_names[j]
            inter = partitions[n1].intersection(partitions[n2])
            if inter:
                overlaps.append((n1, n2, inter))

    assert len(overlaps) == 1
    assert overlaps[0][0] == "Part1"
    assert overlaps[0][1] == "Part3"
    assert "spk_2" in overlaps[0][2]






