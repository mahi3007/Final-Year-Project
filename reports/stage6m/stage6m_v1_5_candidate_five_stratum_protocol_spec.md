# Stage 6M — Five-Stratum Candidate Protocol Specification (v1.5.0-Candidate)
================================================================================

| Parameter | Specification |
|:---|:---|
| **Document State** | `CANDIDATE_PROTOCOL_SPECIFICATION` (Pre-Registration Draft) |
| **Governance Standard** | ADR-005; Protocol Section 14.7 (`PROJECT_LEAD_ACADEMIC_AUTHORIZATION`) |
| **Governance Status** | `DRAFT_HOLD` (Confirmatory Audio Materialization & Adaptation Strictly Blocked) |
| **Base Baseline** | Protocol v1.4.0 (Frozen 6-Stratum Protocol & Commit Identity Preserved) |
| **Target Population** | 5 Confirmatory Strata + 1 Exploratory Out-of-Domain Stratum |
| **Multiplicity Family** | $M = 8$ Simultaneous Hypotheses |
| **Multiplicity Procedure** | Fixed Simultaneous Bonferroni Adjustment ($\alpha_{\text{adj}} = \alpha / 8 = 0.00625$) |
| **Authoritative Decision Engine** | Simultaneous Upper Confidence Bounds (UCBs) |

---

## 1. Executive Summary & Architectural Separation

Under **Protocol v1.4.0**, confirmatory Decision Rule B specified six canonical accents across 1,440 total speakers (240 per stratum: 220 Cohort 3 evaluation + 20 gate reference). Empirical workspace scans and the independent multi-corpus feasibility audit established that **Mozilla Common Voice 27.0** contains **0 unexposed strictly eligible Irish English speakers**, and external corpora (EdAcc, VoxCeleb) are structurally exhausted or methodologically inadmissible.

Rather than altering the frozen v1.4.0 code identity or attempting silent downsampling, this candidate specification defines a **separately versioned five-stratum research protocol**:

1. **Frozen Baseline Preserved:** The historical v1.4.0 execution code (`src/dsg_ctta/evaluation/paired_cluster_inference.py`), its frozen commit hashes, and its 6-stratum benchmark results remain immutable.
2. **Confirmatory Strata ($K = 5$):** Re-anchored to the five surplus strata in Common Voice 27:
   - Australian English (`en_au`)
   - Canadian English (`en_ca`)
   - England English (`en_uk`)
   - South Asian English (`en_in`)
   - US English (`en_us`)
3. **Exploratory Strata ($K_{\text{expl}} = 1$):** Irish English (`en_ie`) is retained exclusively as an **exploratory out-of-domain case study**. It is formally excluded from the confirmatory hypothesis family and cannot influence confirmatory promotion.

---

## 2. Multiplicity Governance Decision: Fixed Bonferroni vs. Holm

### 2.1 Historical Discrepancy Identified
The independent parity audit (`reports/stage6m/stage6m_inference_parity_audit_report.md`) identified an inconsistency between documentation and code:
- **Governing Documentation:** Module docstrings and `stage6m_rule_b_power_simulation_spec.json` referred to "Holm-Bonferroni across all hypotheses".
- **Production Code:** The frozen implementation evaluates single-step simultaneous Upper Confidence Bounds using $\alpha_{\text{adj}} = \alpha / M$.
- **Protocol §6.3:** Stated that "Holm adjustment is an acceptable transparent default; a validated simultaneous max-statistic procedure is also acceptable if frozen before the study."

### 2.2 Formal Project-Lead Governance Decision
**Decision: The 5-Stratum Candidate Protocol formally prespecifies and freezes the Fixed Single-Step Simultaneous Bonferroni Procedure.**

