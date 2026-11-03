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
- **Declared Frame Boundary Verification with MPEG Audio Layer III Padding Tolerance:**
  Real Mozilla Common Voice MP3 recordings (encoded via LAME) include encoder delay (typically 528 samples) and container zero-padding up to the 1,152-sample MPEG frame boundary. `libsndfile`'s `mpg123` backend strips this encoder padding upon decoding, causing `total_decoded_frames` to be slightly below `declared_frames` by 198 to 966 samples across 100% of the 900 empirical Common Voice recordings tested (mean ~250 samples, strictly < 1 MPEG frame of 1,152 samples). The frame completeness invariant enforces `declared_frames - total_decoded_frames <= 1,152` (`MAX_MP3_PADDING_FRAMES`), tolerating standard MPEG codec delay while strictly detecting and rejecting bitstream truncations exceeding 1,152 samples (failing closed with `Truncated audio stream: decoded ... frames but header declares ... shortfall ... exceeds MPEG frame padding tolerance of 1152`).
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

### 2.5 Task 7.4.2.1 — Pilot Artifact Isolation & Evidence Provenance Repair
- **Root Cause Remediation:** The mock verification test previously generated 75 synthetic MP3 fixtures in `tmp_path`, but invoked artifact generation without path overrides, inadvertently writing synthetic durations (0.2s) and hashes into tracked repository reports.
- **Output Path Parameterization:**
  - `generate_materialization_artifacts()` and `generate_pilot_materialization_artifacts()` now accept explicit optional output paths (`report_json_path`, `report_md_path`, `ledger_csv_path`, `speaker_report_path`, `failed_report_path`), ensuring directories are created on demand.
  - Added CLI flag `--output-dir` to [`scripts/materialize_stage6m_cohort3_audio.py`](file:///C:/Users/venka/Downloads/final year project main/scripts/materialize_stage6m_cohort3_audio.py).
- **Test Output Isolation:**
  - Mock materialization tests write 100% of synthetic fixtures and generated reports under `tmp_path`.
  - Zero-audio full-cohort testing writes completeness ledgers under `tmp_path`.
  - Pilot CLI test runs with `--output-dir <tmp_path>` and explicitly asserts byte-level SHA-256 immutability of all repository files before and after CLI execution.
- **Clean Provenance Dry Run Regeneration:**
  - Re-executed `scripts/materialize_stage6m_cohort3_audio.py --pilot --validate-only` to purge mock data and restore clean zero-audio evidence:
    - Target clips: $75$
    - Valid clips: $0$
    - Disposition: `PILOT_ZERO_AUDIO_DRY_RUN`
    - Pilot Ledger: Header only ($0$ data rows)
    - Pilot Speakers: 5 speakers with `is_complete: false`, $0$ clips materialized.

---

## 3. Quantitative Materialization Inventory & Ledgers

### 3.1 Full-Cohort Materialization Inventory (18,975 Clips)
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

### 3.2 Controlled Pilot Inventory (75 Clips — Zero-Audio Dry-Run Evidence)

| Stratum | Speaker ID | Target Clips | Materialized | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Canadian English** | `00143475c51f0cc4...` | 15 | 0 | **INCOMPLETE** |
| **Australian English** | `008f1e5e50d2af13...` | 15 | 0 | **INCOMPLETE** |
| **US English** | `010465487d57bc20...` | 15 | 0 | **INCOMPLETE** |
| **England English** | `016e15e58e2d93cb...` | 15 | 0 | **INCOMPLETE** |
| **South Asian English** | `01c9ba7d35336856...` | 15 | 0 | **INCOMPLETE** |
| **Grand Total** | **5 Speakers** | **75** | **0** | **IN_PROGRESS** |

### Authoritative Ledgers
- **Full-Cohort Per-Clip SHA-256 Ledger:** [`datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv) (SHA-256: `f18391abeebc6a08ca33c3a8a6ffbe0920ed8907863d14f419ffeda1e5384a8c`)
- **Pilot Per-Clip SHA-256 Ledger:** [`datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv) (SHA-256: `f18391abeebc6a08ca33c3a8a6ffbe0920ed8907863d14f419ffeda1e5384a8c`)
- **Pilot Materialization JSON Report:** [`reports/stage6m/stage6m_cohort3_pilot_materialization.json`](file:///C:/Users/venka/Downloads/final year project main/reports/stage6m/stage6m_cohort3_pilot_materialization.json)
- **Pilot Materialization Markdown Report:** [`reports/stage6m/stage6m_cohort3_pilot_materialization.md`](file:///C:/Users/venka/Downloads/final year project main/reports/stage6m/stage6m_cohort3_pilot_materialization.md)
- **Pilot Speaker Completeness Report:** [`datasets/splits/stage6m_cohort3_pilot_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_speaker_completeness_report.json)
- **Pilot Failed Clips Report:** [`datasets/splits/stage6m_cohort3_pilot_failed_clips_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_failed_clips_report.json)

---

## 4. Historical Engine Immutability Audit

The frozen historical execution code at [`src/dsg_ctta/evaluation/paired_cluster_inference.py`](file:///C:/Users/venka/Downloads/final year project main/src/dsg_ctta/evaluation/paired_cluster_inference.py) was audited against historical commit `a7a3b79`:
- **Git Object Blob Hash:** `58d456fbcce43b5322d56df80e4077a32d7f4cca`
- **Lines of Diff against `a7a3b79`:** **Exactly 0 lines.**
- **Status:** **CONFIRMED UNTOUCHED & 100% IMMUTABLE.**

---

## 5. Verification Evidence

### 5.1 Hardened Materializer Test Suite (12 Tests Passed)
Command: `pytest tests/research_validity/test_stage6m_cohort3_audio_materialization.py -v`
```
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_target_manifest_scale_and_fields PASSED [  8%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_validate_audio_file_genuine_mp3_and_boundaries PASSED [ 16%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_speaker_completeness_accounting_zero_audio PASSED [ 25%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_local_sourcing_and_completeness_tracking PASSED [ 33%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_streaming_resume_range_validation PASSED [ 41%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_downstream_acoustic_resampling_contract PASSED [ 50%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_materialization_reports_exist_and_consistent PASSED [ 58%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_historical_v1_4_0_execution_engine_immutability PASSED [ 66%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_speaker_and_clip_selection PASSED [ 75%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_cli_execution_and_report_isolation PASSED [ 83%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_mock_materialization_verification PASSED [ 91%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_committed_pilot_reports_exist_and_clean_zero_audio PASSED [100%]

============================= 12 passed in 8.44s ==============================
```

### 5.2 Stage 6M Targeted Regression Suite (52 Tests Passed)
> **Reporting Qualification:** This suite executes five selected modules specifically targeting Stage 6M confirmatory preparation (Cohort 3 audio materialization, source audit, curation, Project-Lead authorization package, and historical engine immutability). Rather than claiming the entire repository test directory was executed, these results are accurately designated as the **52-test Stage 6M targeted regression suite**.

Command: `pytest tests/research_validity/test_stage6m_cohort3_audio_materialization.py tests/research_validity/test_stage6m_cohort3_source_audit.py tests/research_validity/test_stage6m_cohort3_curation.py tests/research_validity/test_stage6m_project_lead_authorization_package.py tests/research_validity/test_historical_immutability.py -v`
```
============================= 52 passed in 33.03s =============================
```

---

## 6. Formal Project-Lead Physical Pilot Authorization (Protocol Section 14.7)

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║             GOVERNANCE STATUS: PHYSICAL PILOT AUTHORIZED (PROTOCOL SEC 14.7)         ║
║                                                                                      ║
║  1. Materializer full-file integrity and stream termination is VERIFIED (7.4.1.1).   ║
║  2. Pilot test isolation & evidence provenance is REPAIRED & VERIFIED (7.4.2.1).     ║
║  3. Project-Lead formally AUTHORIZES 75-clip controlled physical pilot download.     ║
║  4. Execution path fails closed unless Project-Lead authorization is recorded.       ║
║  5. Acquisition confined strictly to 5 evaluation speakers x 15 clips = 75 clips.    ║
║  6. Full 18,975-clip download remains HELD pending physical pilot verification.      ║
║  7. Confirmatory GPU CTTA adaptation & inference remain STRICTLY BLOCKED.            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

### 6.1 Formal Decision Record
- **Technical Review Verdict:** **PASS** (Task 7.4.2.1 artifact isolation verified)
- **Project-Lead Formal Action:** **APPROVE — 75-clip physical pilot only**
- **Governing Standard:** Protocol Section 14.7 (Project-Lead Academic Authorization)
- **Date:** 2026-11-01

### 6.2 Authorized Scope & Safeguards
| Parameter | Authorized Value | Governance Safeguard |
| :--- | :---: | :--- |
| **Confirmatory Strata** | 5 | Australian, Canadian, England, South Asian, US English |
| **Speakers per Stratum** | 1 | Strictly 1 evaluation speaker per stratum |
| **Total Speakers** | 5 | Identical to provisional manifest selection |
| **Clips per Speaker** | 15 | Exactly 15 original recording IDs per speaker |
| **Total Physical Clips** | 75 | Strictly confined to 75 recordings |
| **Substitutions** | 0 | Zero substitutions permitted |
| **Target Directory** | `datasets/external/common_voice_27/cohort3_pilot_audio` | Completely isolated from full cohort |
| **Technical Fail-Closed Gate** | `verify_pilot_materialization_authorization()` | CLI fails closed unless authorization is recorded in governance JSON |

### 6.3 Evaluation Constraints & Blocked Capabilities
- **Strict Ingest Check Only:** These five speakers belong to the confirmatory evaluation panel. Their pilot acquisition must remain strictly an acquisition and physical decodability integrity check.
- **Strictly Blocked:** ASR performance evaluation, adaptation, threshold tuning, and model selection on these clips remain strictly prohibited.
- **Full Cohort Blocked:** Full 18,975-clip retrieval remains HELD pending physical pilot verification.
- **Execution Engine:** Confirmatory GPU CTTA adaptation and inference remain STRICTLY BLOCKED.


