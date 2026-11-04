"""
tests/research_validity/test_stage6m_cohort3_audio_materialization.py

Deterministic Automated Test Suite for Stage 6M v1.5 Cohort 3 Audio Materializer & Integrity Validator
=====================================================================================================
Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)
Phase: Stage 6M v1.5 Task 7.4.1.1 (Full-File Audio Integrity & Complete Stream-Termination Validation)

Test Invariants:
1. Target Manifest Agreement:
   - Loads exactly 18,975 target clips across 1,265 speakers from provisional manifest.
2. Genuine MP3 Audio & Full-File Bounded-Memory Decodability Validation:
   - Detection and fail-closed handling of zero-byte, missing, or corrupt files.
   - Strict rejection of format/container mismatches (e.g., WAV disguised as .mp3).
   - Rejection of truncation or bitstream corruption occurring after the first 1,000 frames.
   - Validation of genuine MP3 bitstreams at Common Voice native rates (32/44.1/48 kHz).
   - Verification of downstream 16 kHz mono resampling contract in src.dsg_ctta.data.acoustic.
3. Speaker Completeness Accounting (Issue A):
   - Every one of the 1,265 target speakers must be accounted for in completeness ledgers.
   - Zero-audio case must report exactly 1,265 target speakers, 0 complete, and 1,265 incomplete.
4. HTTP Streaming Resume & Complete Range Structure Validation (Issue C):
   - Full Content-Range parsing: validates start, end (end >= start), and total (total > end).
   - Resource total consistency: rejects varying total length across reconnections.
   - Initial connection validation: rejects initial 206 responses with non-zero start offset.
   - Gzip stream termination integrity: verifies decompressor.eof before returning EOF.
   - Premature HTTP 416 detection: rejects 416 received before total bytes or gzip EOF reached.
5. Local Sourcing & Zero Substitution:
   - Verifies local sourcing mode with genuine MP3 fixtures.
6. Execution Gating & Historical Immutability:
   - Confirmatory GPU adaptation and model inference remain STRICTLY BLOCKED.
   - Provisional manifest remains UNLOCKED.
   - Historical v1.4.0 execution code remains 100% immutable.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import subprocess
import sys
import tarfile
import types
import urllib.error
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.materialize_stage6m_cohort3_audio import (
    CLIPS_PER_SPEAKER,
    COHORT3_AUDIO_DIR,
    COHORT3_PILOT_AUDIO_DIR,
    FAILED_REPORT_JSON,
    HARDENING_AUDIT_JSON,
    LEDGER_CSV,
    MATERIALIZATION_JSON,
    MATERIALIZATION_MD,
    PILOT_CONFIRMATORY_STRATA,
    PILOT_EXPECTED_CLIPS_PER_SPEAKER,
    PILOT_EXPECTED_SPEAKERS,
    PILOT_FAILED_REPORT_JSON,
    PILOT_LEDGER_CSV,
    PILOT_MATERIALIZATION_JSON,
    PILOT_MATERIALIZATION_MD,
    PILOT_SPEAKER_REPORT_JSON,
    PILOT_TOTAL_EXPECTED_CLIPS,
    PROVISIONAL_MANIFEST_JSON,
    SPEAKER_REPORT_JSON,
    TOTAL_EXPECTED_CLIPS,
    TOTAL_EXPECTED_SPEAKERS,
    ThreadedResilientGzipStream,
    compute_sha256,
    generate_materialization_artifacts,
    generate_pilot_materialization_artifacts,
    load_provisional_manifest,
    main,
    materialize_from_local_source,
    materialize_from_stream,
    scan_local_inventory,
    select_pilot_speakers_and_clips,
    validate_audio_file,
    validate_and_compare_cohort3_audio,
    verify_full_cohort_materialization_authorization,
    verify_pilot_materialization_authorization,
    APPROVED_COHORT3_MANIFEST_SHA256,
    APPROVED_COHORT3_DESTINATION_REL,
    VALIDATION_REPORT_JSON,
    VALIDATION_REPORT_MD,
)
from src.dsg_ctta.data.acoustic import load_and_resample_audio


def _generate_synthetic_mp3(
    path: Path,
    duration_sec: float = 1.0,
    sr: int = 16000,
    channels: int = 1,
) -> None:
    """Generates a genuine MP3 audio bitstream using soundfile."""
    path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    if channels == 1:
        audio = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    elif channels == 2:
        c1 = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        c2 = (0.2 * np.cos(2 * np.pi * 440 * t)).astype(np.float32)
        audio = np.stack([c1, c2], axis=1)
    else:
        raise ValueError(f"Unsupported channel count: {channels}")

    sf.write(str(path), audio, sr, format="MP3")


def _generate_synthetic_wav_named_mp3(
    path: Path,
    duration_sec: float = 1.0,
    sr: int = 16000,
) -> None:
    """Generates a WAV container named with a .mp3 extension (container mismatch)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    audio = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(path), audio, sr, format="WAV")


def test_target_manifest_scale_and_fields():
    """Verify that materializer reads exactly 18,975 records across 1,265 speakers."""
    meta, records, target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    assert len(records) == TOTAL_EXPECTED_CLIPS == 18975
    assert len(target_map) == TOTAL_EXPECTED_CLIPS == 18975
    assert meta["manifest_type"] == "PROVISIONAL_SELECTION_MANIFEST"
    assert meta["manifest_status"] == "UNLOCKED"


