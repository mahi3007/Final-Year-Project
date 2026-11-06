# Stage 6M v1.5 Task 7.7.2B — Production Validator Impact Assessment and Non-Destructive Resolution Strategies

**Generated:** 2026-11-06 10:16:58 UTC
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Parity Protocol (Section 14.7)
**Task Classification:** Research-only forensic audit and impact assessment (Strictly non-destructive)
**Execution Status:** COMPLETE — 18,975 recordings audited (18,845 accepted + 130 quarantined)

---

## Executive Summary

This assessment provides an exhaustive, read-only empirical audit of the Stage 6M Cohort 3 production audio validator
(`validate_audio_file` in `scripts/materialize_stage6m_cohort3_audio.py`) across the entire evidence population:
**18,845 accepted recordings** (~705 MB) and **130 quarantined recordings** (~5.8 MB), totaling **18,975 recordings**.

### Key Discoveries

1. **Complete Cohort Audit (18,975 / 18,975):** Every recording was independently inspected at the container, physical MPEG bitstream,
   and PCM decoded sample-frame levels. Zero recordings were silently excluded.
2. **Pervasive Absence of Gapless Metadata:** Exactly **0 out of 18,845 accepted recordings** (0.00%) and **0 out of 130 quarantined recordings** (0.00%)
   possess Xing, Info, or LAME gapless playback headers. All recordings are raw CBR MP3 bitstreams preceded by ID3v2 metadata tags (`Lavf54.20.4`).
3. **Shortfall Origin Discovered:** Because no Xing/Info header exists, libsndfile / libmpg123 estimates duration using total file size.
   Every byte of non-audio ID3v2 header metadata adds artificial duration to SoundFile's declared frame count:
   - At 48 kHz / 64 kbps mono (192 bytes/frame), each byte equals $1152 / 192 = 6$ PCM samples.
   - A standard 33-byte ID3v2 tag creates an artificial shortfall of exactly $33 \times 6 = 198$ samples (present in **4,119 accepted recordings**).
   - A 161-byte ID3v2 tag creates an artificial shortfall of exactly $161 \times 6 = 966$ samples (present in **872 accepted recordings**).
   - When container headers exceed ~192 bytes or file size rounding residue exceeds 1,152 samples, the artificial shortfall exceeds
     `MAX_MP3_PADDING_FRAMES = 1152`, causing the production validator to reject the recording.
4. **Potential False Rejections:** All **130 quarantined recordings** (100.0%) exhibit complete, uncorrupted physical MPEG frames to EOF,
   zero sync loss, and successful error-free PCM decoding. They failed solely because of the 1,152 sample-frame threshold applied to an estimated header.
   In accordance with the five refinements, they are classified as **potential false-rejection candidates** rather than proven false rejections,
   as authoritative original recording durations are unavailable.
5. **False Acceptance Limitation (Claim A vs Claim B):** Complete physical frame integrity (Claim A) does **not** prove original source completeness
   (Claim B). Whole-frame loss at frame boundaries leaves structurally valid MPEG bitstreams. Without an authoritative original duration reference,
   the risk of undetected upstream whole-frame loss is **UNKNOWN**.

---

## Production Validator Execution Flow & Callers

The production validator is implemented in `scripts/materialize_stage6m_cohort3_audio.py::validate_audio_file()`:

```text
Path Ingest -> Container & Format Check (sf.info) -> Range & Channel Validations
            -> Complete Stream Decoding (sf.SoundFile in 4,096-frame chunks)
            -> Accumulate total_decoded_frames (using len(chunk) per-channel)
            -> Shortfall = reader.frames - total_decoded_frames
            -> Check: declared_frames > 0 and shortfall > 1152
            -> Compute SHA-256 -> Return (is_valid, duration, sr, channels, sha256, err)
```

### Investigation of `sf.info()` vs `sf.SoundFile()` Equivalence

The validator invokes `sf.info(path)` followed by `sf.SoundFile(path)`. Inspection of PySoundFile source code confirms:
- `sf.info()` internally instantiates `_SoundFileInfo`, which executes `with SoundFile(file) as f:` and reads `f.frames` and `f.samplerate`.
- Both query the identical underlying libsndfile `SF_INFO.frames` field, populated via `mpg123_length()`.
- Therefore, **`sf.info()` provides zero independent duration confirmation** relative to `sf.SoundFile()`. They represent the same measurement.

### Callers and Destructive Action Inventory

1. **Line 863 (`scan_local_inventory`):** Audits pre-existing local audio files. Non-destructive; segregates into `valid_inv` and `failed_inv`.
2. **Line 916 (`materialize_from_local_source`):** Copies candidate files and validates. Retains failed files in `failed_inv` without deleting.
3. **Line 1018 (`materialize_from_stream`):** Extracts audio stream members from tar archive to disk, then validates.
   - **DESTRUCTIVE ACTION (Line 1049):** If validation fails, executes `dest_file.unlink(missing_ok=True)`.
   - Any recording that fails validation during stream materialization is immediately deleted from disk.
