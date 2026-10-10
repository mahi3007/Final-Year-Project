# Stage 4M Multi-Model Acoustic Stress & Boundary Characterization Report
## Post-Execution Scientific Audit Edition

**Protocol Version**: `v1.1.0-model-expansion`  
**Execution Standard**: ADR-005  
**Review Status**: Execution Completed Under Authorized Frozen Protocol (GO)  
**Audit Status**: Post-Execution Scientific Audit Verified  
**Recommendation**: **HOLD** — Mandatory pause prior to Stage 5M candidate deployment review.

---

## 1. Executive Summary & Headline Benchmarks

This report documents the empirical and statistical results of the preregistered **Stage 4M Multi-Model Experimental Suite** following post-execution scientific audit. In accordance with ADR-005, all experiments were executed without altering frozen safety tolerances ($\epsilon_R = 0.00\text{ pp}$, $\epsilon_G = +2.00\text{ pp}$, $\epsilon_D = +2.00\text{ pp}$, $B = 1000$, $\alpha = 0.05$).

The evaluation encompasses:
1. **Primary CTC Factorial Matrix**: 3 self-supervised acoustic backbones (`wav2vec2_base`, `data2vec_base`, `wav2vec2_100h`) evaluated across 4 adaptation methods (`no_adapt`, `suta`, `dsuta`, `dmsuta`), 3 prequential stream permutations (`ORDER_A`, `ORDER_B`, `ORDER_C`), and 5 acoustic conditions (`clean`, `noise_15db`, `noise_5db`, `babble_15db`, `reverb_t60_04`). This yields **180 nominal factorial cells** and **150 canonical settings** (18,000 canonical evaluation records generated from 120 source utterances evaluated across the 150 canonical settings).
2. **Seq2Seq Static Portability Controls**: 3 autoregressive encoder-decoder architectures (`whisper_base`, `distil_whisper_small`, `whisper_tiny`) evaluated in static no-adapt mode across the 5 acoustic conditions on `ORDER_A` (**15 control cells**, 1,800 evaluation records).
3. **Prequential Window Granularity Sweep ($K$-Sweep)**: Window sizes $K \in \{2, 8\}$ evaluated secondary to standard $K=4$ for `wav2vec2_base` + SUTA across 3 acoustic conditions (**6 sensitivity cells**, 720 evaluation records, classified as **exploratory sensitivity analysis**).
4. **Primary Retrospective Safety Assessment (Analysis A)**: 135 active test-time adapting settings evaluated via Stratified Paired Speaker-Cluster Bootstrap ($B=1000$) against the canonical `no_adapt` baseline on `ORDER_A`.
5. **Secondary Omnibus Characterization (Analysis B)**: Full negative-binomial mixed-effects GLMM under Laplace marginal approximation ($p=34$ estimable parameters on 18,000 canonical evaluation records), contrasted against the 36-parameter duplicated sensitivity design (21,600 records).

---

### 1.1 Table 1A: Canonical Static Baseline Benchmark (No-Adapt, ORDER_A)
*Exact Estimand: Static baseline performance evaluated without test-time adaptation on `ORDER_A`.*  
*Evaluation Cohort: 120 utterances, 12 speaker clusters, $N_{\text{ref}} = 1,104$ reference words per cell.*  
*Units: Word Error Rate (WER) in percent (%); Disparity $D = \max_g \text{WER}_g - \min_g \text{WER}_g$ in percentage points (pp).*

