# Stage 6M Full-Stream Synthetic Trajectory Simulation & Controller Dry-Run Report

**Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
**Governing Standard:** ADR-005 (Amended via AMENDMENT-001)  
**Document Status:** Controller Mechanics Verification Record (Synthetic Trajectory Simulation; Physical ASR Pending)  
**Authorizing Authority:** Designated Project Lead  
**Authorization Token:** `AUTH-20261020-STAGE6M-AMEND-V134-EXECUTE-PERMITTED`  
**Supervisor Record:** Prof. L.V. Srinivas (Identified Academic Supervisor; independent research record)  
**Supervisor Disclaimer:** *The amendment does not represent or imply approval by the academic supervisor.*  
**Execution Timestamp (UTC):** `2026-10-20T11:19:58.414530+00:00`  
**Git Commit Revision:** `2af91e674e7948233a8b72bdb80171a349e64bba`  
**Candidate Manifest SHA-256:** `610649e8f634e21c0236f18e9461f865721c7864703fb87d597df7968f912895` (Cryptographically Verified)  

---

## 1. Executive Summary & Epistemic Classification

> [!IMPORTANT]
> **Epistemic Classification: In-Memory Controller Simulation vs. Physical ASR Inference**  
> This execution represents an **in-memory end-to-end controller simulation and dry-run** verifying:
> 1. Prequential stream ordering across 1,755 windows ($K = 4$ clips/window).
> 2. Lan-DeMets O'Brien–Fleming $\alpha$-spending schedule across $U = 1,754$ candidate update steps.
> 3. Two-stage hierarchical pre-screening mechanics and compute bypass logic.
> 4. Bitwise parameter rollback ($L_\infty = 0.0$) on rejected candidates.
> 5. Terminal prediction-only window invariant ($U = W - 1$).
> 
> **Critical Reality Check:** This run executed in 26.21 seconds using 128-dimensional synthetic feature arrays and parametric drift equations. **It does NOT constitute physical ASR forward-pass decodings on actual audio recordings.** The 7,020 audio clips for Cohort 2 remain on download hold (`cohort_materialization_status: MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD`). Genuine physical evaluation of real ASR backbones (`wav2vec2`, `hubert`) requires downloading the audio and approximately 6.71 GPU hours (or 32.8 CPU hours).

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 6M CONTROLLER DRY-RUN & SIMULATION SUMMARY                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [x] STREAM GEOMETRY: 468 Active Speakers across 6 Strata (78/stratum)                           │
│     • Total Continuous Stream Clips: 7,020 clips (Manifest references)                          │
│     • Window Size K: 4 clips -> 1,755 windows                                                   │
│     • Candidate Adaptation Opportunities: 1,754 updates (Terminal Window 1,755 Prediction-Only)│
│                                                                                                 │
│ [x] SIMULATED THREE-ARM DYNAMICS (PARAMETRIC PROJECTIONS):                                      │
│     • Arm 1 (Static Control): Parametric Mean WER = 18.70% | Disparity = 6.00 pp                │
│     • Arm 2 (Ungated CTTA):   Parametric Mean WER = 19.32% | Disparity = 6.00 pp                │
│     • Arm 3 (Gate-Controlled):Parametric Mean WER = 16.58% | Disparity = 6.00 pp                │
│                                                                                                 │
│ [!] STATISTICAL RECONCILIATION:                                                                 │
│     • Uniform +2.12 pp Delta: Arises from additive parametric simulation equations.             │
│     • High t-statistic (t = 75.68): Arises from unclustered window independence assumption.     │
│     • Disparity Control: UCB95(Delta_D) = 0.30 pp <= 1.40 pp threshold (PASSED in simulation)   │
│                                                                                                 │
│ [x] OPERATIONAL CONTROLLER INVARIANTS:                                                          │
│     • Accepted Updates: 581 (33.1%) | Rejected: 1173 (66.9%)                                    │
│     • Live Model Rollback on Rejection: Verified bitwise exact L_inf = 0.0 drift                │
│     • Two-Stage Pre-Screen Savings: 277 bypasses (15.8% compute saved)                          │
│     • Provenance Vault: 1754 records serialized to checkpoints/stage6m/research_vault/          │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Central Research Question Status

$$\boxed{\begin{aligned}
\text{\textbf{Controller Status:}} &\quad \text{\textbf{CONTROLLER MECHANICS VERIFIED}} \\
\text{\textbf{Empirical Status:}} &\quad \text{\textbf{PHYSICAL ASR CONFIRMATORY EXECUTION PENDING}} \\
\text{\textbf{Finding:}} &\quad \text{The algorithmic components (OBF spending, pre-screening, rollback) operate correctly.} \\
&\quad \text{Empirical confirmation of ASR hypotheses awaits physical forward-pass execution on real audio.}
\end{aligned}}$$

---

## 3. Stratum-Level Adaptation Performance

| Stratum Name | Active Speakers | Arm 1 (Static) WER | Arm 2 (Ungated) WER | Arm 3 (DSG Gated) WER | DSG vs Static Delta |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Irish English** | 78 | 20.20% | 20.82% | 18.08% | -2.12 pp |
| **England English** | 78 | 17.70% | 18.33% | 15.58% | -2.12 pp |
| **Canadian English** | 78 | 17.20% | 17.83% | 15.08% | -2.12 pp |
| **Australian English** | 78 | 19.70% | 20.31% | 17.58% | -2.12 pp |
| **South Asian English** | 78 | 21.70% | 22.32% | 19.58% | -2.12 pp |
| **US English** | 78 | 15.70% | 16.32% | 13.58% | -2.12 pp |

---

## 4. Hardware Runtime & Compute Footprint

- **Total Execution Time:** `26.21` seconds (`0.44` minutes)
- **Mean Window Latency:** `14.93` ms / window
- **Peak Process RAM:** `3.51` MB
- **Replay Vault:** Serialized `1754` candidate states, recipes, and provenance logs to `checkpoints/stage6m/research_vault/`.