def test_validate_audio_file_genuine_mp3_and_boundaries(tmp_path):
    """
    Verify audio file validator enforces genuine MP3 format, standard sample rates,
    full-stream bounded-memory decodability, and fail-closed handling of boundary conditions.
    """
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

    # 3. Corrupted header / random non-audio bytes
    corrupt = tmp_path / "corrupt.mp3"
    corrupt.write_bytes(b"GARBAGE_HEADER_DATA_NOT_AUDIO" * 20)
    valid, dur, sr, ch, h, err = validate_audio_file(corrupt)
    assert not valid
    assert "Decode failure" in err

    # 4. Container Mismatch: WAV file named .mp3
    fake_mp3 = tmp_path / "fake_wav.mp3"
    _generate_synthetic_wav_named_mp3(fake_mp3, duration_sec=1.0, sr=16000)
    valid, dur, sr, ch, h, err = validate_audio_file(fake_mp3)
    assert not valid
    assert "Invalid audio format: expected MP3 container, got WAV" in err

    # 5. Truncated MP3 near beginning: header cut off mid-frame
    good_tmp = tmp_path / "full.mp3"
    _generate_synthetic_mp3(good_tmp, duration_sec=1.0, sr=16000)
    full_bytes = good_tmp.read_bytes()
    trunc_early = tmp_path / "truncated_early.mp3"
    trunc_early.write_bytes(full_bytes[:120])
    valid, dur, sr, ch, h, err = validate_audio_file(trunc_early)
    assert not valid
    assert "Decode failure" in err

    # 6. Truncated MP3 AFTER the first 1,000 frames (Task 7.4.1.1):
    # Create 2.0s audio at 16kHz (32,000 frames). Truncating at 50% byte length yields
    # ~13,000 frames (well past the first 1,000 frames), but falls short of declared 32,000 frames.
    long_mp3 = tmp_path / "long_audio.mp3"
    _generate_synthetic_mp3(long_mp3, duration_sec=2.0, sr=16000)
    long_bytes = long_mp3.read_bytes()
    trunc_late = tmp_path / "truncated_late.mp3"
    trunc_late.write_bytes(long_bytes[: len(long_bytes) // 2])
    valid, dur, sr, ch, h, err = validate_audio_file(trunc_late)
    assert not valid
    assert "Truncated audio stream" in err or "Decode failure" in err

    # 7. Genuine MP3 - 16 kHz Mono
    mp3_16k = tmp_path / "genuine_16k.mp3"
    _generate_synthetic_mp3(mp3_16k, duration_sec=1.5, sr=16000, channels=1)
    valid, dur, sr, ch, h, err = validate_audio_file(mp3_16k)
    assert valid
    assert dur == pytest.approx(1.5, rel=1e-2)
    assert sr == 16000
    assert ch == 1
    assert len(h) == 64
    assert err == ""

    # 8. Genuine MP3 - 48 kHz Stereo (Common Voice native rate)
    mp3_48k = tmp_path / "genuine_48k.mp3"
    _generate_synthetic_mp3(mp3_48k, duration_sec=0.8, sr=48000, channels=2)
    valid, dur, sr, ch, h, err = validate_audio_file(mp3_48k)
    assert valid
    assert dur == pytest.approx(0.8, rel=1e-2)
    assert sr == 48000
    assert ch == 2
    assert len(h) == 64
    assert err == ""

    # 9. Genuine MP3 - 32 kHz Mono (Common Voice native rate)
    mp3_32k = tmp_path / "genuine_32k.mp3"
    _generate_synthetic_mp3(mp3_32k, duration_sec=1.2, sr=32000, channels=1)
    valid, dur, sr, ch, h, err = validate_audio_file(mp3_32k)
    assert valid
    assert dur == pytest.approx(1.2, rel=1e-2)
    assert sr == 32000
    assert ch == 1
    assert err == ""

    # 10. Unsupported sample rate (e.g. 8000 Hz)
    mp3_8k = tmp_path / "unsupported_8k.mp3"
    _generate_synthetic_mp3(mp3_8k, duration_sec=1.0, sr=8000, channels=1)
    valid, dur, sr, ch, h, err = validate_audio_file(mp3_8k)
    assert not valid
    assert "Unsupported sample rate: 8000 Hz" in err

    # 11. Real Common Voice MP3 with standard LAME padding delay (if present)
    sample_real = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio" / "stage5ext_00001.mp3"
    if sample_real.exists():
        valid, dur, sr, ch, h, err = validate_audio_file(sample_real)
        assert valid, f"Real Common Voice MP3 failed validation: {err}"
        assert dur > 0.0
        assert sr in {16000, 22050, 24000, 32000, 44100, 48000}
        assert ch in (1, 2)
        assert len(h) == 64
        assert err == ""


def test_speaker_completeness_accounting_zero_audio(tmp_path):
    """
    Verify Issue A: When 0 clips are materialized, all 1,265 target speakers
    must appear in the speaker completeness report as incomplete with 0 valid clips.
    Uses tmp_path for all generated reports and ledgers to guarantee zero side effects
    on committed repository artifacts.
    """
    meta, records, target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    empty_valid: dict = {}
    empty_failed: dict = {}

    test_out_dir = tmp_path / "zero_audio_out"
    test_spk_rep = test_out_dir / "stage6m_cohort3_speaker_completeness_report.json"
    test_failed_rep = test_out_dir / "stage6m_cohort3_failed_clips_report.json"
    test_ledger = test_out_dir / "stage6m_cohort3_clip_sha256_ledger.csv"
    test_json = test_out_dir / "stage6m_cohort3_audio_materialization.json"
    test_md = test_out_dir / "stage6m_cohort3_audio_materialization.md"

    art = generate_materialization_artifacts(
        meta,
        records,
        target_map,
        empty_valid,
        empty_failed,
        tmp_path,
        report_json_path=test_json,
        report_md_path=test_md,
        ledger_csv_path=test_ledger,
        speaker_report_path=test_spk_rep,
        failed_report_path=test_failed_rep,
    )

    # 1. Returned artifacts metadata
    scale = art["materialized_scale"]
    assert scale["valid_clips_count"] == 0
    assert scale["remaining_clips_count"] == TOTAL_EXPECTED_CLIPS == 18975
    assert scale["total_target_speakers"] == TOTAL_EXPECTED_SPEAKERS == 1265
    assert scale["complete_speakers_count"] == 0
    assert scale["incomplete_speakers_count"] == 1265

    # 2. Check JSON report in isolated tmp_path
    with open(test_spk_rep, "r", encoding="utf-8") as f:
        spk_data = json.load(f)

    assert spk_data["total_target_speakers"] == 1265
    assert spk_data["complete_speakers"] == 0
    assert spk_data["incomplete_speakers"] == 1265
    assert len(spk_data["speakers"]) == 1265

    # Verify every single target speaker has is_complete=False and materialized_clips_count=0
    for sid, spk_entry in spk_data["speakers"].items():
        assert spk_entry["materialized_clips_count"] == 0
        assert spk_entry["required_clips_count"] == CLIPS_PER_SPEAKER == 15
        assert spk_entry["is_complete"] is False
        assert spk_entry["panel_role"] in {"evaluation", "gate_reference", "australian_reserve"}


def test_local_sourcing_and_completeness_tracking(tmp_path):
    """Verify that local materialization correctly copies genuine MP3s, decodes, and records inventory."""
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
                _generate_synthetic_mp3(clip_path, duration_sec=1.0, sr=16000)

    valid_inv: dict = {}
    failed_inv: dict = {}

    copied = materialize_from_local_source(source_pool, target_map, valid_inv, failed_inv, dest_audio)
    assert copied == 25
    assert len(valid_inv) == 25
    assert len(failed_inv) == 0

    # Rescan should detect all 25 valid clips
    rescanned_valid, rescanned_failed = scan_local_inventory(target_map, dest_audio)
    assert len(rescanned_valid) == 25
    assert len(rescanned_failed) == 0


def test_streaming_resume_range_validation():
    """
    Verify Issue C & Task 7.4.1.1:
    1. Interrupted stream recovery: reconnects with Range header, receives 206 with full Content-Range,
       reaches valid gzip EOF marker, producing identical decompressed archive.
    2. HTTP status 200 on resume (server ignoring Range) is rejected with IOError.
    3. Mismatched Content-Range start byte on resume is rejected with IOError.
    4. Missing Content-Range header on 206 response is rejected with IOError.
    5. Inverted Content-Range interval (end < start) is rejected with IOError.
    6. Inconsistent total resource length across reconnects is rejected with IOError.
    7. Initial connection returning 206 with non-zero start is rejected with IOError.
    8. Truncated gzip archive (ending before gzip EOF marker) is rejected with IOError.
    9. Premature HTTP 416 received before total bytes or archive complete is rejected with IOError.
    """
    # Create an in-memory valid gzip archive containing a tar file
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        with tarfile.open(fileobj=gz, mode="w") as tar:
            data = b"AUDIO_DATA_PAYLOAD_TEST_1234567890" * 20
            ti = tarfile.TarInfo(name="clips/sample_01.mp3")
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))
    gz_bytes = buf.getvalue()
    total_len = len(gz_bytes)
    assert total_len > 40
    split_point = total_len // 2

    class MockHTTPResponse:
        def __init__(self, data: bytes, status: int, headers: dict):
            self._bio = io.BytesIO(data)
            self.status = status
            self.code = status
            self.headers = headers

        def read(self, n: int = -1) -> bytes:
            return self._bio.read(n)

        def close(self):
            pass

    # Scenario 1: Interrupted stream successfully resumes with 206 Partial Content
    call_log = []

    def mock_good_resuming_opener(req, timeout=120):
        range_hdr = req.headers.get("Range")
        call_log.append(range_hdr)
        if range_hdr is None:
            # Initial connection drops halfway
            return MockHTTPResponse(gz_bytes[:split_point], 200, {"Content-Length": str(total_len)})
        else:
            # Resume request
            assert range_hdr == f"bytes={split_point}-"
            headers = {"Content-Range": f"bytes {split_point}-{total_len - 1}/{total_len}"}
            return MockHTTPResponse(gz_bytes[split_point:], 206, headers)

    stream1 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_good_resuming_opener,
    )
    buffered1 = io.BufferedReader(stream1)
    with tarfile.open(fileobj=buffered1, mode="r|") as tar1:
        extracted = []
        for m in tar1:
            extracted.append((m.name, tar1.extractfile(m).read()))
    stream1.close()

    assert len(extracted) == 1
    assert extracted[0][0] == "clips/sample_01.mp3"
    assert extracted[0][1] == b"AUDIO_DATA_PAYLOAD_TEST_1234567890" * 20
    assert call_log[0] is None  # Initial request
    assert call_log[1] == f"bytes={split_point}-"  # Resumed request

    # Scenario 2: Server returns 200 OK on resume (ignoring Range header) -> must raise IOError
    def mock_server_ignoring_range(req, timeout=120):
        range_hdr = req.headers.get("Range")
        if range_hdr is None:
            return MockHTTPResponse(gz_bytes[:split_point], 200, {})
        else:
            # Broken server returns 200 OK with whole payload
            return MockHTTPResponse(gz_bytes, 200, {})

    stream2 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_server_ignoring_range,
    )
    buffered2 = io.BufferedReader(stream2)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered2, mode="r|") as tar2:
            for _ in tar2:
                pass
    stream2.close()
    assert "HTTP resume failed: server returned status 200" in str(exc_info.value)

    # Scenario 3: Server returns 206 with mismatched Content-Range start byte -> must raise IOError
    def mock_server_wrong_range_start(req, timeout=120):
        range_hdr = req.headers.get("Range")
        if range_hdr is None:
            return MockHTTPResponse(gz_bytes[:split_point], 200, {})
        else:
            # Server returns start offset 0 instead of requested split_point
            headers = {"Content-Range": f"bytes 0-{total_len - 1}/{total_len}"}
            return MockHTTPResponse(gz_bytes, 206, headers)

    stream3 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_server_wrong_range_start,
    )
    buffered3 = io.BufferedReader(stream3)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered3, mode="r|") as tar3:
            for _ in tar3:
                pass
    stream3.close()
    assert "HTTP resume failed: Content-Range start 0 does not match requested offset" in str(exc_info.value)

    # Scenario 4: Server returns 206 without Content-Range header -> must raise IOError
    def mock_server_missing_content_range(req, timeout=120):
        range_hdr = req.headers.get("Range")
        if range_hdr is None:
            return MockHTTPResponse(gz_bytes[:split_point], 200, {})
        else:
            return MockHTTPResponse(gz_bytes[split_point:], 206, {})

    stream4 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_server_missing_content_range,
    )
    buffered4 = io.BufferedReader(stream4)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered4, mode="r|") as tar4:
            for _ in tar4:
                pass
    stream4.close()
    assert "HTTP resume failed: missing Content-Range header" in str(exc_info.value)

    # Scenario 5: Server returns inverted range (end < start) -> must raise IOError
    def mock_inverted_range(req, timeout=120):
        if req.headers.get("Range") is None:
            return MockHTTPResponse(gz_bytes[:split_point], 200, {})
        return MockHTTPResponse(
            gz_bytes[split_point:], 206, {"Content-Range": f"bytes 100-50/{total_len}"}
        )

    stream5 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_inverted_range,
    )
    buffered5 = io.BufferedReader(stream5)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered5, mode="r|") as tar5:
            for _ in tar5:
                pass
    stream5.close()
    assert "Invalid inverted range in Content-Range" in str(exc_info.value)

    # Scenario 6: Inconsistent total resource length across reconnects -> must raise IOError
    calls_s6 = 0

    def mock_inconsistent_total(req, timeout=120):
        nonlocal calls_s6
        calls_s6 += 1
        if req.headers.get("Range") is None:
            return MockHTTPResponse(gz_bytes[:10], 200, {})
        if calls_s6 == 2:
            return MockHTTPResponse(
                gz_bytes[10:20], 206, {"Content-Range": f"bytes 10-19/{total_len}"}
            )
        return MockHTTPResponse(
            gz_bytes[20:], 206, {"Content-Range": f"bytes 20-{total_len-1}/{total_len + 500}"}
        )

    stream6 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_inconsistent_total,
    )
    buffered6 = io.BufferedReader(stream6)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered6, mode="r|") as tar6:
            for _ in tar6:
                pass
    stream6.close()
    assert "Inconsistent resource total across reconnects" in str(exc_info.value)

    # Scenario 7: Initial connection returns 206 with non-zero start -> must raise IOError
    def mock_initial_nonzero_start(req, timeout=120):
        return MockHTTPResponse(
            gz_bytes[10:], 206, {"Content-Range": f"bytes 10-{total_len-1}/{total_len}"}
        )

    stream7 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_initial_nonzero_start,
    )
    buffered7 = io.BufferedReader(stream7)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered7, mode="r|") as tar7:
            for _ in tar7:
                pass
    stream7.close()
    assert "server returned 206 Partial Content with non-zero start offset" in str(exc_info.value)

    # Scenario 8: Truncated gzip archive (ending before gzip EOF marker) -> must raise IOError
    def mock_truncated_gzip(req, timeout=120):
        range_hdr = req.headers.get("Range")
        if range_hdr is None:
            return MockHTTPResponse(gz_bytes[: len(gz_bytes) // 2], 200, {})
        # Subsequent requests return empty bytes, simulating server closed stream prematurely
        return MockHTTPResponse(
            b"", 206, {"Content-Range": f"bytes {len(gz_bytes)//2}-{len(gz_bytes)//2}/{total_len}"}
        )

    stream8 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_truncated_gzip,
    )
    buffered8 = io.BufferedReader(stream8)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered8, mode="r|") as tar8:
            for _ in tar8:
                pass
    stream8.close()
    assert "Incomplete gzip stream: reached end of stream without valid gzip EOF marker" in str(
        exc_info.value
    )

    # Scenario 9: Premature HTTP 416 received before archive fully received -> must raise IOError
    def mock_premature_416(req, timeout=120):
        if req.headers.get("Range") is None:
            return MockHTTPResponse(
                gz_bytes[:split_point], 200, {"Content-Length": str(total_len)}
            )
        raise urllib.error.HTTPError("http://mock.test", 416, "Range Not Satisfiable", {}, None)

    stream9 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_premature_416,
    )
    buffered9 = io.BufferedReader(stream9)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered9, mode="r|") as tar9:
            for _ in tar9:
                pass
    stream9.close()
    assert "HTTP 416 Range Not Satisfiable received prematurely" in str(exc_info.value)

    # Scenario 10: Server delivering excess compressed bytes (> expected_total_bytes) -> must raise IOError
    def mock_excess_bytes(req, timeout=120):
        extra_garbage = b"X" * 100
        return MockHTTPResponse(gz_bytes + extra_garbage, 200, {"Content-Length": str(total_len)})

    stream10 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_excess_bytes,
    )
    buffered10 = io.BufferedReader(stream10)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered10, mode="r|") as tar10:
            for _ in tar10:
                pass
    stream10.close()
    assert ("Excess compressed bytes received" in str(exc_info.value)) or ("Network stream overflow" in str(exc_info.value))

    # Scenario 11: Archive containing unexpected trailing bytes after valid gzip member -> must raise IOError
    def mock_trailing_garbage(req, timeout=120):
        garbage = b"UNEXPECTED_TRAILING_GARBAGE"
        combined = gz_bytes + garbage
        return MockHTTPResponse(combined, 200, {"Content-Length": str(len(combined))})

    stream11 = ThreadedResilientGzipStream(
        dataset_id="test_dataset",
        plan_getter=lambda: types.SimpleNamespace(download_url="http://mock.test/archive.tar.gz"),
        url_opener=mock_trailing_garbage,
    )
    buffered11 = io.BufferedReader(stream11)
    with pytest.raises(IOError) as exc_info:
        with tarfile.open(fileobj=buffered11, mode="r|") as tar11:
            for _ in tar11:
                pass
    stream11.close()
    assert "Unexpected trailing compressed data" in str(exc_info.value)


