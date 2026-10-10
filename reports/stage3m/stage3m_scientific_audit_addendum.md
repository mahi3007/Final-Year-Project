# Stage 3M Scientific Audit & Forensic Reconciliation Addendum

**Protocol Version**: `v1.1.0-model-expansion`  
**Execution Date**: October 2026  
**Software Commit**: `def891b82be3f557c470a2d9eedcc4afdb1700fb`  
**Evaluation Partition**: `datasets/splits/final_test.csv` (SHA256: `a4eb01993bf746b0a0b079224f1480338de01a3b224c635fdcc97a99047285d8`)  
**Pre-Registered Safety Thresholds**: $\delta_G = 0.02$ (+2.00 pp), $\delta_D = 0.02$ (+2.00 pp) [Frozen & Unaltered]  
**Status**: Conditional Hold Addendum — Pre-requisite for Stage 4M Authorization  

---

## Executive Summary & Scientific Verdict

This document provides a formal, forensic audit addendum to the **Stage 3M Multi-Model Continual Test-Time Adaptation (CTTA) Discovery Report**, addressing all five scientific safeguards and protocol updates mandated by the research review.

### Key Audit Conclusions:
1. **P0-1 (Reproducibility Bridge Calibration)**: The numerical differences between historical Stage 3 and amended Stage 3M on `wav2vec2_base` (`ORDER_A`) have been isolated and evaluated with calibrated precision. Both experiments used `facebook/wav2vec2-base-960h` (HF commit `22aad52...`, full checkpoint state dict SHA256 `8d54633...`, initial active LayerNorm parameter hash `e28c2c6b1c568146`), the identical dataset partition (`a4eb0199...`), and identical prequential stream ordering. 
   - `no_adapt`: Evaluated in `eval()` mode; verified prediction-string equality and identical error counts (472 errors, 85.51% WER, $\Delta = 0.00$ pp).
   - `dsuta`: Exact metric concordance (471 errors, 85.33% WER, $\Delta = 0.00$ pp).
   - `suta` (+0.37 pp, +2 errors) & `dmsuta` (+0.54 pp, +3 errors): Active dropout ($p=0.10$) during `model.train()` in adaptation steps, combined with unseeded PyTorch CPU RNG advancement across sequential executions, is the **identified likely cause** of the minor word drift. We explicitly acknowledge that while train-mode versus eval-mode logits differ substantially ($\Delta_{\text{logits}} = 21.99$), proving exact two-word/three-word causality would require an exhaustive controlled permutation study.
2. **P0-2 (DMSUTA Degradation Diagnostics)**: Forensic inspection of `wav2vec2_100h / DMSUTA / ORDER_C` confirms that Window 0 transcribed 29 words (WER = 92.31%), but from Window 1 through Window 14, every hypothesis was completely empty ($L_{\text{hyp}} = 0$, 100% deletion rate across 513 words), resulting in final WER = 99.46% and Mandarin regression of +22.83 pp. While this output is empirically consistent with a potential CTC blank-token collapse, frame-level posterior distributions and gradient norms were not recorded at runtime in the original artifact. This is formally categorized as: **"Severe recognition degradation; underlying mechanism not confirmed."**
3. **P0-3 (Claim Calibration)**: Overgeneralized claims that DSUTA "consistently suppresses subgroup regression across all models" have been eliminated. Counter-evidence is explicitly documented (`data2vec_base / DSUTA / ORDER_C`, where Arabic suffered **+5.44 pp regression** despite overall WER improving by -0.73 pp). Adaptation effects are model-, method-, and stream-order-dependent.
4. **P0-4 (Stage 4M Statistical Specification & Bootstrap Caveats)**: Stage 3M cross-model comparisons are descriptive. For Stage 4M, a comprehensive Generalized Linear Mixed Model (GLMM) incorporating **Acoustic Condition** as a primary factor has been pre-registered in [`stage4m_preregistration_addendum.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage4m_preregistration_addendum.md) and syntactically validated in [`stage4m_analysis_spec_validation.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage4m_analysis_spec_validation.md). Bootstrap intervals on the $N=6$ stream represent stream-level resampling sensitivity, not population-level safety.
5. **P0-5 (Units & Verification Terminology)**: Terminology is strictly calibrated: "prediction string equality verified" is reserved for byte-verified string equivalence (`no_adapt`), and "metric concordance exact" is used for metric equivalence (`dsuta`). All 39 cells match raw inference logs.
6. **P0-6 (Speaker Overlap Audit)**: `stage4m_characterization` shares all 6 speakers with `stage3m_final_test` (overlap = 6). Therefore, **Stage 4M is an expanded-sample stress characterization ($N=12$), NOT an independent speaker validation cohort**. True independent speaker validation is preserved for the disjoint Sentinel Panel ($N=30$) and Common Voice 27 ($N=60$) evaluations.

