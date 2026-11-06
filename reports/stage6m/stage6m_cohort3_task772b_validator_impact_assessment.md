# Stage 6M v1.5 Task 7.7.2B — Production Validator Impact Assessment and Non-Destructive Resolution Strategies

**Generated:** 2026-11-06 11:44:57 UTC
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
3. **Shortfall Origin & Generalized ID3v2 Estimation Formula:** Because no Xing/Info header exists, libsndfile / libmpg123 estimates duration using total file size.
   For an ID3v2 tag of $T$ bytes and audio payload of $A$ bytes, the approximate duration contribution is:
   $$\Delta_{\text{tag}} \approx T \times \frac{1152}{bpf}$$
   Accounting for integer truncation in the total-file-size formula, the exact contribution is:
   $$\Delta_{\text{tag}} = \left\lfloor\frac{(A+T)\times1152}{bpf}\right\rfloor - \left\lfloor\frac{A\times1152}{bpf}\right\rfloor$$
   where the estimator computes a constant integer BPF: $bpf = \lfloor(144000 \times \text{bitrate}) / \text{samplerate}\rfloor$:
   - **48 kHz / 64 kbps mono ($bpf = 192$ B):** $1152 / 192 = 6.000$ samples/byte ($T=33\text{ B} \to 198$, $T=45\text{ B} \to 270$, $T=142\text{ B} \to 852$, $T=161\text{ B} \to 966$).
   - **32 kHz / 48 kbps mono ($bpf = 216$ B):** $1152 / 216 = 5.333$ samples/byte ($T=45\text{ B} \to 240$, $T=142\text{ B} \to 757$, $T=146\text{ B} \to 778$, $T=172\text{ B} \to 917$, $T=175\text{ B} \to 933$).
   - **44.1 kHz / 64 kbps mono ($bpf = 208$ B):** The estimator BPF is strictly 208 bytes ($144000 \times 64 / 44100 = 208.9796 \to 208$). Physical MPEG frame sizes alternate between 208 and 209 bytes due to MPEG padding bits. The resulting shortfall separates into tag inflation ($\approx 45 \times (1152/208) \approx 249$ samples) and frame-padding/rounding residues across physical frames (yielding total observed shortfalls of 880 and 1,063 samples).
   - The acceptance boundary depends on each recording's BPF: $T_{\max} \approx bpf$ bytes, rather than a universal 192-byte limit.
4. **Potential False-Rejection Candidates:** All **130 quarantined recordings** exhibit complete, uncorrupted physical MPEG frames to EOF,
   zero sync loss, and successful error-free PCM decoding. They failed solely because of the 1,152 sample-frame threshold applied to an estimated header.
   Because authoritative original recording durations are unavailable, they are classified strictly as **potential false-rejection candidates**
   rather than proven false rejections. Proven false rejections are not established.
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
| **Accepted Cohort** | 18,845 | 18,845 | 18,845 / 18,845 (100.0%) | 672.31 MB | 9,069 - 181,473 bytes | 48,000 Hz (0) |
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

### Complete Accepted Population Histogram (18,845 / 18,845 Reconciled)

The complete census of all 18,845 accepted recordings falls into exactly 11 shortfall categories:

| Rank | Shortfall ($\Delta$) | Recording Count | Percentage | Representative Recording | Format Parameters | Tag Size ($T$) | Exact Contribution |
| :---: | :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | **270** | 9,080 | 48.18% | `common_voice_en_100703.mp3` | 48 kHz / 64 kbps mono ($bpf=192$) | 45 B | $45 \times 6 = 270$ |
| 2 | **198** | 4,119 | 21.86% | `common_voice_en_100704.mp3` | 48 kHz / 64 kbps mono ($bpf=192$) | 33 B | $33 \times 6 = 198$ |
| 3 | **240** | 3,917 | 20.79% | `common_voice_en_100708.mp3` | 32 kHz / 48 kbps mono ($bpf=216$) | 45 B | $45 \times (1152/216) = 240$ |
| 4 | **966** | 872 | 4.63% | `common_voice_en_118979.mp3` | 48 kHz / 64 kbps mono ($bpf=192$) | 161 B | $161 \times 6 = 966$ |
| 5 | **852** | 465 | 2.47% | `common_voice_en_124501.mp3` | 48 kHz / 64 kbps mono ($bpf=192$) | 142 B | $142 \times 6 = 852$ |
| 6 | **757** | 310 | 1.64% | `common_voice_en_135201.mp3` | 32 kHz / 48 kbps mono ($bpf=216$) | 142 B | $\lfloor 142 \times 5.333 \rfloor = 757$ |
| 7 | **917** | 64 | 0.34% | `common_voice_en_140201.mp3` | 32 kHz / 48 kbps mono ($bpf=216$) | 172 B | $\lfloor 172 \times 5.333 \rfloor = 917$ |
| 8 | **778** | 15 | 0.08% | `common_voice_en_155011.mp3` | 32 kHz / 48 kbps mono ($bpf=216$) | 146 B | $\lfloor 146 \times 5.333 \rfloor = 778$ |
| 9 | **880** | 1 | 0.01% | `common_voice_en_22593686.mp3` | 44.1 kHz / 64 kbps mono ($bpf=208$) | 45 B | Padding residue = 880 |
| 10 | **1063** | 1 | 0.01% | `common_voice_en_22593752.mp3` | 44.1 kHz / 64 kbps mono ($bpf=208$) | 45 B | Padding residue = 1063 |
| 11 | **933** | 1 | 0.01% | `common_voice_en_25353615.mp3` | 32 kHz / 48 kbps mono ($bpf=216$) | 175 B | $\lfloor 175 \times 5.333 \rfloor = 933$ |
| **Total** | — | **18,845** | **100.00%** | — | — | — | Exact census sum |

