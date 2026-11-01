# Stage 6M v1.5 — Cohort 3 Source Identity & Selection Manifest Audit Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_SOURCE_AUDIT`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **GOVERNANCE DISPOSITION:** **AUTHORIZED FOR DATA PREPARATION** (Confirmatory GPU Adaptation Separately Gated)  
> **AUDIT TIMESTAMP (UTC):** 2026-11-01T11:32:29.467918+00:00  
> **SELECTION SEED:** `20261101`  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  

---

## 1. Executive Summary

In accordance with formal Project-Lead Academic Authorization executed under Protocol Section 14.7, this audit establishes the empirical source data integrity, historical partition disjointness, and provisional panel selection for **Cohort 3 Data Preparation**:

1. **Source Identity Verified:** Mozilla Common Voice 27.0 `validated.tsv` matches its authoritative audit hash and size with bitwise exactness (**0 byte difference**).
2. **Historical Exposure Fully Excluded:** All 558 historical speakers across Cohort 1 (60), Stage 5 Sentinel (30), and Cohort 2 (468) are verified as pairwise disjoint and 100% excluded from the Cohort 3 selection pool (**0 speaker overlap**).
3. **Canonical Capacity Confirmed:** Eligible unexposed capacities match registered requirements across all strata, including 305 Australian speakers and 0 unexposed Irish speakers.
4. **Provisional Panels Selected:** Exactly 1,100 confirmatory evaluation speakers ($220 	imes 5$), 100 separate gate-reference speakers ($20 	imes 5$), and 65 Australian replacement reserve speakers are deterministically selected with seed `20261101`.
5. **Provisional Manifest Generated:** An unlocked machine-readable selection manifest (JSON and CSV) is constructed containing 18,975 qualifying clips across 1,265 unique speakers.
6. **Execution Gating Preserved:** Model loading, GPU test-time adaptation, and confirmatory inference remain **STRICTLY BLOCKED** under a separate execution gate pending physical audio download, decode validation, and final manifest locking.

---

## 2. Task A — Source Corpus Bitwise Identity

| Metric | Prespecified Audit Target | Actual Measured Value | Verdict |
| :--- | :--- | :--- | :---: |
| **Source File** | `datasets/external/common_voice_27/validated.tsv` | `datasets/external/common_voice_27/validated.tsv` | **PASS** |
| **Row Count** | 1,929,267 rows | 1,929,267 rows | **PASS** |
| **Byte Size** | 614,927,262 bytes | 614,927,262 bytes | **PASS** |
| **SHA-256 Digest** | `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a` | `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a` | **PASS (BITWISE)** |

---

## 3. Task B — Historical Partition Exposure Reconciliation

| Historical Partition | File Name | Unique Speakers | Historical Exposure Excluded | Overlap with Cohort 3 |
| :--- | :--- | :---: | :---: | :---: |
| **Cohort 1** | `stage5_external_eval.csv` | 60 | 60 | **0** |
| **Stage 5 Sentinel** | `stage5_sentinel_panel.csv` | 30 | 30 | **0** |
| **Cohort 2** | `stage6m_cohort2_audio.csv` | 468 | 468 | **0** |
| **Total Unique Prior** | — | **558** | **558** | **EXACTLY ZERO (0)** |

---

## 4. Task C — Reconciled Speaker Capacity Ledger

| Stratum | Raw Declared | Strict ($\ge 15$ clips) | Prior Exposed | Available Unexposed | Selected Eval | Selected Gate | Selected Reserve | Capacity Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 804 | 398 | 93 | **305** | 220 | 20 | 65 | **VERIFIED** |
| **Canadian English** | 1,031 | 511 | 93 | **418** | 220 | 20 | 0 | **VERIFIED** |
| **England English** | 2,733 | 1,213 | 93 | **1,120** | 220 | 20 | 0 | **VERIFIED** |
| **South Asian English** | 2,459 | 746 | 93 | **653** | 220 | 20 | 0 | **VERIFIED** |
| **US English** | 9,085 | 3,884 | 93 | **3,791** | 220 | 20 | 0 | **VERIFIED** |
| **Irish English** | 220 | 92 | 92 | **0** | 0 | 0 | 0 | **VERIFIED** |