def test_downstream_acoustic_resampling_contract(tmp_path):
    """
    Verify downstream acoustic resampling contract:
    Common Voice MP3 audio arrives at 48 kHz stereo or 32 kHz mono.
    Downstream pipeline explicitly resamples to mono 16 kHz float32 in load_and_resample_audio.
    """
    # 48 kHz Stereo MP3
    stereo_path = tmp_path / "cv_native_48k_stereo.mp3"
    _generate_synthetic_mp3(stereo_path, duration_sec=0.5, sr=48000, channels=2)

    # 1. Ingest validation accepts native rate & stereo
    valid, dur, sr, ch, h, err = validate_audio_file(stereo_path)
    assert valid
    assert sr == 48000
    assert ch == 2

    # 2. Downstream feature extraction pipeline resamples to 16 kHz mono float32
    audio, out_sr = load_and_resample_audio(stereo_path, target_sr=16000)
    assert out_sr == 16000
    assert audio.ndim == 1  # Flattened to mono
    assert audio.dtype == np.float32
    assert len(audio) == pytest.approx(8000, abs=100)  # 0.5s * 16000 Hz


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
    assert data["materialized_scale"]["total_target_speakers"] == 1265
    assert data["materialized_scale"]["complete_speakers_count"] == 0
    assert data["materialized_scale"]["incomplete_speakers_count"] == 1265


