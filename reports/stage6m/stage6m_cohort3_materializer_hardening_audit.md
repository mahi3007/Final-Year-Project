# Stage 6M v1.5 — Task 7.4.1.1 Full-File Audio Integrity & Complete Stream-Termination Audit Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_MATERIALIZER_HARDENING_AUDIT`  
> **TASK ID:** `TASK_7_4_1_1`  
> **TASK TITLE:** Full-File Audio Integrity and Complete Stream-Termination Validation  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol (`v1.5-five-stratum-parity`)  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **AUDIT DISPOSITION:** **PASS — FULL-FILE INTEGRITY & STREAM TERMINATION VERIFIED**  
> **GOVERNANCE STATUS:** **AUTHORIZED FOR DATA PREPARATION**  
> **SELECTION MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** `2026-11-01T12:50:00Z`  

---

## 1. Executive Summary & Review Scope

Following the independent review of Task 7.4.1 (commit [`c499571`](https://github.com/mahi3007/Final-Year-Project/commit/c499571)), two residual reliability gaps were identified:
1. **Issue B Weakness (Partial Frame Decode):** `validate_audio_file()` previously checked only `frames, _ = sf.read(str(path), stop=1000)` (~21 ms at 48 kHz). This verified only that the MP3 begins correctly, but failed to detect files with valid initial headers that suffer corruption or truncation later in the stream.
2. **Issue C Weakness (Incomplete Content-Range & Stream Termination):** `ThreadedResilientGzipStream` previously extracted only `{start}` from `Content-Range`, leaving `{end}` and `{total}` unvalidated. Reconnections did not verify consistency of `{total}` across reconnects. An initial HTTP 206 response was accepted without verifying that `start == 0`. Most critically, `readinto()` returned EOF (`0`) on stream close without verifying `self._decompressor.eof == True`, and HTTP 416 was treated as completion without checking stream termination integrity.

**Task 7.4.1.1 Resolution Status:** Both residual gaps have been closed with bounded-memory full-file decoding, comprehensive RFC 9110 `Content-Range` validation, total consistency tracking, and gzip EOF integrity verification.

---

## 2. Technical Remediation & Implementation Details

### 2.1 Issue A — Speaker Completeness Accounting (Confirmed PASS)
- Initialized all 1,265 unique target speakers from [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) in `speaker_clips` before counting.
- Verified dry-run accounting:
  - Total Target Speakers: **1,265**
  - Complete Speakers: **0**
  - Incomplete Speakers: **1,265**
  - Every single speaker enumerated in [`datasets/splits/stage6m_cohort3_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_speaker_completeness_report.json) with `materialized_clips_count: 0`, `is_complete: false`.

### 2.2 Issue B — Full-File Bounded-Memory Audio Integrity (Task 7.4.1.1)
- **Bounded-Memory Stream Decoding:** Replaced `sf.read(..., stop=1000)` with a bounded chunk iterator using `sf.SoundFile(str(path), "r")`. Audio frames are read in sequential 4,096-frame blocks (~16 KB for mono float32) without loading the whole recording into memory.
- **Declared Frame Boundary Verification (Reaching At Least Declared Frames):**
  The implementation verifies `total_decoded_frames >= declared_frames` via `if declared_frames > 0 and total_decoded_frames < declared_frames:`. It enforces that the decoder reaches at least the declared frame count. Any shortfall indicates mid/late-file truncation or bitstream corruption and fails closed with:
  `Truncated audio stream: decoded 13295 frames but header declares 32000`.
  This check tolerates trailing decoder padding/lead-out frames while strictly detecting and rejecting incomplete streams.
- **Sample Rate & Downstream Resampling Contract:**
  - Common Voice 27.0 recordings arrive at native rates (typically 32 kHz, 44.1 kHz, or 48 kHz). Ingest validates container integrity, non-zero duration, and decodability at native rate (`samplerate in {16000, 22050, 24000, 32000, 44100, 48000}`).
  - Downstream CTTA feature extraction and inference resample to mono 16 kHz float32 on-the-fly via [`src/dsg_ctta/data/acoustic.py::load_and_resample_audio`](file:///C:/Users/venka/Downloads/final year project main/src/dsg_ctta/data/acoustic.py).

### 2.3 Issue C — Complete Content-Range Structure & Gzip Stream Termination (Task 7.4.1.1)
- **Complete Content-Range Validation:**
  - Format parsed: `bytes {start}-{end}/{total}` (or `{total}` as `*`).
  - Enforces `start >= 0`, `end >= start`, and `total > end` (when total is specified).
  - Rejects inverted byte ranges (e.g. `bytes 100-50/200`) with `IOError("Invalid inverted range in Content-Range")`.
- **Total Resource Consistency Tracking:**
  - The expected archive total is recorded in `self._expected_total_bytes` from `Content-Length` (if 200 OK) or `Content-Range` (if 206).
  - Reconnections enforce that the declared `{total}` matches `self._expected_total_bytes`. If inconsistent (e.g. resource total shifts from 135 to 635), raises `IOError("Inconsistent resource total across reconnects")`.
- **Initial Connection Semantics:**
  - Initial request (without Range header) expects HTTP 200 OK.
  - If a server responds with 206 Partial Content on the initial request, `start` MUST be 0. If `start != 0` (e.g. `bytes 10-134/135`), raises `IOError("HTTP initial connect failed: server returned 206 Partial Content with non-zero start offset")`.
- **Exact-Length Completion Condition:**
  - Enforces exact equality upon completion:
    $$\text{received compressed bytes} == \text{expected total bytes}$$
  - Rejects incomplete downloads (`_producer_bytes_read < expected_total_bytes`) with `IOError("Incomplete download: stream ended ... before reaching expected total")`.
  - Rejects excess delivered bytes / network overflow (`_producer_bytes_read > expected_total_bytes`) with `IOError("Excess compressed bytes received: stream delivered ... exceeding expected total")`.
- **Gzip Stream Termination Integrity Check & Trailing Data Rejection:**
  - In `readinto()`, when the network producer ends, `self._decompressor.flush()` is emitted.
  - Before returning EOF (`0 bytes`), `readinto()` strictly verifies:
    1. `self._decompressor.eof == True`: Confirms the complete gzip stream (including header, compressed blocks, and 8-byte CRC32/ISIZE footer) was consumed. If False, raises `IOError("Incomplete gzip stream: reached end of stream without valid gzip EOF marker")`.
    2. `not self._decompressor.unused_data`: Verifies no unexpected trailing compressed data or garbage exists after the gzip member. If present, raises `IOError("Unexpected trailing compressed data: found ... unexpected bytes after gzip EOF marker")`.
- **Premature HTTP 416 Rejection:**
  - If a server returns HTTP 416 when `_producer_bytes_read < self._expected_total_bytes`, raises `IOError("HTTP 416 Range Not Satisfiable received prematurely")`.

### 2.4 Task 7.4.2 — Controlled Materialization Pilot Interface
- **Dedicated CLI Flag:** `--pilot` option executes the isolated 75-clip pilot materialization without touching or modifying the full-cohort ledgers or reports.
- **Deterministic Stratum Sampling:** Selects exactly 5 speakers, 1 from each confirmatory evaluation stratum (`Australian English`, `Canadian English`, `England English`, `South Asian English`, `US English`), sorted deterministically by `speaker_id`.
- **Full Traceability:** Validates that each selected pilot speaker has exactly 15 clips ($5 \times 15 = 75$ clips) and records the parent provisional manifest SHA-256 (`b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`) in all pilot ledgers.
- **Isolated Destination & Ledgers:** Audio is written to a distinct directory (`datasets/external/common_voice_27/cohort3_pilot_audio`), and independent ledgers are produced:
  - [`datasets/splits/stage6m_cohort3_pilot_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_speaker_completeness_report.json)
  - [`datasets/splits/stage6m_cohort3_pilot_failed_clips_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_failed_clips_report.json)
  - [`datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv)
  - [`reports/stage6m/stage6m_cohort3_pilot_materialization.json`](file:///C:/Users/venka/Downloads/final year project main/reports/stage6m/stage6m_cohort3_pilot_materialization.json)
  - [`reports/stage6m/stage6m_cohort3_pilot_materialization.md`](file:///C:/Users/venka/Downloads/final year project main/reports/stage6m/stage6m_cohort3_pilot_materialization.md)

---

## 3. Quantitative Materialization Inventory & Ledgers

Following Task 7.4.1.1 hardening, [`scripts/materialize_stage6m_cohort3_audio.py`](file:///C:/Users/venka/Downloads/final year project main/scripts/materialize_stage6m_cohort3_audio.py) was executed in dry-run / validate-only mode:

| Metric | Target Requirement | Current Materialized | Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluation Clips** | 16,500 ($1,100 \times 15$) | 0 | **TRACKED** |
| **Gate-Reference Clips** | 1,500 ($100 \times 15$) | 0 | **TRACKED** |
| **Australian Reserve Clips** | 975 ($65 \times 15$) | 0 | **TRACKED** |
| **Grand Total Audio Clips** | **18,975** | **0** | **0.00%** |
| **Complete Speakers ($\ge 15$ valid clips)** | 1,265 | 0 / 1,265 (Incomplete: 1,265) | **IN_PROGRESS** |
| **Failed / Corrupt Clips** | 0 allowed | 0 | **PASS** |
| **Total Physical Audio Duration** | — | 0.00 s (0.00 h) | **NOMINAL** |
| **Total Physical Audio Bytes** | — | 0 bytes (0.00 MB) | **NOMINAL** |

### Authoritative Ledgers
- **Per-Clip SHA-256 Ledger:** [`datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv)  
  - SHA-256: `f18391abeebc6a08ca33c3a8a6ffbe0920ed8907863d14f419ffeda1e5384a8c`
- **Speaker Completeness Report:** [`datasets/splits/stage6m_cohort3_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_speaker_completeness_report.json)
- **Failed Clips Report:** [`datasets/splits/stage6m_cohort3_failed_clips_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_failed_clips_report.json)
- **Materialization JSON Report:** [`reports/stage6m/stage6m_cohort3_audio_materialization.json`](file:///C:/Users/venka/Downloads/final year project main/reports/stage6m/stage6m_cohort3_audio_materialization.json)
- **Materialization Markdown Report:** [`reports/stage6m/stage6m_cohort3_audio_materialization.md`](file:///C:/Users/venka/Downloads/final year project main/reports/stage6m/stage6m_cohort3_audio_materialization.md)

---

## 4. Historical Engine Immutability Audit

The frozen historical execution code at [`src/dsg_ctta/evaluation/paired_cluster_inference.py`](file:///C:/Users/venka/Downloads/final year project main/src/dsg_ctta/evaluation/paired_cluster_inference.py) was audited against historical commit `a7a3b79`:
- **Git Object Blob Hash:** `58d456fbcce43b5322d56df80e4077a32d7f4cca`
- **Lines of Diff against `a7a3b79`:** **Exactly 0 lines.**
- **Status:** **CONFIRMED UNTOUCHED & 100% IMMUTABLE.**

---

## 5. Verification Evidence

### 5.1 Hardened Materializer Test Suite
Command: `python -m pytest tests/research_validity/test_stage6m_cohort3_audio_materialization.py -v`
```
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_target_manifest_scale_and_fields PASSED [ 12%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_validate_audio_file_genuine_mp3_and_boundaries PASSED [ 25%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_speaker_completeness_accounting_zero_audio PASSED [ 37%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_local_sourcing_and_completeness_tracking PASSED [ 50%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_streaming_resume_range_validation PASSED [ 62%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_downstream_acoustic_resampling_contract PASSED [ 75%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_materialization_reports_exist_and_consistent PASSED [ 87%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_historical_v1_4_0_execution_engine_immutability PASSED [100%]

============================== 8 passed in 3.54s ==============================
```

### 5.2 Full Stage 6M Regression Suite
Command: `python -m pytest tests/research_validity/test_stage6m_cohort3_audio_materialization.py tests/research_validity/test_stage6m_cohort3_source_audit.py tests/research_validity/test_stage6m_cohort3_curation.py tests/research_validity/test_stage6m_project_lead_authorization_package.py tests/research_validity/test_historical_immutability.py -v`
```
============================= 48 passed in 19.54s =============================
```

---

## 6. Governance Gating & Recommended Next Steps

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: AUTHORIZED (DATA PREPARATION)                   ║
║                                                                                      ║
║  1. Materializer full-file integrity and stream termination is VERIFIED (7.4.1.1).   ║
║  2. Provisional manifest remains UNLOCKED (PROVISIONAL).                             ║
║  3. Controlled pilot download (75 clips) is READY FOR SEPARATE PILOT AUTHORIZATION.  ║
║  4. Full 18,975-clip download remains HELD pending pilot validation.                 ║
║  5. Confirmatory GPU CTTA adaptation & inference remain STRICTLY BLOCKED.            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

### Readiness for Task 7.4.2 — Controlled Materialization Pilot
With the two residual reliability gaps now closed:
- **Pilot Scope:** 75 clips across 5 speakers (1 speaker per stratum $\times 15$ clips), strictly drawn from the provisional manifest with zero substitutions.
- **Pilot Verification:**
  - Full-file bounded-memory MP3 decoding and frame completeness check.
  - Exact SHA-256 computation from on-disk physical files.
  - Accurate recording ID, speaker, accent stratum, transcript, and word-count matching.
  - Downstream mono 16 kHz resampling verification.
- **Governance Gate:** Subject to formal pilot download execution authorization before downloading begins.
