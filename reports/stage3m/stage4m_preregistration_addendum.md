# Stage 4M Preregistration Addendum: Statistical Analysis Specification

**Protocol Version**: `v1.1.0-model-expansion`  
**Document**: Stage 4M Preregistered Statistical Analysis Plan (Formal Protocol Addendum)  
**Status**: Frozen Prior to Stage 4M Outcome Analysis  
**Pre-Registered Semantic Safety Thresholds**: $\epsilon_R = 0.00$ pp ($0.0000$ frac), $\epsilon_G = 2.00$ pp ($0.0200$ frac), $\epsilon_D = 2.00$ pp ($0.0200$ frac) [Unaltered & Frozen]  
**Cluster Bootstrap Resamples**: $B = 1000$ (Stratified Paired Resampling, support = 729 multisets)  
**Significance Level**: $\alpha = 0.05$ (two-tailed)  

---

## 1. Experimental Scope, Observation Granularity & Stream Partitioning

### 1.1 Observation Granularity: Approach A (Utterance-Level)
The Stage 4M analysis unit is frozen at **Approach A: Utterance-Level Observations**.
- **Observation Unit**: A single evaluation record corresponding to utterance $i \in \{1,\dots,120\}$ spoken by speaker $s \in \{1,\dots,12\}$, evaluated under CTC model $m \in \{1,2,3\}$, adaptation method $j \in \{1,2,3,4\}$, stream order $o \in \{1,2,3\}$, and acoustic condition $c \in \{1,2,3,4,5\}$.
- **Experimental Settings**:
  $$N_{\text{settings}} = 3\text{ (Models)} \times 4\text{ (Methods)} \times 3\text{ (Orders)} \times 5\text{ (Conditions)} = 180$$
- **Utterances per Stream**: $U = 120$ unique utterances (10 utterances per speaker across 12 speakers).
- **Nominal Factorial Matrix vs. Canonical GLMM Dataset**:
  - *Nominal Full-Factorial Design*: $3 \text{ models} \times 4 \text{ methods} \times 3 \text{ orders} \times 5 \text{ conditions} = \mathbf{180\text{ nominal factorial combinations}}$ ($21,600$ runs if duplicated).
  - *Canonical Secondary GLMM Dataset (Option A: Canonical No-Adapt Baseline)*: **$150\text{ unique factorial combinations}$** ($15\text{ No-Adapt ORDER_A} + 135\text{ active adaptation}$).
  - *Total Canonical Utterance-Level Records (Option A)*: $150 \times 120 = \mathbf{18,000\text{ records}}$ ($1,800$ canonical No-Adapt + $16,200$ active adaptation).
  - *Duplicated Representation ($21,600$ rows)*: Evaluated strictly as an exploratory sensitivity check, not as the primary canonical GLMM dataset.
- **Exposure / Offset**: Reference word count $N_i$ per utterance enters as $\log N_i$ with coefficient constrained to $1.0$. Reference words are **not aggregated across utterances**.

### 1.2 Adaptation Window Count, Terminal Window Rule & K-Sweep Sensitivity
- **Window Batch Size**: Frozen default $K = 4$ utterances per window.
- **Number of Prediction Windows**:
  $$W = \left\lceil \frac{120}{4} \right\rceil = \mathbf{30\text{ prediction windows}}$$
  *(Note: Stage 3M contained 15 windows for its 60-utterance stream. Stage 4M strictly contains 30 prediction windows).*
- **Terminal Window Rule (Window 29)**:
  Windows $w \in \{0, \dots, 28\}$ execute hypothesis prediction followed by unsupervised parameter adaptation. For the 30th and final window ($w=29$, utterances 116–119), the model generates predictions and logs evaluation. **The terminal adaptation update is omitted (skipped)**, because zero downstream utterances exist in that stream and a terminal update would have no downstream effect on predictions.
- **K-Sweep Sensitivity Check**: An exploratory K-Sweep sensitivity analysis ($K \in \{2, 4, 8\}$) will evaluate buffer size robustness secondary to the primary $K=4$ evaluation.

### 1.3 Speaker Cohort and Accent Groups
- **Speaker Cohort ($N=12$) across all 6 accent groups**:
  - Arabic: `ABA`, `SKA`
  - Hindi: `BJM`, `ASI`
  - Spanish: `EBVS`, `NCC`
  - Mandarin: `TLX`, `TXHC`
  - Vietnamese: `BVT`, `THV`
  - Korean: `YDCK`, `YKXP`
