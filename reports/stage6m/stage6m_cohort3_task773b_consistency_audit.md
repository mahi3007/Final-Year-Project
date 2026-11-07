# Stage 6M v1.5 Task 7.7.3E — Historical Power Provenance Final Reconciliation

**Generated:** 2026-11-06T20:30:00+00:00<br>
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7, Project-Lead Academic Authorization)<br>
**Branch / Starting Commit:** `stage6m-five-stratum-parity` @ `949f9f1`<br>
**Document Status:** **SPECIFICATION_CLOSURE_PROPOSAL_ONLY** (Independent consistency audit; production code untouched)<br>

---

## Executive Summary

Task 7.7.3E achieves complete historical and forensic closure of the Stage 6M v1.5 power simulation provenance. It formally reconciles the three separate historical power simulation results at $N_g = 220$ to their respective underlying artifacts, execution depths, and exact Clopper-Pearson Beta quantiles, eliminating previous conflations between one-sided lower confidence bounds and two-sided confidence interval lower endpoints.

Key Provenance Closures Achieved in Task 7.7.3E:
1. **Three Distinct Historical Results Disentangled with Exact Clopper-Pearson Bounds ($N_g = 220$):**
   - **Result A: Task 5 Exploratory Screening (94.65%):** 2,000 outer trials, $B=2,000$ bootstrap replicates, uncalibrated grid sweep; One-Sided 95% LCB = **93.747416%**, Two-Sided 95% CI: [93.571456%, 95.595129%] (superseded exploratory screening).
   - **Result B: Task 5 Uncalibrated Confirmation (95.35%):** 10,000 outer trials, $B=20,000$ bootstrap replicates, uncalibrated generator with disparity clipping overshoot; One-Sided 95% LCB = **94.988733%**, Two-Sided 95% CI: [94.918893%, 95.754440%] (superseded full-depth confirmation).
   - **Result C: Task 6.3 Calibrated Primary-Model Confirmation (90.58%):** 10,000 outer trials, $B=20,000$ bootstrap replicates, strictly calibrated quadrature; One-Sided 95% Clopper-Pearson LCB = **90.085739%** $\ge 90.0000\%$, Two-Sided 95% CI: [89.990601%, 91.145641%] (governing Section 14.7 approved design).
2. **Incomplete Speaker Analysis Reconciled:** Census of 13 affected evaluation speakers (4 empty, 9 partial clusters, 65 accepted clips) and stratum counts for Options A (1,087 eval speakers) and B (1,096 eval speakers) documented; neither option preserves the registered design or inherits the 90.58% power result without re-evaluation; Australian reserves replace Australian dropouts only.
3. **Admission & Role Terminology Clarified:** Separates dataset-asset admission (18,975 recordings) from confirmatory evaluation participation (1,100 eval, 100 gate, 65 reserve). Formulates Policy 2B strictly as an ESTIMATION_DISCREPANCY_SCREEN rather than physical corruption.
4. **Archive Recovery Complexity Corrected:** Explicitly states sequential tar.gz restart requires continuous decompression, TAR scanning, and in-memory hashing for verified members (no disk writes, no audio decoding), formally retracting the 'zero validation overhead' claim.
5. **Crash Durability & WAL Hardened:** Specifies Windows MoveFileExW no-replace vs write-through flags, defines the DURABILITY_UNCERTAIN recovery state for directory fsync failures, and specifies WAL transaction IDs, serialized single-writer appends, and idempotent ledger projection.
6. **Numerical & Matrix Closure:** Reconciles the single-byte inventory against frozen ledgers (704,970,734 B accepted, 4,780,224 B quarantine, 709,750,958 B total) and qualifies all 23 adversarial scenarios as proposed future tests.

---

## Section 1: Power Provenance & Sampling Design Alignment (Phase 1)

### 1.1 Historical Power Provenance Reconciliation at $N_g = 220$

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

### 1.2 Side-by-Side Sampling Architecture Comparison

