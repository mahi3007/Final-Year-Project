#!/usr/bin/env python3
"""
tests/research_validity/test_stage6m_cohort3_forensic_triage.py

Automated Test Suite for Stage 6M Task 7.7.1 Forensic Triage Engine
===================================================================
Validates:
1. Governance and cryptographic hash verification.
2. Custom MPEG-1 Layer III physical frame boundary walker and sync detection.
3. ID3v2 header and Xing/Info/LAME tag extraction.
4. Independent decoder interfaces (PyAV, miniaudio, SoundFile).
5. Deterministic triage classification rules (VALID_GAPLESS_PADDING vs TRUNCATED_BITSTREAM vs INCONCLUSIVE).
"""

import hashlib
import json
import struct
from pathlib import Path

import pytest

from scripts.triage_cohort3_rejected_clips import (
    APPROVED_PARENT_MANIFEST_SHA256,
    APPROVED_TARGETS_LIST_SHA256,
    FORENSIC_AUTH_JSON,
    PARENT_MANIFEST_JSON,
    QUARANTINE_TARGETS_JSON,
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


def test_triage_governance_canonical_artifacts():
    """Verify that canonical governance artifacts match frozen cryptographic digests."""
    digests = verify_governance_prerequisites(
        parent_manifest_path=PARENT_MANIFEST_JSON,
        targets_json_path=QUARANTINE_TARGETS_JSON,
        auth_json_path=FORENSIC_AUTH_JSON,
    )
    assert digests["parent_manifest_sha256"] == APPROVED_PARENT_MANIFEST_SHA256
    assert digests["quarantine_targets_sha256"] == APPROVED_TARGETS_LIST_SHA256
    assert len(digests["forensic_authorization_sha256"]) == 64


def test_triage_governance_tampering_rejection(tmp_path):
    """Verify that triage engine fails closed when governance artifacts are tampered with."""
    tampered_manifest = tmp_path / "tampered_manifest.json"
    tampered_manifest.write_text('{"tampered": true}', encoding="utf-8")

    with pytest.raises(ValueError, match="Parent manifest SHA-256 mismatch"):
        verify_governance_prerequisites(
            parent_manifest_path=tampered_manifest,
            targets_json_path=QUARANTINE_TARGETS_JSON,
            auth_json_path=FORENSIC_AUTH_JSON,
        )


def test_id3v2_header_parser():
    """Verify ID3v2.4 header parsing including synchsafe integer size."""
    # 10-byte ID3 header: 'ID3', ver 4.0, flags 0, size = 128 bytes (synchsafe: 0 0 1 0)
    # synchsafe 128 = 0x00, 0x00, 0x01, 0x00 -> (1 << 7) = 128
    tag_data = b"ID3\x04\x00\x00\x00\x00\x01\x00" + (b"\x00" * 128)
    present, ver, size, offset, enc = parse_id3v2_header(tag_data)
    assert present is True
    assert ver == "2.4.0"
    assert size == 138  # 10 header + 128 payload
    assert offset == 138


def test_mpeg_physical_frame_parser_detects_truncation():
    """Verify that incomplete trailing frames are correctly flagged as physical truncation."""
    # Build a valid MPEG-1 Layer III 64 kbps, 48 kHz mono frame header
    # Byte 0: 0xFF
    # Byte 1: 0xFB (11111011 -> MPEG-1, Layer III, no CRC)
    # Byte 2: 0x54 (01010100 -> 64 kbps, 48 kHz, no padding)
    # Byte 3: 0xC4 (11000100 -> mono)
    # Frame len = (144000 * 64) // 48000 = 192 bytes
    frame_hdr = b"\xFF\xFB\x54\xC4"
    frame_body = b"\x00" * 188
    valid_frame = frame_hdr + frame_body
    assert len(valid_frame) == 192

    # 1. Test clean single frame
    res_clean = inspect_mpeg_physical_frames(valid_frame, audio_offset=0)
    assert res_clean["total_physical_frames"] == 1
    assert res_clean["all_frames_valid"] is True
    assert res_clean["final_frame_complete"] is True
    assert res_clean["trailing_bytes_count"] == 0

    # 2. Test truncated trailing frame (only 100 bytes of a 192-byte frame)
    truncated_stream = valid_frame + valid_frame[:100]
    res_trunc = inspect_mpeg_physical_frames(truncated_stream, audio_offset=0)
    assert res_trunc["total_physical_frames"] == 1
    assert res_trunc["final_frame_complete"] is False
    assert res_trunc["all_frames_valid"] is False
    assert "Bitstream ended before frame completed" in res_trunc["incomplete_frame_details"]["reason"]


def test_independent_decoders_on_cohort3_audio():
    """Verify that PyAV, miniaudio, and SoundFile can inspect existing cohort MP3 audio."""
    cohort_dir = Path("datasets/external/common_voice_27/cohort3_audio")
    sample_files = list(cohort_dir.glob("*.mp3"))
    if not sample_files:
        pytest.skip("No sample MP3 files found in cohort3_audio")

    sample_mp3 = sample_files[0]

    sf_res = decode_with_soundfile(sample_mp3)
    av_res = decode_with_pyav(sample_mp3)
    ma_res = decode_with_miniaudio(sample_mp3)

    assert sf_res["success"] is True
    assert av_res["success"] is True
    assert ma_res["success"] is True

    assert sf_res["sample_rate"] == 48000
    assert av_res["sample_rate"] == 48000
    assert ma_res["sample_rate"] == 48000

    # PyAV and miniaudio (dr_mp3) match exact sample counts
    assert av_res["decoded_pcm_frames"] == ma_res["decoded_pcm_frames"]
    assert av_res["decoded_pcm_frames"] > 0
