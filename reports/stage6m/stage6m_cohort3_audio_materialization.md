# Stage 6M v1.5 — Cohort 3 Audio Materialization & Integrity Validation Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_AUDIO_MATERIALIZATION`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **GOVERNANCE DISPOSITION:** **IN_PROGRESS_CONTROLLED_PIPELINE**  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** 2026-11-05T06:12:19.410472+00:00  

---

## 1. Executive Summary

This report documents the physical audio materialization and cryptographic integrity validation for **Cohort 3**:
- **Target Specification:** Exactly $18,975$ clips across $1,265$ unique speakers ($15$ clips/speaker) selected from Mozilla Common Voice 27.0.
- **Materialization Pipeline:** Controlled, deterministic pipeline with soundfile decodability verification, non-zero duration checks, and bitwise SHA-256 cryptographic hashing.
- **Current Progress:** **18,845 / 18,975** clips verified (99.31%).
- **Execution Gating:** Model adaptation and confirmatory inference remain **STRICTLY BLOCKED** under a separate execution-readiness decision.

---

## 2. Quantitative Materialization Inventory

| Metric | Target Requirement | Current Materialized | Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluation Clips** | 16,500 ($1,100 \times 15$) | 16,370 | **TRACKED** |
| **Gate-Reference Clips** | 1,500 ($100 \times 15$) | 1,500 | **TRACKED** |
| **Australian Reserve Clips** | 975 ($65 \times 15$) | 975 | **TRACKED** |
| **Grand Total Audio Clips** | **18,975** | **18,845** | **99.31%** |
| **Complete Speakers ($\\ge 15$ valid clips)** | 1,265 | 1,252 / 1,265 (Incomplete: 13) | **IN_PROGRESS** |
| **Failed / Corrupt Clips** | 0 allowed | 130 | **INVESTIGATE** |
| **Total Physical Audio Duration** | — | 94150.68 s (26.15 h) | **NOMINAL** |
| **Total Physical Audio Bytes** | — | 704,970,734 bytes (672.31 MB) | **NOMINAL** |

---

## 3. Cryptographic Provenance & Ledgers

- **Per-Clip SHA-256 Ledger:** [`datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv)  
  - Ledger File SHA-256: `eda8bbe236bac0360d055a7616d5ee5d666119317c4c95a271e994d793fde08c`
- **Failed Clips Ledger:** [`datasets/splits/stage6m_cohort3_failed_clips_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_failed_clips_report.json)
- **Speaker Completeness Report:** [`datasets/splits/stage6m_cohort3_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_speaker_completeness_report.json)

---

## 4. Execution Gating & Next Operational Milestones

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: AUTHORIZED (DATA PREPARATION)                   ║
║                                                                                      ║
║  1. Materialization pipeline and integrity validator are fully operational.          ║
║  2. Manifest remains explicitly UNLOCKED / PROVISIONAL.                              ║
║  3. Final manifest locking is CONDITIONAL upon 100% verified materialization.        ║
║  4. Confirmatory GPU adaptation & model inference remain STRICTLY BLOCKED.           ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
