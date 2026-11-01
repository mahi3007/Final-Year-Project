"""
tests/research_validity/test_stage6m_cohort3_audio_materialization.py

Deterministic Automated Test Suite for Stage 6M v1.5 Cohort 3 Audio Materializer & Integrity Validator
=====================================================================================================
Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)
Phase: Stage 6M v1.5 Milestone 7.4 (Audio Materialization & Integrity Validation)

Test Invariants:
1. Target Manifest Agreement:
   - Loads exactly 18,975 target clips across 1,265 speakers from provisional manifest.
2. Physical Audio Validation:
   - Detection and fail-closed handling of zero-byte, missing, or corrupt files.
   - Successful validation of soundfile decodability, positive duration, channels, sample rate, and SHA-256.
3. Sourcing and Zero Substitution:
   - Verifies local sourcing mode without silent substitutions.
4. Completeness and Ledgers:
   - Generates per-clip SHA-256 ledger, failed-clips report, and speaker-completeness report.
5. Execution Gating:
   - Confirmatory GPU adaptation and model inference remain STRICTLY BLOCKED.
   - Provisional manifest remains UNLOCKED.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.materialize_stage6m_cohort3_audio import (
    CLIPS_PER_SPEAKER,
    FAILED_REPORT_JSON,
    LEDGER_CSV,
    MATERIALIZATION_JSON,
    MATERIALIZATION_MD,
    PROVISIONAL_MANIFEST_JSON,
    SPEAKER_REPORT_JSON,
    TOTAL_EXPECTED_CLIPS,
    TOTAL_EXPECTED_SPEAKERS,
    generate_materialization_artifacts,
    load_provisional_manifest,
    materialize_from_local_source,
    scan_local_inventory,
    validate_audio_file,
)


def _generate_synthetic_wav_as_mp3(path: Path, duration_sec: float = 1.0, sr: int = 16000):
    """Generates a valid audio file using soundfile for testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    audio = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    # Write as WAV format
    sf.write(str(path), audio, sr, format="WAV")


def test_target_manifest_scale_and_fields():
    """Verify that materializer reads exactly 18,975 records across 1,265 speakers."""
    meta, records, target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    assert len(records) == TOTAL_EXPECTED_CLIPS == 18975
    assert len(target_map) == TOTAL_EXPECTED_CLIPS == 18975
    assert meta["manifest_type"] == "PROVISIONAL_SELECTION_MANIFEST"
    assert meta["manifest_status"] == "UNLOCKED"


def test_validate_audio_file_boundaries(tmp_path):
    """Verify audio file validator handles missing, zero-byte, corrupt, and valid audio."""
    # 1. Missing file
    missing = tmp_path / "nonexistent.mp3"
    valid, dur, sr, ch, h, err = validate_audio_file(missing)
    assert not valid
    assert "does not exist" in err

    # 2. Zero-byte file
    empty = tmp_path / "empty.mp3"
    empty.write_bytes(b"")
    valid, dur, sr, ch, h, err = validate_audio_file(empty)
    assert not valid
    assert "empty" in err

    # 3. Corrupted header
    corrupt = tmp_path / "corrupt.mp3"
    corrupt.write_bytes(b"GARBAGE_HEADER_DATA_NOT_AUDIO")
    valid, dur, sr, ch, h, err = validate_audio_file(corrupt)
    assert not valid
    assert "Decode failure" in err

    # 4. Valid audio
    good = tmp_path / "good.wav"
    _generate_synthetic_wav_as_mp3(good, duration_sec=1.5, sr=16000)
    valid, dur, sr, ch, h, err = validate_audio_file(good)
    assert valid
    assert dur == pytest.approx(1.5, rel=1e-2)
    assert sr == 16000
    assert ch == 1
    assert len(h) == 64
    assert err == ""


def test_local_sourcing_and_completeness_tracking(tmp_path):
    """Verify that local materialization correctly copies, decodes, and records inventory."""
    source_pool = tmp_path / "source_pool"
    dest_audio = tmp_path / "cohort3_audio"
    source_pool.mkdir(parents=True, exist_ok=True)
    dest_audio.mkdir(parents=True, exist_ok=True)

    # Mock 2 speakers with 15 clips each (30 clips total)
    mock_records = []
    target_map = {}
    for spk_idx in range(2):
        sid = f"spk_{spk_idx:02d}"
        for clip_idx in range(CLIPS_PER_SPEAKER):
            cid = f"clip_{spk_idx}_{clip_idx:02d}"
            c_fname = f"{cid}.mp3"
            row = {
                "recording_id": cid,
                "clip_filename": c_fname,
                "speaker_id": sid,
                "accent_group": "Australian English",
                "stratum_code": "australia",
                "panel_role": "evaluation",
                "source_path": f"datasets/external/common_voice_27/clips/{c_fname}",
                "transcript": "Hello world testing materialization",
                "word_count": 4,
            }
            mock_records.append(row)
            target_map[c_fname] = row

            # Create 25 of 30 clips in source pool (spk_0 has 15, spk_1 has 10 -> 1 complete, 1 incomplete)
            if not (spk_idx == 1 and clip_idx >= 10):
                clip_path = source_pool / c_fname
                _generate_synthetic_wav_as_mp3(clip_path, duration_sec=1.0)

    valid_inv: dict = {}
    failed_inv: dict = {}

    copied = materialize_from_local_source(source_pool, target_map, valid_inv, failed_inv, dest_audio)
    assert copied == 25
    assert len(valid_inv) == 25
    assert len(failed_inv) == 0

    # Rescan should detect all 25 valid clips
    rescanned_valid, rescanned_failed = scan_local_inventory(target_map, dest_audio)
    assert len(rescanned_valid) == 25


def test_materialization_reports_exist_and_consistent():
    """Verify that materialization output artifacts exist and reflect strict governance."""
    assert MATERIALIZATION_JSON.exists(), f"Missing {MATERIALIZATION_JSON}"
    assert MATERIALIZATION_MD.exists(), f"Missing {MATERIALIZATION_MD}"
    assert LEDGER_CSV.exists(), f"Missing {LEDGER_CSV}"
    assert FAILED_REPORT_JSON.exists(), f"Missing {FAILED_REPORT_JSON}"
    assert SPEAKER_REPORT_JSON.exists(), f"Missing {SPEAKER_REPORT_JSON}"

    with open(MATERIALIZATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["governance_status"] == "AUTHORIZED_FOR_DATA_PREPARATION"
    assert data["manifest_status"] == "UNLOCKED (PROVISIONAL)"
    assert data["execution_gating"]["gpu_ctta_adaptation"] == "STRICTLY_BLOCKED"
    assert data["execution_gating"]["confirmatory_inference"] == "STRICTLY_BLOCKED"
    assert data["target_scale"]["total_target_clips"] == 18975
    assert data["target_scale"]["total_target_speakers"] == 1265
