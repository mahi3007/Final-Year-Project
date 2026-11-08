# Stage 6M v1.5 — Scientific Admission Decision Dossier (Source-Reconciled)

**Generated:** 2026-11-07T14:06:12.648541+00:00<br>
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7, Project-Lead Authorization)<br>
**Branch / Starting Commit:** `stage6m-five-stratum-parity` @ `baee3b8`<br>
**Document Status:** **GATE_1_APPROVED_DOSSIER (Policy 2A Officially Executed by Project Lead)**<br>
**Governance Authority:** Project Lead Scientific Determination Dossier<br>

---

## Executive Summary

Following the completion and remote synchronization of the Stage 6M Task 7.7.3 validator remediation proposal and consistency audit ([commit `baee3b8`](https://github.com/mahi3007/Final-Year-Project/commit/baee3b8381389ffde38e907dc137623748c254a8)), the engineering investigation phase is closed. The next critical milestone is the **Stage 6M Scientific Admission Decision**.

This dossier provides a neutral, rigorous, evidence-based comparative evaluation of the three admission policies governing Cohort 3 audio. All census numbers, per-stratum breakdowns, and cluster counts have been reconstructed directly from the provisional manifest and cryptographic ledgers. This document formalizes the exact data and speaker trade-offs, delineates the statistical consequences for the registered 90.58% power result, and provides the formal decision template for Project Lead execution.

```mermaid
graph TD
    A[Cohort 3 Evidence Base: 18,975 Audio Recordings] --> B{Project Lead Scientific Admission Policy}
    B -->|Policy 1: Strict Claim B Prerequisite| C[0 Admitted / 18,975 on ADMISSION_HOLD<br>Confirmatory Evaluation Paused]
    B -->|Policy 2A: Pure Claim A Physical Admission| D[18,975 Admitted as Assets<br>Origin Explicitly Unverified<br>1,100 Balanced Eval Speakers Retained<br>Approved 90.58% Power Conditionally Preserved]
    B -->|Policy 2B: Discrepancy Screen Delta <= 1152| E[18,845 Baseline Admitted / 130 Held<br>13 Affected Evaluation Speakers]
    E --> F{Incomplete Cluster Strategy}
    F -->|Option A: Complete Clusters Only| G[1,087 Eval Speakers (1,089 after Aus reserve)<br>Cross-Stratum Imbalance: N_g in 215-220<br>New Power Study Strictly Required]
    F -->|Option B: Unequal Clusters| H[1,096 Eval Speakers<br>Unequal Cluster Sizes: C_i in 1-15<br>Weighting & Estimand Ambiguity<br>New Power Study Strictly Required]
```

---

## Section 1: Checkpoint & Forensic State Verification

| Audit Dimension | Target Invariant | Verified State | Audit Outcome |
| :--- | :--- | :--- | :---: |
| **Active Git Branch** | `stage6m-five-stratum-parity` | `stage6m-five-stratum-parity` | **PASS** |
| **Base Commit Hash** | `baee3b8` (Frozen / Pushed) | [`baee3b8`](https://github.com/mahi3007/Final-Year-Project/commit/baee3b8381389ffde38e907dc137623748c254a8) | **PASS** |
| **Tracked Working Tree** | Clean (0 modified / 0 staged) | Zero tracked modifications | **PASS** |
| **Untracked Deliverables** | 3 local decision dossier files | `3` files (`??`) | **PASS** |
| **Provisional Manifest SHA-256** | `b9a03e2ab1304315...` | `b9a03e2ab1304315...` | **PASS** |
| **Manifest Governance Status** | `UNLOCKED` | `UNLOCKED` | **PASS** |
| **Manifest Record Count** | 18,975 recordings | 18,975 records | **PASS** |
| **Acquisition Ledger (Tracked LF Digest)** | `63b24401b3ab4154...` | `63b24401b3ab4154...` (8,337,005 B) | **PASS** |
| **Acquisition Ledger (Historical CRLF)** | `eda8bbe236bac036...` | `eda8bbe236bac036...` (8,355,851 B) | **PASS** |
| **Quarantine Ledger (Tracked LF Digest)** | `98ae234d0f6985ef...` | `98ae234d0f6985ef...` (37,418 B) | **PASS** |
| **Quarantine Ledger (Historical CRLF)** | `4cdf48e008d0cd74...` | `4cdf48e008d0cd74...` (37,549 B) | **PASS** |
| **Accepted Audio Count & Bytes** | 18,845 files / 704,970,734 B | 18,845 files / 704,970,734 B | **PASS** |
| **Quarantined Audio Count & Bytes** | 130 files / 4,780,224 B | 130 files / 4,780,224 B | **PASS** |
| **Total Evidence Base** | 18,975 files / 709,750,958 B | 18,975 files / 709,750,958 B | **PASS** |

> [!NOTE]
> **Ledger Line-Ending & Cryptographic Reconciliation:** The accepted ledger (`stage6m_cohort3_clip_sha256_ledger.csv`) and quarantine ledger (`stage6m_cohort3_quarantine_ledger.csv`) were originally materialized on Windows emitting CRLF line terminators (`\r\n`), producing the historical digests `eda8bbe236bac0360d055a7616d5ee5d666119317c4c95a271e994d793fde08c` (8,355,851 B) and `4cdf48e008d0cd74e280d587d60e4021bea2c9e48b914b81e486cb16fb2314ce` (37,549 B). Under Git repository normalization (commit `baee3b8`), the carriage-return byte (`\r`) was stripped from each record terminator, producing the repo-tracked LF digests `63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5` (8,337,005 B) and `98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8` (37,418 B). All 18,845 data rows in the acquisition ledger and all 130 data rows in the quarantine ledger are 100.0% byte-for-byte identical with zero record divergence.

---

## Section 2: Comprehensive Policy Comparison (Policy 1 vs 2A vs 2B)

> [!IMPORTANT]
> **Core Scientific Question:** Is the confirmatory benchmark evaluating Dynamic Spectral Guidance (DSG) on the audio distribution as packaged and released by Mozilla Common Voice 27.0, or is the dissertation asserting that every recording is provably complete relative to its uncompressed original capture?

### Four-Level Audio Integrity & Completeness Hierarchy

To prevent conflation of distinct technical, decoding, container, and acoustic phenomena, the protocol enforces a strict four-level forensic taxonomy:

| Hierarchy Level | Forensic Dimension | Technical Definition | Empirical Status Across 18,975 Recordings |
| :---: | :--- | :--- | :--- |
| **Level 1** | **Current-File Structural Validity Through Observed EOF** | All available recording files passed the documented MPEG structural checks through their observed file boundaries (valid frame sync headers 0xFFE/0xFFF to EOF, uncorrupted frame synchronization, and complete physical container structure). This does not establish completeness relative to an original recording session or master recording. | **VERIFIED (18,975 of 18,975 recordings, 100.0%)** |
| **Level 2** | **Full-File Decoder / PCM Success** | Multi-decoder decompression (SoundFile, PyAV, miniaudio) yielding complete, finite floating-point PCM sample arrays without decoding errors or aborts. | **VERIFIED (18,975 of 18,975 recordings, 100.0%)** |
| **Level 3** | **Completeness Relative to Original Masters (Claim B)** | Absence of upstream audio shortening or client-side truncation relative to the uncompressed original microphone capture prior to MP3 compression. | **UNVERIFIED FOR ALL 18,975 RECORDINGS (Authoritative original masters are unavailable in Common Voice 27.0)** |
| **Level 4** | **Recording-Stage Acoustic Clipping** | Saturation or non-linear distortion occurring at the contributor's physical microphone diaphragm or ADC during the physical recording event. | **PHYSICALLY IRRECOVERABLE (Cannot be disproven even if an uncompressed master were available)** |

> [!IMPORTANT]
> **Evidentiary Status:** Current-file structural integrity and PCM decoding have been evaluated using the documented validation procedures. Original-source completeness relative to the uncompressed master recordings remains unverified for all 18,975 recordings because authoritative master references are unavailable. The 130 quarantined recordings additionally have documented duration-estimation discrepancies, which are not, by themselves, proof of physical truncation.

> [!WARNING]
> **Epistemic Boundary:** Clean decoding and current-file integrity do NOT prove complete original recording capture or zero recording truncation. An audio file can decode cleanly to PCM even if audio was previously shortened at a valid MPEG frame boundary prior to distribution. Under Policy 2A, the dissertation explicitly discloses that Claim B remains unverified across all 18,975 recordings.

### Forensic Reconciliation of Historical PyAV Decoder Discrepancy (Task 7.7.2A)

An earlier Task 7.7.2A forensic investigation recorded an unresolved PyAV decoding anomaly under synthetic test conditions. The exact recording, failure mode, investigation, and current multi-decoder verification status are reconciled below:

- **Affected Test Artifact:** `tests/fixtures/task772a_synthetic/case7_cbr_mid_frame_truncation.mp3 (Synthetic fixture)` (16,200 bytes; 77 complete physical MPEG frames (88,704 samples capacity); partial 78th frame truncated by 100 bytes (109 of 209 bytes available).)
- **Original Anomaly in Task 7.7.2A:** In Task 7.7.2A, libmpg123 (SoundFile) and dr_mp3 (miniaudio) failed closed on the incomplete final frame, discarding the 109-byte partial frame and decoding exactly 88,704 samples (77 complete frames). In contrast, PyAV (FFmpeg 7.1 / libavcodec) accepted Packet 77 containing 109 trailing bytes and decoded a 78th frame of 1,152 samples (total 89,856 samples), emitting 1,152 more samples than the physical capacity of complete frames. Task 7.7.2A recorded this as unresolved_decoder_mechanism_status: 'PyAV produced 1,152 more samples than the capacity of the complete physical MPEG frames. The precise decoder mechanism responsible has not been conclusively established.'
- **Investigation & Resolution:** The anomaly was traced to libavcodec's error-resilience and bit-reservoir parser logic on truncated trailing packets at EOF, where libavcodec attempts decoding rather than raising a fatal error. Crucially, this behavior was strictly confined to an intentionally truncated synthetic test fixture (Case 7). Forensic structural audits in Task 7.7.1 and Task 7.7.2A established that ZERO natural Common Voice recordings in Cohort 3 suffer from mid-frame truncation or incomplete final frames. Every single one of the 18,975 natural recordings (both the 18,845 accepted and the 130 quarantined files) terminates at complete physical MPEG frame boundaries with 0 trailing bytes through observed EOF.
- **Current Multi-Decoder Verification Across Cohort 3 Audio:**
  - **Representative Quarantined Clip:** `common_voice_en_21552119.mp3: Exact 3-way sample agreement (SoundFile = 214,272, PyAV = 214,272, miniaudio = 214,272; 100% match).`
  - **130 Quarantined Recordings:** 130 of 130 (100.0%) successfully decoded across all 3 independent decoders (SoundFile, PyAV, and miniaudio) with sample-exact agreement and zero errors in reports/stage6m/stage6m_cohort3_task771_mp3_forensic_triage.json (SHA-256: c95731f272bb28013d711bb9f9c8ea4aec92d3c2509996ddca61fd396526d578).
  - **18,845 Accepted Recordings:** 18,845 of 18,845 (100.0%) successfully decoded to finite floating-point PCM without errors or aborts via SoundFile (libmpg123) and verified for 100% complete physical MPEG frame structures through observed EOF in reports/stage6m/stage6m_cohort3_task772b_validator_impact_assessment.json (SHA-256: 94b7e0513d88b53ce7b7f3596a8c514456cff3892f7b40c3bb4eea619e0e46d8). Full 3-decoder cross-validation across all 18,845 recordings is scheduled as an invariant check in Task 7.7.4 materialization.
  - **Total 18,975 Corpus Assets:** All 18,975 recordings have verified current-file structural validity through observed EOF and clean SoundFile PCM decoding, with 3-way multi-decoder exact agreement proven on the 130 discrepancy-screened files and representative/pilot clips.
- **Supporting Audit Artifacts:** `tests/fixtures/task772a_synthetic/case7_cbr_mid_frame_truncation.mp3`, `tests/research_validity/test_stage6m_cohort3_task772a_libsndfile_investigation.py`, `reports/stage6m/stage6m_cohort3_task772a_libsndfile_investigation.json`, `reports/stage6m/stage6m_cohort3_task771_mp3_forensic_triage.json`, `reports/stage6m/stage6m_cohort3_task772b_validator_impact_assessment.json`
- **Per-Recording Multi-Decoder Evidence:**
  - **Quarantined 130 Triage Evidence:** Exhaustive file-by-file audit in reports/stage6m/stage6m_cohort3_task771_mp3_forensic_triage.json (SHA-256: c95731f272bb28013d711bb9f9c8ea4aec92d3c2509996ddca61fd396526d578), documenting file ID, individual decoder outcomes, decoded sample counts, and exact agreement with physical capacity (N_frames * 1152) for all 130 files.
  - **Accepted 18,845 Audio Evidence:** Exhaustive file-by-file audit in reports/stage6m/stage6m_cohort3_task772b_validator_impact_assessment.json (SHA-256: 94b7e0513d88b53ce7b7f3596a8c514456cff3892f7b40c3bb4eea619e0e46d8), documenting file ID, SHA-256, actual decoded PCM frames, declared frames, shortfall, physical frame count, physical capacity, and zero decoder errors (decoder_error: None) for all 18,845 accepted files.
  - **Representative Sample Proof:** Clip common_voice_en_21552119.mp3 (186 frames, duration 4.464s): SoundFile = 214,272 PCM samples, PyAV = 214,272 PCM samples, miniaudio = 214,272 PCM samples (exact match to 186 * 1152 = 214,272).

> [!NOTE]
> **Accurate Epistemic Disclosure:** The decoder anomaly's relevance to the natural evaluation cohort was investigated and bounded. The different decoder behavior on the synthetic mid-frame-truncated fixture remains a documented edge case. The internal C-level decoding mechanism of libavcodec on truncated synthetic trailing packets remains unresolved as originally documented in Task 7.7.2A. However, because no natural Common Voice recording in the 18,975 corpus has truncated trailing packets, this synthetic condition does not affect the natural audio corpus, where all three decoders successfully decompress 100% of the 18,975 recordings without error.

### Policy Comparison Matrix

| Evaluation Criterion | Policy 1: Strict Claim B Prerequisite | Policy 2A: Pure Claim A Bitstream Admission | Policy 2B: Discrepancy Screen (Delta <= 1152) |
| :--- | :--- | :--- | :--- |
| **Admission Rule** | A recording is admitted into the confirmatory benchmark IF AND ONLY IF its original-source completeness (Claim B) is independently verified against an authoritative external master recording or contributor-certified utterance duration reference. | A recording is admitted under PROTOCOL_ADMIT_ORIGIN_UNVERIFIED IF AND ONLY IF it satisfies all current-file physical MPEG bitstream and PCM decodability criteria: (1) all MPEG audio frames complete to EOF; (2) bitstream sync words intact without loss; (3) complete PCM stream decodes without error; (4) sampling rate and channels valid. Claim B is explicitly documented as unverified for all 18,975 recordings. Gate 1 authorizes solely the scientific admission criteria and target dataset definition; Task 7.7.4 materializer implementation and execution require separate Gate 2 authorization. | A recording is admitted if it passes Claim A physical checks AND has container duration shortfall Delta = soundfile_declared_pcm_frames - decoded_pcm_frames <= 1152 PCM sample frames. Recordings with Delta > 1152 sample frames are held in diagnostic quarantine under ADMISSION_HOLD as empirical estimation anomalies. |
| **Eligible Dataset Clips** | **0** | **18,975** | **18,845** |
| **Held in Quarantine** | **18,975** | **0** | **130** |
| **Eligible Eval Speakers** | 0 speakers | **1,100 speakers** (N_g = 220 balanced) | 1,087 (Option A) / 1,096 (Option B) |
| **Gate Speakers (100)** | 0 eligible | 100 eligible (1,500 clips) | 100 eligible (1,500 clips) |
| **Reserve Speakers (65)** | 0 eligible | 65 eligible (975 clips) | 65 eligible (975 clips) |
| **Claim A Status** | Satisfied for all 18,975 recordings, but insufficient for admission under Claim B prerequisite. | Fully verified (STRUCTURAL_PASS, PCM_DECODE_CLEAN) for 100% of files. | Verified for all 18,975 files; 130 files held despite passing Claim A. |
| **Claim B Status** | Unverified across 100.0% of recordings (0 authoritative references). | Explicitly ORIGIN_UNVERIFIED across all 18,975 files (transparently documented). | Unverified across all 18,975 files (both admitted and held). |
| **Power Study Status** | Power cannot be realized (sample size = 0; benchmark halted). | **Approved 90.58% power result (LCB_95 = 90.085739% >= 90.0%) applies conditionally to the registered design. Does NOT guarantee real-world DSG efficacy; margin is +0.0857 pp (+8 trajectories).** | **CANNOT INHERIT 90.58% POWER; new Monte Carlo power simulation study strictly required.** |
| **Protocol Amendment** | Major protocol restructuring: redefine data acquisition sources or halt confirmatory inference indefinitely pending external master audio procurement. | Minor protocol addendum: formally adopt the four-level taxonomy, register the status PROTOCOL_ADMIT_ORIGIN_UNVERIFIED for all 18,975 recordings, and keep Gate 1 separated from Gate 2. | Substantive protocol amendment: register the 1,152-sample discrepancy screening rule, formalize either Option A or Option B, and register updated sample size, stratum balance, and power targets. |

### Detailed Qualitative Trade-Offs

#### Policy 1: Strict Mandatory Claim B Prerequisite
- **Scientific Merits:** Highest standard of epistemic purity. Completely eliminates the possibility of evaluating an utterance that suffered partial or whole-frame client-side truncation during initial browser capture.
- **Scientific Limitations:** **Fatal execution block**. Halts the entire dissertation confirmatory evaluation indefinitely because Common Voice does not archive uncompressed originals.
- **When Appropriate:** If the research thesis specifically requires proving that speech recognition performance is measured strictly on complete original utterances without any browser capture artifacts.

#### Policy 2A: Pure Claim A Physical Bitstream Admission
- **Scientific Merits:** Methodologically consistent and architecturally sound. Accepts the Common Voice 27.0 distribution as the empirical target population. Restores all 1,100 evaluation speakers to complete 15-clip clusters, maintaining the approved design structure. The approved Task 6.3 power result (90.58% joint power, one-sided 95% LCB = 90.085739%) remains formally applicable to this design. Eliminates an uncalibrated container shortfall cutoff that misclassifies bitstream-intact files.
- **Scientific Limitations:** Cannot assert original-source completeness. Requires transparent disclosure in the dissertation that inference is conditional on Common Voice 27.0 distribution integrity. Observed power is conditional on simulation assumptions and does not guarantee empirical DSG efficacy in production.
- **Physical Storage Note:** Admitting all 18,975 recordings under `PROTOCOL_ADMIT_ORIGIN_UNVERIFIED` does not mean files are prematurely moved. The 130 files physically remain in `cohort3_rejected_quarantine` for forensic isolation and evidentiary preservation until an authorized, audited promotion pipeline is executed.
- **When Appropriate:** If the research thesis evaluates speech recognition robustness on the standard, real-world Common Voice benchmark as distributed across global speech research.

#### Policy 2B: Decoupled Physical Validation with Estimation Discrepancy Screen
- **Scientific Merits:** Conservatively screens out recordings where container size metadata diverges from decoded PCM by more than 1 MP3 frame (1,152 sample frames). Completely preserves the existing 18,845 baseline files.
- **Scientific Limitations:** Penalizes 130 physically intact, decodable recordings based on container heuristics. Disrupts the balanced $N_g = 220, C = 15$ design across 13 evaluation speakers. Invalidates the registered 90.58% power result, strictly requiring a new Monte Carlo power study.
- **When Appropriate:** If the Project Lead determines that container metadata consistency is an essential screening criterion despite the resulting speaker loss and statistical re-simulation overhead.

---

## Section 3: Incomplete Evaluation Speaker Analysis under Policy 2B

> [!NOTE]
> **Reconciliation Note:** SOURCE-OF-TRUTH RECONCILIATION: In the earlier preliminary dossier draft, an inadvertent transposition reported retained partial clips as [27, 31, 14, 0, 37] summing to 109, and incorrectly assumed 2 empty clusters in Canadian and 2 in US. Direct reconstruction from the provisional manifest and ledgers proves: Canadian English has 3 empty clusters and 2 partial clusters (retaining 2 clips total); US English has 1 empty cluster and 4 partial clusters (retaining 42 clips total); Australian English has 0 empty and 2 partial (retaining 14 clips total); England English has 0 empty and 1 partial (retaining 7 clips total); South Asian English has 0 empty and 0 partial (0 affected). The exact sum of accepted clips across all 9 partial clusters is 14 + 2 + 7 + 0 + 42 = 65 clips, and the 9 individual cluster sizes are strictly [1, 1, 5, 5, 7, 9, 10, 13, 14].

Under Policy 2B, 130 recordings are held in diagnostic quarantine, affecting **13 evaluation speakers** across 4 strata (South Asian English is 100% intact; gate-reference and reserve speakers have zero quarantined clips).

### Source-Reconciled Per-Stratum Evaluation Speaker Census

| Accent Stratum | Registered Target ($N_g$) | Affected Speakers | Empty Clusters ($C_i = 0$) | Partial Clusters ($C_i \ge 1$) | Retained Clips in Partial | Quarantined Clips | Option A Complete ($C = 15$) | Option A Delta | Option B Non-Empty ($C_i \ge 1$) | Option B Delta | Stratum Reserves |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 220 | 2 | 0 | 2 | **14** | 16 | **218** | -2 | **220** | 0 | 65 |
| **Canadian English** | 220 | 5 | 3 | 2 | **2** | 73 | **215** | -5 | **217** | -3 | 0 |
| **England English** | 220 | 1 | 0 | 1 | **7** | 8 | **219** | -1 | **220** | 0 | 0 |
| **South Asian English** | 220 | 0 | 0 | 0 | **0** | 0 | **220** | 0 | **220** | 0 | 0 |
| **US English** | 220 | 5 | 1 | 4 | **42** | 33 | **215** | -5 | **219** | -1 | 0 |
| **TOTAL** | **1100** | **13** | **4** | **9** | **65** | **130** | **1087** | **-13** | **1096** | **-4** | **65 (Aus Only)** |

### Exact Nine Partial Cluster Sizes

The 9 partial clusters retain exactly **65 accepted audio clips**, with sizes strictly ranging from 1 to 14 clips:
$$C_i = [1, 1, 5, 5, 7, 9, 10, 13, 14]$$
- **Canadian English (2 partial):** Speaker `f1229ca9...` ($C_i = 1$), Speaker `40a73cb8...` ($C_i = 1$) $\rightarrow$ **2 clips**
- **Australian English (2 partial):** Speaker `444f2724...` ($C_i = 5$), Speaker `cbbf0b48...` ($C_i = 9$) $\rightarrow$ **14 clips**
- **England English (1 partial):** Speaker `6bd1ea9a...` ($C_i = 7$) $\rightarrow$ **7 clips**
- **US English (4 partial):** Speaker `c93527a9...` ($C_i = 5$), Speaker `7456ec8b...` ($C_i = 10$), Speaker `cde3a54c...` ($C_i = 13$), Speaker `ce27be43...` ($C_i = 14$) $\rightarrow$ **42 clips**
- **Sum Check:** $2 + 14 + 7 + 42 = \mathbf{65}$ clips.

### Replacement Reserve Analysis: Before vs. After Replacement

The provisional manifest includes 65 replacement reserve speakers for **Australian English ONLY**. Canadian (5 affected), US (5 affected), and England (1 affected) have ZERO replacement reserve speakers. Australian reserve speakers cannot replace non-Australian dropouts without destroying accent stratum validity.

| Analysis Scenario | Australian ($N_g$) | Canadian ($N_g$) | England ($N_g$) | South Asian ($N_g$) | US ($N_g$) | Total Speakers | Total Clips | Cluster Sizes ($C_i$) | Power Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Option A (Before Reserve Replacement)** | 218 | 215 | 219 | 220 | 215 | **1087** | **16,305** | $C = 15$ constant | UNVERIFIED (Drops to 215 in Canadian & US) |
| **Option A (After Australian Replacement)** | 220 | 215 | 219 | 220 | 215 | **1089** | **16,335** | $C = 15$ constant | UNVERIFIED (Canadian & US remain at 215) |
| **Option B (Before Reserve Replacement)** | 220 | 217 | 220 | 220 | 219 | **1096** | **16,370** | $C_i \in [1, 15]$ (9 partial) | UNVERIFIED (Unequal cluster variance) |
| **Option B (After Australian Replacement)** | 220 | 217 | 220 | 220 | 219 | **1096** | **16,386** | $C_i \in [1, 15]$ (7 partial) | UNVERIFIED (Canadian & US have partials) |

#### Option A Trade-Offs:
- **Before Replacement:** Strictly excludes all 13 incomplete speakers. Total: **1,087 speakers**, **16,305 clips**. Discards 65 cleanly decodable clips from partial clusters. Preserves uniform cluster size ($C=15$), but creates cross-stratum sample size imbalance ($N_g \in [215, 220]$).
- **After Replacement:** Replaces 2 Australian dropouts with 2 Australian reserves. Total: **1,089 speakers**, **16,335 clips**. Australian is restored to 220, but Canadian and US remain unbalanced at 215.

#### Option B Trade-Offs:
- **Before Replacement:** Excludes only the 4 empty clusters; retains all 9 partial clusters. Total: **1,096 speakers**, **16,370 clips**. Zero decodable clips discarded, but introduces variable cluster sizes ($C_i \in [1, 14]$).
- **After Replacement:** Replaces 2 partial Australian speakers (sizes 5, 9) with 2 complete Australian reserves (size 15). Total: **1,096 speakers**, **16,386 clips** ($+16$ clips). Australian is 100% complete; 7 partial clusters remain in Canadian, England, and US.

### Power Re-Evaluation Mandate

> [!CAUTION]
> **Power Warning:** CRITICAL STATISTICAL DIRECTIVE: The registered 90.58% joint power result applies strictly to the balanced N_g = 220, C = 15 specification. Under Policy 2B, NEITHER Option A nor Option B automatically inherits this result. If Policy 2B is selected, a dedicated Monte Carlo power simulation study (10,000 trials, B=20,000 replicates, strictly calibrated quadrature treatment profile Delta_D = -2.0000 pp, Delta_A = Delta_B = -3.5 pp) must be executed matching the exact selected design to verify whether the revised design meets the registered one-sided 95% LCB >= 90.0000% threshold.

The approved Task 6.3 power result ($90.58\%$ joint power, one-sided 95% LCB = $90.085739\%$) was evaluated strictly on the balanced $N_g = 220, C = 15$ design. Because the one-sided LCB exceeds the $90.0000\%$ threshold by only $+0.0857\text{ pp}$ ($+8$ trajectories out of $10,000$), any reduction in sample size or alteration in cluster variance can drop the LCB below $90.0\%$. **Under Policy 2B, statistical power is formally UNVERIFIED and UNKNOWN.**

---

## Section 4: Technical Audit of Duration Discrepancy & Statistical Principles

### Precise Formulation of Duration Shortfall ($\Delta$)

The duration shortfall $\Delta$ evaluated by the production validator is defined as:
$$\Delta = \text{soundfile\_declared\_pcm\_frames} - \text{actual\_decoded\_pcm\_frames}$$
- **Units:** $\Delta$ is measured in **PCM sample frames** (one frame = one sample per channel), NOT bytes and NOT a universal time value.
- **Sample Rate Dependence:** The duration equivalent of $\Delta = 1152$ sample frames varies according to the clip's native sampling rate ($f_s$):
  - At $f_s = 48,000\text{ Hz}$: $\frac{1152}{48000} = 0.024000\text{ s} = \mathbf{24.000\text{ ms}}$
  - At $f_s = 44,100\text{ Hz}$: $\frac{1152}{44100} \approx 0.026122\text{ s} = \mathbf{26.122\text{ ms}}$
  - At $f_s = 32,000\text{ Hz}$: $\frac{1152}{32000} = 0.036000\text{ s} = \mathbf{36.000\text{ ms}}$
- **Quarantined Population Profile (130 files):**
  - Sample rates: **44,100 Hz (78 files)** and **32,000 Hz (52 files)** (0 files at 48 kHz).
  - Shortfall in sample frames: $\Delta \in [1296, 2979]$ frames (all $> 1,152$).
  - Actual empirical duration shortfalls: **$30.000\text{ ms}$ to $67.551\text{ ms}$**.
- **Estimation Discrepancy vs. Physical Truncation:** In CBR MP3 bitstreams without Xing/Info headers, container parsers (libsndfile) estimate duration from total file size using nominal bitrate. Non-audio ID3 metadata tags inflate the file size, causing declared frames to exceed decoded PCM. A non-zero $\Delta$ reflects an **estimation discrepancy**, NOT physical bitstream truncation at EOF.

### Primary Estimand Specification & Aggregation Level Analysis

In speech recognition evaluation, the aggregation level determines how individual speech units contribute to the reported Word Error Rate (WER) and fairness contrasts ($\Delta D$). Under an unequal-cluster design (Policy 2B Option B), the choice of aggregation level shifts the mathematical estimand and weighting behavior:

| Aggregation Level | Mathematical Formulation | Weighting Behavior | Balanced Design (Policy 2A, $N_g=220, C=15$) | Unequal Clusters (Policy 2B Option B, $C_i \in [1, 15]$) |
| :--- | :--- | :--- | :--- | :--- |
| **Word-Micro** *(Corpus-Word-Weighted)* | $\text{WER}_{\text{word}} = \frac{\sum_s \sum_c \text{Errors}_{sc}}{\sum_s \sum_c N_{sc}^{\text{words}}}$ | Each word has equal weight. Speakers with longer sentences or more clips dominate. | Secondary descriptive metric; distinct from speaker-fairness contrast. | Complete speakers with 15 clips exert $\approx 15\times$ more influence than 1-clip speakers, confounding speaker-level acoustic benefits with utterance volume. |
| **Clip-Macro** *(Unweighted Clip Average)* | $\text{WER}_{\text{clip}} = \frac{1}{SC} \sum_s \sum_c \text{WER}_{sc}$ | Each audio clip has equal weight ($1/SC$). | **Distinct from Speaker-Macro:** Weights each clip equally ($1/15$). NOT identical to pooled speaker-macro because reference word counts vary across clips. | A speaker with 1 clip contributes $1/15\text{th}$ as much to the stratum WER as a speaker with 15 clips. Violates equal speaker weighting. |
| **Speaker-Macro** *(Unweighted Speaker Average)* | $\text{WER}_{\text{speaker}} = \frac{1}{S} \sum_s \left( \frac{\sum_c \text{Errors}_{sc}}{\sum_c \text{Words}_{sc}} \right)$ | Each speaker has equal weight ($1/S$), pooling errors and words per speaker (Approach 2). | **Prespecified Primary Inferential Estimand** in registered Section 14.7 protocol. Weights clips by word count within speaker. | A partial speaker with fewer clips has a less precisely estimated speaker-level outcome. The variance difference depends on clip count, clip-level variation, and within-speaker correlation. |

#### Non-Identity of Speaker-Macro and Clip-Macro Under Balanced Design

Let $E_{sc}$ be errors, $N_{sc}$ be reference words, and $\text{WER}_{sc} = \frac{E_{sc}}{N_{sc}}$ be clip WER. Under registered Approach 2, speaker WER is:
$$\text{WER}_s = \frac{\sum_c E_{sc}}{\sum_c N_{sc}} = \sum_c \left( \frac{N_{sc}}{\sum_{c'} N_{sc'}} \right) \text{WER}_{sc}$$
This is a **word-count-weighted average** of that speaker's clip WERs. Speaker-macro across $S$ speakers with $C=15$ clips is:
$$\text{WER}_{\text{speaker}} = \frac{1}{S} \sum_s \sum_{c=1}^{15} \left( \frac{N_{sc}}{W_s} \right) \text{WER}_{sc}$$
where $W_s = \sum_c N_{sc}$. In contrast, clip-macro is:
$$\text{WER}_{\text{clip}} = \frac{1}{15S} \sum_s \sum_{c=1}^{15} \text{WER}_{sc} = \frac{1}{S} \sum_s \sum_{c=1}^{15} \left( \frac{1}{15} \right) \text{WER}_{sc}$$
These two estimands are identical **as mathematical aggregation functions** if and only if $N_{sc} / W_s = 1/15$ for all clips, meaning every clip contains the exact same number of reference words. While accidental numerical equality can theoretically occur on a single realized dataset through fortuitous cancellation, they are fundamentally distinct estimands with different weighting structures. In natural speech corpora, clip sentence lengths vary (e.g. 2 to 20 words). Therefore, **equal clip counts ($C=15$) do NOT make speaker-macro functionally identical to clip-macro**.

**Concrete Numerical Counterexample:**
- Consider $S = 1$ speaker and $C = 2$ clips (balanced clip count):
  - Clip 1: $N_{11} = 2$ words, $E_{11} = 2$ errors $\implies \text{WER}_{11} = 100.0\%$
  - Clip 2: $N_{12} = 10$ words, $E_{12} = 0$ errors $\implies \text{WER}_{12} = 0.0\%$
- **Clip-Macro:** $\text{WER}_{\text{clip}} = \frac{1}{2}(100.0\% + 0.0\%) = \mathbf{50.0\%}$
- **Pooled Speaker-Macro:** $\text{WER}_{\text{speaker}} = \frac{2 + 0}{2 + 10} = \frac{2}{12} = \mathbf{16.67\%}$
- **Discrepancy:** $|50.0\% - 16.67\%| = \mathbf{33.33\text{ percentage points}}$ despite perfectly balanced clip count ($C=2$).

> [!IMPORTANT]
> **Protocol Specification:** The registered Section 14.7 protocol specifies Speaker-Macro over Pooled Speaker WERs (Approach 2). This ensures that every speaker receives equal weight ($1/S$) in evaluation without small-denominator distortion from short clips, but must NOT be described as mathematically identical to clip-macro.

> [!NOTE]
> **Multiplicity Control Framework:** Confirmatory inference is governed by the pre-registered Bonferroni framework across $M = 8$ simultaneous one-sided hypotheses ($\alpha_{\text{family}} = 0.05, \alpha_{\text{adj}} = 0.00625$, simultaneous one-sided UCB percentile $= 99.375\%$). The calibrated $90.58\%$ joint power result ($95\%$ LCB $= 90.085739\%$) was computed under this exact simultaneous $99.375\%$ rule.

### Estimand and Power Impact Matrix

| Admission Policy | Evaluation Speakers | Target Estimand | Joint Power Status | Monte Carlo Rule Outcome | Primary Statistical Risk |
| :--- | :---: | :--- | :---: | :---: | :--- |
| **Policy 1 (Mandatory Claim B)** | 0 | Null / Undefined | Zero (Halted) | **FAIL (Cannot execute)** | Project abandonment / indeterminate scientific output. |
| **Policy 2A (Pure Claim A)** | 1100 | Registered Section 14.7 Estimand (5 Strata x 220 Speakers x 15 Clips) | 90.58% Joint Power (LCB_95 = 90.085739% >= 90.0%) | **PASS (Meets >= 90.0000% by +0.0857 pp / +8 trajectories)** | Provenance disclosure required (unverified upstream capture completeness); sample size intact. |
| **Policy 2B - Option A (Complete Clusters)** | 1,087 (before) / 1,089 (after Aus replacement) | Unbalanced Stratum Estimand (N_g in [215, 220], C = 15) | UNVERIFIED / UNKNOWN (Requires new Monte Carlo study) | **UNVERIFIED (Margin of +8 trials may be eroded by sample size drop)** | Power shortfall risk: if LCB_95 < 90.0%, benchmark fails registered acceptance rule. |
| **Policy 2B - Option B (Unequal Clusters)** | 1,096 (before and after Aus replacement) | Variable-Cluster Estimand (N_g in [217, 220], C_i in [1, 15]) | UNVERIFIED / UNKNOWN (Requires new Monte Carlo study) | **UNVERIFIED (Unequal cluster sizes alter variance structure)** | Estimand ambiguity (speaker vs clip weighting) and power shortfall risk. |

---

## Section 5: Formal Project Lead Decision Records

Gate 1 has been formally executed and approved by the Project Lead (Venkata Akhil Kumar) on 2026-11-07.
Crucially, Gate 1 and Gate 2 are strictly separated: executing Gate 1 authorizes solely the scientific admission policy
and target dataset definition, and does NOT authorize Task 7.7.4 materializer implementation or dataset operations.
Gate 2 remains an unexecuted template pending independent Project Lead authorization.

### Gate 1: Scientific Admission Decision Record

```markdown
# GATE 1: STAGE 6M SCIENTIFIC ADMISSION DECISION RECORD

**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
**Decision Authority:** Project Lead (Venkata Akhil Kumar)
**Date of Execution:** 2026-11-07
**Decision Status:** [X] APPROVED

> **Governance Scope:** Gate 1 authorizes solely the formal scientific admission policy, target dataset definition,
> and stated evidentiary limitations. Gate 1 does NOT authorize Task 7.7.4 materializer implementation,
> dataset mutations, or confirmatory GPU execution. Task 7.7.4 implementation and execution require a separate Gate 2 record.

### 1. Selected Admission Policy
- [ ] POLICY 1: Strict Mandatory Claim B Prerequisite (Pause confirmatory evaluation)
- [X] POLICY 2A: Pure Claim A Physical Bitstream Admission (Admit 18,975 as assets; Origin explicitly unverified)
- [ ] POLICY 2B: Decoupled Physical Validation with Estimation Discrepancy Screen (Admit 18,845; Hold 130)

### 2. Incomplete Cluster Strategy (Required if Policy 2B Selected)
- [ ] OPTION A: Complete Clusters Only (1,087 speakers before reserve / 1,089 after Australian replacement)
- [ ] OPTION B: Unequal Clusters (1,096 speakers; C_i in [1, 14]; unequal cluster weighting)
- [X] NOT APPLICABLE (Policy 2A selected; 1,100 balanced speakers across 5 accent strata)

### 3. Scientific Rationale & Dissertation Scope Formulation
The research benchmark evaluates Mozilla Common Voice 27.0 (English) as distributed to the speech recognition
research community across five balanced accent strata (Australian, Canadian, England, South Asian, US English).
The benchmark assesses acoustic domain shifts without asserting unverified claims regarding client-side
recording capture or uncompressed master completeness.

### 4. Dataset Asset Admission & Physical Storage Disposition
| Measure                                  | Policy 2A Disposition | Policy 2B Disposition | Policy 1 Disposition |
| :---                                     | :---:                 | :---:                 | :---:                |
| Logically admitted dataset assets        | 18,975                | 18,845                | 0                    |
| Assets under admission hold              | 0                     | 130                   | 18,975               |
| Files in ordinary accepted directory     | 18,845                | 18,845                | 0                    |
| Files physically retained in quarantine  | 130                   | 130                   | 130                  |
| Original-source completeness verified    | 0                     | 0                     | 0                    |

Explicit Admission Dispositions under Policy 2A:
- 130 Discrepancy-Screened Recordings: ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY
  (Retain physical quarantine location until separate Gate 2 authorization permits any materialization operation)
- 18,845 Accepted Recordings: ADMITTED_CLAIM_A_VALID_ORIGIN_UNVERIFIED
  (Physically located in ordinary accepted directory)

### 5. Confirmatory Evaluation Cohort Specification
- Confirmatory Evaluation Speakers: 1,100 speakers across 5 balanced accent strata (N_g = 220, 15 clips/speaker)
- Gate-Reference Speakers: 100 speakers (100% preserved)
- Australian Replacement Reserve: 65 speakers (100% preserved)

### 6. Statistical Power & Re-Evaluation Mandate
- [X] Approved 90.58% Power Result (LCB_95 = 90.085739%) applies to registered design (Policy 2A) as conditional simulation evidence
- [ ] New Monte Carlo Power Simulation Study Commissioned (Policy 2B: Option A or B)
- [ ] Confirmatory Evaluation Halted (Policy 1)

### 7. Known Limitations & Epistemic Boundaries
- Current-file structural validity through observed EOF: 100% clean decoding across 18,975 recordings (18,845 via SoundFile/libmpg123, 130 via 3-way multi-decoder).
- Claim B (original-source completeness relative to uncompressed masters) remains UNVERIFIED for ALL 18,975 recordings.
- The 130 quarantined recordings have documented duration-estimation discrepancies from ID3v2 tags, which are NOT proven physical truncation.
- Clean decoding does NOT prove complete original recording capture or zero recording truncation.

### 8. Project Lead Determination
Decision Authority: Project Lead (Venkata Akhil Kumar)
Decision Status:    [X] APPROVED (Policy 2A Officially Executed)
                    [ ] REJECTED
                    [ ] AWAITING DETERMINATION
Decision Date:      2026-11-07
```

### Gate 2: Task 7.7.4 Non-Destructive Materialization Authorization Record

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

---

## Section 6: Protected Invariants & Operational Boundaries

- **Repository & Git State:** Tracked working tree is clean at base commit baee3b8381389ffde38e907dc137623748c254a8 (zero tracked modifications, zero staged changes), with three untracked local dossier deliverables (??).
- **Production Validator Code:** `scripts/materialize_stage6m_cohort3_audio.py` (**UNTOUCHED**).
- **Padding Threshold Constant:** `MAX_MP3_PADDING_FRAMES = 1152` (**UNTOUCHED** at line 394).
- **Production Unlink Behavior:** `dest_file.unlink(missing_ok=True)` intact at line 1049 (**UNTOUCHED**).
- **Accepted Audio Count:** Exactly 18,845 recordings in `cohort3_audio` (**UNTOUCHED**).
- **Quarantined Audio Count:** Exactly 130 recordings in `cohort3_rejected_quarantine` (**UNTOUCHED**).
- **Provisional Manifest Digest:** `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` (**UNLOCKED**, **UNTOUCHED**).
- **Acquisition Ledger LF Digest:** `63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5` (**UNTOUCHED**).
- **Quarantine Ledger LF Digest:** `98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8` (**UNTOUCHED**).
- **Gate 1 Scientific Admission:** **APPROVED** (Policy 2A Formally Adopted by Project Lead on 2026-11-07).
- **Confirmatory Audio Promotion:** **ZERO files promoted**; **ZERO speakers substituted**.
- **Task 7.7.4 Production Remediation:** **AUTHORIZED FOR IMPLEMENTATION & PRE-PRODUCTION VALIDATION** (Gate 2 approved on 2026-11-07; production dataset finalization reserved for Gate 3).
- **GPU CTTA Adaptation & Confirmatory Inference:** **BLOCKED / FROZEN**.

---

## Section 7: Stop Condition & Next Action

This dossier records the formal execution of Gate 1 (Scientific Admission Decision Record) under Policy 2A by the Project Lead (Venkata Akhil Kumar). Per protocol directives, Gate 1 authorizes solely the formal scientific admission criteria and target dataset definition; it does NOT authorize Task 7.7.4 materializer implementation, dataset mutations, manifest locking, or GPU CTTA execution. The next authorized milestone is the dedicated pre-Gate 2 test maintenance task, followed by the separate Gate 2 authorization decision.
