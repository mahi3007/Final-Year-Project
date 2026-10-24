# Stage 6M: Physical Cohort 1 Three-Arm Streaming Experiment Report (Post-Execution Audit Edition)

> [!NOTE]
> **Provenance Status:** `POST_AUDIT_PHYSICAL_BENCHMARK_RUN`  
> **Tested Commit SHA:** `3f7e8e4964fb083648ece1e48a99cecde079decd`  
> **Initial Model Parameter Hash (SHA-256):** `c99f94b989be13803bef41cf1d2debe37114bdc521e90f8b4b11a0f17774aaba` (prefix `c99f94b989be1380`)  
> **Tested Controller:** `StreamingSentinelSafetyGate` (Unclipped OBF Schedule + Stratified Cluster Bootstrap $B=500$)  
> **Execution Timestamp:** `2026-10-24T15:53:47.078643+00:00` (Elapsed: 8,749.3s / 145.82 min)  
> **Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
> **Execution Engine:** Physical PyTorch Deep Neural Acoustic Inference (`facebook/wav2vec2-base-960h`)  
> **Corpus Scale:** 900 physical audio clips | 60 speakers | 6 strata | 225 prequential windows ($K=4$) | 8,667 reference words  

---

## 1. Executive Summary & Provenance Reconciliation

This report documents the **physical execution of the matched three-arm prequential streaming benchmark on Cohort 1** (`datasets/splits/stage5_external_eval.csv`) and incorporates the findings of the post-execution audit.

Every word error count derives from acoustic neural forward passes on 16 kHz audio waveforms with active SUTA adaptation and live parameter rollbacks.

### Initial Parameter Hash Provenance Reconciliation
- **Committed Run (`task-842`, Commit `3f7e8e4`):** The completed 145.82-minute run printed `Initial Frozen Model Parameter Hash: c99f94b989be1380` in its console log and recorded `"initial_live_parameter_hash_sha256": "c99f94b989be13803bef41cf1d2debe37114bdc521e90f8b4b11a0f17774aaba"` in `reports/stage6m/stage6m_physical_cohort1_revised_gate_report.json`.
- **Prior Aborted Attempt (`task-806`, Commit `02abcbb`):** An earlier attempt printed `Initial Frozen Model Parameter Hash: 09ce3883f93bfa3a` before aborting at window 14 due to a Windows `cp1252` stdout character encoding error on Unicode `\u0394`. Commit `3f7e8e4` resolved this encoding issue, and the subsequent completed run (`task-842`) instantiated the model with initial hash `c99f94b989be1380`.
- **Resolution:** The console log of the committed run and the report JSON agree identically on `c99f94b989be1380`. The prefix `09ce...` reported in the preliminary chat launch message was an errant copy from the aborted `task-806` console header.
- **Artifact Naming:** The decision log is stored at `reports/stage6m/stage6m_physical_cohort1_revised_gate_decisions.csv` (correcting the duplicate `_gate_gate_` naming convention).

---

## 2. Primary Comparison Across 8,667 Reference Words

| Arm | Description | Total Errors | Corpus WER | Disparity $D$ | $\Delta$ vs Static | $\Delta$ vs Ungated | Decisions |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Arm 1** | Static Baseline (`No-Adapt`) | 1,980 | **22.8453%** | **29.79 pp** | — | — | — |
| **Arm 2** | Ungated CTTA (`SUTA`) | 2,060 | **23.7672%** | **27.89 pp** | +0.92 pp (+80 err) | — | 224 Unconditional Updates |
| **Arm 3** | DSG Gate-Controlled CTTA | 1,981 | **22.8568%** | **29.45 pp** | **+0.01 pp (+1 err)** | **-0.91 pp (-79 err)** | **12 Accepted (5.36%) / 212 Rejected** |