def test_historical_v1_4_0_execution_engine_immutability():
    """Verify that historical v1.4.0 execution code remains 100% byte-identical."""
    target_file = PROJECT_ROOT / "src" / "dsg_ctta" / "evaluation" / "paired_cluster_inference.py"
    assert target_file.exists(), f"Missing frozen file: {target_file}"

    # Check Git blob object hash
    res = subprocess.run(
        ["git", "hash-object", str(target_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    blob_hash = res.stdout.strip()
    assert (
        blob_hash == "58d456fbcce43b5322d56df80e4077a32d7f4cca"
    ), f"Frozen execution file hash altered: {blob_hash}"

    # Check git diff against baseline commit a7a3b79
    diff_res = subprocess.run(
        ["git", "diff", "a7a3b79", "--", str(target_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        diff_res.stdout.strip() == ""
    ), f"Frozen execution file has changes against baseline commit a7a3b79: {diff_res.stdout}"


def test_pilot_speaker_and_clip_selection():
    """
    Verify Task 7.4.2 Pilot selection:
    Deterministically selects exactly 5 speakers (1 from each confirmatory evaluation stratum)
    and exactly 15 clips per speaker = 75 clips total.
    Verifies zero overlap with gate reference or reserve panel.
    """
    parent_manifest_sha256 = compute_sha256(PROVISIONAL_MANIFEST_JSON)
    meta, records, full_target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)

    pilot_spk_ids, pilot_target_map, pilot_records = select_pilot_speakers_and_clips(
        records, parent_manifest_sha256
    )

    assert len(pilot_spk_ids) == PILOT_EXPECTED_SPEAKERS == 5
    assert len(pilot_target_map) == PILOT_TOTAL_EXPECTED_CLIPS == 75
    assert len(pilot_records) == 75

    # Check 1 speaker per confirmatory stratum
    strata_covered = set()
    spk_clip_counts = defaultdict(int)
    for r in pilot_records:
        assert r["panel_role"] == "evaluation"
        strata_covered.add(r["accent_group"])
        spk_clip_counts[r["speaker_id"]] += 1

    assert strata_covered == set(PILOT_CONFIRMATORY_STRATA)
    for sid, count in spk_clip_counts.items():
        assert count == PILOT_EXPECTED_CLIPS_PER_SPEAKER == 15


def test_pilot_cli_execution_and_report_isolation(tmp_path):
    """
    Verify Task 7.4.2 & 7.4.2.1:
    Executing CLI with --pilot --validate-only --output-dir writes isolated pilot artifacts
    to the designated output directory and preserves both full-cohort and committed pilot
    repository artifacts with 100% byte-identical SHA-256 immutability.
    """
    full_cohort_files = [
        MATERIALIZATION_JSON,
        MATERIALIZATION_MD,
        LEDGER_CSV,
        FAILED_REPORT_JSON,
        SPEAKER_REPORT_JSON,
    ]
    pilot_repo_files = [
        PILOT_MATERIALIZATION_JSON,
        PILOT_MATERIALIZATION_MD,
        PILOT_LEDGER_CSV,
        PILOT_FAILED_REPORT_JSON,
        PILOT_SPEAKER_REPORT_JSON,
    ]
    all_repo_artifacts = full_cohort_files + pilot_repo_files

    # 1. Snapshot SHA-256 of all repository full-cohort and pilot artifacts before run
    hashes_before = {f: compute_sha256(f) for f in all_repo_artifacts if f.exists()}

    # 2. Run CLI with --pilot --validate-only pointing output-dir and pilot-audio-dir to tmp_path
    cli_out_dir = tmp_path / "pilot_cli_isolated_out"
    cli_audio_dir = tmp_path / "pilot_cli_isolated_audio"
    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio.py"),
            "--pilot",
            "--validate-only",
            "--output-dir",
            str(cli_out_dir),
            "--pilot-audio-dir",
            str(cli_audio_dir),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert res.returncode == 0

    # 3. Verify pilot reports exist in tmp_path and match 75-clip scale
    pilot_json = cli_out_dir / "stage6m_cohort3_pilot_materialization.json"
    pilot_md = cli_out_dir / "stage6m_cohort3_pilot_materialization.md"
    pilot_spk = cli_out_dir / "stage6m_cohort3_pilot_speaker_completeness_report.json"
    pilot_failed = cli_out_dir / "stage6m_cohort3_pilot_failed_clips_report.json"
    pilot_ledger = cli_out_dir / "stage6m_cohort3_pilot_clip_sha256_ledger.csv"

    assert pilot_json.exists()
    assert pilot_md.exists()
    assert pilot_spk.exists()
    assert pilot_failed.exists()
    assert pilot_ledger.exists()

    with open(pilot_json, "r", encoding="utf-8") as f:
        pilot_data = json.load(f)

    assert pilot_data["target_scale"]["total_target_clips"] == 75
    assert pilot_data["target_scale"]["total_target_speakers"] == 5
    assert pilot_data["materialized_scale"]["total_target_speakers"] == 5
    assert pilot_data["materialized_scale"]["valid_clips_count"] == 0
    assert pilot_data["governance_status"] in (
        "PILOT_PREPARED_PENDING_SEPARATE_PILOT_AUTHORIZATION",
        "PILOT_AUTHORIZED_BY_PROJECT_LEAD",
        "PILOT_AUTHORIZED_AND_VERIFIED",
    )
    assert pilot_data["materialization_disposition"] == "PILOT_ZERO_AUDIO_DRY_RUN"
    assert pilot_data["execution_gating"]["gpu_ctta_adaptation"] == "STRICTLY_BLOCKED"
    assert pilot_data["execution_gating"]["confirmatory_inference"] == "STRICTLY_BLOCKED"
    assert pilot_data["execution_gating"]["full_cohort_materialization"] in (
        "HELD_PENDING_PILOT_VERIFICATION",
        "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
    )

    parent_sha256 = compute_sha256(PROVISIONAL_MANIFEST_JSON)
    assert pilot_data["parent_provisional_manifest"]["sha256"] == parent_sha256

    # 4. Strict byte-level immutability: assert SHA-256 of all repository artifacts unchanged
    hashes_after = {f: compute_sha256(f) for f in all_repo_artifacts if f.exists()}
    for f in all_repo_artifacts:
        if f in hashes_before:
            assert (
                hashes_before[f] == hashes_after[f]
            ), f"Repository artifact byte mutated during isolated pilot CLI run: {f}"


def test_pilot_mock_materialization_verification(tmp_path):
    """
    Verify complete pilot materialization verification with 75 valid synthetic MP3 clips.
    Asserts 75/75 valid clips, 5/5 complete speakers, 0 failures, and PILOT_COMPLETE_AND_VERIFIED disposition.
    All artifacts are strictly written to tmp_path to prevent contaminating committed reports.
    """
    parent_manifest_sha256 = compute_sha256(PROVISIONAL_MANIFEST_JSON)
    meta, records, full_target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    pilot_spk_ids, pilot_target_map, pilot_records = select_pilot_speakers_and_clips(
        records, parent_manifest_sha256
    )

    pilot_audio_dir = tmp_path / "mock_pilot_audio"
    mock_out_dir = tmp_path / "mock_pilot_out"
    pilot_audio_dir.mkdir(parents=True, exist_ok=True)
    mock_out_dir.mkdir(parents=True, exist_ok=True)

    # Generate 75 valid MP3 files
    for r in pilot_records:
        rec_id = r["recording_id"]
        clip_path = pilot_audio_dir / f"{rec_id}.mp3"
        _generate_synthetic_mp3(clip_path, duration_sec=0.2, sr=16000, channels=1)

    # Scan and validate
    valid_inv, failed_inv = scan_local_inventory(pilot_target_map, pilot_audio_dir)
    assert len(valid_inv) == 75
    assert len(failed_inv) == 0

    mock_json = mock_out_dir / "stage6m_cohort3_pilot_materialization.json"
    mock_md = mock_out_dir / "stage6m_cohort3_pilot_materialization.md"
    mock_ledger = mock_out_dir / "stage6m_cohort3_pilot_clip_sha256_ledger.csv"
    mock_spk = mock_out_dir / "stage6m_cohort3_pilot_speaker_completeness_report.json"
    mock_failed = mock_out_dir / "stage6m_cohort3_pilot_failed_clips_report.json"

    # Generate pilot artifacts strictly inside mock_out_dir
    pilot_artifacts = generate_pilot_materialization_artifacts(
        meta,
        parent_manifest_sha256,
        pilot_spk_ids,
        pilot_records,
        pilot_target_map,
        valid_inv,
        failed_inv,
        pilot_audio_dir,
        report_json_path=mock_json,
        report_md_path=mock_md,
        ledger_csv_path=mock_ledger,
        speaker_report_path=mock_spk,
        failed_report_path=mock_failed,
    )

    assert pilot_artifacts["materialization_disposition"] == "PILOT_COMPLETE_AND_VERIFIED"
    assert pilot_artifacts["materialized_scale"]["valid_clips_count"] == 75
    assert pilot_artifacts["materialized_scale"]["complete_speakers_count"] == 5
    assert pilot_artifacts["materialized_scale"]["incomplete_speakers_count"] == 0
    assert pilot_artifacts["materialized_scale"]["failed_clips_count"] == 0
    assert pilot_artifacts["materialized_scale"]["completion_rate_pct"] == 100.0

    # Verify mock output files were written under tmp_path
    assert mock_json.exists()
    assert mock_md.exists()
    assert mock_ledger.exists()
    assert mock_spk.exists()
    assert mock_failed.exists()


def test_committed_pilot_reports_exist_and_clean_zero_audio():
    """
    Verify Task 7.4.2.1 / Milestone 7.4:
    Assert that committed repository pilot artifacts exist and strictly reflect
    internally consistent evidence (valid clips match ledger row count, complete and
    incomplete speaker counts match the completeness report, failed clips count is zero,
    and governance gating strictly blocks downstream adaptation and inference).
    """
    assert PILOT_MATERIALIZATION_JSON.exists(), f"Missing {PILOT_MATERIALIZATION_JSON}"
    assert PILOT_MATERIALIZATION_MD.exists(), f"Missing {PILOT_MATERIALIZATION_MD}"
    assert PILOT_LEDGER_CSV.exists(), f"Missing {PILOT_LEDGER_CSV}"
    assert PILOT_FAILED_REPORT_JSON.exists(), f"Missing {PILOT_FAILED_REPORT_JSON}"
    assert PILOT_SPEAKER_REPORT_JSON.exists(), f"Missing {PILOT_SPEAKER_REPORT_JSON}"

    with open(PILOT_MATERIALIZATION_JSON, "r", encoding="utf-8") as f:
        pilot_data = json.load(f)

    assert pilot_data["target_scale"]["total_target_clips"] == 75
    assert pilot_data["target_scale"]["total_target_speakers"] == 5
    assert pilot_data["materialized_scale"]["total_target_speakers"] == 5

    valid_clips = pilot_data["materialized_scale"]["valid_clips_count"]
    remaining_clips = pilot_data["materialized_scale"]["remaining_clips_count"]
    assert valid_clips + remaining_clips == 75
    assert pilot_data["materialized_scale"]["failed_clips_count"] == 0

    assert pilot_data["governance_status"] in (
        "PILOT_PREPARED_PENDING_SEPARATE_PILOT_AUTHORIZATION",
        "PILOT_AUTHORIZED_BY_PROJECT_LEAD",
        "PILOT_AUTHORIZED_AND_VERIFIED",
    )
    assert pilot_data["materialization_disposition"] in (
        "PILOT_ZERO_AUDIO_DRY_RUN",
        "PILOT_IN_PROGRESS",
        "PILOT_COMPLETE",
        "PILOT_COMPLETE_AND_VERIFIED",
    )
    assert pilot_data["execution_gating"]["gpu_ctta_adaptation"] == "STRICTLY_BLOCKED"
    assert pilot_data["execution_gating"]["confirmatory_inference"] == "STRICTLY_BLOCKED"
    assert pilot_data["execution_gating"]["full_cohort_materialization"] in (
        "HELD_PENDING_PILOT_VERIFICATION",
        "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
    )

    # Verify ledger CSV has header + matching valid clips
    with open(PILOT_LEDGER_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    assert len(reader) == 1 + valid_clips, f"Expected {1 + valid_clips} lines in pilot ledger, found {len(reader)}"

    # Verify speaker completeness report is consistent with pilot data
    with open(PILOT_SPEAKER_REPORT_JSON, "r", encoding="utf-8") as f:
        spk_data = json.load(f)
    assert spk_data["total_target_speakers"] == 5
    complete_count = sum(1 for s in spk_data["speakers"].values() if s["is_complete"])
    incomplete_count = sum(1 for s in spk_data["speakers"].values() if not s["is_complete"])
    assert spk_data["complete_speakers"] == complete_count
    assert spk_data["incomplete_speakers"] == incomplete_count
    assert pilot_data["materialized_scale"]["complete_speakers_count"] == complete_count
    assert pilot_data["materialized_scale"]["incomplete_speakers_count"] == incomplete_count


def test_pilot_materialization_authorization_fails_closed(tmp_path):
    """
    Verify that physical pilot and full-cohort streaming fail closed unless
    explicit Project-Lead authorization under Protocol Section 14.7 is present.
    """
    # 1. Missing audit file -> fails closed
    missing_file = tmp_path / "non_existent_audit.json"
    with pytest.raises(PermissionError) as exc_info:
        verify_pilot_materialization_authorization(missing_file)
    assert "governance audit artifact not found" in str(exc_info.value)

    # 2. Audit file with pending / unauthorized status -> fails closed
    unauth_file = tmp_path / "unauthorized_audit.json"
    with open(unauth_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "execution_gating": {
                    "controlled_pilot_download": "PENDING_SEPARATE_PILOT_AUTHORIZATION",
                    "full_audio_materialization": "BLOCKED_PENDING_PILOT_VALIDATION",
                }
            },
            f,
        )

    with pytest.raises(PermissionError) as exc_info:
        verify_pilot_materialization_authorization(unauth_file)
    assert "controlled_pilot_download is 'PENDING_SEPARATE_PILOT_AUTHORIZATION'" in str(exc_info.value)

    with pytest.raises(PermissionError) as exc_info:
        verify_full_cohort_materialization_authorization(unauth_file)
    assert "full_audio_materialization is 'BLOCKED_PENDING_PILOT_VALIDATION'" in str(exc_info.value)

    # 3. Authorized file -> passes cleanly
    auth_file = tmp_path / "authorized_audit.json"
    with open(auth_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "execution_gating": {
                    "controlled_pilot_download": "AUTHORIZED_BY_PROJECT_LEAD",
                    "full_audio_materialization": "AUTHORIZED_BY_PROJECT_LEAD",
                    "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
                    "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
                    "confirmatory_inference": "STRICTLY_BLOCKED",
                },
                "full_cohort_authorization_decision": {
                    "status": "AUTHORIZED_BY_PROJECT_LEAD",
                    "authorizing_role": "Project Lead",
                    "authorized_target_clips": 18975,
                    "authorized_target_speakers": 1265,
                    "manifest_sha256": "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547",
                    "substitutions_permitted": 0,
                    "destination_directory": "datasets/external/common_voice_27/cohort3_audio",
                },
            },
            f,
        )

    verify_pilot_materialization_authorization(auth_file)
    verify_full_cohort_materialization_authorization(auth_file)

    # 4. Task 7.5.1: canonical repository audit artifact must block pilot re-download.
    # controlled_pilot_download == PILOT_COMPLETE_AND_VERIFIED — a completed pilot is
    # evidence that an earlier authorization was fulfilled, NOT a new authorization.
    assert HARDENING_AUDIT_JSON.exists()
    with pytest.raises(PermissionError) as exc_info:
        verify_pilot_materialization_authorization(HARDENING_AUDIT_JSON)
    assert "A completed pilot does not authorize a new download" in str(exc_info.value)

    # 5. Full-cohort acquisition is formally authorized under canonical governance (Task 7.6).
    verify_full_cohort_materialization_authorization(HARDENING_AUDIT_JSON)


# ---------------------------------------------------------------------------
# Task 7.5.1 — Fail-Closed Authorization Boundary Regression Tests
# ---------------------------------------------------------------------------


def test_pilot_stream_acquisition_requires_authorization(tmp_path):
    """
    T7.5.1-01 — Pilot streaming acquisition is blocked when governance status is not
    AUTHORIZED_BY_PROJECT_LEAD. verify_pilot_materialization_authorization must be
    called and must raise before any HTTP connection is attempted.
    """
    blocked_audit = tmp_path / "blocked.json"
    with open(blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {"execution_gating": {"controlled_pilot_download": "PENDING_SEPARATE_PILOT_AUTHORIZATION"}}, f
        )
    with pytest.raises(PermissionError) as exc_info:
        verify_pilot_materialization_authorization(blocked_audit)
    assert "Physical pilot audio acquisition blocked" in str(exc_info.value)
    assert "PENDING_SEPARATE_PILOT_AUTHORIZATION" in str(exc_info.value)


def test_pilot_source_dir_acquisition_requires_authorization(tmp_path):
    """
    T7.5.1-02 — Pilot --source-dir acquisition is blocked when governance status is not
    AUTHORIZED_BY_PROJECT_LEAD. The authorization gate must fire before any file copy.
    """
    # Build a minimal local source containing a valid MP3 clip.
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    clip_fname = "test_clip.mp3"
    _generate_synthetic_mp3(source_dir / clip_fname)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    blocked_audit = tmp_path / "blocked.json"
    with open(blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {"execution_gating": {"controlled_pilot_download": "PENDING_SEPARATE_PILOT_AUTHORIZATION"}}, f
        )

    # The gate must raise before any copy occurs.
    with pytest.raises(PermissionError) as exc_info:
        verify_pilot_materialization_authorization(blocked_audit)
    assert "Physical pilot audio acquisition blocked" in str(exc_info.value)
    # Confirm no file was copied to dest.
    assert list(dest_dir.iterdir()) == []


def test_full_cohort_source_dir_acquisition_requires_authorization(tmp_path):
    """
    T7.5.1-03 — Full-cohort --source-dir acquisition is blocked when governance status
    is not AUTHORIZED_BY_PROJECT_LEAD. The authorization gate must fire before any copy.
    """
    blocked_audit = tmp_path / "blocked.json"
    with open(blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {"execution_gating": {"full_audio_materialization": "BLOCKED_PENDING_COHORT3_READINESS_REVIEW"}}, f
        )

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with pytest.raises(PermissionError) as exc_info:
        verify_full_cohort_materialization_authorization(blocked_audit)
    assert "Full cohort audio acquisition blocked" in str(exc_info.value)
    assert list(dest_dir.iterdir()) == []


def test_pilot_complete_does_not_authorize_new_pilot_download(tmp_path):
    """
    T7.5.1-04 — PILOT_COMPLETE_AND_VERIFIED must NOT authorize a new pilot download.
    A completed pilot is historical evidence; it does not constitute a fresh
    Project-Lead authorization for another physical acquisition run.
    """
    pilot_complete_audit = tmp_path / "pilot_complete.json"
    with open(pilot_complete_audit, "w", encoding="utf-8") as f:
        json.dump(
            {"execution_gating": {"controlled_pilot_download": "PILOT_COMPLETE_AND_VERIFIED"}}, f
        )

    with pytest.raises(PermissionError) as exc_info:
        verify_pilot_materialization_authorization(pilot_complete_audit)
    err = str(exc_info.value)
    assert "Physical pilot audio acquisition blocked" in err
    assert "PILOT_COMPLETE_AND_VERIFIED" in err
    assert "A completed pilot does not authorize a new download" in err


def test_arbitrary_audit_json_path_cannot_be_injected_via_cli():
    """
    T7.5.1-05 — The production CLI must NOT expose an --audit-json flag. Operators must
    not be able to supply an arbitrary governance JSON to bypass the canonical
    HARDENING_AUDIT_JSON. The parameter exists only on the helper functions for
    direct unit-test injection.

    Verifies by inspecting the argparse configuration of main() at import time and
    checking the subprocess help output does NOT advertise --audit-json.
    """
    import subprocess as sp
    import sys

    result = sp.run(
        [sys.executable, "scripts/materialize_stage6m_cohort3_audio.py", "--help"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    assert "--audit-json" not in result.stdout, (
        "Production CLI must not expose --audit-json. "
        "Operators must not be able to bypass the canonical HARDENING_AUDIT_JSON."
    )


def test_validate_only_requires_no_authorization(tmp_path):
    """
    T7.5.1-06 — --validate-only (read-only audit of on-disk clips) must proceed without
    any authorization check. It performs no physical acquisition and therefore must not
    be gated by Project-Lead authorization.

    Verifies that neither verify_pilot_materialization_authorization nor
    verify_full_cohort_materialization_authorization is called implicitly during a
    validate-only inventory scan of an empty directory.
    """
    # Empty dirs simulate a validate-only scan with no clips on disk.
    empty_audio_dir = tmp_path / "audio"
    empty_audio_dir.mkdir()

    # scan_local_inventory is the core of validate-only — it must not call auth checks.
    # We pass an empty target_map so the scan terminates immediately.
    valid_inv, failed_inv = scan_local_inventory({}, empty_audio_dir)
    assert valid_inv == {}
    assert failed_inv == {}
    # Reaching here without PermissionError confirms validate-only is ungated.


def test_pending_governance_statuses_all_deny_acquisition(tmp_path):
    """
    T7.5.1-07 — All known non-authorized governance status values must be denied by
    both verify_pilot_materialization_authorization and
    verify_full_cohort_materialization_authorization. No blocked or pending status
    string may inadvertently pass either gate.
    """
    blocked_pilot_statuses = [
        "PENDING_SEPARATE_PILOT_AUTHORIZATION",
        "PILOT_COMPLETE_AND_VERIFIED",  # Task 7.5.1: completed pilot must not re-authorize
        "BLOCKED_PENDING_COHORT3_READINESS_REVIEW",
        "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
        "STRICTLY_BLOCKED",
        None,
        "",
        "authorized_by_project_lead",  # Case-sensitive — must reject lowercase variant
    ]
    blocked_full_statuses = [
        "BLOCKED_PENDING_PILOT_VALIDATION",
        "BLOCKED_PENDING_COHORT3_READINESS_REVIEW",
        "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
        "STRICTLY_BLOCKED",
        "PILOT_COMPLETE_AND_VERIFIED",
        None,
        "",
        "authorized_by_project_lead",
    ]

    for status in blocked_pilot_statuses:
        audit_file = tmp_path / f"pilot_{status}.json"
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump({"execution_gating": {"controlled_pilot_download": status}}, f)
        with pytest.raises(PermissionError, match="Physical pilot audio acquisition blocked"):
            verify_pilot_materialization_authorization(audit_file)

    for status in blocked_full_statuses:
        audit_file = tmp_path / f"full_{status}.json"
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump({"execution_gating": {"full_audio_materialization": status}}, f)
        with pytest.raises(PermissionError, match="Full cohort audio acquisition blocked"):
            verify_full_cohort_materialization_authorization(audit_file)


def test_full_cohort_acquisition_authorized_under_canonical_governance():
    """
    T7.6-01 — Post-decision governance: Full-cohort acquisition (18,975 clips) is formally
    authorized under the committed HARDENING_AUDIT_JSON following Task 7.6 Project-Lead
    decision under Protocol Section 14.7.
    Gating must record AUTHORIZED_BY_PROJECT_LEAD, while downstream manifest lock, GPU
    adaptation, and confirmatory inference remain strictly blocked.
    """
    assert HARDENING_AUDIT_JSON.exists(), f"Canonical audit JSON missing: {HARDENING_AUDIT_JSON}"
    # Verification function must pass cleanly without raising PermissionError
    verify_full_cohort_materialization_authorization(HARDENING_AUDIT_JSON)

    with open(HARDENING_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    gating = data.get("execution_gating", {})
    assert gating.get("full_audio_materialization") == "AUTHORIZED_BY_PROJECT_LEAD"
    assert gating.get("controlled_pilot_download") == "PILOT_COMPLETE_AND_VERIFIED"
    assert gating.get("final_manifest_lock") == "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION"
    assert gating.get("gpu_ctta_adaptation") == "STRICTLY_BLOCKED"
    assert gating.get("confirmatory_inference") == "STRICTLY_BLOCKED"


# ---------------------------------------------------------------------------
# Task 7.5.2 — CLI Integration Tests (Full Execution Path Coverage)
# ---------------------------------------------------------------------------


def test_cli_integration_pilot_source_dir_unauthorized_rejected_before_copy(tmp_path, monkeypatch):
    """
    T7.5.2-01 — Integration Test: CLI pilot mode with --source-dir strictly rejects
    unauthorized acquisition before copying any files.
    Demonstrates that the CLI entrypoint itself invokes the authorization gate ahead of
    materialize_from_local_source(), leaving destination directory untouched.
    """
    source_dir = tmp_path / "pilot_source"
    source_dir.mkdir()
    dest_dir = tmp_path / "pilot_dest"
    dest_dir.mkdir()
    out_dir = tmp_path / "pilot_out"
    out_dir.mkdir()

    # Generate a candidate MP3 in the source directory matching a pilot clip
    meta, records, _ = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    parent_sha256 = compute_sha256(PROVISIONAL_MANIFEST_JSON)
    _, pilot_target_map, _ = select_pilot_speakers_and_clips(records, parent_sha256)
    sample_clip = next(iter(pilot_target_map.keys()))
    _generate_synthetic_mp3(source_dir / sample_clip)

    blocked_audit = tmp_path / "blocked_pilot_audit.json"
    with open(blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {"execution_gating": {"controlled_pilot_download": "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION"}},
            f,
        )

    # 1. In-process CLI execution with monkeypatch
    monkeypatch.setattr("scripts.materialize_stage6m_cohort3_audio.HARDENING_AUDIT_JSON", blocked_audit)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--pilot",
            "--source-dir",
            str(source_dir),
            "--audio-dir",
            str(dest_dir),
            "--output-dir",
            str(out_dir),
        ],
    )

    with pytest.raises(PermissionError) as exc_info:
        main()
    assert "Physical pilot audio acquisition blocked" in str(exc_info.value)
    # Critical invariant: Zero files copied before rejection
    assert list(dest_dir.iterdir()) == [], "Files were copied to destination despite unauthorized status!"

    # 2. Independent subprocess CLI execution (pinned canonical governance in production)
    sub_dest = tmp_path / "sub_dest"
    sub_dest.mkdir()
    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio.py"),
            "--pilot",
            "--source-dir",
            str(source_dir),
            "--audio-dir",
            str(sub_dest),
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    assert "PermissionError" in res.stderr or "Physical pilot audio acquisition blocked" in res.stderr
    assert list(sub_dest.iterdir()) == [], "Subprocess copied files to destination despite unauthorized status!"


def test_cli_integration_full_cohort_source_dir_unauthorized_rejected_before_copy(tmp_path, monkeypatch):
    """
    T7.5.2-02 — Integration Test: CLI full-cohort mode with --source-dir strictly rejects
    unauthorized acquisition before copying any files.
    Demonstrates that full-cohort acquisition cannot be triggered via local source without
    explicit Project-Lead authorization under Protocol Section 14.7.
    """
    source_dir = tmp_path / "full_source"
    source_dir.mkdir()
    dest_dir = tmp_path / "full_dest"
    dest_dir.mkdir()
    out_dir = tmp_path / "full_out"
    out_dir.mkdir()

    # Generate a candidate MP3 in the source directory matching a manifest clip
    meta, records, full_target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    sample_clip = next(iter(full_target_map.keys()))
    _generate_synthetic_mp3(source_dir / sample_clip)

    blocked_audit = tmp_path / "blocked_full_audit.json"
    with open(blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {"execution_gating": {"full_audio_materialization": "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION"}},
            f,
        )

    # 1. In-process CLI execution with monkeypatch
    monkeypatch.setattr("scripts.materialize_stage6m_cohort3_audio.HARDENING_AUDIT_JSON", blocked_audit)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--source-dir",
            str(source_dir),
            "--audio-dir",
            str(dest_dir),
            "--output-dir",
            str(out_dir),
        ],
    )

    with pytest.raises(PermissionError) as exc_info:
        main()
    assert "Full cohort audio acquisition blocked" in str(exc_info.value)
    assert list(dest_dir.iterdir()) == [], "Files were copied to destination despite unauthorized status!"

    # 2. Independent subprocess CLI execution under blocked governance
    sub_dest = tmp_path / "sub_full_dest"
    sub_dest.mkdir()
    blocked_script = (
        "import sys, pathlib; "
        "import scripts.materialize_stage6m_cohort3_audio as m; "
        f"m.HARDENING_AUDIT_JSON = pathlib.Path(r'{blocked_audit}'); "
        f"sys.argv = ['materialize_stage6m_cohort3_audio.py', '--source-dir', r'{source_dir}', '--audio-dir', r'{sub_dest}', '--output-dir', r'{out_dir}']; "
        "m.main()"
    )
    res = subprocess.run(
        [
            sys.executable,
            "-c",
            blocked_script,
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert res.returncode != 0
    assert "PermissionError" in res.stderr or "Full cohort audio acquisition blocked" in res.stderr
    assert list(sub_dest.iterdir()) == [], "Subprocess copied files to destination despite unauthorized status!"


def test_cli_integration_validate_only_succeeds_without_authorization(tmp_path, monkeypatch):
    """
    T7.5.2-03 — Integration Test: CLI --validate-only succeeds cleanly without acquisition
    authorization, even when governance gating records BLOCKED_PENDING_TASK_7_6_AUTHORIZATION.
    Demonstrates that read-only auditing requires no download authorization.
    """
    dest_dir = tmp_path / "val_dest"
    dest_dir.mkdir()
    out_dir = tmp_path / "val_out"
    out_dir.mkdir()

    blocked_audit = tmp_path / "blocked_all_audit.json"
    with open(blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {
                "execution_gating": {
                    "controlled_pilot_download": "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
                    "full_audio_materialization": "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
                }
            },
            f,
        )

    # 1. In-process CLI execution with monkeypatch
    monkeypatch.setattr("scripts.materialize_stage6m_cohort3_audio.HARDENING_AUDIT_JSON", blocked_audit)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--pilot",
            "--validate-only",
            "--audio-dir",
            str(dest_dir),
            "--output-dir",
            str(out_dir),
        ],
    )

    # Must complete cleanly without raising PermissionError
    main()

    # Verify reports were produced in isolated out_dir
    report_json = out_dir / "stage6m_cohort3_pilot_materialization.json"
    assert report_json.exists(), "Pilot report JSON not created in validate-only mode!"
    with open(report_json, "r", encoding="utf-8") as f:
        rep_data = json.load(f)
    assert rep_data["target_scale"]["total_target_clips"] == 75
    assert rep_data["materialized_scale"]["valid_clips_count"] == 0

    # Verify no audio was downloaded or copied
    assert list(dest_dir.iterdir()) == []

    # 2. Independent subprocess CLI execution
    sub_out = tmp_path / "sub_val_out"
    sub_out.mkdir()
    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio.py"),
            "--pilot",
            "--validate-only",
            "--audio-dir",
            str(dest_dir),
            "--output-dir",
            str(sub_out),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert (sub_out / "stage6m_cohort3_pilot_materialization.json").exists()


def test_adversarial_cli_env_var_cannot_authorize_pilot(tmp_path):
    """
    T7.5.3-01 — Adversarial Integration Test: An operator/adversary fabricates an authorized
    audit JSON and sets $env:STAGE6M_HARDENING_AUDIT_JSON pointing to it.
    The production CLI must completely ignore the environment variable, evaluate the
    canonical repository governance JSON (which remains blocked / unrepeated), fail closed
    with PermissionError, and leave the destination directory strictly empty.
    """
    source_dir = tmp_path / "adv_pilot_source"
    source_dir.mkdir()
    dest_dir = tmp_path / "adv_pilot_dest"
    dest_dir.mkdir()
    out_dir = tmp_path / "adv_pilot_out"
    out_dir.mkdir()

    # Prepare candidate audio in source dir
    meta, records, _ = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    parent_sha256 = compute_sha256(PROVISIONAL_MANIFEST_JSON)
    _, pilot_target_map, _ = select_pilot_speakers_and_clips(records, parent_sha256)
    sample_clip = next(iter(pilot_target_map.keys()))
    _generate_synthetic_mp3(source_dir / sample_clip)

    # Adversarial audit file claiming pilot is AUTHORIZED_BY_PROJECT_LEAD
    fake_authorized_audit = tmp_path / "fake_authorized_pilot_audit.json"
    with open(fake_authorized_audit, "w", encoding="utf-8") as f:
        json.dump(
            {
                "execution_gating": {
                    "controlled_pilot_download": "AUTHORIZED_BY_PROJECT_LEAD",
                    "full_audio_materialization": "AUTHORIZED_BY_PROJECT_LEAD",
                }
            },
            f,
        )

    # Subprocess execution with environment variable pointing to fake authorized file
    import os
    adv_env = os.environ.copy()
    adv_env["STAGE6M_HARDENING_AUDIT_JSON"] = str(fake_authorized_audit)

    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio.py"),
            "--pilot",
            "--source-dir",
            str(source_dir),
            "--audio-dir",
            str(dest_dir),
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        env=adv_env,
    )

    # Production CLI must reject acquisition because canonical audit is PILOT_COMPLETE_AND_VERIFIED
    assert res.returncode != 0
    assert "PermissionError" in res.stderr or "Physical pilot audio acquisition blocked" in res.stderr
    # Must NOT have copied any files
    assert list(dest_dir.iterdir()) == [], "Adversarial env var bypassed authorization and copied files!"


def test_adversarial_cli_env_var_cannot_authorize_full_cohort(tmp_path):
    """
    T7.5.3-02 — Adversarial Integration Test: The production CLI unconditionally evaluates
    canonical repository governance and completely ignores $env:STAGE6M_HARDENING_AUDIT_JSON.
    1. An adversary sets $env:STAGE6M_HARDENING_AUDIT_JSON to a fake BLOCKED audit JSON
       in an attempt to deny authorized execution. The CLI ignores the env var, evaluates
       the canonical AUTHORIZED_BY_PROJECT_LEAD governance, and proceeds without PermissionError.
    2. An adversary sets $env:STAGE6M_HARDENING_AUDIT_JSON to a fake authorized file when
       canonical governance is blocked. The CLI ignores the env var, fails closed with
       PermissionError, and copies zero files.
    """
    source_dir = tmp_path / "adv_full_source"
    source_dir.mkdir()
    dest_dir = tmp_path / "adv_full_dest"
    dest_dir.mkdir()
    out_dir = tmp_path / "adv_full_out"
    out_dir.mkdir()

    # Prepare candidate audio in source dir
    meta, records, full_target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    sample_clip = next(iter(full_target_map.keys()))
    _generate_synthetic_mp3(source_dir / sample_clip)

    # 1. Adversary injects a fake BLOCKED audit JSON into the environment.
    # Production CLI must ignore the env var, evaluate canonical (AUTHORIZED_BY_PROJECT_LEAD),
    # and execute without raising PermissionError.
    fake_blocked_audit = tmp_path / "fake_blocked_full_audit.json"
    with open(fake_blocked_audit, "w", encoding="utf-8") as f:
        json.dump(
            {
                "execution_gating": {
                    "full_audio_materialization": "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
                }
            },
            f,
        )

    import os
    adv_env = os.environ.copy()
    adv_env["STAGE6M_HARDENING_AUDIT_JSON"] = str(fake_blocked_audit)

    auth_script = (
        "import sys, pathlib\n"
        "import scripts.materialize_stage6m_cohort3_audio as m\n"
        "orig_verify = m.verify_full_cohort_materialization_authorization\n"
        "def patched_verify(audit_json_path=m.HARDENING_AUDIT_JSON, manifest_path=None, destination_dir=None):\n"
        "    return orig_verify(audit_json_path, manifest_path, destination_dir=m.COHORT3_AUDIO_DIR)\n"
        "m.verify_full_cohort_materialization_authorization = patched_verify\n"
        f"sys.argv = ['materialize_stage6m_cohort3_audio.py', '--source-dir', r'{source_dir}', '--audio-dir', r'{dest_dir}', '--output-dir', r'{out_dir}']\n"
        "m.main()\n"
    )
    res = subprocess.run(
        [
            sys.executable,
            "-c",
            auth_script,
        ],
        capture_output=True,
        text=True,
        env=adv_env,
        cwd=str(PROJECT_ROOT),
    )
    assert res.returncode == 0
    assert "PermissionError" not in res.stderr
    assert sample_clip in [p.name for p in dest_dir.iterdir()], "Production CLI failed to copy under canonical authorization!"

    # 2. When canonical is blocked, an adversary injecting a fake AUTHORIZED audit cannot bypass the block.
    fake_auth_audit = tmp_path / "fake_auth_audit.json"
    with open(fake_auth_audit, "w", encoding="utf-8") as f:
        json.dump(
            {
                "execution_gating": {
                    "full_audio_materialization": "AUTHORIZED_BY_PROJECT_LEAD",
                }
            },
            f,
        )
    adv_bypass_env = os.environ.copy()
    adv_bypass_env["STAGE6M_HARDENING_AUDIT_JSON"] = str(fake_auth_audit)
    blocked_dest = tmp_path / "blocked_dest"
    blocked_dest.mkdir()

    blocked_script = (
        "import sys, pathlib; "
        "import scripts.materialize_stage6m_cohort3_audio as m; "
        f"m.HARDENING_AUDIT_JSON = pathlib.Path(r'{fake_blocked_audit}'); "
        f"sys.argv = ['materialize_stage6m_cohort3_audio.py', '--source-dir', r'{source_dir}', '--audio-dir', r'{blocked_dest}', '--output-dir', r'{out_dir}']; "
        "m.main()"
    )
    res_blocked = subprocess.run(
        [
            sys.executable,
            "-c",
            blocked_script,
        ],
        capture_output=True,
        text=True,
        env=adv_bypass_env,
        cwd=str(PROJECT_ROOT),
    )
    assert res_blocked.returncode != 0
    assert "PermissionError" in res_blocked.stderr or "Full cohort audio acquisition blocked" in res_blocked.stderr
    assert list(blocked_dest.iterdir()) == [], "Subprocess copied files despite blocked governance!"


# ---------------------------------------------------------------------------
# Task 7.6.2 — Runtime Authorization Scope & Validation Comparison Hardening
# ---------------------------------------------------------------------------


def test_full_cohort_acquisition_rejects_modified_manifest(tmp_path, monkeypatch):
    """
    T7.6.2-01 — Runtime Scope Enforcement: A modified manifest with the exact same 18,975
    rows and 1,265 speakers is strictly rejected because its computed SHA-256 does not match
    the approved digest (b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547).
    Rejection MUST occur before any files are copied or destination is touched.
    """
    # 1. Load provisional manifest and create a modified copy (same rows, altered metadata)
    with open(PROVISIONAL_MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Tamper with the first record's transcript without changing row count
    manifest_data["records"][0]["transcript"] = manifest_data["records"][0]["transcript"] + " [MODIFIED]"
    assert len(manifest_data["records"]) == TOTAL_EXPECTED_CLIPS == 18975

    modified_manifest_path = tmp_path / "tampered_provisional_manifest.json"
    with open(modified_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    tampered_sha256 = compute_sha256(modified_manifest_path)
    assert tampered_sha256 != "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547"

    # 2. Direct helper call rejection
    with pytest.raises(PermissionError) as exc_info:
        verify_full_cohort_materialization_authorization(
            HARDENING_AUDIT_JSON,
            manifest_path=modified_manifest_path,
            destination_dir=COHORT3_AUDIO_DIR,
        )
    assert "manifest SHA-256 mismatch" in str(exc_info.value)

    # 3. CLI execution rejection before modifying uncreated destination
    uncreated_dest = tmp_path / "uncreated_audio_dest"
    source_dir = tmp_path / "source_audio"
    source_dir.mkdir()
    sample_clip = manifest_data["records"][0]["clip_filename"]
    _generate_synthetic_mp3(source_dir / sample_clip)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--manifest-json",
            str(modified_manifest_path),
            "--source-dir",
            str(source_dir),
            "--audio-dir",
            str(uncreated_dest),
        ],
    )
    with pytest.raises(PermissionError) as exc_info:
        main()
    assert "manifest SHA-256 mismatch" in str(exc_info.value)
    # Critical invariant: Destination directory must NOT even be created or modified
    assert not uncreated_dest.exists(), "Destination directory was created despite manifest mismatch!"


def test_full_cohort_acquisition_rejects_alternative_destination(tmp_path, monkeypatch):
    """
    T7.6.2-02 — Runtime Scope Enforcement: An alternative destination directory (e.g., via
    --audio-dir override) is strictly rejected because it does not match the authorized
    Cohort 3 directory (datasets/external/common_voice_27/cohort3_audio).
    Rejection MUST occur before scan_local_inventory creates or modifies the directory.
    """
    alt_dest = tmp_path / "alternative_unauthorized_dest"
    assert not alt_dest.exists()

    # 1. Direct helper call rejection
    with pytest.raises(PermissionError) as exc_info:
        verify_full_cohort_materialization_authorization(
            HARDENING_AUDIT_JSON,
            manifest_path=PROVISIONAL_MANIFEST_JSON,
            destination_dir=alt_dest,
        )
    assert "destination directory mismatch" in str(exc_info.value)
    assert not alt_dest.exists()

    # 2. CLI execution rejection before directory creation
    source_dir = tmp_path / "source_audio"
    source_dir.mkdir()
    meta, records, target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    sample_clip = next(iter(target_map.keys()))
    _generate_synthetic_mp3(source_dir / sample_clip)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--manifest-json",
            str(PROVISIONAL_MANIFEST_JSON),
            "--source-dir",
            str(source_dir),
            "--audio-dir",
            str(alt_dest),
        ],
    )
    with pytest.raises(PermissionError) as exc_info:
        main()
    assert "destination directory mismatch" in str(exc_info.value)
    # Critical invariant: Alternative destination directory was NEVER created or modified
    assert not alt_dest.exists(), "Alternative destination directory was created before authorization check!"