- **Speaker Overlap Disclosure**: Six of the twelve speakers (`ABA`, `BJM`, `EBVS`, `TLX`, `BVT`, `YDCK`) overlap with the Stage 3M test set. Stage 4M is an **expanded-sample stress characterization ($N=12$), NOT an independent speaker validation cohort**. True independent speaker validation is reserved for the disjoint Sentinel Panel ($N=30$) and Common Voice ($N=60$) evaluations.

---

## 2. Separation of Offline Evaluation from Operational Adaptation Acceptance (P0-2)

To prevent confusion between offline research auditing and online deployment control, the protocol explicitly decouples two distinct analytical roles:

### Analysis A — Primary Retrospective Stage 4M Safety Assessment (Primary Observed Subgroup-Safety Assessment)
- **Role**: Offline, post-hoc scientific evaluation of completed experimental streams.
- **Data Source**: Model prediction transcripts generated during the completed 180 factorial runs.
- **Strict Offline Evaluation Boundary**:
  - Stage 4M reference transcripts are used **strictly offline** to compute empirical WER, group deltas, disparity, and bootstrap uncertainty.
  - Reference transcripts **never flow into the online adaptation loop**, candidate parameter acceptance, model selection, or threshold tuning.
  - Streaming test adaptation operates entirely unsupervised without access to ground truth labels.
  - Stage 4M results cannot be used to tune or alter the frozen safety thresholds ($\epsilon_R, \epsilon_G, \epsilon_D$).
- **Primary Estimands** (calculated directly from prediction transcripts):
  $$\Delta_R = R_{\text{adapt}} - R_{\text{no-adapt}} \quad [\text{pp}]$$
  $$\Delta_g = R_{g,\text{adapt}} - R_{g,\text{no-adapt}} \quad [\text{pp}]$$
  $$\max_g \Delta_g = \max_{g \in \mathcal{G}} \Delta_g \quad [\text{pp}]$$
  $$\Delta_D = D_{\text{adapt}} - D_{\text{no-adapt}} \quad [\text{pp}], \quad D = \max_g R_g - \min_g R_g$$
- **Uncertainty Quantification**: Stratified Paired Speaker-Cluster Bootstrap ($B=1000$). Each bootstrap replicate pairs the exact same resampled speakers between adapted and No-Adapt streams, preserving 100% representation of all 6 accent groups.

### Operational DSG Controller (Online Deployment Acceptance Engine)
- **Role**: Decides during live streaming execution whether to accept a candidate parameter update $\theta'$ or retain the current model state $\theta_t$.
- **Allowed Input Data**:
  - The operational DSG controller executes on the **disjoint Sentinel Panel ($N=30$ independent speakers)**, which is an external, frozen validation set completely separate from the incoming test stream.
  - The controller **never accesses reference transcripts of the incoming evaluation stream**.
  - All decisions follow a strict **fail-closed policy**: missing data, NaN/Inf, or threshold breaches result in immediate update rejection.

### Analysis B — Secondary Mixed-Effects Characterization (Omnibus Model Engine)
- **Role**: Investigates average population-level fixed effects across backbones, adaptation methods, acoustic stress conditions, and stream arrival orders.
- **Why Group Interactions are Excluded from Omnibus GLMM**:
  Including Speech Group $\times$ Method interactions would add $5 \times 3 = 15$ degrees of freedom, and Group $\times$ Method $\times$ Condition would add 60 degrees of freedom. With only $N=12$ speakers (2 per group), adding 15 to 60 interaction parameters would severely overparameterize the model relative to the independent speaker clusters. Therefore, the omnibus GLMM estimates average structural effects, while **Analysis A provides the authoritative subgroup safety evaluation**.

---

## 3. Safety-Gate Unit Contract Specification (P0-1)

To eliminate ambiguity between fractional rate differences and percentage points, the unit contract is formally codified:

### 3.1 Canonical Internal Representation vs. Human-Readable Reporting
| Domain | Representation Scale | Tolerances ($\epsilon_R, \epsilon_G, \epsilon_D$) | Inputs ($\Delta_R, \max \Delta_g, \Delta_D$) | Usage / Interface |
| :--- | :---: | :---: | :---: | :--- |
| **Canonical Internal** | **Fractional Rates** (Open-ended finite $\mathbb{R}$) | $\epsilon_R = 0.0000$<br>$\epsilon_G = 0.0200$<br>$\epsilon_D = 0.0200$ | e.g. $\max \Delta_g = 0.0150$<br>$UCB_G = 0.0280$<br>$\Delta_R = +1.1000$ (severe) | `DisparitySafetyGate`, `BootstrapMetrics`, `GateDecision` |
| **Human-Readable Reporting**| **Percentage Points** (Open-ended finite $\mathbb{R}$) | $\epsilon_R = 0.00\text{ pp}$<br>$\epsilon_G = 2.00\text{ pp}$<br>$\epsilon_D = 2.00\text{ pp}$ | e.g. $\max \Delta_g = 1.50\text{ pp}$<br>$UCB_G = 2.80\text{ pp}$<br>$\Delta_R = +110.0\text{ pp}$ | Audit reports, LaTeX tables, text summaries |

### 3.2 Removal of Invalid $[-1.0, 1.0]$ Domain Restrictions
- **Word Error Rate Formula**:
  $$\text{WER} = \frac{S + D + I}{N_{\text{reference words}}}$$
  Because insertions ($I$) contribute to the numerator without bound, WER can exceed $1.0$ ($100\%$). In high-noise or catastrophic adaptation conditions, recognition can deteriorate severely, yielding empirical WER values well above $100\%$.
- **Unbounded Fractional Rate Differences**:
  For example, if baseline WER is $0.80$ ($80\%$) and adapted WER deteriorates to $1.90$ ($190\%$):
  $$\Delta_R = 1.90 - 0.80 = +1.10 \quad (+110.0\text{ pp})$$
  Similarly, if a degraded baseline model ($1.60$) is repaired to ($0.40$), the negative improvement is $\Delta_R = -1.20$ ($-120.0\text{ pp}$). Group disparities ($D = \max_g R_g - \min_g R_g$) and disparity differences ($\Delta_D$) are likewise not bounded by $[-1.0, 1.0]$.
- **Contract Enforcement**:
  The controller validates that inputs are **finite real numbers** ($\mathbb{R}_{\text{finite}}$) without clipping, truncation, or rejection of mathematically valid WER differences solely due to magnitude $> 1.0$. Strict fail-closed policy immediately rejects NaN and infinite values (`FAIL_CLOSED_EVALUATOR_ERROR`).

### 3.3 Exact Mathematical Mapping & Invariance
The relationship between fractional rate differences and percentage points is a strict bijection:
$$\text{value}_{\text{pp}} = \text{value}_{\text{fraction}} \times 100.0, \qquad \text{value}_{\text{fraction}} = \frac{\text{value}_{\text{pp}}}{100.0}$$

- **Threshold Equivalence**:
  $$\epsilon_G = 0.0200 \text{ (fraction)} \quad \equiv \quad \epsilon_G = 2.00\text{ percentage points (pp)}$$
- **Input Equivalence**:
  $$0.0150 \text{ (fraction)} \quad \equiv \quad 1.50\text{ percentage points (pp)}$$
  $$1.1000 \text{ (fraction)} \quad \equiv \quad 110.00\text{ percentage points (pp)}$$
- **Decision Invariance**:
  A fractional metric $0.0280$ compared against fractional threshold $0.0200$ produces:
  $$0.0280 > 0.0200 \implies \mathbf{REJECT}$$
  The equivalent percentage-point metric $2.80$ pp compared against percentage-point threshold $2.00$ pp produces:
  $$2.80\text{ pp} > 2.00\text{ pp} \implies \mathbf{REJECT}$$
  Both representations produce 100% mathematically identical gate acceptance decisions.
- **Code Enforcement**: [`DisparitySafetyGate`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/controller/gate.py) accepts fractional rates natively, and provides `from_percentage_points(...)` and `decision_to_percentage_points(...)` for exact bidirectional conversion.

---

## 4. Constrained Fixed-Effect Model Specification & Identifiability Reconciliation (P0-1)

### 4.1 Constrained Fixed-Effect Formula ($p=34$ Coefficients)
Because No-Adapt model weights are never updated, its predictions are invariant to stream arrival order. In the canonical 18,000-record dataset (150 settings), No-Adapt is evaluated under reference ordering `ORDER_A` only. 

Under treatment contrast coding, retaining both a standalone Order main effect ($\beta_o^{\text{Order}}$) and Method × Order interactions causes collinearity and rank deficiency, because No-Adapt has no observations under `ORDER_B` or `ORDER_C` to independently identify the standalone Order main effect. 

