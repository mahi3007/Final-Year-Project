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
    ThreadedResilientGzipStream,
    generate_materialization_artifacts,
    load_provisional_manifest,
    materialize_from_local_source,
    scan_local_inventory,
    validate_audio_file,
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


def test_speaker_completeness_accounting_zero_audio(tmp_path):
    """
    Verify Issue A: When 0 clips are materialized, all 1,265 target speakers
    must appear in the speaker completeness report as incomplete with 0 valid clips.
    """
    meta, records, target_map = load_provisional_manifest(PROVISIONAL_MANIFEST_JSON)
    empty_valid: dict = {}
    empty_failed: dict = {}

    art = generate_materialization_artifacts(
        meta, records, target_map, empty_valid, empty_failed, tmp_path
    )

    # 1. Returned artifacts metadata
    scale = art["materialized_scale"]
    assert scale["valid_clips_count"] == 0
    assert scale["remaining_clips_count"] == TOTAL_EXPECTED_CLIPS == 18975
    assert scale["total_target_speakers"] == TOTAL_EXPECTED_SPEAKERS == 1265
    assert scale["complete_speakers_count"] == 0
    assert scale["incomplete_speakers_count"] == 1265

    # 2. Check JSON report
    with open(SPEAKER_REPORT_JSON, "r", encoding="utf-8") as f:
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