### 2.3 Mathematical & Methodological Rationale
1. **Direct Parameter Bounds:** The confirmatory criteria require verifying that treatment differences satisfy substantive thresholds:
   - Event A (Static Superiority): $\text{UCB}(\Delta_{\text{static}}) < 0.0$ pp
   - Event B (SUTA Superiority): $\text{UCB}(\Delta_{\text{ungated}}) < 0.0$ pp
   - Event C (Accent Regression): $\text{UCB}(\Delta_g) \le +2.0$ pp for all $g \in \{1, \dots, 5\}$
   - Event D (Disparity Guard): $\text{UCB}(\Delta_D) \le 0.0$ pp
   
   Single-step Bonferroni provides simultaneous confidence bounds $[-\infty, \text{UCB}_m]$ with joint coverage $P(\theta_m \le \text{UCB}_m, \forall m \in \{1,\dots,8\}) \ge 1 - \alpha$. In contrast, stepwise Holm testing operates purely on ordered $p$-values and does not yield coherent simultaneous interval bounds against non-zero margins (such as the $+2.0$ pp regression guard).
2. **Intersection Equivalence & Conservatism:** To claim full confirmatory success, the protocol mandates that **all $M$ null hypotheses must be rejected**. For the intersection event $\bigcap_{m=1}^M \{H_{0,m} \text{ rejected}\}$, the Holm step-down threshold for the least significant test is $\alpha / (M - M + 1) = \alpha$, but the most restrictive test requires $p_{(1)} \le \alpha / M$. Under Bonferroni, every test must satisfy $p_m \le \alpha / M$. Consequently:
   $$\{\text{All } M \text{ rejected under Bonferroni}\} \subseteq \{\text{All } M \text{ rejected under Holm}\}$$
   Bonferroni is strictly conservative. Any study satisfying the Bonferroni criteria is guaranteed to satisfy Holm, fully protecting the family-wise error rate ($\text{FWER} \le 0.05$).
3. **Decision Priority:** In accordance with audit finding §2.3, the **simultaneous Upper Confidence Bounds are authoritative**. If an asymptotic score $p$-value and a Wald/bootstrap UCB produce conflicting indications near the boundary, the prespecified UCB criteria determine the pass/fail disposition.

---

## 3. Five-Stratum Hypothesis Family Architecture ($M = 8$)

The confirmatory family comprises exactly $M = 8$ one-sided hypotheses tested at family-wise error rate $\alpha = 0.05$:

$$\alpha_{\text{adj}} = \frac{0.05}{8} = 0.00625 \quad (0.625\%)$$

The corresponding one-sided simultaneous confidence level for all intervals and quantiles is:

$$\text{Simultaneous Confidence Level} = (1 - \alpha_{\text{adj}}) \times 100\% = 99.375\%$$

### Primary Superiority (Events A & B)
* **Event A ($H_{0,A}: \Delta_{\text{static}} \ge 0$):**
  - Point estimate: $\widehat{\Delta}_{\text{static}} = \text{WER}_{\text{DSG}} - \text{WER}_{\text{static}} < 0.0$ pp.
  - Linearized cluster-robust $t$-UCB:
    $$\text{UCB}_A = \widehat{\Delta}_{\text{static}} + t_{1 - \alpha_{\text{adj}},\, N - 1} \cdot \widehat{\text{SE}}(\widehat{\Delta}_{\text{static}}) < 0.0\text{ pp}$$
* **Event B ($H_{0,B}: \Delta_{\text{ungated}} \ge 0$):**
  - Point estimate: $\widehat{\Delta}_{\text{ungated}} = \text{WER}_{\text{DSG}} - \text{WER}_{\text{ungated}} < 0.0$ pp.
  - Linearized cluster-robust $t$-UCB:
    $$\text{UCB}_B = \widehat{\Delta}_{\text{ungated}} + t_{1 - \alpha_{\text{adj}},\, N - 1} \cdot \widehat{\text{SE}}(\widehat{\Delta}_{\text{ungated}}) < 0.0\text{ pp}$$