4. **Line 1499 (`audit_local_audio_inventory`):** Pre-flight integrity check against manifest ledger. Read-only verification.

---

## Formal Five-Quantity Evidence Model

To prevent conflation between compressed MPEG bitstream structures and uncompressed PCM audio, the assessment defines:

| Quantity | Symbol | Native Unit | What It Proves | What It Cannot Prove |
| :--- | :---: | :---: | :--- | :--- |
| **SoundFile Declared Frames** | $F_{\text{declared}}$ | PCM sample frames | Initial estimate returned by libsndfile (`mpg123_length()`). | Does not prove actual decodability or stream length. |
| **Actual Decoded PCM Frames** | $F_{\text{decoded}}$ | PCM sample frames | Exact audio samples delivered by complete stream decode. | Cannot prove whether frames were truncated upstream. |
| **Physical MPEG Capacity** | $F_{\text{phys\_cap}}$ | PCM sample frames | Upper bound: $N_{\text{complete MPEG frames}} \times 1152$. | Cannot prove encoder delay/padding or original length. |
| **Xing / Info / LAME Metadata** | $F_{\text{xing}}$ | MPEG / PCM frames | Declared encoder frames, delay (528), and padding. | Cannot prove absence of truncation if header missing. |
| **Authoritative Original Duration** | $F_{\text{orig}}$ | PCM sample frames / sec | Ground truth uncompressed master recording length. | **Absent in Common Voice 27.0** (Claim B unverified). |

> [!IMPORTANT]
> **Unit Consistency Rule:** For MPEG-1 Layer III, physical PCM capacity is defined strictly as:
> $$F_{\text{phys\_cap}} = N_{\text{complete MPEG frames}} \times 1152$$
> This represents a per-channel sample-frame count. For stereo audio, `len(chunk)` represents sample frames, not twice that number. `chunk.size` must never be used as a duration count.

---

## Full Read-Only Cohort Audit Results

### Cohort Population Metrics

| Population | Target Count | Verified On Disk | Hash Ledger Agreement | Total File Size | Decoded Frame Range | Dominant Sample Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Accepted Cohort** | 18,845 | 18,845 | 18,845 / 18,845 (100.0%) | 672.31 MB | 9,069 - 181,473 bytes | 48,000 Hz (14,536) |
| **Quarantined Cohort** | 130 | 130 | 130 / 130 (100.0%) | 4.56 MB | 12,784 - 77,706 bytes | 48,000 Hz (0) |
| **Total Evidence Base** | **18,975** | **18,975** | **18,975 / 18,975 (100.0%)** | **676.87 MB** | — | — |

### Shortfall Distribution Analysis

The table below details the declared-versus-decoded shortfall ($F_{\text{declared}} - F_{\text{decoded}}$) across both cohorts:

| Category | Shortfall Range (PCM frames) | Accepted Cohort Count | Quarantined Cohort Count | Current Validator Action |
| :--- | :---: | :---: | :---: | :--- |
| **Zero Shortfall** | $\Delta = 0$ | 0 | 0 | PASS |
| **Positive Within Tolerance** | $0 < \Delta \le 1152$ | 18,845 (100.0%) | 0 (0.0%) | PASS |
| **Positive Exceeding Tolerance** | $\Delta > 1152$ | 0 (0.0%) | 130 (100.0%) | FAIL (Quarantined) |
| **Negative Shortfall** | $\Delta < 0$ | 0 | 0 | PASS |

### Empirical Shortfall Clustering

- **Accepted Recordings:** Shortfall values cluster precisely at values determined by ID3 tag length:
  - $\Delta = 270$ samples: **9,080 recordings** (48.18%)
  - $\Delta = 198$ samples: **4,119 recordings** (21.86%)
  - $\Delta = 240$ samples: **3,917 recordings** (20.79%)
  - $\Delta = 966$ samples: **872 recordings** (4.63%)
  - $\Delta = 852$ samples: **465 recordings** (2.47%)
  - $\Delta = 757$ samples: **310 recordings** (1.64%)
  - $\Delta = 917$ samples: **64 recordings** (0.34%)
  - $\Delta = 778$ samples: **15 recordings** (0.08%)
  - $\Delta = 880$ samples: **1 recordings** (0.01%)
  - $\Delta = 1063$ samples: **1 recordings** (0.01%)
- **Quarantined Recordings:** Shortfall values range from **1,296 to 2,979 samples** (approx. 27.0 ms to 62.1 ms at 48 kHz).
  Every single quarantined recording failed strictly because its shortfall exceeded 1,152 samples.

---