| Architecture Family | Model Backbone | Parameter Count | Clean (WER % / $D$ pp) | Noise 15dB (WER % / $D$ pp) | Noise 5dB (WER % / $D$ pp) | Babble 15dB (WER % / $D$ pp) | Reverb $T_{60}=0.4\text{s}$ (WER % / $D$ pp) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CTC (Self-Supervised)** | `wav2vec2_base` | 95.0M | 87.86% / 8.15 pp | 93.12% / 10.87 pp | 98.01% / 5.98 pp | 94.02% / 7.61 pp | 93.48% / 8.15 pp |
| **CTC (Self-Supervised)** | `data2vec_base` | 93.8M | **83.79%** / 13.59 pp | **92.12%** / 11.96 pp | 98.19% / 4.89 pp | **93.21%** / 11.41 pp | **91.39%** / 7.61 pp |
| **CTC (Low-Resource)** | `wav2vec2_100h` | 95.0M | 87.86% / 8.70 pp | 94.47% / 11.96 pp | 99.00% / 12.50 pp | 97.83% / 11.41 pp | 95.83% / 7.61 pp |
| **Seq2Seq (Control)** | `distil_whisper_small` | 166.0M | **80.43%** / 8.70 pp | **85.87%** / 14.13 pp | 101.54% / 20.65 pp | **87.77%** / 10.33 pp | **86.50%** / 13.04 pp |
| **Seq2Seq (Control)** | `whisper_base` | 74.0M | 88.86% / 13.04 pp | 97.64% / 9.78 pp | 113.77% / 18.48 pp | 93.66% / 5.43 pp | 95.38% / 13.59 pp |
| **Seq2Seq (Control)** | `whisper_tiny` | 39.0M | 95.38% / 20.11 pp | 101.81% / 16.85 pp | 113.13% / 40.22 pp | 101.27% / 16.85 pp | 105.53% / 25.54 pp |

---

### 1.2 Table 1B: Factorial Adaptation Macro-Average Benchmark
*Exact Estimand: Macro-average of cell-level corpus WER and disparity across all 12 nominal stream runs for CTC models (4 methods $\times$ 3 orders = 1,440 evaluation records per cell group, 13,248 total reference words) versus single static baseline run for Seq2Seq controls.*  
*Units: Word Error Rate (WER) in percent (%); Disparity $D$ in percentage points (pp).*

| Architecture Family | Model Backbone | Parameter Count | Clean (WER % / $D$ pp) | Noise 15dB (WER % / $D$ pp) | Noise 5dB (WER % / $D$ pp) | Babble 15dB (WER % / $D$ pp) | Reverb $T_{60}=0.4\text{s}$ (WER % / $D$ pp) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CTC (Self-Supervised)** | `wav2vec2_base` | 95.0M | 87.64% / 7.52 pp | 92.96% / 10.51 pp | 98.22% / 5.30 pp | 94.06% / 7.11 pp | 93.73% / 8.11 pp |
| **CTC (Self-Supervised)** | `data2vec_base` | 93.8M | **83.61%** / 11.23 pp | **91.93%** / 11.64 pp | 98.65% / 4.17 pp | **93.10%** / 11.19 pp | **90.86%** / 7.56 pp |
| **CTC (Low-Resource)** | `wav2vec2_100h` | 95.0M | 87.54% / 7.75 pp | 94.24% / 13.00 pp | 98.47% / 11.64 pp | 97.00% / 10.37 pp | 95.18% / 7.16 pp |
| **Seq2Seq (Control)** | `distil_whisper_small` | 166.0M | **80.43%** / 8.70 pp | **85.87%** / 14.13 pp | 101.54% / 20.65 pp | **87.77%** / 10.33 pp | **86.50%** / 13.04 pp |
| **Seq2Seq (Control)** | `whisper_base` | 74.0M | 88.86% / 13.04 pp | 97.64% / 9.78 pp | 113.77% / 18.48 pp | 93.66% / 5.43 pp | 95.38% / 13.59 pp |
| **Seq2Seq (Control)** | `whisper_tiny` | 39.0M | 95.38% / 20.11 pp | 101.81% / 16.85 pp | 113.13% / 40.22 pp | 101.27% / 16.85 pp | 105.53% / 25.54 pp |

---

## 2. Model Architecture Comparison & Error Decomposition

### 2.1 Clean Acoustics vs. Severe Degradation
- **Clean Acoustics**: `distil_whisper_small` demonstrates superior baseline transcription accuracy in clean speech ($\text{WER} = 80.43\%$), outperforming `data2vec_base` ($83.79\%$) and `wav2vec2_base` ($87.86\%$). This reflects strong language model priors learned during large-scale sequence-to-sequence pretraining.
- **Severe Noise ($5\text{ dB}$ SNR)**: Severe acoustic noise substantially degrades ASR performance across all evaluated models. Both Seq2Seq controls exceed $100\%$ WER (`distil_whisper_small` = $101.54\%$, `whisper_base` = $113.77\%$, `whisper_tiny` = $113.13\%$), indicating that total edit distance exceeds the reference word count.

