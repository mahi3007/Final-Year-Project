"""
Blocking Research Validity Test: Seed Reproducibility.
Verifies that random seeds produce deterministic and identical split partitions and manifests.
"""

from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.data.splits import create_speaker_disjoint_splits


def test_seed_determinism(tmp_path):
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=str(tmp_path),
        utterances_per_speaker=2
    )

    m1 = create_speaker_disjoint_splits(utterances=primary_utts, seed=12345, external_utterances=ext_utts)
    m2 = create_speaker_disjoint_splits(utterances=primary_utts, seed=12345, external_utterances=ext_utts)

    assert m1.manifest_hash == m2.manifest_hash
    for p_name in m1.partitions:
        assert m1.partitions[p_name].speaker_ids == m2.partitions[p_name].speaker_ids