Therefore, the No-Adapt stream-order effect is **constrained to zero by design**. The standalone Order main effect is omitted, while retaining the Method × Order interaction terms $(\beta\beta)_{jo}^{\text{Method} \times \text{Order}}$. These 6 interaction terms estimate how the active adaptation methods (`suta`, `dsuta`, `dmsuta`) evolve across stream arrival orders (`ORDER_B`, `ORDER_C`) relative to their respective `ORDER_A` baselines:

$$E_{i,s,m,j,o,c} \sim \operatorname{NegativeBinomial}(\mu_{i,s,m,j,o,c}, \phi)$$

$$\begin{aligned}
\log \mu_{i,s,m,j,o,c} ={}& \log N_i + \beta_0 \\
&{}+ \beta_m^{\text{Model}} + \beta_j^{\text{Method}} + \beta_c^{\text{Condition}} \\
&{}+ (\beta\beta)_{mj}^{\text{Model} \times \text{Method}} + (\beta\beta)_{jc}^{\text{Method} \times \text{Condition}} + (\beta\beta)_{jo}^{\text{Method} \times \text{Order}} \\
&{}+ b_s + u_i
\end{aligned}$$

where $b_s$ represents speaker random intercepts and $u_i$ (or $b_i$) represents utterance random intercepts.

### 4.2 Reference Categories & Complete Parameter Decomposition ($p=34$)
Using standard reference-level (treatment) contrast coding:
- **Reference Cell**: `model = wav2vec2_base`, `method = no_adapt`, `condition = clean`, `ordering = ORDER_A`.
- **Parameter Breakdown**:
  1. Intercept: $\beta_0$ ($1$ coefficient)
  2. Model: `data2vec_base`, `wav2vec2_100h` ($2$ coefficients)
  3. Method: `dmsuta`, `dsuta`, `suta` ($3$ coefficients)
  4. Condition: `babble_15db`, `noise_15db`, `noise_5db`, `reverb_t60_04` ($4$ coefficients)
  5. Model $\times$ Method: $2 \times 3$ interactions ($6$ coefficients)
  6. Method $\times$ Condition: $3 \times 4$ interactions ($12$ coefficients)
  7. Method $\times$ Order: $3 \times 2$ interactions ($6$ coefficients)
     - `dmsuta:ORDER_B`, `dmsuta:ORDER_C`
     - `dsuta:ORDER_B`, `dsuta:ORDER_C`
     - `suta:ORDER_B`, `suta:ORDER_C`
  $$\mathbf{p = 1 + 2 + 3 + 4 + 6 + 12 + 6 = 34\text{ coefficients}}$$

- **Design Matrix Shape, Rank & Singular Values**:
  - Cell level ($150 \times 34$): **Exact Rank 34** (Full rank; zero aliased columns; condition number $48.388$; smallest singular value $0.345$; largest singular value $16.692$).
  - Utterance level ($18,000 \times 34$): **Exact Rank 34** (Full rank; zero aliased columns; condition number $48.388$; smallest singular value $3.779$; largest singular value $182.853$).
- **Demonstration of Old 36-Parameter Rank Deficiency**:
  If the standalone Order main effect (2 df) were reintroduced alongside Method × Order on the canonical 18,000-row dataset, the resulting $18,000 \times 36$ design matrix would have 2 unidentifiable directions and rank 34 (rank deficient by 2). Constraining the No-Adapt order effect to zero eliminates the rank deficiency and guarantees full mathematical identifiability.

### 4.3 Option A Canonical No-Adapt Baseline, Sensitivity Check & Distinction from Nominal Design (P0-2)
- **Option A (Canonical No-Adapt Baseline)**:
  Evaluates No-Adapt under `ORDER_A` only, yielding 1,800 canonical baseline records ($15 \times 120$) and 18,000 total canonical utterance-level observations across 150 unique settings.
- **Separation of Concepts**:
  1. *Nominal Factorial Design*: 180 combinations ($3 \times 4 \times 3 \times 5$).
  2. *Canonical GLMM Dataset (Option A)*: 150 combinations ($15 \text{ No-Adapt} + 135 \text{ active}$), totaling **18,000 utterance records**.
  3. *Duplicated Representation*: 21,600 rows (repeating No-Adapt across `ORDER_B` and `ORDER_C`), used strictly as a sensitivity check.
