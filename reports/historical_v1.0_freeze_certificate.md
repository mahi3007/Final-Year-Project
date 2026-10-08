# Historical v1.0.0-canonical Freeze Certificate
Phase 1 - Historical Artifact Freeze Verification
Protocol amendment: v1.1.0-model-expansion
Generated: 2026-10-08T20:37:00+05:30

## 1. Git State

| Item | Value |
|---|---|
| Branch | main |
| HEAD commit | 15404a1 |
| Working tree | Clean - zero staged changes |
| Remote sync | origin/main == HEAD |
| git diff HEAD | Empty |

## 2. SHA-256 Manifest

Total immutable files hashed: 37
Missing files: 0
Manifest path: manifests/historical_v1.0_artifact_manifest.json

## 3. Stage 2 Numerical Verification (source: reports/stage2_final_report.md lines 106-112)

| Model | WER Expected | WER Found | D Expected | D Found | PASS |
|---|---|---|---|---|---|
| wav2vec2_base | 85.51% | 85.51% | 20.65% | 20.65% | PASS |
| whisper_base | 90.40% | 90.40% | 17.39% | 17.39% | PASS |
| data2vec_base | 84.06% | 84.06% | 14.13% | 14.13% | PASS |
| distil_whisper_small | 81.52% | 81.52% | 21.74% | 21.74% | PASS |
| whisper_tiny | 96.38% | 96.38% | 47.83% | 47.83% | PASS |
| wav2vec2_100h | 88.04% | 88.04% | 21.74% | 21.74% | PASS |

Stage 2 model IDs verified:
- wav2vec2_base -> facebook/wav2vec2-base-960h (CTC)
- whisper_base -> openai/whisper-base (Seq2Seq)
- data2vec_base -> facebook/data2vec-audio-base-960h (CTC)
- distil_whisper_small -> distil-whisper/distil-small.en (Seq2Seq)
- whisper_tiny -> openai/whisper-tiny (Seq2Seq)
- wav2vec2_100h -> facebook/wav2vec2-base-100h (CTC)

## 4. Stage 3 Numerical Verification (source: reports/ctta/multi_order_all_methods.csv)

| ORDER | Method | WER | delta_R | delta_D | max_delta_g | PASS |
|---|---|---|---|---|---|---|
| ORDER_A | no_adapt | 0.8551 | 0.0 | 0.0 | 0.0 | PASS |
| ORDER_A | suta | 0.8514 | -0.0037 | -0.0108 | 0.0 | PASS |
| ORDER_A | dsuta | 0.8533 | -0.0018 | -0.0108 | 0.0 | PASS |
| ORDER_A | dmsuta | 0.8551 | 0.0 | 0.0 | 0.0 | PASS |
| ORDER_B | suta | 0.8569 | +0.0018 | 0.0 | 0.0109 | PASS |
| ORDER_C | suta | 0.8551 | 0.0 | 0.0 | 0.0109 | PASS |

Stage 3 design invariants:
- Model: wav2vec2_base only (PASS)
- total_utterances: 60 (PASS)
- total_reference_words: 552 (PASS)
- window_size_k: 4 (PASS)
- num_updates: 15 windows (PASS)
- Orders: ORDER_A, ORDER_B, ORDER_C (PASS)

## 5. Stage 4 Verification (source: stage4d_multi_order_matrix.csv + dsg_go_no_go_decision.json)

| Invariant | Expected | Found | PASS |
|---|---|---|---|
| Total speakers | 12 | 12 | PASS |
| Total utterances | 120 | 120 | PASS |
| delta_G frozen | 0.02 | 0.02 | PASS |
| delta_D frozen | 0.02 | 0.02 | PASS |
| Bootstrap B | 1000 | 1000 | PASS |
| Acoustic conditions | 5 | 5 | PASS |
| Stream orders | 3 | 3 | PASS |
| Unstable cells | 3 | 3 | PASS |
| reverberation/SUTA max delta_g | 0.0326 | 0.0326 | PASS |
| babble/DMSUTA max delta_g | 0.0815 | 0.0815 | PASS |

Threshold calibration: frozen on calibration.csv only - never test data exposed. PASS.

## 6. DSG Configuration Verification (source: configs/stage5_gate_config.json)

