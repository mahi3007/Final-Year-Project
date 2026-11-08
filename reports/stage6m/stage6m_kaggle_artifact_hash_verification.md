# Stage 6M: Kaggle Artifact Hash Verification Report

**Catalogue ID:** `STAGE6M-KAGGLE-HASH-CATALOGUE-20261107`  
**Generated At:** `2026-11-07T17:59:01.035548+00:00`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Verification Verdict:** **ALL ASSETS VERIFIED EXACT**

---

## 1. Frozen Benchmark Verification Summary

| Component | Path | File Size | SHA-256 Digest | Status |
| :--- | :--- | :---: | :--- | :---: |
| **Official Locked Manifest** | `datasets/splits/stage6m_cohort3_final_manifest.json` | 26,680,115 B | `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` | **VERIFIED** |
| **Disposition Ledger** | `datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv` | 8,637,604 B | `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5` | **VERIFIED** |
| **Requirements Lock** | `requirements-kaggle.txt` | 1,379 B | `53b85af593eacd0645302c3d3293c46924d8cee50bb72a7b6435c4f12e7a7e02` | **VERIFIED** |
| **Physical Audio Assets** | `datasets/audio/stage6m/cohort3_reconciled_assets/*.mp3` | 709,750,958 B | 18,975 / 18,975 verified | **VERIFIED** |

---

## 2. Configuration Artifacts

| Configuration File | Bytes | SHA-256 Digest | Role in Stage 6M |
| :--- | :---: | :--- | :--- |
| `model_role_registry.json` | 8,575 | `a276bfb8b517fd20dac163b3b3cd2b6d16bbfaf44808d708f54c82842cd8ce2f` | Configuration specification |
| `stage4_thresholds.json` | 1,157 | `ed9f31a2c0076a01ec5e6f47d578a2eaadc15977c954897b30f9e71ac92a1853` | Configuration specification |
| `stage5_gate_config.json` | 1,293 | `e5833c4fe22d4683faa67b8e108ea9d497b16aa37995f6bd5e79a69198a48088` | Configuration specification |
| `stage6m_model_registry.json` | 5,629 | `7bde510f5b517acb4890468dd4e581e03ce3299564b020d51e2ca86455647cca` | Configuration specification |
| `stage6m_protocol_config.json` | 9,430 | `8f4654413ef6596a5857d5fc1f7acdceccb3c3d795efe32d51f05f72fe206616` | Configuration specification |

---

## 3. Kaggle Deployment Package Verification

All frozen artifacts match their registered cryptographic digests. These artifacts form the exact payload required for creating the private Kaggle dataset (`stage6m-frozen-benchmark`).

*Verification completed in 2.38 seconds.*
