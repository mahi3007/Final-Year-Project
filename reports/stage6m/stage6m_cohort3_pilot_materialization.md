# Stage 6M v1.5 — Cohort 3 Controlled Audio Materialization Pilot Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_PILOT_MATERIALIZATION`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Controlled Materialization Pilot)  
> **GOVERNANCE DISPOSITION:** **PILOT_IN_PROGRESS**  
> **PARENT PROVISIONAL MANIFEST:** [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) (SHA-256: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`)  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** 2026-11-03T05:52:23.893953+00:00  

---

## 1. Executive Summary

This report documents the preparation and execution of the **Controlled Audio Materialization Pilot** for **Cohort 3**:
- **Target Specification:** Exactly $75$ clips across $5$ unique speakers ($1$ speaker per confirmatory evaluation stratum $\times 15$ clips/speaker).
- **Stratum Representation:** Australian English, Canadian English, England English, South Asian English, US English.
- **Parent Manifest Traceability:** Deterministically derived from provisional manifest (SHA-256 `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`).
- **Current Progress:** **30 / 75** clips verified (40.00%).
- **Execution Gating:** Confirmatory GPU CTTA adaptation and model inference remain **STRICTLY BLOCKED**.

---

## 2. Quantitative Pilot Inventory

| Stratum | Speaker ID | Target Clips | Materialized | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Canadian English** | `00143475c51f0cc4...` | 15 | 0 | **INCOMPLETE** |
| **Australian English** | `008f1e5e50d2af13...` | 15 | 15 | **PASS** |
| **US English** | `010465487d57bc20...` | 15 | 0 | **INCOMPLETE** |
| **England English** | `016e15e58e2d93cb...` | 15 | 0 | **INCOMPLETE** |
| **South Asian English** | `01c9ba7d35336856...` | 15 | 15 | **PASS** |
| **Grand Total** | **5 Speakers** | **75** | **30** | **IN_PROGRESS** |

---

## 3. Cryptographic Provenance & Ledgers

- **Pilot SHA-256 Ledger:** [`datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_pilot_clip_sha256_ledger.csv)  
  - Ledger File SHA-256: `1df451ff966e916105fbe571ebdc4cb02d07e35f207a8eecd620c0bd273c0fe2`
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