### Per-Accent Non-Regression Safety (Event C: Hypotheses 3–7)
For each stratum $g \in \{\text{Australian, Canadian, England, South Asian, US English}\}$:
* **Hypothesis $H_{0,C,g}: \Delta_g > +2.0$ pp:**
  - Within-stratum contrast: $\widehat{\Delta}_g = \text{WER}_{\text{DSG},g} - \text{WER}_{\text{static},g}$.
  - Stratum-specific cluster-robust $t$-UCB:
    $$\text{UCB}_g = \widehat{\Delta}_g + t_{1 - \alpha_{\text{adj}},\, n_g - 1} \cdot \widehat{\text{SE}}(\widehat{\Delta}_g) \le +2.0\text{ pp}$$
  - **Criterion:** Event C passes if and only if $\max_{g \in \{1,\dots,5\}} \text{UCB}_g \le +2.0$ pp.

### Disparity Non-Increase (Event D: Hypothesis 8)
* **Hypothesis $H_{0,D}: \Delta_D > 0.0$ pp:**
  - Cross-accent disparity: $D = \max_{g \in \{1,\dots,5\}} \text{WER}_g - \min_{g \in \{1,\dots,5\}} \text{WER}_g$.
  - Disparity change: $\Delta_D = D_{\text{DSG}} - D_{\text{static}}$.
  - Stratified paired speaker-cluster bootstrap: resample $n_g$ speakers with replacement within stratum $g$ across $B$ replicates.
  - **Criterion:** The $99.375^{\text{th}}$ empirical percentile of bootstrap differences must satisfy:
    $$\text{UCB}_D = \text{Percentile}_{99.375\%}(\Delta_D^{(1)}, \dots, \Delta_D^{(B)}) \le 0.0\text{ pp}$$

### Joint Confirmatory Success
$$\text{Confirmatory Success} \iff \text{Event A} \land \text{Event B} \land \text{Event C} \land \text{Event D}$$

---

## 4. Requirements for Data-Generating Model Reconciliation (Task 3 Scope)

Before running final power evaluations or sample-size sweeps, the candidate power simulator must be reconciled with the design-stage specification:

1. **Speaker-Level Paired Contrast SD:**
   - The residual paired difference variability must be parameterized directly at the speaker level:
     $$\sigma_{\text{paired}} = 0.032 \quad (3.2\text{ pp})$$
   - It must **not** be divided by $\sqrt{C}$ (where $C = 15$ clips), which improperly deflated the simulated noise to $0.83$ pp in prior exploratory runs.
2. **Target Superiority Margins:**
   - The design-stage evaluation scenario must represent the prespecified target treatment effects:
     - Expected DSG superiority vs. Static: $-3.5$ pp
     - Expected DSG superiority vs. Ungated SUTA: $-3.5$ pp
3. **Accent Variation & Disparity Calibration:**
   - In prior runs, independent random accent effects drawn with $\sigma_{\text{accent}} = 0.050$ randomly reshuffled the accent ranking, diluting the nominal $-2.0$ pp disparity reduction to an empirical mean of only $-1.03$ pp and producing $\Delta_D \ge 0$ in $\approx 20\%$ of trials.
   - The candidate simulator must separate the fixed population treatment profile (which achieves the target $-2.0$ pp disparity narrowing) from speaker-level sampling variability, preventing artificial power ceilings.
4. **Bootstrap Tail Resolution:**
   - Monte Carlo power simulations must employ sufficient bootstrap replicates (e.g. $B \ge 2,000$, with sensitivity checks up to $B = 20,000$) to provide stable estimates of the $99.375^{\text{th}}$ percentile.

---

## 5. Capacity Boundaries & Power Acceptance Criteria

1. **Capacity Envelope (Mozilla Common Voice 27.0):**
   - The candidate confirmatory design is bounded by the verified Australian English eligible capacity:
     $$N_{g,\text{total}} \le 305 \implies N_{g,\text{eval}} \le 285 \quad (\text{with } 20 \text{ reserved gate-reference speakers})$$
