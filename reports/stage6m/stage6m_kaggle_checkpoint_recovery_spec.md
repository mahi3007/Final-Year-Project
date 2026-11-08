# Stage 6M: Kaggle Checkpoint & Recovery Specification

**Document ID:** `STAGE6M-KAGGLE-CHECKPOINT-SPEC-20261107`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Target Environment:** Kaggle Virtual GPU (NVIDIA Tesla T4 x2, 12-Hour Session Limit)  

---

## 1. Problem Statement & Motivation

The Stage 6M confirmatory benchmark evaluates **16,500 audio recordings** organized into **4,125 streaming windows** ($K=4$) across three paired experimental arms (Static Baseline, Ungated SUTA, and DSG-Gated SUTA).

Although the benchmark's estimated runtime on an NVIDIA Tesla T4 GPU is **~2.8 to 4.2 hours** (well within Kaggle's 12.0-hour limit), cloud environments can experience:
- Interactive idle timeouts.
- Transient browser disconnects.
- Background run preemption or container resets.
- Ephemeral storage limits.

To ensure **zero data loss** and **100% deterministic trajectory recovery**, a robust checkpoint-and-recovery mechanism is integrated into the Kaggle runner.

---

## 2. Checkpoint Architecture

Checkpoints are serialized to `/kaggle/working/checkpoints/stage6m/` at fixed window intervals ($\Delta W = 50$ windows) and on every gate decision:

```
/kaggle/working/checkpoints/stage6m/
├── checkpoint_latest.json          # Pointer to most recent valid checkpoint
├── state_win_0050.pt               # PyTorch model & optimizer weights for Arms 2 & 3
├── state_win_0100.pt
├── gate_state_latest.json          # Alpha spending, cumulative statistics, boundary values
└── stream_records.jsonl            # Append-only prequential prediction log
```

### Serialized State Vector
1. **Window Index:** `completed_window_idx` ($0 \le win\_idx < 4125$).
2. **Arm 1 (Static Baseline):** Parameter hash verification (`init_hash`). Arm 1 weights are never updated; verified bitwise invariant.
3. **Arm 2 (Ungated CTTA):**
   - LayerNorm weight & bias state dictionary (`arm2_model.state_dict()`).
   - SUTA optimizer state dictionary (`arm2_optimizer.state_dict()`).
   - Bitwise parameter SHA-256 hash (`arm2_param_hash`).
4. **Arm 3 (DSG Gate-Controlled CTTA):**
   - LayerNorm weight & bias state dictionary (`arm3_model.state_dict()`).
   - SUTA optimizer state dictionary (`arm3_optimizer.state_dict()`).
   - Bitwise parameter SHA-256 hash (`arm3_param_hash`).
5. **Sentinel Safety Gate State:**
   - Lan-DeMets O'Brien-Fleming cumulative spent alpha ($\alpha_{\text{spent}}$).
   - Candidate decision history (`APPROVED` vs. `REJECTED`).
   - Stratum-level running non-inferiority margins.
   - Live model rollback audit log.
6. **Append-Only Prediction Log:** Append-only JSONL entries containing transcription hypotheses, word counts, and execution metrics.

---

## 3. Recovery Protocol (Fault-Tolerant Resume)

When the Kaggle runner launches (or restarts following a session disconnect):
1. **Checkpoint Detection:** The runner inspects `/kaggle/working/checkpoints/stage6m/checkpoint_latest.json`.
2. **Hash Verification:** If a checkpoint exists, the runner loads `state_win_XXXX.pt` and verifies that the model parameter SHA-256 matches the recorded hash in the metadata.
3. **Model & Gate Reconstitution:**
   - Restores Arm 2 and Arm 3 model weights and optimizer states.
   - Reconstitutes the `StreamingSentinelSafetyGate` with exact cumulative alpha spending and update index.
4. **Fast-Forward Stream:**
   - The audio stream skips to `start_clip_idx = (completed_window_idx + 1) * K`.
   - The stream resumes from window `completed_window_idx + 1` with identical trajectory continuity.
5. **No Redundant Inference:** Previously completed windows are **never re-evaluated**, guaranteeing that stochastic adaptation states and random number generator positions are perfectly aligned.

---

## 4. Disk Space Conservation

Kaggle provides up to **20 GB** of scratch space in `/kaggle/working/`.
- Only the **2 most recent** full model weight checkpoints (`.pt` files, ~5 MB each for LayerNorm parameters) are retained; older `.pt` checkpoints are pruned.
- The append-only record log (`stream_records.jsonl`) consumes **< 25 MB** for all 16,500 clips.
- Total checkpoint disk footprint: **< 100 MB** (less than 0.5% of available scratch space).

---

## 5. Clean Finalization & Packaging

Upon completion of Window 4,124 ($U=4,124$ candidate updates):
1. The final terminal window is evaluated (prediction-only, no adaptation update).
2. The entire output directory is bundled:
   ```bash
   tar -czvf /kaggle/working/stage6m_cohort3_results.tar.gz -C /kaggle/working results/ reports/ checkpoints/
   ```
3. The resulting `.tar.gz` archive (~15–30 MB) is immediately available for download via the Kaggle notebook output pane.
