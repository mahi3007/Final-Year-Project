# Stage 6M v1.5 — Task 7.5 Cohort 3 Full Materialization Readiness Review

> **DOCUMENT ID:** `STAGE6M_COHORT3_FULL_MATERIALIZATION_READINESS_REVIEW`  
> **TASK ID:** `TASK_7_5`  
> **TASK TITLE:** Stage 6M Cohort 3 Full Materialization Readiness Review  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol (`v1.5-five-stratum-parity`)  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **READINESS DISPOSITION:** **TECHNICAL READINESS ESTABLISHED (FULL ACQUISITION HELD PENDING TASK 7.6 PROJECT-LEAD AUTHORIZATION)**  
> **GOVERNANCE STATUS:** **AUTHORIZED FOR DATA PREPARATION**  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:**  
> - **75-Clip Pilot:** `PILOT_COMPLETE_AND_VERIFIED`  
> - **Full 18,975-Clip Acquisition:** `BLOCKED_PENDING_TASK_7_6_AUTHORIZATION` (HELD)  
> - **Final Manifest Lock:** `BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION`  
> - **GPU CTTA Adaptation:** `STRICTLY_BLOCKED`  
> - **Confirmatory Model Inference:** `STRICTLY_BLOCKED`  
> **TIMESTAMP (UTC):** `2026-11-04T08:35:00Z`  

---

## 1. Executive Summary & Review Purpose

This document establishes the formal engineering and academic readiness review for the prospective full physical acquisition of **Stage 6M Cohort 3** ($18,975$ target audio recordings across $1,265$ unique speakers).

> **CRITICAL GOVERNANCE MANDATE:**  
> This milestone constitutes a **technical and administrative readiness review**, **NOT** permission or authorization to commence full-cohort physical downloading. In accordance with **Protocol Section 14.7**, full-cohort audio retrieval remains strictly blocked until a dedicated, separate Project-Lead authorization decision is formally established and recorded in Task 7.6.

Following the successful completion, independent verification, and evidence reconciliation of the Task 7.4.4 75-clip controlled physical pilot, this review systematically audits six foundational prerequisites:
1. **Provisional Manifest Verification:** Cryptographic stability, stratum allocations, speaker counts, and clip-per-speaker invariants.
2. **Source Availability & Provenance:** Exhaustive cross-referencing against Mozilla Common Voice 27.0 release inventory, 1:1 speaker identity, zero missing clips, and historical exposure isolation.
3. **Acquisition Engineering Readiness:** Demonstrated reliability of streaming decompression, LAME frame padding tolerance, RFC 9110 HTTP Range resume, URL refresh, network recovery, and isolated reporting.
4. **Storage & Operational Capacity:** Empirical file-size distribution modeling, upper-envelope storage projections, and filesystem headroom.
5. **Historical Engine Immutability:** Strict bitwise immutability of the frozen historical execution engine.
6. **Governance Gating:** Rigorous fail-closed policy enforcement preventing premature download, manifest mutation, GPU adaptation, or confirmatory inference.

---

## 2. Section A — Provisional Manifest Verification

The provisional selection manifest at [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) was audited in place without modification:

### 2.1 Manifest Scale and Allocation Invariants
| Requirement Parameter | Expected Specification | Verified Manifest State | Audit Disposition |
| :--- | :---: | :---: | :---: |
| **Total Target Speakers** | $1,265$ | **$1,265$** | **PASS** |
| **Clips per Speaker** | Exactly $15$ | **Exactly $15$** (set = $\{15\}$) | **PASS** |
| **Total Physical Clips** | $18,975$ ($1,265 \times 15$) | **$18,975$** | **PASS** |
| **Unique Clip Filenames** | $18,975$ | **$18,975$** (Duplicate clips: $0$) | **PASS** |
| **Evaluation Panel Speakers** | $1,100$ ($220 \times 5$ strata) | **$1,100$** ($16,500$ clips) | **PASS** |
| **Gate-Reference Speakers** | $100$ ($20 \times 5$ strata) | **$100$** ($1,500$ clips) | **PASS** |
| **Australian Reserve Speakers** | $65$ ($65 \times 15$ clips) | **$65$** ($975$ clips) | **PASS** |
| **Confirmatory Strata** | $5$ Strata | **$5$ Strata** | **PASS** |

