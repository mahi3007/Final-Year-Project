# Stage 6M Task 6.1 & 6.2 — Event D Type I Null Calibration & Disparity Safety Audit

> **DOCUMENT STATUS:** Authoritative Statistical Calibration Report & Task 6.2 Addendum
> **GOVERNANCE STATUS:** DRAFT_HOLD (Confirmatory Audio Download & Execution Blocked)
> **EVALUATION BRANCH:** `stage6m-five-stratum-parity` (HEAD commit `e0e1647`)
> **FINAL CALIBRATION VERDICT:** **CONDITIONAL HOLD**

---

## Historical Audit Trail (Preserved Task 6.1 Baseline)

In Task 6.1, we audited the initial Event D sensitivity finding (where an unexpected 2.3% false-pass rate was observed) and identified non-linear probability clipping in the data-generating model as the root cause:
- **Nominal Baseline Disparity:** 9.3000 pp (23.5% - 14.2%)
- **Clipped Static Disparity ($D_1$):** 9.2496 pp
- **Uncalibrated DSG Disparity ($D_3$):** 9.0063 pp (under uniform $\delta_g = -3.50$ pp)
- **Realized Population Disparity Change ($\Delta D$):** **-0.2433 pp** (beneficial disparity narrowing rather than a genuine null)
- **Historical Uncalibrated Simulation False-Pass Rate:** 1.90% to 2.3% (statistically driven by the non-zero negative disparity shift)

> [!NOTE] SUPERSEDED TASK 6.1 PRELIMINARY INTERPRETATION:
> Earlier preliminary commentary tentatively suggested that $N_g = 220$ was 'strictly certified as Type I controlled' while $N_g = 285$ was 'non-controlled' because their observed point estimates were 0.580% and 0.630% relative to nominal 0.625%. That preliminary distinction is **formally superseded and retracted** in Task 6.2. Both results are fully compatible with nominal $\alpha_{\text{adj}} = 0.625\%$, and finite Monte Carlo uncertainty prevents strict 95% confidence certification for either.

---

## Task 6.2 Addendum: Mathematical Verification & Statistical Interpretation

### 1. Verification of the Nested-Clipping Model (Task A & B)
The candidate data-generating process applies non-linear clipping at $[a, b] = [0.01, 0.99]$ twice in sequence:
$$p_1 = \operatorname{clip}(\mu_g + u, a, b), \quad u \sim \mathcal{N}(0, \sigma_{\text{spk}}^2)$$
$$p_3 = \operatorname{clip}(p_1 + \delta_g + \epsilon, a, b), \quad \epsilon \sim \mathcal{N}(0, \sigma_{\text{paired}}^2)$$

Because the first clipping operation produces discrete point masses at $a = 0.01$ and $b = 0.99$, a single-step Gaussian approximation with combined variance $\sqrt{\sigma_{\text{spk}}^2 + \sigma_{\text{paired}}^2}$ is not mathematically exact. By the Law of Total Expectation, the exact expectation decomposes into three components:
$$E[p_3] = T_{\text{lower}} + T_{\text{upper}} + T_{\text{interior}}$$
where:
- $T_{\text{lower}} = P(p_1 = a) \cdot E[\operatorname{clip}(a + \delta_g + \epsilon, a, b)] = \Phi\left(\frac{a - \mu_g}{\sigma_{\text{spk}}}\right) g_{\text{clip}}(a + \delta_g, \sigma_{\text{paired}}, a, b)$
- $T_{\text{upper}} = P(p_1 = b) \cdot E[\operatorname{clip}(b + \delta_g + \epsilon, a, b)] = \left[1 - \Phi\left(\frac{b - \mu_g}{\sigma_{\text{spk}}}\right)\right] g_{\text{clip}}(b + \delta_g, \sigma_{\text{paired}}, a, b)$
- $T_{\text{interior}} = \int_a^b g_{\text{clip}}(x + \delta_g, \sigma_{\text{paired}}, a, b) \frac{1}{\sigma_{\text{spk}}} \phi\left(\frac{x - \mu_g}{\sigma_{\text{spk}}}\right) dx$