- **Sensitivity Comparison (Canonical 34-Parameter vs. Duplicated 36-Parameter)**:
  Fitted on identical synthetic data using the Laplace GLMM engine:
  - Dispersion $\phi$: $7.889$ (Canonical 34-param) vs $8.019$ (Duplicated 36-param) ($\Delta = 0.1305$)
  - Speaker SD $\sigma_s$: $0.097$ (Canonical 34-param) vs $0.096$ (Duplicated 36-param) ($\Delta = 0.0013$)
  - Utterance SD $\sigma_u$: $0.087$ (Canonical 34-param) vs $0.088$ (Duplicated 36-param) ($\Delta = 0.0014$)
  - Noise 5dB Fixed Effect $\beta$: $0.1913$ (Canonical 34-param) vs $0.1916$ (Duplicated 36-param) ($\Delta = 0.0003$)
  *Note on Uncertainty*: While point estimates show close agreement across specifications, point-estimate proximity alone does not imply that standard errors or confidence intervals are identical. The canonical 18,000-row dataset avoids artificial sample-size inflation.
- **Descriptive Role & Analysis A Independence**:
  The secondary GLMM is strictly an omnibus descriptive analysis. The primary retrospective safety assessment (Analysis A) computes direct paired differences per stream/speaker from raw transcripts, completely independent of the GLMM's row structure and parameterization.

---

## 5. GLMM Estimation Objective, Laplace Approximation & Scope (P0-3, P0-4)

### 5.1 Hierarchical Random Effects Structure (Utterances Nested in Speakers)
- In L2-ARCTIC, each utterance $i \in \{1,\dots,120\}$ is recorded by exactly one speaker $s(i) \in \{1,\dots,12\}$ (10 unique utterance texts per speaker).
- Utterances are **hierarchically nested within speakers** ($i \in s(i)$).
- Each utterance $i$ (and each speaker $s$) is observed repeatedly across experimental conditions.
- The random effects vector is:
  $$\mathbf{v} = (b_1,\dots,b_{12}, u_1,\dots,u_{120})^T \in \mathbb{R}^{132}$$
  with $b_s \sim \mathcal{N}(0, \sigma_s^2)$ for 12 speaker clusters, and $u_i \sim \mathcal{N}(0, \sigma_u^2)$ for 120 nested utterances.

### 5.2 Laplace-Approximated Marginal Log-Likelihood Objective & Observed Curvature
The Negative Binomial distribution uses variance $\operatorname{Var}(Y_k) = \mu_k + \mu_k^2 / \phi$ and log-link $\eta_k = \log \mu_k$.
Let $\ell(y_k \mid \mu_k(\mathbf{v}), \phi)$ be the conditional Negative Binomial log-likelihood.

#### Exact Observed Curvature vs. Expected Fisher Information
The Hessian required by the Laplace determinant is the negative second derivative of the conditional log-likelihood with respect to the linear predictor $\eta_k = \log \mu_k$:
- **Exact Observed Negative Curvature**:
  $$w_k^{\text{obs}} = -\frac{\partial^2 \ell_k}{\partial \eta_k^2} = \frac{\mu_k (1 + y_k / \phi)}{(1 + \mu_k / \phi)^2}$$
- **Expected Fisher Information**:
  $$w_k^{\text{Fisher}} = \mathbb{E}[w_k^{\text{obs}}] = \frac{\mu_k}{1 + \mu_k / \phi}$$
The exact Laplace approximation uses the **observed curvature** $w_k^{\text{obs}}$, verified numerically against finite-difference second derivatives ($5.472946$ vs $5.472932$, match $< 10^{-4}$). The Fisher information ($4.878048$) is an expected-curvature approximation that differs when $y_k \ne \mu_k$.

