# Stage 6M v1.5 Task 7.7.3E — Production Validator Remediation Proposal and Exact Bound Reconciliation

**Generated:** 2026-11-07T10:45:00+00:00<br>
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7, Project-Lead Academic Authorization)<br>
**Branch / Starting Commit:** `stage6m-five-stratum-parity` @ `949f9f1`<br>
**Document Status:** **SPECIFICATION_CLOSURE_PROPOSAL_ONLY** (Engineering architecture proposal only; production code unchanged)<br>

---

## Executive Summary

Task 7.7.2B demonstrated that the existing production validator (scripts/materialize_stage6m_cohort3_audio.py::validate_audio_file) enforces a duration shortfall tolerance (MAX_MP3_PADDING_FRAMES = 1152) against a duration estimate declared by soundfile / libmpg123. Because 100% of Mozilla Common Voice 27.0 recordings lack Xing/Info gapless metadata, libmpg123 computes declared frames from total file size. Non-audio container bytes (ID3v2 tags) inflate this estimate by Delta_tag = floor((A+T)*1152/bpf) - floor(A*1152/bpf) sample frames, causing 130 structurally intact recordings with error-free PCM decoding to exceed the threshold and suffer immediate destructive unlinking during archive extraction.

Task 7.7.3E proposes a decoupled two-layer validation and admission architecture coupled with an atomic, non-destructive staging materialization pipeline. Physical bitstream decodability (Layer 1) is strictly separated from research cohort admission (Layer 2). Classification is decoupled across 5 separate classification dimensions (Physical Structure, PCM Decode, Metadata Consistency, Origin Completeness, and Admission Decision). Destructive unlinking is completely eliminated in favor of diagnostic quarantine partitioning.

Crucially, the full-cohort audit revealed that zero authoritative original-duration references exist across the entire 18,975-recording population (0 / 18,975). If Claim B (original-source unshortened status) is made a mandatory prerequisite for confirmatory admission, exactly 0 recordings qualify. The proposal presents Policy 1 (Mandatory Claim B), Policy 2A (Pure Claim A Physical Admission), and Policy 2B (Decoupled Physical Validation with Estimation Discrepancy Screen) as explicit Project Lead decisions without unilaterally selecting any policy.

- **Historical Power Provenance Reconciliation:** Historical power simulation results at N_g = 220 are formally reconciled across three distinct milestones with exact Clopper-Pearson bounds:
  - **Result A: Task 5 Exploratory Screening (94.65% power, 2,000 trials, B=2,000 bootstrap; One-Sided 95% LCB = 93.747416%, Two-Sided 95% CI: [93.571456%, 95.595129%]; superseded coarse sweep).**
  - **Result B: Task 5 Uncalibrated Confirmation (95.35% power, 10,000 trials, B=20,000 bootstrap; One-Sided 95% LCB = 94.988733%, Two-Sided 95% CI: [94.918893%, 95.754440%]; uncalibrated model with Delta_D = -2.1733 pp overshoot; superseded full-depth confirmation).**
  - **Result C: Task 6.3 Calibrated Primary Confirmation (90.58% power, 10,000 trials, B=20,000 bootstrap; One-Sided 95% Clopper-Pearson LCB = 90.085739% >= 90.0000%; Two-Sided 95% CI: [89.990601%, 91.145641%]; strictly calibrated quadrature; approved Section 14.7 design result).**
  Under protocol convention, the one-sided LCB governs; the historical two-sided 95% CI lower endpoint of 89.990601% does not pass 90.0% on its own. The result remains conditional on registered data-generating treatment effect assumptions (Delta_D = -2.0 pp, Delta_A = Delta_B = -3.5 pp).
- **Role Separation Governance:** Admitting all 18,975 files as dataset assets (under Policy 2A) does NOT mean all 1,265 speakers participate in the confirmatory evaluation estimand. The 1,100 evaluation speakers, 100 gate-reference speakers, and 65 Australian reserve speakers strictly retain their distinct, pre-registered roles: evaluation speakers test confirmatory hypotheses; gate-reference speakers calibrate adaptation gating; reserve speakers remain unexposed.
- **Archive Replay Complexity & Durability:** Sequential .tar.gz archives cannot be seek-skipped in O(1). Resuming from byte 0 requires continuous decompression, TAR scanning, and in-memory hashing of previously committed members to verify integrity (no repeated disk writes or audio decoding occur, but decompression, TAR scanning, and hashing do occur; zero validation overhead is retracted). For crash durability, Windows promotion specifies MoveFileExW omitting MOVEFILE_REPLACE_EXISTING for atomic no-clobber, and MOVEFILE_WRITE_THROUGH where write-through durability is required. Directory metadata flush failures (fsync) transition the transaction to state DURABILITY_UNCERTAIN without deleting either copy, reconciling destination and journal by hash on restart. A single serialized journal writer records unique transaction IDs (tx_id).

---

## Section 1: Audit of Current Production Validator (`scripts/materialize_stage6m_cohort3_audio.py`)

The production materializer implements validation in `validate_audio_file(file_path: Path) -> Tuple[bool, str]` with hard-coded threshold `MAX_MP3_PADDING_FRAMES = 1152 (line 394)`.

### Current Execution Flow & Control Sequence

```text
[Archive Stream Ingest] -> [Direct Write to Destination: audio_dir/{rec_id}.mp3]
                        -> [validate_audio_file(dest_file)]
                             ├─ sf.info(dest_file) -> declared_frames (from total file size)
                             ├─ sf.SoundFile(dest_file).read() -> decoded_frames
                             └─ shortfall = declared_frames - decoded_frames
                        -> If shortfall > 1152:
                             └─ dest_file.unlink(missing_ok=True)  <-- DESTRUCTIVE UNLINK
```

### Architectural Defects in Existing Implementation

- **Coupling bitstream decodability with container estimation heuristics.:** Coupling bitstream decodability with container estimation heuristics.
- **Destructive unlinking of failed files without quarantine preservation.:** Destructive unlinking of failed files without quarantine preservation.
- **Lack of intermediate staging directory and transactional journal.:** Lack of intermediate staging directory and transactional journal.
- **Direct in-place extraction to production destinations.:** Direct in-place extraction to production destinations.

---

## Section 2: Decoupled Multi-Dimensional Validation & Admission Model

To resolve the conflation between bitstream integrity and research eligibility, the proposal decouples validation across 5 separate classification dimensions:

```mermaid
graph TD
    A[Incoming Tar Member Stream] --> B[Dim 1: Physical MPEG Bitstream Parser]
    B -->|Corrupt Frame / Lost Sync / Truncated EOF| C[STRUCTURAL_FAIL_*]
    B -->|Frames Complete to EOF + Valid Sync| D[STRUCTURAL_PASS]
    D --> E[Dim 2: Complete Stream PCM Decoder]
    E -->|Decode Abort / Zero Frames| F[PCM_DECODE_ERROR]
    E -->|Decoder Disagreement on Padding/Delay| G[PCM_DECODE_INCONCLUSIVE]
    E -->|Clean Decode without Error| H[PCM_DECODE_CLEAN]
    H --> I[Dim 3: Metadata Consistency Parser]
    I -->|No Xing/Info| J[METADATA_ABSENT]
    I -->|Xing Frames Disagree with MPEG Frames| K[METADATA_ANOMALY]
    I -->|Xing Matches Physical Frames| L[METADATA_CONSISTENT]
    H --> M{Dim 4: Original Source Completeness (Claim B)}
    M -->|Authoritative Master Duration Verified| N[ORIGIN_VERIFIED -> CONFIRMATORY_ADMIT]
    M -->|Master Duration Absent / Common Voice 27.0| O[ORIGIN_UNVERIFIED]
    O --> P{Dim 5: Protocol Admission Governance}
    P -->|Policy 1: Mandatory Claim B| Q[ADMISSION_HOLD (All 18,975)]
    P -->|Policy 2A: Pure Claim A Admission| R[PROTOCOL_ADMIT_ORIGIN_UNVERIFIED (All 18,975)]
    P -->|Policy 2B: Estimation Discrepancy Screen| S[PROTOCOL_ADMIT (18,845) + ADMISSION_HOLD (130)]
    C --> T[PRESERVE in Diagnostic Quarantine]
    F --> T
    G --> T
    K --> T
    Q --> T
    N --> U[ADMIT to cohort3_audio]
    R --> U
    S --> U
```

### The 5 Classification Dimensions

#### Dimension 1: Physical MPEG Bitstream Structure
- `STRUCTURAL_PASS`: Every frame header valid (`0xFFE`/`0xFFF`); zero lost sync words; final frame complete to EOF.
- `STRUCTURAL_FAIL_TRUNCATED_BITSTREAM`: Final MPEG frame has missing bytes at EOF.
- `STRUCTURAL_FAIL_SYNC_LOST`: MPEG synchronization word corrupted or lost mid-stream.
- `STRUCTURAL_FAIL_NON_AUDIO`: Empty file (0 bytes), invalid container headers, or non-MPEG payload.

#### Dimension 2: PCM Decoder Outcome
- `PCM_DECODE_CLEAN`: Decoder processed all physical frames without error; `total_decoded_frames > 0`; sample rate & channels within bounds.
- `PCM_DECODE_ERROR`: Decoder aborted, raised exception, or returned zero decoded frames.
- `PCM_DECODE_INCONCLUSIVE`: Disagreement between reference decoders (e.g. SoundFile vs libmpg123/FFmpeg) regarding padding/delay without established bitstream corruption.

#### Dimension 3: Metadata Consistency
- `METADATA_ABSENT`: No Xing/Info/LAME header present (standard profile for 100% of Common Voice 27.0 CBR audio).
- `METADATA_CONSISTENT`: Xing/Info header present and declared frames match physical MPEG frame count exactly.
- `METADATA_ANOMALY`: Xing/Info header present but declared frames disagree with physical frame count; physical bitstream intact.
- `METADATA_CORRUPT`: Malformed or illegal Xing/Info header structure.

#### Dimension 4: Original-Source Completeness (Claim B)
- `ORIGIN_VERIFIED`: Authoritative uncompressed master duration reference exists and confirms zero upstream whole-frame truncation.
- `ORIGIN_UNVERIFIED`: No authoritative master reference exists; upstream whole-frame truncation cannot be ruled out from bitstream alone.

#### Dimension 5: Protocol Admission Decision
- `CONFIRMATORY_ADMIT`: Admitted to confirmatory cohort. Strictly requires `ORIGIN_VERIFIED`.
- `PROTOCOL_ADMIT_ORIGIN_UNVERIFIED`: Admitted to confirmatory cohort under explicit Project Lead protocol governance acknowledging `ORIGIN_UNVERIFIED`.
- `ADMISSION_HOLD`: Preserved safely in diagnostic quarantine; withheld from confirmatory cohort pending verification or remediation.
- `ADMISSION_REJECT`: Preserved in diagnostic quarantine; permanently rejected from confirmatory research due to physical bitstream defect.

> [!IMPORTANT]
> **Decoupling Invariants:**
> 1. **Malformed Metadata != Physical Bitstream Corruption:** A malformed Xing/Info header is classified as `METADATA_ANOMALY` or `METADATA_CORRUPT`. If physical MPEG frames and PCM decoding are clean, the recording is structurally valid and placed on `ADMISSION_HOLD`, not falsely marked as bitstream-corrupt.
> 2. **Decoder Disagreement Initially Inconclusive:** Disagreements between decoders are classified as `PCM_DECODE_INCONCLUSIVE` and placed on `ADMISSION_HOLD` pending investigation, rather than treated as an immediate bitstream failure.
> 3. **No Unverified Recording Labeled CONFIRMATORY_PASS:** Because 0 / 18,975 recordings have verified Claim B, no recording can be labeled `CONFIRMATORY_PASS` without an authoritative master. Any admission under Policy 2A or 2B is explicitly labeled `PROTOCOL_ADMIT_ORIGIN_UNVERIFIED`.

---

## Section 3: Non-Destructive Materialization Architecture & Crash Recovery

The proposed materialization pipeline completely eliminates in-place extraction and destructive unlinking:

### 8-Stage Staging Pipeline

1. **Stage 1 — Streaming Archive Ingest:** Extract member stream to .staging/in_flight/{rec_id}_{attempt_id}.part.<br>
   *Invariant:* Never write directly to production directories.
1. **Stage 2 — Container & Size Sanitization:** Check size > 0 and header magic.<br>
   *Invariant:* Empty files diverted to quarantine as FAIL_EMPTY_FILE.
1. **Stage 3 — Diagnostic Parsing & PCM Decoding:** Run MPEG frame parser and full SoundFile PCM decode.<br>
   *Invariant:* No file deletion regardless of decoder outcome.
