"""
Blocking Research Validity Test: Sentinel Panel Contamination.
Verifies that sentinel panel speakers NEVER appear in online adaptation/test streams.
"""

import pytest
from dsg_ctta.online.sentinel import FrozenSentinelPanel
from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.data.splits import create_speaker_disjoint_splits


def test_sentinel_panel_clean(tmp_path):
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=str(tmp_path),
        utterances_per_speaker=2
    )

    manifest = create_speaker_disjoint_splits(
        utterances=primary_utts,
        seed=42,
        external_utterances=ext_utts
    )

    sentinel_utts = manifest.partitions["sentinel_candidates"].utterances
    test_utts = manifest.partitions["final_test"].utterances

    panel = FrozenSentinelPanel(panel_id="sentinel_v1", sentinel_utterances=sentinel_utts)
    test_speaker_ids = [u.speaker_id for u in test_utts]

    # Should pass without error
    panel.assert_no_speaker_contamination(test_speaker_ids)


def test_contaminated_sentinel_raises_assertion(tmp_path):
    primary_utts, _ = generate_research_fixture_dataset(
        output_dir=str(tmp_path),
        utterances_per_speaker=2
    )
    panel = FrozenSentinelPanel(panel_id="sentinel_v1", sentinel_utterances=primary_utts[:2])
    
    # Contaminate stream with sentinel speaker
    contaminated_stream_speakers = [primary_utts[0].speaker_id, "other_spk"]

    with pytest.raises(AssertionError, match="CRITICAL RESEARCH INVALIDITY"):
        panel.assert_no_speaker_contamination(contaminated_stream_speakers)