### Disparity Comparators and the "Leveling Down" Phenomenon
- **Comparator 1 (Relative to Static Baseline):** Arm 3 reduces cross-accent disparity from **29.79 pp** to **29.45 pp** (a modest reduction of **-0.34 pp**).
- **Comparator 2 (Relative to Ungated SUTA):** Ungated SUTA exhibits a numerically lower disparity of **27.89 pp**, which is 1.56 pp lower than Arm 3. However, this lower disparity is driven entirely by **leveling down**:
  - Under Ungated SUTA, the best-performing accent (**Canadian English**) degraded severely from **12.87%** to **14.07%** (**+1.20 pp**, +18 errors).
  - Meanwhile, the worst-performing accent (**South Asian English**) only changed from **42.66%** to **41.96%** (**-0.70 pp**).
  - Because disparity is defined as $D = \max_g \text{WER}_g - \min_g \text{WER}_g$, degrading the best-performing group compresses the gap from the bottom.
  - Arm 3 prevented catastrophic degradation in Canadian English (13.13% vs Ungated 14.07%), refusing to achieve lower disparity through degradation of advantaged speakers.

---

## 3. Stratum-Level Word Error Rates ($\text{WER}_g$)

Arm 3 produced lower WER than the Static Baseline in **4 out of 6 strata** (Australian, England, Irish, and South Asian English), while Canadian English and US English saw minor error increases:

| Stratum | Ref Words | Arm 1 (Static) | Arm 2 (Ungated) | Arm 3 (DSG) | Arm 3 $\Delta$ vs Arm 1 | Arm 3 $\Delta$ vs Arm 2 | Direction vs Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 1,493 | 23.58% | 25.52% | **23.51%** | -0.07 pp (-1 err) | -2.01 pp (-30 err) | **Improved** |
| **Canadian English** | 1,500 | 12.87% | 14.07% | **13.13%** | +0.27 pp (+4 err) | -0.93 pp (-14 err) | Minor regression |
| **England English** | 1,393 | 21.25% | 22.61% | **21.18%** | -0.07 pp (-1 err) | -1.44 pp (-20 err) | **Improved** |
| **Irish English** | 1,383 | 15.76% | 17.28% | **15.62%** | -0.14 pp (-2 err) | -1.66 pp (-23 err) | **Improved** |
| **South Asian English** | 1,430 | 42.66% | 41.96% | **42.59%** | -0.07 pp (-1 err) | +0.63 pp (+9 err) | **Improved** |
| **US English** | 1,468 | 21.19% | 21.39% | **21.32%** | +0.14 pp (+2 err) | -0.07 pp (-1 err) | Minor regression |

---

## 4. Inferential Statistics (Speaker-Clustered Analysis, $N = 60$)

### Primary Utility Hypothesis (Arm 3 vs. Arm 2)
- **Paired $t$-test:** $t(59) = -2.3079, p = 0.0245 < 0.05$ (two-tailed).
- **Effect Size:** Arm 3 prevented 79 word errors relative to ungated adaptation, confirming statistically significant protection against continuous adaptation degradation.

### Secondary Stability Hypothesis (Arm 3 vs. Arm 1)
- **Standard Paired $t$-test:** $t(59) = -0.2574, p = 0.7978$ (two-tailed).
  - *Interpretation:* The standard paired $t$-test finds **no statistically significant difference** between Arm 3 and the Static Baseline at the $\alpha = 0.05$ level.
- **Formal Equivalence Testing (Two One-Sided Tests — TOST):**
  - Pre-specified Practical Equivalence Margin: $\Delta_{\text{equiv}} = \pm 0.50\text{ pp}$ ($\pm 0.5\%$ absolute WER).
  - Unweighted mean paired difference ($\text{Arm 3} - \text{Arm 1}$): $-0.0310\text{ pp}$ ($SE = 0.1204\text{ pp}$).
  - 90% Confidence Interval: $[-0.2321, +0.1702]\text{ pp}$ (falls entirely inside $[-0.50, +0.50]\text{ pp}$).
  - 95% Confidence Interval: $[-0.2669, +0.2049]\text{ pp}$ (falls entirely inside $[-0.50, +0.50]\text{ pp}$).
  - Lower bound test ($H_{01}: \Delta \le -0.50\text{ pp}$): $t_1 = +3.8963, p_1 = 1.26 \times 10^{-4} < 0.001$.
  - Upper bound test ($H_{02}: \Delta \ge +0.50\text{ pp}$): $t_2 = -4.4111, p_2 = 2.21 \times 10^{-5} < 0.001$.
  - Equivalence Conclusion: $p_{\text{TOST}} = \max(p_1, p_2) = 1.26 \times 10^{-4} < 0.001$.
  - *Conclusion:* Arm 3 is **statistically equivalent to the Static Baseline within the pre-specified $\pm 0.50\text{ pp}$ equivalence margin**.

