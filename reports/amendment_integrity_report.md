# Amendment & Historical Freeze Integrity Report
**Protocol Version:** `v1.1.0-model-expansion`  
**Execution Phase:** Phase 1 (Historical Freeze & Amendment Integrity)  
**Verification Status:** **100% BIT-FOR-BIT MATCH VERIFIED**  
**Audit Timestamp:** 2026-10-08T17:00:05.233161+00:00  

---

## 1. Executive Summary

In accordance with Phase 1 mandates, all 37 historical artifacts from Protocol `v1.0.0-canonical` (Stages 2–5) and `v1.0-cv27-amended` (Historical Stage 6) were audited against the authoritative cryptographic manifest. Zero discrepancies, zero missing files, and zero hash drifts were observed.

```
Total Historical Files Hashed: 37
Bit-for-Bit Hash Matches:      37 / 37 (100.0%)
Modified or Missing Files:     0
Historical Invariant Status:   COMPLETELY IMMUTABLE AND LOCKED
```

---

## 2. Directory & Namespacing Isolation

To guarantee that upcoming amended multi-model experiments do not overwrite or contaminate historical data, strict file-system partitioning is enforced:

| Subsystem / Stage | Historical Storage (v1.0.0 / v1.0-cv27) | Amended Storage (v1.1.0-model-expansion) | Isolation Policy |
|---|---|---|---|
| **Stage 2 Baseline** | `reports/stage2_final_report.md` | `reports/stage2_final_report.md` (Read-only ref) | STRICT READ-ONLY |
| **Stage 3 Discovery** | `reports/ctta/` (Wav2Vec2 only) | `results/stage3_multimodel/`, `reports/stage3_multimodel_extension.md` | DEDICATED NEW PATH |
| **Stage 4 Stress** | `reports/stage4/` (Wav2Vec2 only) | `results/stage4_multimodel/`, `reports/stage4_multimodel_extension.md` | DEDICATED NEW PATH |
| **Stage 5 DSG Gate** | `reports/stage5/` (Wav2Vec2 only) | `results/stage5_multimodel/`, `reports/stage5_multimodel_qualification.md` | DEDICATED NEW PATH |
| **Stage 6 Validation**| `reports/stage6/` (Historical run) | `results/stage6_multimodel/`, `reports/stage6_multimodel_final_validation.md` | DEDICATED NEW PATH |
| **Model Registry** | Hardcoded configs | `configs/model_role_registry.json` | CANONICAL SINGLE SOURCE |
| **Experiment IDs** | `EXP_STAGE3_*`, `EXP_STAGE4_*` | `EXP_v1.1.0_STAGE3M_*`, `EXP_v1.1.0_STAGE4M_*`, etc. | EXPLICIT NAMESPACING |

---

## 3. Cryptographically Verified Artifact Register (37 Items)