### 2.2 Empirical Error Decomposition (Substitutions, Deletions, Insertions)
To evaluate the precise failure mechanisms rather than speculating on qualitative causes, we analyzed the edit distance composition and hypothesis-to-reference length ratio ($L_{\text{hyp}} / L_{\text{ref}}$) recorded in [`results/stage4_multimodel/stage4m_error_decomposition_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage4_multimodel/stage4m_error_decomposition_audit.csv):

### Table 2: Error Decomposition: Clean vs. Severe Noise ($5\text{ dB}$)
*Evaluated on static baseline runs ($N_{\text{ref}} = 1,104$ reference words, 120 utterances).*

| Model Backbone | Acoustic Condition | Hyp Words | Length Ratio $L_{\text{hyp}}/L_{\text{ref}}$ | Substitutions ($S$) | Deletions ($D$) | Insertions ($I$) | Total Edits ($S+D+I$) | Corpus WER (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` (CTC) | Clean | 1,036 | 0.9384 | 768 | 135 | 67 | 970 | 87.86% |
| `wav2vec2_base` (CTC) | Noise 5dB | 476 | **0.4312** | 428 | **640** | 14 | 1,082 | 98.01% |
| `data2vec_base` (CTC) | Clean | 1,050 | 0.9511 | 719 | 130 | 76 | 925 | 83.79% |
| `data2vec_base` (CTC) | Noise 5dB | 265 | **0.2400** | 239 | **842** | 3 | 1,084 | 98.19% |
| `wav2vec2_100h` (CTC) | Clean | 1,063 | 0.9629 | 781 | 115 | 74 | 970 | 87.86% |
| `wav2vec2_100h` (CTC) | Noise 5dB | 811 | **0.7346** | 744 | **321** | 28 | 1,093 | 99.00% |
| `distil_whisper_small` (Seq2Seq) | Clean | 1,148 | 1.0399 | 692 | 76 | 120 | 888 | 80.43% |
| `distil_whisper_small` (Seq2Seq) | Noise 5dB | 1,190 | **1.0779** | 809 | 113 | **199** | 1,121 | **101.54%** |
| `whisper_base` (Seq2Seq) | Clean | 1,140 | 1.0326 | 757 | 94 | 130 | 981 | 88.86% |
| `whisper_base` (Seq2Seq) | Noise 5dB | 1,240 | **1.1232** | 864 | 128 | **264** | 1,256 | **113.77%** |
| `whisper_tiny` (Seq2Seq) | Clean | 1,131 | 1.0245 | 754 | 136 | 163 | 1,053 | 95.38% |
| `whisper_tiny` (Seq2Seq) | Noise 5dB | 1,170 | **1.0598** | 841 | 171 | **237** | 1,249 | **113.13%** |

### Key Mechanistic Findings
1. **CTC Models Suffer From Deletion Collapse**:
   Under severe noise ($5\text{ dB}$), CTC models experience a collapse in hypothesis length: length ratio drops to **0.2400** in `data2vec_base` and **0.4312** in `wav2vec2_base`. Deletions explode from ~130 to **842** (data2vec) and **640** (wav2vec2). When acoustic representations are obscured by severe noise, CTC confidence falls below threshold and predominantly outputs the blank token `[pad]`, causing massive deletions rather than insertions (insertions drop to 3–14 words).
2. **Seq2Seq Models Suffer From Insertion Explosion**:
   In contrast, Seq2Seq autoregressive decoding maintains or expands hypothesis length ($L_{\text{hyp}} / L_{\text{ref}} = 1.0779\text{ to }1.1232$). Deletions remain modest (113–171), but **insertions explode to 199–264 words** (more than doubling clean insertion counts).
3. **Hypothesis vs. Established Cause**:
   The empirical data establishes that Seq2Seq WER exceeding $100\%$ is directly driven by **insertion inflation** and length expansion. However, whether these insertions represent ungrounded phonetic hallucination, repetitive loop artifacts, or language-model runaway generation remains an unproven hypothesis that requires explicit token n-gram analysis and decoder attention visualization.

---

## 3. Disparity Compression: Lower Disparity Does Not Indicate Safer Recognition

A central finding of Stage 4M is the empirical demonstration of **Disparity Compression**:

$$\boxed{\Delta_D < 0 \ \not\Rightarrow\ \text{Improved System Safety}}$$

Consider the empirical trajectories:
- **`wav2vec2_base`**: Clean baseline WER = 87.86%, Disparity = 8.15 pp $\longrightarrow$ Noise 5dB WER = 98.01%, Disparity = **5.98 pp** (Disparity drops by $-2.17\text{ pp}$ while WER deteriorates by $+10.15\text{ pp}$).
- **`data2vec_base`**: Clean baseline WER = 83.79%, Disparity = 13.59 pp $\longrightarrow$ Noise 5dB WER = 98.19%, Disparity = **4.89 pp** (Disparity drops by $-8.70\text{ pp}$ while WER deteriorates by $+14.40\text{ pp}$).

### Scientific Explanation
Disparity $D = \max_g \text{WER}_g - \min_g \text{WER}_g$ measures relative differences between speaker demographic strata. When acoustic corruption becomes severe, error rates saturate near 100% across all speaker groups. Consequently, between-group variance compresses toward zero. A system that performs catastrophically for every group exhibits smaller disparity than a system that performs well overall.

This underscores the strict necessity of ADR-005's **tripartite** safety gate: disparity ($\Delta_D$) must never be evaluated in isolation without joint enforcement of overall risk ($\Delta_R$) and maximum subgroup regression ($\max_g \Delta_g$).

---

## 4. Retrospective Safety Assessment (Analysis A) vs. Operational DSG Controller

To eliminate ambiguity between post-hoc research analysis and online controller decisions, we formally distinguish the two processes:

1. **Operational Online DSG Controller (Stage 5M Architecture)**:
   - Evaluates candidate parameter updates at each streaming window during live test-time adaptation.
   - Evaluates updates exclusively against the designated, label-isolated **Sentinel Panel** ($N=30$, `datasets/splits/sentinel_panel.csv`).
   - Does **not** have access to test stream ground-truth reference transcripts.
2. **Primary Retrospective Safety Assessment (Stage 4M Analysis A)**:
   - Evaluates completed experimental runs post-hoc against the actual Stage 4M reference transcripts.
   - Purpose: To characterize whether unconstrained test-time adaptation runs satisfied the tripartite safety criteria in retrospect.
   - All 135 decisions reported below are **Retrospective Safety Classifications**, documented in [`results/stage4_multimodel/stage4m_retrospective_vs_operational_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage4_multimodel/stage4m_retrospective_vs_operational_audit.csv).

```
Total Active Adapting Settings Evaluated:  135
├── Retrospective ACCEPT Classifications:   20 (14.8%)
└── Retrospective REJECT Classifications:  115 (85.2%)
```

### Table 3: Breakdown of Retrospective Safety Classifications

| Retrospective Outcome / Violation Category | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **Retrospective ACCEPT** | 20 | 14.8% | All 3 upper confidence bounds satisfied ($\text{UCB}_{95}(\Delta_R) \le 0.00\text{ pp}$, $\text{UCB}_{95}(\max_g \Delta_g) \le 2.00\text{ pp}$, $\text{UCB}_{95}(\Delta_D) \le 2.00\text{ pp}$). |
| **Triple Bound Violation ($\Delta_R \wedge \Delta_G \wedge \Delta_D$)** | 48 | 35.6% | Candidate failed overall risk, subgroup regression, and disparity bounds simultaneously. |
| **Disparity Growth Only ($\text{UCB}_{95}(\Delta_D) > 2.00\text{ pp}$)** | 15 | 11.1% | Candidate widened the gap between best- and worst-performing speaker subgroups. |
| **Joint Disparity & Subgroup Violation** | 12 | 8.9% | Candidate widened disparity while simultaneously degrading protected group performance. |
| **Subgroup Regression Only ($\text{UCB}_{95}(\max_g \Delta_g) > 2.00\text{ pp}$)** | 5 | 3.7% | Protected subgroup performance degraded despite aggregate stability. |
| **Overall Risk Only ($\text{UCB}_{95}(\Delta_R) > 0.00\text{ pp}$)** | 4 | 3.0% | Overall Word Error Rate increased. |
| **Other Compound Violations** | 31 | 23.0% | Pairwise combinations of boundary exceedances. |

### Interpretation
In 115 out of 135 evaluated active-adaptation settings, the completed runs failed at least one of the preregistered safety criteria when evaluated against reference transcripts. This indicates that unconstrained adaptation frequently compromises subgroup performance. The 20 accepted settings cluster in clean and reverberation conditions under D-SUTA and DM-SUTA. Under severe noise ($5\text{ dB}$), **100% of adapting settings were rejected**.

---

## 5. Secondary Omnibus Mixed-Effects GLMM (Analysis B) & Variance Diagnosis

The secondary mixed-effects model was fit using negative-binomial regression (NB2 parameterization) under Laplace marginal approximation.

### 5.1 Parameter Estimates & Sensitivity Comparison
- **Canonical 34-Parameter Specification ($N = 18,000$ canonical records across 150 settings)**:
  - Column rank: **34** (Full Rank), Condition Number: $\kappa = 48.388$
  - Estimated Overdispersion: $\hat{\phi} = 143.9554$
  - Speaker Random Intercept SD: $\hat{\sigma}_s = 0.0042$
  - Utterance Random Intercept SD: $\hat{\sigma}_u = 0.2265$
  - Fit duration: $1.19\text{ seconds}$
- **Duplicated 36-Parameter Specification ($N = 21,600$ records across 180 settings)**:
  - Estimated Overdispersion: $\hat{\phi} = 144.0748$ ($\Delta \phi = 0.1194$)
  - Speaker Random Intercept SD: $\hat{\sigma}_s = 0.0062$ ($\Delta \sigma_s = 0.0020$)
  - Utterance Random Intercept SD: $\hat{\sigma}_u = 0.2260$ ($\Delta \sigma_u = 0.0006$)

### 5.2 Variance Component Diagnostic Findings
1. **Interpretation of Large Dispersion $\hat{\phi} = 143.96$**:
   Under the NB2 variance function $\operatorname{Var}(Y) = \mu + \mu^2 / \phi$, when $\phi$ is large, the quadratic overdispersion term $\mu^2 / \phi$ is small. This indicates that overdispersion beyond the Poisson variance is modest once utterance-level random effects ($\hat{\sigma}_u = 0.2265$) and fixed-effect interactions are accounted for.
2. **Near-Zero Speaker Variance $\hat{\sigma}_s = 0.0042$**:
   - Diagnostic analysis of the raw empirical data reveals that the standard deviation of speaker-level mean log error rate across the 12 speaker clusters is only **0.0338** (empirical speaker mean WER ranges from $0.8872$ to $0.9962$).
   - In contrast, the standard deviation across the 120 utterance items is **0.1730** (ranging from $0.2745$ to $1.3741$), over **5 times larger**.
   - Because the 12 speaker clusters are balanced and homogeneous relative to the huge variation in utterance difficulty, once utterance random intercepts ($\hat{\sigma}_u = 0.2265$) and fixed effects ($p=34$) absorb systematic variation, residual speaker variance is small.
   - The Hessian at the optimum is strictly positive definite, confirming a stable interior estimate rather than a boundary collapse.
3. **Finite-Sample Uncertainty Disclosure**:
   The secondary GLMM serves strictly as an omnibus descriptive characterization; primary safety decisions are governed exclusively by the non-parametric speaker-clustered paired bootstrap (Analysis A).

---

## 6. Diagnostic Evaluation: Empty Hypotheses & Outliers

1. **Zero Empty Hypotheses**:
   **Zero empty hypotheses were observed among the 18,000 canonical CTC evaluation records** (`empty_hypotheses_count = 0` across all 150 settings).
   - *Precision Note*: These 18,000 evaluation records represent repeated evaluations of a curated cohort of 120 source utterances across the 150 canonical factorial settings.
   - *Failure Mode Note*: The absence of empty transcripts indicates that complete blank-label collapse did not occur. However, as demonstrated in Section 2, severe acoustic noise ($5\text{ dB}$) still produces near-complete deletion collapse with length ratios falling to 0.24–0.43 and WER approaching 99%.
2. **Severe WER Outliers ($\text{WER} > 1.0$)**:
   - Severe WER counts occur primarily due to insertion bursts:
     - `clean`: 774 records
     - `reverb_t60_04`: 696 records
     - `babble_15db`: 568 records
     - `noise_15db`: 402 records
     - `noise_5db`: 146 records
   - In severe noise ($5\text{ dB}$), deletions dominate over insertions, reducing the frequency of $\text{WER} > 1.0$ outliers as models truncate hypotheses.

---

## 7. $K$-Sweep Sensitivity Analysis & Protocol Reconciliation

### 7.1 Protocol Reconciliation & Classification
- **Historical Preregistration**: The original Stage 4 calibration sweep evaluated $K \in \{1, 4, 5, 10\}$ on an 80-utterance split.
- **Stage 4M Execution**: In the Stage 4M Preregistration Addendum line 34, an exploratory sensitivity check of $K \in \{2, 4, 8\}$ was documented for buffer size sensitivity on 120 utterances. Because no formal confirmatory amendment was executed, **$K \in \{2, 4, 8\}$ is formally classified as an exploratory sensitivity check**, documented in [`results/stage4_multimodel/stage4m_k_sweep_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage4_multimodel/stage4m_k_sweep_audit.csv).
- **Confirmatory Status**: The $K$-sweep results are exploratory only and do not constitute confirmatory proof of optimality.

### Table 4: Exploratory $K$-Sweep Sensitivity Results (`wav2vec2_base` + SUTA, ORDER_A)
*Evaluation Cohort: 120 utterances, 12 speakers, $N_{\text{ref}} = 1,104$ reference words.*  
*Units: Word Error Rate (WER) in percent (%); Disparity $D$ in percentage points (pp).*

| Acoustic Condition | Window Size $K$ | Total Windows | Corpus WER (%) | Disparity $D$ (pp) | Protocol Classification |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `clean` | $K=2$ | 60 | 86.78% | 9.78 pp | Exploratory Sensitivity |
| `clean` | **$K=4$** | **30** | **87.50%** | **8.15 pp** | **Canonical Benchmark ($K=4$)** |
| `clean` | $K=8$ | 15 | 87.77% | 8.15 pp | Exploratory Sensitivity |
| `noise_5db` | $K=2$ | 60 | 98.55% | 6.52 pp | Exploratory Sensitivity |
| `noise_5db` | **$K=4$** | **30** | **98.46%** | **3.80 pp** | **Canonical Benchmark ($K=4$)** |
| `noise_5db` | $K=8$ | 15 | 98.19% | 4.89 pp | Exploratory Sensitivity |
| `reverb_t60_04` | $K=2$ | 60 | 93.84% | 9.24 pp | Exploratory Sensitivity |
| `reverb_t60_04` | **$K=4$** | **30** | **94.11%** | **7.07 pp** | **Canonical Benchmark ($K=4$)** |
| `reverb_t60_04` | $K=8$ | 15 | 94.02% | 8.15 pp | Exploratory Sensitivity |

*(Note: For `wav2vec2_base` clean, the static No-Adapt baseline is 87.86% ($D = 8.15\text{ pp}$), the standard SUTA run on ORDER_A at $K=4$ is 87.50% ($D = 8.15\text{ pp}$), and the macro-average across all 12 nominal clean cells is 87.64% ($D = 7.52\text{ pp}$).)*

---

## 8. Principal Conclusions & Architectural Recommendation

Based on the completed Stage 4M multi-model execution and post-execution audit:

1. **Acoustic Stress Produces Substantial Recognition Degradation**: Both self-supervised CTC and autoregressive Seq2Seq models experience severe degradation under acoustic noise, with $5\text{ dB}$ noise yielding near-complete recognition collapse.
2. **Error Mechanics Differ Substantially by Architecture**: CTC models collapse via **massive deletions** and hypothesis truncation ($L_{\text{hyp}} / L_{\text{ref}} \approx 0.24\text{--}0.43$), whereas Seq2Seq models collapse via **massive insertion bursts** ($L_{\text{hyp}} / L_{\text{ref}} > 1.07$), pushing WER above 100%.
3. **Disparity Compresses Under Catastrophic Performance**: Smaller demographic disparity under severe noise is an artifact of universal saturation, demonstrating that $\Delta_D < 0$ does not imply system safety without joint bound enforcement.
4. **Retrospective Safety Classifications Frequently Fail**: In 115 of 135 evaluated active-adaptation settings (85.2%), the completed adaptation runs failed at least one frozen safety criterion, motivating conservative risk gating.
5. **Absence of Empty Hypotheses Does Not Negate Recognition Failure**: Zero empty hypotheses were observed among the 18,000 evaluation records, but this does not prevent catastrophic 98–99% WER.

### Architectural Decision: HOLD
In compliance with project governance:
- **Stage 5M (Closed-Loop Online Control) remains on HOLD**.
- No candidate models or online adaptation controllers are authorized for deployment to Stage 5M pending formal stakeholder review of these audited Stage 4M results.

---
*Report audited and certified in compliance with ADR-005 and protocol v1.1.0-model-expansion.*
