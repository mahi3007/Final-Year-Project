"""
Blocking Research Validity Test: Zero Speaker Leakage.
Verifies that no speaker ID ever appears in more than one partition.
"""

import pytest
from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.data.splits import create_speaker_disjoint_splits


def test_zero_speaker_leakage_on_splits(tmp_path):
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=str(tmp_path),
        utterances_per_speaker=2
    )

    manifest = create_speaker_disjoint_splits(
        utterances=primary_utts,
        seed=42,
        external_utterances=ext_utts
    )

    all_partitions = list(manifest.partitions.keys())
    assert len(all_partitions) >= 4, "Must have at least 4 partitions"

    # Pairwise check for zero speaker intersection
    for i in range(len(all_partitions)):
        for j in range(i + 1, len(all_partitions)):
            p1 = manifest.partitions[all_partitions[i]]
            p2 = manifest.partitions[all_partitions[j]]

            s1 = set(p1.speaker_ids)
            s2 = set(p2.speaker_ids)

            overlap = s1.intersection(s2)
            assert len(overlap) == 0, f"LEAKAGE DETECTED between '{p1.partition_name}' and '{p2.partition_name}': {overlap}"


def test_intentional_leakage_detection_raises_error(tmp_path):
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=str(tmp_path),
        utterances_per_speaker=2
    )

    # Intentionally duplicate a speaker across external and primary
    corrupted_ext = [u.model_copy() for u in ext_utts]
    corrupted_ext[0].speaker_id = primary_utts[0].speaker_id  # Force leak!

    with pytest.raises(AssertionError, match="CRITICAL LEAKAGE"):
        create_speaker_disjoint_splits(
            utterances=primary_utts,
            seed=42,
            external_utterances=corrupted_ext
        )