1. **Stage 4 — Five-Dimensional Classification:** Assign 5 classification states and determine quarantine destination.<br>
   *Invariant:* State assignment recorded in memory structure.
1. **Stage 5 — Pre-Promotion WAL Journal Append:** Write PREPARED record with tx_id to .staging/wal_journal.jsonl and flush.<br>
   *Invariant:* WAL write precedes any promotion action.
1. **Stage 6 — Same-Volume Atomic Promotion:** Execute MoveFileExW (Windows) or hardlink+unlink (POSIX) to final destination.<br>
   *Invariant:* Atomic move; destination never clobbered or overwritten.
1. **Stage 7 — Directory Metadata Flush & Verification:** Call fsync on destination directory. On failure, transition to DURABILITY_UNCERTAIN.<br>
   *Invariant:* Preserve both staging and destination if flush fails.
1. **Stage 8 — Post-Promotion WAL Commit & Ledger Projection:** Write COMMITTED record to WAL; idempotently append row to CSV ledger.<br>
   *Invariant:* CSV ledgers are reproducible projections of authoritative WAL.

### Engineering Resilience & Failure Recovery

| Resilience Dimension | Engineered Design & Failure Handling | Protection Invariant |
| :--- | :--- | :--- |
| **Archive Replay Complexity** | In a sequential .tar.gz archive, compressed bytes form a continuous DEFLATE bitstream without random-access sync points. On restart from byte 0: the client sequentially replays decompression and TAR member scanning. To verify previously committed members against recorded ledger hashes, their decompressed payload must still be streamed and hashed in memory. Thus: NO REPEATED DISK WRITES and NO REPEATED AUDIO DECODING occur for committed members, but DECOMPRESSION, TAR SCANNING, and IN-MEMORY HASH COMPUTATION DO OCCUR. True O(1) random-access requires an external index. The claim of zero validation overhead is formally retracted. | Decompression + hashing; no disk rewrite. |
| **Windows Atomic Promotion Flags** | On Windows, atomic no-clobber promotion must use MoveFileExW with flag 0 (omitting MOVEFILE_REPLACE_EXISTING), which fails atomically with ERROR_ALREADY_EXISTS if the target exists. Where write-through durability is required, the implementation must additionally specify MOVEFILE_WRITE_THROUGH. The implementation specification explicitly distinguishes no-replace behavior from write-through durability. | Distinct no-replace and write-through flags. |
| **Durability Uncertain State** | In Scenario 20 (filesystem metadata flush failure): if promotion succeeds (destination link exists) but directory metadata fsync fails, promotion cannot simply be 'aborted and staged file retained' because the destination link already exists on disk. The pipeline transitions the recording to state DURABILITY_UNCERTAIN: 1. Retain both staging and destination copies without unlinking either. 2. Write a DURABILITY_UNCERTAIN record to the WAL journal with unique tx_id. 3. Stop further materialization. 4. On restart, the reconciliation sweep verifies destination file existence and SHA-256 against staging; if identical, completes    ledger write and removes redundant staging link. Zero acquired copies are deleted. | Both copies retained on fsync failure; zero data loss. |
| **WAL Transaction Architecture** | The Write-Ahead Log (.staging/wal_journal.jsonl) establishes a unique transaction/event ID (tx_id = uuid4 or monotonic counter) with a single serialized journal writer. Each entry records: tx_id, timestamp, recording_id, attempt_id, staging_path, target_path, sha256, status. Ledger writes must be replayable without duplicate rows. The WAL is the authoritative recovery record, with the CSV ledgers treated as reproducible, idempotent projections. On startup, torn or partial final lines are discarded; uncommitted PREPARED records inspect destination existence and reconcile idempotently. | Unique tx_id; serialized writer; reproducible ledgers. |
| **Preservation of Acquired Copies** | Zero unlinking strictly means NEVER DELETING THE ONLY ACQUIRED COPY of an audio recording. Removing a redundant staging hard-link after verified, fsynced destination creation does not violate evidence preservation. | Never delete only acquired physical copy. |
| **Interrupted Staging Attempts** | If extraction is interrupted by process crash or network drop, the incomplete .part file is preserved in .staging/interrupted/{rec_id}_{attempt_id}.part with its partial byte count and partial SHA-256 logged. On restart, retries allocate a new attempt ID without deleting prior attempts. | Zero unlinking; all acquired copies preserved. |
| **Duplicate Archive Members** | If the same recording ID appears multiple times: compute SHA-256 of new member. If identical to existing record, log DUPLICATE_SKIPPED and preserve staging copy. If conflicting, move to collision quarantine. | Idempotent handling; conflicting hashes quarantined. |
| **Zero-Byte Members** | Zero-byte members are detected at Stage 2, moved to quarantine as FAIL_EMPTY_FILE, and never admitted. | Quarantined; never admitted. |
| **Disk Exhaustion** | Pre-flight capacity check verifies free disk space exceeds uncompressed cohort estimate plus 20% safety margin. | Pre-flight check fails closed before staging. |

---

## Section 4: Comparative Evaluation of Four Candidate Validation Strategies

