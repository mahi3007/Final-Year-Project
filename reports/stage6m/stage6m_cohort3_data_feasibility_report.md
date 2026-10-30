# Stage 6M Confirmatory Cohort 3 — Data Feasibility & Speaker Capacity Audit Report

- **Governing Standard:** ADR-005
- **Protocol Version:** v1.4.0
- **Decision Rule:** Decision Rule B
- **Predicate Version:** V1.4.0-Strict
- **Target Specification:** 6 Strata x 220 Speakers x 15 Clips = 19,800 Cohort 3 Clips + 120-Speaker Dedicated Gate-Reference Panel (Total = 1,440 Speakers)
- **Audit Timestamp (UTC):** 2026-10-30T11:58:57.059166+00:00
- **Curation Script Commit:** [`6a9190a`](https://github.com/mahi3007/Final-Year-Project/commit/6a9190a8d6bd81883a83bf0a971228118c4b790c)
- **Overall Feasibility Disposition:** **FAIL-CLOSED CAPACITY BOTTLENECK (COHORT 3 MATERIALIZATION FORBIDDEN)**

---

## 1. Executive Summary & Core Feasibility Finding

This audit evaluates the empirical capacity of **Mozilla Common Voice 27.0** (`validated.tsv`) to satisfy the statistical sample size requirements of **Decision Rule B** (1,320 independent speakers, 19,800 clips) and a separate 120-speaker Gate Reference Panel, while strictly enforcing **zero speaker leakage** against all prior developmental and confirmatory partitions.

### Key Finding:
1. **Five Strata Have Surplus Unexposed Capacity:** Australian English, Canadian English, England English, South Asian English, and US English all possess ample strictly qualified, unexposed speakers ($\ge 305$ to $3,791$ available vs. $240$ required).
2. **Irish English Represents an Absolute Empirical Bottleneck:**
   - In the **entirety** of Common Voice 27 worldwide, there are only **220 raw speakers** with declared Irish English accent.
   - Only **92 unique Irish speakers** meet strict quality filtering ($\ge 15$ distinct qualified clips satisfying Predicate V: `locale == 'en'`, `up_votes >= 2`, `down_votes < 2`, `words >= 2`, non-empty path).
   - All **92** strictly eligible Irish speakers have already been exposed across historical partitions.
   - Consequently, the number of unexposed, strictly qualified Irish English speakers available in Common Voice 27 is **EXACTLY ZERO (0)**.
   - The stratum shortfall for Irish English is **240 speakers** (or **148 speakers** even if all historical data were disregarded).

---

## 2. Empirical Speaker Capacity Ledger

| Stratum | Raw Declared | Strict ($\ge 15$ clips) | Prior Exposed | Unexposed Available | Req C3 | Req Gate | Total Req | Shortfall | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 804 | 398 | 93 | **305** | 220 | 20 | 240 | 0 | **PASS** |
| **Canadian English** | 1,031 | 511 | 93 | **418** | 220 | 20 | 240 | 0 | **PASS** |
| **England English** | 2,733 | 1,213 | 93 | **1,120** | 220 | 20 | 240 | 0 | **PASS** |
| **Irish English** | 220 | 92 | 92 | **0** | 220 | 20 | 240 | 240 | **CRITICAL SHORTFALL** |
| **South Asian English** | 2,459 | 746 | 93 | **653** | 220 | 20 | 240 | 0 | **PASS** |
| **US English** | 9,085 | 3,884 | 93 | **3,791** | 220 | 20 | 240 | 0 | **PASS** |

*Note on Physical vs Metadata Availability:* This feasibility audit establishes candidate speaker capacity from verified metadata in `validated.tsv`. Under Protocol v1.4.0, physical audio availability requires file existence on disk, decodability, and bitwise SHA-256 verification after materialization.

---

## 3. Historical Partition Disjointness & Irish Exposure Reconciliation

### 3.1 Historical Partition Ledger & Provenance
| Partition | File Name | Rows | Unique Speakers | SHA-256 Digest | Disjointness Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **Cohort 1** | `stage5_external_eval.csv` | 900 | 60 | `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32` | **DISJOINT** |
| **Stage 5 Sentinel** | `stage5_sentinel_panel.csv` | 300 | 30 | `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543` | **DISJOINT** |
| **Cohort 2** | `stage6m_cohort2_audio.csv` | 7,020 | 468 | `dd837e249b15588cb15b7a3b234e820e08699722569cc24e57d119a868854f70` | **DISJOINT** |
| **Total Unique** | — | **8,220** | **558** | — | **ZERO OVERLAP** |

### 3.2 Precise Irish Exposure Reconciliation
- **Total Historically Exposed Irish Speakers:** **93 unique speakers** (10 in Cohort 1, 5 in Stage 5 Sentinel, 78 in Cohort 2).
- **Historically Exposed Meeting Strict Predicate V:** **92 unique speakers**.
- **Historical Irish Ineligible Under Strict Predicate V:** **1 speaker** (`f3ea04475e301f84785710b9c56023f3c81f7abff656d40e674db8acde55c748688d0a4285eb6e8ea7f4d8b1fb6c99ab3c7f7d460878c4193256a61831e17ce7`).
- **Detailed Explanation:** Speaker `f3ea04475e301f84...` (from Cohort 1 (Stage 5 External Eval)) has 16 total clips in Common Voice 27, but only 13 clips satisfy strict Predicate V (Only 13 of 16 clips satisfy Predicate V: 2 clip(s) fail down_votes < 2 (down_votes >= 2), 1 clip(s) fail words >= 2 (words < 2). Requires >= 15.).
- **Unexposed Strictly Eligible Irish Speakers Remaining:** **0**.

---

## 4. Immutable Source Data Provenance

```json
{
  "source_dataset": "Mozilla Common Voice",
  "source_release": "cv-corpus-27.0-2026-09-11",
  "source_file": "datasets/external/common_voice_27/validated.tsv",
  "source_file_bytes": 614927262,
  "source_file_sha256": "733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a",
  "source_rows_scanned": 1929267,
  "curation_script_commit": "6a9190a8d6bd81883a83bf0a971228118c4b790c",
  "predicate_version": "V1.4.0-Strict",
  "historical_partition_hashes": {
    "stage5_external_eval.csv": "41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32",
    "stage5_sentinel_panel.csv": "665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543",
    "stage6m_cohort2_audio.csv": "dd837e249b15588cb15b7a3b234e820e08699722569cc24e57d119a868854f70"
  }
}
```

---

## 5. Methodological Analysis & Scientific Design Options

### 5.1 Inadmissibility of Ad-Hoc Fixes
1. **Silent Downsampling Forbidden:** Reducing Irish English to 92, 78, or 0 would unbalance the 6-strata factorial design and distort the max-min disparity metric $\Delta_D = \max WER - \min WER$.
2. **Single-Accent Corpus Supplementation Forbidden:** Sourcing Irish English from an auxiliary corpus (e.g. EdAcc) while sourcing the other 5 strata from Common Voice 27 would introduce a fatal corpus-by-accent confound (acoustic recording conditions confounded with accent adaptation).
3. **Option B (N=468 / 78 per accent) Inadmissible:** The 78 historical Irish speakers have already been exposed in Cohort 2. Furthermore, 78 (Cohort 3) + 20 (Gate Panel) = 98 speakers, which still exceeds the 92 total eligible Irish speakers in CV27.

### 5.2 Recommended Path: Harmonized Multi-Corpus Crossed Design
To scientifically expand the speaker pool without corpus confounding, the study should adopt a **crossed multi-corpus sampling design** across **all six strata**:
- Every accent stratum is represented across multiple sources (e.g., Common Voice, EdAcc, VoxCeleb).
- Source contributions are balanced or statistically modeled.
- Acoustic and recording metadata are preserved and accounted for in the statistical model.
- Partition disjointness is maintained across all historical, development, gate, and confirmatory sets.
- Statistical power is re-evaluated for the exact v1.4 composite decision rule before protocol freezing.