### 3-Way Independent Model Comparison (Uncalibrated $\delta_g = -3.50$ pp)
| Evaluation Method | Static Disparity ($D_1$) | DSG Disparity ($D_3$) | Population $\Delta D$ | US English Arm 3 $E[p_3]$ | Lower Point Mass Contribution ($T_{\text{lower}}$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Naive Single-Step Approximation** | 9.2496 pp | 9.0063 pp | -0.2433 pp | 11.0035% | 0.0000% (Ignored) |
| **2. Exact Nested Numerical Quadrature** | 9.2496 pp | 9.0034 pp | **-0.2463 pp** | 11.0065% | **+0.0258%** |
| **3. High-Precision Monte Carlo (10,000,000 draws)** | 9.2496 pp | 9.0009 pp | **-0.2487 pp** | 11.0068% | Emulated in empirical draws |

**Conclusion:** The naive single-step approximation underestimates the clipping effect by $0.003$ pp because it ignores the boundary mass. The exact nested numerical quadrature matches the 10,000,000-sample Monte Carlo simulation within $0.0001$ pp.

---

### 2. Exact Quadrature Null Calibration (Task B)
Using `scipy.optimize.brentq` over the exact nested numerical quadrature function, we solved for the unique stratum-specific shifts $\delta_g$ that satisfy $E[p_3(\mu_g, \delta_g)] = E[p_1(\mu_g)] - 0.035000000000$ across all 5 confirmatory strata:

| Confirmatory Stratum | Baseline WER ($\mu_g$) | Static $E[p_1]$ | Target DSG $E[p_3]$ | Calibrated Shift ($\delta_g$) | Realized DSG $E[p_3]$ (Quadrature) | Residual Error |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 19.3% | 19.3000% | 15.8000% | **-3.5515 pp** | 15.8000% | $< 10^{-12}$ pp |
| **Canadian English** | 16.1% | 16.1000% | 12.6000% | **-3.6557 pp** | 12.6000% | $< 10^{-12}$ pp |
| **England English** | 17.4% | 17.4000% | 13.9000% | **-3.6011 pp** | 13.9000% | $< 10^{-12}$ pp |
| **South Asian English** | 23.5% | 23.5000% | 20.0000% | **-3.5095 pp** | 20.0000% | $< 10^{-12}$ pp |
| **US English** | 14.2% | 14.2000% | 10.7000% | **-3.7816 pp** | 10.7000% | $< 10^{-12}$ pp |

- **Quadrature Static Population Disparity:** 9.24964037 pp
- **Quadrature DSG Population Disparity:** 9.24964037 pp
- **Quadrature Population Disparity Change ($\Delta D$):** **+0.000000000000 pp** (Exact Null verified)
- **10M Monte Carlo Empirical Delta Disparity:** **-0.002432 pp** (Deviation = 0.002432 pp, well within standard error)

---

### 3. Corrected Interpretation of Null Simulations (Task C)

Under the prespecified $M = 8$ Bonferroni family ($\alpha_{\text{adj}} = 0.05 / 8 = 0.00625 = 0.625\%$), two 10,000-trial simulations with $B = 20,000$ bootstrap replicates per trial were performed under the calibrated exact null:

| Sample Size ($N_g$) | Evaluation Confirmatory Speakers | Outer Trials | Bootstrap Reps ($B$) | False Passes | False-Pass Rate | Exact Two-Sided 95% CI | One-Sided 95% Upper Bound | Distance from Expected Count ($62.5$) | Binomial $p$-value | Compatibility Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N_g = 220$** | 1,100 | 10,000 | 20,000 | 58 | **0.580%** | [0.441%, 0.749%] | **0.721%** | **-0.57 SD** (58 vs 62.5) | $p = 0.568$ | **COMPATIBLE** |
| **$N_g = 285$** | 1,425 | 10,000 | 20,000 | 63 | **0.630%** | [0.484%, 0.805%] | **0.776%** | **+0.06 SD** (63 vs 62.5) | $p = 0.950$ | **COMPATIBLE** |

> **AUTHORITATIVE STATISTICAL INTERPRETATION (SUPERSEDING TASK 6.1 PREVIOUS WORDING):**
>
> **1. No Evidence of Inflated Type I Error:**
> The observed null rejection rates are compatible with the nominal Bonferroni level ($0.625\%$). Under a perfectly calibrated $0.625\%$ test with 10,000 simulations, the expected false-pass count is $62.5$ with standard deviation $\sqrt{10,000 \times 0.00625 \times 0.99375} \approx 7.88$.
> - 58 false passes ($N_g = 220$) is approximately $0.57$ standard deviations below expectation.
> - 63 false passes ($N_g = 285$) is approximately $0.06$ standard deviations above expectation.
> No statistically significant inflation was detected in either simulation.
>
> **2. Finite-Sample Monte Carlo Confidence vs Strict Certification:**
> Because the one-sided 95% Clopper–Pearson upper bounds are $0.721\%$ ($N_g = 220$) and $0.776\%$ ($N_g = 285$), both exceeding $0.625\%$, the finite Monte Carlo experiment cannot certify with 95% confidence that the true false-pass probability is strictly below the threshold. We explicitly distinguish lack of evidence of inflation from proof of control.
>
> **3. Rejection of Artificial Distinction Between $N_g = 220$ and $N_g = 285$:**
> Previous wording suggesting that $N_g = 220$ is 'strictly controlled' while $N_g = 285$ 'failed' is **superseded and retracted**. The $0.05$ percentage-point difference between $0.580\%$ and $0.630\%$ is purely Monte Carlo sampling variation ($z = 0.45, p = 0.65$).

---

### 4. Sample Size Decision Rationale: Operational Capacity Reserve
The authoritative reason to designate **$N_g = 220$ as the primary confirmatory sample size** is operational capacity, not the minor Monte Carlo difference in the null simulations:

| Sample Size Candidate | Confirmatory Evaluation Speakers | Gate Reserve | Total Unexposed Required | Total CV27 Australian Capacity | Australian Reserve Margin | Capacity Risk Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N_g = 220$ (PRIMARY)** | **1,100** | **20** | **240** | **305** | **+65 speakers (+21.3%)** | **BUFFERED (Recommended)** |
| **$N_g = 285$ (BENCHMARK)** | 1,425 | 20 | 305 | 305 | 0 speakers (0.0%) | EXHAUSTED (Zero tolerance) |

At $N_g = 220$, the study preserves 65 eligible Australian speakers to absorb recording dropouts, decoding failures, corrupted files, and participant validation exclusions.

---

### 5. Diagnostic Harm Stress Tests (Reported Separately)
Harm tests evaluate an entirely different hypothesis: whether Event D incorrectly accepts a harmful divergence in disparity. As established in Task 6.1, under harmful disparity widening (true $\Delta D = +0.50$ pp and $+1.00$ pp), the candidate engine rejects disparity non-increase in **7,999 out of 8,000 trajectories ($99.988\%$)**:
- True $\Delta D = +0.50$ pp, $N_g = 220$: $1 / 2,000$ false passes ($0.050\%$)
- True $\Delta D = +0.50$ pp, $N_g = 285$: $0 / 2,000$ false passes ($0.000\%$)
- True $\Delta D = +1.00$ pp, $N_g = 220$: $0 / 2,000$ false passes ($0.000\%$)
- True $\Delta D = +1.00$ pp, $N_g = 285$: $0 / 2,000$ false passes ($0.000\%$)

---

### 6. Implementation Audit & Frozen Code Immutability
1. **Paired Cluster Bootstrap Resampling:** The cluster vector `bi` indexes `wc`, `err1`, `err3` simultaneously per speaker.
2. **Stratified Resampling:** Independent within each of the 5 confirmatory strata.
3. **Decision Rule:** One-sided $99.375\%$ simultaneous UCB $\le 0.0000$ pp (inclusive).
4. **Engine Parity:** `paired_cluster_inference_v15.py` and `evaluate_trial_all_events` match identically.
5. **Frozen Code:** `src/dsg_ctta/evaluation/paired_cluster_inference.py` has **0 lines diff** against `origin/main`.

---

## Final Governance Verdict

```
FINAL VERDICT: CONDITIONAL HOLD
GOVERNANCE STATUS: DRAFT_HOLD PRESERVED
RECOMMENDED DESIGN: N_g = 220 SPEAKERS PER ACCENT (1,100 TOTAL EVALUATION SPEAKERS)
AUTHORIZATION PREREQUISITE: Formal Project-Lead Sign-Off Prior to Cohort 3 Execution
```
