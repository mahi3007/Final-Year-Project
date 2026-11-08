# Stage 6M Task 7.7.4 Non-Destructive Dataset Materialization & Verification Architecture Specification

**Document ID:** `STAGE6M_TASK774_NON_DESTRUCTIVE_MATERIALIZATION_SPEC`<br>
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)<br>
**Governing Branch / Base Commit:** `stage6m-five-stratum-parity` @ [`baee3b8`](https://github.com/mahi3007/Final-Year-Project/commit/baee3b8381389ffde38e907dc137623748c254a8)<br>
**Document Status:** **APPROVED_ENGINEERING_SPECIFICATION (Gate 2 Approved for Implementation & Pre-Production Validation)**<br>
**Project Lead:** Venkata Akhil Kumar<br>
**Timestamp (UTC):** 2026-11-07T14:06:12.122945+00:00<br>

> [!WARNING]
> **Authoritative Notice:** This document is the approved engineering specification for Task 7.7.4. Gate 2 formally authorizes implementation of scripts/materialize_stage6m_cohort3_audio_v2.py and pre-production validation. Zero physical audio promotion, mutation, or copying of real recordings is authorized under Gate 2. Production dataset finalization, reconciliation into datasets/audio/stage6m/cohort3_reconciled_assets/, and final manifest locking remain strictly governed under Gate 3.

---

## 1. Forensic Audit of Legacy Production Materializer

**Source Component:** `scripts/materialize_stage6m_cohort3_audio.py`  
**Audit Objective:** Identify every destructive, overwriting, or unsafe operation in the legacy production materializer.

### Identified Critical Flaws & Destructive Failure Modes

| Flaw Identifier | Code Location | Severity | Vulnerability Mechanism | Architectural Remediation |
| :--- | :--- | :---: | :--- | :--- |
| **DESTRUCTIVE_UNLINK_ON_FAILURE** | `Line 1049: dest_file.unlink(missing_ok=True)` | **CRITICAL / DESTRUCTIVE** | When validate_audio_file() returns False, the script immediately unlinks (deletes) dest_file from disk. If rerun against existing files that fail the legacy 1,152-sample threshold, it permanently deletes them from the filesystem without creating a forensic backup. | Strict prohibition of unlink() on extracted files; route invalid files to forensic isolation without deleting source or destination. |
| **DIRECT_IN_PLACE_OVERWRITE** | `Line 1011: with open(dest_file, 'wb') as out_f:` | **HIGH / DATA INTEGRITY RISK** | Extracted audio streams are written directly to the target filename dest_file without atomic staging. If the extraction stream drops (e.g. HTTP disconnect, network timeout, thread failure), a partial, corrupt MP3 file is left at the destination path with no rollback. | Mandatory atomic staging via temporary files (.tmp.{rec_id}.mp3) with complete checksum validation prior to os.replace(). |
| **SAMPLING_RATE_UNAWARE_PADDING_THRESHOLD** | `Line 394: MAX_MP3_PADDING_FRAMES = 1152` | **HIGH / FALSE REJECTION RISK** | The script enforces a fixed threshold of 1,152 sample frames across all files regardless of sampling rate, treating any shortfall Delta > 1152 as bitstream truncation. For 44.1 kHz (26.12 ms) and 32 kHz (36.00 ms) files, ID3 container metadata sizing artifacts naturally induce shortfalls of 1,296 to 2,979 frames (30.0 to 67.5 ms). This incorrectly caused 130 perfectly decodable clips to be rejected. | Decouple current-file physical decodability (Claim A) from metadata container duration estimation discrepancies. |
| **ABSENCE_OF_IDEMPOTENT_RESUME** | `Lines 1000-1016` | **MEDIUM / I/O INEFFICIENCY & INTEGRITY HAZARD** | The legacy script does not verify existing destination files against authoritative SHA-256 hashes before opening them for writing. An accidental rerun can overwrite already validated files. | Idempotent pre-check: if dest_file exists and matches ledger SHA-256, skip re-extraction. |

---

## 2. Non-Destructive Replacement Architecture

To replace the unsafe operations identified in Section 1, Task 7.7.4 establishes a robust, non-destructive, atomic materialization architecture governed by five core principles:

### P1_READ_ONLY_SOURCE_ACCESS: Strict Read-Only Source Access
The source archives (tar.gz) and existing quarantine audio directory (cohort3_rejected_quarantine) must be mounted and accessed with read-only permissions. Zero mutation, deletion, or renaming of source files is permitted.

### P2_ATOMIC_NO_CLOBBER_PUBLICATION: Atomic No-Clobber Publication via Hard-Link & Process-Isolated Staging
Audio files must be written to an isolated, run-specific staging directory: dest_dir / f'.staging_run_{run_id}/' (where run_id encodes process PID, timestamp, and a 128-bit UUID). Individual staging files use full 128-bit UUIDs: staging_dir / f'{recording_id}_{uuid.uuid4().hex}.tmp' opened with os.O_CREAT | os.O_EXCL | os.O_WRONLY. In the event of an O_EXCL collision, the materializer executes a bounded retry loop (up to 5 attempts with exponential backoff) with a fresh UUID. Full cryptographic SHA-256 verification and multi-decoder PCM decodability must pass before publication. Final publication MUST be executed using same-filesystem atomic hard-linking: os.link(temp_path, dest_path) followed by os.unlink(temp_path). Under POSIX and Windows NTFS, os.link() atomically fails with FileExistsError if dest_path already exists, guaranteeing that existing files CANNOT be overwritten or clobbered. The use of os.replace() is STRICTLY FORBIDDEN because os.replace() unconditionally replaces any existing destination file, introducing an unsafe race condition if another process creates dest_path concurrently between the existence check and publication.

### P3_IDEMPOTENT_EXISTENCE_VERIFICATION: Idempotent Digest Verification & Fail-Closed Mismatch Handling
If dest_dir / f'{recording_id}.mp3' already exists on disk prior to staging, the materializer computes its SHA-256 digest. If the hash matches the ledger, the file is validated and skipped with zero disk writes. If the hash mismatches, execution immediately fails closed (DestinationCollisionMismatchError) without modifying, overwriting, or deleting the existing file.

### P4_ISOLATED_DESTINATION_STRUCTURE: Isolated Reconciled Target Directory & OS-Level Ownership-Locked Orphan Sweep
Materialized assets are directed to an isolated, dedicated directory (datasets/audio/stage6m/cohort3_reconciled_assets/). Staging occurs strictly within dedicated, run-specific directories: dest_dir / f'.staging_run_{run_id}/'. To prevent accidental deletion of active staging directories during multi-process execution, PID and heartbeat TTL checks alone are NOT sufficient: PID reuse and delayed heartbeats can cause an active process to be mistaken for an orphan. Each materializer process creates a dedicated lockfile (run.lock) inside its staging directory and acquires an OS-level exclusive file lock (msvcrt.locking with LK_NBLCK on Windows; fcntl.flock with LOCK_EX | LOCK_NB on POSIX) for the entire duration of the run. Orphan recovery sweeps are strictly forbidden from pruning any staging directory unless: (1) an exclusive OS-level file lock is successfully acquired on run.lock (proving no running process holds it); (2) the heartbeat timestamp exceeds the safe orphan TTL (> 3,600s); and (3) PID inspection confirms the process is terminated. If the OS lock cannot be acquired, an active concurrent process holds the directory and the sweep immediately skips it.

### P5_EXPLICIT_PER_FILE_DISPOSITION_RECORD: Explicit Disposition Ledger
Every audio file processed must receive an explicit cryptographic and forensic entry in a disposition ledger (stage6m_cohort3_materialization_disposition_ledger.csv) recording its source, destination, size, SHA-256, duration, sample rate, channels, PCM frame count, container frame count, Delta, and scientific admission disposition.

### Step-by-Step Materialization Sequence

- Step 1: Ingest authoritative provisional manifest (18,975 records).
- Step 2: Initialize read-only source reader (accessing remote tar.gz and local quarantine inventory).
- Step 3: Check if destination file dest_path already exists. If yes: compute SHA-256. If matching: mark VERIFIED_EXISTING_SKIPPED and proceed to next clip. If mismatch: fail closed immediately.
- Step 4: Initialize run-specific staging directory: dest_dir / f'.staging_run_{run_id}/'. Create run.lock and acquire an OS-level exclusive file lock (msvcrt.locking on Windows / fcntl.flock on POSIX), held open throughout process lifetime.
- Step 5: Generate unique staging path with full 128-bit UUID: staging_dir / f'{rec_id}_{uuid.uuid4().hex}.tmp'. Open with os.O_CREAT | os.O_EXCL | os.O_WRONLY (retry loop on collision).
- Step 6: Extract audio bitstream into temporary staging file.
- Step 7: Compute SHA-256 digest of staging file and verify against ledger digest.
- Step 8: Execute multi-decoder PCM decodability test (SoundFile, PyAV, miniaudio) ensuring bitstream integrity.
- Step 9: Atomic no-clobber publication: execute os.link(temp_path, dest_path). If FileExistsError is raised (concurrent creation): unlink temp_path, verify dest_path SHA-256 (if matching, treat as verified concurrent; if mismatch, fail closed). Once linked, call os.unlink(temp_path).
- Step 10: Filesystem capability check: if os.link() raises OSError (e.g. cross-volume link EXDEV or unsupported filesystem), fail closed immediately (UnsupportedFilesystemError); NEVER fall back to os.replace() or file overwrite.
- Step 11: Append cryptographic entry to disposition ledger.
- Step 12: Emit final materialization report and cryptographic verification manifest; release lock, remove run.lock, and cleanly remove empty run staging directory.

---

## 3. Forensic Preservation and Representation of the 130 Quarantined Recordings

**Preservation Policy:** The 130 quarantined audio files in datasets/audio/stage6m/cohort3_rejected_quarantine/ (4,780,224 bytes, ledger LF SHA-256: 98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8) must remain physically intact in their dedicated quarantine directory as immutable forensic evidence.

### Dataset Asset Representation Under Proposed Policy 2A
- **Scientific Admission Status:** `ADMITTED_ASSET`
- **Forensic Classification:** `ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY`
- **Provenance Tracking:** In the reconciled dataset manifest, these 130 recordings are admitted as evaluation assets based on verified current-file MPEG bitstream integrity and successful PCM decoding (Claim A satisfied). However, each record carries an explicit metadata flag: origin_completeness_verified: false and container_estimation_discrepancy_frames: Delta, formally recording that upstream capture completeness (Claim B) is unverified. Current-file structural integrity and PCM decoding have been evaluated using the documented validation procedures. Original-source completeness relative to the uncompressed master recordings remains unverified for all 18,975 recordings because authoritative master references are unavailable. The 130 quarantined recordings additionally have documented duration-estimation discrepancies, which are not, by themselves, proof of physical truncation.
- **Prohibition of Silent Promotion:** Task 7.7.4 strictly forbids copying or moving quarantined files into the main directory without generating an immutable provenance record. Every admitted recording must trace directly to its quarantine ledger entry.

---

## 4. Failure Handling, Rollback Guarantees, and Idempotency

| Failure Scenario | Fault Tolerance & Recovery Mechanism | Safety Guarantee |
| :--- | :--- | :--- |
| **Destination file already exists with identical SHA-256** | Pre-check validates digest against ledger. Skip extraction and staging completely (zero disk writes). Return VERIFIED_EXISTING. | Atomicity preserved via staging file isolation. |
| **Destination file already exists with mismatched SHA-256** | Execution immediately halts with DestinationCollisionMismatchError. Destination file is NOT modified, deleted, or overwritten. | Atomicity preserved via staging file isolation. |
| **Race condition: destination file appears between check and publication** | os.link(temp_path, dest_path) atomically raises FileExistsError without modifying dest_path. Temporary staging file is unlinked. dest_path SHA-256 is checked: if matching, recorded as verified; if mismatch, execution halts with error. Zero overwriting occurs. | Atomicity preserved via staging file isolation. |
| **Filesystem does not support hard links or operation spans volumes (EXDEV)** | os.link() raises OSError. Materializer immediately fails closed (UnsupportedFilesystemError) and unlinks staging file. Falling back to os.replace() or copying over destination is strictly prohibited. | Atomicity preserved via staging file isolation. |
| **Network stream interruption or HTTP TCP reset during extraction** | ThreadedResilientGzipStream catches socket error, issues HTTP 206 Partial Content request at exact byte offset with exponential backoff (max 5 retries). Staging file is unlinked if incomplete. | Atomicity preserved via staging file isolation. |
| **SHA-256 checksum mismatch on staged file** | Staging file is immediately unlinked. No corrupt file is ever published. Error logged to failed_inventory. | Atomicity preserved via staging file isolation. |
| **PCM decoding failure or non-finite audio samples** | Staged file is moved to diagnostic isolation directory; final destination is left untouched. Failure recorded. | Atomicity preserved via staging file isolation. |
| **Temporary filename collision during exclusive creation (O_CREAT | O_EXCL)** | While a 128-bit UUID collision probability is negligible, if FileExistsError occurs on open, the materializer catches it and executes a bounded retry loop (up to 5 attempts) generating a fresh UUID with exponential backoff before failing. | Atomicity preserved via staging file isolation. |
| **Process killed mid-execution (SIGINT / SIGKILL / crash) with concurrent runs active** | Each run stages files within its dedicated directory (.staging_run_{run_id}/). To guard against PID reuse and delayed heartbeats, recovery sweeps require acquiring an exclusive OS-level file lock on run.lock (msvcrt.locking on Windows / fcntl.flock on POSIX) in non-blocking mode. If an active process is currently running, the OS kernel denies lock acquisition, guaranteeing the active directory is never touched. Pruning occurs only if the exclusive OS lock is acquired AND heartbeat TTL > 3,600s AND PID verification confirms process termination. | Atomicity preserved via staging file isolation. |

> **Rollback Guarantee:** Zero partial, corrupt, or clobbered destination files can ever exist. os.link() provides atomic no-clobber publication, guaranteeing that existing files are never replaced under any concurrency scenario.

---

## 5. Verification Test Suite Specifications

Prior to executing any production materialization, the replacement workflow must pass the following four automated safety tests:

- **`test_destination_already_exists_correct_hash_skips_writes`**: Verifies that when a destination file exists with matching ledger SHA-256, the materializer skips extraction and performs zero disk writes.
- **`test_destination_already_exists_mismatched_hash_fails_closed`**: Verifies that when a destination file exists with a mismatched hash, execution fails closed and the destination file remains completely unaltered.
- **`test_race_condition_destination_appears_concurrently_no_clobber`**: Simulates a concurrent process creating the destination file between check and publication; verifies that os.link raises FileExistsError and the destination file is never overwritten.
- **`test_unsupported_filesystem_fails_closed_no_replace_fallback`**: Simulates an OSError from os.link (unsupported hardlinks); verifies that the materializer fails closed and does NOT fall back to os.replace().
- **`test_process_crash_orphaned_staging_files_preserves_dest`**: Simulates a crash leaving orphaned .staging_*.tmp files; verifies that recovery cleans up staging files and destination/source files remain intact.
- **`test_staging_orphan_recovery_requires_exclusive_os_lock_guards_pid_reuse`**: Verifies that an active process holding an OS-level exclusive file lock on run.lock blocks orphan recovery sweeps from deleting its staging directory, even if PID inspection or heartbeat timing is simulated as expired, protecting against PID reuse.
- **`test_materializer_cannot_unlink_source_files`**: Verifies that all source files and quarantine directory files have unchanged modification times, byte counts, and SHA-256 digests after materializer run.
- **`test_quarantine_forensic_preservation_and_disposition_flagging`**: Verifies that all 130 quarantined clips carry the explicit ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY tag and exact Delta sample frame shortfalls.

---

## 6. Governance Authorization Gates & Preconditions

**Implementation Status:** `AUTHORIZED_FOR_IMPLEMENTATION_AND_VALIDATION (Gate 2 Passed; Pre-Production Only)`

### Mandatory Authorization Gates:
- Gate 1: Project Lead formal decision on Scientific Admission Policy (Policy 2A).
- Gate 2: Project Lead formal authorization of Task 7.7.4 materializer implementation and execution.
- Gate 3: Execution of materialization dry run on 10 synthetic clips and physical verification of non-destructive invariants.
- Gate 4: Manifest verification and hash reconciliation locking under Gate 3 (STATUS: LOCKED).

### Strictly Prohibited Operations:
- Automatic execution of Task 7.7.4 under Gate 1 approval alone.
- Modifying lines 394 and 1049 of scripts/materialize_stage6m_cohort3_audio.py without Gate 2 authorization.
- Running the legacy materializer against existing Cohort 3 audio.
- Executing GPU CTTA inference.

---

## 7. Project Lead Gate 2 Authorization Record

```markdown
# GATE 2: TASK 7.7.4 NON-DESTRUCTIVE MATERIALIZATION AUTHORIZATION RECORD

**Governing Protocol:**      Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
**Authorization Authority:** Project Lead (Venkata Akhil Kumar)
**Date of Execution:**      2026-11-07

Scope: Authorizes implementation and pre-production validation of Task 7.7.4 non-destructive
       materializer (scripts/materialize_stage6m_cohort3_audio_v2.py) incorporating atomic hard-links,
       Windows OS-level exclusive locking (msvcrt.locking LK_NBLCK), 3-decoder verification, and
       cryptographic per-file disposition ledger generation.
Precondition: Prior approved Gate 1 Scientific Admission Decision (Policy 2A) and verified NTFS
              scratch demonstration (SHA-256: 8fc90c378658e9b92483971902c0b9161a73d941fe363498d05acc9d83929fc3).

Authorization Status:    [X] AUTHORIZED FOR IMPLEMENTATION & PRE-PRODUCTION VALIDATION (Gate 2 Passed)
                         [ ] REJECTED / SPECIFICATION REVISION REQUIRED
                         [ ] AWAITING DETERMINATION

Approved Scope:          Implementation of scripts/materialize_stage6m_cohort3_audio_v2.py, unit tests,
                         synthetic filesystem tests, decoder integration tests, and pre-production validation.
Production Dataset Boundary: Zero physical audio promotion, mutation, or copying of real recordings under Gate 2.
                         Production dataset finalization, reconciliation into
                         datasets/audio/stage6m/cohort3_reconciled_assets/, and final manifest locking
                         remain strictly governed under Gate 3.
Authorization Date:      2026-11-07
```

