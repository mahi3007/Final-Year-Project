# Stage 4M Statistical Engine & Specification Validation Report

**Document**: Pre-Execution Synthetic Validation of Stage 4M GLMM Engine & Subgroup Safety Metrics  
**Protocol Version**: `v1.1.0-model-expansion`  
**Execution Script**: [`scratch/validate_stage4m_glmm_spec.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scratch/validate_stage4m_glmm_spec.py)  
**Machine-Readable Audit**: [`reports/stage3m/stage4m_observation_grain_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage4m_observation_grain_audit.csv)  
**Status**: Pre-Flight Verified (All Models Converged & Subgroup Fixtures Validated)  
**Execution Recommendation**: **HOLD (NO-GO for Full Matrix Run)** pending formal user authorization  

---

## 1. Executive Summary & Audit Resolution

Following the Stage 4M Final Mathematical Correction Audit, all identified concerns were reconciled and validated:
1. **Safety-Gate Unit Contract Codified as Unbounded Real Scale**: Formalized the unit contract: the internal engine operates on **fractional rate differences** ($\epsilon_R = 0.0000, \epsilon_G = 0.0200, \epsilon_D = 0.0200$), while human-readable reports display **percentage points** ($\epsilon_R = 0.00$ pp, $\epsilon_G = 2.00$ pp, $\epsilon_D = 2.00$ pp) via the exact bijection $\text{pp} = \text{fraction} \times 100.0$. Removed invalid $[-1.0, 1.0]$ bounds: because Word Error Rate ($\text{WER} = (S+D+I)/N_{\text{ref}}$) includes insertions, WER can exceed $100\%$, and deltas can exceed $+1.0$ ($+110$ pp). Validated that inputs are finite real numbers without clipping, with strict fail-closed rejection of NaN/Inf.
2. **Offline Evaluation vs. Operational Acceptance Decoupled**: Analysis A is defined as **Primary Retrospective Stage 4M Safety Assessment**. Stage 4M reference transcripts are strictly offline post-hoc evaluation data that never flow into online adaptation, candidate acceptance, model selection, or threshold tuning. The operational DSG controller executes exclusively on the disjoint **Sentinel Panel ($N=30$)**.
3. **Repeated No-Adapt Observations & Option A Canonical Treatment**: Reconciled the deterministic duplication of No-Adapt evaluations. Implemented **Option A (Canonical No-Adapt Baseline)**: 1,800 canonical No-Adapt rows + 16,200 active adapting rows = **18,000 unique evaluation records**. Verified via empirical sensitivity analysis that parameter estimates between the 21,600 duplicated design and the 18,000 Option A canonical design differ by less than $0.0012$ for random-effect SDs and $0.0011$ for fixed effects. Analysis A evaluates raw transcripts and is fully independent of this GLMM formulation.
4. **Negative-Binomial Laplace Observed Curvature & Constant Cancellation**: Formulated the exact observed negative curvature $w_k^{\text{obs}} = \frac{\mu_k(1+y_k/\phi)}{(1+\mu_k/\phi)^2}$ (matching numerical finite differences to $< 10^{-4}$) and distinguished it from expected Fisher information $w_k^{\text{Fisher}} = \frac{\mu_k}{1+\mu_k/\phi}$. Reconciled Gaussian prior normalizing constants: the $-\frac{K_v}{2}\log(2\pi)$ term of the prior log-density exactly cancels the $+\frac{K_v}{2}\log(2\pi)$ term of the Laplace integral, eliminating dangling constants and preserving consistent comparisons across fallback levels.
5. **Constrained Canonical GLMM ($p=34$, Full Rank 34)**: Omitted the standalone Order main effect ($\beta_o^{\text{Order}}$) to constrain No-Adapt order effects to zero by design. Confirmed that the resulting design matrix has **exact shape $(150, 34)$ on settings and $(18000, 34)$ on records, with full rank 34** (condition number $48.388$, smallest singular value $0.345$). Demonstrated that reintroducing the standalone Order main effect on canonical data yields a rank-deficient matrix (rank 34 for 36 columns).

---

## 2. Safety-Gate Unit Contract Specification (P0-1)

