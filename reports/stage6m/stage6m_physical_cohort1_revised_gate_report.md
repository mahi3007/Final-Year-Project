# Stage 6M: Physical Cohort 1 Three-Arm Streaming Experiment Report (Post-Audit Benchmark)

> [!NOTE]
> **Provenance Status:** `POST_AUDIT_PHYSICAL_BENCHMARK_RUN`  
> **Tested Commit SHA:** `3f7e8e4964fb083648ece1e48a99cecde079decd`  
> **Tested Controller:** `StreamingSentinelSafetyGate` (Unclipped OBF Schedule + Stratified Cluster Bootstrap $B=500$)  
> **Execution Timestamp:** `2026-10-24T15:53:47.078643+00:00`  
> **Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
> **Execution Mode:** Physical PyTorch Neural Forward Passes (`facebook/wav2vec2-base-960h`)  
> **Scale:** 900 physical audio clips | 60 speakers | 6 strata | 225 windows ($K=4$)  
> **Total Stream Duration:** 145.8 minutes (9.721s / clip)  

---

## 1. Executive Summary & Epistemic Status

This report documents the **physical execution of the matched three-arm streaming experiment on Cohort 1** (`datasets/splits/stage5_external_eval.csv`) using the revised `StreamingSentinelSafetyGate`.

Unlike prior controller dry-runs, **every word error reported herein derives from deep neural network forward passes on 16 kHz audio waveforms**.

### Primary Comparison Across 8,667 Words

| Arm | Description | Corpus WER | Disparity $D$ | $\Delta$ vs Static | $\Delta$ vs Ungated | Candidate Decisions |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Arm 1** | Static Baseline (`No-Adapt`) | **22.85%** | **29.79 pp** | — | — | — |
| **Arm 2** | Ungated CTTA (`SUTA`) | **23.77%** | **27.89 pp** | +0.92 pp | — | 224 Unconditional Updates |
| **Arm 3** | DSG Gate-Controlled CTTA | **22.86%** | **29.45 pp** | **+0.01 pp** | **-0.91 pp** | **12 Accepted (5.4%) / 212 Rejected** |

---

## 2. Stratum-Level Word Error Rates ($	ext{WER}_g$)

| Stratum | Ref Words | Arm 1 (Static) | Arm 2 (Ungated) | Arm 3 (DSG) | Arm 3 $\Delta$ vs Arm 1 | Arm 3 $\Delta$ vs Arm 2 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 1,493 | 23.58% | 25.52% | **23.51%** | -0.07 pp | -2.01 pp |
| **Canadian English** | 1,500 | 12.87% | 14.07% | **13.13%** | +0.27 pp | -0.93 pp |
| **England English** | 1,393 | 21.25% | 22.61% | **21.18%** | -0.07 pp | -1.44 pp |
| **Irish English** | 1,383 | 15.76% | 17.28% | **15.62%** | -0.14 pp | -1.66 pp |
| **South Asian English** | 1,430 | 42.66% | 41.96% | **42.59%** | -0.07 pp | +0.63 pp |
| **US English** | 1,468 | 21.19% | 21.39% | **21.32%** | +0.14 pp | -0.07 pp |

---

## 3. Inferential Statistics (Speaker-Clustered Paired Comparison, $N = 60$)

- **Primary Utility Hypothesis (Arm 3 vs. Arm 2):**
  - Paired $t$-statistic: $t = -2.3079$ ($df = 59$)
  - Two-tailed $p$-value: $p = 2.4527e-02$
  - Conclusion: Statistically significant difference (p < 0.05)

- **Secondary Stability Hypothesis (Arm 3 vs. Arm 1):**
  - Paired $t$-statistic: $t = -0.2574$ ($df = 59$)
  - Two-tailed $p$-value: $p = 7.9776e-01$

---

## 4. Sequential Gate Dynamics

- **Total Update Opportunities:** 224
- **Accepted Updates:** 12 (5.36%)
- **Statistically Rejected Updates:** 212 (94.64%)
- **Model State Consistency:** Live model parameter rollback verified on all rejections ($L_\infty = 0.0$).
