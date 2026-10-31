# Stage 6M — Five-Stratum Candidate Data-Generating Model & Calibration Report (v1.5.0-Candidate)
================================================================================

| Parameter | Specification |
|:---|:---|
| **Document State** | `CANDIDATE_DATA_MODEL_REPORT` (Pre-Registration Draft) |
| **Governance Standard** | ADR-005; Protocol Section 14.7 (`PROJECT_LEAD_ACADEMIC_AUTHORIZATION`) |
| **Governance Status** | `DRAFT_HOLD` (Confirmatory Audio Materialization & Adaptation Strictly Blocked) |
| **Branch** | `stage6m-five-stratum-parity` |
| **Baseline Preserved** | Protocol v1.4.0 (`src/dsg_ctta/evaluation/paired_cluster_inference.py` Untouched) |
| **Confirmatory Strata** | 5 Confirmatory Strata (Australian, Canadian, England, South Asian, US English) |
| **Exploratory Strata** | 1 Out-of-Domain Stratum (Irish English, strictly excluded from confirmatory family) |
| **Multiplicity Family** | $M = 8$ Hypotheses, Fixed Single-Step Simultaneous Bonferroni ($\alpha_{\text{adj}} = 0.00625$) |
| **Authoritative Engine** | Simultaneous Upper Confidence Bounds (Linearized $t$-UCB for A, B, C; Bootstrap for D) |

---

## 1. Executive Summary & Task 3 Scope

Under **Stage 6M Task 3**, the data-generating model for the proposed five-stratum confirmatory experiment was fully reconciled with the declared `DesignStagePowerSpec` and empirical development calibration findings.

### Key Corrections Implemented:
1. **Direct Speaker-Level Paired Noise ($\sigma_{\text{paired}} = 0.032$):**
   Removed the erroneous $\sqrt{15}$ divisor from prior exploratory scripts. The 3.2 pp standard deviation directly parameterizes speaker-level paired treatment differences ($\epsilon_3, \epsilon_2 \sim N(0, 0.032^2)$).
2. **Reconciled Five-Stratum Treatment Effects:**
   - Target DSG superiority vs. Static: $-3.5$ pp average WER improvement.
   - Target DSG superiority vs. Corrected Ungated SUTA: $-3.5$ pp average WER improvement.
   - Target population disparity reduction: $-2.0$ pp reduction in max-minus-min gap.
   - Treatment effect vector $\boldsymbol{\delta}$ derived strictly across the five confirmatory strata, excluding Irish English.
3. **Decoupled Fixed Strata from Random Accent Shuffling:**
   The primary design scenario models the five named accent strata as **fixed population groups**. This prevents random accent variation ($\sigma_{\text{accent}} = 0.050$) from arbitrarily permuting accent rankings across simulated trials and diluting the prespecified $-2.0$ pp disparity effect. Random accent variation is preserved exclusively as a secondary sensitivity scenario.
4. **Unified Integer Word Counts & Integer Binomial Errors:**
   Each speaker draws a single integer word count from the discrete Uniform$[100, 180)$ distribution (following `DesignStagePowerSpec` convention), paired across all three evaluation arms. Integer binomial error counts ($e_1, e_2, e_3$) are generated per arm.
5. **Absolute Immutability of Frozen v1.4.0 Baseline:**
   `src/dsg_ctta/evaluation/paired_cluster_inference.py` was untouched. All candidate code is cleanly isolated in `scripts/stage6m_v1_5_candidate_power_simulator.py`.

---

## 2. Exact Data-Generating Equations

### 2.1 Confirmatory Strata & Baseline WER Calibration
The five confirmatory strata are indexed by $g \in \{1, \dots, 5\}$:
- Australian English: $\mu_{\text{AU}} = 0.193$ ($19.3$ pp)
- Canadian English: $\mu_{\text{CA}} = 0.161$ ($16.1$ pp)
- England English: $\mu_{\text{UK}} = 0.174$ ($17.4$ pp)
- South Asian English: $\mu_{\text{SA}} = 0.235$ ($23.5$ pp)
- US English: $\mu_{\text{US}} = 0.142$ ($14.2$ pp)

*Exclusion Invariant:* Irish English ($\mu_{\text{IE}} = 0.261$) is an exploratory out-of-domain stratum and is strictly excluded from all confirmatory baseline summary statistics:
$$\mu_{\min} = \min_{g} \mu_g = 0.142 \quad (\text{US English})$$
$$\mu_{\max} = \max_{g} \mu_g = 0.235 \quad (\text{South Asian English})$$
$$\text{Range} = \mu_{\max} - \mu_{\min} = 0.235 - 0.142 = 0.093 \quad (9.3\text{ pp})$$
$$\bar{\mu} = \frac{1}{5}\sum_{g=1}^5 \mu_g = \frac{0.142 + 0.161 + 0.174 + 0.193 + 0.235}{5} = 0.181 \quad (18.1\text{ pp})$$

