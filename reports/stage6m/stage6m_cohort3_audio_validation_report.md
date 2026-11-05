# Stage 6M v1.5 — Cohort 3 Audio Post-Acquisition Validation Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_AUDIO_VALIDATION_REPORT`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Parity  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Post-Acquisition Independent Hash Validation)  
> **VERDICT:** **FAIL_BASELINE_LEDGER_INVALID**  
> **BASELINE LEDGER:** [`datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv) (SHA-256: `eda8bbe236bac0360d055a7616d5ee5d666119317c4c95a271e994d793fde08c`)  
> **DESTINATION DIRECTORY:** `datasets/external/common_voice_27/cohort3_audio`  
> **TIMESTAMP (UTC):** 2026-11-05T06:22:48.677260+00:00  

---

## 1. Summary of Recalculated Hash Comparison

| Metric | Count | Expected | Status |
| :--- | :---: | :---: | :---: |
| Target Expected Clips | 18,975 | 18,975 | - |
| Ledger Structural Discrepancies | 2 | 0 | FAIL |
| Verified Matching Hashes | 18,845 | 18,975 | FAIL |
| Missing Files | 130 | 0 | FAIL |
| Corrupt / Undecodable Files | 0 | 0 | PASS |
| SHA-256 Hash Mismatches | 0 | 0 | PASS |
| Unexpected Files in Destination | 0 | 0 | PASS |
| **Total Discrepancies** | **132** | **0** | **FAIL_BASELINE_LEDGER_INVALID** |

---

## 2. Integrity Verification Findings

### Ledger Structural Discrepancies (2)
- **[total_ledger_rows]**: Baseline ledger row count 18845 does not match expected 18975
- **[unique_recording_ids]**: Baseline ledger contains 18845 unique recording IDs (expected 18975)
### Missing Files (130)
- `common_voice_en_25321355.mp3` (common_voice_en_25321355): File does not exist on disk
- `common_voice_en_21637126.mp3` (common_voice_en_21637126): File does not exist on disk
- `common_voice_en_25321376.mp3` (common_voice_en_25321376): File does not exist on disk
- `common_voice_en_21636368.mp3` (common_voice_en_21636368): File does not exist on disk
- `common_voice_en_21636374.mp3` (common_voice_en_21636374): File does not exist on disk
- `common_voice_en_21638164.mp3` (common_voice_en_21638164): File does not exist on disk
- `common_voice_en_25074415.mp3` (common_voice_en_25074415): File does not exist on disk
- `common_voice_en_25757742.mp3` (common_voice_en_25757742): File does not exist on disk
- `common_voice_en_25381658.mp3` (common_voice_en_25381658): File does not exist on disk
- `common_voice_en_25526479.mp3` (common_voice_en_25526479): File does not exist on disk
- ... and 120 more missing files.
