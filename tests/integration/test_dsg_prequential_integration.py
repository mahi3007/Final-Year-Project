"""
Stage 5A Integration Test: DSG Controller Integration with Prequential Stream.
==============================================================================
Validates the full prequential loop with Disparity Safety Gate:
For every window B_t:
  1. theta_t predicts B_t
  2. Predictions are frozen and recorded
  3. Unlabeled B_t produces candidate theta' in shadow clone
  4. DSG evaluates candidate against the frozen sentinel reference
  5. ACCEPT -> theta_(t+1) = theta'
  6. REJECT -> theta_(t+1) = theta_t
"""

import pytest
import numpy as np
import pandas as pd
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.shadow import ShadowCandidateManager, compute_model_parameter_hash
from dsg_ctta.models.mock_model import MockASRModel
from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.data.splits import create_speaker_disjoint_splits
from dsg_ctta.online.stream import PrequentialStream


def test_dsg_prequential_loop_integration(tmp_path):
    # 1. Generate test fixture data
    fixture_dir = str(tmp_path / "fixture")
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=fixture_dir,
        utterances_per_speaker=4
    )

    manifest = create_speaker_disjoint_splits(
        utterances=primary_utts,
        seed=42,
        external_utterances=ext_utts
    )

    adapt_utts = manifest.partitions["final_test"].utterances
    stream = PrequentialStream(utterances=adapt_utts, window_size_k=2)

    # 2. Instantiate Mock Live Model and DSG Controller
    live_model = MockASRModel(seed=42)
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    evaluator = SentinelSafetyEvaluator(gate, num_bootstrap=100, min_speakers_per_group=1)

    # Synthetic sentinel records (representing sentinel panel)
    def make_sentinel_records(err_level=1):
        records = []
        for g in ["native_region", "non_native"]:
            for s in [f"spk_{g}_{i}" for i in range(2)]:
                for u in range(3):
                    records.append({
                        "utterance_id": f"utt_{s}_{u}",
                        "speaker_id": s,
                        "group_id": g,
                        "substitutions": err_level,
                        "deletions": 0,
                        "insertions": 0,
                        "reference_length": 10,
                    })
        return records

    decisions = []
    window_count = 0

    # 3. Prequential Adaptation Loop with DSG
    for win_idx, batch_utts, unlabeled_batch in stream.generate_windows():
        window_count += 1
        live_hash_before = compute_model_parameter_hash(live_model)

        # Step 1: Live inference on B_t using theta_t
        for u in batch_utts:
            hyp = live_model.transcribe(u.audio_filepath)
            assert isinstance(hyp, str)

        # Step 2: Create shadow candidate and adapt
        candidate = ShadowCandidateManager.create_candidate_clone(live_model)
        # Simulate adaptation by altering seed
        candidate.seed += 1

        # Step 3: Evaluate on sentinel
        # Toggle sentinel records to test both accept and reject
        cand_err = 1 if win_idx % 2 == 0 else 3  # window 0: accept, window 1: reject
        base_records = make_sentinel_records(err_level=1)
        cand_records = make_sentinel_records(err_level=cand_err)

        decision = evaluator.evaluate_records(
            records_live=base_records,
            records_candidate=cand_records,
            candidate_identifier=f"cand_w{win_idx}",
            live_identifier=f"live_w{win_idx}",
        )
        decisions.append(decision)

        # Step 4: Apply state transition
        live_model = ShadowCandidateManager.apply_transition(
            live_model=live_model,
            candidate_model=candidate,
            decision=decision,
            pre_adaptation_hash=live_hash_before,
        )

        live_hash_after = compute_model_parameter_hash(live_model)
        if not decision.accept:
            assert live_hash_after == live_hash_before, "Rejection must preserve live model bit-for-bit"

    assert window_count > 0
    assert any(d.accept for d in decisions)
    assert any(not d.accept for d in decisions)