---

## Section 1 (P0-1): Forensic Reconciliation of Historical Stage 3 and Stage 3M

### 1.1 Calibrated Comparative Matrix (`wav2vec2_base`, `ORDER_A`)

| Method | Historical WER (%) | Stage 3M WER (%) | Discrepancy ($\Delta$ pp) | Historical Errors (of 552) | Stage 3M Errors (of 552) | Error Delta | Historical Disparity $D$ (pp) | Stage 3M Disparity $D$ (pp) | Full Checkpoint SHA-256 State Dict | Active LayerNorm Hash | Divergence Interpretation | Audit Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **`no_adapt`** | 85.51% | 85.51% | **0.00 pp** | 472 | 472 | 0 | 20.65 pp | 20.65 pp | `8d54633...` (MATCH) | `e28c2c6b1c568146` (MATCH) | Deterministic inference in `eval()` mode. Exact prediction string and metric equality. | `PREDICTION_EQUALITY_VERIFIED` |
| **`suta`** | 85.14% | 85.51% | **+0.37 pp** | 470 | 472 | +2 | 19.57 pp | 21.74 pp | `8d54633...` (MATCH) | `e28c2c6b1c568146` (MATCH) | Identified likely cause: unseeded PyTorch RNG with active dropout ($p=0.10$) in `model.train()` during `adapt()`. | `REPRODUCIBILITY_LIKELY_DROPOUT_RNG_STOCHASTICITY` |
| **`dsuta`** | 85.33% | 85.33% | **0.00 pp** | 471 | 471 | 0 | 19.57 pp | 19.57 pp | `8d54633...` (MATCH) | `e28c2c6b1c568146` (MATCH) | Restorative reset controller bounded parameter drift, producing exact integer metric concordance. | `METRIC_CONCORDANCE_EXACT` |
| **`dmsuta`** | 85.51% | 86.05% | **+0.54 pp** | 472 | 475 | +3 | 20.65 pp | 21.74 pp | `8d54633...` (MATCH) | `e28c2c6b1c568146` (MATCH) | Identified likely cause: interaction between active dropout in `model.train()` and model-bank candidate selection. | `REPRODUCIBILITY_LIKELY_DROPOUT_RNG_STOCHASTICITY` |