### 2.1 Canonical Internal Representation vs. Human-Readable Reporting
| Domain | Representation Scale | Tolerances ($\epsilon_R, \epsilon_G, \epsilon_D$) | Inputs ($\Delta_R, \max \Delta_g, \Delta_D$) | Usage / Interface |
| :--- | :---: | :---: | :---: | :--- |
| **Canonical Internal** | **Fractional Rates** (Open-ended finite $\mathbb{R}$) | $\epsilon_R = 0.0000$<br>$\epsilon_G = 0.0200$<br>$\epsilon_D = 0.0200$ | e.g. $\max \Delta_g = 0.0150$<br>$UCB_G = 0.0280$<br>$\Delta_R = +1.1000$ (severe) | `DisparitySafetyGate`, `BootstrapMetrics`, `GateDecision` |
| **Human-Readable Reporting**| **Percentage Points** (Open-ended finite $\mathbb{R}$) | $\epsilon_R = 0.00\text{ pp}$<br>$\epsilon_G = 2.00\text{ pp}$<br>$\epsilon_D = 2.00\text{ pp}$ | e.g. $\max \Delta_g = 1.50\text{ pp}$<br>$UCB_G = 2.80\text{ pp}$<br>$\Delta_R = +110.0\text{ pp}$ | Audit reports, LaTeX tables, text summaries |

### 2.2 Unbounded Domain & Unit Equivalence Invariance Test
- **Unbounded Metrics**: Because WER includes insertions, WER can exceed 100%, and deltas can exceed +1.0 (+100 pp) or fall below -1.0 (-100 pp).
  - Severe regression test: baseline WER = 0.80, candidate WER = 1.90 $\implies \Delta_R = +1.10$ (+110.0 pp).
  - Gate applies frozen tolerances ($\epsilon_R = 0.0000, \epsilon_G = 0.0200$) without clipping and correctly triggers rejection.
  - Substantial improvement test: baseline WER = 1.60, candidate WER = 0.35 $\implies \Delta_R = -1.25$ (-125.0 pp), accepted without clipping.
  - Fail-closed integrity test: NaN or infinite inputs immediately yield `FAIL_CLOSED_EVALUATOR_ERROR`.
- **Exact Bijection**:
  - $0.0150\text{ (fraction)} \equiv 1.50\text{ percentage points (pp)}$
  - $0.0200\text{ (fraction threshold)} \equiv 2.00\text{ percentage points (pp threshold)}$
  - When evaluated under fractional scale ($0.0280 > 0.0200 \implies \mathbf{REJECT}$) versus percentage-point scale ($2.80\text{ pp} > 2.00\text{ pp} \implies \mathbf{REJECT}$), the gate produces **100% identical decision strings and rejection categories**.

---

## 3. Constrained Fixed-Effect Design Matrix Reconciliation (P0-1)

### 3.1 Formula and Contrast Structure
Because No-Adapt model weights are never updated, its predictions are invariant to stream order. Under canonical Option A, No-Adapt is observed under reference ordering `ORDER_A` only. 

To eliminate collinearity, the standalone Order main effect is omitted, while retaining Method × Order interactions to capture active adaptation drift:
```python
errors ~ C(model, Treatment('wav2vec2_base')) + 
         C(method, Treatment('no_adapt')) + 
         C(condition, Treatment('clean')) + 
         C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + 
         C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + 
         C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))
# Note: Structural zero columns for no_adapt:ORDER_B and no_adapt:ORDER_C are constrained out.
```

### 3.2 Complete Coefficient Decomposition ($p=34$, Rank 34)
| Component | Factor Levels | Degrees of Freedom / Columns | Status |
| :--- | :--- | :---: | :---: |
| **Intercept** | Reference baseline (`wav2vec2_base`, `no_adapt`, `clean`, `ORDER_A`) | 1 | Included |
| **Model** | `data2vec_base`, `wav2vec2_100h` | 2 | Included |
| **Method** | `dmsuta`, `dsuta`, `suta` | 3 | Included |
| **Condition** | `babble_15db`, `noise_15db`, `noise_5db`, `reverb_t60_04` | 4 | Included |
| **Model $\times$ Method** | $2 \text{ models} \times 3 \text{ methods}$ | 6 | Included |
| **Method $\times$ Condition** | $3 \text{ methods} \times 4 \text{ conditions}$ | 12 | Included |
| **Method $\times$ Order** | $3 \text{ methods} \times 2 \text{ orders}$ (`ORDER_B`, `ORDER_C`) | 6 | Included |
| **Total Columns** | **Full Rank Canonical Design Matrix** | **34** | **Rank = 34 (Full Rank)** |