### 2.2 Per-Accent DSG Treatment Effect Vector ($\delta_g$)
To simultaneously satisfy the $3.5$ pp average superiority over Static and the $-2.0$ pp reduction in max-min disparity:
$$\delta_g = -0.035 + \left(\frac{\mu_g - \bar{\mu}}{\mu_{\max} - \mu_{\min}}\right) (-0.020)$$

Explicit calculated values for each stratum:
- **US English ($\mu = 0.142$):** $\delta_{\text{US}} = -0.035 + \left(\frac{-0.039}{0.093}\right)(-0.020) = -0.026613$ ($-2.661$ pp)
- **Canadian English ($\mu = 0.161$):** $\delta_{\text{CA}} = -0.035 + \left(\frac{-0.020}{0.093}\right)(-0.020) = -0.030699$ ($-3.070$ pp)
- **England English ($\mu = 0.174$):** $\delta_{\text{UK}} = -0.035 + \left(\frac{-0.007}{0.093}\right)(-0.020) = -0.033495$ ($-3.349$ pp)
- **Australian English ($\mu = 0.193$):** $\delta_{\text{AU}} = -0.035 + \left(\frac{+0.012}{0.093}\right)(-0.020) = -0.037581$ ($-3.758$ pp)
- **South Asian English ($\mu = 0.235$):** $\delta_{\text{SA}} = -0.035 + \left(\frac{+0.054}{0.093}\right)(-0.020) = -0.046613$ ($-4.661$ pp)

**Analytical Proof of Calibration:**
1. **Average Effect:** $\frac{1}{5}\sum_{g=1}^5 \delta_g = -0.035000$ ($-3.500$ pp).
2. **Disparity Reduction:**
   - Static Disparity: $D_{\text{static}} = \mu_{\text{SA}} - \mu_{\text{US}} = 0.235 - 0.142 = 0.093000$ ($9.300$ pp).
   - DSG Disparity: $D_{\text{DSG}} = (\mu_{\text{SA}} + \delta_{\text{SA}}) - (\mu_{\text{US}} + \delta_{\text{US}}) = 0.188387 - 0.115387 = 0.073000$ ($7.300$ pp).
   - $\Delta_D = D_{\text{DSG}} - D_{\text{static}} = 0.073000 - 0.093000 = -0.020000$ ($-2.000$ pp).
3. **Monotonicity:** The slope of $(\mu_g + \delta_g)$ with respect to $\mu_g$ is $1 - \frac{0.020}{0.093} = +0.785 > 0$, guaranteeing that accent ranking is strictly preserved.

### 2.3 Speaker Generation Equations
For accent $g$ and speaker $i \in \{1, \dots, N_g\}$:

1. **Between-Speaker Shift:**
   $$u_{gi} \sim \mathcal{N}(0,\, 0.065^2) \quad (\sigma_{\text{between\_speaker}} = 6.5\text{ pp})$$
2. **Arm 1 (Static Baseline Error Probability):**
   $$p_{1,gi} = \operatorname{clip}(\mu_g + u_{gi},\, 0.01,\, 0.99)$$
3. **Arm 3 (DSG-CTTA Error Probability):**
   $$\epsilon_{3,gi} \sim \mathcal{N}(0,\, 0.032^2) \quad (\sigma_{\text{paired\_diff}} = 3.2\text{ pp})$$
   $$p_{3,gi} = \operatorname{clip}(p_{1,gi} + \delta_g + \epsilon_{3,gi},\, 0.01,\, 0.99)$$
4. **Arm 2 (Corrected Ungated SUTA Error Probability):**
   $$\epsilon_{2,gi} \sim \mathcal{N}(0,\, 0.032^2) \quad (\sigma_{\text{paired\_diff}} = 3.2\text{ pp})$$
   $$p_{2,gi} = \operatorname{clip}(p_{3,gi} + 0.035 + \epsilon_{2,gi},\, 0.01,\, 0.99)$$
   *Note:* $\epsilon_{3,gi}$ and $\epsilon_{2,gi}$ are independently sampled.
5. **Speaker Word Count (Paired Across Arms):**
   $$wc_{gi} \sim \operatorname{Uniform}_{\text{integer}}[100,\, 180)$$