#### Gaussian Prior Normalization Constants & Exact Cancellation
The joint log-posterior with Gaussian random effects $\mathbf{v} \in \mathbb{R}^{K_v}$ ($K_v = 132$) includes the Gaussian prior density:
$$\log p(\mathbf{y}, \mathbf{v} \mid \boldsymbol{\theta}) = \sum_k \ell(y_k \mid \mathbf{v}, \phi) - \frac{1}{2}\mathbf{v}^T \boldsymbol{\Sigma}_\theta^{-1}\mathbf{v} - \frac{1}{2}\log\det(\boldsymbol{\Sigma}_\theta) - \frac{K_v}{2}\log(2\pi)$$
Integrating out $\mathbf{v}$ via the multivariate Laplace approximation introduces the Gaussian integral factor $(2\pi)^{K_v/2}$:
$$\log L_{\text{Laplace}}(\boldsymbol{\theta}) \approx \log p(\mathbf{y}, \hat{\mathbf{v}} \mid \boldsymbol{\theta}) + \frac{K_v}{2}\log(2\pi) - \frac{1}{2}\log\det\left(-\nabla_\mathbf{v}^2 \log p(\mathbf{y}, \hat{\mathbf{v}})\right)$$
Notice that the prior normalization constant $-\frac{K_v}{2}\log(2\pi)$ and the Laplace Gaussian integral factor $+\frac{K_v}{2}\log(2\pi)$ **EXACTLY CANCEL**:
$$\mathbf{\log L_{\text{Laplace}}(\boldsymbol{\beta}, \phi, \sigma_s, \sigma_u) = \sum_k \ell(y_k \mid \hat{\mathbf{v}}, \phi) - \frac{1}{2}\hat{\mathbf{v}}^T \boldsymbol{\Sigma}_\theta^{-1}\hat{\mathbf{v}} - \frac{1}{2}\log\det(\boldsymbol{\Sigma}_\theta) - \frac{1}{2}\log\det\left(-\nabla_\mathbf{v}^2 h(\hat{\mathbf{v}})\right)}$$
where:
1. **Inner Optimization**: For fixed outer parameters $(\boldsymbol{\beta}, \phi, \sigma_s, \sigma_u)$, the conditional mode $\hat{\mathbf{v}}$ is computed via Newton-Raphson / L-BFGS over $\mathbb{R}^{132}$.
2. **Observed Hessian**: $-\nabla_\mathbf{v}^2 h(\hat{\mathbf{v}}) = \boldsymbol{\Sigma}_\theta^{-1} + \mathbf{Z}^T \mathbf{W}^{\text{obs}}(\hat{\mathbf{v}}) \mathbf{Z}$, where $\mathbf{W}^{\text{obs}} = \operatorname{diag}(w_k^{\text{obs}})$.
3. **No Dangling Constants**: Canceling the prior constant ensures that likelihood comparisons across fallback levels with different random-effect dimensions (e.g. Level 1 $K_v=132$ vs Level 2 $K_v=12$) remain mathematically consistent and free of arbitrary offsets.
4. **Outer Optimization**: Evaluated via L-BFGS-B / Adam over outer parameters $(\boldsymbol{\beta}, \log \phi, \log \sigma_s, \log \sigma_u)$.

### 5.3 Multi-Dataset Validation & Calibrated Interpretation Scope
- **Validation Evidence**: Tested across 5 independent synthetic datasets of 21,600 rows each:
  - $\hat{\phi} = 7.96 \pm 0.20$ (True: $8.00$)
  - $\hat{\sigma}_s = 0.157 \pm 0.039$ (True: $0.150$)
  - $\hat{\sigma}_u = 0.094 \pm 0.003$ (True: $0.100$)
  - $\hat{\beta}_{\text{noise\_5db}} = 0.169 \pm 0.024$ (True: $0.180$)
  - This parameter recovery confirms that the solver reliably recovers the variance components and dispersion parameter. It serves as strong software-engineering validation, while finite-sample uncertainty for inference remains governed by cluster degrees of freedom.
- **Restricted Model Interpretation**:
  The secondary GLMM deliberately omits `Model × Condition` ($2 \times 4 = 8$ df) to maintain model parsimony on $N=12$ speakers. The model evaluates average acoustic stress impacts and method-specific stress resilience, but **does NOT claim to characterize architecture-specific sensitivity to each acoustic condition**. Terms will not be added opportunistically post-hoc.

### 5.4 Prediction Targets: Cohort-Standardized vs. Population-Marginal
When generating counterfactual rate predictions via G-computation:
- **Cohort-Standardized Target**: Standardizes over the empirical distribution of observed speaker and utterance clusters:
  $$\hat{\mu}^{\text{cohort}} = \frac{1}{N_{\text{obs}}} \sum_{k=1}^{N_{\text{obs}}} \exp(\mathbf{x}^T \boldsymbol{\beta} + \hat{b}_{s(k)} + \hat{u}_{i(k)})$$
