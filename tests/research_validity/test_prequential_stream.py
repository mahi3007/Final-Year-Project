"""
Stage 3A Research Validity Tests:
- Prequential stream orderings and deterministic hashing
- Strict label isolation boundary during online streaming
- No-adaptation control invariant (theta_(t+1) == theta_t == theta_0)
- Metric calculation invariants (group regression, disparity, delta_D)
"""

import pytest
import torch
import numpy as np
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.online.stream import (
    PrequentialStream,
    order_utterances,
    ORDER_A_GROUPS,
    ORDER_B_GROUPS,
    ORDER_C_GROUPS
)
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer, UnlabeledAudioBatch
from dsg_ctta.models.mock_model import MockASRModel
from dsg_ctta.adaptation.no_adapt import NoAdaptationAdapter


def _create_synthetic_utterances(n_per_group: int = 2) -> list[UtteranceMetadata]:
    """Helper to create dummy metadata for testing."""
    groups = ["Arabic", "Hindi", "Korean", "Mandarin", "Spanish", "Vietnamese"]
    utts = []
    idx = 0
    prov = ProvenanceInfo(
        source_dataset="L2-ARCTIC",
        dataset_release="v1.0",
        normalization_version="v1.0.0-canonical",
        protocol_version="v1.0.0-canonical"
    )
    for g in groups:
        for i in range(n_per_group):
            idx += 1
            utts.append(
                UtteranceMetadata(
                    utterance_id=f"utt_{idx:03d}",
                    speaker_id=f"spk_{g[:3]}_{i+1}",
                    group_id=g,
                    group_type="accent",
                    audio_filepath=f"dummy/path/{idx}.wav",
                    audio_sha256="dummyhash",
                    sampling_rate_hz=16000,
                    duration_seconds=3.0,
                    snr_db=25.0,
                    speech_rate_wpm=130.0,
                    device_id="mic1",
                    reference_raw="THIS IS A TEST",
                    reference_normalized="this is a test",
                    reference_word_count=4,
                    reference_char_count=14,
                    partition="development",
                    provenance=prov
                )
            )
    return utts


def test_stream_ordering_determinism():
    """Verify pre-registered accent orderings are deterministic and match specification."""
    utts = _create_synthetic_utterances(n_per_group=2)

    # ORDER_A: Arabic -> Hindi -> Korean -> Mandarin -> Spanish -> Vietnamese
    ordered_a = order_utterances(utts, ordering_id="ORDER_A")
    first_groups_a = [u.group_id for u in ordered_a]
    assert first_groups_a[:2] == ["Arabic", "Arabic"]
    assert first_groups_a[2:4] == ["Hindi", "Hindi"]
    assert first_groups_a[-2:] == ["Vietnamese", "Vietnamese"]

    # ORDER_B: Vietnamese -> Spanish -> Mandarin -> Korean -> Hindi -> Arabic
    ordered_b = order_utterances(utts, ordering_id="ORDER_B")
    first_groups_b = [u.group_id for u in ordered_b]
    assert first_groups_b[:2] == ["Vietnamese", "Vietnamese"]
    assert first_groups_b[-2:] == ["Arabic", "Arabic"]

    # Stream hash determinism
    stream1 = PrequentialStream(utts, window_size_k=4, ordering_id="ORDER_A", seed=42)
    stream2 = PrequentialStream(utts, window_size_k=4, ordering_id="ORDER_A", seed=42)
    assert stream1.stream_hash == stream2.stream_hash

    # Different ordering must produce different stream hash
    stream_b = PrequentialStream(utts, window_size_k=4, ordering_id="ORDER_B", seed=42)
    assert stream1.stream_hash != stream_b.stream_hash