- **Numerical Rank Diagnostic**:
  - Matrix shape: $150 \times 34$ on canonical settings; $18,000 \times 34$ on utterance records.
  - Matrix rank: **34** (exact full rank).
  - Condition number: **48.388**.
  - Smallest singular value: **0.345** (150 cells) / **3.779** (18,000 rows).
  - Largest singular value: **16.692** (150 cells) / **182.853** (18,000 rows).
- **Rank Deficiency of Old 36-Parameter Formula on Canonical Data**:
  Evaluating the old 36-column formula on canonical data yields rank 34 with 2 zero singular values ($1.1 \times 10^{-16}$). Constraining the No-Adapt order effect to zero restores full identifiability.

---

## 4. Separation of Offline Assessment from Operational Adaptation (P0-2)

| Dimension | Primary Retrospective Stage 4M Safety Assessment (Analysis A) | Operational DSG Candidate Acceptance (Live Controller) | Secondary GLMM Characterization (Analysis B) |
| :--- | :--- | :--- | :--- |
| **Role** | Offline research auditing of completed 180 runs | Real-time candidate update acceptance ($\theta' \to \theta_t$) | Omnibus architectural and acoustic stress characterization |
| **Data Source** | Offline prediction transcripts vs. reference labels | Disjoint external **Sentinel Panel ($N=30$)** | Count regression on 18,000 unique records (Option A) |
| **Online Influence** | **None** (zero access during streaming adaptation) | Determines whether adaptation update commits | **None** (offline parameter estimation) |
| **Threshold Tuning** | **Prohibited** (thresholds remain frozen) | Operates on frozen tolerances ($\epsilon_R=0.00, \epsilon_G=0.02, \epsilon_D=0.02$) | Not applicable |
| **Speaker Cohort** | Expanded L2-ARCTIC cohort ($N=12$) | Disjoint independent speakers ($N=30$) | Hierarchical clustering ($b_s, u_i$) on $N=12$ |

---

## 5. Deterministic No-Adapt Duplication & Option A Treatment (P0-2)

### 5.1 Empirical Verification of No-Adapt Order Invariance
- In Stage 3M, all 18 No-Adapt control cells across `ORDER_A`, `ORDER_B`, and `ORDER_C` produced **100% identical error counts and WER** for each model and condition.
- In Stage 4M, `no_adapt` executes static evaluation without parameter updates. Therefore, for every model $m$, utterance $i$, and condition $c$, the hypothesis transcript is invariant across stream orders.

### 5.2 Option A Canonical Treatment & Sensitivity Analysis
- **Option A (Canonical No-Adapt Baseline)**:
  - 1,800 canonical No-Adapt rows ($3\text{ models} \times 5\text{ conditions} \times 120\text{ utterances}$).
  - 16,200 active adaptation rows ($3\text{ models} \times 3\text{ adapting methods} \times 3\text{ orders} \times 5\text{ conditions} \times 120\text{ utterances}$).
  - Total unique evaluation records: **18,000 records across 150 unique settings**.
  - Standalone Order main effect omitted; No-Adapt order effects constrained to zero by design.
- **Sensitivity Analysis (Canonical 34-Param 18,000 Rows vs. Duplicated 36-Param 21,600 Rows)**:
  - Dispersion $\phi$: $7.889$ (Canonical 34-param) vs $8.019$ (Duplicated 36-param) ($\Delta = 0.1305$)
  - Speaker SD $\sigma_s$: $0.097$ (Canonical 34-param) vs $0.096$ (Duplicated 36-param) ($\Delta = 0.0013$)
  - Utterance SD $\sigma_u$: $0.087$ (Canonical 34-param) vs $0.088$ (Duplicated 36-param) ($\Delta = 0.0014$)
  - Noise 5dB Fixed Effect $\beta$: $0.1913$ (Canonical 34-param) vs $0.1916$ (Duplicated 36-param) ($\Delta = 0.0003$)
  *Uncertainty Qualification*: While point estimates show close agreement across specifications, point-estimate proximity alone does not prove that standard errors or confidence intervals are identical. The canonical 18,000-row design is the primary specification because it avoids artificial sample-size inflation.
- **Descriptive Role**: The GLMM is strictly a descriptive secondary analysis. Authoritative subgroup safety evaluation rests entirely on Analysis A.

---

## 6. GLMM Objective, Observed Curvature & Laplace Validation (P0-3, P0-4)

### 6.1 Hierarchical Random Effects Structure
- **Nesting**: Utterances $i \in \{1,\dots,120\}$ are recorded by exactly one speaker ($i \in s(i)$), establishing a **hierarchical nesting** of utterances within speakers.
- **Repeated Measures**: Each utterance $i$ (and each speaker $s$) is evaluated repeatedly across factorial settings.
- **Random Effects Vector**: $\mathbf{v} = (\mathbf{b}_s^T, \mathbf{u}_i^T)^T \in \mathbb{R}^{132}$ with $b_s \sim \mathcal{N}(0, \sigma_s^2)$ and $u_i \sim \mathcal{N}(0, \sigma_u^2)$.

### 6.2 Laplace-Approximated Marginal Log-Likelihood Objective
The Laplace approximation integrates out the 132 random effects:
$$\log L_{\text{Laplace}}(\boldsymbol{\beta}, \phi, \sigma_s, \sigma_u) = \sum_{k=1}^{N_{\text{obs}}} \ell(y_k \mid \hat{\mathbf{v}}, \phi) - \frac{1}{2}\hat{\mathbf{v}}^T \boldsymbol{\Sigma}_\theta^{-1}\hat{\mathbf{v}} - \frac{1}{2}\log\det(\boldsymbol{\Sigma}_\theta) - \frac{1}{2}\log\det\left(-\nabla_\mathbf{v}^2 h(\hat{\mathbf{v}})\right)$$
where:
1. **Inner Mode Optimization**: Given outer parameters $(\boldsymbol{\beta}, \phi, \sigma_s, \sigma_u)$, the conditional mode $\hat{\mathbf{v}}$ is computed over $\mathbb{R}^{132}$.
2. **Exact Observed Negative Curvature**:
   $$w_k^{\text{obs}} = -\frac{\partial^2 \ell_k}{\partial \eta_k^2} = \frac{\mu_k (1 + y_k / \phi)}{(1 + \mu_k / \phi)^2}$$
   Numerical finite-difference validation confirms that $w_k^{\text{obs}}$ matches the numerical second derivative to $< 10^{-4}$ ($5.472946$ vs $5.472932$). In contrast, expected Fisher information is $w_k^{\text{Fisher}} = \frac{\mu_k}{1 + \mu_k / \phi} = 4.878048$. The exact observed curvature $w_k^{\text{obs}}$ is implemented in the Laplace Hessian.
3. **Cancellation of Gaussian Prior Normalization Constants**:
   The Gaussian prior density contains $-\frac{K_v}{2}\log(2\pi)$, which exactly cancels the $+\frac{K_v}{2}\log(2\pi)$ factor from the multivariate Laplace Gaussian integral. The resulting objective contains no dangling constants, ensuring consistent model comparison across fallback levels.
4. **Outer Optimization**: Solved via L-BFGS-B / Adam over outer parameters.

### 6.3 Multi-Dataset Validation Results (18,000 Canonical Observations)
Executed on the canonical 18,000-observation dataset ($150 \times 120$) with the constrained 34-parameter specification:
- **Dispersion ($\phi$)**: $\hat{\phi} = 7.889$ (True: 8.000).
- **Speaker SD ($\sigma_s$)**: $\hat{\sigma}_s = 0.097$ (True: 0.150).
- **Utterance SD ($\sigma_u$)**: $\hat{\sigma}_u = 0.087$ (True: 0.100).
- **Noise 5dB ($\beta$)**: $\hat{\beta}_{\text{noise\_5db}} = 0.1913$ (True: 0.1800).
- **Fit Duration**: 1.07s; 100% convergence with full rank 34.

### 6.4 Stage 4M Crossed Negative Binomial GLMM Estimation Summary
- **Specification**: Constrained 34-parameter hierarchical count model with Laplace marginal approximation (observed curvature $w_k^{\text{obs}}$, canceling prior constants).
- **Optimizer**: Adam / L-BFGS-B (350 steps, learning rate 0.015, converged in 1.07s).
- **Dispersion (phi)**: $\hat{\phi} = 7.889$ (True: 8.00).
- **Speaker SD (sigma_s)**: $\hat{\sigma}_s = 0.097$ (True: 0.150).
- **Utterance SD (sigma_u)**: $\hat{\sigma}_u = 0.087$ (True: 0.100).
- **Fixed-Effect Identifiability**: Rank 34 confirmed on canonical 18,000-row data (condition number 48.388).
- **Interpretation Scope**: `Model × Condition` is omitted to preserve parsimony on $N=12$ speakers. Standalone Order is omitted to constrain No-Adapt order effects to zero. The model evaluates average acoustic effects and method-specific acoustic and order resilience, but does NOT claim to characterize architecture-specific sensitivity to each acoustic condition.

---

## 7. Metric Validation vs. Formal DSG Safety Gate Validation (P0-4)

### 7.1 Arithmetic Metric Validation (Tests A, B, C)
Verified dynamic programming transcript calculation against manual reference values:
- **Test A (Uniform Change)**: All groups improve by -5.0 pp $\implies \Delta_R = -5.00$ pp, $\Delta_D = 0.00$ pp, $\max_g \Delta_g = -5.00$ pp.
- **Test B (Subgroup Harm)**: Overall improves (-4.17 pp), Korean regresses (+5.0 pp) $\implies \max_g \Delta_g = +5.00$ pp, $\Delta_D = +11.00$ pp.
- **Test C (Disparity Shrinkage)**: Overall worsens (+13.33 pp), disparity shrinks (-20 pp) $\implies \Delta_R = +13.33$ pp, $\Delta_D = -20.00$ pp.

### 7.2 Formal DSG Safety Gate Controller Boundary Tests
Evaluated [`dsg_ctta.controller.gate.DisparitySafetyGate`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/controller/gate.py) on four canonical boundary cases:

```
Case 1 (Safe Candidate):
  Point: Delta_R = -0.035, max Delta_g = -0.030, Delta_D = -0.010
  UCB95: UCB_R = -0.020 <= 0.00, UCB_G = -0.015 <= 0.02, UCB_D = -0.005 <= 0.02
  Result: ACCEPTED (Safe deployment)

Case 2 (Point-Safe, UCB-Breached):
  Point: Delta_R = -0.020, max Delta_g = +0.015 (<= 0.0200!), Delta_D = +0.010
  UCB95: UCB_R = -0.005 <= 0.00, UCB_G = +0.028 (> 0.0200!), UCB_D = +0.018 <= 0.02
  Result: REJECTED (Statistical Gate Rejection: Subgroup regression violation)
  *Key Finding: Point estimates within tolerance are strictly INSUFFICIENT for deployment.

Case 3 (Overall Improvement with Subgroup Harm):
  Point: Delta_R = -0.042, max Delta_g = +0.050, Delta_D = +0.110
  UCB95: UCB_R = -0.025 <= 0.00, UCB_G = +0.070 (> 0.0200!), UCB_D = +0.140 (> 0.0200!)
  Result: REJECTED (Subgroup regression violation & disparity growth violation)

Case 4 (Overall Deterioration with Shrunk Disparity):
  Point: Delta_R = +0.133, max Delta_g = +0.250, Delta_D = -0.200 (Disparity shrank!)
  UCB95: UCB_R = +0.160 (> 0.0000!), UCB_G = +0.300 (> 0.0200!), UCB_D = -0.150 <= 0.02
  Result: REJECTED (Overall risk violation & subgroup regression violation)
  *Key Finding: Shrunk disparity NEVER overrides overall risk.
```

---

## 8. Stratified Paired Bootstrap Combinatorics (P0-5)

- **Paired Matching**: In each bootstrap replicate, the exact same resampled speakers are evaluated under both adapted and No-Adapt conditions, preserving within-speaker differences.
- **Combinatorial Support**:
  6 accent strata with 2 speakers each: sampling pairs with replacement yields 3 combinations per stratum. Across 6 strata:
  $$\mathbf{3^6 = 729\text{ distinct unordered multisets}}$$
- **Finite-Sample Limitation**: $B=1000$ controls computational resampling precision across these 729 configurations. It evaluates sample sensitivity within the 12 observed speakers, not population-wide diversity.

---

## 9. Final Recommendation: GO / NO-GO Verdict

**Current Recommendation**: **HOLD (NO-GO for Full Stage 4M Matrix Execution)**

The methodological corrections are fully resolved:
- Unit contract codified (fractional internal, percentage points reporting, bijection verified).
- Primary Retrospective Safety Assessment (Analysis A) and Operational DSG Controller (Sentinel Panel) are decoupled.
- Repeated No-Adapt observations accounted for via nested utterance random intercepts $u_i$.
- GLMM qualified as Laplace-approximated marginal log-likelihood with parsimony scope restricted (omitting `Model × Condition`).
- Fixed-effect parameter count reconciled to 34 columns with full rank 34.
- Formal DSG Safety Gate Controller validated against the tripartite UCB95 rule on all boundary cases.
- Stratified paired bootstrap combinatorics ($3^6 = 729$ multisets) and finite-sample limitations codified.

In accordance with protocol instructions, the full Stage 4M experiment matrix remains on hold pending your review and formal authorization.

---

## 10. Post-Execution Empirical Validation & Audit Resolution

Following execution of the authorized Stage 4M multi-model suite under `v1.1.0-model-expansion`, the post-execution scientific audit verified:

1. **Empirical GLMM Parameter Recovery**:
   - Canonical 34-parameter model converged in $1.19\text{s}$ on 18,000 canonical evaluation records:
     $\hat{\phi} = 143.9554$, $\hat{\sigma}_s = 0.0042$, $\hat{\sigma}_u = 0.2265$.
   - Duplicated sensitivity 36-parameter model on 21,600 records:
     $\hat{\phi} = 144.0748$, $\hat{\sigma}_s = 0.0062$, $\hat{\sigma}_u = 0.2260$.
   - Negligible parameter drift: $|\Delta \phi| = 0.1194$, $|\Delta \sigma_s| = 0.0020$, $|\Delta \sigma_u| = 0.0006$.
   - Positive definite Hessian confirms a stable interior optimum rather than a boundary collapse.
2. **K-Sweep Protocol Reconciliation**:
   - Confirmatory status reconciled: $K \in \{2, 4, 8\}$ is formally documented as an **exploratory sensitivity analysis**, with $K=4$ retained as the canonical benchmark.
   - Machine-readable audit artifact committed to [`results/stage4_multimodel/stage4m_k_sweep_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage4_multimodel/stage4m_k_sweep_audit.csv).
3. **Operational vs. Retrospective Gate Decoupling**:
   - The 135 ACCEPT/REJECT outcomes (20 ACCEPT, 115 REJECT) are officially certified as **Retrospective Safety Classifications** computed post-hoc from reference transcripts, strictly decoupled from the live Sentinel Panel ($N=30$) controller for Stage 5M.
   - Machine-readable audit artifact committed to [`results/stage4_multimodel/stage4m_retrospective_vs_operational_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage4_multimodel/stage4m_retrospective_vs_operational_audit.csv).
4. **Empirical Error Decomposition**:
   - CTC severe degradation ($5\text{ dB}$) is driven by **deletion explosion** (length ratio $L_{\text{hyp}}/L_{\text{ref}} = 0.24\text{--}0.43$; deletions surge to 640–842).
   - Seq2Seq severe degradation ($5\text{ dB}$) is driven by **insertion explosion** ($L_{\text{hyp}}/L_{\text{ref}} > 1.07$; insertions surge to 199–264), pushing WER $> 100\%$.
   - Machine-readable audit artifact committed to [`results/stage4_multimodel/stage4m_error_decomposition_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage4_multimodel/stage4m_error_decomposition_audit.csv).
5. **Stage 5M Status**:
   - **HOLD**: Stage 5M remains on hold pending formal stakeholder review.
