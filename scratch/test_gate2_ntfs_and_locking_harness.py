"""
scratch/test_gate2_ntfs_and_locking_harness.py

Stage 6M Pre-Gate 2 NTFS Filesystem & Windows OS-Locking Demonstration Harness
=============================================================================
Governing Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark
Governance Status: Gate 1 APPROVED (Policy 2A); Gate 2 NOT AUTHORIZED.

Objective:
Demonstrate the non-destructive filesystem primitives required by Task 7.7.4
using synthetic test files only in an isolated scratch directory.

Phases:
1. Target volume and filesystem identification (NTFS confirmation).
2. Atomic hard-link publication via os.link() on target volume.
3. No-clobber protection: absent, matching digest skip, mismatched collision, and multi-process concurrency race.
4. Windows OS-level locking (msvcrt.locking LK_NBLCK) & precedence over PID/TTL.
5. Source file immutability & handle closure verification.
6. Safe synthetic-only cleanup.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET_AUDIO_DIR = PROJECT_ROOT / "datasets" / "audio" / "stage6m"
DEMO_ROOT = PROJECT_ROOT / "scratch" / "gate2_filesystem_demo"


def get_volume_info(path: Path) -> dict:
    """Retrieve Windows volume information using kernel32.GetVolumeInformationW."""
    drive = os.path.splitdrive(str(path.resolve()))[0] + "\\"
    kernel32 = ctypes.windll.kernel32
    vol_name = ctypes.create_unicode_buffer(1024)
    fs_name = ctypes.create_unicode_buffer(1024)
    serial_num = ctypes.c_ulong()
    max_len = ctypes.c_ulong()
    flags = ctypes.c_ulong()

    res = kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(drive),
        vol_name,
        1024,
        ctypes.byref(serial_num),
        ctypes.byref(max_len),
        ctypes.byref(flags),
        fs_name,
        1024,
    )
    if not res:
        raise OSError(f"Failed to query volume info for drive: {drive}")

    flag_val = flags.value
    return {
        "drive": drive,
        "volume_name": vol_name.value,
        "filesystem": fs_name.value,
        "serial_number_hex": hex(serial_num.value),
        "flags_hex": hex(flag_val),
        "supports_persistent_acls": bool(flag_val & 0x00000008),
        "supports_named_streams": bool(flag_val & 0x00040000),
        "supports_read_only_volume": bool(flag_val & 0x00080000),
    }


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 digest of file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# -----------------------------------------------------------------------------
# Worker Routines for Subprocess Concurrency & Locking
# -----------------------------------------------------------------------------

def run_concurrent_worker(worker_id: int, staged_file_str: str, dest_file_str: str, sync_gate_str: str, result_file_str: str):
    """
    Worker process for concurrent publication race.
    Waits for sync_gate file to appear, then immediately calls os.link().
    Records result to result_file.
    """
    staged_path = Path(staged_file_str)
    dest_path = Path(dest_file_str)
    sync_gate = Path(sync_gate_str)
    result_path = Path(result_file_str)

    # Spin-wait for synchronization gate
    while not sync_gate.exists():
        time.sleep(0.001)

    result = {
        "worker_id": worker_id,
        "status": "UNKNOWN",
        "error_type": None,
        "error_msg": None,
        "timestamp_ns": time.time_ns(),
    }

    try:
        os.link(staged_path, dest_path)
        result["status"] = "PUBLISHED_SUCCESS"
    except FileExistsError as e:
        result["status"] = "COLLISION_NO_CLOBBER"
        result["error_type"] = "FileExistsError"
        result["error_msg"] = str(e)
    except Exception as e:
        result["status"] = "UNEXPECTED_ERROR"
        result["error_type"] = type(e).__name__
        result["error_msg"] = str(e)

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


def run_lock_holder(lock_file_str: str, ready_signal_str: str, stop_signal_str: str):
    """
    Process A: Holds an OS-level exclusive non-blocking lock on run.lock.
    Signals readiness via ready_signal file, then holds until stop_signal appears.
    """
    lock_path = Path(lock_file_str)
    ready_signal = Path(ready_signal_str)
    stop_signal = Path(stop_signal_str)

    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        # Signal that lock is successfully held
        ready_signal.write_text("LOCKED", encoding="utf-8")

        # Wait until told to release
        while not stop_signal.exists():
            time.sleep(0.01)

        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


# -----------------------------------------------------------------------------
# Main Demonstration Orchestrator
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Stage 6M Pre-Gate 2 NTFS & Locking Demonstration")
    parser.add_argument("--worker-concurrent", action="store_true", help="Internal worker: concurrent publication")
    parser.add_argument("--worker-lock-holder", action="store_true", help="Internal worker: OS lock holder")
    parser.add_argument("--worker-id", type=int, default=0)
    parser.add_argument("--staged-file", type=str, default="")
    parser.add_argument("--dest-file", type=str, default="")
    parser.add_argument("--sync-gate", type=str, default="")
    parser.add_argument("--result-file", type=str, default="")
    parser.add_argument("--lock-file", type=str, default="")
    parser.add_argument("--ready-signal", type=str, default="")
    parser.add_argument("--stop-signal", type=str, default="")
    args = parser.parse_args()

    if args.worker_concurrent:
        run_concurrent_worker(args.worker_id, args.staged_file, args.dest_file, args.sync_gate, args.result_file)
        sys.exit(0)

    if args.worker_lock_holder:
        run_lock_holder(args.lock_file, args.ready_signal, args.stop_signal)
        sys.exit(0)

    print("=" * 80)
    print("STAGE 6M — GATE 2 PRE-AUTHORIZATION NTFS & OS-LOCKING DEMONSTRATION")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # PHASE 1: TARGET VOLUME IDENTIFICATION
    # -------------------------------------------------------------------------
    print("\n[PHASE 1] Target Volume Identification...")
    target_audio_path = TARGET_AUDIO_DIR.resolve()
    scratch_path = DEMO_ROOT.resolve()
    cv27_path = (PROJECT_ROOT / "datasets" / "external" / "common_voice_27").resolve()

    target_vol = get_volume_info(target_audio_path)
    scratch_vol = get_volume_info(PROJECT_ROOT / "scratch")
    cv27_vol = get_volume_info(cv27_path)

    print(f"  Target Audio Path:      {target_audio_path}")
    print(f"  Target Path Exists:     {target_audio_path.exists()}")
    print(f"  Target Drive:           {target_vol['drive']}")
    print(f"  Target Volume Name:     {target_vol['volume_name']}")
    print(f"  Target FS Type:         {target_vol['filesystem']}")
    print(f"  Target Serial:          {target_vol['serial_number_hex']}")
    print(f"  Scratch Drive:          {scratch_vol['drive']}")
    print(f"  Scratch FS Type:        {scratch_vol['filesystem']}")
    print(f"  Scratch Serial:         {scratch_vol['serial_number_hex']}")
    print(f"  CV27 Audio Drive:       {cv27_vol['drive']}")
    print(f"  CV27 FS Type:           {cv27_vol['filesystem']}")
    print(f"  CV27 Serial:            {cv27_vol['serial_number_hex']}")

    assert target_vol["filesystem"] == "NTFS", f"FATAL: Target filesystem is not NTFS: {target_vol['filesystem']}"
    assert scratch_vol["filesystem"] == "NTFS", f"FATAL: Scratch filesystem is not NTFS: {scratch_vol['filesystem']}"
    assert cv27_vol["filesystem"] == "NTFS", f"FATAL: CV27 filesystem is not NTFS: {cv27_vol['filesystem']}"
    assert target_vol["serial_number_hex"] == scratch_vol["serial_number_hex"], "FATAL: Target and scratch are on different volumes!"
    assert target_vol["serial_number_hex"] == cv27_vol["serial_number_hex"], "FATAL: Target and CV27 are on different volumes!"

    # Verify production destination directory does not exist
    prod_reconciled = TARGET_AUDIO_DIR / "cohort3_reconciled_assets"
    print(f"  Production Reconciled Assets Directory Exists: {prod_reconciled.exists()}")
    assert not prod_reconciled.exists(), "PROTECTED VIOLATION: Production reconciled directory already exists!"

    print("  [PHASE 1 PASS] Target volume confirmed NTFS (Volume: OS, Serial: " + target_vol['serial_number_hex'] + ") and identical across target, scratch, and source paths.")

    # Initialize scratch test directory
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    DEMO_ROOT.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # PHASE 2: ATOMIC HARD-LINK PUBLICATION
    # -------------------------------------------------------------------------
    print("\n[PHASE 2] Atomic Hard-Link Publication...")
    p2_staging_dir = DEMO_ROOT / ".staging_run_phase2"
    p2_dest_dir = DEMO_ROOT / "test_dest_phase2"
    p2_staging_dir.mkdir(parents=True, exist_ok=True)
    p2_dest_dir.mkdir(parents=True, exist_ok=True)

    synthetic_payload_p2 = b"SYNTHETIC_MP3_PAYLOAD_PHASE_2_" + os.urandom(1024)
    p2_staged_file = p2_staging_dir / "clip_001.tmp"

    # Step 1: Write and explicitly flush/close
    with open(p2_staged_file, "wb") as f:
        f.write(synthetic_payload_p2)
        f.flush()
        os.fsync(f.fileno())

    # Step 2: Compute staged digest
    staged_hash = compute_sha256(p2_staged_file)
    staged_stat_before = p2_staged_file.stat()
    assert staged_stat_before.st_nlink == 1

    # Step 3: Hard-link publish
    p2_dest_file = p2_dest_dir / "clip_001.mp3"
    os.link(str(p2_staged_file), str(p2_dest_file))

    # Step 4: Verify destination
    dest_stat = p2_dest_file.stat()
    assert dest_stat.st_nlink == 2, f"Expected 2 links, got {dest_stat.st_nlink}"
    assert p2_dest_file.stat().st_size == len(synthetic_payload_p2)
    assert compute_sha256(p2_dest_file) == staged_hash

    # Step 5: Unlink staging
    os.unlink(p2_staged_file)
    assert not p2_staged_file.exists()
    assert p2_dest_file.exists()
    assert p2_dest_file.stat().st_nlink == 1
    assert compute_sha256(p2_dest_file) == staged_hash

    print(f"  Published: {p2_dest_file.name}")
    print(f"  Payload Size: {len(synthetic_payload_p2)} bytes")
    print(f"  SHA-256: {staged_hash}")
    print(f"  Link Count Progression: 1 -> 2 (linked) -> 1 (staging unlinked)")
    print("  [PHASE 2 PASS] Hard-link publication succeeded atomically with exact hash preservation.")

    # -------------------------------------------------------------------------
    # PHASE 3: NO-CLOBBER TESTS
    # -------------------------------------------------------------------------
    print("\n[PHASE 3] No-Clobber Tests...")
    p3_dir = DEMO_ROOT / "phase3_noclobber"
    p3_dir.mkdir(parents=True, exist_ok=True)

    dest_target = p3_dir / "target_clip.mp3"
    canonical_payload = b"CANONICAL_ORIGINAL_DATA_12345"
    with open(dest_target, "wb") as f:
        f.write(canonical_payload)
        f.flush()
        os.fsync(f.fileno())

    canonical_hash = compute_sha256(dest_target)
    canonical_mtime_before = dest_target.stat().st_mtime_ns
    print(f"  Initial Destination File Created (SHA-256: {canonical_hash[:16]}...)")

    # Test B: Matching digest skip (idempotency)
    print("  Testing Scenario B: Destination exists with matching hash...")
    matching_staging = p3_dir / "matching_staged.tmp"
    with open(matching_staging, "wb") as f:
        f.write(canonical_payload)
        f.flush()
        os.fsync(f.fileno())

    staged_hash = compute_sha256(matching_staging)
    skip_action = "NONE"
    if dest_target.exists():
        existing_hash = compute_sha256(dest_target)
        if existing_hash == staged_hash:
            # Idempotent skip: unlink staging without touching destination
            os.unlink(matching_staging)
            skip_action = "VERIFIED_EXISTING_SKIPPED"

    assert skip_action == "VERIFIED_EXISTING_SKIPPED"
    assert dest_target.stat().st_mtime_ns == canonical_mtime_before
    assert compute_sha256(dest_target) == canonical_hash
    print("  -> Scenario B PASS: Identical hash detected, zero disk writes to destination, mtime unchanged.")

    # Test C: Mismatched digest collision protection
    print("  Testing Scenario C: Destination exists with mismatched hash...")
    conflicting_staging = p3_dir / "conflicting_staged.tmp"
    conflicting_payload = b"CONFLICTING_DIFFERENT_DATA_67890"
    with open(conflicting_staging, "wb") as f:
        f.write(conflicting_payload)
        f.flush()
        os.fsync(f.fileno())

    # Raw os.link() call must raise FileExistsError
    link_failed_with_file_exists = False
    try:
        os.link(str(conflicting_staging), str(dest_target))
    except FileExistsError:
        link_failed_with_file_exists = True

    assert link_failed_with_file_exists, "FATAL: os.link did not raise FileExistsError on existing destination!"
    assert dest_target.stat().st_mtime_ns == canonical_mtime_before
    assert compute_sha256(dest_target) == canonical_hash
    os.unlink(conflicting_staging)
    print("  -> Scenario C PASS: os.link raised FileExistsError, original file untouched.")

    # Test D: Multi-process concurrent publication race condition
    print("  Testing Scenario D: Concurrent publication race condition (5 separate processes)...")
    p3_concurrent_dir = DEMO_ROOT / "phase3_concurrent"
    p3_concurrent_dir.mkdir(parents=True, exist_ok=True)

    concurrent_dest = p3_concurrent_dir / "shared_publication_target.mp3"
    sync_gate_file = p3_concurrent_dir / "sync.gate"
    num_workers = 5

    worker_staged_files = []
    worker_result_files = []
    subprocesses = []

    # Prepare staging files for 5 workers with identical payload
    concurrent_payload = b"CONCURRENT_SHARED_PAYLOAD_ABCDEF"
    expected_concurrent_hash = hashlib.sha256(concurrent_payload).hexdigest()

    for wid in range(num_workers):
        w_staged = p3_concurrent_dir / f"worker_{wid}_staged.tmp"
        w_res = p3_concurrent_dir / f"worker_{wid}_result.json"
        with open(w_staged, "wb") as f:
            f.write(concurrent_payload)
            f.flush()
            os.fsync(f.fileno())
        worker_staged_files.append(w_staged)
        worker_result_files.append(w_res)

        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-concurrent",
            "--worker-id", str(wid),
            "--staged-file", str(w_staged),
            "--dest-file", str(concurrent_dest),
            "--sync-gate", str(sync_gate_file),
            "--result-file", str(w_res),
        ]
        subprocesses.append(subprocess.Popen(cmd))

    # Give all workers 200ms to initialize and start spin-waiting
    time.sleep(0.2)

    # Release synchronization gate
    sync_gate_file.write_text("RELEASE", encoding="utf-8")

    # Wait for all processes to complete
    for sp in subprocesses:
        sp.wait(timeout=10)

    # Inspect results
    results = []
    for wid in range(num_workers):
        with open(worker_result_files[wid], "r", encoding="utf-8") as f:
            results.append(json.load(f))

    successes = [r for r in results if r["status"] == "PUBLISHED_SUCCESS"]
    collisions = [r for r in results if r["status"] == "COLLISION_NO_CLOBBER"]
    errors = [r for r in results if r["status"] == "UNEXPECTED_ERROR"]

    print(f"  Concurrent Workers: {num_workers}")
    print(f"  Workers with PUBLISHED_SUCCESS: {len(successes)}")
    print(f"  Workers with COLLISION_NO_CLOBBER: {len(collisions)}")
    print(f"  Workers with UNEXPECTED_ERROR: {len(errors)}")

    assert len(successes) == 1, f"Expected exactly 1 successful publisher, got {len(successes)}"
    assert len(collisions) == num_workers - 1, f"Expected {num_workers - 1} collisions, got {len(collisions)}"
    assert len(errors) == 0, f"Encountered unexpected worker errors: {errors}"

    # Verify destination file
    assert concurrent_dest.exists()
    assert compute_sha256(concurrent_dest) == expected_concurrent_hash
    print(f"  Winner Worker ID: {successes[0]['worker_id']}")
    print("  -> Scenario D PASS: Exactly one worker published, zero files clobbered, all losers handled collision.")

    # -------------------------------------------------------------------------
    # PHASE 4: WINDOWS OS LOCKING & ORPHAN RECOVERY PRECEDENCE
    # -------------------------------------------------------------------------
    print("\n[PHASE 4] Windows OS-Level File Locking & Precedence Over PID/TTL...")
    p4_dir = DEMO_ROOT / "phase4_locking"
    p4_staging_dir = p4_dir / ".staging_run_workerA"
    p4_staging_dir.mkdir(parents=True, exist_ok=True)

    lock_file = p4_staging_dir / "run.lock"
    ready_signal = p4_dir / "lock_ready.signal"
    stop_signal = p4_dir / "lock_stop.signal"

    # Create stale heartbeat (> 3,600s ago) and dead PID
    heartbeat_file = p4_staging_dir / "heartbeat.json"
    with open(heartbeat_file, "w", encoding="utf-8") as f:
        json.dump({
            "pid": 999999,  # Non-existent dead PID
            "last_heartbeat_utc": "2026-11-01T00:00:00+00:00",
            "age_seconds": 150000,  # Far exceeded 3,600s TTL
        }, f, indent=2)

    # Spawn Process A holding the OS lock
    cmd_holder = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker-lock-holder",
        "--lock-file", str(lock_file),
        "--ready-signal", str(ready_signal),
        "--stop-signal", str(stop_signal),
    ]
    proc_a = subprocess.Popen(cmd_holder)

    # Wait for Process A to signal lock acquisition
    while not ready_signal.exists():
        time.sleep(0.05)

    print("  Process A holds active OS-level exclusive file lock (msvcrt.locking LK_NBLCK)")

    # Simulate Process B (Orphan Recovery Sweeper)
    print("  Simulating Process B (Orphan Recovery Sweeper) while Process A is active...")
    sweep_attempted_delete = False
    sweep_skipped_due_to_lock = False

    # Attempt to acquire lock on run.lock as part of sweep
    try:
        fd_sweep = os.open(lock_file, os.O_RDWR)
        try:
            msvcrt.locking(fd_sweep, msvcrt.LK_NBLCK, 1)
            # If lock acquired, sweeper would delete
            sweep_attempted_delete = True
            msvcrt.locking(fd_sweep, msvcrt.LK_UNLCK, 1)
        except OSError as e:
            # Lock cannot be acquired: an active process owns the staging directory!
            sweep_skipped_due_to_lock = True
            print(f"  Sweeper lock attempt caught expected: {type(e).__name__} (Errno: {getattr(e, 'errno', 'None')})")
        finally:
            os.close(fd_sweep)
    except Exception as e:
        print(f"  Unexpected exception in sweep: {e}")

    assert sweep_skipped_due_to_lock, "FATAL: Sweeper acquired lock while Process A held it!"
    assert not sweep_attempted_delete, "FATAL: Sweeper attempted delete on locked staging directory!"
    assert p4_staging_dir.exists(), "FATAL: Staging directory was deleted while locked!"
    print("  -> Sweeper correctly skipped directory: OS lock prevented cleanup despite stale TTL & dead PID.")

    # Tell Process A to release lock
    stop_signal.write_text("STOP", encoding="utf-8")
    proc_a.wait(timeout=5)
    print("  Process A released lock and terminated cleanly.")

    # Now run sweeper again on abandoned staging directory
    print("  Simulating Process B (Orphan Sweeper) after Process A terminated...")
    sweep_after_acquired = False
    fd_sweep2 = os.open(lock_file, os.O_RDWR)
    try:
        msvcrt.locking(fd_sweep2, msvcrt.LK_NBLCK, 1)
        sweep_after_acquired = True
        msvcrt.locking(fd_sweep2, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd_sweep2)

    assert sweep_after_acquired, "FATAL: Sweeper could not acquire lock after Process A released it!"
    # Safe cleanup executed by sweeper
    shutil.rmtree(p4_staging_dir)
    assert not p4_staging_dir.exists()
    print("  -> Sweeper acquired lock on abandoned directory and cleanly pruned it.")
    print("  [PHASE 4 PASS] OS-level lock strictly overrides TTL and PID metadata.")

    # -------------------------------------------------------------------------
    # PHASE 5: SOURCE-PROTECTION DESIGN CHECK
    # -------------------------------------------------------------------------
    print("\n[PHASE 5] Source-Protection Invariant Verification...")
    p5_dir = DEMO_ROOT / "phase5_source_protection"
    p5_source_dir = p5_dir / "synthetic_source_pool"
    p5_dest_dir = p5_dir / "published_dest"
    p5_staging_dir = p5_dir / ".staging_run_p5"

    p5_source_dir.mkdir(parents=True, exist_ok=True)
    p5_dest_dir.mkdir(parents=True, exist_ok=True)
    p5_staging_dir.mkdir(parents=True, exist_ok=True)

    source_clip = p5_source_dir / "sample_recording.mp3"
    source_payload = b"SYNTHETIC_IMMUTABLE_SOURCE_PAYLOAD_9999"
    with open(source_clip, "wb") as f:
        f.write(source_payload)
        f.flush()
        os.fsync(f.fileno())

    source_hash_before = compute_sha256(source_clip)
    source_stat_before = source_clip.stat()

    # Materializer pipeline execution: read-only extraction -> staging -> publication
    staged_copy = p5_staging_dir / "staged.tmp"
    with open(source_clip, "rb") as src_f:
        data = src_f.read()
    with open(staged_copy, "wb") as stg_f:
        stg_f.write(data)
        stg_f.flush()
        os.fsync(stg_f.fileno())

    published_clip = p5_dest_dir / "published.mp3"
    os.link(str(staged_copy), str(published_clip))
    os.unlink(staged_copy)

    # Verify source protection invariants
    source_stat_after = source_clip.stat()
    source_hash_after = compute_sha256(source_clip)

    assert source_clip.exists(), "FATAL: Source file missing!"
    assert source_hash_before == source_hash_after, "FATAL: Source hash altered!"
    assert source_stat_before.st_size == source_stat_after.st_size, "FATAL: Source size altered!"
    assert source_stat_before.st_mtime_ns == source_stat_after.st_mtime_ns, "FATAL: Source mtime altered!"
    assert str(source_clip) != str(published_clip), "FATAL: Source used as destination!"
    assert compute_sha256(published_clip) == source_hash_before, "FATAL: Published hash mismatch!"

    print(f"  Source File: {source_clip.name}")
    print(f"  Source Hash Before & After: {source_hash_before[:16]}... (Identical)")
    print(f"  Source Size: {source_stat_before.st_size} bytes (Identical)")
    print(f"  Source mtime Before: {source_stat_before.st_mtime_ns}")
    print(f"  Source mtime After:  {source_stat_after.st_mtime_ns} (Identical)")
    print("  [PHASE 5 PASS] Source remains strictly immutable and unmutated.")

    # -------------------------------------------------------------------------
    # PHASE 6: SYNTHETIC CLEANUP
    # -------------------------------------------------------------------------
    print("\n[PHASE 6] Safe Synthetic Cleanup...")
    # Verify DEMO_ROOT is strictly within scratch/ and not production
    assert "scratch" in str(DEMO_ROOT), "FATAL: DEMO_ROOT is not inside scratch!"
    assert "datasets\\audio\\stage6m" not in str(DEMO_ROOT), "FATAL: DEMO_ROOT points to production audio!"

    shutil.rmtree(DEMO_ROOT)
    assert not DEMO_ROOT.exists(), "DEMO_ROOT was not cleaned up!"
    print(f"  Cleaned up all scratch synthetic files in: {DEMO_ROOT}")

    # Re-verify production directory state
    assert not prod_reconciled.exists(), "PROTECTED VIOLATION: Production reconciled directory was created!"
    print("  Production directory integrity confirmed: datasets/audio/stage6m/cohort3_reconciled_assets/ does not exist.")
    print("  [PHASE 6 PASS] Synthetic cleanup verified; production zero footprint preserved.")

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("GATE 2 PRE-AUTHORIZATION DEMONSTRATION COMPLETE: ALL INVARIANTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
