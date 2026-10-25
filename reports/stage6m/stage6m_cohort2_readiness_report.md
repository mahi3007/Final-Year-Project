# Stage 6M Confirmatory Cohort 2 Preflight Readiness Report

> [!WARNING]
> **Overall Preflight Status:** `HOLD`  
> **Summary:** MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Confirmatory data prerequisites not yet materialized on disk.  
> **Timestamp:** 2026-10-25T09:44:17.955061+00:00  
> **Git Commit:** `25ced72f02`  
> **Protocol:** `v1.3.4-stage6m-self-authorization-amendment` (ADR-005)

---

## 1. Governance & Execution Disclaimer

Passing technical preflight checks establishes scientific feasibility; it does NOT constitute authorization of compute expenditure or confirmatory benchmark execution. Hardware execution requires designated project lead or supervisory signoff.

---

## 2. Preflight Checklist Verification Matrix

| Checklist Item | Scope | Status | Key Metrics / Evidence |
| :--- | :--- | :---: | :--- |
| **1. Manifest Integrity & Schema** | `stage6m_locked_candidate_manifest.json` | `PASS` | SHA-256 locked (610649e8f6...); 468 speakers across 6 strata (78/stratum); Option 1B reserve verified (27 reserve); authority reconciled (RECONCILED_AMENDMENT_V134). |
| **2. Manifest <-> CSV Agreement** | `stage6m_cohort2_audio.csv` | `HOLD` | Validation could not be completed: evaluation CSV not materialized on disk (prerequisite missing). |
| **3. Audio Materialization & Decodability** | `cohort2_audio/*.mp3` | `HOLD` | Validation could not be completed: physical audio files not materialized (MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Cohort 2 audio directory not found: datasets/external/common_voice_27/cohort2_audio). |
| **4. Sentinel Panel Completeness & Isolation** | `stage5_sentinel_panel.csv` | `PASS` | 30 core clips (281 words, uncertainty floor = 0.3559 pp); sampled audio decodability verified; 0 speaker overlap (zero leakage). |
| **5. Configuration & Budget Freeze** | Prequential Lan-DeMets Gating | `PASS` | Model (wav2vec2_base), thresholds, Lan-DeMets spending, 1754 candidate updates, and compute budget frozen. |

---

## 3. Status Reasons and Action Items

The following items currently hold confirmatory execution:

- **MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Evaluation CSV not materialized: datasets/splits/stage6m_cohort2_audio.csv**
- **MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Authoritative clip lock file not materialized: datasets/splits/stage6m_cohort2_audio.lock.json**
- **MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Cohort 2 audio directory not found: datasets/external/common_voice_27/cohort2_audio**

### Required Steps to Lift HOLD:
1. Materialize `datasets/splits/stage6m_cohort2_audio.csv` matching the locked candidate manifest.
2. Download/extract the 7,020 physical MP3 audio files into `datasets/external/common_voice_27/cohort2_audio/`.
3. Verify compute allocation (e.g. Kaggle Tesla P100 GPU session).
4. Rerun preflight validation to verify transition to `READY FOR AUTHORIZED EXECUTION`.

---

## 4. Frozen Execution Configuration

```json
{
  "check_name": "execution_configuration_freeze",
  "status": "PASS",
  "governing_protocol": "v1.3.4-stage6m-self-authorization-amendment",
  "governing_standard": "ADR-005",
  "model_architecture": "wav2vec2_base",
  "huggingface_backbone": "facebook/wav2vec2-base-960h",
  "stream_geometry": {
    "cohort": "cohort2",
    "total_evaluation_clips": 7020,
    "window_size_k": 4,
    "total_stream_windows_w": 1755,
    "adaptation_updates_u": 1754,
    "terminal_window_index": 1754,
    "terminal_window_mode": "PREDICTION_ONLY_INVARIANT"
  },
  "gate_parameters": {
    "epsilon_r_pp": 0.0,
    "epsilon_g_pp": 2.0,
    "epsilon_d_pp": 2.0,
    "alpha_target": 0.05,
    "spending_function": "Lan-DeMets O'Brien-Fleming",
    "effective_uncertainty_floor_pp": 0.3559,
    "tie_breaker_rule": "REJECT_TIE_STRICT_INEQUALITY",
    "rollback_guarantee": "BITWISE_EXACT_PARAMETER_HASH"
  },
  "hardware_environment": {
    "cuda_available": false,
    "device_type": "cpu",
    "device_name": "None (CPU Execution)",
    "total_vram_gb": 0.0,
    "pytorch_version": "2.11.0+cpu"
  },
  "compute_budget_estimate": {
    "evaluation_clip_forward_passes": 21060,
    "sentinel_forward_passes": 52650,
    "suta_backward_passes": 3508,
    "estimated_runtime_hours_p100": 3.8,
    "recommended_accelerator": "Kaggle NVIDIA Tesla P100 (16 GB VRAM)"
  },
  "output_locations": {
    "results_dir": "results/stage6m_kaggle",
    "reports_dir": "reports/stage6m"
  }
}
```
