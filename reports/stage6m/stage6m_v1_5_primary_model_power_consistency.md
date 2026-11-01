# Stage 6M Task 6.3 — Primary Model and Power Consistency Audit

> **DOCUMENT STATUS:** Authoritative Consistency Audit Report & Power Provenance Reconciliation
> **GOVERNANCE STATUS:** DRAFT_HOLD (Cohort 3 Audio Materialization Blocked)
> **EVALUATION BRANCH:** `stage6m-five-stratum-parity` (Starting commit `1212954`)
> **FINAL GOVERNANCE VERDICT:** **CONDITIONAL HOLD**

---

## Executive Summary

This audit establishes the mathematical consistency and inferential provenance between the corrected
nested-clipping data-generating model (Task 6.2) and the primary five-stratum candidate statistical power confirmation:
1. **Primary Model Calibration Confirmed (Task A):** Under exact nested numerical quadrature, the five-stratum candidate generator achieves:
   - Mean DSG improvement vs Static = **3.500000 pp** (Target: 3.50 pp)
   - Mean DSG improvement vs corrected ungated SUTA = **3.500000 pp** (Target: 3.50 pp)
   - Population disparity change ($\Delta D$) = **-2.000000 pp** (Target: -2.00 pp)
2. **Power Result Provenance Reconciled (Task B):**
   - The original Task 5 report recorded **95.35%** joint power at $N_g = 220$ under an uncalibrated generator where probability clipping caused an overshoot in disparity reduction (realized $\Delta D = -2.1733$ pp).
   - Under the exact calibrated generator targeting strictly $\Delta D = -2.0000$ pp, confirmed joint power at $N_g = 220$ is **90.58%** (exact 95% CI: [89.99%, 91.15%], 95% LCB = **90.09%**).
   - Both the $\ge 90.00\%$ joint power and $\ge 90.00\%$ LCB pre-registered criteria remain strictly satisfied.
3. **Operational Capacity Preserved:** $N_g = 220$ remains the recommended primary design candidate because it preserves **65 eligible Australian evaluation speakers (+21.3%)** as an operational reserve, whereas $N_g = 285$ leaves zero reserve margin.
4. **Scientific Limitation Disclosed (Task C):** Statistical power is conditional on the hypothesized $-2.0$ pp disparity narrowing; if true narrowing is $\le -1.0$ pp, power degrades below $50\%$. These targets must be characterized as scenario assumptions rather than physical facts.
5. **Event D Null Interpretation Re-Affirmed (Task D):** The observed null rates ($0.580\%$ at $N_g = 220$ and $0.630\%$ at $N_g = 285$) are statistically compatible with nominal $0.625\%$; neither strictly certifies error control with 95% confidence.

---

## 1. Task A — Primary Model Calibration Audit

The candidate study data generator applies two consecutive non-linear clipping operations:
$$p_1 = \operatorname{clip}(\mu_g + u, 0.01, 0.99), \quad u \sim \mathcal{N}(0, \sigma_{\text{spk}}^2)$$
$$p_3 = \operatorname{clip}(p_1 + \delta_g + \epsilon, 0.01, 0.99), \quad \epsilon \sim \mathcal{N}(0, \sigma_{\text{paired}}^2)$$

Because $p_1 = 0.01$ creates a discrete probability mass ($T_{\text{lower}} = +0.0258$ pp for US English), the pre-clipping linear formula $\delta_g = -3.5 + \frac{\mu_g - \bar{\mu}}{\text{range}} \times (-2.0)$ fails to realize exact scenario parameters.

### Exact Model Comparison: Uncalibrated vs Calibrated

