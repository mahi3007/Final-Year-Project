# Stage 6M Technical Specification: Counterfactual Replay Vault & Candidate Provenance

**Protocol:** `v1.2.0-stage6m-proposal`  
**Governing Standard:** ADR-005  
**Document Status:** Technical Architecture Specification for Stakeholder Review  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED**  
**Submission Date:** 2026-10-12  

---

## 1. Executive Summary & Archival Invariant

In Stage 5M, the downstream outcomes of all 2,560 rejected candidates were unobserved because candidate weights were discarded online (`del cand_core`) to maintain fail-closed invariants. Stage 6M specifies a **Controlled Offline Counterfactual Replay Vault** designed to prevent this missingness in newly generated experiments.

> [!CRITICAL]
> **Archival Immutability & Limitation Notice**:
> The Stage 6M Replay Vault operates **strictly prospectively**. It is designed to capture and evaluate candidate states in future Stage 6M experiments. **It does NOT retroactively recover or fabricate counterfactual outcomes for the 2,560 discarded Stage 5M candidates**, whose weights were permanently discarded upon rejection. Those historical Stage 5M outcomes remain irrevocably unobserved.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            REPLAY VAULT OPERATIONAL TAXONOMY                                │
├─────────────────────────┬───────────────────────────┬───────────────────────────────────────┤
│ Verification Level      │ Mathematical Invariant    │ Practical Test                        │
├─────────────────────────┼───────────────────────────┼───────────────────────────────────────┤
│ 1. Parameter Integrity  │ L_∞(θ_saved, θ_loaded) = 0│ Exact bit-for-bit state_dict reload   │
├─────────────────────────┼───────────────────────────┼───────────────────────────────────────┤
│ 2. Inference Stability  │ |z_orig - z_reload| ≤ tol │ Logits match within numerical tol     │
│                         │ (tol = 1e-5 on GPU)       │ (accounts for non-deterministic CUDA) │
├─────────────────────────┼───────────────────────────┼───────────────────────────────────────┤
│ 3. Hypothesis Invariant │ Ŷ_orig == Ŷ_reload        │ Exact character-for-character match   │
│                         │ (Greedy CTC argmax)       │ of transcribed hypothesis string      │
├─────────────────────────┼───────────────────────────┼───────────────────────────────────────┤
│ 4. Metric Consistency   │ WER(Ŷ_orig) == WER(Ŷ_rel) │ Exact integer error count match       │
└─────────────────────────┴───────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Replay Vault Architecture & Directory Structure

The Replay Vault operates in an access-controlled, sandboxed directory:
`checkpoints/stage6m/research_vault/`

```
checkpoints/stage6m/research_vault/
├── manifest/
│   └── stage6m_candidate_provenance_manifest.jsonl
├── models/
│   ├── cand_{run_id}_step{t}_state.pt         (Serialized candidate parameter delta)
│   └── ret_{run_id}_step{t}_state.pt          (Serialized retained comparator state)
└── recipes/
    └── recipe_{run_id}_step{t}.json           (Deterministic reconstruction recipe)
```

### 2.1 Complete Candidate Metadata Schema
Every candidate evaluation $t$ logs a structured record in `stage6m_candidate_provenance_manifest.jsonl`:
```json
{
  "candidate_id": "cand_wav2vec2_base_clean_suta_order_a_step14",
  "run_id": "wav2vec2_base_clean_suta_order_a",
  "window_index": 14,
  "stream_order": "ORDER_A",
  "model_key": "wav2vec2_base",
  "method": "suta",
  "adaptation_config": {
    "lr": 0.0001,
    "steps": 10,
    "temperature": 2.5,
    "optimizer": "AdamW",
    "betas": [0.9, 0.999],
    "eps": 1e-8
  },
  "random_seed": 20261012,
  "torch_rng_state_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "pre_update_checkpoint_hash": "5272cc15fda04952",
  "candidate_checkpoint_hash": "a1b2c3d4e5f67890",
  "candidate_checkpoint_path": "checkpoints/stage6m/research_vault/models/cand_..._state.pt",
  "cumulative_accepted_updates_count": 1,
  "operational_decision": "REJECT",
  "gate_ucb_delta_r": 0.0045,
  "gate_ucb_max_delta_g": 0.0210,
  "gate_ucb_delta_d": 0.0180,
  "gate_rejection_reasons": ["EPSILON_R_EXCEEDED", "EPSILON_G_EXCEEDED"],
  "prospective_window_audio_ids": ["cv_en_141", "cv_en_142", "cv_en_143", "cv_en_144"],
  "counterfactual_verification_status": "PENDING_OFFLINE_EVALUATION"
}
```
- **Status:** `PROPOSED`.

---

## 3. Separation of Parameter Integrity from Numerical Reproducibility