- **Population-Marginal Target**: Integrates over the theoretical distribution of random effects using the log-normal expectation identity:
  $$\mathbb{E}_{\mathbf{v}}[\exp(\mathbf{x}^T \boldsymbol{\beta} + b_s + u_i)] = \exp\left(\mathbf{x}^T \boldsymbol{\beta} + \frac{\sigma_s^2 + \sigma_u^2}{2}\right)$$
The primary safety evaluation reports cohort-standardized rates matching the observed sample.

### 5.5 Model Fallback Hierarchy & Small-Cluster Degrees of Freedom
To guard against numerical non-convergence while maintaining strict statistical validity, a 4-tier fallback hierarchy is preregistered:
- **Level 1 (Primary Default)**:
  - *Specification*: Crossed/Hierarchical Negative Binomial GLMM with Laplace marginal approximation ($b_s, u_i$).
  - *Trigger*: Primary default model.
- **Level 2 (Single-Cluster Random Intercept)**:
  - *Specification*: Negative Binomial GLMM with speaker random intercepts only ($b_s$).
  - *Trigger*: Level 1 non-convergence, singular Hessian, or boundary variance estimate ($\hat{\sigma}_u < 10^{-4}$).
- **Level 3 (Poisson GLM with Cluster-Robust Sandwich)**:
  - *Specification*: Quasi-Poisson / Poisson GLM with cluster-robust standard errors clustered on 12 speaker clusters.
  - *Small-Cluster Policy*: With $G=12$ independent clusters, standard sandwich estimators are biased downward. Critical values must use Student-$t$ distribution with $df = G - 1 = 11$ degrees of freedom. Results are treated as exploratory sensitivity checks.
  - *Trigger*: Level 2 non-convergence or $\hat{\phi} \to \infty$.
- **Level 4 (Continuous Log-Rate Linear Model)**:
  - *Specification*: Weighted linear regression on transformed utterance log-rates $y_i = \log((E + 0.5) / N_i)$ with cluster-robust standard errors ($df = 11$).
  - *Trigger*: Optimization failure across all GLM/GLMM solvers.
  - *Removal of Empirical Logit*: The empirical logit $\log((E+0.5)/(N - E + 0.5))$ has been **completely removed** from all fallback specifications because edit distance $E = S + D + I$ can exceed word count $N_i$, rendering the binomial denominator negative and mathematically undefined.

---

## 6. Metric Validation vs. Formal Safety Gate Controller Validation (P0-4)

The protocol establishes a strict boundary between arithmetic metric calculations and formal safety decisions:

1. **Metric Validation (Tests A, B, C)**:
   - Verifies the arithmetic correctness of $\Delta_R, \Delta_g, \max_g \Delta_g, \Delta_D$.
   - *Test A (Uniform Change)*: All groups improve by -5.0 pp $\implies \Delta_R = -5.00$ pp, $\Delta_D = 0.00$ pp, $\max_g \Delta_g = -5.00$ pp.
   - *Test B (Subgroup Harm)*: Overall improves (-4.17 pp), 1 group regresses (+5.0 pp) $\implies \max_g \Delta_g = +5.00$ pp, $\Delta_D = +11.00$ pp.
   - *Test C (Disparity Shrinkage)*: Overall worsens (+13.33 pp), disparity shrinks (-20 pp) $\implies \Delta_R = +13.33$ pp, $\Delta_D = -20.00$ pp.
2. **Controller Validation (Frozen Tripartite UCB95 Rule)**:
   - Evaluates whether the formal DSG safety gate accepts or rejects candidate updates.
   - *Gate Case 1 (Safe Candidate)*: $UCB_{95}(\Delta_R) \le 0.00$, $UCB_{95}(\max \Delta_g) \le 0.02$, $UCB_{95}(\Delta_D) \le 0.02 \implies$ **ACCEPT**.
   - *Gate Case 2 (Point-Safe, UCB-Breached)*: Point estimates $\Delta_R = -0.02$, $\max \Delta_g = +0.0150 \le 0.0200$, BUT $UCB_{95}(\max \Delta_g) = +0.0280 > 0.0200 \implies$ **REJECT**. (Point estimates alone are strictly insufficient for deployment!).
   - *Gate Case 3 (Subgroup Harm)*: $UCB_{95}(\max \Delta_g) = +0.0700 > 0.0200 \implies$ **REJECT**.
   - *Gate Case 4 (Disparity Shrinkage with Overall Risk)*: $UCB_{95}(\Delta_D) = -0.1500 \le 0.0200$, BUT $UCB_{95}(\Delta_R) = +0.1600 > 0.0000 \implies$ **REJECT**. (Negative $\Delta_D$ cannot override overall risk!).

