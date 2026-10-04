"""
Unit Tests for Bootstrap Determinism, Stratification, and Pairing Integrity.
============================================================================
Validates:
1. Bit-for-bit reproducible results across repeated runs with identical seed.
2. Different seeds produce distinct bootstrap distributions.
3. Candidate/base pairing order is strictly preserved.
4. Stratified sampling guarantees zero omitted groups across all replicates.
5. Deterministic group ordering.
"""

import pytest
import numpy as np
from dsg_ctta.controller.bootstrap import run_paired_speaker_bootstrap
from dsg_ctta.controller.exceptions import InconsistentPairingError


def make_synthetic_sentinel_records(num_groups=6, spks_per_group=5, utts_per_spk=5):
    records_base = []
    records_cand = []
    rng = np.random.RandomState(42)

    for g_idx in range(num_groups):
        grp_name = f"group_{chr(65 + g_idx)}"
        for s_idx in range(spks_per_group):
            spk_id = f"spk_{grp_name}_{s_idx:02d}"
            for u_idx in range(utts_per_spk):
                utt_id = f"utt_{spk_id}_{u_idx:02d}"
                ref_len = 10
                be = rng.randint(0, 3)
                ce = rng.randint(0, 3)
                records_base.append({
                    "utterance_id": utt_id,
                    "speaker_id": spk_id,
                    "group_id": grp_name,
                    "substitutions": be,
                    "deletions": 0,
                    "insertions": 0,
                    "reference_length": ref_len,
                })
                records_cand.append({
                    "utterance_id": utt_id,
                    "speaker_id": spk_id,
                    "group_id": grp_name,
                    "substitutions": ce,
                    "deletions": 0,
                    "insertions": 0,
                    "reference_length": ref_len,
                })
    return records_base, records_cand


def test_bootstrap_exact_reproducibility():
    """Identical seed must yield bitwise identical UCBs and statistics."""
    base, cand = make_synthetic_sentinel_records()
    res1 = run_paired_speaker_bootstrap(base, cand, num_replicates=500, seed=20261002)
    res2 = run_paired_speaker_bootstrap(base, cand, num_replicates=500, seed=20261002)

    assert res1.ucb_r == res2.ucb_r
    assert res1.ucb_max_group == res2.ucb_max_group
    assert res1.ucb_d == res2.ucb_d
    assert res1.delta_r == res2.delta_r
    assert res1.max_delta_g == res2.max_delta_g
    assert res1.group_ucbs == res2.group_ucbs


def test_different_seeds_produce_distinct_draws():
    """Different seeds must yield distinct bootstrap estimates."""
    base, cand = make_synthetic_sentinel_records()
    res1 = run_paired_speaker_bootstrap(base, cand, num_replicates=500, seed=111)
    res2 = run_paired_speaker_bootstrap(base, cand, num_replicates=500, seed=999)

    # Point estimates must match (same data)
    assert res1.delta_r == res2.delta_r
    # But bootstrap UCBs differ due to sampling
    assert res1.ucb_r != res2.ucb_r or res1.ucb_max_group != res2.ucb_max_group


def test_zero_omitted_groups_across_all_replicates():
    """Stratified sampling must guarantee exactly zero omitted groups in 1000 replicates."""
    base, cand = make_synthetic_sentinel_records(num_groups=6, spks_per_group=5)
    res = run_paired_speaker_bootstrap(base, cand, num_replicates=1000, seed=20261002)

    assert res.omitted_groups_count == 0
    assert len(res.group_ucbs) == 6
    assert len(res.group_deltas) == 6


def test_pairing_inconsistency_raises_error():
    """Reordering or mismatching records must immediately fail closed."""
    base, cand = make_synthetic_sentinel_records()

    # Tamper with utterance_id order in candidate
    cand_tampered = list(reversed(cand))

    with pytest.raises(InconsistentPairingError, match="Utterance ID mismatch"):
        run_paired_speaker_bootstrap(base, cand_tampered, num_replicates=100)


def test_speaker_mismatch_raises_error():
    """Speaker ID mismatch must fail closed."""
    base, cand = make_synthetic_sentinel_records()
    cand[0] = dict(cand[0], speaker_id="rogue_speaker")

    with pytest.raises(InconsistentPairingError, match="Speaker ID mismatch"):
        run_paired_speaker_bootstrap(base, cand, num_replicates=100)
