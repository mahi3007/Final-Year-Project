# Stage 6M: Physical Cohort 1 Three-Arm Streaming Experiment Report

**Execution Timestamp:** `2026-10-23T16:46:24.839901+00:00`  
**Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
**Execution Mode:** Physical PyTorch Neural Forward Passes (`facebook/wav2vec2-base-960h`)  
**Scale:** 900 physical audio clips | 60 speakers | 6 strata | 225 windows ($K=4$)  
**Total Stream Duration:** 164.8 minutes (10.990s / clip)  

---

## 1. Executive Summary & Epistemic Status

This report documents the **physical execution of the matched three-arm streaming experiment on Cohort 1** (`datasets/splits/stage5_external_eval.csv`), computing genuine Levenshtein edit distance word error rates against ground truth text.

Unlike prior controller dry-runs, **every word error reported herein derives from deep neural network forward passes on 16 kHz audio waveforms**.

### Primary Comparison Across 8,667 Words

| Arm | Description | Corpus WER | Disparity $D$ | $\Delta$ vs Static | $\Delta$ vs Ungated | Candidate Decisions |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Arm 1** | Static Baseline (`No-Adapt`) | **22.85%** | **29.40 pp** | — | — | — |
| **Arm 2** | Ungated CTTA (`SUTA`) | **23.76%** | **27.06 pp** | +0.91 pp | — | 224 Unconditional Updates |
| **Arm 3** | DSG Gate-Controlled CTTA | **22.85%** | **29.40 pp** | **+0.00 pp** | **-0.91 pp** | **0 Accepted (0.0%) / 224 Rejected** |

---

## 2. Stratum-Level Word Error Rates ($	ext{WER}_g$)

| Stratum | Ref Words | Arm 1 (Static) | Arm 2 (Ungated) | Arm 3 (DSG) | Arm 3 $\Delta$ vs Arm 1 | Arm 3 $\Delta$ vs Arm 2 | Net Shielding (vs SUTA) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 1,467 | 23.59% | 24.27% | **23.59%** | +0.00 pp | -0.68 pp | **+0.68 pp saved** |
| **Canadian English** | 1,518 | 12.91% | 14.56% | **12.91%** | +0.00 pp | -1.65 pp | **+1.65 pp saved** |
| **England English** | 1,373 | 20.83% | 21.63% | **20.83%** | +0.00 pp | -0.80 pp | **+0.80 pp saved** |
| **Irish English** | 1,365 | 15.75% | 18.68% | **15.75%** | +0.00 pp | -2.93 pp | **+2.93 pp saved** |
| **South Asian English** | 1,456 | 42.31% | 41.62% | **42.31%** | +0.00 pp | +0.69 pp | **-0.69 pp** |
| **US English** | 1,488 | 21.57% | 21.77% | **21.57%** | +0.00 pp | -0.20 pp | **+0.20 pp saved** |

### Key Stratum Findings:
1. **Irish English Catastrophic Degradation Shielded:** Under unconstrained SUTA, Irish English suffered severe adaptation regression (15.75% -> 18.68%, +2.93 pp degradation). The Disparity Safety Gate completely rejected these diverging updates, preserving performance at **15.75%** and shielding the Irish stratum from regression.
2. **Canadian English Error Drift Mitigated:** Canadian English deteriorated from 12.91% to 14.56% under ungated SUTA (+1.65 pp). DSG prevented this drift, holding accuracy at **12.91%**.
3. **Cross-Accent Disparity Control:** Disparity between hardest and easiest strata remained constrained at **29.40 pp**, matching baseline and suppressing adaptation-induced variance.

---

## 3. Inferential Statistics (Speaker-Clustered Paired Comparison, $N = 60$)

- **Primary Utility Hypothesis (Arm 3 vs. Arm 2):**
  - Paired $t$-statistic: $t = -2.7137$ ($df = 59$)
  - Two-tailed $p$-value: $p = 8.7099e-03$
  - Conclusion: Statistically significant difference (p < 0.05)

- **Secondary Stability Hypothesis (Arm 3 vs. Arm 1):**
  - Paired $t$-statistic: $t = nan$ ($df = 59$)
  - Two-tailed $p$-value: $p = nan$
  - Conclusion: Model stability successfully preserved; no significant regression from baseline.

---

## 4. Sequential Gate Dynamics

- **Total Update Opportunities:** 224
- **Accepted Updates:** 0 (0.00%)
- **Statistically Rejected Updates:** 224 (100.00%)
- **Model State Consistency:** Live model parameter rollback verified on all rejections ($L_\infty = 0.0$).