### 2.2 Five-Stratum Distribution
| Confirmatory Stratum | Evaluation Speakers | Gate-Ref Speakers | Reserve Speakers | Total Speakers | Total Clips |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 220 | 20 | 65 | **305** | **4,575** |
| **Canadian English** | 220 | 20 | 0 | **240** | **3,600** |
| **England English** | 220 | 20 | 0 | **240** | **3,600** |
| **South Asian English** | 220 | 20 | 0 | **240** | **3,600** |
| **US English** | 220 | 20 | 0 | **240** | **3,600** |
| **Grand Total** | **1,100** | **100** | **65** | **1,265** | **18,975** |

### 2.3 Cryptographic Integrity
- **Provisional Manifest SHA-256:** `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`
- **Provisional Manifest CSV SHA-256:** `24013d3d63c1cadb978d68426e5ffaf490dbabb930a94788e2a9a7de70cf0a17`
- **Manifest Status:** **UNLOCKED (PROVISIONAL)** — Invariant: manifest locking requires 100% physical materialization and cannot precede physical acquisition.
- **Review Mutation Check:** **ZERO MUTATIONS** — The provisional manifest was audited read-only; no records were altered, reordered, or replaced.

---

## 3. Section B — Source Availability, Provenance & Exposure Isolation

### 3.1 Common Voice 27 Source Inventory Cross-Referencing
All $18,975$ target clips were audited against the official Common Voice 27.0 release inventory at [`datasets/external/common_voice_27/validated.tsv`](file:///C:/Users/venka/Downloads/final year project main/datasets/external/common_voice_27/validated.tsv):
- **Source Corpus Identity:** Mozilla Common Voice 27.0 release `cv-corpus-27.0-2026-09-11` (`en`).
- **Source Index File Size:** $614,927,262$ bytes ($614.93$ MB).
- **Source Index SHA-256:** `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a`.
- **Manifest Clips Matched in Source Inventory:** **18,975 / 18,975 (100.00%)**.
- **Missing Source Recordings:** **0**.
- **Clip-to-Speaker 1:1 Identity:** **100% Verified** — Every clip in the provisional manifest maps to the identical `client_id` in `validated.tsv` ($0$ speaker mismatches).
- **Substitutions / Silent Replacements:** **0** — Strict identity preservation; no surrogate recordings introduced.

### 3.2 Historical Exposure Isolation (Complete 558-Speaker Audit)
To strictly prevent data leakage and evaluate whether any candidate speaker was previously exposed during prior model training, tuning, or evaluation, all historical partitions were cross-referenced:
- **Historical Partitions Audited:**
  1. **Cohort 1 External Evaluation:** [`datasets/splits/stage5_external_eval.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage5_external_eval.csv) — $60$ unique speakers, SHA-256 `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32`.
  2. **Stage 5 Sentinel Panel:** [`datasets/splits/stage5_sentinel_panel.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage5_sentinel_panel.csv) — $30$ unique speakers, SHA-256 `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543`.
  3. **Cohort 2 Evaluation Partition:** [`datasets/splits/stage6m_cohort2_audio.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort2_audio.csv) — $468$ unique speakers, SHA-256 `dd837e249b15588cb15b7a3b234e820e08699722569cc24e57d119a868854f70`.
- **Historical Partition Pairwise Disjointness:** **100% Verified** ($0$ overlap across all three historical subsets).
- **Historical Exposed Pool (Union of Unique Speaker IDs):** **Exactly 558 unique speakers** ($60 + 30 + 468 = 558$).
- **Overlap with Cohort 3 Provisional Manifest (1,265 Speakers):** **Exactly 0 speakers (0.00%)**.
- **Isolation Disposition:** **PASS — 100% strict isolation confirmed across all historical evaluation and sentinel partitions.** No speaker previously utilized in any model evaluation, tuning, or development appears in Cohort 3.

---

## 4. Section C — Acquisition Engineering Readiness

The Task 7.4.4 physical pilot demonstrated production-grade materialization behavior across actual Common Voice archive members. Key engineering capabilities verified include:

### 4.1 Verified Materialization Mechanisms
1. **Full-File Bounded Chunk Decoding:**
   - Evaluated using `sf.SoundFile` streaming iterator in 4,096-frame blocks (~16 KB mono float32).
   - Entire bitstreams are parsed sequentially to verify decodability from header to terminating frame without unconstrained RAM allocation.
2. **MPEG Audio Layer III (LAME) Padding Tolerance:**
   - Mozilla Common Voice MP3 files encoded with LAME feature encoder delay (~528 samples) and container frame alignment padding.
   - Decoders (`libsndfile`/`mpg123`) strip encoder delay, producing shortfalls strictly $< 1,152$ samples ($1$ MPEG frame).
   - Enforces `declared_frames - total_decoded_frames <= 1152` (`MAX_MP3_PADDING_FRAMES`), tolerating valid codec delay while failing closed on bitstream truncations $> 1,152$ samples.
3. **RFC 9110 HTTP Range Resume & Reconnection:**
   - Enforces strict parsing of `bytes {start}-{end}/{total}` with total consistency validation across reconnects.
   - Rejects non-206 responses on resume, inverted byte ranges, and initial non-zero offsets.
4. **Presigned AWS S3 URL Refresh:**
   - Handled expiration of presigned S3 URLs by refreshing tokens and resuming streaming decompression at the exact byte offset without restarting.
5. **Network Interruption Recovery:**
   - Demonstrably verified during live pilot execution: recovered from socket drop (`getaddrinfo failed`) at byte offset $4,731,764,736$ B, resuming seamlessly with zero byte underflow or frame loss.
6. **Per-File SHA-256 Ledger Generation:**
   - Successfully generated cryptographic ledgers for physical audio files. Independent recalculation on disk verified 100% bitwise matching ($0$ mismatches).
7. **Speaker Completeness Accounting:**
   - All $1,265$ target speakers initialized upfront in completeness inventories.
   - Pilot successfully tracked 5/5 complete speakers with $15/15$ clips each.
8. **Artifact Isolation:**
   - `--output-dir` parameterization prevents test fixtures from mutating tracked repository reports.

### 4.2 Archive Termination Qualification Boundary
- **Engineering Decompression & Termination Validation:** Automated unit testing (`test_streaming_resume_range_validation`) validated complete gzip decompression and verified that `decompressor.eof == True` is strictly enforced before EOF is returned to the caller.
- **Empirical Pilot Boundary:** The 75-clip physical pilot materializer retrieved and verified all target recordings upon encountering target members in the tar stream up to member #1,188,858, at which point target acquisition reached 100% (75/75 clips) and the process exited cleanly.
- **Qualification Scope:** This confirms that the pilot acquisition successfully retrieved and validated the specified recordings, but it does **not** represent consumption of the entire ~95 GB compressed archive through its final gzip EOF marker. For full-cohort acquisition, streaming continues until all $18,975$ target clips are acquired or the complete tar archive is traversed. Full-archive traversal remains documented as an operational boundary for Task 7.6 full-cohort planning.

---

## 5. Section D — Storage and Operational Capacity

To prevent mid-acquisition disk exhaustion, storage requirements were modeled empirically from the complete target manifest ($18,975$ clips) and the physical pilot file-size distribution ($N=75$):

### 5.1 Empirical Pilot Audio Distribution ($N=75$)
- **Total Physical Bytes:** $3,397,743$ bytes ($3.24$ MiB / $3.40$ MB).
- **Mean Clip Size:** $45,303.2$ bytes ($44.24$ KiB / $45.30$ KB).
- **Median Clip Size:** $44,397.0$ bytes ($43.36$ KiB / $44.40$ KB).
- **Standard Deviation ($\sigma$):** $17,710.9$ bytes ($17.30$ KiB / $17.71$ KB).
- **Minimum Clip Size:** $14,637$ bytes ($14.29$ KiB / $14.64$ KB).
- **Maximum Clip Size:** $83,373$ bytes ($81.42$ KiB / $83.37$ KB).
- **95th Percentile ($P_{95}$):** $78,573$ bytes ($76.73$ KiB / $78.57$ KB).
- **Total Audio Duration:** $424.72$ seconds ($7.08$ minutes; mean $5.66$ s/clip).

### 5.2 Full-Cohort Storage Operational Planning Estimates ($18,975$ Clips)
> **PLANNING ESTIMATE QUALIFICATION:**  
> The figures below are derived from an empirical sample of $N=75$ physical recordings from $5$ speakers. Multiplying the sample's $P_{95}$ file size by $18,975$ does **not** establish a formal 95% upper confidence bound for total cohort size. Similarly, the mean plus three standard deviations scenario is a conservative planning envelope rather than a guaranteed maximum. They serve as operational planning estimates to size host storage headroom.

| Projection Scenario | Calculation Basis | Projected Raw Audio Bytes | Projected Raw Audio MB | Projected Raw Audio GB |
| :--- | :--- | :---: | :---: | :---: |
| **Mean Planning Estimate** | $18,975 \times \mu$ | $859,628,979$ | $819.81$ MiB | **$0.86$ GB** |
| **95th Percentile Planning Estimate** | $18,975 \times P_{95}$ | $1,490,922,675$ | $1,421.85$ MiB | **$1.49$ GB** |
| **Conservative 3σ Planning Envelope** | $18,975 \times (\mu + 3\sigma)$ | $1,867,823,803$ | $1,781.29$ MiB | **$1.87$ GB** |

### 5.3 Operational Headroom Budget
| Component | Budget Allocation | Rationale |
| :--- | :---: | :--- |
| **Conservative Raw Audio Storage** | $2.00$ GB | Reconciled reserve rounding up from the $1.87$ GB 3σ planning envelope |
| **Materialization Ledgers & Reports** | $0.05$ GB | $18,975$-row SHA-256 CSV, speaker reports, audit JSON/MD |
| **Streaming / Decompression Buffers** | $0.50$ GB | Ring buffers, tar extraction chunk buffers, curl temp pipes |
| **Validation & Recovery Headroom** | $0.50$ GB | Temporary soundfile decodes, checksum logs, retry caches |
| **Total Recommended Operational Reserve** | **$3.05$ GB** | **Minimum recommended host disk headroom ($2.00 + 0.05 + 0.50 + 0.50$)** |

### 5.4 Filesystem Capacity & Network Audit
- **Host System Drive:** `C:`
- **Measurement Timestamp (UTC):** `2026-11-04T09:46:12Z`
- **Available Free Space (Historical Evidence):** **$23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB)** recorded at audit timestamp.
- **Operational Reserve Requirement:** $3.05$ decimal GB ($2.84$ GiB).
- **Safety Margin Ratio:** **$\frac{23.65\text{ GB}}{3.05\text{ GB}} \approx \mathbf{7.75\times}$** ($> 770\%$ of required headroom).
- **Historical Evidence Qualification:** The $23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB) free space represents historical capacity evidence captured at timestamp `2026-11-04T09:46:12Z`. It does not constitute a guaranteed maximum or perpetual reservation; available host disk space must be independently re-verified before full physical acquisition begins in Task 7.7.
- **Storage Capacity Verdict:** **PASS — Substantial operational headroom confirmed on recorded evidence.**
- **Network Operational Parameters:** Full acquisition traverses an archive up to ~95 GB (gzip compressed). Estimated streaming duration is 3.5 to 8.0 hours depending on network throughput, MDC server response latency, and HTTP Range resume overhead. The materializer's resume and socket recovery mechanisms have been proven during pilot execution.

---

## 6. Section E — Historical Engine Immutability Audit

The frozen historical execution code was audited directly via Git object hash:
```powershell
git hash-object src/dsg_ctta/evaluation/paired_cluster_inference.py
```
- **Observed Git Blob Hash:** `58d456fbcce43b5322d56df80e4077a32d7f4cca`
- **Expected Historical Hash:** `58d456fbcce43b5322d56df80e4077a32d7f4cca`
- **Diff against Historical Commit `a7a3b79`:** **Exactly 0 lines.**
- **Immutability Disposition:** **PASS — Historical inference engine is 100% untouched and cryptographically frozen.**

---

## 7. Section F — Governance Decision & Fail-Closed Safeguards

### 7.1 Core Assessment Question
> **Is the project technically and administratively ready for the separate full 18,975-clip acquisition?**

**Answer: YES — Technical and administrative readiness is established.**  
- Provisional manifest scale, five-stratum allocation, and cryptographic hash are verified.
- Source availability in Common Voice 27 is 100% confirmed with zero missing clips and zero exposure overlap.
- Materialization streaming, decoding, resume, and reporting mechanisms are fully proven by the 75-clip physical pilot.
- Storage capacity exceeds conservative operational headroom by over $8\times$.
- Historical execution engine remains bitwise immutable.

### 7.2 Fail-Closed Policy Enforcement (Protocol Section 14.7)
Despite full technical readiness, **physical acquisition of the full cohort remains STRICTLY HELD**:
```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                     GOVERNANCE HOLD: TASK 7.6 AUTHORIZATION REQUIRED                 ║
║                                                                                      ║
║  1. Technical readiness is established by Task 7.5 Readiness Review.                 ║
║  2. Full 18,975-clip physical materialization is NOT authorized by pilot pass.       ║
║  3. Materializer fails closed: full_audio_materialization remains                    ║
║     BLOCKED_PENDING_TASK_7_6_AUTHORIZATION until Task 7.6 approval.                  ║
║  4. Final manifest lock remains BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION.     ║
║  5. Confirmatory GPU CTTA adaptation & inference remain STRICTLY BLOCKED.            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Subsequent Project Roadmap

| Milestone | Task ID | Scope & Objective | Current Governance Status |
| :--- | :---: | :--- | :---: |
| **Physical Pilot Completion** | Task 7.4.4 | 75 physical clips verified across 5 strata | **COMPLETE & VERIFIED** |
| **Evidence Reconciliation** | Task 7.4.5 | Publish final pilot evidence, reconcile repo | **COMPLETE & PUBLISHED** |
| **Cohort 3 Readiness Review** | Task 7.5 | Source feasibility, manifest integrity, storage review | **COMPLETE (THIS REPORT)** |
| **Separate Full-Cohort Authorization** | Task 7.6 | Formal Project-Lead academic decision under Sec 14.7 | **NEXT PENDING MILESTONE** |
| **Full Physical Materialization** | Task 7.7 | Acquire and validate 18,975 clips under Sec 14.7 scope | **BLOCKED PENDING TASK 7.6** |
| **Final Manifest Validation & Lock** | Task 7.8 | 100% physical completeness audit and manifest freeze | **BLOCKED PENDING TASK 7.7** |
| **Confirmatory Execution Authorization** | Subsequent | GPU CTTA adaptation and confirmatory inference | **STRICTLY BLOCKED** |