| Sampling Dimension | Approved Protocol v1.5 Spec | Task 6.3 Calibrated Confirmation | Provisional Manifest (`provisional_manifest.json`) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Governing Benchmark Strata** | 5 Strata (Australian, Canadian, England, South Asian, US) | 5 Strata evaluated across N_g in [220, 285] | 5 Strata (Australian, Canadian, England, South Asian, US) | **CONGRUENT** |
| **Confirmatory Evaluation Speakers** | 1,100 speakers (N_g = 220 per stratum) | N_g = 220: Confirmed 90.58% joint power (LCB_95 = 90.085739%) | 1,100 evaluation speakers (220 per stratum x 5) | **CONGRUENT** |
| **Clips per Speaker (Cluster Size C)** | C = 15 clips per speaker | C = 15 clips per speaker (sigma_paired = 0.032 speaker-level) | 15 clips per speaker (100% of selected speakers) | **CONGRUENT** |
| **Gate-Reference Speaker Reserve** | 100 speakers (20 per stratum; excluded from eval power) | 20 reserved gate speakers deducted from capacity ceiling | 100 gate-reference speakers (20 per stratum x 5) | **CONGRUENT** |
| **Australian Replacement Reserve** | 65 speakers (285 - 220 = 65 unexposed Australian reserve) | Preserves 65 Australian evaluation speakers (+21.3% buffer) | 65 Australian reserve speakers (role: australian_reserve) | **CONGRUENT** |
| **Total Materialized Speakers** | 1,265 speakers (1,100 eval + 100 gate + 65 reserve) | Capacity envelope bounded by Australian N_total <= 305 | 1,265 speakers (1,100 eval + 100 gate + 65 reserve) | **CONGRUENT** |
| **Total Materialized Audio Clips** | 18,975 clips (1,265 x 15) | Not directly modeled (clip count fixed at 15/speaker) | 18,975 clips (16,500 eval + 1,500 gate + 975 reserve) | **CONGRUENT** |

---

## Section 2: Incomplete Speaker Analysis & Power Consequences (Phase 2)

### Census of Affected Evaluation Speakers

- **Total Manifest Speakers:** 1,265 speakers (1,100 eval + 100 gate + 65 reserve)
- **Evaluation Speakers with 15/15 Clips Fully Intact:** **1,087 / 1,100 speakers (98.82%)**
- **Affected Evaluation Speakers:** **13 speakers** (Canadian: 5, US: 5, Australian: 2, England: 1, South Asian: 0)
- **Empty Clusters ($C_i = 0$):** **4 speakers** (0 clips retained)
- **Partial Clusters ($1 \le C_i \le 14$):** **9 speakers** (65 accepted clips retained)
- **Quarantined Clips across Affected Speakers:** Exactly **130 clips**

### Per-Stratum Evaluation Speaker Counts under Policy 2B

| Stratum | Registered Target ($N_g$) | Option A: Complete Clusters ($C_i = 15$) | Option B: Non-Empty Clusters ($C_i \ge 1$) | Option A Delta | Option B Delta |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 220 | **218** | **220** | -2 | 0 |
| **Canadian English** | 220 | **215** | **217** | -5 | -3 |
| **England English** | 220 | **219** | **220** | -1 | 0 |
| **South Asian English** | 220 | **220** | **220** | 0 | 0 |
| **US English** | 220 | **215** | **219** | -5 | -1 |
| **Total Evaluation Speakers** | 1100 | **1087** | **1096** | -13 | -4 |

### Statistical & Power Consequences

CRITICAL STATISTICAL FINDING: Under Policy 2B, neither Option A (complete clusters only) nor Option B (unequal clusters) preserves the full registered N_g = 220 design across all strata. Option A results in cross-stratum speaker sample size imbalance (N_g in [215, 220], total 1,087 speakers), while Option B retains more recordings (65 accepted clips across 9 partial clusters) but introduces nine unequal-size speaker clusters (C_i in [1, 14] for 9 speakers, total 1,096 speakers). Under Option B, the statistical analysis must formally define whether speakers or recordings receive equal weighting and how the paired-cluster bootstrap handles those unequal cluster sizes (e.g. cluster-level resampling vs ratio estimation). The approved Task 6.3 joint power of 90.58% applies strictly to the balanced N_g = 220, C = 15 specification. Therefore, NEITHER OPTION CAN INHERIT THE APPROVED 90.58% POWER RESULT WITHOUT A FORMAL RE-EVALUATION. A dedicated Monte Carlo power simulation would be required to verify whether Option A or Option B maintains the one-sided 95% LCB >= 90.0% threshold.

### Replacement Reserve Feasibility (Option C Nuance)

OPTION C STRUCTURAL SCOPE: The provisional manifest contains 65 replacement reserve speakers for Australian English ONLY. These 65 Australian reserves may potentially replace the 2 affected Australian evaluation speakers (restoring Australian English to 220 complete speakers), strictly subject to the protocol's replacement conditions. However, the manifest contains ZERO replacement reserves for Canadian (5 affected), US (5 affected), or England (1 affected). The Australian reserves cannot replace Canadian, US, or England speakers without destroying accent stratum validity. Therefore, full cohort restoration through the reserve is structurally impossible without a formal protocol amendment and drawing from unexposed Common Voice pools.