| Dimension | Strategy A: Existing Threshold | Strategy B: Decoded PCM Only | Strategy C: Metadata-Aware Tiered | Strategy D: Multi-Evidence Architecture (Research Candidate) |
| :--- | :--- | :--- | :--- | :--- |
| **Core Formulation** | Threshold check: sf.info declared frames - sf.read PCM frames <= 1152 samples. | Verify soundfile / libmpg123 decodes without error and yields non-zero samples. | Calculate Delta_tag = floor((A+T)*1152/bpf) - floor(A*1152/bpf); verify shortfall <= Delta_tag + 1152. | Independent verification of physical frames, PCM decoding, metadata, and origin completeness. |
| **Evidence Required** | soundfile declared frames and decoded frames. | Complete stream PCM decoding outcome. | ID3v2 header tag size + soundfile info + PCM frames. | Physical bitstream parser + PCM decoder + metadata parser + external master reference. |
| **Accepted Cohort Pass** | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0%) | 18,845 / 18,845 (100.0% Claim A) |
| **Quarantine Cohort Pass** | 0 / 130 (0.0%) | 130 / 130 (100.0%) | 130 / 130 (100.0%) | 130 / 130 (100.0% Claim A) |
| **Potential False Rejections** | 130 recordings rejected solely due to ID3v2 tag padding. | 0 recordings rejected. | 0 recordings rejected. | 0 recordings rejected for container tag padding. |
| **Potential False Acceptances** | Misses upstream whole-frame truncation in 100% of accepted files. | Admits truncated files if decoder gracefully terminates. | Admits files where upstream truncation happens to match tag size. | 0 physical false acceptances; origin completeness explicitly unverified. |
| **What It Detects** | Large discrepancy between container file size and decoded PCM frames. | Fatal bitstream corruption preventing PCM decoding. | Container-induced estimation discrepancy; confirms tag accounts for shortfall. | Physical frame truncation, sync loss, decoder aborts, tag inflation, metadata anomalies. |
| **What It Cannot Detect** | Physical MPEG bitstream validity; tag inflation offset; upstream truncation. | Truncated final frames, header-decoder frame count mismatches, upstream truncation. | Does not verify physical frame synchronization or EOF completeness. | Upstream whole-frame truncation cannot be detected without external master (governed by Claim B). |
| **Fail-Closed Posture** | Destructively unlinks on fail; fails open to upstream truncation. | Permissive; relies entirely on decoder resilience. | Moderate; mathematically bounded heuristic. | Strict fail-closed: defective frames quarantined; intact frames admitted with explicit provenance. |
| **Implementation Complexity** | Low (current 25-line function). | Low (minimal code changes). | Moderate (requires ID3v2 tag parser and BPF lookup). | High (multi-layer parser, staging pipeline, WAL journal). |
| **Runtime Overhead** | Baseline (~5.7 ms / file). | Low (~5.5 ms / file). | Low (+0.3 ms / file). | Moderate (+0.8 ms / file; ~165 files/sec throughput). |
| **Overall Assessment** | DEFECTIVE: Conflates container tags with corruption; causes destructive unlinking. | INSUFFICIENT: Blind to physical framing and partial final frame truncation. | DIAGNOSTIC CANDIDATE: Explains discrepancy, but preserves heuristic framework. | RECOMMENDED RESEARCH SPECIFICATION: Pure separation of physics and protocol. |

### Scope of the Diagnostic libmpg123 Duration Estimation Formula

In Tasks 7.7.2A and 7.7.2B, the research audit established that the duration shortfall observed in SoundFile is governed by:
$$\Delta_{\text{tag}} = \left\lfloor \frac{(A + T) \cdot 1152}{bpf} \right\rfloor - \left\lfloor \frac{A \cdot 1152}{bpf} \right\rfloor$$

> [!IMPORTANT]
> **Explicit Scope Limitation:** This formula is specific to the investigated **fixed-BPF, file-size-based duration estimation path** in `libsndfile` / `libmpg123` when Xing/Info metadata is absent. It is a diagnostic model of observed libmpg123 estimation behavior, **not** a universal duration formula for arbitrary variable-bitrate MP3 files.

---

## Section 5: Power Provenance, Sampling Reconciliation & Incomplete-Speaker Analysis

### 5.1 Historical Power Provenance Reconciliation at $N_g = 220$ (Phase 1)

Three distinct simulation results exist in the Stage 6M archive for the primary design sample size of $N_g = 220$ evaluation speakers per stratum ($1,100$ evaluation speakers total). To ensure historical and forensic precision, they are distinguished as follows:

| Result ID | Historical Milestone & Source | Trials ($k/n$) | Joint Power | Exact One-Sided 95% LCB | Exact Two-Sided 95% CI | Historical Stored Field (`lcb_95`) | Scientific Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **RESULT_A** | **Task 5 Exploratory Screening**<br>[`stage6m_v1_5_sample_size_power_sweep.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_5_sample_size_power_sweep.json) | 1,893 / 2,000 | **94.65%** | **93.747416%** | `[93.571456%, 95.595129%]` | Stored lcb_95: 0.93571 (= two-sided lower endpoint) | **SUPERSEDED (Exploratory Screening)** |
| **RESULT_B** | **Task 5 Uncalibrated Confirmation**<br>[`stage6m_v1_5_scientific_readiness_audit.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_5_scientific_readiness_audit.json) | 9,535 / 10,000 | **95.35%** | **94.988733%** | `[94.918893%, 95.754440%]` | Stored lcb_95: 0.94919 (= two-sided lower endpoint) | **SUPERSEDED (Uncalibrated Confirmation)** |
| **RESULT_C** | **Task 6.3 Calibrated Confirmation**<br>[`stage6m_v1_5_primary_model_power_consistency.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_5_primary_model_power_consistency.json) | 9,058 / 10,000 | **90.58%** | **90.085739%** | `[89.990601%, 91.145641%]` | Stored one_sided_95_lcb: 90.09% / CI: [89.99%, 91.15%] | **APPROVED DESIGN RESULT (Section 14.7)** |

#### Exact Clopper-Pearson Bounds vs. Historical Field Naming

1. **Mathematical Definitions of Confidence Quantiles:**
   - **Exact One-Sided 95% Lower Confidence Bound (LCB):**
     $$\text{LCB}_{0.95} = \operatorname{Beta}^{-1}(0.05;\, k,\, n - k + 1)$$
   - **Exact Two-Sided 95% Confidence Interval Endpoints:**
     $$L_{\text{2-sided}} = \operatorname{Beta}^{-1}(0.025;\, k,\, n - k + 1), \quad U_{\text{2-sided}} = \operatorname{Beta}^{-1}(0.975;\, k + 1,\, n - k)$$
2. **Legacy Field-Naming Issue in Task 5 JSON Artifacts:**
   - In both [`stage6m_v1_5_sample_size_power_sweep.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_5_sample_size_power_sweep.json) and [`stage6m_v1_5_scientific_readiness_audit.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_5_scientific_readiness_audit.json), the generation scripts called `clopper_pearson_interval(...)` with two-sided tail $\alpha/2 = 0.025$, and stored the lower return value into the JSON field named `lcb_95` ($93.571\%$ and $94.919\%$, respectively).
   - These stored values are mathematically the lower endpoints of two-sided 95% confidence intervals, **not** one-sided 95% LCBs.
   - The historical JSON files remain untouched and immutable to preserve archival integrity.
   - Recalculating using the exact one-sided Beta quantile yields: Result A One-Sided 95% LCB = **93.747416%**, Result B One-Sided 95% LCB = **94.988733%**.
3. **Result C Upper Endpoint & Registered Criterion Reconciliation:**
   - Standard exact Clopper-Pearson calculation for $k = 9,058$, $n = 10,000$ yields two-sided 95% CI $[89.990601\%,\, 91.145641\%]$, matching [`stage6m_v1_5_mc_acceptance_rule_audit.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_5_mc_acceptance_rule_audit.json). The previous upper endpoint report of $91.146603\%$ is reconciled and corrected to **$91.145641\%$**.
   - The approved primary design strictly passes under the registered one-sided 95% LCB criterion ($90.085739\% \ge 90.0000\%$). The historical two-sided lower endpoint ($89.990601\%$) has a shortfall of $-0.0094$ pp and does not meet the $90.0\%$ threshold on its own.