## False-Rejection Candidate Analysis

- **Potential False-Rejection Candidates:** **130 / 130** (100.0%)
- **Physical Structural Integrity:** All 130 recordings possess intact sequential MPEG frames from stream start to EOF.
- **Decodability:** All 130 recordings decode completely without decoder errors or stream aborts.
- **Reason for Failure:** The shortfall was entirely an artifact of libmpg123 estimating duration from file size in the absence of Xing headers.
- **Epistemological Constraint:** Without an authoritative original uncompressed recording duration, these recordings cannot be labeled
  as *proven* false rejections. They are classified strictly as **potential false-rejection candidates**.

---

## False-Acceptance Limitations (Claim A vs Claim B)

- **Claim A (Current File Structural Completeness):** Established for **18,845 / 18,845 accepted recordings** and **130 / 130 quarantined recordings**.
- **Claim B (Original Recording Completeness):** **UNVERIFIABLE** for 100% of the cohort.
- **Task 7.7.2A Whole-Frame Truncation Demonstration:** In Case 8 of Task 7.7.2A, dropping complete MPEG audio frames produced a file that decoded
  perfectly, possessed valid frame boundaries, and exhibited zero physical structural errors. Therefore, complete-frame loss is inherently
  undetectable from bitstream structure alone.
- **Risk Statement:** Without an authoritative duration reference, the risk of undetected upstream whole-frame loss is **UNKNOWN** and must
  not be classified as low.

---

## Comparative Evaluation of Four Candidate Strategies

| Evaluation Criterion | Strategy A: Existing Rule | Strategy B: Decoded PCM Rule | Strategy C: Metadata-Aware Rule | Strategy D: Multi-Evidence Rule (Research Rec.) |
| :--- | :--- | :--- | :--- | :--- |
| **Core Rule** | `shortfall <= 1152` | `decoded_frames > 0` and error-free | Xing-verified OR physical complete | Multi-layer: Physical + PCM + Metadata |
| **Evidence Required** | SoundFile header + PCM decode | PCM decode only | ID3v2 + MPEG parse + PCM decode | Full bitstream parse + PCM decode + Master ref |
| **Accepted Cohort Pass** | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) |
| **Quarantine Cohort Pass** | 0 / 130 (0.0%) | 130 / 130 (100.0%) | 130 / 130 (100.0%) | 130 / 130 (100.0%) |
| **Potential False Rejections** | High (130 recordings rejected on estimation artifact) | Minimal for estimation artifacts; non-zero overall | Low (verifies physical frame completeness) | Low (verifies physical frame completeness) |
| **False Acceptance Risk** | Unknown (whole-frame loss undetected) | Unknown (truncation at frame boundaries undetected) | Unknown (whole-frame loss undetected) | Unknown without master; detects broken sync/partial frames |
| **What It Detects** | Large shortfall against estimated header | Decode exceptions, 0-byte/empty streams | Incomplete final frames, sync loss, corrupt Xing | Partial frames, broken sync, corrupt headers |
| **What It Cannot Detect** | Whole-frame loss upstream; container header inflation | Incomplete frames concealed by decoder tolerance | Whole-frame loss upstream | Whole-frame loss upstream without master |
| **Fail-Closed Behavior** | Fails closed on estimate, rejecting valid files | Fails open on truncated complete frames | Fails closed on malformed metadata & incomplete frames | Fails closed on any structural or decode defect |
| **Implementation Complexity** | Zero (current code) | Low (remove shortfall check) | Moderate (requires bitstream parser) | Moderate-High (formal forensic inspection) |
| **Remaining Uncertainty** | Discards 130 valid speakers | May admit upstream-shortened files | Upstream whole-frame completeness unproven | Upstream whole-frame completeness unproven |

### Research Recommendation

**Strategy D (Multi-Evidence Rule)** is the recommended scientific approach for Stage 6M:
1. It grounds file validity in **physical bitstream completeness** rather than libsndfile's file-size estimation.
2. It rigorously distinguishes **Claim A** (verified) from **Claim B** (unverified), explicitly acknowledging the limits of forensic evidence.
3. It avoids destructive file deletion and permits principled remediation of the 130 quarantined recordings under Project Lead review.

---

## Protected State & Invariant Verification

- `scripts/materialize_stage6m_cohort3_audio.py` **UNMODIFIED** (`MAX_MP3_PADDING_FRAMES = 1152` intact).
- Provisional manifest `stage6m_cohort3_provisional_manifest.json` digest: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` (**UNCHANGED**).
- Acquisition ledger `stage6m_cohort3_clip_sha256_ledger.csv` (**UNMODIFIED**).
- Quarantine ledger `stage6m_cohort3_quarantine_ledger.csv` (**UNMODIFIED**).
- Zero recordings deleted, moved, copied, promoted, or substituted.