> [!NOTE]
> **Histogram Reconciliation:** Preliminary output listed the top 10 categories summing to 18,844.
> The complete census includes category 11: $\Delta = 933$ samples (1 recording: `common_voice_en_25353615.mp3`, size 21,127 B, ID3 tag 175 B at 32 kHz / 48 kbps).
> Summing all 11 categories yields exactly 18,845 recordings.

### Quarantined Shortfall Census Range and Reconciliation

- **Exhaustive Census Range:** **1,296 to 2,979 PCM sample frames** ($40.50\text{ ms}$ to $67.551\text{ ms}$)
  - **Minimum Shortfall File:** `common_voice_en_25321355.mp3` (Declared: 193,680, Decoded: 192,384, Shortfall: **1,296 frames** / $40.50\text{ ms}$, 32,000 Hz / 48 kbps mono, Size: 36,315 B)
  - **Maximum Shortfall File:** `common_voice_en_21907677.mp3` (Declared: 430,371, Decoded: 427,392, Shortfall: **2,979 frames** / $67.551\text{ ms}$, 44,100 Hz / 64 kbps mono, Size: 77,706 B)
  - **Median Shortfall:** 1,705 PCM sample frames.
- **Reconciliation of Preliminary 1,173–2,255 Range:**
  The preliminary figure of 1,173–2,255 frames was an informal theoretical approximation ($1,152 + 21$ to $\approx 2 \times 1,152$) based on pilot sample profiling prior to the full 130-file census.
  The exhaustive census of all 130 quarantined files confirms the exact span is 1,296 to 2,979 PCM sample frames ($40.50\text{ ms}$ to $67.551\text{ ms}$), in exact agreement with Task 7.7.1 triage results (`min_shortfall_pcm_frames: 1296`, `max_shortfall_pcm_frames: 2979`).
  The 27.0 ms figure previously cited in preliminary drafting resulted from an erroneous conversion assuming 48 kHz ($1296/48000 = 27.0\text{ ms}$); the actual recording `common_voice_en_25321355.mp3` has a 32 kHz sample rate ($1296/32000 = 40.50\text{ ms}$).

---

## False-Rejection Candidate Analysis

- **Potential False-Rejection Candidates:** **130 / 130** (100.0%)
- **Current Files with Complete Physical MPEG Frames:** **130 / 130** (100.0%)
- **Successfully Decoded Current Files:** **130 / 130** (100.0%)
- **Authoritative Original-Duration References:** **0 / 130** (0.00%)
- **Proven False Rejections:** **0** (Not established without master recording duration)
- **Reason for Rejection:** Shortfall exceeded 1,152 samples due to libmpg123 file-size estimation over non-audio ID3v2 tags.
- **Scientific Qualification:** In accordance with the Project Lead's ruling, these files are classified strictly as **potential false-rejection candidates**. They must not be labeled as proven false rejections or proven valid recordings.

---

## False-Acceptance Limitations (Claim A vs Claim B)

- **Claim A (Current File Structural Completeness):** Established for **18,845 / 18,845 accepted recordings** and **130 / 130 quarantined recordings**.
- **Claim B (Original Recording Completeness):** **UNVERIFIABLE** across all 18,975 recordings.
- **Task 7.7.2A Whole-Frame Truncation Demonstration:** In Case 8 of Task 7.7.2A, dropping complete MPEG audio frames produced a file that decoded
  perfectly, possessed valid frame boundaries, and exhibited zero physical structural errors. Therefore, complete-frame loss is inherently
  undetectable from bitstream structure alone.
- **Risk Statement:** Without an authoritative duration reference, the risk of undetected upstream whole-frame loss is **UNKNOWN** and must
  not be classified as low.

---

## Comparative Evaluation of Four Candidate Strategies

