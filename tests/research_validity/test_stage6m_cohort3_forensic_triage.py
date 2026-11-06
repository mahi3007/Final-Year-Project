#!/usr/bin/env python3
"""
tests/research_validity/test_stage6m_cohort3_forensic_triage.py

Automated Test Suite for Stage 6M Task 7.7.1D Forensic Engine Remediation
========================================================================
Validates:
1. Governance: Embedded digests, authorization fields, and exhaustive one-field tampering suite.
2. Quarantine Integrity: Archive member path validation, duplicate member rejection,
   truncated member rejection, zero-byte file rejection, and collision handling.
3. SoundFile Bounded Chunk Decoding: True decoded PCM frame counting vs container estimate.
4. MPEG Frame Boundary Walker: Sync words, frame lengths, physical frame integrity, truncation detection.
5. Xing & LAME Gapless Tag Parser: Strict Frame 0 expected location verification and delay/padding extraction.
6. Numerical Gapless Reconciliation: Reconciliation against LAME delay/padding within tolerance.
7. Decoder Agreement / Disagreement: Multi-decoder consensus vs fail-closed INCONCLUSIVE on discrepancy.
8. Negative Evidentiary Proof: Proves that missing gapless metadata CANNOT yield VALID_GAPLESS_PADDING.
9. Quarantined Inventory Verification: Proves all 130 clips are individually reconciled with 100% complete frames.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import struct
import tarfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from scripts.quarantine_stage6m_cohort3_rejected_audio import (
    APPROVED_QUARANTINE_DEST_REL,
    DATASET_ID,
    extract_tar_member_to_file,
    scan_quarantine_inventory,
    validate_archive_member_path,
    verify_quarantine_retrieval_authorization,
)
from scripts.triage_cohort3_rejected_clips import (
    APPROVED_PARENT_MANIFEST_SHA256,
    APPROVED_QUARANTINE_LEDGER_SHA256,
    APPROVED_QUARANTINE_LEDGER_SHA256_LF,
    APPROVED_TARGETS_LIST_SHA256,
    FORENSIC_AUTH_JSON,
    PARENT_MANIFEST_JSON,
    QUARANTINE_DIR,
    QUARANTINE_LEDGER_CSV,
    QUARANTINE_TARGETS_JSON,
    TOTAL_QUARANTINE_TARGETS,
    compute_expected_xing_offset,
    compute_sha256,
    decode_with_miniaudio,
    decode_with_pyav,
    decode_with_soundfile,
    inspect_mpeg_physical_frames,
    parse_id3v2_header,
    parse_xing_and_lame_metadata,
    perform_single_file_forensic_triage,
    verify_governance_prerequisites,
)


# ============================================================================
# 1. Governance & Cryptographic Integrity Tests
# ============================================================================

def test_triage_governance_canonical_artifacts():
    """Verify that canonical governance artifacts match frozen cryptographic digests."""
    digests = verify_governance_prerequisites(
        parent_manifest_path=PARENT_MANIFEST_JSON,
        targets_json_path=QUARANTINE_TARGETS_JSON,
        auth_json_path=FORENSIC_AUTH_JSON,
        quarantine_ledger_path=QUARANTINE_LEDGER_CSV,
    )
    assert digests["parent_manifest_sha256"] == APPROVED_PARENT_MANIFEST_SHA256
    assert digests["quarantine_targets_sha256"] == APPROVED_TARGETS_LIST_SHA256
    assert digests["quarantine_ledger_sha256"] in (APPROVED_QUARANTINE_LEDGER_SHA256, APPROVED_QUARANTINE_LEDGER_SHA256_LF)
    assert len(digests["forensic_authorization_sha256"]) == 64


TAMPER_CASES = [
    ("governance_status", "PROVISIONAL_UNAUTHORIZED"),
    ("parent_provisional_manifest.sha256", "0" * 64),
    ("quarantine_target_list.sha256", "1" * 64),
    ("quarantine_target_list.target_recordings_count", 999),
    ("source_dataset.dataset_id", "unauthorized_dataset_id"),
    ("source_dataset.platform", "HuggingFace Hub"),
    ("quarantine_destination.directory_rel", "datasets/unauthorized"),
    ("authorization_boundaries.authorizing_role", "Junior Developer"),
    ("authorization_boundaries.decision_status", "UNAUTHORIZED"),
    ("authorization_boundaries.purpose", "Production pipeline processing"),
    ("authorization_boundaries.substitutions_permitted", 5),
    ("authorization_boundaries.manifest_modification", "PERMITTED"),
    ("authorization_boundaries.cohort_promotion", "PERMITTED"),
    ("authorization_boundaries.execution_gating.quarantine_retrieval", "BLOCKED"),
    ("authorization_boundaries.execution_gating.forensic_triage", "BLOCKED"),
    ("authorization_boundaries.execution_gating.cohort_promotion", "AUTHORIZED"),
    ("authorization_boundaries.execution_gating.final_manifest_lock", "UNLOCKED"),
    ("authorization_boundaries.execution_gating.gpu_ctta_adaptation", "RUNNING"),
    ("authorization_boundaries.execution_gating.confirmatory_inference", "RUNNING"),
]


@pytest.mark.parametrize("field_path,tampered_val", TAMPER_CASES)
def test_governance_exhaustive_one_field_tampering(tmp_path, field_path, tampered_val):
    """Proves that triage engine fails closed when ANY authorization field is tampered with."""
    with open(FORENSIC_AUTH_JSON, "r", encoding="utf-8") as f:
        auth_data = json.load(f)

    # Mutate field
    parts = field_path.split(".")
    curr = auth_data
    for p in parts[:-1]:
        curr = curr[p]
    curr[parts[-1]] = tampered_val

    tampered_auth = tmp_path / f"tampered_{field_path.replace('.', '_')}.json"
    tampered_auth.write_text(json.dumps(auth_data), encoding="utf-8")

    with pytest.raises(ValueError):
        verify_governance_prerequisites(
            parent_manifest_path=PARENT_MANIFEST_JSON,
            targets_json_path=QUARANTINE_TARGETS_JSON,
            auth_json_path=tampered_auth,
            quarantine_ledger_path=QUARANTINE_LEDGER_CSV,
        )


def test_governance_ledger_tampering_rejection(tmp_path):
    """Verify that tampered quarantine ledger fails closed."""
    tampered_ledger = tmp_path / "tampered_ledger.csv"
    tampered_ledger.write_text("corrupted,ledger,data\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Quarantine ledger SHA-256 mismatch"):
        verify_governance_prerequisites(
            parent_manifest_path=PARENT_MANIFEST_JSON,
            targets_json_path=QUARANTINE_TARGETS_JSON,
            auth_json_path=FORENSIC_AUTH_JSON,
            quarantine_ledger_path=tampered_ledger,
        )


# ============================================================================
# 2. Quarantine Integrity & Member Extraction Tests
# ============================================================================

def test_archive_member_path_validation():
    """Verify exact archive member path validation against expected Common Voice hierarchy."""
    target_map = {"clip_001.mp3": {}, "clip_002.mp3": {}}

    # Valid paths
    valid1, name1 = validate_archive_member_path("cv-corpus-27.0-2024-12-06/en/clips/clip_001.mp3", target_map)
    assert valid1 is True
    assert name1 == "clip_001.mp3"

    valid2, name2 = validate_archive_member_path("clips/clip_002.mp3", target_map)
    assert valid2 is True
    assert name2 == "clip_002.mp3"

    # Invalid paths
    assert validate_archive_member_path("../clips/clip_001.mp3", target_map)[0] is False
    assert validate_archive_member_path("clips/unknown_clip.mp3", target_map)[0] is False
    assert validate_archive_member_path("clips/clip_001.wav", target_map)[0] is False
    assert validate_archive_member_path("other_dir/clip_001.mp3", target_map)[0] is False


def test_tar_member_extraction_integrity(tmp_path):
    """Verify atomic member extraction, byte count verification, and zero-byte rejection."""
    dest_file = tmp_path / "test_extract.mp3"
    part_file = tmp_path / "test_extract.mp3.part"

    payload = b"TEST_AUDIO_BYTES_PAYLOAD" * 100

    # 1. Successful extraction
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w") as tar:
        tinfo = tarfile.TarInfo(name="clips/test_extract.mp3")
        tinfo.size = len(payload)
        tar.addfile(tinfo, io.BytesIO(payload))
    bio.seek(0)

    with tarfile.open(fileobj=bio, mode="r") as tar:
        member = tar.getmember("clips/test_extract.mp3")
        written, sha = extract_tar_member_to_file(tar, member, dest_file)

    assert dest_file.is_file()
    assert not part_file.exists()
    assert written == len(payload)
    assert sha == hashlib.sha256(payload).hexdigest()

    # 2. Zero-byte member rejection
    dest_zero = tmp_path / "zero.mp3"
    bio_zero = io.BytesIO()
    with tarfile.open(fileobj=bio_zero, mode="w") as tar:
        tinfo_zero = tarfile.TarInfo(name="clips/zero.mp3")
        tinfo_zero.size = 0
        tar.addfile(tinfo_zero, io.BytesIO(b""))
    bio_zero.seek(0)

    with tarfile.open(fileobj=bio_zero, mode="r") as tar:
        member_zero = tar.getmember("clips/zero.mp3")
        with pytest.raises(ValueError, match="Refusing to extract zero-byte archive member"):
            extract_tar_member_to_file(tar, member_zero, dest_zero)

    # 3. Size mismatch rejection (truncated extraction)
    dest_trunc = tmp_path / "trunc.mp3"
    bio_trunc = io.BytesIO()
    with tarfile.open(fileobj=bio_trunc, mode="w") as tar:
        tinfo_trunc = tarfile.TarInfo(name="clips/trunc.mp3")
        payload_trunc = b"A" * 200
        tinfo_trunc.size = len(payload_trunc)
        tar.addfile(tinfo_trunc, io.BytesIO(payload_trunc))
    bio_trunc.seek(0)

    with tarfile.open(fileobj=bio_trunc, mode="r") as tar:
        member_trunc = tar.getmember("clips/trunc.mp3")
        # Simulate member truncated mid-stream (e.g. socket drop or truncated tar archive)
        with patch.object(tar, "extractfile", return_value=io.BytesIO(b"A" * 100)):
            with pytest.raises(IOError, match="Byte count mismatch"):
                extract_tar_member_to_file(tar, member_trunc, dest_trunc)
    assert not dest_trunc.exists()
    assert not (tmp_path / "trunc.mp3.part").exists()


def test_scan_quarantine_inventory_rejects_zero_byte_and_foreign_files(tmp_path):
    """Verify that scan_quarantine_inventory fails closed on zero-byte or foreign files."""
    q_dir = tmp_path / "quarantine"
    q_dir.mkdir()
    target_map = {
        "valid.mp3": {
            "recording_id": "rec_1", "clip_filename": "valid.mp3",
            "speaker_id": "spk_1", "accent_group": "Canada", "stratum_code": "ca", "panel_role": "evaluation"
        }
    }

    # 1. Clean valid file
    (q_dir / "valid.mp3").write_bytes(b"VALID_MP3_DATA_12345")
    inv = scan_quarantine_inventory(target_map, q_dir)
    assert len(inv) == 1
    assert "valid.mp3" in inv

    # 2. Zero-byte file rejection
    (q_dir / "valid.mp3").write_bytes(b"")
    with pytest.raises(ValueError, match="Unverified zero-byte file detected"):
        scan_quarantine_inventory(target_map, q_dir)

    # 3. Foreign unexpected file rejection
    (q_dir / "valid.mp3").write_bytes(b"VALID_MP3_DATA_12345")
    (q_dir / "foreign.mp3").write_bytes(b"FOREIGN_UNAUTHORIZED_FILE")
    with pytest.raises(ValueError, match="Unexpected foreign file"):
        scan_quarantine_inventory(target_map, q_dir)


# ============================================================================
# 3. MPEG Frame Walker & Bitstream Verification Tests
# ============================================================================

def test_id3v2_header_parser():
    """Verify ID3v2.4 header parsing including synchsafe integer size."""
    tag_data = b"ID3\x04\x00\x00\x00\x00\x01\x00" + (b"\x00" * 128)
    present, ver, size, offset, enc = parse_id3v2_header(tag_data)
    assert present is True
    assert ver == "2.4.0"
    assert size == 138
    assert offset == 138


def test_mpeg_physical_frame_parser_detects_truncation():
    """Verify that incomplete trailing frames are correctly flagged as physical truncation."""
    frame_hdr = b"\xFF\xFB\x54\xC4"  # MPEG-1 Layer III 64 kbps, 48 kHz mono -> 192 bytes
    valid_frame = frame_hdr + (b"\x00" * 188)
    assert len(valid_frame) == 192

    # 1. Clean frame
    res_clean = inspect_mpeg_physical_frames(valid_frame, audio_offset=0)
    assert res_clean["total_physical_frames"] == 1
    assert res_clean["all_frames_valid"] is True
    assert res_clean["final_frame_complete"] is True
    assert res_clean["trailing_bytes_count"] == 0

    # 2. Truncated trailing frame (only 100 bytes of 192)
    truncated_stream = valid_frame + valid_frame[:100]
    res_trunc = inspect_mpeg_physical_frames(truncated_stream, audio_offset=0)
    assert res_trunc["total_physical_frames"] == 1
    assert res_trunc["final_frame_complete"] is False
    assert res_trunc["all_frames_valid"] is False
    assert "Bitstream ended before frame completed" in res_trunc["incomplete_frame_details"]["reason"]

    # 3. Trailing garbage bytes
    garbage_stream = valid_frame + b"\x12\x34\x56"
    res_garb = inspect_mpeg_physical_frames(garbage_stream, audio_offset=0)
    assert res_garb["trailing_bytes_count"] == 3
    assert res_garb["final_frame_complete"] is False


# ============================================================================
# 4. Xing & LAME Gapless Metadata Parsing Tests
# ============================================================================

def test_synthetic_xing_lame_frame0_detection():
    """Verify parsing of synthetic Xing/Info header and 24-bit delay/padding tag at Frame 0."""
    # MPEG-1 Layer III 64 kbps, 44.1 kHz, mono
    # hdr: 0xFF, 0xFB, 0x50, 0xC4 (208 bytes frame length)
    hdr = b"\xFF\xFB\x50\xC4"
    expected_offset = compute_expected_xing_offset(hdr)
    assert expected_offset == 21  # 4 header + 17 side info

    prefix = hdr + (b"\x00" * 17)
    assert len(prefix) == 21

    # Delay = 576 (0x240), Padding = 1401 (0x579)
    # 24-bit packed: (0x240 << 12) | 0x579 -> bytes [0x24, 0x05, 0x79]
    d_p_packed = bytes([0x24, 0x05, 0x79])

    xing_body = (
        b"Xing"
        + struct.pack(">I", 0x0B)  # Flags: frames, bytes, quality
        + struct.pack(">I", 186)   # 186 declared frames
        + struct.pack(">I", 38870) # declared bytes
        + struct.pack(">I", 50)    # quality
        + b"LAME3.99r"             # 9-byte encoder string
        + (b"\x00" * 12)           # 12 info bytes
        + d_p_packed               # delay & padding bytes
    )
    frame0 = prefix + xing_body
    frame0 += b"\xAA" * (208 - len(frame0))
    assert len(frame0) == 208

    # 1. At expected location
    meta = parse_xing_and_lame_metadata(frame0, audio_offset=0)
    assert meta["xing_header_present"] is True
    assert meta["at_expected_location"] is True
    assert meta["header_type"] == "Xing"
    assert meta["xing_declared_frames"] == 186
    assert meta["lame_tag_present"] is True
    assert meta["encoder_delay_samples"] == 576
    assert meta["encoder_padding_samples"] == 1401
    assert meta["has_gapless_lame_tag"] is True

    # 2. Misplaced Xing (e.g. offset 10 instead of 21)
    misplaced_frame = hdr + (b"\x00" * 6) + xing_body
    misplaced_frame += b"\xAA" * (208 - len(misplaced_frame))
    meta_misplaced = parse_xing_and_lame_metadata(misplaced_frame, audio_offset=0)
    assert meta_misplaced["xing_header_present"] is False
    assert meta_misplaced["at_expected_location"] is False
    assert meta_misplaced["has_gapless_lame_tag"] is False


# ============================================================================
# 5. Numerical Gapless Reconciliation & Negative Evidentiary Proof
# ============================================================================

def test_missing_metadata_cannot_yield_valid_gapless_padding(tmp_path):
    """
    CRITICAL PROOF: A file with 100% complete frames and exact multi-decoder agreement
    CANNOT be classified as VALID_GAPLESS_PADDING if gapless metadata is absent.
    Must be classified as INCONCLUSIVE.
    """
    target_info = {
        "recording_id": "syn_rec_001",
        "clip_filename": "syn_missing_meta.mp3",
        "speaker_id": "spk_synth",
        "accent_group": "Canada",
        "stratum_code": "canada",
        "panel_role": "evaluation",
        "task7_7_error_message": "decoded 214272 frames but header declares 216249 (shortfall of 1977 frames)",
    }

    test_file = tmp_path / "syn_missing_meta.mp3"

    # Build 2 clean MPEG-1 Layer III frames (416 bytes total) without Xing header
    hdr = b"\xFF\xFB\x50\xC4"  # 208 bytes/frame, 1152 samples/frame -> 2304 samples capacity
    frame = hdr + (b"\x00" * 204)
    raw_data = frame * 2
    test_file.write_bytes(raw_data)

    # Mock decoders to return complete, agreeing sample counts
    mock_sf = {
        "success": True,
        "metadata_declared_frames": 2304 + 1977,
        "actual_decoded_pcm_frames": 2304,
        "decoded_pcm_frames": 2304,
        "sample_rate": 44100,
        "channels": 1,
        "error": None,
    }
    mock_av = {"success": True, "decoded_pcm_frames": 2304, "sample_rate": 44100, "channels": 1, "error": None}
    mock_ma = {"success": True, "decoded_pcm_frames": 2304, "sample_rate": 44100, "channels": 1, "error": None}

    with patch("scripts.triage_cohort3_rejected_clips.decode_with_soundfile", return_value=mock_sf), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_pyav", return_value=mock_av), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_miniaudio", return_value=mock_ma):

        res = perform_single_file_forensic_triage(test_file, target_info)

    # Invariants under Protocol Section 14.7:
    assert res["forensic_classification"] == "INCONCLUSIVE"
    assert res["forensic_classification"] != "VALID_GAPLESS_PADDING"
    assert res["reconciliation"]["gapless_numerically_reconciled"] is False
    assert res["reconciliation"]["reconciliation_status"] == "MISSING_GAPLESS_METADATA"
    assert any("credible gapless metadata" in r and "ABSENT" in r for r in res["classification_reasons"])


def test_decoder_disagreement_fails_closed_to_inconclusive(tmp_path):
    """Verify that decoder disagreement on decoded sample counts yields INCONCLUSIVE."""
    target_info = {
        "recording_id": "syn_disagree_001",
        "clip_filename": "syn_disagree.mp3",
        "speaker_id": "spk_synth",
        "accent_group": "Canada",
        "stratum_code": "canada",
        "panel_role": "evaluation",
        "task7_7_error_message": "",
    }
    test_file = tmp_path / "syn_disagree.mp3"
    hdr = b"\xFF\xFB\x50\xC4"
    test_file.write_bytes(hdr + (b"\x00" * 204))

    # Mock decoders disagreeing (SoundFile: 1152, PyAV: 1152, miniaudio: 1100)
    mock_sf = {"success": True, "metadata_declared_frames": 1152, "actual_decoded_pcm_frames": 1152, "decoded_pcm_frames": 1152, "sample_rate": 44100, "channels": 1, "error": None}
    mock_av = {"success": True, "decoded_pcm_frames": 1152, "sample_rate": 44100, "channels": 1, "error": None}
    mock_ma = {"success": True, "decoded_pcm_frames": 1100, "sample_rate": 44100, "channels": 1, "error": None}

    with patch("scripts.triage_cohort3_rejected_clips.decode_with_soundfile", return_value=mock_sf), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_pyav", return_value=mock_av), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_miniaudio", return_value=mock_ma):

        res = perform_single_file_forensic_triage(test_file, target_info)

    assert res["forensic_classification"] == "INCONCLUSIVE"
    assert res["reconciliation"]["exact_decoder_agreement"] is False
    assert res["reconciliation"]["decoder_discrepancy_samples"] == 52


def test_numerical_gapless_reconciliation_boundary(tmp_path):
    """Verify numerical reconciliation when valid gapless metadata exists."""
    target_info = {
        "recording_id": "syn_rec_valid",
        "clip_filename": "syn_rec_valid.mp3",
        "speaker_id": "spk_synth",
        "accent_group": "Canada",
        "stratum_code": "canada",
        "panel_role": "evaluation",
        "task7_7_error_message": "decoded 214272 frames but header declares 216249 (shortfall of 1977 frames)",
    }
    test_file = tmp_path / "syn_rec_valid.mp3"
    hdr = b"\xFF\xFB\x50\xC4"
    test_file.write_bytes(hdr + (b"\x00" * 204))

    # 1. Matching shortfall within 1 MPEG frame tolerance (shortfall=1977, trim=1977)
    mock_meta_match = {
        "xing_header_present": True,
        "at_expected_location": True,
        "has_gapless_lame_tag": True,
        "encoder_delay_samples": 576,
        "encoder_padding_samples": 1401,  # 576 + 1401 = 1977
    }
    mock_sf = {"success": True, "metadata_declared_frames": 216249, "actual_decoded_pcm_frames": 214272, "decoded_pcm_frames": 214272, "sample_rate": 44100, "channels": 1, "error": None}
    mock_av = {"success": True, "decoded_pcm_frames": 214272, "sample_rate": 44100, "channels": 1, "error": None}
    mock_ma = {"success": True, "decoded_pcm_frames": 214272, "sample_rate": 44100, "channels": 1, "error": None}

    with patch("scripts.triage_cohort3_rejected_clips.parse_xing_and_lame_metadata", return_value=mock_meta_match), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_soundfile", return_value=mock_sf), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_pyav", return_value=mock_av), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_miniaudio", return_value=mock_ma):

        res_match = perform_single_file_forensic_triage(test_file, target_info)

    assert res_match["reconciliation"]["gapless_numerically_reconciled"] is True
    assert res_match["forensic_classification"] == "VALID_GAPLESS_PADDING"

    # 2. Shortfall exceeding tolerance (shortfall=5000 vs trim=1977) -> INCONCLUSIVE
    mock_sf_mismatch = {"success": True, "metadata_declared_frames": 219272, "actual_decoded_pcm_frames": 214272, "decoded_pcm_frames": 214272, "sample_rate": 44100, "channels": 1, "error": None}
    with patch("scripts.triage_cohort3_rejected_clips.parse_xing_and_lame_metadata", return_value=mock_meta_match), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_soundfile", return_value=mock_sf_mismatch), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_pyav", return_value=mock_av), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_miniaudio", return_value=mock_ma):

        res_mismatch = perform_single_file_forensic_triage(test_file, target_info)

    assert res_mismatch["reconciliation"]["gapless_numerically_reconciled"] is False
    assert res_mismatch["forensic_classification"] == "INCONCLUSIVE"


def test_decoder_failure_without_physical_truncation_yields_inconclusive(tmp_path):
    """Verify that when physical frames are complete, a decoder failure fails closed to INCONCLUSIVE rather than TRUNCATED_BITSTREAM."""
    target_info = {
        "recording_id": "syn_dec_fail_001",
        "clip_filename": "syn_dec_fail.mp3",
        "speaker_id": "spk_synth",
        "accent_group": "Canada",
        "stratum_code": "canada",
        "panel_role": "evaluation",
        "task7_7_error_message": "",
    }
    test_file = tmp_path / "syn_dec_fail.mp3"
    hdr = b"\xFF\xFB\x50\xC4"  # valid MPEG-1 Layer III 64 kbps mono frame header
    test_file.write_bytes(hdr + (b"\x00" * 204))  # 208 bytes frame

    # Mock decoder failure (e.g. soundfile raises decoding error)
    mock_sf_fail = {"success": False, "error": "Internal decoder crash", "metadata_declared_frames": None, "actual_decoded_pcm_frames": None}
    mock_av = {"success": True, "decoded_pcm_frames": 1152, "sample_rate": 44100, "channels": 1, "error": None}
    mock_ma = {"success": True, "decoded_pcm_frames": 1152, "sample_rate": 44100, "channels": 1, "error": None}

    with patch("scripts.triage_cohort3_rejected_clips.decode_with_soundfile", return_value=mock_sf_fail), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_pyav", return_value=mock_av), \
         patch("scripts.triage_cohort3_rejected_clips.decode_with_miniaudio", return_value=mock_ma):

        res = perform_single_file_forensic_triage(test_file, target_info)

    # Must be INCONCLUSIVE, NOT TRUNCATED_BITSTREAM, because bitstream itself is not physically truncated
    assert res["forensic_classification"] == "INCONCLUSIVE"
    assert res["forensic_classification"] != "TRUNCATED_BITSTREAM"
    assert any("Decoder failure without confirmed physical bitstream truncation" in r for r in res["classification_reasons"])


# ============================================================================
# 6. Physical Quarantined 130-File Consensus Verification
# ============================================================================

def test_all_130_quarantined_files_physical_and_decoder_consensus():
    """
    Verifies that all 130 quarantined recordings:
    1. Possess 100% complete MPEG-1 Layer III frames with zero trailing bytes.
    2. Have verified frame-by-frame Constant Bitrate (78 at 64 kbps, 52 at 48 kbps).
    3. Have exact multi-decoder agreement (SoundFile == PyAV == miniaudio).
    4. Exactly equal physical frame capacity (N_frames * 1152).
    5. Are classified as INCONCLUSIVE due to lack of Frame 0 gapless metadata.
    """
    if not QUARANTINE_DIR.is_dir():
        pytest.skip(f"Quarantine directory {QUARANTINE_DIR} not found.")

    with open(QUARANTINE_TARGETS_JSON, "r", encoding="utf-8") as f:
        targets = json.load(f)["targets"]

    assert len(targets) == TOTAL_QUARANTINE_TARGETS

    bitrate_counts: Dict[int, int] = {}

    for target in targets:
        fname = target["clip_filename"]
        fpath = QUARANTINE_DIR / fname
        assert fpath.is_file(), f"Quarantine recording missing: {fname}"

        raw_bytes = fpath.read_bytes()
        id3_present, id3_ver, id3_size, audio_offset, id3_enc = parse_id3v2_header(raw_bytes)

        # 1. Physical bitstream
        frame_scan = inspect_mpeg_physical_frames(raw_bytes, audio_offset)
        assert frame_scan["all_frames_valid"] is True, f"Invalid frames in {fname}"
        assert frame_scan["final_frame_complete"] is True, f"Incomplete final frame in {fname}"
        assert frame_scan["trailing_bytes_count"] == 0, f"Trailing bytes in {fname}"
        assert frame_scan["is_constant_bitrate"] is True, f"Non-CBR frames detected in {fname}"

        dom_br = frame_scan["dominant_bitrate_kbps"]
        bitrate_counts[dom_br] = bitrate_counts.get(dom_br, 0) + 1

        # 2. SoundFile chunked decode
        sf_res = decode_with_soundfile(fpath)
        assert sf_res["success"] is True

        # 3. PyAV decode
        av_res = decode_with_pyav(fpath)
        assert av_res["success"] is True

        # 4. miniaudio decode
        ma_res = decode_with_miniaudio(fpath)
        assert ma_res["success"] is True

        # Consensus invariants
        assert sf_res["actual_decoded_pcm_frames"] == av_res["decoded_pcm_frames"] == ma_res["decoded_pcm_frames"]
        assert sf_res["actual_decoded_pcm_frames"] == frame_scan["total_physical_capacity_samples"]

        # 5. Metadata absence
        meta = parse_xing_and_lame_metadata(raw_bytes, audio_offset)
        assert meta["has_gapless_lame_tag"] is False, f"Unexpected gapless tag found in CBR file {fname}"

        # 6. Triage result must be INCONCLUSIVE
        triage = perform_single_file_forensic_triage(fpath, target)
        assert triage["forensic_classification"] == "INCONCLUSIVE"
        assert triage["forensic_classification"] != "VALID_GAPLESS_PADDING"
        assert triage["forensic_classification"] != "TRUNCATED_BITSTREAM"

    # Exactly 78 at 64 kbps, 52 at 48 kbps
    assert bitrate_counts == {64: 78, 48: 52}