*Machine-readable artifact*: [`reports/stage3m/stage3m_reproducibility_bridge.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage3m_reproducibility_bridge.csv)

### 1.2 Checkpoint Provenance & Uncertainty Qualification

To ensure complete provenance clarity:
- **Full Model Checkpoint Revision**: `facebook/wav2vec2-base-960h`, HuggingFace git commit hash `22aad52d435eb6dbaf354bdad9b0da84ce7d6156`.
- **Full Model State Dict Hash**: SHA-256 hash across all 212 tensors in `model.state_dict()` is `8d54633c960fea688716673a1c493d861c4a86cede21668b0f6991e2b6f8b006`.
- **Active LayerNorm Parameter Hash**: Hash across trainable affine parameters before Window 0 is `e28c2c6b1c568146`. We explicitly note that this is an active parameter hash, not a substitute for the complete checkpoint hash.
- **Uncertainty Qualification**: While our experiments demonstrated that switching from `model.eval()` to `model.train()` induces a maximum logit shift of 21.99 on identical audio, we classify this mechanism as the **identified likely cause** rather than a conclusively proven causal proof for the exact two-word (SUTA) and three-word (DMSUTA) differences.

---

## Section 2 (P0-2): Empirical Investigation of DMSUTA Recognition Degradation

### 2.1 Window-by-Window Diagnostic Trace (`wav2vec2_100h`, `DMSUTA`, `ORDER_C`)

In Stage 3M, `wav2vec2_100h / DMSUTA / ORDER_C` produced an extreme error rate ($\text{WER} = 99.46\%$, $\Delta_R = +11.42\%$, Mandarin $\Delta_{\text{Mandarin}} = +22.83\%$). A diagnostic replay and prediction audit yielded the following window metrics:

| Window ID | Primary Accent | Ref Words | Decoded Words | Window WER (%) | Substitutions | Deletions | Insertions | Parameter Drift $\|\theta_t - \theta_0\|_2$ | Selected Checkpoint |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | Hindi | 39 | 29 | **92.31%** | 26 | 10 | 0 | 0.0000 | `theta_0_anchor` |
| **1** | Hindi | 35 | 0 | **100.0%** | 0 | 35 | 0 | 0.0193 | `1eb574dc9b29d31f` |
| **2** | Hindi / Mandarin | 36 | 0 | **100.0%** | 0 | 36 | 0 | 0.0185 | `055c833f6997717c` |
| **3** | Mandarin | 38 | 0 | **100.0%** | 0 | 38 | 0 | 0.0279 | `fb5ededf34d7438d` |
| **4** | Mandarin | 36 | 0 | **100.0%** | 0 | 36 | 0 | 0.0392 | `237c642cbd0db493` |
| **5** | Arabic | 39 | 0 | **100.0%** | 0 | 39 | 0 | 0.0510 | `1c566417ce1989e4` |
| **6** | Arabic | 35 | 0 | **100.0%** | 0 | 35 | 0 | 0.0620 | `fb5ededf34d7438d` |
| **7** | Arabic / Vietnamese | 36 | 0 | **100.0%** | 0 | 36 | 0 | 0.0625 | `70a64dde81f48561` |
| **8** | Vietnamese | 38 | 0 | **100.0%** | 0 | 38 | 0 | 0.0614 | `c6d23c1e1b67ded2` |
| **9** | Vietnamese | 36 | 0 | **100.0%** | 0 | 36 | 0 | 0.0610 | `0347738cb1b52c2e` |
| **10** | Korean | 39 | 0 | **100.0%** | 0 | 39 | 0 | 0.0624 | `b8281f042145d01d` |
| **11** | Korean | 35 | 0 | **100.0%** | 0 | 35 | 0 | 0.0626 | `b63e53c5ee4ad6a3` |
| **12** | Korean / Spanish | 36 | 0 | **100.0%** | 0 | 36 | 0 | 0.0605 | `9b9187c5eb37d7d6` |
| **13** | Spanish | 38 | 0 | **100.0%** | 0 | 38 | 0 | 0.0617 | `1c566417ce1989e4` |
| **14** | Spanish | 36 | 0 | **100.0%** | 0 | 36 | 0 | 0.0614 | `f3c09b34d3285faf` |

*Machine-readable artifact*: [`reports/stage3m/stage3m_collapse_diagnostics.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage3m_collapse_diagnostics.csv)

### 2.2 Mechanism Assessment: Calibrated Formal Classification

1. **Observed Result**: Severe recognition degradation. In Window 0, the model decoded 29 words (WER = 92.31%). After adapting on Window 0, the model decoded empty strings $L_{\text{hyp}} = 0$ for all remaining 513 reference words (100% deletion rate).
2. **Plausible Interpretation**: Consistent with a potential CTC blank-token collapse.
3. **Formal Scientific Statement**:
   > *"DMSUTA exhibited severe recognition degradation under `ORDER_C`. The observed WER and 100% deletion rate are consistent with a potential CTC collapse, but the exact underlying mechanism requires additional verification."*
4. **The Disparity Paradox**: Demographic disparity dropped from $21.74 \text{ pp}$ to $3.26 \text{ pp}$ ($\Delta_D = -18.48 \text{ pp}$). Because the model failed completely across all groups, disparity contracted. This demonstrates that **$\Delta_D < 0$ does not imply improved safety when the model collapses across all groups simultaneously**.

---

## Section 3 (P0-3): Preserved Calibrated Claims

All scientific claims have been calibrated to preserve empirical rigor:
- **DSUTA Safety**:
  > *"The effects of continual adaptation were model-, method- and stream-order-dependent. DSUTA improved overall WER in several experimental conditions, but subgroup regression remained in some runs (e.g., +5.44 pp for Arabic on `data2vec_base` under `ORDER_C`). The results do not establish that any existing adaptation method is consistently safe across all tested backbones and stream orders."*