| Evaluation Criterion | Strategy A: Existing Rule | Strategy B: Decoded PCM Rule | Strategy C: Metadata-Aware Rule | Strategy D: Multi-Evidence Rule (Research Rec.) |
| :--- | :--- | :--- | :--- | :--- |
| **Core Formulation** | `shortfall <= 1152` | `decoded_frames > 0` and error-free | Tiered metadata consistency (Xing vs absent vs corrupt) | Multi-layer: Physical + PCM + Metadata + Master |
| **Evidence Required** | SoundFile header + PCM decode | PCM decode only | ID3v2 + MPEG parse + PCM decode + (Master for admission) | Full bitstream parse + PCM decode + Master ref |
| **Accepted Cohort Structural Pass** | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) |
| **Quarantined Current-File Structural Pass** | 130 / 130 (100.0%) | 130 / 130 (100.0%) | 130 / 130 (100.0%) | 130 / 130 (100.0%) |
| **Quarantined Confirmatory Admission** | **0 / 130 (0.0%) — REJECTED** | 130 / 130 (100.0%) — Admitted on decode only | **0 / 130 (0.0%) — HOLD** | **0 / 130 (0.0%) — HOLD** |
| **Quarantined Formal Classification** | REJECTED_BY_ESTIMATE | DECODED_PASS | `STRUCTURAL_PASS_ORIGIN_UNVERIFIED` | `STRUCTURAL_PASS_ORIGIN_UNVERIFIED` |
| **Non-Destructive Preservation** | **0 / 130** (Unlinked by materializer) | 130 / 130 PRESERVE | 130 / 130 PRESERVE (under HOLD) | **130 / 130 PRESERVE (under HOLD in quarantine)** |
| **Potential False Rejections** | High (130 structural-pass candidates rejected) | Minimal for estimation artifacts; non-zero overall | Low for structural pass; held for origin verification | Unknown / unquantified. Conservative HOLD may withhold intact files |
| **Upstream Truncation Risk** | UNKNOWN without master | UNKNOWN (truncation at boundaries undetected) | UNKNOWN without master | UNKNOWN without master; detects broken sync/partial frames |
| **What It Detects** | Shortfall against estimated header | Decode exceptions, empty streams | Incomplete final frames, sync loss, corrupt metadata | Partial frames, broken sync, corrupt headers |
| **What It Cannot Detect** | Whole-frame loss upstream; container inflation | Incomplete frames masked by decoder | Whole-frame loss upstream | Whole-frame loss upstream without master |
| **Fail-Closed Disposition** | Fails closed on estimate, rejecting valid files | Fails open on truncated complete frames | Fails closed on malformed metadata & partial frames | Fails closed on any structural or decode defect |
| **Implementation Complexity** | Zero (current code) | Low (remove shortfall check) | Moderate (requires bitstream parser) | Moderate-High (formal forensic inspection) |
| **Admission Disposition** | Discards 130 potential candidates | May admit upstream-shortened files | **HOLD (Origin Unverified)** | **HOLD (Origin Unverified)** |

### Research Recommendation & Non-Destructive Preservation Disposition

**Strategy D (Multi-Evidence Rule)** is the recommended research architecture for Stage 6M:
1. **Distinguishes Current-File Integrity from Origin Completeness:** Strategy D verifies that current physical MPEG frames are 100% complete
   (Claim A = PASS). Where authoritative original-duration evidence is unavailable, Claim B remains UNVERIFIED, and the admission outcome
   remains strictly indeterminate: `STRUCTURAL_PASS_ORIGIN_UNVERIFIED` with admission disposition **HOLD**.
2. **Evidence Tiers for Metadata & Completeness:**
   - *Valid Xing/LAME metadata & internally consistent frames:* Metadata consistency established (current stream only; not origin master proof).
   - *Metadata absent, physical frames complete:* Claim A passes; Claim B remains UNVERIFIED.
   - *Malformed metadata:* Requires rejection or deeper forensic investigation.
   - *No authoritative original-duration reference:* Confirmatory admission remains strictly HOLD.
3. **Research-Only Recommendation — Production Materializer Unchanged:**
   The assessment recommends a non-destructive HOLD/PRESERVE disposition for future validator remediation.
   This recommendation has not been implemented in the production materializer. Its existing unlink behavior
   (`dest_file.unlink(missing_ok=True)` in line 1049 of `scripts/materialize_stage6m_cohort3_audio.py`) remains unchanged
   and requires separate Project Lead authorization to modify.
4. **Historical Sequence of Quarantine Recovery:**
   - *Step 1 (Original Materialization):* The production validator rejected and unlinked the 130 recordings during initial archive extraction.
   - *Step 2 (Authorized Forensic Retrieval):* A subsequent authorized read-only extraction recovered the 130 recordings into `cohort3_rejected_quarantine`.
   - *Step 3 (Current Diagnostic Quarantine):* The 130 recordings are now safely preserved in diagnostic quarantine under a research-only PRESERVE disposition.
   - *Step 4 (Cohort Boundary Maintained):* Zero quarantined recordings have been promoted into the confirmatory cohort, and no speakers have been substituted.

---

## Protected State & Invariant Verification

- `scripts/materialize_stage6m_cohort3_audio.py` **UNMODIFIED** (`MAX_MP3_PADDING_FRAMES = 1152` intact).
- Provisional manifest `stage6m_cohort3_provisional_manifest.json` digest: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` (**UNCHANGED**).
- Acquisition ledger `stage6m_cohort3_clip_sha256_ledger.csv` (**UNMODIFIED**).
- Quarantine ledger `stage6m_cohort3_quarantine_ledger.csv` (**UNMODIFIED**).
- Zero recordings deleted, moved, copied, promoted, or substituted.
