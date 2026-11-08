# Stage 6M: Confirmatory Transcript Isolation Audit Report

**Report ID:** `STAGE6M-TRANSCRIPT-ISOLATION-AUDIT-20261107`  
**Generated At:** `2026-11-07T17:48:05.025934+00:00`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Parent Locked Manifest SHA-256:** `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0`  
**Audit Verdict:** **ZERO LABEL EXPOSURE CONFIRMED**

---

## 1. Architectural Motivation & Isolation Architecture

To guarantee strict scientific blinding and eliminate any risk of accidental data leakage or experimenter bias during the streaming adaptation benchmark, the Stage 6M dataset components have been cryptographically and physically partitioned into two decoupled artifacts:

```
Official Locked Manifest (Parent)
SHA-256: 171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0
├── 1. Restricted Online Manifest (for Streaming Adaptation Runner)
│   Path: datasets/splits/stage6m_cohort3_online_inference_manifest.json
│   SHA-256: 0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1
│   ├── 16,500 Evaluation Clips: Transcripts = null (Strictly Shielded)
│   ├──  1,500 Gate-Reference Clips: Transcripts = Active (Required by DSG Sentinel Gate)
│   └──    975 Australian Reserve Clips: Transcripts = null (Sealed)
│
└── 2. Sealed Evaluation Transcripts Key (Reserved for Gate 6 Offline Scoring)
    Path: datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json
    SHA-256: f427ae7fbf386f77b0795cc1fa33b2f7831c89f89ecfce7fa30036cde5c5223e
    └── 17,475 Total Sealed Reference Transcripts (16,500 Evaluation + 975 Reserve)
```

---

## 2. Invariant & Leakage Audit Matrix

| Verification Dimension | Expected State | Audited State | Result |
| :--- | :--- | :--- | :---: |
| **Parent Locked Manifest Integrity** | SHA-256 == `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` | Match verified | **PASSED** |
| **Evaluation Records in Online Manifest** | 16,500 clips with `transcript == null` | 16,500 / 16,500 nullified | **PASSED** |
| **Evaluation Transcript Leakage** | 0 evaluation records with text | **0 records leaked** | **PASSED** |
| **Gate-Reference Sentinel Transcripts** | 1,500 clips with non-empty text | 1,500 / 1,500 active | **PASSED** |
| **Reserve Records in Online Manifest** | 975 clips with `transcript == null` | 975 / 975 nullified | **PASSED** |
| **Total Records in Online Manifest** | 18,975 records | 18,975 records | **PASSED** |
| **Sealed Scoring Key Completeness** | 16,500 eval + 975 reserve = 17,475 | 17,475 entries | **PASSED** |
| **Zero Panel Overlap** | 0 shared speakers | 0 shared speakers | **PASSED** |

---

## 3. Operational Protocols for Online Runner

1. The online runner (`cloud/kaggle/run_stage6m_cohort3_kaggle_benchmark.py`) loads **only** `stage6m_cohort3_online_inference_manifest.json`.
2. The online runner cannot read evaluation reference transcripts because the field is `null`.
3. Prequential streaming predictions are logged directly to `/kaggle/working/prequential_stream_records.jsonl`.
4. Only upon completion of all 4,125 streaming windows and transition to Gate 6 is the offline scoring key (`stage6m_cohort3_sealed_evaluation_transcripts.json`) ingested to evaluate Word Error Rates and conduct the registered simultaneous statistical inference.

*Audit completed in 2.11 seconds.*
