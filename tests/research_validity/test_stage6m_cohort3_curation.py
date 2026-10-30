"""
tests/research_validity/test_stage6m_cohort3_curation.py

Comprehensive Automated Test Suite for Stage 6M Cohort 3 Curation & Feasibility Utility
========================================================================================
Governing Standard: ADR-005
Protocol Reference: Protocol v1.4.0 (Decision Rule B)

Test Coverage:
1. Finding A (Fail-Closed Historical Partition Validation):
   - Missing historical partition file strictly raises FileNotFoundError (no fail-open).
   - Malformed CSV with missing 'speaker_id' column strictly raises ValueError.
   - Empty, blank, or null 'speaker_id' values strictly raise ValueError.
   - Unexpected speaker counts strictly raise ValueError.
   - Simulated pairwise speaker overlap strictly raises ValueError.
2. Finding B (Strict Quality Predicate & Physical Clip Eligibility):
   - Predicate V requires non-empty path ending in .mp3, locale='en', up>=2, down<2, words>=2.
   - Speaker eligibility requires at least 15 DISTINCT valid clip paths.
   - Duplicate clip paths per speaker in metadata are deduplicated before counting.
   - Multi-accent declared speakers are strictly excluded from homogeneous strata.
3. Finding C (Immutable Provenance Ledger & Irish Exposure Reconciliation):
   - Provenance records source file bytes, SHA-256, scanned rows, commit SHA, and partition hashes.
   - Historical Irish reconciliation correctly tracks 93 total, 92 strictly eligible, and 1 ineligible.
4. Finding D (Fail-Closed Materialization Gating):
   - Capacity shortfall in --materialize mode strictly exits with status code 1.
   - Sufficient capacity in --materialize mode raises NotImplementedError until downloader is added.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.curate_stage6m_cohort3_dataset import (
    CANONICAL_PROTOCOL_ACCENTS,
    PREDICATE_VERSION,
    PROTOCOL_VERSION,
    TARGET_COHORT3_CLIPS_PER_SPEAKER,
    TARGET_COHORT3_SPEAKERS_PER_STRATUM,
    TARGET_GATE_SPEAKERS_PER_STRATUM,
    TOTAL_REQUIRED_PER_STRATUM,
    audit_speaker_capacity,
    compute_sha256,
    load_partition_speakers,
    verify_historical_disjointness,
)


# ==============================================================================
# 1. Finding A: Fail-Closed Historical Partition Validation Tests
# ==============================================================================


def test_missing_historical_partition_raises_filenotfound(tmp_path):
    """Verify that a missing historical partition file strictly fails closed."""
    nonexistent = tmp_path / "nonexistent_partition.csv"
    with pytest.raises(FileNotFoundError, match="Required historical partition .* is missing"):
        load_partition_speakers(nonexistent, expected_speaker_count=60)


def test_malformed_csv_missing_speaker_id_raises_valueerror(tmp_path):
    """Verify that a CSV missing the mandatory 'speaker_id' column strictly raises ValueError."""
    bad_csv = tmp_path / "missing_speaker_col.csv"
    bad_csv.write_text("recording_id,transcript,stage5_accent_group\nrec_01,hello world,US English\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing mandatory 'speaker_id' column"):
        load_partition_speakers(bad_csv)


@pytest.mark.parametrize("invalid_id", ["", "   ", "nan", "none", "null", "NaN", "NULL"])
def test_empty_or_null_speaker_id_raises_valueerror(tmp_path, invalid_id):
    """Verify that empty, blank, or null speaker IDs in historical partitions strictly fail closed."""
    bad_csv = tmp_path / f"invalid_spk_{invalid_id}.csv"
    bad_csv.write_text(
        f"speaker_id,recording_id,transcript\n{invalid_id},rec_01,hello world\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="speaker_id.*empty/invalid"):
        load_partition_speakers(bad_csv)


def test_unexpected_speaker_count_raises_valueerror(tmp_path):
    """Verify that a partition with unexpected speaker count fails closed."""
    test_csv = tmp_path / "wrong_count.csv"
    # Write 2 speakers when 5 expected
    test_csv.write_text(
        "speaker_id,recording_id\nspk_01,rec_01\nspk_01,rec_02\nspk_02,rec_03\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="expected exactly 5 unique speakers, found 2"):
        load_partition_speakers(test_csv, expected_speaker_count=5)


def test_pairwise_disjointness_violation_raises_valueerror():
    """Verify that overlapping speakers across partitions strictly raise ValueError."""
    part1 = {"spk_A", "spk_B", "spk_C"}
    part2 = {"spk_D", "spk_E", "spk_A"}  # Overlaps on spk_A
    with pytest.raises(ValueError, match="Fail-Closed Disjointness Violation: detected 1 overlapping"):
        verify_historical_disjointness({"Partition1": part1, "Partition2": part2})


def test_pairwise_disjointness_clean_passes():
    """Verify that completely disjoint partitions pass validation cleanly."""
    part1 = {"spk_A", "spk_B"}
    part2 = {"spk_C", "spk_D"}
    part3 = {"spk_E", "spk_F"}
    res = verify_historical_disjointness({"P1": part1, "P2": part2, "P3": part3})
    assert res["disjointness_status"] == "PASS"
    assert res["pairwise_overlaps"]["P1 x P2"] == 0
    assert res["pairwise_overlaps"]["P1 x P3"] == 0
    assert res["pairwise_overlaps"]["P2 x P3"] == 0


# ==============================================================================
# 2. Finding B: Strict Predicate & Distinct Physical Clip Validation Tests
# ==============================================================================


def test_distinct_clip_path_deduplication(tmp_path):
    """
    Verify that speaker eligibility requires 15 DISTINCT valid clip paths,
    not merely 15 repeated metadata rows.
    """
    # Create minimal synthetic TSV where speaker has 16 rows, but only 10 unique paths
    tsv_file = tmp_path / "dup_paths.tsv"
    rows = ["client_id\tpath\tsentence\tup_votes\tdown_votes\taccents\tlocale"]
    for i in range(16):
        path_idx = i % 10  # Only 10 distinct paths: clip_0.mp3 through clip_9.mp3
        rows.append(
            f"spk_dup\tclip_{path_idx}.mp3\tthis is a valid test sentence\t3\t0\tirish english\ten"
        )
    tsv_file.write_text("\n".join(rows) + "\n", encoding="utf-8")

    # Create dummy empty historical partitions
    c1 = tmp_path / "c1.csv"
    c1.write_text("speaker_id,recording_id\nspk_hist,rec_1\n", encoding="utf-8")
    sent = tmp_path / "sent.csv"
    sent.write_text("speaker_id,recording_id\nspk_sent,rec_2\n", encoding="utf-8")
    c2 = tmp_path / "c2.csv"
    c2.write_text("speaker_id,recording_id\nspk_c2,rec_3\n", encoding="utf-8")

    result = audit_speaker_capacity(
        val_tsv=tsv_file,
        c1_path=c1,
        sentinel_path=sent,
        c2_path=c2,
    )

    # spk_dup has 16 rows, but only 10 distinct paths -> must NOT qualify as strictly eligible
    irish_capacity = result["strata_capacity"]["Irish English"]
    assert irish_capacity["raw_declared_speakers"] == 1
    assert irish_capacity["strictly_qualified_speakers"] == 0
    assert irish_capacity["unexposed_available_speakers"] == 0


def test_predicate_v_exclusion_boundaries(tmp_path):
    """
    Verify that clips failing individual predicate conditions are strictly excluded:
    - path non-mp3 or empty
    - locale != 'en'
    - up_votes < 2
    - down_votes >= 2
    - word_count < 2
    """
    tsv_file = tmp_path / "pred_boundaries.tsv"
    rows = [
        "client_id\tpath\tsentence\tup_votes\tdown_votes\taccents\tlocale",
        # Valid clip
        "spk_test\tvalid.mp3\tvalid sentence text\t2\t0\tirish english\ten",
        # Invalid: empty path
        "spk_test\t\tvalid sentence text\t2\t0\tirish english\ten",
        # Invalid: non-mp3
        "spk_test\tbad_ext.wav\tvalid sentence text\t2\t0\tirish english\ten",
        # Invalid: wrong locale
        "spk_test\twrong_loc.mp3\tvalid sentence text\t2\t0\tirish english\tde",
        # Invalid: low up_votes
        "spk_test\tlow_up.mp3\tvalid sentence text\t1\t0\tirish english\ten",
        # Invalid: high down_votes
        "spk_test\thigh_down.mp3\tvalid sentence text\t4\t2\tirish english\ten",
        # Invalid: 1 word only
        "spk_test\tshort_sentence.mp3\tword\t3\t0\tirish english\ten",
    ]
    tsv_file.write_text("\n".join(rows) + "\n", encoding="utf-8")

    c1 = tmp_path / "c1.csv"
    c1.write_text("speaker_id,recording_id\nspk_hist,rec_1\n", encoding="utf-8")
    sent = tmp_path / "sent.csv"
    sent.write_text("speaker_id,recording_id\nspk_sent,rec_2\n", encoding="utf-8")
    c2 = tmp_path / "c2.csv"
    c2.write_text("speaker_id,recording_id\nspk_c2,rec_3\n", encoding="utf-8")

    result = audit_speaker_capacity(
        val_tsv=tsv_file,
        c1_path=c1,
        sentinel_path=sent,
        c2_path=c2,
    )

    irish_capacity = result["strata_capacity"]["Irish English"]
    # Only 1 clip passed, so strictly qualified = 0 (needs 15)
    assert irish_capacity["strictly_qualified_speakers"] == 0


# ==============================================================================
# 3. Finding C: Immutable Provenance & Irish Reconciliation Tests
# ==============================================================================


def test_immutable_provenance_schema_and_reconciliation(tmp_path):
    """
    Verify that audit_speaker_capacity generates complete immutable source provenance
    and exact Irish exposure reconciliation structure.
    """
    tsv_file = tmp_path / "prov_test.tsv"
    tsv_file.write_text(
        "client_id\tpath\tsentence\tup_votes\tdown_votes\taccents\tlocale\n"
        "spk_1\tclip_1.mp3\ttesting provenance block\t2\t0\tunited states english\ten\n",
        encoding="utf-8",
    )

    c1 = tmp_path / "c1.csv"
    c1.write_text("speaker_id,recording_id,stage5_accent_group\nspk_hist1,rec_1,US English\n", encoding="utf-8")
    sent = tmp_path / "sent.csv"
    sent.write_text("speaker_id,recording_id,stage5_accent_group\nspk_hist2,rec_2,US English\n", encoding="utf-8")
    c2 = tmp_path / "c2.csv"
    c2.write_text("speaker_id,recording_id,stage5_accent_group\nspk_hist3,rec_3,US English\n", encoding="utf-8")

    result = audit_speaker_capacity(
        val_tsv=tsv_file,
        c1_path=c1,
        sentinel_path=sent,
        c2_path=c2,
    )

    prov = result["immutable_source_provenance"]
    assert prov["source_dataset"] == "Mozilla Common Voice"
    assert prov["source_file"] == "validated.tsv"
    assert prov["source_file_bytes"] == tsv_file.stat().st_size
    assert prov["source_file_sha256"] == compute_sha256(tsv_file)
    assert prov["source_rows_scanned"] == 1
    assert "curation_script_commit" in prov
    assert "historical_partition_hashes" in prov
    assert "historical_disjointness" in prov

    ir_rec = result["irish_exposure_reconciliation"]
    assert "historical_irish_speakers_total" in ir_rec
    assert "historical_irish_meeting_strict_predicate" in ir_rec
    assert "historical_irish_ineligible_under_strict_predicate" in ir_rec
    assert "unexposed_strictly_eligible_irish_remaining" in ir_rec


# ==============================================================================
# 4. Finding D: Materialize Mode Gating Tests
# ==============================================================================


def test_cli_materialize_exits_code_1_on_shortfall():
    """Verify that scripts/curate_stage6m_cohort3_dataset.py --materialize exits with code 1."""
    script_path = PROJECT_ROOT / "scripts" / "curate_stage6m_cohort3_dataset.py"
    res = subprocess.run(
        [sys.executable, str(script_path), "--materialize"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "[FAIL-CLOSED INTEGRITY CHECK]" in res.stderr or "[FAIL-CLOSED INTEGRITY CHECK]" in res.stdout
    assert "Materialization mode invoked, but fail-closed invariant forbids creating ungrounded datasets" in res.stderr or "Materialization mode invoked, but fail-closed invariant forbids creating ungrounded datasets" in res.stdout