- **Entropy Minimization**:
  > *"The observed pattern is consistent with a potential mechanism involving unstable entropy-minimization updates. Confirming this explanation requires additional analysis of model states, logits and adaptation dynamics."*
- **Cross-Model Comparisons**: Labeled strictly as **descriptive**.
- **Subgroup Regression (+2.17 pp on `data2vec_base`)**: Treated as an **exploratory signal** given the single-speaker-per-group sample size ($N=6$).

---

## Section 4 (P0-4): Frozen Stage 4M Statistical Model & Speaker Overlap

### 4.1 Stage 4M Preregistered Statistical Specification
The Stage 4M statistical analysis model incorporates **Acoustic Condition** as a primary factor alongside Model, Method, Order, and Speaker clustering:

$$E_{i,s,m,j,o,c} \sim \operatorname{NegativeBinomial}(\mu_{i,s,m,j,o,c}, \phi)$$

$$\begin{aligned}
\log \mu_{i,s,m,j,o,c} ={}& \log N_i + \beta_0 \\
&{}+ \beta_m^{\text{Model}} + \beta_j^{\text{Method}} + \beta_c^{\text{Condition}} + \beta_o^{\text{Order}} \\
&{}+ (\beta\beta)_{mj}^{\text{Model} \times \text{Method}} + (\beta\beta)_{jc}^{\text{Method} \times \text{Condition}} + (\beta\beta)_{jo}^{\text{Method} \times \text{Order}} \\
&{}+ b_s + b_i
\end{aligned}$$

- Complete preregistration details: [`reports/stage3m/stage4m_preregistration_addendum.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage4m_preregistration_addendum.md)
- Syntax and convergence validation: [`reports/stage3m/stage4m_analysis_spec_validation.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage4m_analysis_spec_validation.md)
- **$K$-Sweep Rule**: Window sizes $K \in \{1, 4, 5, 10\}$ are evaluated exclusively as a secondary sensitivity experiment on clean audio and will never be silently pooled with the primary $K=4$ acoustic stress matrix.
- **Seq2Seq Rule**: Whisper models are evaluated strictly as static controls (`no_adapt`) and are not included in adaptation-method interactions.

### 4.2 Speaker Overlap Disclosure
- All 6 Stage 3M speakers overlap with the 12-speaker Stage 4M cohort.
- **Appropriate Description**: Stage 4M is an **expanded-sample acoustic-stress characterization ($N=12$), NOT an independent speaker validation cohort**.
- True independent speaker validation is preserved for the disjoint Sentinel Panel ($N=30$) and Common Voice 27 ($N=60$) evaluations.
- Bootstrap replicates ($B=1000$) measure resampling sensitivity under their assumptions and do not create independent speakers.

---

## Section 5 (P0-5): Terminology & Unit Verification

1. **Terminology Rules Enforced**:
   - "Prediction string equality verified" is used strictly where character-by-character string equality was checked (`no_adapt`).
   - "Exact metric concordance" is used where aggregate metrics match identically (`dsuta`).
2. **Units Standard**:
   - WER (%) and CER (%): Percentages.
   - Disparity $D$ (pp): Percentage points.
   - All deltas ($\Delta_R, \Delta_D, \Delta_g$): Percentage points (pp).
   - All 39 cells in `stage3m_full_results.csv` match raw predictions to within $10^{-6}$.

---

## Section 6: GO / NO-GO Recommendation for Stage 4M

### Recommendation: **GO (Ready for Authorization)**
All protocol corrections, preregistration addenda, convergence checks, and wording calibrations are complete. Stage 4M execution should proceed strictly according to the frozen statistical model.

### Remaining Unresolved Risks to Monitor in Stage 4M:
1. **Convergence of Crossed Random Effects**: If crossed random effects ($b_s, b_i$) fail on empirical Stage 4M counts, the pipeline must strictly follow the Level 2/3 fallback tree (speaker-only random intercept or Poisson with cluster-robust covariance).
2. **CTC Collapse Re-occurrence**: Stage 4M must record frame-level blank token probability statistics and gradient norms per window to directly capture the onset of recognition degradation if it re-occurs under acoustic stress.
3. **Small Sample Uncertainty**: Even with $N=12$ speakers (2 per group), group-level estimates remain subject to substantial sampling variability.