A key scientific correction in this audit is separating **bit-for-bit parameter integrity** from **numerical inference reproducibility across heterogeneous execution environments**.

### 3.1 Checkpoint Parameter Integrity ($L_\infty = 0$)
When model weights are serialized and deserialized within PyTorch using `torch.save` and `torch.load`:
$$L_\infty(\theta_{\text{saved}}, \theta_{\text{loaded}}) = \max_i |\theta_{\text{saved}}[i] - \theta_{\text{loaded}}[i]| = 0.0$$
- **Rule:** Parameter reload must be mathematically exact bit-for-bit. Any non-zero delta indicates checkpoint corruption.
- **Status:** `PROPOSED & TESTED IN PROTOCOL HARNESS`.

### 3.2 Numerical Inference Reproducibility (Floating-Point Tolerance)
Executing deep neural network forward passes across heterogeneous GPU architectures (e.g., Tesla T4 vs. A100 vs. RTX 4090) or different CUDA/cuDNN versions may produce slight floating-point differences due to non-deterministic atomic operations and fused kernels.
- **Logit Tolerance Invariant:**
  $$\max_{t, c} |z_{\text{orig}}[t, c] - z_{\text{reload}}[t, c]| \le 1.0 \times 10^{-5}$$
- **Greedy Transcript Invariant:** Under greedy CTC decoding ($\operatorname{argmax}_c z[t, c]$), the argmax is stable against $10^{-5}$ perturbations unless logits are identical to the 5th decimal place.
- **Transcript Exact Match:** The decoded transcript string must match character-for-character:
  $$\operatorname{Decoded}(\hat{Y}_{\text{orig}}) \equiv \operatorname{Decoded}(\hat{Y}_{\text{reload}})$$
- **Status:** `PROPOSED`.

---

## 4. Offline Counterfactual Evaluation Protocol

To ensure that evaluation references **never leak** into operational decisions:

1. **Firewall Invariant:** The operational streaming loop runs to completion across all windows $B_0, \dots, B_{29}$ with reference labels firewalled.
2. **Post-Stream Batch Evaluation Pass:** An isolated audit worker accesses `checkpoints/stage6m/research_vault/` and evaluates the paired counterfactual on window $B_{t+1}$:
   - Evaluates retained comparator model: $\hat{Y}_{t+1}^{\text{ret}} = f_{\theta_t}(X_{t+1})$.
   - Evaluates candidate model: $\hat{Y}_{t+1}^{\text{cand}} = f_{\theta'_t}(X_{t+1})$.
   - Retrieves quarantined reference transcripts $Y_{t+1}$ from encrypted vault.
   - Computes:
     $$\Delta E_{t+1} = \operatorname{LevenshteinErrors}(\hat{Y}_{t+1}^{\text{cand}}, Y_{t+1}) - \operatorname{LevenshteinErrors}(\hat{Y}_{t+1}^{\text{ret}}, Y_{t+1})$$
3. **Audit Status Update:** Manifest is updated with `counterfactual_verification_status = VERIFIED_EXACT_PAIRED_COUNTERFACTUAL`.
- **Status:** `PROPOSED`.

---

## 5. Missingness Classification & Sensitivity Invariants

If a candidate state cannot be evaluated (e.g., disk I/O failure, unresolvable audio clip):
1. **Explicit Tagging:** Tagged as `UNAVAILABLE_CORRUPTED` or `UNAVAILABLE_MISSING_COMPARATOR`.
2. **Prohibition of Silent Neutral Imputation:** It is strictly prohibited to record $\Delta E_{t+1} = 0$ for unobserved outcomes.
3. **Deterministic Sensitivity Range:** For any missingness $M_{\text{unavail}}$, compute deterministic worst-case sensitivity bounds:
   $$\text{Lower Bound} = \frac{N_{\text{harmful}}}{N_{\text{total}}}, \quad \text{Upper Bound} = \frac{N_{\text{harmful}} + M_{\text{unavail}}}{N_{\text{total}}}$$
- **Status:** `PROPOSED & ENFORCED`.

---

## 6. Audit Trail & Claim Status

| Claim / Component | Description | Status | Evidence Reference |
| :--- | :--- | :---: | :--- |
| **No Retroactive Stage 5M Recovery** | Stage 5M discarded weights remain unobserved | `VERIFIED FROM ARTIFACT` | ADR-005 historical record |
| **L_∞ = 0 Parameter Integrity** | State dict reload bit-for-bit identical | `PROPOSED & TESTED` | Section 3.1 |
| **Numerical Inference Tolerance** | Logit tol ≤ 1e-5; exact transcript match | `PROPOSED` | Section 3.2 |
| **Offline Reference Isolation** | Transcripts evaluated post-stream in vault | `PROPOSED` | Section 4 |
| **Zero Silent Neutral Imputation** | Missing cases never imputed as neutral | `PROPOSED & ENFORCED` | Section 5 |