| Stage | Relative Path | Size (Bytes) | SHA-256 (First 12 chars) | Status |
|---|---|---|---|:---:|
| `stage2` | `reports/stage2_final_report.md` | 23,144 | `ea6d321aaa5a...` | **VERIFIED** |
| `stage2` | `reports/stage2_final_report.pdf` | 945,774 | `c97fbb82e3bc...` | **VERIFIED** |
| `stage2` | `reports/split_report.json` | 1,907 | `87b954f0b99c...` | **VERIFIED** |
| `configs` | `configs/default_config.yaml` | 1,461 | `1756fef13f12...` | **VERIFIED** |
| `configs` | `configs/stage4_thresholds.json` | 1,157 | `ed9f31a2c007...` | **VERIFIED** |
| `configs` | `configs/stage5_gate_config.json` | 1,293 | `e5833c4fe22d...` | **VERIFIED** |
| `stage3` | `reports/ctta/multi_order_all_methods.csv` | 2,035 | `c123b2f2c098...` | **VERIFIED** |
| `stage3` | `reports/ctta/cross_method_comparison.csv` | 969 | `33798f7ce810...` | **VERIFIED** |
| `stage3` | `reports/ctta/bootstrap_uncertainty.csv` | 2,181 | `0db78541a385...` | **VERIFIED** |
| `stage3` | `reports/ctta/discovery_findings.json` | 7,771 | `564c5a8da506...` | **VERIFIED** |
| `stage3` | `reports/ctta/suta/summary.json` | 739 | `cdde7faaefb9...` | **VERIFIED** |
| `stage3` | `reports/ctta/suta/group_metrics.csv` | 553 | `026243c22deb...` | **VERIFIED** |
| `stage3` | `reports/ctta/suta/experiment_manifest.json` | 888 | `4ed5dc019e0e...` | **VERIFIED** |
| `stage3` | `reports/ctta/no_adapt/summary.json` | 745 | `42ef016c46c2...` | **VERIFIED** |
| `stage3` | `reports/ctta/dsuta/summary.json` | 741 | `30ab0fcd6683...` | **VERIFIED** |
| `stage3` | `reports/ctta/dmsuta/summary.json` | 743 | `99685c53e591...` | **VERIFIED** |
| `stage3` | `reports/stage3_discovery_report.md` | 21,362 | `7cb8701bb713...` | **VERIFIED** |
| `stage4` | `reports/stage4/stage4d_multi_order_matrix.csv` | 2,029 | `f72b514a70c9...` | **VERIFIED** |
| `stage4` | `reports/stage4/stage4e_acoustic_stress_matrix.csv` | 3,237 | `b490aeaf949a...` | **VERIFIED** |
| `stage4` | `reports/stage4/stage4d_speaker_cluster_bootstrap.csv` | 1,579 | `41e2e7d6fc45...` | **VERIFIED** |
| `stage4` | `reports/stage4/stage4e_stress_speaker_cluster_bootstrap.csv` | 2,592 | `d0447631fc4b...` | **VERIFIED** |
| `stage4` | `reports/stage4/stage4g_boundary_condition_map.csv` | 2,792 | `6e6739778096...` | **VERIFIED** |
| `stage4` | `reports/stage4/dsg_go_no_go_decision.json` | 2,878 | `82645c8e2b93...` | **VERIFIED** |
| `stage4` | `reports/stage4_characterization_report.md` | 31,973 | `5127160426f3...` | **VERIFIED** |
| `baseline` | `reports/baseline/wav2vec2_base/wav2vec2_base_final_test_summary.json` | 2,409 | `46192324103e...` | **VERIFIED** |
| `baseline` | `reports/baseline/wav2vec2_base/wav2vec2_base_final_test_predictions.csv` | 13,501 | `65113c71a428...` | **VERIFIED** |
| `stage6` | `reports/stage6/six_model_benchmark.csv` | 1,260 | `52ab71a7d9eb...` | **VERIFIED** |
| `stage6` | `reports/stage6/eight_model_benchmark.csv` | 1,686 | `3e4567e4d6c6...` | **VERIFIED** |
| `stage6` | `reports/stage6/model_compatibility_manifest.json` | 2,766 | `cf5b2ff3b1f8...` | **VERIFIED** |
| `stage6` | `reports/stage6/six_model_dsg_summary.csv` | 837 | `518b58b29ebd...` | **VERIFIED** |
| `stage6` | `reports/stage6/eight_model_dsg_summary.csv` | 1,113 | `9301349ddba7...` | **VERIFIED** |
| `stage6` | `reports/stage6/six_model_group_metrics.csv` | 12,990 | `490a32df747a...` | **VERIFIED** |
| `stage6` | `reports/stage6/eight_model_group_metrics.csv` | 19,592 | `3dbb39f1570d...` | **VERIFIED** |
| `stage5` | `reports/stage5/dsg_decision_log.csv` | 43,070 | `2548d00eb724...` | **VERIFIED** |
| `stage5` | `reports/stage5/final_external_metrics.csv` | 739 | `a76bfc4efbfa...` | **VERIFIED** |
| `stage5` | `reports/stage5/final_reproducibility_manifest.json` | 56,567 | `b863bb26aa33...` | **VERIFIED** |
| `stage5` | `reports/stage5/predecessor_persistence.csv` | 2,793 | `bc4755f6338a...` | **VERIFIED** |

---

## 4. Historical Configuration Invariance

- **Calibration Thresholds:** `configs/stage4_thresholds.json` has SHA-256 `ed9f31a2...`, freezing $\delta_G = 0.0200, \delta_D = 0.0200$.
- **Gate Tolerances:** `configs/stage5_gate_config.json` has SHA-256 `e5833c4f...`, freezing $\epsilon_R = 0.0000, \epsilon_G = 0.0200, \epsilon_D = 0.0200$, $B=1,000, \text{confidence}=0.95$.
- **Dataset Partition Locks:** Both `datasets/splits/stage5_external_eval.lock.json` and `stage5_sentinel_panel.lock.json` remain pristine.

---

## 5. Phase 1 Sign-Off Verdict

- **Integrity Rule 1 (Old reports unchanged):** PASS
- **Integrity Rule 2 (Old CSVs unchanged):** PASS
- **Integrity Rule 3 (Old configs unchanged):** PASS
- **Integrity Rule 4 (Old hashes identical):** PASS
- **Integrity Rule 5 (New outputs quarantined):** PASS

**PHASE 1 VERDICT: PASS & LOCKED**