---

## 5. Task D & E — Provisional Panel Selection Architecture

- **Selection Seed:** `20261101` (Date of Project-Lead Authorization)
- **Selection Algorithm:**
  1. Candidate unexposed eligible speakers ranked by `sha256("20261101:speaker:<stratum>:<speaker_id>")`.
  2. First 220 speakers allocated to `evaluation`.
  3. Next 20 speakers allocated to `gate_reference`.
  4. For Australian English, remaining 65 speakers allocated to `australian_reserve`.
  5. For each speaker, qualifying clips ranked by `sha256("20261101:clip:<speaker_id>:<clip_path>")`; first 15 selected.

### Selected Population Totals:
- **Confirmatory Evaluation Speakers:** $1,100$ ($220 	imes 5$ strata)
- **Gate-Reference Speakers:** $100$ ($20 	imes 5$ strata)
- **Australian Replacement Reserve:** $65$ speakers (+21.3% buffer)
- **Total Unique Selected Speakers:** $1,265$ speakers
- **Clips per Speaker:** Exactly $15$ strictly qualifying clips (Predicate V1.5-Strict)
- **Total Selected Clips:** $18,975$ clips ($16,500$ evaluation, $1,500$ gate-reference, $975$ reserve)

---

## 6. Task F — Validation Summary

- **Speaker Counts:** Exactly $1,100$ evaluation, $100$ gate-reference, $65$ Australian reserve (**PASS**).
- **Panel Disjointness:** Zero overlap between evaluation, gate-reference, and reserve panels (**PASS**).
- **Historical Disjointness:** Zero overlap between selected speakers and 558 prior exposed speakers (**PASS**).
- **Clip Balance:** Exactly 15 clips per speaker across all 1,265 speakers (**PASS**).
- **ID Deduplication:** Exactly zero duplicate clip IDs or speaker IDs (**PASS**).
- **Provisional Manifest Hashes:**
  - JSON Manifest (`stage6m_cohort3_provisional_manifest.json`): `d1c9a1d1bb9d111112e2217bd2fce64df2436bffca525bee545dae123e034be5`
  - CSV Manifest (`stage6m_cohort3_provisional_manifest.csv`): `24013d3d63c1cadb978d68426e5ffaf490dbabb930a94788e2a9a7de70cf0a17`

---

## 7. Task H — Execution Gating & Next Operational Milestones

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: AUTHORIZED (DATA PREPARATION)                   ║
║                                                                                      ║
║  1. Source audit, capacity reconciliation, and provisional manifest are COMPLETE.    ║
║  2. Audio downloading and physical validation are AUTHORIZED under controlled        ║
║     pipelines with bitwise SHA-256 verification.                                     ║
║  3. Confirmatory GPU CTTA adaptation and model inference remain STRICTLY BLOCKED     ║
║     under a separate execution gate pending final manifest locking.                  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Remote Tracking & Fixed Historical Baseline Reconciliation

1. **Remote Repository Synchronization:**
   - Commit `fe73fba548c25335fdb7bcb10a799c2162d6e82e` (Milestone 7.1–7.3 deliverable) is verified on remote GitHub `origin/main` with parent `06cf833` (Project-Lead Academic Authorization).
   - Remote branch listing reflects `main` as authoritative.
2. **Fixed Baseline Immutability:**
   - The frozen execution code (`src/dsg_ctta/evaluation/paired_cluster_inference.py`) is verified against the historical frozen commit `a7a3b79`.
   - Authoritative Git object blob hash: `58d456fbcce43b5322d56df80e4077a32d7f4cca`.
   - Exact bitwise match verified (**0 diff against fixed commit `a7a3b79`**), independent of moving branch references.

