# Stage 6M v1.5 — Task 7.7.1 Quarantine Retrieval Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_TASK771_QUARANTINE_RETRIEVAL`  
> **TASK ID:** `TASK_7_7_1`  
> **GOVERNING STANDARD:** Protocol Section 14.7 (*Project-Lead Academic Authorization*)  
> **STATUS:** **QUARANTINE_RETRIEVAL_PARTIAL**  
> **QUARANTINE LEDGER:** [`datasets/splits/stage6m_cohort3_quarantine_ledger.csv`](file:///C:\Users\venka\Downloads\final year project main\datasets\splits\stage6m_cohort3_quarantine_ledger.csv) (SHA-256: `4a7b24340a535a59ab59420096e070c24e62715fda31220d584e18ece7393fc9`)  
> **TIMESTAMP (UTC):** 2026-11-05T07:04:05.825232+00:00  

---

## 1. Summary of Recovered Diagnostic Audio

| Metric | Value | Required Target | Status |
| :--- | :---: | :---: | :---: |
| Quarantine Targets | 130 | 130 | - |
| Recovered Original Recordings | 0 | 130 | INCOMPLETE |
| Unique Incomplete Speakers | 0 | 13 | INCOMPLETE |
| Missing Targets | 130 | 0 | FAIL |
| Compressed Bytes Consumed | 0 B | - | - |
| Tar Members Scanned | 0 | - | - |
| Early Stream Termination | False | True | - |

### Strata Breakdown
| Stratum | Target Files | Recovered Files | Status |
| :--- | :---: | :---: | :---: |

---

## 2. Quarantine Governance Invariants

- **Zero Deletion Policy**: All 130 recovered bitstreams preserved exactly as extracted.
- **Strict Isolation**: Quarantined files reside exclusively in `cohort3_rejected_quarantine` and are barred from promotion to Cohort 3.
- **Preservation**: The 18,845 valid physical recordings and partial-acquisition ledger remain untouched.