#### Detailed Findings by Simulation Result

- **Result A — Task 5 Exploratory Screening (94.65%):** Task 5 exploratory screening sweep across N_g in [220, 285] evaluated at 2,000 outer trials and B=2,000 bootstrap replicates. At N_g=220, reported 94.65% joint power (1,893 / 2,000 trials). Exact one-sided 95% LCB is 93.747416%; exact two-sided 95% CI is [93.571456%, 95.595129%]. Legacy source artifact stored 93.571% in field 'lcb_95', which was the two-sided lower endpoint. This was an uncalibrated coarse screening sweep designed to map the feasibility trajectory, not a confirmatory evaluation. FORMALLY SUPERSEDED.
- **Result B — Task 5 Uncalibrated Full-Depth Confirmation (95.35%):** Task 5 uncalibrated full-depth confirmation evaluated at 10,000 outer trials and B=20,000 bootstrap replicates. At N_g=220, reported 95.35% joint power (9,535 / 10,000 trials). Exact one-sided 95% LCB is 94.988733%; exact two-sided 95% CI is [94.918893%, 95.754440%]. Legacy source artifact stored 94.919% in field 'lcb_95', which was the two-sided lower endpoint. Although run at full confirmatory depth, it employed the uncalibrated generator where probability clipping caused an artificial overshoot in disparity reduction (realized Delta_D = -2.1733 pp vs nominal -2.0 pp). FORMALLY SUPERSEDED.
- **Result C — Task 6.3 Calibrated Primary-Model Confirmation (90.58%):** Task 6.3 calibrated-model confirmation evaluated at 10,000 outer trials and B=20,000 bootstrap replicates strictly targeting the pre-registered treatment effect (Delta_D = -2.0000 pp, Delta_A = Delta_B = -3.5 pp). Formally confirmed 90.58% joint power (9,058 / 10,000 trials). Exact One-Sided 95% Clopper-Pearson LCB is 90.085739% (>= 90.0000% -> PASS by +0.0857 pp / +8 trials). Exact two-sided 95% CI is [89.990601%, 91.145641%]. Under the protocol's one-sided LCB convention, the design passes; the two-sided lower endpoint (89.990601%, shortfall -0.0094 pp) does not pass the 90% criterion on its own. Governing result for approved Section 14.7 primary design.

#### Attribution & Provenance Guardrails

