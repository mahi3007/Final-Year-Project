"""
tests/research_validity/test_stage6m_cohort2_audio_validation.py

Automated Test Suite for Stage 6M Cohort 2 Full-Corpus Audio Validator
=======================================================================
Standard: ADR-005
Protocol: v1.3.4-stage6m-self-authorization-amendment

Verifies:
1. Fail-closed behavior on missing audio directory.
2. Exact detection of missing clips.
3. Detection of zero-byte audio files.
4. Detection of corrupt / non-decodable audio headers.
5. Detection of extraneous / unmapped MP3 files.
6. Successful end-to-end decodability and 16 kHz resampling verification on valid audio.
7. Proper CLI exit codes (0 on PASS, 1 on FAIL).
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.validate_stage6m_cohort2_audio import (
    validate_single_clip,
    run_audio_validation,
)


def _create_mock_eval_csv(csv_path: Path, clip_ids: list[str]):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "recording_id",
                "speaker_id",
                "speaker_id_prefix",
                "stage5_accent_group",
                "stratum_code",
                "audio_path",
                "transcript",
                "word_count",
                "selection_seed",
                "clip_order_within_speaker",
                "protocol_version",
                "dataset_name",
            ],
        )
        writer.writeheader()
        for idx, cid in enumerate(clip_ids):
            writer.writerow(
                {
                    "recording_id": cid,
                    "speaker_id": f"spk_{idx:04d}",
                    "speaker_id_prefix": f"spk_{idx:04d}"[:24],
                    "stage5_accent_group": "US English",
                    "stratum_code": "us",
                    "audio_path": f"{cid}.mp3",
                    "transcript": "Test clip transcription",
                    "word_count": 3,
                    "selection_seed": 20261020,
                    "clip_order_within_speaker": 1,
                    "protocol_version": "v1.3.4-stage6m-self-authorization-amendment",
                    "dataset_name": "stage6m_cohort2_audio",
                }
            )


def _generate_valid_audio_file(file_path: Path, sr: int = 16000, duration_sec: float = 0.5):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False, dtype=np.float32)
    waveform = 0.5 * np.sin(2 * np.pi * 440 * t)
    # Write using soundfile (wav container with mp3 or wav extension)
    sf.write(str(file_path), waveform, sr)


def test_audio_validator_fails_closed_when_directory_missing(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    _create_mock_eval_csv(csv_p, ["clip_01", "clip_02"])
    audio_dir = tmp_path / "nonexistent_audio_dir"

    success, report = run_audio_validation(
        eval_csv_path=csv_p,
        audio_dir=audio_dir,
        reports_dir=tmp_path / "reports",
    )
    assert not success
    assert report["overall_status"] == "HOLD_AUDIO_DIRECTORY_MISSING"
    assert report["clips_failed"] == 2


def test_audio_validator_fails_on_missing_files(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    _create_mock_eval_csv(csv_p, ["clip_01", "clip_02", "clip_03"])
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Provide only clip_01 and clip_02; omit clip_03
    _generate_valid_audio_file(audio_dir / "clip_01.mp3")
    _generate_valid_audio_file(audio_dir / "clip_02.mp3")

    success, report = run_audio_validation(
        eval_csv_path=csv_p,
        audio_dir=audio_dir,
        reports_dir=tmp_path / "reports",
    )
    assert not success
    assert report["overall_status"] == "FAIL"
    assert report["clips_passed"] == 2
    assert report["clips_failed"] == 1
    assert report["missing_files_count"] == 1
    assert report["failure_summary"]["FAIL_MISSING"] == 1


def test_audio_validator_fails_on_zero_byte_file(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    _create_mock_eval_csv(csv_p, ["clip_01"])
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    zero_file = audio_dir / "clip_01.mp3"
    zero_file.write_bytes(b"")

    success, report = run_audio_validation(
        eval_csv_path=csv_p,
        audio_dir=audio_dir,
        reports_dir=tmp_path / "reports",
    )
    assert not success
    assert report["overall_status"] == "FAIL"
    assert report["failure_summary"]["FAIL_ZERO_BYTE"] == 1


def test_audio_validator_fails_on_corrupt_file_header(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    _create_mock_eval_csv(csv_p, ["clip_01"])
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    corrupt_file = audio_dir / "clip_01.mp3"
    corrupt_file.write_bytes(b"CORRUPTED_GARBAGE_BYTES_NOT_AUDIO")

    success, report = run_audio_validation(
        eval_csv_path=csv_p,
        audio_dir=audio_dir,
        reports_dir=tmp_path / "reports",
    )
    assert not success
    assert report["overall_status"] == "FAIL"
    assert "FAIL_DECODE_HEADER" in report["failure_summary"]


def test_audio_validator_detects_extraneous_files(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    _create_mock_eval_csv(csv_p, ["clip_01"])
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    _generate_valid_audio_file(audio_dir / "clip_01.mp3")
    _generate_valid_audio_file(audio_dir / "unlisted_extra_clip.mp3")

    success, report = run_audio_validation(
        eval_csv_path=csv_p,
        audio_dir=audio_dir,
        reports_dir=tmp_path / "reports",
    )
    assert not success
    assert report["overall_status"] == "FAIL"
    assert report["extraneous_files_count"] == 1
    assert "unlisted_extra_clip.mp3" in report["extraneous_files"]


def test_audio_validator_passes_on_valid_waveforms(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    clip_ids = [f"clip_{i:02d}" for i in range(1, 6)]
    _create_mock_eval_csv(csv_p, clip_ids)
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    for cid in clip_ids:
        _generate_valid_audio_file(audio_dir / f"{cid}.mp3", sr=24000, duration_sec=0.5)

    success, report = run_audio_validation(
        eval_csv_path=csv_p,
        audio_dir=audio_dir,
        reports_dir=tmp_path / "reports",
    )
    assert success
    assert report["overall_status"] == "PASS"
    assert report["clips_tested"] == 5
    assert report["clips_passed"] == 5
    assert report["clips_failed"] == 0
    assert report["extraneous_files_count"] == 0
    assert report["metrics"]["total_duration_sec"] > 0
    assert report["metrics"]["total_resampled_samples"] == 5 * int(16000 * 0.5)

    # Confirm report files were written
    assert (tmp_path / "reports" / "stage6m_cohort2_audio_validation_report.json").exists()
    assert (tmp_path / "reports" / "stage6m_cohort2_audio_validation_report.md").exists()


def test_audio_validator_cli_exit_code(tmp_path):
    csv_p = tmp_path / "mock_eval.csv"
    _create_mock_eval_csv(csv_p, ["clip_01"])
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    _generate_valid_audio_file(audio_dir / "clip_01.mp3")

    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "validate_stage6m_cohort2_audio.py"),
        "--eval-csv",
        str(csv_p),
        "--audio-dir",
        str(audio_dir),
        "--reports-dir",
        str(tmp_path / "reports"),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0
    assert "Verdict: PASS" in proc.stdout