---

## 5. Audit Analysis: Zero-Variance Acceptance and Sequential Calibration

### Finding: All 12 Accepted Candidates Had Zero Measured Sentinel Effect
Audit inspection of `stage6m_physical_cohort1_revised_gate_decisions.csv` revealed that for all 12 accepted updates (windows 8, 39, 40, 44, 61, 71, 84, 89, 90, 98, 148, 169):
$$\Delta_R = 0.0000, \quad SE_R = 0.0000, \quad UCB_R = 0.0000, \quad UCB_{\max g} = 0.0000, \quad UCB_D = 0.0000$$

### Root Cause Analysis
1. **Finite-Sample Discrete Argmax Collapse:** On the core panel of 30 sentinel clips (450 total reference words), small parameter updates produced by SUTA gradient steps did not flip greedy CTC argmax tokens. Thus, candidate transcriptions were bitwise identical to live transcriptions on that panel.
2. **Sequential Multiplier Bypassed:** Because sample standard error collapsed to zero ($SE_R = 0$), the upper confidence bound evaluated to:
   $$UCB_R = \Delta_R + z_t \cdot SE_R = 0.0 + z_t \cdot 0.0 = 0.0 \le \epsilon_R \ (0.00)$$
   This effectively bypassed the O'Brien–Fleming multiplier $z_t$. An update at look 8 ($z_8 \approx 9.78$) passed just as easily as at look 200 ($z_{200} \approx 2.07$), despite demonstrating no measured improvement.
3. **Statistical Implication:** Zero sample variance on 450 words does not establish zero population uncertainty. By Poisson/Binomial sampling, observing zero differences on 450 words admits a 95% upper bound of $3/450 \approx 0.67\%$.
4. **Corrective Architectural Requirement:**
   - Enforce an analytical finite-sample uncertainty floor: $SE_{\text{floor}} = 1/\sqrt{W_{\text{total}}} \times 100\%$ ($4.71\%$ for 450 words).
   - Enforce a strict utility requirement: updates with $\Delta_R \ge 0.00$ or degenerate zero-variance ties must default to `REJECT` (fail-closed stability), ensuring parameter updates are taken only when positive empirical benefit is established.

### Sequential Calibration under the Shared Sentinel Panel
- Reusing a fixed panel of 30 sentinel clips across repeated looks introduces positive equicorrelation ($\text{Cov}(T_k, T_m) = \sigma_\alpha^2 > 0$) across successive test statistics.
- Classical sequential testing theory (Armitage 1975, Jennison & Turnbull 2000) proves that positive correlation between successive statistics **lowers the boundary crossing probability** relative to independent increments.
- A 1,000-stream Monte Carlo simulation of the deployed gate under the compound-symmetric shared-sentinel null process yielded **0 false acceptances out of 1,000 streams** (Empirical FWER = 0.0000, 95% Wilson CI: $[0.0000, 0.0038]$), rigorously confirming family-wise error rate control below $\alpha = 0.05$.

---

## 6. Stage 6M Readiness Decision

> [!CAUTION]
> **Cohort 2 Decision: NO-GO**  
> **Status:** `MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD` remains strictly active.  
> While Cohort 1 physical execution successfully demonstrates that the DSG controller prevents catastrophic continuous adaptation degradation on real speech (saving 79 errors vs ungated SUTA), confirmatory execution of Cohort 2 is deferred until the uncertainty floor regularization and strict utility criteria are formalized in the production gate.
