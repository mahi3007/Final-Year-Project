"""
Unit Tests for Fail-Closed Safety Semantics of DSG.
===================================================
Verifies that any invalid state, corrupt input, missing metadata,
NaN, Inf, or exception results in an automatic, uncompromising REJECT.
"""

import pytest
import math
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.bootstrap import run_paired_speaker_bootstrap
from dsg_ctta.controller.exceptions import (
    InvalidMetricsError,
    DegenerateBootstrapError,
    EmptySentinelError,
)


def make_clean_records():
    records_base = []
    records_cand = []
    for g in ["grp1", "grp2", "grp3"]:
        for s in [f"spk_{g}_{i}" for i in range(4)]:
            for u in range(3):
                records_base.append({
                    "utterance_id": f"utt_{s}_{u}",
                    "speaker_id": s,
                    "group_id": g,
                    "substitutions": 1,
                    "deletions": 0,
                    "insertions": 0,
                    "reference_length": 10,
                })
                records_cand.append({
                    "utterance_id": f"utt_{s}_{u}",
                    "speaker_id": s,
                    "group_id": g,
                    "substitutions": 1,
                    "deletions": 0,
                    "insertions": 0,
                    "reference_length": 10,
                })
    return records_base, records_cand


def test_nan_substitutions_causes_fail_closed_reject():
    """NaN in error counts must be caught and lead to REJECT."""
    base, cand = make_clean_records()
    cand[5]["substitutions"] = float("nan")

    gate = DisparitySafetyGate()
    evaluator = SentinelSafetyEvaluator(gate)

    decision = evaluator.evaluate_records(base, cand)
    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("FAIL-CLOSED" in r for r in decision.rejection_reasons)


def test_inf_reference_length_causes_fail_closed_reject():
    """Inf in reference length must be caught and lead to REJECT."""
    base, cand = make_clean_records()
    cand[2]["reference_length"] = float("inf")

    gate = DisparitySafetyGate()
    evaluator = SentinelSafetyEvaluator(gate)

    decision = evaluator.evaluate_records(base, cand)
    assert decision.decision == "REJECT"
    assert decision.accept is False


def test_missing_field_causes_fail_closed_reject():
    """Missing key in record must cause REJECT."""
    base, cand = make_clean_records()
    del cand[0]["group_id"]

    gate = DisparitySafetyGate()
    evaluator = SentinelSafetyEvaluator(gate)

    decision = evaluator.evaluate_records(base, cand)
    assert decision.decision == "REJECT"
    assert decision.accept is False


def test_insufficient_clusters_causes_fail_closed_reject():
    """If a stratum has fewer clusters than min_speakers_per_group, fail closed."""
    base, cand = make_clean_records()
    # Filter out speakers so grp1 has only 1 speaker
    base_filtered = [r for r in base if not (r["group_id"] == "grp1" and r["speaker_id"] != "spk_grp1_0")]
    cand_filtered = [r for r in cand if not (r["group_id"] == "grp1" and r["speaker_id"] != "spk_grp1_0")]

    gate = DisparitySafetyGate()
    evaluator = SentinelSafetyEvaluator(gate, min_speakers_per_group=3)

    decision = evaluator.evaluate_records(base_filtered, cand_filtered)
    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("speaker clusters" in r for r in decision.rejection_reasons)


def test_empty_sentinel_records_causes_fail_closed_reject():
    """Empty sentinel lists must result in REJECT."""
    gate = DisparitySafetyGate()
    evaluator = SentinelSafetyEvaluator(gate)

    decision = evaluator.evaluate_records([], [])
    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("empty" in r.lower() for r in decision.rejection_reasons)


def test_exception_in_inference_forces_reject():
    """Simulated inference failure must result in safe REJECT with live model untouched."""
    gate = DisparitySafetyGate()
    evaluator = SentinelSafetyEvaluator(gate)

    class BrokenModel:
        def transcribe(self, path):
            raise RuntimeError("GPU Out of Memory / CUDA Fault!")

    live = BrokenModel()
    cand = BrokenModel()

    decision = evaluator.evaluate_candidate(live, cand, sentinel_utterances=["dummy_utt"])
    assert decision.decision == "REJECT"
    assert decision.accept is False
    assert any("CUDA Fault" in r or "FAIL-CLOSED" in r for r in decision.rejection_reasons)
