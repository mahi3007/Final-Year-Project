"""
DSG-CTTA Stage 5 — Blocking Tests: External Evaluation Set Integrity
=====================================================================

These tests enforce the research-validity invariants required by Phase 3N
and the broader Stage 5 protocol.

All previous tests (31/31) must continue to pass.
These 14 new tests are BLOCKING: they must pass before Stage 5A controller
implementation begins.

Tests:
  1.  test_eval_has_exactly_six_groups
  2.  test_eval_has_exactly_ten_speakers_per_group
  3.  test_eval_has_exactly_fifteen_clips_per_speaker
  4.  test_eval_total_speakers_is_sixty
  5.  test_eval_total_clips_is_nine_hundred
  6.  test_no_duplicate_recording_ids
  7.  test_no_duplicate_audio_hashes
  8.  test_all_transcripts_nonempty
  9.  test_selection_seed_provenance
  10. test_group_definition_provenance
  11. test_no_l2_arctic_speaker_reuse
  12. test_no_calibration_speaker_reuse
  13. test_eval_manifest_immutable
  14. test_eval_availability_scope_correct

Run: pytest tests/research_validity/test_stage5_external_eval.py -v
"""

from __future__ import annotations

import csv
import hashlib
import json
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"

EVAL_CSV = SPLITS_DIR / "stage5_external_eval.csv"
EVAL_MANIFEST = SPLITS_DIR / "stage5_external_eval_manifest.json"
EVAL_LOCK = SPLITS_DIR / "stage5_external_eval.lock.json"

CALIBRATION_CSV = SPLITS_DIR / "calibration.csv"