6. **Observed Integer Error Counts:**
   $$e_{1,gi} \sim \operatorname{Binomial}(wc_{gi},\, p_{1,gi})$$
   $$e_{2,gi} \sim \operatorname{Binomial}(wc_{gi},\, p_{2,gi})$$
   $$e_{3,gi} \sim \operatorname{Binomial}(wc_{gi},\, p_{3,gi})$$

---

## 3. Parameter Provenance & Epistemic Taxonomy

To maintain methodological clarity and avoid epistemic conflation, all simulator parameters are categorized into five distinct tiers:

| Parameter Category | Parameters | Provenance & Evidence Base | Role in v1.5 Candidate Model |
|:---|:---|:---|:---|
| **1. Historical Frozen Specification (v1.4.0)** | $K = 6$, $M = 9$, $N_g = 220$, Holm/Bonferroni duality | Frozen commit `868374b` / `paired_cluster_inference.py`. Hardcodes 6 accents. | **Immutable Baseline Reference.** Preserved for historical audit and parity testing. |
| **2. Five-Stratum Candidate Assumptions** | $K = 5$, $M = 8$, $\alpha_{\text{adj}} = 0.00625$, $99.375\%$ UCB | ADR-005; formal Project-Lead decision on fixed Bonferroni adjustment (`8f92b0b`). | **Operative Candidate Architecture.** Authoritative decision rules for prospective promotion. |
| **3. Empirically Supported Parameters** | $\sigma_{\text{speaker}} = 0.065$, $\sigma_{\text{paired}} = 0.032$, CV27 baselines | Common Voice 27.0 development benchmarks; physical Cohort 1 ($N=60$) & Cohort 2 ($N=468$). | **Ground-Truth Variance Calibration.** Controls cross-speaker and within-speaker noise dispersion. |
| **4. Prespecified Scenario Targets** | $\Delta_{\text{static}} = -3.5$ pp, $\Delta_{\text{ungated}} = -3.5$ pp, $\Delta_D = -2.0$ pp | Research hypothesis targets declared in `DesignStagePowerSpec`. | **Alternative Hypothesis Benchmark.** Defines effect magnitudes under which statistical power is assessed. |
| **5. Sensitivity Parameters** | $\sigma_{\text{accent}} = 0.050$, bootstrap reps $B \in [2000, 20000]$ | Empirical accent variance across CV27 subsets; Monte Carlo bootstrap quantile stability. | **Robustness Auditing.** Evaluates whether findings withstand random population shifts and tail variability. |

---

## 4. Paired Covariance Structure & Measurement Noise Separation

A foundational principle of Task 3 is the strict separation between **latent probability contrasts** and **observed binomial measurement noise**:

1. **Latent Contrasts:**
   - DSG vs. Static:
     $$p_{3,gi} - p_{1,gi} = \delta_g + \epsilon_{3,gi}$$
     $$\mathbb{E}[p_{3,gi} - p_{1,gi}] = \delta_g, \quad \operatorname{Var}(p_{3,gi} - p_{1,gi}) = \sigma_{\text{paired\_diff}}^2 = 0.032^2$$
   - DSG vs. SUTA:
     $$p_{3,gi} - p_{2,gi} = -0.035 - \epsilon_{2,gi}$$
     $$\mathbb{E}[p_{3,gi} - p_{2,gi}] = -0.035, \quad \operatorname{Var}(p_{3,gi} - p_{2,gi}) = \sigma_{\text{paired\_diff}}^2 = 0.032^2$$
2. **Observed Binomial Differences:**
   The observed per-speaker error-rate difference $\widehat{\Delta}_{31,gi} = \frac{e_{3,gi} - e_{1,gi}}{wc_{gi}}$ includes additional binomial sampling noise:
   $$\operatorname{Var}\left(\frac{e_{3,gi} - e_{1,gi}}{wc_{gi}}\right) = \sigma_{\text{paired\_diff}}^2 + \mathbb{E}\left[\frac{p_{1,gi}(1 - p_{1,gi}) + p_{3,gi}(1 - p_{3,gi})}{wc_{gi}}\right]$$
   For $wc \approx 140$ and $p \approx 0.18$, binomial sampling adds $\approx 0.0021$ to the variance, raising the observed speaker-level error-rate standard deviation from $3.2$ pp to $\approx 5.6$ pp.
3. **Word-Weighted Aggregation:**
   The study estimands are word-weighted sums over the entire corpus:
   $$\widehat{\Delta}_{\text{static}} = \frac{\sum_{g,i} e_{3,gi} - \sum_{g,i} e_{1,gi}}{\sum_{g,i} wc_{gi}}$$
   By the Law of Large Numbers, binomial sampling error averages out across all clusters ($N_{\text{total}} \ge 1,100$), ensuring unbiased convergence to the target population effects.

