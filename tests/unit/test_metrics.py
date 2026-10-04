"""
Unit tests for exact Levenshtein alignment, WER, and CER calculations.
Verifies hand-calculated edge cases and mathematical correctness.
"""

import pytest
from dsg_ctta.offline.metrics import compute_utterance_metrics


def test_exact_match():
    ref = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
    hyp = "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
    m = compute_utterance_metrics(ref, hyp)

    assert m.substitutions == 0
    assert m.deletions == 0
    assert m.insertions == 0
    assert m.hits == 9
    assert m.reference_length == 9
    assert m.wer == 0.0
    assert m.cer == 0.0


def test_single_substitution():
    ref = "THE DOG BARKED LOUDLY"
    hyp = "THE CAT BARKED LOUDLY"
    m = compute_utterance_metrics(ref, hyp)

    assert m.substitutions == 1
    assert m.deletions == 0
    assert m.insertions == 0
    assert m.hits == 3
    assert m.reference_length == 4
    assert pytest.approx(m.wer, 1e-5) == 1.0 / 4.0


def test_pure_deletions():
    ref = "ONE TWO THREE FOUR FIVE"
    hyp = "ONE THREE FIVE"
    m = compute_utterance_metrics(ref, hyp)

    assert m.substitutions == 0
    assert m.deletions == 2  # 'TWO' and 'FOUR' deleted
    assert m.insertions == 0
    assert m.hits == 3
    assert m.reference_length == 5
    assert pytest.approx(m.wer, 1e-5) == 2.0 / 5.0


def test_pure_insertions():
    ref = "A B C"
    hyp = "A X B Y C Z"
    m = compute_utterance_metrics(ref, hyp)

    assert m.substitutions == 0
    assert m.deletions == 0
    assert m.insertions == 3
    assert m.hits == 3
    assert m.reference_length == 3
    assert pytest.approx(m.wer, 1e-5) == 3.0 / 3.0  # 100% WER due to 3 insertions


def test_mixed_errors():
    # Ref: A B C D (4 words)
    # Hyp: A X D   (3 words: A=hit, B->X sub, C=del, D=hit)
    ref = "A B C D"
    hyp = "A X D"
    m = compute_utterance_metrics(ref, hyp)

    assert m.hits == 2
    assert m.substitutions == 1
    assert m.deletions == 1
    assert m.insertions == 0
    assert m.reference_length == 4
    assert pytest.approx(m.wer, 1e-5) == 2.0 / 4.0


def test_empty_hypothesis():
    ref = "HELLO WORLD"
    hyp = ""
    m = compute_utterance_metrics(ref, hyp)

    assert m.substitutions == 0
    assert m.deletions == 2
    assert m.insertions == 0
    assert m.reference_length == 2
    assert m.wer == 1.0


def test_empty_reference():
    ref = ""
    hyp = "HELLO WORLD"
    m = compute_utterance_metrics(ref, hyp)

    assert m.insertions == 2
    assert m.reference_length == 0
    assert m.wer == 1.0


def test_both_empty():
    ref = ""
    hyp = ""
    m = compute_utterance_metrics(ref, hyp)

    assert m.total_errors == 0
    assert m.wer == 0.0
    assert m.cer == 0.0
