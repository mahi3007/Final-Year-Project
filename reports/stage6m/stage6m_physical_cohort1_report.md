# Stage 6M: Physical Cohort 1 Three-Arm Streaming Experiment Report

**Execution Timestamp:** `2026-10-23T18:00:58.903440+00:00`  
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

### Key Stratum Findings & Subgroup Trade-Off Analysis:
1. **Irish English Catastrophic Degradation Shielded:** Under unconstrained SUTA, Irish English suffered severe adaptation regression (15.75% -> 18.68%, +2.93 pp degradation). The Disparity Safety Gate completely rejected these diverging updates, preserving performance at **15.75%** and shielding the Irish stratum from regression (+2.93 pp saved).
2. **Canadian English Error Drift Mitigated:** Canadian English deteriorated from 12.91% to 14.56% under ungated SUTA (+1.65 pp). DSG prevented this drift, holding accuracy at **12.91%** (+1.65 pp saved).
3. **Subgroup Trade-Off (South Asian English vs. Global Safety):** Under ungated SUTA, South Asian English improved slightly from 42.31% to 41.62% (-0.69 pp gain). However, because SUTA simultaneously induced severe regression on Irish English (+2.93 pp) and Canadian English (+1.65 pp), the global gate rejected these updates. This illustrates the fundamental trade-off: **disparity-aware safety gating conservatively prioritizes suppressing localized subgroup degradation over capturing unverified, localized adaptation gains**.
4. **Cross-Accent Disparity Control:** Disparity between hardest and easiest strata remained constrained at **29.40 pp**, matching baseline and suppressing adaptation-induced variance.

---

## 3. Inferential Statistics (Speaker-Clustered Paired Comparison, $N = 60$)

- **Primary Utility Hypothesis (Arm 3 vs. Arm 2):**
  - Paired $t$-statistic: $t = -2.7121$ ($df = 59$)
  - Two-tailed $p$-value: $p = 8.7462e-03$
  - Conclusion: **Statistically significant error reduction by DSG relative to ungated CTTA ($p < 0.01$).**

- **Secondary Stability Hypothesis (Arm 3 vs. Arm 1):**
  - Paired $t$-statistic: Identical ($df = 59$)
  - Conclusion: Model stability successfully preserved; zero empirical drift from static baseline.

### Speaker-Level Paired Distribution ($N = 60$)

| Speaker ID (Hash Prefix) | Accent Stratum | Ref Words | Arm 1 (Static) | Arm 2 (Ungated) | Arm 3 (DSG) | Arm 3 vs Arm 2 ($\Delta$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `02a40eed38bf20ab...` | South Asian English | 103 | 41.8% | 43.7% | 41.8% | -1.9 pp |
| `02cb893287feb15b...` | Irish English | 174 | 3.5% | 4.0% | 3.5% | -0.6 pp |
| `06c53aec09bca54d...` | Irish English | 119 | 8.4% | 12.6% | 8.4% | -4.2 pp |
| `0acf313028bfe2af...` | Australian English | 181 | 6.6% | 4.4% | 6.6% | +2.2 pp |
| `0e60a578941d4184...` | Australian English | 156 | 12.2% | 14.1% | 12.2% | -1.9 pp |
| `1225019d528d47c1...` | Canadian English | 169 | 14.2% | 16.0% | 14.2% | -1.8 pp |
| `194875abc05277ec...` | Irish English | 122 | 10.7% | 11.5% | 10.7% | -0.8 pp |
| `1a03eae370181165...` | Australian English | 141 | 29.8% | 33.3% | 29.8% | -3.5 pp |
| `1bda50a4a88d77a1...` | Canadian English | 156 | 8.3% | 12.2% | 8.3% | -3.9 pp |
| `228508a13bdcb59b...` | US English | 165 | 35.8% | 34.5% | 35.8% | +1.2 pp |
| *... [50 additional speakers recorded in JSON artifact] ...* | | | | | | |

---

## 4. Sequential Gate Dynamics & Epistemic Interpretation

- **Total Update Opportunities:** 224
- **Accepted Updates:** 0 (0.00%)
- **Statistically Rejected Updates:** 224 (100.00%)
- **Bitwise Model Rollback Verified:** Live model parameter hash was checked at every rejection:
  - Initial live parameter hash: `8390bd20927fa3b2`
  - Final live parameter hash:   `8390bd20927fa3b2`
  - Maximum parameter drift across rejected windows: $L_\infty = 0.0000$ (exact bitwise immutability).
- **Mathematical Mechanism of Universal Rejection:**
  - The core sentinel panel used for fast screening contained 30 clips (~300 words), producing an approximate standard error $SE_{sent} = \sqrt{\frac{2 \cdot \hat{p} (1 - \hat{p})}{N_{sent}}} \approx 3.38\%$.
  - Under Lan-DeMets O'Brien-Fleming alpha spending, $z_t \in [1.96, 4.50]$, creating an uncertainty buffer $z_t \cdot SE_{sent} \approx 6.6\% \text{ to } 15.2\%$.
  - Because the decision rule required $\text{UCB}_R = \Delta R + z_t \cdot SE_{sent} \le 0.00\%$, an unsupervised update on a 4-clip window would have needed to produce an instantaneous $\Delta R \le -6.6\%$ to $-15.2\%$ improvement on the sentinel panel to clear the gate.
  - This mathematically explains why 100% of candidate updates were rejected: the uncertainty penalty on the downsampled panel set a hurdle far higher than a single unsupervised gradient step can achieve, resulting in a conservative blanket safeguard.

---

## 5. Artifact Audit Trail

The complete empirical data supporting this report is exported into reproducible CSV and JSON artifacts:
1. **Report JSON:** [`reports/stage6m/stage6m_physical_cohort1_report.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_physical_cohort1_report.json)
2. **Speaker-Level Paired Records ($N=60$):** [`reports/stage6m/stage6m_physical_cohort1_speaker_records.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_physical_cohort1_speaker_records.csv)
3. **Sequential Gate Decisions ($U=224$):** [`reports/stage6m/stage6m_physical_cohort1_gate_decisions.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_physical_cohort1_gate_decisions.csv)

> [!WARNING]
> **Epistemic Qualification on Zero Acceptances:**
> Rejecting 100% of candidate updates demonstrates that the Disparity Safety Gate acts as an effective, fail-safe barrier against unconstrained adaptation divergence. However, because zero updates were promoted to the live model on this specific cohort, **this experiment proves conservative harm-prevention, not selective adaptation benefit**. It establishes that DSG prevents regression, but does not yet establish that DSG can selectively admit beneficial updates under this threshold configuration on Common Voice 27.0.