---

## 5. Verification Evidence & Deterministic Test Results

Ten automated deterministic and sampling tests were implemented in `tests/research_validity/test_stage6m_candidate_data_model.py`:

```text
tests/research_validity/test_stage6m_candidate_data_model.py::test_deterministic_mean_dsg_improvement_vs_static PASSED [ 10%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_deterministic_mean_dsg_improvement_vs_suta PASSED [ 20%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_deterministic_population_disparity_reduction_before_noise PASSED [ 30%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_latent_speaker_level_paired_difference_sd PASSED [ 40%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_all_word_and_error_counts_are_valid_integers PASSED [ 50%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_each_speaker_has_paired_observations_across_all_arms PASSED [ 60%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_five_stratum_baseline_calculations_exclude_irish_english PASSED [ 70%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_fixed_seed_reproducibility PASSED [ 80%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_frozen_six_stratum_implementation_remains_unchanged PASSED [ 90%]
tests/research_validity/test_stage6m_candidate_data_model.py::test_latent_differences_vs_observed_binomial_differences PASSED [100%]
```

### Verification Checklist:
| Validation Item | Required Result | Observed Empirical Result | Status |
|:---|:---|:---|:---:|
| **Mean DSG improvement vs Static** | $-3.50$ pp | $-3.500000$ pp (analytical); $-3.501$ pp (latent $N=500\text{k}$) | **PASSED** |
| **Mean DSG improvement vs SUTA** | $-3.50$ pp | $-3.500000$ pp (analytical); $-3.499$ pp (latent $N=500\text{k}$) | **PASSED** |
| **Population disparity reduction** | $-2.00$ pp | $-2.000000$ pp (analytical); $-2.000$ pp (exact before noise) | **PASSED** |
| **Latent paired-difference SD** | $3.20$ pp | $0.03200$ (DSG vs Static); $0.03197$ (DSG vs SUTA) | **PASSED** |
| **Latent between-speaker SD** | $6.50$ pp | $0.06498$ (exact within statistical tolerance) | **PASSED** |
| **Word counts convention** | Valid integers $\in [100, 180)$ | All records valid integers, $100 \le wc < 180$ | **PASSED** |
| **Binomial error counts** | Integers $\in [0, wc]$ | All records valid integers, $0 \le err \le wc$ | **PASSED** |
| **Cross-arm pairing** | Paired observations across arms | Identical $wc$ shared across Static, SUTA, DSG | **PASSED** |
| **Exclusion of Irish English** | Confirmatory baseline excludes Irish | 5 strata evaluated; Irish raises ValueError if passed | **PASSED** |
| **Fixed-seed reproducibility** | Bitwise identical datasets | Seed 20261030 reproduced bitwise across trials | **PASSED** |
| **Frozen v1.4.0 immutability** | Zero diff relative to origin/main | Clean git status on `paired_cluster_inference.py` | **PASSED** |
| **Governance status** | `DRAFT_HOLD` | Strictly preserved; no audio materialized | **PASSED** |

**VERDICT: PASS**

---

## 6. Full Test Suite Regression Status

The entire Stage 6M validity test harness was executed jointly:
- `tests/research_validity/test_stage6m_candidate_data_model.py`: 10 passed.
- `tests/research_validity/test_stage6m_inference_parity.py`: 10 passed.
- `tests/research_validity/test_stage6m_multi_corpus_feasibility_audit.py`: 15 passed.

**Total: 35 passed in 106.07s.** Zero failures, zero warnings regressions.

---

## 7. Remaining Limitations & Next Actions

1. **Model Labeling:**
   This model is formally designated as the **v1.5 Candidate Design-Stage Data Model**. It is not claimed to be fully "protocol-exact" for inference until independent dual-path parity has been audited for the prospective five-stratum candidate execution path.
2. **Sample-Size Sweep Proscription:**
   Per Task 3 governance instructions, no sample-size power sweeps across candidate $N_g \in [220, 285]$ were executed. That analysis is reserved for Task 5 after bootstrap stability is verified.
3. **Immediate Next Step (Task 4):**
   Execute the **Bootstrap Quantile Stability Analysis**:
   - Evaluate the convergence of the Bonferroni $99.375^{\text{th}}$ upper percentile across bootstrap sample sizes $B \in \{500, 1000, 2000, 5000, 10000, 20000\}$.
   - Quantify Monte Carlo error in the tail percentile estimator to establish the minimum necessary replicate count for the confirmatory study.