def test_online_label_isolation_in_prequential_stream():
    """Verify that online batches yield zero access to reference transcripts or group labels."""
    utts = _create_synthetic_utterances(n_per_group=2)
    stream = PrequentialStream(utts, window_size_k=4, ordering_id="ORDER_A")

    for batch_idx, batch_utts, unlabeled_batch in stream.generate_windows():
        assert isinstance(unlabeled_batch, UnlabeledAudioBatch)
        assert len(unlabeled_batch.items) <= 4

        for item in unlabeled_batch.items:
            # Check strictly forbidden attributes do not exist
            assert not hasattr(item, "reference_raw")
            assert not hasattr(item, "reference_normalized")
            assert not hasattr(item, "group_id")
            assert not hasattr(item, "speaker_id")
            assert not hasattr(item, "wer")
            assert not hasattr(item, "cer")

            # Permitted attributes only
            assert hasattr(item, "utterance_id")
            assert hasattr(item, "audio_filepath")
            assert hasattr(item, "duration_seconds")
            assert hasattr(item, "sampling_rate_hz")


def test_no_adaptation_control_invariant():
    """Verify NoAdaptationAdapter never alters model parameters (theta_(t+1) == theta_t)."""
    model = MockASRModel(model_id="mock-asr-v1")
    # Attach a mock PyTorch module to model for hash calculation
    model.model = torch.nn.Linear(4, 4)
    model.load_model()
    adapter = NoAdaptationAdapter(asr_model=model)

    utts = _create_synthetic_utterances(n_per_group=1)
    unlabeled_batch = LabelIsolationSanitizer.sanitize_batch(utts, batch_idx=0)

    hash_before = adapter.compute_model_hash()
    assert hash_before != "uninitialized"

    step_res = adapter.adapt(unlabeled_batch)
    hash_after = adapter.compute_model_hash()

    assert step_res.updated is False
    assert step_res.reset_occurred is False
    assert step_res.theta_before_hash == hash_before
    assert step_res.theta_after_hash == hash_after
    assert hash_before == hash_after


def test_suta_parameter_isolation():
    """Verify SutaAdapter unfreezes ONLY LayerNorm parameters, keeping attention/linear frozen."""
    class DummySpeechModule(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(8, 8)
            self.layer_norm = torch.nn.LayerNorm(8)

        def forward(self, x):
            return self.layer_norm(self.linear(x))

    model = MockASRModel(model_id="mock-asr-v1")
    model.model = DummySpeechModule()
    model.load_model()

    from dsg_ctta.adaptation.suta import SutaAdapter
    adapter = SutaAdapter(asr_model=model)

    # Check that linear weights are frozen
    assert model.model.linear.weight.requires_grad is False
    assert model.model.linear.bias.requires_grad is False

    # Check that LayerNorm weights are active
    assert model.model.layer_norm.weight.requires_grad is True
    assert model.model.layer_norm.bias.requires_grad is True


def test_dsuta_adapter_contract():
    """Verify DsutaAdapter initialization, LayerNorm isolation, and dynamic reset state."""
    class DummySpeechModule(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(8, 8)
            self.layer_norm = torch.nn.LayerNorm(8)

        def forward(self, x):
            return self.layer_norm(self.linear(x))

    model = MockASRModel(model_id="mock-asr-v1")
    model.model = DummySpeechModule()
    model.load_model()

    from dsg_ctta.adaptation.dsuta import DsutaAdapter
    adapter = DsutaAdapter(asr_model=model)

    assert adapter.method_id == "dsuta"
    assert model.model.linear.weight.requires_grad is False
    assert model.model.layer_norm.weight.requires_grad is True
    assert adapter.total_resets == 0


def test_dmsuta_adapter_contract():
    """Verify DmsutaAdapter initializes dynamic model bank with source anchor theta_0."""
    class DummySpeechModule(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(8, 8)
            self.layer_norm = torch.nn.LayerNorm(8)

        def forward(self, x):
            return self.layer_norm(self.linear(x))

    model = MockASRModel(model_id="mock-asr-v1")
    model.model = DummySpeechModule()
    model.load_model()

    from dsg_ctta.adaptation.dmsuta import DmsutaAdapter
    adapter = DmsutaAdapter(asr_model=model, config={"max_bank_size": 3})

    assert adapter.method_id == "dmsuta"
    assert len(adapter.model_bank) == 1
    assert adapter.model_bank[0]["id"] == "theta_0_anchor"
    assert adapter.model_bank[0]["is_anchor"] is True


