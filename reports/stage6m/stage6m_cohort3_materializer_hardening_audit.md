# Stage 6M v1.5 — Task 7.4.1 Independent Materializer Hardening & Streaming Reliability Audit Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_MATERIALIZER_HARDENING_AUDIT`  
> **TASK ID:** `TASK_7_4_1`  
> **TASK TITLE:** Independent Materializer Hardening & Streaming Reliability Audit  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol (`v1.5-five-stratum-parity`)  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **AUDIT DISPOSITION:** **PASS — HARDENED PIPELINE VERIFIED**  
> **GOVERNANCE STATUS:** **AUTHORIZED FOR DATA PREPARATION**  
> **SELECTION MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** `2026-11-01T12:26:00Z`  

---

## 1. Executive Summary & Review Scope

Following the independent review of Milestone 7.4 ([commit 466de94](https://github.com/mahi3007/Final-Year-Project/commit/466de94562f4f49387645c490bfddcfb0caec3d8)), three high-priority technical issues were identified before any physical audio acquisition scales up:
1. **Issue A (Speaker Completeness Accounting):** The speaker completeness ledger previously omitted speakers with zero materialized clips because it iterated strictly over the keys of `valid_inv`. When 0 clips were materialized, the ledger showed 0 complete and 0 incomplete speakers, leaving an empty inventory.
2. **Issue B (Genuine MP3 Format Validation & Sample-Rate Policy):** Audio test fixtures previously wrote WAV-format bytes into `.mp3` filenames, masking that `soundfile` decoded WAV. The validator did not inspect `info.format`, allowing container mismatches. Additionally, the sample rate policy between ingest validation (native Common Voice rates) and downstream model adaptation (mono 16 kHz) required formal documentation and verification.
3. **Issue C (HTTP Streaming Resume & Range Response Validation):** The resilient HTTP stream sent `Range: bytes={offset}-` on reconnects but lacked validation that the server returned HTTP 206 Partial Content or that the `Content-Range` header aligned with the requested offset.

**Task 7.4.1 Resolution Status:** All three issues have been resolved, hardened in code, and verified by deterministic automated tests.

---

## 2. Technical Audit & Detailed Remediation

### 2.1 Issue A — Speaker Completeness Accounting

- **Root Cause Analysis:** In [`scripts/materialize_stage6m_cohort3_audio.py`](file:///C:/Users/venka/Downloads/final year project main/scripts/materialize_stage6m_cohort3_audio.py), `speaker_clips` was populated solely as clips matched `valid_inv`. If a speaker had 0 valid clips, their speaker ID was never added to the dictionary.
- **Hardened Implementation:** Every one of the 1,265 unique target speakers from [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) is explicitly initialized in `speaker_clips` with `required_clips_count = 15`.
- **Zero-Audio Dry-Run Evidence:**
  - Total Target Speakers: **1,265**
  - Complete Speakers: **0**
  - Incomplete Speakers: **1,265**
  - Every speaker is enumerated in [`datasets/splits/stage6m_cohort3_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_speaker_completeness_report.json) with `materialized_clips_count: 0`, `is_complete: false`.
- **Automated Verification:** Verified by `test_speaker_completeness_accounting_zero_audio` in [`tests/research_validity/test_stage6m_cohort3_audio_materialization.py`](file:///C:/Users/venka/Downloads/final year project main/tests/research_validity/test_stage6m_cohort3_audio_materialization.py).

### 2.2 Issue B — Genuine MP3 Validation & Downstream Sample-Rate Contract

- **Root Cause Analysis:** The prior `validate_audio_file()` checked `duration > 0`, `samplerate > 0`, and `channels >= 1`, but did not check `info.format`. The test helper `_generate_synthetic_wav_as_mp3()` wrote WAV data into `.mp3` files.
- **Hardened Implementation:**
  1. **Container & Codec Inspection:** `validate_audio_file()` now strictly verifies `(info.format or "").upper() == "MP3"`. Non-MP3 containers (e.g., WAV containers named `.mp3`) are strictly rejected with:
     `Invalid audio format: expected MP3 container, got WAV`.
  2. **Frame Decodability Check:** Performs a test decode via `sf.read(str(path), stop=1000)` to ensure audio frames actually decode and are non-empty. Corrupt bitstreams and truncated files fail closed with `Decode failure`.
  3. **Sample-Rate Policy & Downstream Contract:**
     - **Ingest Validation:** Mozilla Common Voice 27.0 recordings natively feature varied sample rates (typically 32 kHz, 44.1 kHz, or 48 kHz). Ingest validates container integrity, non-zero duration, and decodability at native rate (`samplerate in {16000, 22050, 24000, 32000, 44100, 48000}`).
     - **Downstream Resampling:** Downstream acoustic processing and CTTA models (Wav2Vec2, Whisper) require mono 16,000 Hz float32 audio. This resampling is handled on-the-fly by [`src/dsg_ctta/data/acoustic.py::load_and_resample_audio`](file:///C:/Users/venka/Downloads/final year project main/src/dsg_ctta/data/acoustic.py), which averages stereo channels to mono and resamples using `librosa.resample`.
- **Automated Verification:**
  - `test_validate_audio_file_genuine_mp3_and_boundaries` passed across missing, empty, corrupted, fake-WAV, truncated, 16k mono, 48k stereo, 32k mono, and 8k unsupported fixtures.
  - `test_downstream_acoustic_resampling_contract` verified that a genuine 48 kHz stereo MP3 passes ingest validation and is converted to `(8000,) float32 sr=16000` mono audio downstream.

### 2.3 Issue C — Streaming Resume & HTTP Range Response Verification

- **Root Cause Analysis:** In [`ThreadedResilientGzipStream`](file:///C:/Users/venka/Downloads/final year project main/scripts/materialize_stage6m_cohort3_audio.py), reconnects sent `Range: bytes={offset}-`, but did not verify `resp.status == 206` or parse `Content-Range`. A server responding with 200 OK would send from byte 0, causing duplicate byte decompression and archive corruption.
- **Hardened Implementation:**
  1. **Dependency Injection:** `ThreadedResilientGzipStream` now accepts an optional `url_opener` callable for deterministic mocking and integration testing.
  2. **HTTP 206 Enforcement:** When resuming (`_producer_bytes_read > 0`), the stream requires `status == 206`. If status is 200 OK, it immediately raises:
     `IOError("HTTP resume failed: server returned status 200 (expected 206 Partial Content) when requesting range bytes={offset}-")`.
  3. **Content-Range Header Alignment:** Parses `Content-Range: bytes {start}-{end}/{total}` and verifies `start == _producer_bytes_read`. If mismatched or missing, raises `IOError`.
  4. **Consumer Exception Propagation:** In `readinto()`, any fatal producer exception stored in `_producer_error` is immediately re-raised to the caller thread, terminating decompression cleanly.
- **Automated Verification:** Verified by `test_streaming_resume_range_validation` across 4 deterministic test scenarios:
  - Clean interrupted-stream recovery producing identical decompressed archive.
  - Server returning 200 OK on resume raises `IOError`.
  - Server returning mismatched range start byte raises `IOError`.
  - Server missing `Content-Range` header raises `IOError`.

---

## 3. Quantitative Materialization Inventory & Ledgers

Following pipeline hardening, [`scripts/materialize_stage6m_cohort3_audio.py`](file:///C:/Users/venka/Downloads/final year project main/scripts/materialize_stage6m_cohort3_audio.py) was executed in dry-run / validate-only mode:

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
Executed: `python -m pytest tests/research_validity/test_stage6m_cohort3_audio_materialization.py -v`
```
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_target_manifest_scale_and_fields PASSED [ 12%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_validate_audio_file_genuine_mp3_and_boundaries PASSED [ 25%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_speaker_completeness_accounting_zero_audio PASSED [ 37%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_local_sourcing_and_completeness_tracking PASSED [ 50%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_streaming_resume_range_validation PASSED [ 62%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_downstream_acoustic_resampling_contract PASSED [ 75%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_materialization_reports_exist_and_consistent PASSED [ 87%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_historical_v1_4_0_execution_engine_immutability PASSED [100%]

============================== 8 passed in 5.09s ==============================
```

### 5.2 Full Stage 6M Regression Suite
Executed: `python -m pytest tests/research_validity/test_stage6m_cohort3_audio_materialization.py tests/research_validity/test_stage6m_cohort3_source_audit.py tests/research_validity/test_stage6m_cohort3_curation.py tests/research_validity/test_stage6m_project_lead_authorization_package.py tests/research_validity/test_historical_immutability.py -v`
```
============================= 48 passed in 19.54s =============================
```

---

## 6. Governance Gating & Recommended Next Steps

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: AUTHORIZED (DATA PREPARATION)                   ║
║                                                                                      ║
║  1. Materializer hardening and streaming reliability audit is COMPLETE (Task 7.4.1).  ║
║  2. Provisional manifest remains UNLOCKED (PROVISIONAL).                             ║
║  3. Full 18,975-clip download remains HELD pending a small controlled pilot.        ║
║  4. Confirmatory GPU CTTA adaptation & inference remain STRICTLY BLOCKED.            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

### Recommended Next Milestone: Task 7.4.2 — Controlled Materialization Pilot
In accordance with the reviewer's recommended sequence:
1. **Pilot Scope:** Select an authorized, contiguous subset of speakers from the provisional manifest (e.g., 5 speakers across all 5 strata = 75 clips total; zero substitutions).
2. **Materialize Pilot:** Download and validate through the hardened streaming pipeline.
3. **Independent Pilot Audit:** Verify file bitstreams, SHA-256 hashes, transcripts, decodability, and speaker completeness.
4. **Scale Up:** Proceed to full 18,975-clip materialization only after the pilot audit formally passes.
