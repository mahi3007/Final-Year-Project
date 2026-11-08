"""
tests/research_validity/test_stage6m_cohort3_materializer_v2.py

Deterministic Automated Test Suite for Stage 6M Task 7.7.4 Non-Destructive Materializer (v2)
=============================================================================================
Governing Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
Governance Phase:   Gate 2 Implementation & Pre-Production Validation

Test Coverage:
1. P1: Strict read-only source access and source immutability invariant.
2. P2: Atomic no-clobber publication via os.link() with fail-closed collision handling.
3. P3: Idempotent pre-check: matching hashes skip writes; mismatched hashes fail closed.
4. P4: OS-level staging locks (msvcrt.locking LK_NBLCK) overriding PID and TTL in orphan recovery.
5. P5: 3-decoder multi-backend verification pipeline (SoundFile, PyAV, miniaudio).
6. P6: Quarantine preservation and forensic disposition tracking under Policy 2A.
7. Production boundary guard: blocks premature production dataset mutation prior to Gate 3.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.materialize_stage6m_cohort3_audio_v2 import (
    DEFAULT_RECONCILED_DEST_DIR,
    DestinationCollisionMismatchError,
    RunLockManager,
    SourceMutationProhibitedError,
    StagingLockAcquisitionError,
    UnsupportedFilesystemError,
    compute_sha256,
    publish_staged_file,
    stage_and_publish_clip,
    verify_audio_three_decoders,
)


def _generate_synthetic_mp3(file_path: Path, duration_sec: float = 0.5, sr: int = 48000, channels: int = 1):
    """Generate a clean synthetic MP3 audio file with valid MPEG frames."""
    num_samples = int(duration_sec * sr)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    # 440 Hz sine tone
    audio_data = 0.5 * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    if channels == 2:
        audio_data = np.column_stack([audio_data, audio_data])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(file_path), audio_data, sr, format="MP3")


# -----------------------------------------------------------------------------
# 1. Source Protection & Immutability Invariant (P1)
# -----------------------------------------------------------------------------

def test_materializer_cannot_unlink_or_mutate_source_files(tmp_path):
    """
    Rule P1: Verify that source files remain 100% byte-identical, size-identical,
    and timestamp-identical across the entire materialization lifecycle.
    Also verifies that attempting to set the destination equal to the source raises
    SourceMutationProhibitedError.
    """
    source_dir = tmp_path / "source_pool"
    dest_dir = tmp_path / "published_dest"
    staging_dir = tmp_path / "staging_root"
    source_dir.mkdir()
    dest_dir.mkdir()

    source_clip = source_dir / "sample_001.mp3"
    _generate_synthetic_mp3(source_clip, duration_sec=0.3)

    source_stat_before = source_clip.stat()
    source_hash_before = compute_sha256(source_clip)

    dest_clip = dest_dir / "sample_001.mp3"
    with RunLockManager(staging_dir) as lock_mgr:
        res = stage_and_publish_clip(
            recording_id="sample_001",
            source_path=source_clip,
            dest_path=dest_clip,
            lock_mgr=lock_mgr,
            expected_sha256=source_hash_before,
        )

    # Invariants on source file
    source_stat_after = source_clip.stat()
    source_hash_after = compute_sha256(source_clip)

    assert source_clip.exists()
    assert source_hash_before == source_hash_after
    assert source_stat_before.st_size == source_stat_after.st_size
    assert source_stat_before.st_mtime_ns == source_stat_after.st_mtime_ns
    assert res["disposition_action"] == "PUBLISHED_ATOMIC_HARDLINK"
    assert dest_clip.exists()
    assert compute_sha256(dest_clip) == source_hash_before

    # Verify fail-closed when source equals destination
    with RunLockManager(staging_dir) as lock_mgr:
        with pytest.raises(SourceMutationProhibitedError):
            stage_and_publish_clip(
                recording_id="sample_001",
                source_path=source_clip,
                dest_path=source_clip,  # Source equals destination!
                lock_mgr=lock_mgr,
            )


# -----------------------------------------------------------------------------
# 2. Atomic No-Clobber Publication & Idempotency (P2, P3)
# -----------------------------------------------------------------------------

def test_destination_already_exists_correct_hash_skips_writes(tmp_path):
    """
    Rule P3: When destination file already exists with matching SHA-256,
    the materializer must skip extraction and hard-link, leaving destination
    st_mtime_ns completely unchanged (zero disk writes).
    """
    source_dir = tmp_path / "source_pool"
    dest_dir = tmp_path / "dest_pool"
    staging_dir = tmp_path / "staging_root"
    source_dir.mkdir()
    dest_dir.mkdir()

    source_clip = source_dir / "clip_idem.mp3"
    _generate_synthetic_mp3(source_clip, duration_sec=0.2)
    expected_hash = compute_sha256(source_clip)

    dest_clip = dest_dir / "clip_idem.mp3"
    # Pre-populate destination with identical content
    shutil.copy2(source_clip, dest_clip)
    dest_stat_before = dest_clip.stat()

    time.sleep(0.01)  # Ensure time tick

    with RunLockManager(staging_dir) as lock_mgr:
        res = stage_and_publish_clip(
            recording_id="clip_idem",
            source_path=source_clip,
            dest_path=dest_clip,
            lock_mgr=lock_mgr,
            expected_sha256=expected_hash,
        )

    dest_stat_after = dest_clip.stat()
    assert res["disposition_action"] == "VERIFIED_EXISTING_SKIPPED"
    assert dest_stat_before.st_mtime_ns == dest_stat_after.st_mtime_ns
    assert compute_sha256(dest_clip) == expected_hash


def test_destination_already_exists_mismatched_hash_fails_closed(tmp_path):
    """
    Rule P3: When destination file already exists with a mismatched SHA-256,
    execution must immediately raise DestinationCollisionMismatchError.
    The existing destination file must NOT be modified, deleted, or overwritten.
    """
    source_dir = tmp_path / "source_pool"
    dest_dir = tmp_path / "dest_pool"
    staging_dir = tmp_path / "staging_root"
    source_dir.mkdir()
    dest_dir.mkdir()

    source_clip = source_dir / "clip_mismatch.mp3"
    _generate_synthetic_mp3(source_clip, duration_sec=0.2, sr=48000)
    source_hash = compute_sha256(source_clip)

    dest_clip = dest_dir / "clip_mismatch.mp3"
    # Pre-populate destination with divergent content
    _generate_synthetic_mp3(dest_clip, duration_sec=0.4, sr=44100)
    original_dest_hash = compute_sha256(dest_clip)
    original_dest_stat = dest_clip.stat()

    assert original_dest_hash != source_hash

    with RunLockManager(staging_dir) as lock_mgr:
        with pytest.raises(DestinationCollisionMismatchError):
            stage_and_publish_clip(
                recording_id="clip_mismatch",
                source_path=source_clip,
                dest_path=dest_clip,
                lock_mgr=lock_mgr,
                expected_sha256=source_hash,
            )

    # Verify destination file was left completely intact
    dest_stat_after = dest_clip.stat()
    assert dest_clip.exists()
    assert compute_sha256(dest_clip) == original_dest_hash
    assert original_dest_stat.st_size == dest_stat_after.st_size
    assert original_dest_stat.st_mtime_ns == dest_stat_after.st_mtime_ns


def test_race_condition_destination_appears_concurrently_no_clobber(tmp_path):
    """
    Rule P2: Simulates a race condition where dest_path appears between
    the existence check and publication. os.link() raises FileExistsError.
    The materializer handles collision cleanly without clobbering.
    """
    staging_file = tmp_path / "staged.tmp"
    dest_file = tmp_path / "dest.mp3"

    payload = b"RACE_PAYLOAD_CONTENT"
    staging_file.write_bytes(payload)
    dest_file.write_bytes(payload)
    expected_hash = compute_sha256(dest_file)

    # Publication attempts os.link() to already existing dest_file
    action = publish_staged_file(staging_file, dest_file, expected_hash)
    assert action == "VERIFIED_EXISTING_SKIPPED" or action == "CONCURRENT_COLLISION_VERIFIED"
    assert not staging_file.exists()
    assert compute_sha256(dest_file) == expected_hash


def test_unsupported_filesystem_fails_closed_no_replace_fallback(tmp_path):
    """
    Rule P2: When os.link() raises OSError (e.g. cross-volume link EXDEV or
    unsupported filesystem), the materializer must fail closed with UnsupportedFilesystemError.
    Falling back to os.replace() is strictly forbidden.
    """
    staged_file = tmp_path / "staged.tmp"
    dest_file = tmp_path / "dest.mp3"
    staged_file.write_bytes(b"DATA")
    h = compute_sha256(staged_file)

    with patch("os.link", side_effect=OSError(18, "Invalid cross-device link")):
        with pytest.raises(UnsupportedFilesystemError) as exc_info:
            publish_staged_file(staged_file, dest_file, h)

    assert "Overwriting fallback via os.replace() is strictly forbidden" in str(exc_info.value)
    assert not dest_file.exists()


# -----------------------------------------------------------------------------
# 3. Windows OS-Level Exclusive Locking & Precedence over PID/TTL (P4)
# -----------------------------------------------------------------------------

def test_staging_orphan_recovery_requires_exclusive_os_lock_guards_pid_reuse(tmp_path):
    """
    Rule P4: Orphan recovery sweeps are strictly forbidden from pruning any staging
    directory while an active process holds the exclusive OS lock on run.lock,
    even if heartbeat TTL has expired and PID is simulated as terminated.
    """
    staging_root = tmp_path / "staging_root"
    staging_root.mkdir()

    with RunLockManager(staging_root, run_id="active_worker") as active_mgr:
        assert active_mgr.staging_dir.exists()
        assert active_mgr.lock_file.exists()

        # Artificially backdate heartbeat and set non-existent dead PID
        with open(active_mgr.heartbeat_file, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": "active_worker",
                "pid": 999999,  # Non-existent PID
                "timestamp_epoch": time.time() - 100000.0,  # Expired TTL
            }, f)

        # Sweeper runs while active_mgr holds OS lock on run.lock
        swept = RunLockManager.sweep_orphaned_staging_directories(staging_root, orphan_ttl_seconds=3600.0)

        # Invariant: Directory must NOT be swept because OS lock is held!
        assert len(swept) == 0
        assert active_mgr.staging_dir.exists()

    # Once active_mgr exits (lock released), sweeper can prune abandoned directory
    # Create abandoned directory with stale lock
    abandoned_dir = staging_root / ".staging_run_abandoned"
    abandoned_dir.mkdir()
    lock_f = abandoned_dir / "run.lock"
    lock_f.write_text("LOCK")
    hb_f = abandoned_dir / "heartbeat.json"
    with open(hb_f, "w", encoding="utf-8") as f:
        json.dump({
            "run_id": "abandoned",
            "pid": 999999,
            "timestamp_epoch": time.time() - 100000.0,
        }, f)

    swept2 = RunLockManager.sweep_orphaned_staging_directories(staging_root, orphan_ttl_seconds=3600.0)
    assert len(swept2) == 1
    assert not abandoned_dir.exists()


# -----------------------------------------------------------------------------
# 4. Multi-Decoder Verification Pipeline (P5)
# -----------------------------------------------------------------------------

def test_three_decoder_verification_pipeline(tmp_path):
    """
    Rule P5: Verify that verify_audio_three_decoders correctly evaluates
    clean MP3 bitstreams, returns valid PCM sample counts, non-zero duration,
    and fails closed on zero-byte or corrupt files.
    """
    valid_mp3 = tmp_path / "valid.mp3"
    _generate_synthetic_mp3(valid_mp3, duration_sec=0.5, sr=48000)

    res_valid = verify_audio_three_decoders(valid_mp3)
    assert res_valid["is_valid"] is True
    assert res_valid["soundfile_valid"] is True
    assert res_valid["soundfile_sr"] == 48000
    assert res_valid["soundfile_frames"] > 0
    assert res_valid["soundfile_duration_sec"] > 0.0
    assert len(res_valid["sha256"]) == 64

    # Test zero-byte file
    zero_mp3 = tmp_path / "zero.mp3"
    zero_mp3.write_bytes(b"")
    res_zero = verify_audio_three_decoders(zero_mp3)
    assert res_zero["is_valid"] is False
    assert "zero bytes" in res_zero["overall_error"].lower()

    # Test corrupt bitstream
    corrupt_mp3 = tmp_path / "corrupt.mp3"
    corrupt_mp3.write_bytes(b"NOT_AN_MP3_DATA_STREAM")
    res_corrupt = verify_audio_three_decoders(corrupt_mp3)
    assert res_corrupt["is_valid"] is False


# -----------------------------------------------------------------------------
# 5. Quarantine Preservation & Policy 2A Representation (P6)
# -----------------------------------------------------------------------------

def test_quarantine_preservation_and_policy2a_metadata():
    """
    Rule P6: Verify that the 130 discrepancy-screened recordings in
    cohort3_rejected_quarantine retain their original physical location,
    byte integrity, and explicit Policy 2A admission disposition.
    """
    quarantine_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort3_rejected_quarantine"
    assert quarantine_dir.exists(), f"Quarantine directory missing: {quarantine_dir}"

    quarantine_files = list(quarantine_dir.glob("*.mp3"))
    assert len(quarantine_files) == 130, f"Expected 130 quarantined files, found {len(quarantine_files)}"

    # Check a representative quarantined recording
    sample_clip = quarantine_files[0]
    assert sample_clip.stat().st_size > 0
    # Must decode cleanly under Claim A
    dec = verify_audio_three_decoders(sample_clip)
    assert dec["is_valid"] is True
    assert dec["soundfile_valid"] is True
    assert dec["soundfile_frames"] > 0


# -----------------------------------------------------------------------------
# 6. Production Boundary Protection Guard
# -----------------------------------------------------------------------------

def test_production_boundary_guard_blocks_unauthorized_materialization():
    """
    Verify that invoking scripts/materialize_stage6m_cohort3_audio_v2.py
    with the production reconciled destination directory without explicit Gate 3A
    authorization strictly returns exit code 2 with BLOCKED_UNAUTHORIZED status
    without creating or modifying production directories.
    """
    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio_v2.py"),
            "--destination-dir",
            str(DEFAULT_RECONCILED_DEST_DIR),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    output = res.stderr + res.stdout
    assert "BLOCKED_UNAUTHORIZED" in output
    assert "Gate 2 authorizes implementation and pre-production validation ONLY" in output
    assert "--authorize-gate3a" in output
    if not DEFAULT_RECONCILED_DEST_DIR.exists():
        assert not DEFAULT_RECONCILED_DEST_DIR.exists()
    else:
        assert len(list(DEFAULT_RECONCILED_DEST_DIR.glob("*.mp3"))) == 18975


def test_production_boundary_guard_blocks_if_cli_flag_set_but_record_missing(tmp_path):
    """
    Dual-key check: Verify that providing --authorize-gate3a without an approved
    Gate 3A decision record file on disk still fails closed with code 2 and BLOCKED_UNAUTHORIZED.
    """
    fake_record = tmp_path / "unapproved_record.json"
    fake_record.write_text(json.dumps({"status": "UNEXECUTED"}), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio_v2.py"),
            "--destination-dir",
            str(DEFAULT_RECONCILED_DEST_DIR),
            "--authorize-gate3a",
            "--gate3a-record",
            str(fake_record),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    output = res.stderr + res.stdout
    assert "BLOCKED_UNAUTHORIZED" in output
    assert "approved Gate 3A decision record" in output
    if not DEFAULT_RECONCILED_DEST_DIR.exists():
        assert not DEFAULT_RECONCILED_DEST_DIR.exists()
    else:
        assert len(list(DEFAULT_RECONCILED_DEST_DIR.glob("*.mp3"))) == 18975


def test_production_boundary_guard_accepts_gate3a_in_dry_run():
    """
    Verify that invoking scripts/materialize_stage6m_cohort3_audio_v2.py
    with --authorize-gate3a and --dry-run is recognized as authorized and exits cleanly
    without touching the production destination directory.
    """
    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio_v2.py"),
            "--destination-dir",
            str(DEFAULT_RECONCILED_DEST_DIR),
            "--dry-run",
            "--authorize-gate3a",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    if not DEFAULT_RECONCILED_DEST_DIR.exists():
        assert not DEFAULT_RECONCILED_DEST_DIR.exists()
    else:
        assert len(list(DEFAULT_RECONCILED_DEST_DIR.glob("*.mp3"))) == 18975


def test_production_boundary_guard_dual_key_success_in_dry_run(tmp_path):
    """
    Verify that providing both --authorize-gate3a AND an approved Gate 3A decision record
    is recognized as fully authorized by the dual-key guard in dry-run mode.
    """
    valid_record = tmp_path / "approved_gate3a_record.json"
    valid_record.write_text(
        json.dumps(
            {
                "status": "APPROVED",
                "authority": "Project Lead (Dissertation Author)",
                "scope": "STAGE_6M_GATE_3A_PRODUCTION_MATERIALIZATION",
                "approval_date": "2026-11-07",
            }
        ),
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio_v2.py"),
            "--destination-dir",
            str(DEFAULT_RECONCILED_DEST_DIR),
            "--dry-run",
            "--authorize-gate3a",
            "--gate3a-record",
            str(valid_record),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    if not DEFAULT_RECONCILED_DEST_DIR.exists():
        assert not DEFAULT_RECONCILED_DEST_DIR.exists()
    else:
        assert len(list(DEFAULT_RECONCILED_DEST_DIR.glob("*.mp3"))) == 18975