---

## Section 3: Admission Policy Formulation & Role Terminology (Phase 3)

### Dataset-Asset Admission vs. Confirmatory Evaluation Participation

CRITICAL GOVERNANCE DISTINCTION: Admitting all 18,975 recordings into the dataset assets (e.g. under Policy 2A) does NOT mean all 1,265 speakers participate in the confirmatory evaluation estimand. The 1,100 evaluation speakers, 100 gate-reference speakers, and 65 Australian reserve speakers strictly retain their distinct, pre-registered roles: - Evaluation Speakers (1,100): Exclusively evaluated in Primary Hypothesis Testing (Events A, B, C, D). - Gate-Reference Speakers (100): Exclusively calibrate adaptation gating; never evaluated in WER contrast estimands. - Australian Reserve Speakers (65): Standby pool for authorized dropouts; unexposed during primary confirmatory execution.

### Refining Policy 2B as an Estimation Discrepancy Screen

Policy 2B is formally designated an ESTIMATION_DISCREPANCY_SCREEN (or ESTIMATION_SHORTFALL_HOLD). The shortfall threshold (Delta > 1152 samples / 24-67.5 ms) represents an inherited duration-estimation discrepancy arising from non-audio container bytes. It is NOT evidence of physical bitstream corruption or upstream whole-frame truncation. The 130 recordings are held under ADMISSION_HOLD in diagnostic quarantine as an empirical discrepancy anomaly, and any scientific decision regarding their eventual admission requires separate Project Lead authorization.

### Comparative Policy Formulation Matrix

| Policy Option | Decision Status | Governing Admission Rule | Admitted Clips | Quarantined Clips | Evaluated Speakers ($N_{\text{eval}}$) | Operational & Epistemic Consequences |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Strict Mandatory Claim B Prerequisite** (`POLICY_1`) | *Project Lead Protocol Decision (Option 1)* | Admit IF AND ONLY IF Claim B (authoritative master duration) is verified. | **0** | **18,975** | **0** | All 18,975 recordings placed on ADMISSION_HOLD; confirmatory benchmark paused. |
| **Pure Claim A Physical Bitstream Admission** (`POLICY_2A`) | *Project Lead Protocol Decision (Option 2A)* | Admit under PROTOCOL_ADMIT_ORIGIN_UNVERIFIED IF physical MPEG frames are complete to EOF and PCM decoding succeeds. | **18,975** | **0** | **1,265** | All 18,975 recordings admitted as dataset assets. Restores all 1,100 evaluation speakers to 15-clip clusters. |
| **Decoupled Physical Validation with Estimation Discrepancy Screen** (`POLICY_2B`) | *Project Lead Protocol Decision (Option 2B)* | Admit if physical frames complete AND container shortfall Delta <= 1152. Hold if Delta > 1152. | **18,845** | **130** | **1,252** | Admits 18,845 baseline files; holds 130 files in diagnostic quarantine under ADMISSION_HOLD. 13 evaluation speakers handled via Option A or B. |

---

## Section 4: Recovery Specification Refinements & Complexity (Phase 4)

### Archive Replay Complexity

In a sequential .tar.gz archive, TAR member headers are compressed within a continuous DEFLATE bitstream without seek points. On network reconnect or restart from byte 0: the client sequentially replays decompression and TAR member scanning. To verify previously committed members against recorded ledger hashes, their decompressed payload must still be streamed and hashed in memory. Thus: NO REPEATED DISK WRITES and NO REPEATED AUDIO DECODING occur for committed members, but DECOMPRESSION, TAR SCANNING, and IN-MEMORY HASH COMPUTATION DO OCCUR. True O(1) random-access requires an external index. The claim of zero validation overhead is formally retracted.

### Windows Promotion Flags (No-Replace vs. Write-Through)

On Windows, atomic no-clobber promotion must use MoveFileExW with flag 0 (omitting MOVEFILE_REPLACE_EXISTING), which fails atomically with ERROR_ALREADY_EXISTS if the target exists. Where immediate filesystem metadata durability is required, the implementation must additionally specify MOVEFILE_WRITE_THROUGH. The implementation explicitly separates no-replace behavior from durability.