- **Rule 1:**  Result A (94.65%) must strictly be labeled exploratory screening (2,000 trials, B=2,000 bootstrap replicates, one-sided 95% LCB = 93.747416%, two-sided 95% CI
- **Rule 2:**  Result B (95.35%) must strictly be labeled full-depth uncalibrated confirmation (10,000 trials, B=20,000 replicates, one-sided 95% LCB = 94.988733%, two-sided 95% CI
- **Rule 3:**  Result C (90.58%) must strictly be labeled Task 6.3 calibrated confirmation (10,000 trials, B=20,000 replicates, one-sided 95% LCB = 90.085739%, two-sided 95% CI
- **Rule 4:**  Both uncalibrated results (A & B) are formally identified as superseded.
- **Rule 5:**  The 90.58% calibrated result remains the sole approved design result for N_g = 220 under Section 14.7.
- **Rule 6:**  No historical result is silently deleted, conflated, or rewritten.

> [!IMPORTANT]
> **CRITICAL SCIENTIFIC CAVEAT: The 90.58% joint power result is strictly conditional on realizing the hypothesized population treatment profile (true disparity narrowing of -2.0 pp and superiority of -3.5 pp). If true disparity narrowing is <= -1.0 pp, simulated joint power degrades below 50%. These estimates represent design scenario targets rather than physical guarantees.**

### 5.2 Side-by-Side Sampling Architecture Comparison

| Sampling Dimension | Approved Protocol v1.5 Spec | Task 6.3 Calibrated Confirmation | Provisional Manifest (`provisional_manifest.json`) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Governing Benchmark Strata** | 5 Strata (Australian, Canadian, England, South Asian, US) | 5 Strata evaluated across N_g in [220, 285] | 5 Strata (Australian, Canadian, England, South Asian, US) | **CONGRUENT** |
| **Confirmatory Evaluation Speakers** | 1,100 speakers (N_g = 220 per stratum) | N_g = 220: Confirmed 90.58% joint power (LCB_95 = 90.085739%) | 1,100 evaluation speakers (220 per stratum x 5) | **CONGRUENT** |
| **Clips per Speaker (Cluster Size C)** | C = 15 clips per speaker | C = 15 clips per speaker (sigma_paired = 0.032 speaker-level) | 15 clips per speaker (100% of selected speakers) | **CONGRUENT** |
| **Gate-Reference Speaker Reserve** | 100 speakers (20 per stratum; excluded from eval power) | 20 reserved gate speakers deducted from capacity ceiling | 100 gate-reference speakers (20 per stratum x 5) | **CONGRUENT** |
| **Australian Replacement Reserve** | 65 speakers (standby pool against Australian dropouts) | 65 reserve speakers unexposed during primary eval | 65 Australian reserve speakers (15 clips/speaker = 975 clips) | **CONGRUENT** |
| **Total Materialized Speakers** | 1,265 speakers (1,100 eval + 100 gate + 65 reserve) | Capacity envelope bounded by Australian N_total <= 305 | 1,265 speakers (1,100 eval + 100 gate + 65 reserve) | **CONGRUENT** |
| **Total Materialized Audio Clips** | 18,975 clips (1,265 x 15) | Not directly modeled (clip count fixed at 15/speaker) | 18,975 clips (16,500 eval + 1,500 gate + 975 reserve) | **CONGRUENT** |

### 5.3 Incomplete Speaker Analysis & Statistical Consequences (Phase 2)

#### Census of Affected Evaluation Speakers

- **Total Materialized Speakers:** 1,265 speakers (1,100 eval + 100 gate + 65 reserve)
- **Evaluation Speakers with 15/15 Clips Fully Intact:** **1,087 / 1,100 speakers (98.82%)**
- **Affected Evaluation Speakers:** **13 speakers** (Canadian: 5, US: 5, Australian: 2, England: 1, South Asian: 0)
- **Empty Clusters ($C_i = 0$):** **4 speakers** (0 clips retained)
- **Partial Clusters ($1 \le C_i \le 14$):** **9 speakers** (65 accepted clips retained)
- **Quarantined Clips across Affected Speakers:** Exactly **130 clips**

#### Per-Stratum Evaluation Speaker Counts under Policy 2B

| Stratum | Registered Target ($N_g$) | Option A: Complete Clusters ($C_i = 15$) | Option B: Non-Empty Clusters ($C_i \ge 1$) | Option A Delta | Option B Delta |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 220 | **218** | **220** | -2 | 0 |
| **Canadian English** | 220 | **215** | **217** | -5 | -3 |
| **England English** | 220 | **219** | **220** | -1 | 0 |
| **South Asian English** | 220 | **220** | **220** | 0 | 0 |
| **US English** | 220 | **215** | **219** | -5 | -1 |
| **Total Evaluation Speakers** | 1100 | **1087** | **1096** | -13 | -4 |

#### Statistical & Power Consequences

CRITICAL STATISTICAL FINDING: Under Policy 2B, neither Option A (complete clusters only) nor Option B (unequal clusters) preserves the full registered N_g = 220 design across all strata. Option A results in cross-stratum speaker sample size imbalance (N_g in [215, 220], total 1,087 speakers), while Option B retains more recordings (65 accepted clips across 9 partial clusters) but introduces nine unequal-size speaker clusters (C_i in [1, 14] for 9 speakers, total 1,096 speakers). Under Option B, the statistical analysis must formally define whether speakers or recordings receive equal weighting and how the paired-cluster bootstrap handles those unequal cluster sizes (e.g. cluster-level resampling vs ratio estimation). The approved Task 6.3 joint power of 90.58% applies strictly to the balanced N_g = 220, C = 15 specification. Therefore, NEITHER OPTION CAN INHERIT THE APPROVED 90.58% POWER RESULT WITHOUT A FORMAL RE-EVALUATION. A dedicated Monte Carlo power simulation would be required to verify whether Option A or Option B maintains the one-sided 95% LCB >= 90.0% threshold.

#### Replacement Reserve Feasibility (Option C Nuance)

OPTION C STRUCTURAL SCOPE: The provisional manifest contains 65 replacement reserve speakers for Australian English ONLY. These 65 Australian reserves may potentially replace the 2 affected Australian evaluation speakers (restoring Australian English to 220 complete speakers), strictly subject to the protocol's replacement conditions. However, the manifest contains ZERO replacement reserves for Canadian (5 affected), US (5 affected), or England (1 affected). The Australian reserves cannot replace Canadian, US, or England speakers without destroying accent stratum validity. Therefore, full cohort restoration through the reserve is structurally impossible without a formal protocol amendment and drawing from unexposed Common Voice pools.

### 5.4 Admission Policy Formulation & Role Terminology (Phase 3)

#### Dataset-Asset Admission vs. Confirmatory Evaluation Participation

CRITICAL GOVERNANCE DISTINCTION: Admitting all 18,975 recordings into the dataset assets (e.g. under Policy 2A) does NOT mean all 1,265 speakers participate in the confirmatory evaluation estimand. The 1,100 evaluation speakers, 100 gate-reference speakers, and 65 Australian reserve speakers strictly retain their distinct, pre-registered roles: - Evaluation Speakers (1,100): Exclusively evaluated in Primary Hypothesis Testing (Events A, B, C, D). - Gate-Reference Speakers (100): Exclusively calibrate adaptation gating; never evaluated in WER contrast estimands. - Australian Reserve Speakers (65): Standby pool for authorized dropouts; unexposed during primary confirmatory execution.

#### Refining Policy 2B as an Estimation Discrepancy Screen

Policy 2B is formally designated an ESTIMATION_DISCREPANCY_SCREEN (or ESTIMATION_SHORTFALL_HOLD). The shortfall threshold (Delta > 1152 samples / 24-67.5 ms) represents an inherited duration-estimation discrepancy arising from non-audio container bytes. It is NOT evidence of physical bitstream corruption or upstream whole-frame truncation. The 130 recordings are held under ADMISSION_HOLD in diagnostic quarantine as an empirical discrepancy anomaly, and any scientific decision regarding their eventual admission requires separate Project Lead authorization.

#### Comparative Policy Formulation Matrix

| Policy Option | Decision Status | Governing Admission Rule | Admitted Clips | Quarantined Clips | Evaluated Speakers ($N_{\text{eval}}$) | Operational & Epistemic Consequences |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Strict Mandatory Claim B Prerequisite** (`POLICY_1`) | *Project Lead Protocol Decision (Option 1)* | Confirmatory cohort admission strictly requires an independent, authoritative uncompressed original duration reference. | **0** | **18,975** | **0** | Because Mozilla Common Voice 27.0 does not distribute uncompressed master WAV recordings or external duration ledgers, exactly zero recordings can satisfy Claim B. Under Policy 1, the entire cohort of 18,975 recordings must be placed on ADMISSION_HOLD. Confirmatory execution of Stage 6M Cohort 3 cannot proceed without sourcing external master references. |
| **Pure Claim A Physical Bitstream Admission** (`POLICY_2A`) | *Project Lead Protocol Decision (Option 2A)* | Admit to confirmatory cohort under PROTOCOL_ADMIT_ORIGIN_UNVERIFIED IF current-file physical MPEG frames are complete to EOF and PCM decoding succeeds without error. Treat the 130 quarantined recordings under the identical rule as the 18,845 accepted recordings. | **18,975** | **0** | **1,265** | All 18,975 recordings meet the physical and decoding criteria. Exactly 18,975 recordings are admitted as dataset assets. Restores all 1,100 evaluation speakers to full 15-clip clusters. Upstream whole-frame loss is governed as a known dataset-level limitation. Gate-reference (100) and reserve (65) speakers strictly retain their non-evaluative roles. |
| **Decoupled Physical Validation with Estimation Discrepancy Screen** (`POLICY_2B`) | *Project Lead Protocol Decision (Option 2B)* | Admit recordings that pass physical completeness AND exhibit container shortfall Delta <= 1152 samples. Hold recordings exhibiting Delta > 1152 samples under ADMISSION_HOLD in diagnostic quarantine as an empirical duration estimation discrepancy anomaly (ESTIMATION_DISCREPANCY_SCREEN / ESTIMATION_SHORTFALL_HOLD). | **18,845** | **130** | **1,252** | Permits confirmatory research to proceed on the 18,845 baseline recordings whose physical bitstreams and decoded PCM are 100% complete and verified against the frozen acquisition ledger. Exactly 1,252 of 1,265 speakers (98.97%) have all 15 clips intact (1,087 evaluation, 100 gate-reference, 65 reserve). The 130 quarantined recordings (affecting 13 evaluation speakers) remain preserved in diagnostic quarantine under ADMISSION_HOLD pending separate remediation authorization (Task 7.7.4). Analysis of evaluation speakers proceeds under Option A (1,087 complete speakers) or Option B (1,096 non-empty speakers), both requiring a new power re-evaluation. |

---

## Section 6: Comprehensive Adversarial Validation Matrix (23 Scenarios)

> [!WARNING]
> **All 23 scenarios represent a proposed test matrix for future validation suites. They do NOT constitute proof that the proposed staging, atomic promotion, crash recovery, and ledger reconciliation pipeline has passed those tests, because that pipeline is currently in proposal status and has not yet been implemented.**

| Scenario ID | Category | Input Condition / Edge Case | Dim 1: Physical Structure | Dim 2: PCM Decode | Dim 3: Metadata | Dim 4: Origin (Claim B) | Dim 5: Admission Decision | Preservation Action |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `SCEN-01` | **Container / Framing** | Headerless CBR MP3 (standard Common Voice stream) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **PRESERVE** |
| `SCEN-02` | **Container / Framing** | Headerless VBR MP3 (varying bitrate headers without Xing) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **PRESERVE** |
| `SCEN-03` | **Metadata / Header** | Corrupt Xing header declared frames (declared != physical) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ANOMALY` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **PRESERVE** |
| `SCEN-04` | **Truncation / Incomplete** | Mid-frame truncation at EOF (last frame missing bytes) | `STRUCTURAL_FAIL_TRUNCATED_BITSTREAM` | `PCM_DECODE_ERROR` | `N/A` | `INELIGIBLE` | **ADMISSION_REJECT** | **PRESERVE** |
| `SCEN-05` | **Truncation / Incomplete** | Zero-byte file (empty member in tar) | `STRUCTURAL_FAIL_NON_AUDIO` | `PCM_DECODE_ERROR` | `N/A` | `INELIGIBLE` | **ADMISSION_REJECT** | **QUARANTINE_EMPTY_FILE** |
| `SCEN-06` | **Bitstream Corruption** | Mid-stream sync-word corruption (0xFFE/0xFFF bit flip) | `STRUCTURAL_FAIL_SYNC_LOST` | `PCM_DECODE_ERROR` | `N/A` | `INELIGIBLE` | **ADMISSION_REJECT** | **PRESERVE** |
| `SCEN-07` | **Bitstream Corruption** | Invalid MPEG layer / sample rate / channel mode index | `STRUCTURAL_FAIL_NON_AUDIO` | `PCM_DECODE_ERROR` | `N/A` | `INELIGIBLE` | **ADMISSION_REJECT** | **PRESERVE** |
| `SCEN-08` | **Decoder Edge Cases** | Decoder agreement on clean decode (SoundFile == FFmpeg) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **PRESERVE** |
| `SCEN-09` | **Decoder Edge Cases** | Decoder disagreement on padding/delay (SoundFile != FFmpeg) | `STRUCTURAL_PASS` | `PCM_DECODE_INCONCLUSIVE` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **PRESERVE** |
| `SCEN-10` | **Decoder Edge Cases** | Decoded PCM all-zeros (silent audio) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **FLAG_SILENT_AUDIO** | **PRESERVE** |
| `SCEN-11` | **Archive Interruption** | Stream read timeout during tar member extraction | `N/A` | `N/A` | `N/A` | `ORIGIN_UNVERIFIED` | **RETRY_REQUIRED** | **PRESERVE_PARTIAL_LOG_INTERRUPTED** |
| `SCEN-12` | **Archive Interruption** | Worker process SIGKILL during PCM decode | `N/A` | `N/A` | `N/A` | `ORIGIN_UNVERIFIED` | **RETRY_REQUIRED** | **RETAIN_STAGING_PART_RECORD_CRASH** |
| `SCEN-13` | **Archive Interruption** | Worker process SIGKILL during MoveFileExW promotion | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **CRASH_RECONCILIATION** | **RECONCILE_ON_RESTART** |
| `SCEN-14` | **Filesystem / OS** | Destination file already exists with identical SHA-256 | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **IDEMPOTENT_PASS** | **PRESERVE_EXISTING_LOG_IDEMPOTENT** |
| `SCEN-15` | **Filesystem / OS** | Destination file already exists with conflicting SHA-256 | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **QUARANTINE_COLLISION** | **DIVERT_TO_COLLISION_QUARANTINE** |
| `SCEN-16` | **Filesystem / OS** | Disk space exhausted during staging write (ENOSPC) | `N/A` | `N/A` | `N/A` | `ORIGIN_UNVERIFIED` | **ABORT_PIPELINE** | **LOG_ENOSPC_PRESERVE_STATE** |
| `SCEN-17` | **WAL Crash Recovery** | Torn line at EOF of wal_journal.jsonl due to crash | `N/A` | `N/A` | `N/A` | `ORIGIN_UNVERIFIED` | **JOURNAL_RECOVERY** | **DISCARD_TORN_LINE_REPLAY_VALID** |
| `SCEN-18` | **WAL Crash Recovery** | Process crash between atomic promotion and CSV ledger append | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **IDEMPOTENT_RECOVERY** | **COMPLETE_PENDING_LEDGER_WRITE** |
| `SCEN-19` | **Concurrency** | Concurrent worker destination collision on identical recording ID | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **IDEMPOTENT_PASS** | **SERIALIZE_VIA_LOCK_AND_IDEMPOTENT_PASS** |
| `SCEN-20` | **Filesystem Durability** | Filesystem metadata flush failure (os.fsync error after destination link created) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **DURABILITY_UNCERTAIN** | **PRESERVE_BOTH_STAGING_AND_DEST_RECONCILE_ON_RESTART** |
| `SCEN-21` | **Metadata / Header** | ID3v2 extended headers and footers present | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **PARSE_EXTENDED_HEADER_ISOLATE_AUDIO** |
| `SCEN-22` | **Metadata / Header** | Recognized trailing container tags (ID3v1 128B or APEv2 footer) | `STRUCTURAL_PASS` | `PCM_DECODE_CLEAN` | `METADATA_ABSENT` | `ORIGIN_UNVERIFIED` | **ADMISSION_HOLD** | **ISOLATE_TRAILING_TAG_VERIFY_FRAMES** |
| `SCEN-23` | **Archive Security** | TAR symlink, hardlink, or special-file archive member | `STRUCTURAL_FAIL_NON_AUDIO` | `N/A` | `N/A` | `INELIGIBLE` | **ADMISSION_REJECT** | **REJECT_SPECIAL_MEMBER_LOG_SECURITY** |

---

## Section 7: Operational & Resource Impact Assessment

### Authoritative Byte Inventory

| Evidence Population | Verified Files | Authoritative Exact Bytes | MiB ($1024^2$) | MB ($10^6$) | Ledger Agreement |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Accepted Audio (`cohort3_audio`)** | 18,845 | **704,970,734 B** | 672.31 MiB | 704.97 MB | [`stage6m_cohort3_clip_sha256_ledger.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv) (**100.0% Match**) |
| **Quarantine Audio (`cohort3_rejected_quarantine`)** | 130 | **4,780,224 B** | 4.56 MiB | 4.78 MB | [`stage6m_cohort3_quarantine_ledger.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_quarantine_ledger.csv) (**100.0% Match**) |
| **Total Evidence Base** | **18,975** | **709,750,958 B** | **676.87 MiB** | **709.75 MB** | **All 18,975 file digests verified against frozen ledgers** |

### System Resource Feasibility

| Operational Dimension | Current Production Validator | Proposed Remediated Pipeline | Delta / Net Impact | Feasibility Status |
| :--- | :--- | :--- | :--- | :---: |
| **Memory Consumption** | ~45 MB estimated (bounded chunked reading: 4,096 frames/chunk) | ~48 MB estimated (bounded chunks + 64 KB bitstream buffer) | +3 MB (+6.7% estimated) — entirely negligible. | **PASS (Estimated)** |
| **CPU Overhead / File** | ~5.7 ms / file estimated (sf.info + sf.SoundFile read) | ~6.5 ms / file estimated (ID3 parse + physical frame step + sf.SoundFile read) | +0.8 ms / file (+14.0% estimated) — corresponds to ~154 files/sec single-threaded capacity. | **PASS (Estimated)** |
| **Extraction Throughput** | ~175 files / second estimated (16 worker threads, I/O bound) | ~165 files / second estimated (16 worker threads, amortized pipeline) | Minimal impact (-5.7% estimated); overall cohort materialization completes in ~115 seconds. | **PASS (Estimated)** |
| **Total Disk Storage** | 704.97 MB (accepted files only; failed files unlinked) | 709.75 MB (704.97 MB accepted + 4.78 MB quarantined + ~0.2 MB staging buffer) | +4.78 MB (+0.68%) — minimal storage cost to preserve 100% of acquired physical evidence. | **PASS (Measured)** |
| **Audit Ledger Size** | ~8.3 MB (valid clips only) | Audit ledger CSV with 18,975 records occupies ~8.3 MB; hash digests verifiable in < 50 ms. | Identical footprint | **PASS (Measured)** |
| **Crash Recovery** | Dirty destination files | By writing exclusively to .staging/{rec_id}_{attempt_id}.part and using a journaled state machine with atomic no-clobber moves, aborted runs leave zero corrupted files in production directories. Resuming is 100% idempotent. | 100% Idempotent | **PASS (Design)** |

### Test Evidence Qualification

- **Milestone Regression Evidence:** The 55/55 passing tests confirm zero regression in existing milestone artifacts and ledgers.
- **Proposed Architecture Status:** The 23 adversarial scenarios represent a proposed test matrix for future validation. They do NOT constitute proof that the proposed staging, atomic promotion, crash recovery, and ledger reconciliation pipeline has passed those tests, because that pipeline is currently in proposal status and has not yet been implemented.

---

## Section 8: Protected State & Invariant Verification

- Production Validator Code: `scripts/materialize_stage6m_cohort3_audio.py` (**UNTOUCHED**).
- Production Threshold Constant: `MAX_MP3_PADDING_FRAMES = 1152` (**UNTOUCHED** at line 394).
- Production Unlink Behavior: `dest_file.unlink(missing_ok=True)` intact at line 1049 (**UNTOUCHED**).
- Accepted Audio Count: Exactly 18,845 recordings in `cohort3_audio` (**UNTOUCHED**).
- Quarantined Audio Count: Exactly 130 recordings in `cohort3_rejected_quarantine` (**UNTOUCHED**).
- Provisional Manifest Digest: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` (**UNLOCKED**, **UNTOUCHED**).
- Acquisition Ledger SHA-256 (LF): `63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5` (**UNTOUCHED**).
- Quarantine Ledger SHA-256 (LF): `98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8` (**UNTOUCHED**).
- Confirmatory Cohort Promotion: **ZERO files promoted**; **ZERO speakers substituted**.
- GPU CTTA Adaptation & Confirmatory Inference: **BLOCKED / FROZEN**.

---

## Section 9: Next Steps & Milestone Roadmap

1. **Task 7.7.3E Review & Decision:** Project Lead reviews this reconciled remediation proposal and consistency audit, formally selecting among Policy 1, Policy 2A, and Policy 2B.
2. **Incomplete Evaluation Speaker Strategy:** If Policy 2B is selected, formalize whether to apply Option A (complete clusters only) or Option B (unequal cluster weighting) and commission a power re-evaluation.
3. **Task 7.7.4 Authorization (Conditional):** If Policy 2A or 2B is authorized, develop the implementation specification for non-destructive staging.
4. **Task 7.7.5 Implementation & Validation Suite:** Implement the non-destructive staging pipeline and execute the 23 adversarial test scenarios.
5. **Task 7.7.6 Cohort Manifest Locking:** Compute final cryptographic manifest digest and transition status to `LOCKED`.
6. **Stage 6M Confirmatory Inference:** Proceed to GPU-accelerated inference across all 5 strata.