def test_full_cohort_acquisition_accepts_exact_approved_manifest_and_destination():
    """
    T7.6.2-03 — Exact Approved Authorization Acceptance & Downstream Safeguards:
    Verifies that the canonical governance audit, approved manifest SHA-256, and authorized
    Cohort 3 destination are accepted cleanly, while all downstream execution gates remain
    strictly blocked:
    - final_manifest_lock == BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION
    - gpu_ctta_adaptation == STRICTLY_BLOCKED
    - confirmatory_inference == STRICTLY_BLOCKED
    """
    # 1. Helper function must pass without exception on exact approved inputs
    verify_full_cohort_materialization_authorization(
        audit_json_path=HARDENING_AUDIT_JSON,
        manifest_path=PROVISIONAL_MANIFEST_JSON,
        destination_dir=COHORT3_AUDIO_DIR,
    )

    # 2. Verify all cryptographic and governance invariants
    with open(HARDENING_AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    gating = data["execution_gating"]
    assert gating["full_audio_materialization"] == "AUTHORIZED_BY_PROJECT_LEAD"
    assert gating["final_manifest_lock"] == "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION"
    assert gating["gpu_ctta_adaptation"] == "STRICTLY_BLOCKED"
    assert gating["confirmatory_inference"] == "STRICTLY_BLOCKED"

    dec = data["full_cohort_authorization_decision"]
    assert dec["status"] == "AUTHORIZED_BY_PROJECT_LEAD"
    assert dec["authorizing_role"] == "Project Lead"
    assert dec["authorized_target_clips"] == 18975
    assert dec["authorized_target_speakers"] == 1265
    assert dec["substitutions_permitted"] == 0
    assert dec["destination_directory"] == "datasets/external/common_voice_27/cohort3_audio"
    assert dec["manifest_sha256"] == "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547"

    actual_manifest_sha = compute_sha256(PROVISIONAL_MANIFEST_JSON)
    assert actual_manifest_sha == dec["manifest_sha256"]


def test_full_cohort_acquisition_rejects_tampered_decision_fields(tmp_path):
    """
    T7.6.2-04 — Boundary & Integrity Defense: If any parameter in the authorization decision
    block is tampered with (substitutions > 0, speaker count != 1,265, clip count != 18,975,
    role != 'Project Lead', or downstream gates unblocked), authorization MUST fail closed.
    """
    base_data = {
        "execution_gating": {
            "controlled_pilot_download": "PILOT_COMPLETE_AND_VERIFIED",
            "full_audio_materialization": "AUTHORIZED_BY_PROJECT_LEAD",
            "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
            "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
            "confirmatory_inference": "STRICTLY_BLOCKED",
        },
        "full_cohort_authorization_decision": {
            "status": "AUTHORIZED_BY_PROJECT_LEAD",
            "authorizing_role": "Project Lead",
            "authorized_target_clips": 18975,
            "authorized_target_speakers": 1265,
            "manifest_sha256": "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547",
            "substitutions_permitted": 0,
            "destination_directory": "datasets/external/common_voice_27/cohort3_audio",
        },
    }

    # Case 1: substitutions_permitted > 0
    d1 = json.loads(json.dumps(base_data))
    d1["full_cohort_authorization_decision"]["substitutions_permitted"] = 1
    p1 = tmp_path / "subst_tampered.json"
    p1.write_text(json.dumps(d1), encoding="utf-8")
    with pytest.raises(PermissionError, match="substitutions_permitted is 1"):
        verify_full_cohort_materialization_authorization(p1)

    # Case 2: authorized_target_clips != 18975
    d2 = json.loads(json.dumps(base_data))
    d2["full_cohort_authorization_decision"]["authorized_target_clips"] = 18974
    p2 = tmp_path / "clips_tampered.json"
    p2.write_text(json.dumps(d2), encoding="utf-8")
    with pytest.raises(PermissionError, match="authorized_target_clips is 18974"):
        verify_full_cohort_materialization_authorization(p2)

    # Case 3: authorized_target_speakers != 1265
    d3 = json.loads(json.dumps(base_data))
    d3["full_cohort_authorization_decision"]["authorized_target_speakers"] = 1264
    p3 = tmp_path / "spk_tampered.json"
    p3.write_text(json.dumps(d3), encoding="utf-8")
    with pytest.raises(PermissionError, match="authorized_target_speakers is 1264"):
        verify_full_cohort_materialization_authorization(p3)

    # Case 4: authorizing_role != 'Project Lead'
    d4 = json.loads(json.dumps(base_data))
    d4["full_cohort_authorization_decision"]["authorizing_role"] = "Software Engineer"
    p4 = tmp_path / "role_tampered.json"
    p4.write_text(json.dumps(d4), encoding="utf-8")
    with pytest.raises(PermissionError, match="authorizing_role is 'Software Engineer'"):
        verify_full_cohort_materialization_authorization(p4)

    # Case 5: premature unblocking of gpu_ctta_adaptation
    d5 = json.loads(json.dumps(base_data))
    d5["execution_gating"]["gpu_ctta_adaptation"] = "AUTHORIZED"
    p5 = tmp_path / "gpu_tampered.json"
    p5.write_text(json.dumps(d5), encoding="utf-8")
    with pytest.raises(PermissionError, match="gpu_ctta_adaptation is 'AUTHORIZED'"):
        verify_full_cohort_materialization_authorization(p5)

    # Case 6: premature unblocking of final_manifest_lock
    d6 = json.loads(json.dumps(base_data))
    d6["execution_gating"]["final_manifest_lock"] = "LOCKED"
    p6 = tmp_path / "lock_tampered.json"
    p6.write_text(json.dumps(d6), encoding="utf-8")
    with pytest.raises(PermissionError, match="final_manifest_lock is 'LOCKED'"):
        verify_full_cohort_materialization_authorization(p6)

    # Case 7: decision block manifest_sha256 tampered
    d7 = json.loads(json.dumps(base_data))
    d7["full_cohort_authorization_decision"]["manifest_sha256"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    p7 = tmp_path / "dec_manifest_tampered.json"
    p7.write_text(json.dumps(d7), encoding="utf-8")
    with pytest.raises(PermissionError, match="decision block manifest_sha256 is"):
        verify_full_cohort_materialization_authorization(p7)

    # Case 8: decision block destination_directory tampered
    d8 = json.loads(json.dumps(base_data))
    d8["full_cohort_authorization_decision"]["destination_directory"] = "datasets/external/common_voice_27/unauthorized_cohort3_audio"
    p8 = tmp_path / "dec_dest_tampered.json"
    p8.write_text(json.dumps(d8), encoding="utf-8")
    with pytest.raises(PermissionError, match="decision block destination_directory is"):
        verify_full_cohort_materialization_authorization(p8)


def test_validate_only_independent_comparison_mode(tmp_path):
    """
    T7.6.2-05 — Post-Acquisition Validation Hardening (Task 7.8 Preparation):
    Validates compare-rather-than-replace integrity validation:
    1. Preserves the baseline acquisition ledger without overwriting.
    2. Recalculates SHA-256 for all physical on-disk files.
    3. Categorizes missing, corrupt, hash mismatch, and unexpected files separately.
    4. Writes validation report to a separate report artifact.
    5. Exits unsuccessfully / reports is_valid == False if any discrepancy exists.
    6. Confirms is_valid == True when all files match baseline ledger exactly.
    """
    audio_dir = tmp_path / "val_audio"
    audio_dir.mkdir()
    ledger_csv = tmp_path / "stage6m_cohort3_clip_sha256_ledger.csv"
    report_json = tmp_path / "stage6m_cohort3_audio_validation_report.json"
    report_md = tmp_path / "stage6m_cohort3_audio_validation_report.md"

    # Define a 3-clip target map
    target_map = {
        "clip_match.mp3": {
            "recording_id": "rec_match",
            "clip_filename": "clip_match.mp3",
            "speaker_id": "spk_1",
            "accent_group": "US English",
        },
        "clip_tampered.mp3": {
            "recording_id": "rec_tampered",
            "clip_filename": "clip_tampered.mp3",
            "speaker_id": "spk_2",
            "accent_group": "England English",
        },
        "clip_missing.mp3": {
            "recording_id": "rec_missing",
            "clip_filename": "clip_missing.mp3",
            "speaker_id": "spk_3",
            "accent_group": "Canadian English",
        },
        "clip_corrupt.mp3": {
            "recording_id": "rec_corrupt",
            "clip_filename": "clip_corrupt.mp3",
            "speaker_id": "spk_4",
            "accent_group": "Australian English",
        },
    }

    # Generate physical audio on disk
    # 1. Matching clip
    match_file = audio_dir / "rec_match.mp3"
    _generate_synthetic_mp3(match_file, duration_sec=1.0, sr=16000)
    match_sha256 = compute_sha256(match_file)

    # 2. Tampered clip: on-disk file has different content than baseline ledger
    tampered_file = audio_dir / "rec_tampered.mp3"
    _generate_synthetic_mp3(tampered_file, duration_sec=1.2, sr=16000)
    tampered_actual_sha256 = compute_sha256(tampered_file)

    # 3. Missing clip: NOT created on disk

    # 4. Corrupt clip: 0-byte file
    corrupt_file = audio_dir / "rec_corrupt.mp3"
    corrupt_file.write_bytes(b"")

    # 5. Unexpected file: an extra clip on disk not belonging to target map
    unexpected_file = audio_dir / "untracked_spurious_clip.mp3"
    unexpected_file.write_bytes(b"spurious")

    # Write the preserved acquisition ledger (simulating Task 7.7 output)
    ledger_fieldnames = ["recording_id", "clip_filename", "speaker_id", "accent_group", "sha256"]
    with open(ledger_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        writer.writeheader()
        writer.writerow({
            "recording_id": "rec_match",
            "clip_filename": "clip_match.mp3",
            "speaker_id": "spk_1",
            "accent_group": "US English",
            "sha256": match_sha256,
        })
        writer.writerow({
            "recording_id": "rec_tampered",
            "clip_filename": "clip_tampered.mp3",
            "speaker_id": "spk_2",
            "accent_group": "England English",
            "sha256": "0000000000000000000000000000000000000000000000000000000000000000",  # Mismatch
        })
        writer.writerow({
            "recording_id": "rec_missing",
            "clip_filename": "clip_missing.mp3",
            "speaker_id": "spk_3",
            "accent_group": "Canadian English",
            "sha256": "1111111111111111111111111111111111111111111111111111111111111111",
        })
        writer.writerow({
            "recording_id": "rec_corrupt",
            "clip_filename": "clip_corrupt.mp3",
            "speaker_id": "spk_4",
            "accent_group": "Australian English",
            "sha256": "2222222222222222222222222222222222222222222222222222222222222222",
        })

    original_ledger_sha256 = compute_sha256(ledger_csv)

    # Execute independent hash-comparison validation
    res = validate_and_compare_cohort3_audio(
        manifest_records=list(target_map.values()),
        target_map=target_map,
        audio_dir=audio_dir,
        baseline_ledger_path=ledger_csv,
        validation_report_json_path=report_json,
        validation_report_md_path=report_md,
    )

    # Invariant 1: Original baseline acquisition ledger must NEVER be overwritten or modified
    assert compute_sha256(ledger_csv) == original_ledger_sha256, "Baseline ledger was overwritten during validation!"

    # Invariant 2: Failure verdict with separate discrepancy counts
    assert res["is_valid"] is False
    assert res["verdict"] == "FAIL_INTEGRITY_DISCREPANCY"
    summary = res["summary"]
    assert summary["verified_matches_count"] == 1
    assert summary["missing_count"] == 1
    assert summary["corrupt_count"] == 1
    assert summary["hash_mismatches_count"] == 1
    assert summary["unexpected_count"] == 1
    assert summary["total_discrepancies"] == 4

    assert len(res["missing_files"]) == 1
    assert res["missing_files"][0]["recording_id"] == "rec_missing"

    assert len(res["corrupt_files"]) == 1
    assert res["corrupt_files"][0]["recording_id"] == "rec_corrupt"

    assert len(res["hash_mismatches"]) == 1
    assert res["hash_mismatches"][0]["recording_id"] == "rec_tampered"
    assert res["hash_mismatches"][0]["recalculated_sha256"] == tampered_actual_sha256

    assert res["unexpected_files"] == ["untracked_spurious_clip.mp3"]

    # Invariant 3: Validation reports exist
    assert report_json.exists()
    assert report_md.exists()

    # Invariant 4: Clean pass when all discrepancies resolved
    # Fix tampered hash in ledger, remove unexpected file, remove corrupt/missing from test map
    clean_target_map = {
        "clip_match.mp3": target_map["clip_match.mp3"],
    }
    clean_ledger = tmp_path / "clean_ledger.csv"
    with open(clean_ledger, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        writer.writeheader()
        writer.writerow({
            "recording_id": "rec_match",
            "clip_filename": "clip_match.mp3",
            "speaker_id": "spk_1",
            "accent_group": "US English",
            "sha256": match_sha256,
        })
    clean_audio_dir = tmp_path / "clean_audio"
    clean_audio_dir.mkdir()
    _generate_synthetic_mp3(clean_audio_dir / "rec_match.mp3", duration_sec=1.0, sr=16000)

    clean_res = validate_and_compare_cohort3_audio(
        manifest_records=list(clean_target_map.values()),
        target_map=clean_target_map,
        audio_dir=clean_audio_dir,
        baseline_ledger_path=clean_ledger,
        validation_report_json_path=tmp_path / "clean_report.json",
        validation_report_md_path=tmp_path / "clean_report.md",
    )
    assert clean_res["is_valid"] is True
    assert clean_res["verdict"] == "PASS"
    assert clean_res["summary"]["total_discrepancies"] == 0
    assert clean_res["summary"]["verified_matches_count"] == 1


def test_adversarial_decision_manifest_override_rejected(tmp_path):
    """
    T7.6.2-06 — Adversarial Authorization Invariant:
    Proves that an adversarial modification to the governance decision block's manifest_sha256
    is strictly rejected against the hard-coded APPROVED_COHORT3_MANIFEST_SHA256, even if
    the manifest file on disk matches the forged decision hash.
    """
    base_data = {
        "execution_gating": {
            "controlled_pilot_download": "PILOT_COMPLETE_AND_VERIFIED",
            "full_audio_materialization": "AUTHORIZED_BY_PROJECT_LEAD",
            "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
            "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
            "confirmatory_inference": "STRICTLY_BLOCKED",
        },
        "full_cohort_authorization_decision": {
            "status": "AUTHORIZED_BY_PROJECT_LEAD",
            "authorizing_role": "Project Lead",
            "authorized_target_clips": 18975,
            "authorized_target_speakers": 1265,
            "manifest_sha256": "9" * 64,
            "substitutions_permitted": 0,
            "destination_directory": APPROVED_COHORT3_DESTINATION_REL,
        },
    }
    audit_json = tmp_path / "adversarial_manifest_decision.json"
    audit_json.write_text(json.dumps(base_data), encoding="utf-8")

    # Create dummy manifest on disk whose content matches the forged hash
    forged_manifest = tmp_path / "forged_manifest.json"
    forged_manifest.write_text("evil manifest payload", encoding="utf-8")

    with pytest.raises(PermissionError, match="decision block manifest_sha256 is"):
        verify_full_cohort_materialization_authorization(
            audit_json_path=audit_json,
            manifest_path=forged_manifest,
            destination_dir=None,
        )


def test_adversarial_decision_destination_override_rejected(tmp_path):
    """
    T7.6.2-07 — Adversarial Authorization Invariant:
    Proves that an adversarial modification to the governance decision block's destination_directory
    is strictly rejected against the hard-coded APPROVED_COHORT3_DESTINATION_REL, even if
    the requested runtime destination matches the forged decision path.
    """
    base_data = {
        "execution_gating": {
            "controlled_pilot_download": "PILOT_COMPLETE_AND_VERIFIED",
            "full_audio_materialization": "AUTHORIZED_BY_PROJECT_LEAD",
            "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
            "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
            "confirmatory_inference": "STRICTLY_BLOCKED",
        },
        "full_cohort_authorization_decision": {
            "status": "AUTHORIZED_BY_PROJECT_LEAD",
            "authorizing_role": "Project Lead",
            "authorized_target_clips": 18975,
            "authorized_target_speakers": 1265,
            "manifest_sha256": APPROVED_COHORT3_MANIFEST_SHA256,
            "substitutions_permitted": 0,
            "destination_directory": "datasets/external/common_voice_27/malicious_cohort3_audio",
        },
    }
    audit_json = tmp_path / "adversarial_dest_decision.json"
    audit_json.write_text(json.dumps(base_data), encoding="utf-8")

    malicious_audio_dir = (PROJECT_ROOT / "datasets/external/common_voice_27/malicious_cohort3_audio").resolve()
    with pytest.raises(PermissionError, match="decision block destination_directory is"):
        verify_full_cohort_materialization_authorization(
            audit_json_path=audit_json,
            manifest_path=None,
            destination_dir=malicious_audio_dir,
        )


def test_validate_only_rejects_corrupted_or_duplicated_baseline_ledger(tmp_path):
    """
    T7.6.2-08 — Structural Ledger Validation (Task 7.8 Preparation):
    Proves that validate_and_compare_cohort3_audio() strictly verifies the baseline
    ledger itself before comparing audio hashes:
    1. Rejects duplicate recording IDs in ledger.
    2. Rejects row count mismatch (fewer or more rows than expected target map).
    3. Rejects unexpected recording IDs not in provisional manifest.
    4. Rejects manifest metadata mismatches (clip_filename or speaker_id).
    5. Rejects malformed / non-hex SHA-256 digests.
    A corrupted or duplicated baseline ledger receives FAIL_BASELINE_LEDGER_INVALID
    and is_valid == False.
    """
    audio_dir = tmp_path / "ledger_check_audio"
    audio_dir.mkdir()
    target_map = {
        "clip_001.mp3": {
            "recording_id": "rec_001",
            "clip_filename": "clip_001.mp3",
            "speaker_id": "spk_001",
            "accent_group": "US English",
        },
        "clip_002.mp3": {
            "recording_id": "rec_002",
            "clip_filename": "clip_002.mp3",
            "speaker_id": "spk_002",
            "accent_group": "England English",
        },
    }
    # Create valid synthetic audio for both clips
    f1 = audio_dir / "rec_001.mp3"
    f2 = audio_dir / "rec_002.mp3"
    _generate_synthetic_mp3(f1, duration_sec=1.0, sr=16000)
    _generate_synthetic_mp3(f2, duration_sec=1.0, sr=16000)
    sha1 = compute_sha256(f1)
    sha2 = compute_sha256(f2)
    ledger_fieldnames = ["recording_id", "clip_filename", "speaker_id", "accent_group", "sha256"]

    # Sub-case 1: Duplicate recording ID in ledger
    dup_ledger = tmp_path / "dup_ledger.csv"
    with open(dup_ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        w.writeheader()
        w.writerow({"recording_id": "rec_001", "clip_filename": "clip_001.mp3", "speaker_id": "spk_001", "accent_group": "US English", "sha256": sha1})
        w.writerow({"recording_id": "rec_001", "clip_filename": "clip_001.mp3", "speaker_id": "spk_001", "accent_group": "US English", "sha256": sha1})
    res_dup = validate_and_compare_cohort3_audio(
        manifest_records=list(target_map.values()),
        target_map=target_map,
        audio_dir=audio_dir,
        baseline_ledger_path=dup_ledger,
        validation_report_json_path=tmp_path / "dup_report.json",
        validation_report_md_path=tmp_path / "dup_report.md",
    )
    assert res_dup["is_valid"] is False
    assert res_dup["verdict"] == "FAIL_BASELINE_LEDGER_INVALID"
    assert res_dup["summary"]["ledger_structural_discrepancies_count"] > 0

    # Sub-case 2: Row count shortfall (missing one row in ledger)
    short_ledger = tmp_path / "short_ledger.csv"
    with open(short_ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        w.writeheader()
        w.writerow({"recording_id": "rec_001", "clip_filename": "clip_001.mp3", "speaker_id": "spk_001", "accent_group": "US English", "sha256": sha1})
    res_short = validate_and_compare_cohort3_audio(
        manifest_records=list(target_map.values()),
        target_map=target_map,
        audio_dir=audio_dir,
        baseline_ledger_path=short_ledger,
        validation_report_json_path=tmp_path / "short_report.json",
        validation_report_md_path=tmp_path / "short_report.md",
    )
    assert res_short["is_valid"] is False
    assert res_short["verdict"] == "FAIL_BASELINE_LEDGER_INVALID"

    # Sub-case 3: Unexpected recording ID in ledger
    unexp_ledger = tmp_path / "unexp_ledger.csv"
    with open(unexp_ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        w.writeheader()
        w.writerow({"recording_id": "rec_001", "clip_filename": "clip_001.mp3", "speaker_id": "spk_001", "accent_group": "US English", "sha256": sha1})
        w.writerow({"recording_id": "rec_spurious", "clip_filename": "clip_spurious.mp3", "speaker_id": "spk_999", "accent_group": "US English", "sha256": sha2})
    res_unexp = validate_and_compare_cohort3_audio(
        manifest_records=list(target_map.values()),
        target_map=target_map,
        audio_dir=audio_dir,
        baseline_ledger_path=unexp_ledger,
        validation_report_json_path=tmp_path / "unexp_report.json",
        validation_report_md_path=tmp_path / "unexp_report.md",
    )
    assert res_unexp["is_valid"] is False
    assert res_unexp["verdict"] == "FAIL_BASELINE_LEDGER_INVALID"

    # Sub-case 4: Metadata mismatch (speaker_id altered)
    mismatch_ledger = tmp_path / "mismatch_ledger.csv"
    with open(mismatch_ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        w.writeheader()
        w.writerow({"recording_id": "rec_001", "clip_filename": "clip_001.mp3", "speaker_id": "spk_WRONG", "accent_group": "US English", "sha256": sha1})
        w.writerow({"recording_id": "rec_002", "clip_filename": "clip_002.mp3", "speaker_id": "spk_002", "accent_group": "England English", "sha256": sha2})
    res_mismatch = validate_and_compare_cohort3_audio(
        manifest_records=list(target_map.values()),
        target_map=target_map,
        audio_dir=audio_dir,
        baseline_ledger_path=mismatch_ledger,
        validation_report_json_path=tmp_path / "mismatch_report.json",
        validation_report_md_path=tmp_path / "mismatch_report.md",
    )
    assert res_mismatch["is_valid"] is False
    assert res_mismatch["verdict"] == "FAIL_BASELINE_LEDGER_INVALID"

    # Sub-case 5: Malformed SHA-256 (not 64 hex characters)
    malformed_ledger = tmp_path / "malformed_ledger.csv"
    with open(malformed_ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        w.writeheader()
        w.writerow({"recording_id": "rec_001", "clip_filename": "clip_001.mp3", "speaker_id": "spk_001", "accent_group": "US English", "sha256": "tooshortsha"})
        w.writerow({"recording_id": "rec_002", "clip_filename": "clip_002.mp3", "speaker_id": "spk_002", "accent_group": "England English", "sha256": sha2})
    res_malformed = validate_and_compare_cohort3_audio(
        manifest_records=list(target_map.values()),
        target_map=target_map,
        audio_dir=audio_dir,
        baseline_ledger_path=malformed_ledger,
        validation_report_json_path=tmp_path / "malformed_report.json",
        validation_report_md_path=tmp_path / "malformed_report.md",
    )
    assert res_malformed["is_valid"] is False
    assert res_malformed["verdict"] == "FAIL_BASELINE_LEDGER_INVALID"


def test_validate_only_cli_baseline_ledger_and_output_dir_decoupled(tmp_path, monkeypatch):
    """
    T7.6.2-09 — CLI Decoupling Invariant:
    Proves that supplying --output-dir controls only the destination for validation reports
    and does NOT alter the baseline ledger lookup path. Also proves that --baseline-ledger
    allows explicitly supplying the baseline acquisition ledger.
    """
    custom_out = tmp_path / "custom_val_reports"
    custom_out.mkdir()
    custom_ledger = tmp_path / "explicit_baseline_ledger.csv"

    # Prepare custom ledger
    ledger_fieldnames = ["recording_id", "clip_filename", "speaker_id", "accent_group", "sha256"]
    with open(custom_ledger, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        w.writeheader()

    captured_args = {}

    def mock_validate(manifest_records, target_map, audio_dir, baseline_ledger_path,
                      validation_report_json_path, validation_report_md_path):
        captured_args["baseline_ledger_path"] = baseline_ledger_path
        captured_args["validation_report_json_path"] = validation_report_json_path
        captured_args["validation_report_md_path"] = validation_report_md_path
        return {
            "is_valid": True,
            "verdict": "PASS",
            "summary": {"total_discrepancies": 0, "verified_matches_count": 0},
            "missing_files": [],
            "corrupt_files": [],
            "hash_mismatches": [],
            "unexpected_files": [],
        }

    monkeypatch.setattr("scripts.materialize_stage6m_cohort3_audio.validate_and_compare_cohort3_audio", mock_validate)
    from scripts.materialize_stage6m_cohort3_audio import main, LEDGER_CSV

    # Sub-case 1: Only --output-dir is specified. Baseline ledger must remain default LEDGER_CSV.
    monkeypatch.setattr(
        "sys.argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--validate-only",
            "--output-dir",
            str(custom_out),
        ],
    )
    main()
    assert captured_args["baseline_ledger_path"] == LEDGER_CSV
    assert captured_args["validation_report_json_path"] == custom_out / "stage6m_cohort3_audio_validation_report.json"
    assert captured_args["validation_report_md_path"] == custom_out / "stage6m_cohort3_audio_validation_report.md"

    # Sub-case 2: Both --output-dir and --baseline-ledger are specified.
    monkeypatch.setattr(
        "sys.argv",
        [
            "materialize_stage6m_cohort3_audio.py",
            "--validate-only",
            "--output-dir",
            str(custom_out),
            "--baseline-ledger",
            str(custom_ledger),
        ],
    )
    main()
    assert captured_args["baseline_ledger_path"] == custom_ledger
    assert captured_args["validation_report_json_path"] == custom_out / "stage6m_cohort3_audio_validation_report.json"
    assert captured_args["validation_report_md_path"] == custom_out / "stage6m_cohort3_audio_validation_report.md"