### Durability Uncertain Recovery State (`DURABILITY_UNCERTAIN`)

In Scenario 20 (filesystem metadata flush failure): if promotion succeeds (e.g. POSIX hard-link created or MoveFileExW executed) but directory metadata fsync fails, the promotion cannot simply be 'aborted and staged file retained' because the destination link already exists on disk. The pipeline transitions the recording to state DURABILITY_UNCERTAIN: 1. Retain both staging and destination copies without unlinking either. 2. Write a DURABILITY_UNCERTAIN record to the WAL journal with unique tx_id. 3. Stop further materialization. 4. On restart, the reconciliation sweep verifies destination file existence and SHA-256 against staging; if identical, completes    ledger write and removes redundant staging link. Zero acquired copies are deleted.

### WAL Transaction Architecture

The Write-Ahead Log (.staging/wal_journal.jsonl) uses unique transaction IDs (tx_id = uuid4 or monotonic counter) with serialized single-writer appends. Each entry contains: tx_id, timestamp, rec_id, attempt_id, staging_path, target_path, sha256, status. Torn or partial final lines on recovery are discarded; uncommitted PREPARED entries inspect destination existence and reconcile idempotently. The CSV ledgers are reproducible, idempotent projections of the authoritative WAL journal.

### Definition of Zero Unlinking

Zero unlinking strictly means NEVER DELETING THE ONLY ACQUIRED COPY of an audio recording. Removing a redundant staging hard-link after verified, fsynced destination creation does not violate evidence preservation.

---

## Section 5: Numerical & Test Evidence Closure (Phase 5)

### Single Authoritative Per-File Inventory

| Evidence Population | Verified Files | Authoritative Exact Bytes | MiB ($1024^2$) | MB ($10^6$) | Ledger Agreement |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Accepted Audio (`cohort3_audio`)** | 18,845 | **704,970,734 B** | 672.31 MiB | 704.97 MB | [`stage6m_cohort3_clip_sha256_ledger.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv) (**100.0% Match**) |
| **Quarantine Audio (`cohort3_rejected_quarantine`)** | 130 | **4,780,224 B** | 4.56 MiB | 4.78 MB | [`stage6m_cohort3_quarantine_ledger.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_quarantine_ledger.csv) (**100.0% Match**) |
| **Total Evidence Base** | **18,975** | **709,750,958 B** | **676.87 MiB** | **709.75 MB** | **All 18,975 file digests verified against frozen ledgers** |

### Explanation of Differences from Preliminary Exploratory Profiling

- Accepted Delta: **+6,448 B (704,970,734 authoritative vs 704,964,286 preliminary exploratory estimate).**
- Quarantine Delta: **-1,205 B (4,780,224 authoritative vs 4,781,429 preliminary exploratory estimate).**
- Net Total Delta: **+5,243 B (709,750,958 authoritative vs 709,745,715 preliminary exploratory estimate).**
- **Reconciliation:** Earlier values were preliminary exploratory estimates; frozen ledgers and disk match to the single byte.

### Qualification of Adversarial Scenarios

> [!WARNING]
> **All 23 scenarios represent a proposed test matrix for future validation suites. They do NOT constitute proof that the proposed staging, atomic promotion, crash recovery, and ledger reconciliation pipeline has passed those tests, because that pipeline is currently in proposal status and has not yet been implemented.**

---

## Section 6: Protected State & Invariant Verification

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

## Section 7: Unresolved Decisions for Project Lead Determination

1. **Admission Policy Selection:** Project Lead must formally select among:
   - **Policy 1:** Strict Claim B mandate (holds all 18,975 recordings; benchmark paused).
   - **Policy 2A:** Pure Claim A physical admission (admits all 18,975 recordings as dataset assets under PROTOCOL_ADMIT_ORIGIN_UNVERIFIED).
   - **Policy 2B:** Estimation discrepancy screen (admits 18,845 baseline recordings, holds 130 in diagnostic quarantine).
2. **Incomplete Evaluation Speaker Strategy & Power Re-evaluation:** If Policy 2B is selected:
   - Formally select between Option A (complete clusters only, N_eval = 1,087) and Option B (unequal cluster weighting, N_eval = 1,096).
   - Commission a new Monte Carlo power simulation to verify whether Option A or Option B maintains one-sided 95% LCB >= 90.0%.
3. **Remediation Implementation Authorization (Task 7.7.4):** Remediation pipeline implementation remains on HOLD pending written Project Lead authorization.