---

## 7. Stratified Paired Bootstrap Combinatorics & Limitations (P0-5)

- **Stratified Paired Protocol**:
  The 12 speakers belong to 6 accent strata ($G_k = \{s_{k,1}, s_{k,2}\}$). In each bootstrap replicate $b \in \{1,\dots,1000\}$, exactly 2 speakers are sampled with replacement within each stratum, ensuring all 6 accent groups are 100% preserved. The exact same resampled speakers are evaluated under both adapted and No-Adapt conditions.
- **Combinatorial Support (729 Multisets)**:
  Within each stratum, sampling pairs with replacement yields 3 combinations: $\{s_1, s_1\}$, $\{s_1, s_2\}$, $\{s_2, s_2\}$. Across 6 strata, there are:
  $$3^6 = \mathbf{729\text{ distinct unordered multisets}}$$
- **Explicit Finite-Sample Limitation**:
  Generating $B=1000$ replicates controls the computational precision of the percentile bootstrap; it does **not** create 1,000 independent speakers. The bootstrap accounts for resampling sensitivity across the 12 observed speakers.

---

## 8. Adaptation Execution Mode & Reproducibility (P0-6)

- **Execution Mode**: `model.eval()`.
- **Dropout State**: Inactive ($p=0.0$).
- **Gradients**: Enabled via `torch.enable_grad()` for adapted LayerNorm parameters.
- **Stage 3M vs. Stage 4M Disclosure**: Stage 3M ran with dropout layers active during adaptation. Stage 4M operates under `model.eval()` with dropout inactive, stabilizing unsupervised entropy gradients and guaranteeing deterministic reproduction.
- **Run-Level Seed Policy & Prohibition of Per-Window Resets**: Each experimental stream run $(m, j, o, c)$ is assigned a unique 32-bit seed derived from SHA256. The RNG advances naturally across all 30 prediction windows with a strict prohibition of per-window resets.

---

## 9. Summary of Protocol Invariants

| Protocol Item | Pre-Registered Specification | Status |
| :--- | :--- | :--- |
| **Observation Grain** | Utterance-level record ($E_i, \log N_i$) | **FROZEN (21,600 rows)** |
| **Prediction Windows** | 30 prediction windows per stream ($W = 120 / 4$) | **FROZEN (Reconciled)** |
| **Terminal Window Rule** | Windows 0..28 adapt; Window 29 evaluated only | **FROZEN** |
| **Fixed-Effect Model** | 36 parameters (Intercept + 4 mains + 3 two-way interactions) | **FROZEN & VERIFIED (Rank 36)** |
| **Primary Safety Assessment** | Primary Retrospective Stage 4M Safety Assessment (Analysis A) | **FROZEN (Offline Only)** |
| **Operational DSG Controller** | Online candidate acceptance via disjoint Sentinel Panel ($N=30$) | **FROZEN (Disjoint Data)** |
| **Unit Contract** | Fractional internal ($0.0000, 0.0200, 0.0200$) / Percentage points reporting ($0.00, 2.00, 2.00$ pp) | **FROZEN & ENFORCED** |
| **Secondary Model** | Omnibus GLMM with Laplace marginal approximation (Analysis B) | **FROZEN & VALIDATED** |
| **Repeated Observations** | No-Adapt order duplicates absorbed by utterance random intercept $u_i$ | **FROZEN & DOCUMENTED** |
| **Model Scope** | `Model × Condition` omitted to preserve parsimony on $N=12$ speakers | **FROZEN RESTRICTION** |
| **Formal Safety Gate** | Tripartite UCB95 rule ($\epsilon_R=0.00, \epsilon_G=0.02, \epsilon_D=0.02$) | **FROZEN & VERIFIED** |
| **Bootstrap Procedure** | Stratified Paired Speaker Bootstrap ($B=1000$, 729 multisets) | **FROZEN** |
| **Adaptation Mode** | `model.eval()` with dropout inactive; LayerNorm gradients active | **FROZEN & DISCLOSED** |
| **Historical Results** | Stage 0–6 and Stage 3M experimental results | **IMMUTABLE** |
| **Execution State** | Full Stage 4M experimental matrix run | **ON HOLD (NO-GO)** |