2. **Acceptance Thresholds:**
   To qualify for consideration under Project-Lead Academic Authorization, the candidate design must demonstrate:
   $$\widehat{P}_{\text{joint}} \ge 0.90 \quad \text{AND} \quad \text{LCB}_{95\%}(\widehat{P}_{\text{joint}}) \ge 0.90$$
   where $\text{LCB}_{95\%}$ is the exact Clopper-Pearson 95% lower confidence bound from at least $S = 10,000$ Monte Carlo trials with $B = 20,000$ bootstrap replicates.
3. **Confirmed Candidate Sample-Size Architecture (Calibrated Model):**
   - **Primary Confirmatory Recommendation ($N_g = 220$, $N_{\text{total}} = 1,100$):**
     - Confirmed Joint Power (Corrected Model): **$90.58\%$** ($9,058 / 10,000$ trials, $B = 20,000$).
     - Exact Confidence Bounds:
       - **One-Sided 95% Clopper-Pearson LCB:** **$90.09\%$** ($90.085739\%$, $\ge 90.0000\% \implies \text{PASS}$ by $+0.0857$ pp / $+8$ trials).
       - **Two-Sided 95% CI Lower Endpoint:** **$89.99\%$** ($89.990601\%$, shortfall of $-0.0094$ pp / $-1$ trial vs $90.0000\%$).
     - Operational Reserve: Preserves **65 strictly eligible unexposed Australian speakers** ($21.3\%$ buffer) as a replacement reserve against physical audio corruption or decoding dropouts.
     - *Historical Superseded Finding:* Task 5 initially reported $95.35\%$ ($95\%$ CI: $[94.92\%, 95.75\%]$) under an uncalibrated generator where clipping induced a $-2.1733$ pp disparity reduction; this is formally superseded by the exact $-2.0000$ pp calibrated estimate.
   - **Ceiling Capacity Benchmark ($N_g = 285$, $N_{\text{total}} = 1,425$):**
     - Benchmark Joint Power: **$96.96\%$** ($2,424 / 2,500$ trials, $B = 20,000$), One-Sided 95% LCB = **$96.33\%$**.
     - Status: **Supplemental Capacity Benchmark Only** (consumes 100% of Australian capacity; leaves zero replacement reserve).
     - *Historical Superseded Finding:* Task 5 reported $98.74\%$ ($95\%$ CI: $[98.50\%, 98.95\%]$).
   - **Conditional Nature Caveat:** All simulated power estimates are conditional on realizing the hypothesized $-2.0$ pp disparity narrowing; if physical narrowing is $\le -1.0$ pp, power degrades below $50\%$. These assumptions represent development-stage design scenario targets rather than physical guarantees.

---

## 6. Implementation Engine & Governance Readiness

1. **Confirmatory Inference Implementation:**
   - Implemented in `src/dsg_ctta/evaluation/paired_cluster_inference_v15.py`.
   - Frozen v1.4.0 execution code (`paired_cluster_inference.py`) remains strictly immutable.
   - Numerical parity with the five-stratum power simulator verified to within $< 10^{-5}$ across all test statistics, UCBs, and event decisions.
2. **Sensitivity Profile:**
   - Primary design is robust ($\ge 90\%$ joint power) against superiority degradations down to $2.0$ pp and between-speaker variance inflation up to $8.5$ pp.
   - Event D (Disparity Safety) is the primary sensitivity bottleneck; power depends critically on achieving non-zero physical disparity narrowing ($\Delta_D \le -1.5$ pp).
3. **Governance Authorization Standard:**
   - Formal transition from `DRAFT_HOLD` to confirmatory execution requires explicit **Project-Lead Academic Authorization** under Protocol Section 14.7.
   - Preserves `DRAFT_HOLD` until formal Project-Lead review and authorization.

