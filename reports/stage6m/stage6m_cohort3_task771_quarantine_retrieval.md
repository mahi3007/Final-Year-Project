# Stage 6M v1.5 — Task 7.7.1 Quarantine Retrieval Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_TASK771_QUARANTINE_RETRIEVAL`  
> **TASK ID:** `TASK_7_7_1`  
> **GOVERNING STANDARD:** Protocol Section 14.7 (*Project-Lead Academic Authorization*)  
> **STATUS:** **QUARANTINE_RETRIEVAL_COMPLETE**  
> **QUARANTINE LEDGER:** [`datasets/splits/stage6m_cohort3_quarantine_ledger.csv`](file:///C:\Users\venka\Downloads\final year project main\datasets\splits\stage6m_cohort3_quarantine_ledger.csv) (SHA-256: `4cdf48e008d0cd74e280d587d60e4021bea2c9e48b914b81e486cb16fb2314ce`)  
> **TIMESTAMP (UTC):** 2026-11-05T20:24:17.828717+00:00  

---

## 1. Summary of Recovered Diagnostic Audio

| Metric | Value | Required Target | Status |
| :--- | :---: | :---: | :---: |
| Quarantine Targets | 130 | 130 | - |
| Recovered Original Recordings | 130 | 130 | PASS |
| Unique Incomplete Speakers | 13 | 13 | PASS |
| Missing Targets | 0 | 0 | PASS |
| Compressed Bytes Consumed | 71,016,615,616 B | - | - |
| Tar Members Scanned | 1,889,282 | - | - |
| Early Stream Termination | True | True | - |

### Strata Breakdown
| Stratum | Target Files | Recovered Files | Status |
| :--- | :---: | :---: | :---: |
| Australian English | 16 | 16 | PASS |
| Canadian English | 73 | 73 | PASS |
| England English | 8 | 8 | PASS |
| US English | 33 | 33 | PASS |

---

## 2. Quarantine Governance Invariants

- **Zero Deletion Policy**: All 130 recovered bitstreams preserved exactly as extracted.
- **Strict Isolation**: Quarantined files reside exclusively in `cohort3_rejected_quarantine` and are barred from promotion to Cohort 3.
- **Preservation**: The 18,845 valid physical recordings and partial-acquisition ledger remain untouched.