| Parameter | Expected | Found | PASS |
|---|---|---|---|
| epsilon_R | 0.0000 | 0.0000 | PASS |
| epsilon_G | 0.0200 | 0.0200 | PASS |
| epsilon_D | 0.0200 | 0.0200 | PASS |
| B | 1000 | 1000 | PASS |
| confidence | 0.95 | 0.95 | PASS |
| resampling_unit | speaker | speaker | PASS |
| paired | true | true | PASS |
| fail_closed | true | true | PASS |

Rollback semantics (src/dsg_ctta/controller/shadow.py lines 96-102):
  ACCEPT: promote candidate theta -> theta_{t+1}
  REJECT: discard candidate, retain live_model theta_t (NOT theta_{t-1})
  CONFIRMED: PASS

Fail-closed policy:
  on_nan_action: REJECT (PASS)
  on_inf_action: REJECT (PASS)
  on_missing_group_action: REJECT (PASS)
  on_empty_sentinel_action: REJECT (PASS)
  on_exception_action: REJECT (PASS)

NOTE: configs/default_config.yaml has epsilon_r=0.01 (legacy scaffold).
The operative frozen gate reads configs/stage5_gate_config.json (epsilon_R=0.0000).
Stage 6 code explicitly loads GATE_CONFIG = configs/stage5_gate_config.json. PASS.

## 7. Stage 6 Artifact Verification

- six_model_benchmark.csv: Found (PASS)
- eight_model_benchmark.csv: Found (PASS)
- model_compatibility_manifest.json: Found (PASS)
- DSG summary CSVs (6-model, 8-model): Found (PASS)
- Group metrics CSVs (6-model, 8-model): Found (PASS)
- Seq2Seq marked INCOMPATIBLE_NON_CTC in CSVs: whisper_base, distil_whisper_small (PASS)

## 8. Speaker Leakage Verification

Partitions and speakers (from stage2_final_report.md Section 3.2):
  development:        DTW, ERMS, LDC, NJS, PRK, YBAA
  calibration:        HJK, HKK, MPXM, SKA, TNI, TNT
  sentinel_candidates: ASI, BWC, HCC, LXC, YDCK, ZHAA
  final_test:         ABA, BJM, BVT, EBVS, MBX, TLX

All four sets are pairwise disjoint. Stage 2 report confirms empty intersection. PASS.
Sentinel contamination check enforced in code via FrozenSentinelPanel.assert_no_speaker_contamination(). PASS.

## 9. Label Isolation Verification

Adapters accept only UnlabeledAudioBatch (no reference transcripts in the batch object).
Confirmed in src/dsg_ctta/adaptation/base.py line 65 type signature. PASS.

## 10. Architecture Boundary Verification

Seq2Seq models marked INCOMPATIBLE_NON_CTC in Stage 6 benchmark CSV.
Incompatible model gate present in scripts/stage6/02_run_model.py docstring (line 19). PASS.

## 11. Discrepancies

DISCREPANCY (non-blocking, labelling only):
  wav2vec2_base and data2vec_base are listed in Stage 6 historical CSV without overlap/held-out labelling.
  Under v1.1.0, these must be labelled overlap_ctc_controls in all NEW artifacts.
  Historical Stage 6 CSVs must NOT be retroactively modified.
  Action: Phase 2 model registry assignment. No historical numbers affected.

## 12. Checklist Summary

| Check | Result |
|---|---|
| Git working tree clean | PASS |
| Zero tracked files modified | PASS |
| 37/37 historical artifacts found and hashed | PASS |
| Stage 2 WER/D numbers verified | PASS |
| Stage 3 WER/delta_R/delta_D/max_delta_g | PASS |
| Stage 3 design invariants | PASS |
| Stage 4 design invariants | PASS |
| Stage 4 thresholds frozen on calibration only | PASS |
| DSG epsilon_R=0 epsilon_G=0.02 epsilon_D=0.02 B=1000 | PASS |
| DSG rollback: retain theta_t not theta_{t-1} | PASS |
| Fail-closed: REJECT on error/NaN/missing | PASS |
| Stage 6 artifacts untouched | PASS |
| Seq2Seq CTTA incompatibility enforced | PASS |
| Speaker leakage: zero overlap | PASS |
| Label isolation enforced | PASS |
| SHA-256 manifest written | PASS |

## STATUS: FROZEN_AND_VERIFIED

Next authorized phase: PHASE 2 - Model Registry + Architecture Audit

This certificate was generated by audit inspection only.
No experiments were run. No historical results were modified.
No thresholds or configs were changed.