| Evaluation Metric | Registered Design Target | Historical Task 5 (Pre-Clipping Linear) | Corrected Task 6.3 (Nested Quadrature) | 10M-Sample Latent Monte Carlo Check | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mean DSG Improvement vs Static** | 3.50 pp | 3.4044 pp | **3.500000 pp** | 3.5006 pp | **EXACT MATCH** |
| **Mean DSG Superiority vs SUTA** | 3.50 pp | 3.50 pp | **3.500000 pp** | 3.50 pp | **EXACT MATCH** |
| **Static Population Disparity ($D_1$)** | — | 9.2496 pp | **9.2496 pp** | 9.2458 pp | Verified |
| **DSG Population Disparity ($D_3$)** | — | 7.0763 pp | **7.2496 pp** | 7.2434 pp | Verified |
| **Population Disparity Change ($\Delta D$)** | **-2.00 pp** | -2.1733 pp (Overshoot: -0.1733 pp) | **-2.000000000000 pp** | **-2.0025 pp** | **EXACT MATCH** |

### Stratum-Specific Calibrated Parameters

| Confirmatory Accent Stratum | Baseline WER ($\mu_g$) | Static Expected $E[p_1]$ | Uncalibrated $\delta_g$ | Calibrated Shift ($\delta_g$) | DSG Expected $E[p_3]$ | Realized Improvement | Lower Point Mass ($T_{\text{lower}}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 19.3% | 19.3047% | -3.7581 pp | **-3.8137 pp** | 15.5481% | **3.7566 pp** | +0.0029% |
| **Canadian English** | 16.1% | 16.1222% | -3.0699 pp | **-3.2001 pp** | 13.0538% | **3.0685 pp** | +0.0128% |
| **England English** | 17.4% | 17.4121% | -3.3495 pp | **-3.4425 pp** | 14.0648% | **3.3474 pp** | +0.0072% |
| **South Asian English** | 23.5% | 23.5004% | -4.6613 pp | **-4.6798 pp** | 18.8366% | **4.6638 pp** | +0.0003% |
| **US English** | 14.2% | 14.2508% | -2.6613 pp | **-2.8680 pp** | 11.5870% | **2.6638 pp** | +0.0280% |

---

## 2. Task B — Statistical Power Provenance & Full-Depth Confirmation

### Provenance Reconciliation
Under the uncalibrated generator used in Task 5, probability clipping compressed the lower-WER stratum (US English) more than higher-WER strata, causing the realized disparity to narrow by **$-2.1733$ pp** instead of the registered $-2.0000$ pp. This unintended extra $0.1733$ pp of disparity narrowing inflated the original simulated power to $95.35\%$.

When the candidate generator is strictly calibrated via nested numerical quadrature to achieve **exactly $-2.000000$ pp** of disparity reduction, confirmatory power remains robustly above the pre-registered $90.00\%$ threshold:

| Parameter | Candidate Design Point ($N_g = 220$) | Benchmark Design Point ($N_g = 285$) | Pre-Registered Standard |
| :--- | :---: | :---: | :---: |
| **Confirmatory Evaluation Speakers** | **1,100** | 1,425 | $\le 1,425$ Capacity |
| **Outer Monte Carlo Trials** | 10,000 | 2,500 | $\ge 10,000$ |
| **Bootstrap Replicates / Trial** | 20,000 | 20,000 | $\ge 20,000$ |
| **Event A Power (Static Super.)** | **100.00%** | 100.00% | — |
| **Event B Power (SUTA Super.)** | **100.00%** | 100.00% | — |
| **Event C Power (Accent Guard)** | **100.00%** | 100.00% | — |
| **Event D Power (Disparity Guard)** | **90.58%** | 96.96% | — |
| **Joint Confirmatory Power** | **90.58%** | **96.96%** | $\ge 90.00\%$ |
| **Exact 95% Two-Sided CI** | **[89.99%, 91.15%]** | [96.21%, 97.60%] | — |
| **One-Sided 95% LCB** | **90.09%** | **96.33%** | $\ge 90.00\%$ |
| **Statistical Power Verdict** | **PASS** | **PASS** | **PASS** |

---

## 3. Task C — Exploratory Sensitivity Analysis Provenance

> **METHODOLOGICAL NOTE:** The sensitivity curve represents exploratory screening runs using $1,000$ outer trials and $B = 2,000$ bootstrap replicates, NOT full-depth confirmatory confirmation.

| True Disparity Narrowing ($\Delta D$) | Scenario Description | Exploratory Joint Power ($N_g = 220$) | Design Status |
| :---: | :--- | :---: | :---: |
| **-2.00 pp** | Primary registered design scenario | **94.30%** | ADEQUATELY POWERED |
| **-1.50 pp** | Moderately weaker disparity narrowing | **77.50%** | UNDERPOWERED (< 90%) |
| **-1.00 pp** | Substantially weaker disparity narrowing | **41.70%** | UNDERPOWERED (< 90%) |
| **+0.00 pp** | Genuine null disparity change | **2.30%** | NULL (Rejection = False Pass) |

> **CRITICAL SCIENTIFIC LIMITATION:** The five-stratum candidate is adequately powered (>= 90%) only if the hypothesized -2.0 pp disparity reduction is realized in practice. Under weaker effects (-1.5 pp or -1.0 pp), confirmatory power drops to 77.5% and 41.7% respectively. These effects must be characterized in the dissertation as development-stage design scenario assumptions rather than established physical constants.

---

## 4. Task D — Event D Null Calibration Provenance

The Task 6.2 Event D null-calibration results are fully preserved and re-affirmed:

| Sample Size ($N_g$) | Outer Trials | False Passes | False-Pass Rate | Nominal $\alpha_{\text{adj}}$ | Exact Two-Sided 95% CI | One-Sided 95% UCB | $z$-score from Expectation ($62.5$) | Binomial $p$-value | Conclusion |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N_g = 220$** | 10,000 | 58 | **0.580%** | 0.625% | [0.441%, 0.749%] | **0.721%** | **-0.57 SD** | $p = 0.568$ | Compatible (No inflation) |
| **$N_g = 285$** | 10,000 | 63 | **0.630%** | 0.625% | [0.484%, 0.805%] | **0.776%** | **+0.06 SD** | $p = 0.950$ | Compatible (No inflation) |

### Monte Carlo Residual Uncertainty Analysis
- **10M-Sample Latent Monte Carlo Residual:** **-0.002432 pp**
- **Monte Carlo Standard Error:** **\pm 0.004111 pp**
- **Exact 95% Monte Carlo Confidence Interval:** **[-0.010490 pp, +0.005626 pp]**
- **Statistical Test:** $z = -0.59, p = 0.5541$ (Statistically indistinguishable from $0.0000$ pp)

---

## 5. Frozen Production Code Immutability & Stage 6M Parity

1. **Frozen Production Code Immutability:** `src/dsg_ctta/evaluation/paired_cluster_inference.py` has **0 lines diff** against `origin/main`.
2. **Separate Candidate Inference Path:** The five-stratum candidate engine is strictly housed in `src/dsg_ctta/evaluation/paired_cluster_inference_v15.py`.
3. **Multiplicity Family Preservation:** $M = 8$, $\alpha = 0.05$, $\alpha_{\text{adj}} = 0.00625$, simultaneous percentile = $99.375\%$.
4. **Boundary Decision Rule:** $\text{UCB}_D \le 0.0000$ pp (inclusive).

---

## Final Governance Verdict

```
FINAL VERDICT: CONDITIONAL HOLD
GOVERNANCE STATUS: DRAFT_HOLD PRESERVED
PRIMARY RECOMMENDED DESIGN: N_g = 220 SPEAKERS PER ACCENT (1,100 CONFIRMATORY EVALUATION SPEAKERS)
MAXIMUM-CAPACITY BENCHMARK: N_g = 285 SPEAKERS PER ACCENT (1,425 SPEAKERS; CONSUMES 100% AUSTRALIAN POOL)
AUTHORIZATION PREREQUISITE: Formal Project-Lead Sign-Off Prior to Cohort 3 Audio Materialization
```
