# Stage 6M Gate 3B Pre-Lock Independent Audit Report (v2 Corrected)

**Report ID:** `STAGE6M-GATE3B-PRELOCK-AUDIT-20261107-V3`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch / Base Commit:** `stage6m-five-stratum-parity` @ [`baee3b8`](https://github.com/mahi3007/Final-Year-Project/commit/baee3b8381389ffde38e907dc137623748c254a8)  
**Governance Status:** **GATE 3B PRE-LOCK READ-ONLY AUDIT COMPLETE (AWAITING GATE 3B AUTHORIZATION)**  
**Audit Timestamp:** `2026-11-07T16:55:55.229607+00:00`  
**Audit Duration:** `18.42 seconds`  

---

## 1. Executive Summary

In preparation for the Gate 3B manifest-locking decision, an independent, read-only forensic audit was performed across the physically materialized Stage 6M Cohort 3 research dataset (`datasets/audio/stage6m/cohort3_reconciled_assets/`).

All **12 independent audit criteria** specified by the Project Lead have **PASSED WITH ZERO DISCREPANCIES**.

Following evidentiary review by the Project Lead, the candidate manifest's Claim B metadata was semantically reconciled to maintain strict concordance with **Policy 2A**: original-source completeness relative to uncompressed master captures is recorded as `source_origin_completeness_verified = false` and `source_origin_completeness_status = "UNVERIFIED"` for **all 18,975 recordings**, decoupling current-file structural/decoder validity (Claim A) from uncompressed master completeness (Claim B). Original-source completeness is formally documented as unverified due to the unavailability of upstream master recordings, rather than falsely asserted as verified or erroneously characterized as proven incomplete.

The corrected candidate manifest (v3) is isolated at `scratch/candidate_manifest/stage6m_cohort3_candidate_final_manifest.json`. The official production manifest (`datasets/splits/stage6m_cohort3_final_manifest.json`) **does NOT exist on disk** and remains strictly blocked pending explicit Gate 3B authorization.

---

## 2. Policy 2A Claim B Evidentiary Traceability Matrix

| Evidentiary Dimension | Manifest Field Name | Accepted Clips (18,845) | Quarantined Clips (130) | Full Population (18,975) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Claim A: File Structure** | `current_file_structural_validity_passed` | `True` (18,845) | `True` (130) | `True` (18,975) | **PASSED** |
| **Claim A: PCM Decoding** | `decoder_validation_passed` | `True` (18,845) | `True` (130) | `True` (18,975) | **PASSED** |
| **Claim B: Origin Master Verification** | `source_origin_completeness_verified` | `False` (18,845) | `False` (130) | `False` (18,975) | **PASSED** |
| **Claim B: Origin Master Status** | `source_origin_completeness_status` | `"UNVERIFIED"` (18,845) | `"UNVERIFIED"` (130) | `"UNVERIFIED"` (18,975) | **PASSED** |
| **Duration Discrepancy** | `duration_estimation_discrepancy` | `False` (18,845) | `True` (130) | Mixed (130 True) | **PASSED** |
| **Policy 2A Admission** | `policy_2a_admitted` | `True` (18,845) | `True` (130) | `True` (18,975) | **PASSED** |
| **Admission Disposition** | `admission_disposition` | `ADMITTED_CLAIM_A_VALID_ORIGIN_UNVERIFIED` | `ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY` | 100% Policy 2A | **PASSED** |

---

## 3. Candidate Final Manifest Provenance & Version Tracking

| Manifest Version | Isolated Location | File Size | SHA-256 Digest | Status |
| :--- | :--- | :---: | :--- | :--- |
| **v1 (Legacy Claim B)** | `scratch/candidate_manifest/..._v1_legacy_claim_b.json` | 21,157,500 B | `44747c12297a257bfeb7da496e34b8d1d04c44c595b3a639695ac293581bb117` | Preserved Archive |
| **v2 (Boolean-Only)** | `scratch/candidate_manifest/..._v2_unverified_boolean_only.json` | 24,989,315 B | `718426757691c88b56e6371c425e6fbd1c757d9f42c648d1cc09d3182e84256e` | Preserved Archive |
| **v3 (Semantically Reconciled)** | `scratch/candidate_manifest/..._candidate_final_manifest.json` | 26,071,214 B | `c09edaf82d62645293b51d70152b326008f42832a21fbdd765ef2218c4f0fb89` | **Active Review Candidate** |
| **Production Target** | `datasets/splits/stage6m_cohort3_final_manifest.json` | 0 B | *None (File does NOT exist)* | **STRICTLY BLOCKED** |

---

## 4. Twelve-Point Audit Verification Matrix

| # | Audit Criterion | Expected Standard | Observed Finding | Status |
| :-: | :--- | :--- | :--- | :-: |
| **1** | **Destination Asset Accounting** | 18,975 files, 709,750,958 bytes | 18,975 files, 709,750,958 bytes (0 zero-byte) | **PASSED** |
| **2** | **Source-to-Destination SHA-256** | 100% agreement, 0 mismatches | 18,975 / 18,975 matching digests (0 mismatches) | **PASSED** |
| **3** | **File Object (st_ino) Independence** | 0 destination files share inode with source | 0 / 18,975 shared inodes (100% distinct file objects) | **PASSED** |
| **4** | **Three-Decoder Consensus** | 100% decodability across 3 backends | SoundFile: 18,975, PyAV: 18,975, miniaudio: 18,975 | **PASSED** |
| **5** | **Disposition Ledger Integrity** | 18,975 records, all PASS, zero errors | 18,975 rows, 0 errors, SHA-256 `b242282ef1586219...` | **PASSED** |
| **6** | **Unique Speaker Accounting** | 1,265 speakers, exactly 15 clips each | 1,265 unique speakers, 0 non-15 speakers | **PASSED** |
| **7** | **Evaluation Strata Balance** | Exactly 220 speakers per stratum (5 strata) | Australia: 220, Canada: 220, England: 220, India: 220, US: 220 | **PASSED** |
| **8** | **Gate Calibration Panel** | 100 separate speakers (20 per stratum) | Australia: 20, Canada: 20, England: 20, India: 20, US: 20 | **PASSED** |
| **9** | **Australian Reserve Panel** | 65 separate Australian speakers | Australia: 65 reserve speakers (975 clips) | **PASSED** |
| **10** | **Panel Disjointness & Separation** | Zero overlap across panels | Eval ∩ Gate: 0, Eval ∩ Reserve: 0, Gate ∩ Reserve: 0 | **PASSED** |
| **11** | **Executing Materializer Provenance** | `0cacb4a1f26aa73a78a545e9045210fbd9e5d465b7fc414e78e557ccb9e75dfa` | Matched: `0cacb4a1f26aa73a78a545e9045210fbd9e5d465b7fc414e78e557ccb9e75dfa` (42,528 bytes) | **PASSED** |
| **12** | **Provisional Manifest Immutability** | Byte-identical, clean git tree | Clean: True, SHA-256: `b9a03e2ab1304315...` | **PASSED** |

---

## 5. Protected Boundaries Strictly Preserved

- **Official Manifest Not Published:** `datasets/splits/stage6m_cohort3_final_manifest.json` does NOT exist on disk.
- **Original Audio Untouched:** `cohort3_audio` (18,845 files) and `cohort3_rejected_quarantine` (130 files) are 100% intact.
- **Materialized Destination Untouched:** 18,975 files (709,750,958 bytes) in `cohort3_reconciled_assets/`.
- **Provisional Manifest Untouched:** `stage6m_cohort3_provisional_manifest.json` remains identical to base commit.
- **GPU Inference & Adaptation Blocked:** Gates 4, 5, and 6 remain unexecuted.
- **Git Tree Clean of Automated Commits:** Zero commits or pushes.

---

## 6. Next Steps: Awaiting Gate 3B Authorization

The semantic reconciliation and pre-lock audit are complete and independently confirmed. All prerequisites for **Gate 3B (Final Manifest Validation and Lock)** have been met.

The semantically reconciled candidate manifest v3 (`c09edaf82d62645293b51d70152b326008f42832a21fbdd765ef2218c4f0fb89`) is ready in `scratch/candidate_manifest/`. Upon receiving explicit Gate 3B authorization, the official manifest will be generated, validated, cryptographically hashed, and locked at `datasets/splits/stage6m_cohort3_final_manifest.json`.
