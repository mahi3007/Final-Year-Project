# Stage 6M Gate 3B: Final Manifest Lock Audit Report

**Report ID:** `STAGE6M-GATE3B-LOCK-AUDIT-20261107`  
**Generated At:** `2026-11-07T17:07:40.854400+00:00`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Authorizing Authority:** Project Lead (Dissertation Author) — APPROVED  
**Audit Verdict:** **PASSED AND LOCKED**

---

## 1. Executive Summary & Lock Milestone

Gate 3B — Final Manifest Validation and Lock has been executed and completed under **Policy 2A (Reconciled Target Population Admission)**. Candidate Manifest v3 has been promoted, sealed with `manifest_status = "LOCKED"`, and serialized to the official production path:

- **Official Manifest Path:** `datasets/splits/stage6m_cohort3_final_manifest.json`
- **Manifest Status:** `LOCKED`
- **Manifest File Size:** **`26,680,115` bytes**
- **Manifest SHA-256 Digest:** **`171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0`**
- **Total Records:** **`18,975`**
- **Total Speakers:** **`1,265`**

Per protocol requirements, the cryptographic digest was calculated **externally** after serializing the completed locked manifest with all final metadata and status flags. The manifest does not embed its own SHA-256 within itself, eliminating circular dependencies.

---

## 2. Candidate Manifest Lineage & Preservation

All three historical candidate manifest iterations have been permanently preserved in `scratch/candidate_manifest/`:

| Version | Artifact Filename | Size (Bytes) | SHA-256 Digest | Status & Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **v1** | `stage6m_cohort3_candidate_final_manifest_v1_legacy_claim_b.json` | 21,157,500 | `44747c12297a257bfeb7da496e34b8d1d04c44c595b3a639695ac293581bb117` | *Superseded:* Conflated Claim A (bitstream validity) with Claim B (origin completeness). |
| **v2** | `stage6m_cohort3_candidate_final_manifest_v2_unverified_boolean_only.json` | 24,989,315 | `718426757691c88b56e6371c425e6fbd1c757d9f42c648d1cc09d3182e84256e` | *Superseded:* Boolean `false` present but omitted explicit string status field. |
| **v3** | `stage6m_cohort3_candidate_final_manifest_v3_unverified_semantic_status.json` | 26,071,214 | `c09edaf82d62645293b51d70152b326008f42832a21fbdd765ef2218c4f0fb89` | **Promoted & Locked:** Full semantic decoupling of Claim A and Claim B. |

---

## 3. Scientific Invariants & Panel Partitioning Verification

Independent verification of `datasets/splits/stage6m_cohort3_final_manifest.json` confirms 100% adherence to the registered scientific design:

| Cohort Partition | Unique Speakers | Clips / Speaker | Total Clips | Stratum Allocation | Panel Overlap |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Confirmatory Evaluation** | 1,100 | 15 | 16,500 | 220 per stratum (Australia, Canada, England, South Asian, US) | **0** |
| **Gate-Reference Calibration** | 100 | 15 | 1,500 | 20 per stratum (Australia, Canada, England, South Asian, US) | **0** |
| **Australian Reserve Panel** | 65 | 15 | 975 | 65 Australian stratum (power-preserving contingency) | **0** |
| **Total Cohort 3 Inventory** | **1,265** | **15** | **18,975** | **Balanced across all five primary strata** | **0** |

### Per-Stratum Speaker Accounting
- **Australia (`australia`):** 220 evaluation + 20 gate-reference + 65 reserve = 305 speakers (4,575 clips)
- **Canada (`canada`):** 220 evaluation + 20 gate-reference = 240 speakers (3,600 clips)
- **England (`england`):** 220 evaluation + 20 gate-reference = 240 speakers (3,600 clips)
- **South Asian (`south_asian`):** 220 evaluation + 20 gate-reference = 240 speakers (3,600 clips)
- **United States (`us`):** 220 evaluation + 20 gate-reference = 240 speakers (3,600 clips)

---

## 4. Policy 2A Evidentiary Decoupling & Claim Verification

All 18,975 manifest records were audited for decoupled Claim A and Claim B fields:

```json
{
  "current_file_structural_validity_passed": true,
  "decoder_validation_passed": true,
  "source_origin_completeness_verified": false,
  "source_origin_completeness_status": "UNVERIFIED",
  "policy_2a_admitted": true
}
```

| Verification Dimension | Expected Records | Observed Records | Agreement Rate | Compliance Status |
| :--- | :---: | :---: | :---: | :---: |
| **Claim A:** Current-File Structural Validity | 18,975 | 18,975 | 100.0% | **PASSED** |
| **Claim A:** Three-Decoder Consensus Decodability | 18,975 | 18,975 | 100.0% | **PASSED** |
| **Claim B:** Source Origin Completeness Verified (`false`) | 18,975 | 18,975 | 100.0% | **PASSED** |
| **Claim B:** Source Origin Completeness Status (`UNVERIFIED`) | 18,975 | 18,975 | 100.0% | **PASSED** |
| **Policy 2A:** Admitted Population Status (`true`) | 18,975 | 18,975 | 100.0% | **PASSED** |
| **Accepted Recordings:** `ADMITTED_CLAIM_A_VALID_ORIGIN_UNVERIFIED` | 18,845 | 18,845 | 100.0% | **PASSED** |
| **Quarantined Recordings:** `ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY` | 130 | 130 | 100.0% | **PASSED** |

---

## 5. Physical Dataset & Ledger Reconciliation

| Inventory Invariant | Disposition Ledger | Physical Destination Audio | Manifest Records | Verification Result |
| :--- | :---: | :---: | :---: | :---: |
| **Total Audio Files** | 18,975 | 18,975 | 18,975 | **100% Exact Match** |
| **Total Audio Bytes** | 709,750,958 | 709,750,958 | 709,750,958 | **100% Exact Match** |
| **Zero-Byte Files** | 0 | 0 | 0 | **0 Zero-Byte Files** |
| **SHA-256 Agreement** | 100% | 100% | 100% | **0 Hash Mismatches** |
| **Provisional Manifest** | Unchanged | Unchanged | Clean git status | **Intact (17,744,805 B)** |

- **Disposition Ledger Path:** `datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv`
- **Disposition Ledger SHA-256:** `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5`
- **Provisional Manifest SHA-256:** `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`

---

## 6. Strict Governance Boundaries & Next Milestone

1. **Gate 3B Completion:** The official manifest is locked and independently verified.
2. **Confirmatory Shielding:** Confirmatory evaluation cohort (1,100 speakers / 16,500 clips) remains strictly sealed.
3. **GPU Experiments Blocked:** Gates 4, 5, and 6 remain blocked until explicit Project Lead authorization.
4. **Git Workspace Guard:** No automated git staging, commit, or push operations were performed.

*Audit completed in 3.97 seconds.*