# ---------------------------------------------------------------------------
# Protocol constants (must match phase3_external_eval_curation.py & amendment)
# ---------------------------------------------------------------------------
EXPECTED_GROUPS = {
    "US English",
    "England English",
    "South Asian English",
    "Australian English",
    "Canadian English",
    "Irish English",
}
EXPECTED_STRATA_CODES = {"us", "england", "south_asian", "australia", "canada", "ireland"}
EXPECTED_SPEAKERS_PER_GROUP = 10
EXPECTED_CLIPS_PER_SPEAKER = 15
EXPECTED_TOTAL_SPEAKERS = 60
EXPECTED_TOTAL_CLIPS = 900
EXPECTED_SELECTION_SEED = 20261001
EXPECTED_RULE_VERSION = "v1.0-cv27-amended"
EXPECTED_GROUP_DEF_VERSION = "stage5_cv27_normalized_strata_v1"
EXPECTED_DATASET_RELEASE = "cv-corpus-27.0-2026-09-11"
EXPECTED_AVAILABILITY_SCOPE = "stage5_final_evaluation_only"



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_eval_csv() -> list[dict]:
    if not EVAL_CSV.exists():
        pytest.skip(f"External eval CSV not yet created: {EVAL_CSV}")
    rows = []
    with open(EVAL_CSV, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    return rows


def _load_eval_manifest() -> dict:
    if not EVAL_MANIFEST.exists():
        pytest.skip(f"Manifest not yet created: {EVAL_MANIFEST}")
    with open(EVAL_MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _load_eval_lock() -> dict:
    if not EVAL_LOCK.exists():
        pytest.skip(f"Lock file not yet created: {EVAL_LOCK}")
    with open(EVAL_LOCK, encoding="utf-8") as fh:
        return json.load(fh)


def _load_calibration_speakers() -> set[str]:
    if not CALIBRATION_CSV.exists():
        return set()
    speakers = set()
    with open(CALIBRATION_CSV, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            spk = row.get("speaker_id") or row.get("speaker") or ""
            if spk:
                speakers.add(spk.strip())
    return speakers


def _sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


# ---------------------------------------------------------------------------
# Test 1: exactly six groups
# ---------------------------------------------------------------------------

def test_eval_has_exactly_six_groups():
    """
    The external evaluation set must contain exactly the 6 predefined Stage 5 accent groups.
    """
    rows = _load_eval_csv()
    found_groups = {r.get("stage5_accent_group") or r.get("dataset_group") for r in rows}
    assert found_groups == EXPECTED_GROUPS, (
        f"Expected groups {EXPECTED_GROUPS}, found {found_groups}"
    )


# ---------------------------------------------------------------------------
# Test 2: exactly 10 speakers per group
# ---------------------------------------------------------------------------

def test_eval_has_exactly_ten_speakers_per_group():
    """
    Each group must contain exactly 10 unique speaker IDs.
    """
    rows = _load_eval_csv()
    from collections import defaultdict
    group_speakers: dict = defaultdict(set)

    for row in rows:
        grp = row.get("stage5_accent_group") or row.get("dataset_group")
        group_speakers[grp].add(row["speaker_id"])

    errors = []
    for group in EXPECTED_GROUPS:
        count = len(group_speakers[group])
        if count != EXPECTED_SPEAKERS_PER_GROUP:
            errors.append(
                f"[{group}] speakers={count}, expected={EXPECTED_SPEAKERS_PER_GROUP}"
            )

    assert not errors, "Speaker count errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 3: exactly 15 clips per speaker
# ---------------------------------------------------------------------------

def test_eval_has_exactly_fifteen_clips_per_speaker():
    """
    Each selected speaker must have exactly 15 clips in the evaluation set.
    """
    rows = _load_eval_csv()
    from collections import defaultdict
    speaker_clips: dict = defaultdict(int)

    for row in rows:
        speaker_clips[row["speaker_id"]] += 1

    errors = []
    for spk_id, count in speaker_clips.items():
        if count != EXPECTED_CLIPS_PER_SPEAKER:
            errors.append(
                f"speaker={spk_id[:16]}… clips={count}, expected={EXPECTED_CLIPS_PER_SPEAKER}"
            )

    assert not errors, f"Clip count errors ({len(errors)}):\n" + "\n".join(errors[:20])


# ---------------------------------------------------------------------------
# Test 4: total speaker count == 60
# ---------------------------------------------------------------------------

def test_eval_total_speakers_is_sixty():
    """Total unique speakers across all groups must be exactly 60."""
    rows = _load_eval_csv()
    unique_speakers = {r["speaker_id"] for r in rows}
    assert len(unique_speakers) == EXPECTED_TOTAL_SPEAKERS, (
        f"Total speakers={len(unique_speakers)}, expected={EXPECTED_TOTAL_SPEAKERS}"
    )


# ---------------------------------------------------------------------------
# Test 5: total clip count == 900
# ---------------------------------------------------------------------------

def test_eval_total_clips_is_nine_hundred():
    """Total clips in the evaluation set must be exactly 900."""
    rows = _load_eval_csv()
    assert len(rows) == EXPECTED_TOTAL_CLIPS, (
        f"Total clips={len(rows)}, expected={EXPECTED_TOTAL_CLIPS}"
    )


# ---------------------------------------------------------------------------
# Test 6: no duplicate recording IDs
# ---------------------------------------------------------------------------

def test_no_duplicate_recording_ids():
    """All recording_id values must be unique."""
    rows = _load_eval_csv()
    ids = [r["recording_id"] for r in rows]
    assert len(ids) == len(set(ids)), (
        f"Duplicate recording IDs found: {len(ids) - len(set(ids))} duplicates"
    )


# ---------------------------------------------------------------------------
# Test 7: no duplicate audio hashes
# ---------------------------------------------------------------------------

def test_no_duplicate_audio_hashes():
    """
    All non-pending audio_hash values must be unique.
    Pending ('PENDING_MATERIALIZATION') values are skipped.
    """
    rows = _load_eval_csv()
    hashes = [
        r["audio_hash"] for r in rows
        if r.get("audio_hash", "").strip()
        and r["audio_hash"] not in ("PENDING_MATERIALIZATION", "")
    ]
    if not hashes:
        pytest.skip("Audio not yet materialized — audio_hash column is PENDING")

    assert len(hashes) == len(set(hashes)), (
        f"Duplicate audio hashes: {len(hashes) - len(set(hashes))} duplicates"
    )


# ---------------------------------------------------------------------------
# Test 8: all transcripts non-empty
# ---------------------------------------------------------------------------

def test_all_transcripts_nonempty():
    """Every row must have a non-empty transcript."""
    rows = _load_eval_csv()
    empty = [r["recording_id"] for r in rows if not r.get("transcript", "").strip()]
    assert not empty, (
        f"Empty transcripts found in {len(empty)} rows: {empty[:10]}"
    )


# ---------------------------------------------------------------------------
# Test 9: selection seed provenance
# ---------------------------------------------------------------------------

def test_selection_seed_provenance():
    """
    The manifest must record the correct selection seed and rule version.
    """
    manifest = _load_eval_manifest()
    sel = manifest.get("selection", {})

    assert sel.get("seed") == EXPECTED_SELECTION_SEED, (
        f"seed={sel.get('seed')}, expected={EXPECTED_SELECTION_SEED}"
    )
    assert sel.get("rule_version") == EXPECTED_RULE_VERSION, (
        f"rule_version={sel.get('rule_version')}, expected={EXPECTED_RULE_VERSION}"
    )


# ---------------------------------------------------------------------------
# Test 10: group definition provenance
# ---------------------------------------------------------------------------

def test_group_definition_provenance():
    """
    Every row must record the correct group_definition_version and dataset_release.
    """
    rows = _load_eval_csv()
    wrong_def = [
        r["recording_id"]
        for r in rows
        if r.get("group_definition_version") != EXPECTED_GROUP_DEF_VERSION
    ]
    wrong_release = [
        r["recording_id"]
        for r in rows
        if r.get("dataset_release") != EXPECTED_DATASET_RELEASE
    ]

    assert not wrong_def, (
        f"{len(wrong_def)} rows have wrong group_definition_version: {wrong_def[:5]}"
    )
    assert not wrong_release, (
        f"{len(wrong_release)} rows have wrong dataset_release: {wrong_release[:5]}"
    )


# ---------------------------------------------------------------------------
# Test 11: no L2-ARCTIC speaker reuse
# ---------------------------------------------------------------------------

def test_no_l2_arctic_speaker_reuse():
    """
    No speaker_id in the external evaluation set should appear in any
    L2-ARCTIC splits file.

    Note: Because Common Voice uses hashed UUIDs and L2-ARCTIC uses
    researcher-assigned speaker codes, overlap is architecturally impossible.
    This test provides a programmatic guarantee.
    """
    rows = _load_eval_csv()
    cv_speakers = {r["speaker_id"] for r in rows}

    l2_speakers: set[str] = set()
    for split_file in SPLITS_DIR.glob("*.csv"):
        if "stage5_external" in split_file.name:
            continue
        try:
            with open(split_file, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    spk = row.get("speaker_id") or row.get("speaker") or ""
                    if spk:
                        l2_speakers.add(spk.strip())
        except Exception:
            pass

    shared = cv_speakers & l2_speakers
    assert not shared, (
        f"CRITICAL: {len(shared)} speaker IDs appear in both CV external set "
        f"and L2-ARCTIC splits: {list(shared)[:5]}"
    )


# ---------------------------------------------------------------------------
# Test 12: no calibration speaker reuse
# ---------------------------------------------------------------------------

def test_no_calibration_speaker_reuse():
    """
    The external evaluation speakers must not appear in the calibration split.
    This is the core independence invariant from the pre-flight audit.
    """
    rows = _load_eval_csv()
    cv_speakers = {r["speaker_id"] for r in rows}
    cal_speakers = _load_calibration_speakers()

    shared = cv_speakers & cal_speakers
    assert not shared, (
        f"CRITICAL: {len(shared)} external evaluation speakers appear in calibration: "
        f"{list(shared)[:5]}"
    )


# ---------------------------------------------------------------------------
# Test 13: manifest immutability (hash matches lock file)
# ---------------------------------------------------------------------------

def test_eval_manifest_immutable():
    """
    The SHA-256 hash of stage5_external_eval.csv must match the value
    stored in the lock file. Any modification to the evaluation set
    will cause this test to fail.
    """
    if not EVAL_CSV.exists():
        pytest.skip("Evaluation CSV not yet created")
    if not EVAL_LOCK.exists():
        pytest.skip("Lock file not yet created")

    lock = _load_eval_lock()
    expected_hash = lock.get("csv_hash")
    actual_hash = _sha256_file(EVAL_CSV)

    assert expected_hash == actual_hash, (
        f"IMMUTABILITY VIOLATED: CSV hash mismatch.\n"
        f"  Expected (lock): {expected_hash}\n"
        f"  Actual:          {actual_hash}\n"
        f"  The evaluation set has been modified after freezing."
    )


# ---------------------------------------------------------------------------
# Test 14: availability scope is correct
# ---------------------------------------------------------------------------

def test_eval_availability_scope_correct():
    """
    Every row must have availability_scope = 'stage5_final_evaluation_only'.
    This programmatically enforces the holdout rule.
    """
    rows = _load_eval_csv()
    wrong = [
        r["recording_id"]
        for r in rows
        if r.get("availability_scope") != EXPECTED_AVAILABILITY_SCOPE
    ]
    assert not wrong, (
        f"{len(wrong)} rows have wrong availability_scope: {wrong[:10]}"
    )


# ---------------------------------------------------------------------------
# Test 15: raw accent preservation and no compound/piped values
# ---------------------------------------------------------------------------

def test_eval_raw_accent_preservation_and_no_compound():
    """
    Every row must preserve the raw source accent and must not contain
    any ambiguous compound/piped ('|') values.
    """
    rows = _load_eval_csv()
    for r in rows:
        raw = r.get("source_accent_raw", "")
        rec_id = r.get("recording_id", "")
        assert raw.strip(), f"Empty source_accent_raw in {rec_id}"
        assert "|" not in raw, f"Compound/piped accent '{raw}' found in {rec_id}"


# ---------------------------------------------------------------------------
# Test 16: speaker accent homogeneity
# ---------------------------------------------------------------------------

def test_speaker_accent_homogeneity():
    """
    Every selected speaker must have 100% consistent accent declarations.
    """
    rows = _load_eval_csv()
    from collections import defaultdict
    speaker_groups = defaultdict(set)
    for r in rows:
        grp = r.get("stage5_accent_group") or r.get("dataset_group")
        speaker_groups[r["speaker_id"]].add(grp)

    for spk, grps in speaker_groups.items():
        assert len(grps) == 1, (
            f"Speaker {spk} has multiple accent groups declared: {grps}"
        )

