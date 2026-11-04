# Stage 6M v1.5 — Cohort 3 Controlled Audio Materialization Pilot Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_PILOT_MATERIALIZATION`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Controlled Materialization Pilot)  
> **GOVERNANCE DISPOSITION:** **PILOT_COMPLETE_AND_VERIFIED**  
> **PARENT PROVISIONAL MANIFEST:** [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) (SHA-256: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`)  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** 2026-11-04T08:08:01.269560+00:00  

---

## 1. Executive Summary

This report documents the preparation and execution of the **Controlled Audio Materialization Pilot** for **Cohort 3**:
- **Target Specification:** Exactly $75$ clips across $5$ unique speakers ($1$ speaker per confirmatory evaluation stratum $\times 15$ clips/speaker).
- **Stratum Representation:** Australian English, Canadian English, England English, South Asian English, US English.
- **Parent Manifest Traceability:** Deterministically derived from provisional manifest (SHA-256 `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`).
- **Current Progress:** **75 / 75** clips verified (100.00%).
- **Execution Gating:** Confirmatory GPU CTTA adaptation and model inference remain **STRICTLY BLOCKED**.

---

## 2. Quantitative Pilot Inventory

| Stratum | Speaker ID | Target Clips | Materialized | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Canadian English** | `00143475c51f0cc4...` | 15 | 15 | **PASS** |
| **Australian English** | `008f1e5e50d2af13...` | 15 | 15 | **PASS** |
| **US English** | `010465487d57bc20...` | 15 | 15 | **PASS** |
| **England English** | `016e15e58e2d93cb...` | 15 | 15 | **PASS** |
| **South Asian English** | `01c9ba7d35336856...` | 15 | 15 | **PASS** |
| **Grand Total** | **5 Speakers** | **75** | **75** | **PASS** |

---

## 3. Cryptographic Provenance & Ledgers

- **Pilot SHA-256 Ledger:** [`datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv)  
  - Ledger File SHA-256: `3afd649c41fa617a64f475a80781d00ffb17511b109b26c5a05c3062ee6e6359`
- **Pilot Speaker Completeness Report:** [`datasets/splits/stage6m_cohort3_pilot_speaker_completeness_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_speaker_completeness_report.json)
- **Pilot Failed Clips Report:** [`datasets/splits/stage6m_cohort3_pilot_failed_clips_report.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_failed_clips_report.json)
- **Parent Provisional Manifest:** [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) (SHA-256: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`)

---

## 4. Execution Gating & Next Operational Milestones

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: CONTROLLED PILOT AUTHORIZED                     ║
║                                                                                      ║
║  1. 75-clip pilot execution harness is authorized by Project-Lead (Sec 14.7).        ║
║  2. Pilot manifests and ledgers are distinct; full-cohort reports are untouched.     ║
║  3. Physical acquisition strictly confined to 5 speakers x 15 clips = 75 clips.      ║
║  4. Confirmatory GPU adaptation & model inference remain STRICTLY BLOCKED.           ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
