"""
Blocking Research Validity Test: Online Label Isolation.
Verifies that UnlabeledAudioBatch objects contain zero reference text or ground truth attributes.
"""

from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer


def test_label_isolation_strips_all_ground_truth(tmp_path):
    primary_utts, _ = generate_research_fixture_dataset(
        output_dir=str(tmp_path),
        utterances_per_speaker=2
    )

    batch = LabelIsolationSanitizer.sanitize_batch(primary_utts, batch_idx=0)

    for item in batch.items:
        # Assert item does NOT possess ground-truth transcript or group fields
        assert not hasattr(item, "reference_raw")
        assert not hasattr(item, "reference_normalized")
        assert not hasattr(item, "group_id")
        assert not hasattr(item, "speaker_id")
        assert not hasattr(item, "substitutions")
        assert not hasattr(item, "wer")
