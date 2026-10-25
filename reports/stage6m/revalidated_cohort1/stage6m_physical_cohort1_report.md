# Stage 6M: Physical Cohort 1 Three-Arm Streaming Experiment Report (Post-Execution Audit Edition)

> [!NOTE]
> **Provenance Status:** `POST_AUDIT_PHYSICAL_BENCHMARK_RUN`  
> **Tested Commit SHA:** `d1230787109adf070d6186740e947943664c52cb`  
> **Initial Model Parameter Hash (SHA-256):** `cbdef0a09bed300c26d542f5bd920712c3387f3648569a89f5aa16da4021a261` (prefix `cbdef0a09bed300c`)  
> **Tested Controller:** `StreamingSentinelSafetyGate` (Unclipped OBF Schedule + Stratified Cluster Bootstrap $B=500$)  
> **Execution Timestamp:** `2026-10-25T02:03:34.465269+00:00`  
> **Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
> **Execution Mode:** Physical PyTorch Neural Forward Passes (`facebook/wav2vec2-base-960h`)  
> **Scale:** 900 physical audio clips | 60 speakers | 6 strata | 225 windows ($K=4$)  
> **Total Stream Duration:** 144.8 minutes (9.651s / clip)  

---

## 1. Executive Summary & Epistemic Status

This report documents the **physical execution of the matched three-arm streaming experiment on Cohort 1** (`datasets/splits/stage5_external_eval.csv`) using the revised `StreamingSentinelSafetyGate`.

Unlike prior controller dry-runs, **every word error reported herein derives from deep neural network forward passes on 16 kHz audio waveforms**.

### Primary Comparison Across 8,667 Words

| Arm | Description | Corpus WER | Disparity $D$ | $\Delta$ vs Static | $\Delta$ vs Ungated | Candidate Decisions |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Arm 1** | Static Baseline (`No-Adapt`) | **22.85%** | **29.79 pp** | — | — | — |
| **Arm 2** | Ungated CTTA (`SUTA`) | **23.88%** | **26.94 pp** | +1.04 pp | — | 224 Unconditional Updates |
| **Arm 3** | DSG Gate-Controlled CTTA | **22.85%** | **29.79 pp** | **+0.00 pp** | **-1.04 pp** | **0 Accepted (0.0%) / 224 Rejected** |

### Disparity Comparators and Leveling Down
- **Relative to Static Baseline:** Arm 3 reduces cross-accent disparity from **29.79 pp** to **29.79 pp** (+0.00 pp).
- **Relative to Ungated SUTA:** Ungated SUTA exhibits a numerically lower disparity (26.94 pp vs. 29.79 pp), but this reduction is an artifact of **leveling down**: ungated SUTA degrades the best-performing accent (Canadian English degrades from 12.87% to 14.73%, +1.86 pp) rather than lifting disadvantaged groups. Arm 3 preserved Canadian English accuracy (12.87%), refusing to achieve lower disparity through degradation of advantaged speakers.

---

## 2. Stratum-Level Word Error Rates ($	ext{WER}_g$)

| Stratum | Ref Words | Arm 1 (Static) | Arm 2 (Ungated) | Arm 3 (DSG) | Arm 3 $\Delta$ vs Arm 1 | Arm 3 $\Delta$ vs Arm 2 | Direction vs Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 1,493 | 23.58% | 25.85% | **23.58%** | +0.00 pp | -2.28 pp | **Unchanged** |
| **Canadian English** | 1,500 | 12.87% | 14.73% | **12.87%** | +0.00 pp | -1.87 pp | **Unchanged** |
| **England English** | 1,393 | 21.25% | 22.04% | **21.25%** | +0.00 pp | -0.79 pp | **Unchanged** |
| **Irish English** | 1,383 | 15.76% | 17.79% | **15.76%** | +0.00 pp | -2.02 pp | **Unchanged** |
| **South Asian English** | 1,430 | 42.66% | 41.68% | **42.66%** | +0.00 pp | +0.98 pp | **Unchanged** |
| **US English** | 1,468 | 21.19% | 21.39% | **21.19%** | +0.00 pp | -0.20 pp | **Unchanged** |

---

## 3. Inferential Statistics (Speaker-Clustered Paired Comparison, $N = 60$)

> [!NOTE]
> **Estimand Clarification:** Inferential tests below evaluate the **unweighted speaker-average paired difference** ($(1/S) \sum_s (\text{WER}_{3,s} - \text{WER}_{1,s})$). This estimand weights each speaker equally and is distinct from the corpus-word-weighted aggregate WER difference (+0.0000 pp).

- **Primary Utility Hypothesis (Arm 3 vs. Arm 2):**
  - Paired $t$-statistic: $t = -2.4536$ ($df = 59$)
  - Two-tailed $p$-value: $p = 1.7116e-02$
  - Conclusion: Statistically significant difference (p < 0.05)

- **Secondary Stability Hypothesis (Arm 3 vs. Arm 1):**
  - Paired $t$-statistic: $t = nan$ ($df = 59$)
  - Two-tailed $p$-value: $p = nan$
  - Conclusion: No statistically significant difference detected at $\alpha = 0.05$.

- **Formal Two One-Sided Tests (TOST) Equivalence Analysis:**
  - Exploratory Equivalence Margin: $\Delta_{\text{equiv}} = \pm 0.50\text{ pp}$ (exploratory equivalence analysis using a $\pm 0.50$ percentage-point margin)
  - Observed Sample Difference: +0.0000 pp (identical predictions across all 900 clips and 60 speakers)
  - Sample Standard Error: $SE = 0.0000\text{ pp}$ ($s = 0.0$, degenerate sample variance)
  - 90% & 95% Student $t$-intervals: **Not Estimable** (inferential intervals degenerate under zero observed sample variance; displaying [0, 0] would be mathematically misleading)
  - TOST Equivalence Tests ($H_{01}: \Delta \le -0.50\text{ pp}, H_{02}: \Delta \ge +0.50\text{ pp}$): **Not Estimable** ($t$-statistics undefined / degenerate under zero sample variance)
  - Conclusion: Equivalence within margin not established (zero sample variance reflects sample identity from complete rollback, not population equivalence)

---

## 4. Sequential Gate Dynamics

- **Total Update Opportunities:** 224
- **Accepted Updates:** 0 (0.00%)
- **Statistically Rejected Updates:** 224 (100.00%)
- **Model State Consistency:** Live model parameter rollback verified on all rejections ($L_\infty = 0.0$).
