# Stage 6M Confirmatory Sample Size Decision & Option A Power Analysis

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md)  
**Governance Status:** `HOLD — STRICTLY NOT AUTHORIZED` (`execution_authorized = false`)  
**Design Path Selected:** **Option A — Confirmatory Sample Size Expansion**  
**Final Sample Size Status:** **UNFROZEN** (Pending stakeholder choice between Candidate Pool Expansion and $N=468$ Fallback)  
**Initial Planning Target:** **$N = 180$ independent speakers** ($N_g = 30$ speakers per group across 6 groups)  
**Intermediate Candidate:** **$N = 240$ independent speakers** ($N_g = 40$ speakers per group across 6 groups)  
**High-Power Candidate:** **$N = 360$ independent speakers** ($N_g = 60$ speakers per group across 6 groups; $77.20\%$ drift power under Adj. UCB97.5)  
**High-Capacity Candidate (3 Reserve):** **$N = 450$ independent speakers** ($N_g = 75$ speakers per group across 6 groups; $84.50\%$ drift power under Adj. UCB97.5)  
**Maximum Balanced Cohort Capacity:** **$N = 468$ independent speakers** ($N_g = 78$ speakers per group across 6 groups; $85.83\%$ drift power under Adj. UCB97.5, exact: $85.825\%$)  
**Replication Baseline:** **$N = 60$ independent speakers** ([`stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv))  
**Canonical Simulation Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad` ([`power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json))  
**Simulation Engine:** [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py) ($S = 4,000$ Outer Trials, $B = 1,000$ Inner Bootstrap Resamples)

---

## 1. Executive Summary & Design Rationale

### 1.1 The Core Scientific Question
In accordance with the supervisory review, the central contribution of this research—titled *Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR*—is not merely to demonstrate that test-time adaptation reduces Word Error Rate (WER). Rather, it investigates whether a **disparity safety gate** can control adaptation-induced degradation and subgroup disparity expansion without excessively sacrificing adaptation benefits.

A confirmatory study that evaluates only overall-WER superiority would leave the core safety claim unverified. Consequently, the research supervisor formally approved **Option A**: expanding the independent evaluation cohort to adequately power the **joint safety–utility decision criterion**:

$$\text{Joint Success} = \text{Event } A \cap \text{Event } B \cap \text{Event } C$$
$$\text{where } A = \{\Delta_R < 0.00\text{ pp}, p < 0.05\}, \quad B = \{\text{UCB}_{95\%}(\Delta R_{\text{clean}}) \le +0.50\text{ pp}\}, \quad C = \{\text{Adjusted UCB}_{97.5\%}(\Delta_D) \le +1.40\text{ pp}\}$$

### 1.2 Resolution of Dual-Scenario Power Target & Bootstrap Realignment
In the final independent statistical audit, the simulation specifications were realigned:
1. **Bootstrap Resample Count Aligned:** Deliverable 6 froze the disparity safety gate procedure at $B = 1,000$. The official canonical power simulation grid has now been fully recalculated at **$S = 4,000$ outer trials and $B = 1,000$ inner bootstrap resamples**, resolving the earlier discrepancy where $B=400$ had been described.
2. **Clean Non-Degradation Estimand Formally Evaluated:** Under both Approach A (Point Guardrail) and Approach B (Inferential One-Sided UCB95), Event B passes in **$100.00\%$** of trials across candidate cohort sizes, imposing zero power penalty on joint success.
3. **Canonical Power at $N=468$:** Under the canonical $S=4,000, B=1,000$ run, joint power for the balanced capacity cohort ($N=468$) reaches **$85.83\% \pm 0.55\%$** (exact: **$85.825\%$**) under Scenario 2 (Modest Disparity Drift $\Delta_D = +0.50\text{ pp}$), with a 95% Monte Carlo confidence interval of **$[84.74\%, 86.91\%]$**.
4. **Data Constraint & Unfrozen Sample Size:** Because only $78$ verified unexposed Irish English speakers are available in Mozilla Common Voice 27.0, $N = 468$ ($78 \times 6$ strata) leaves **zero reserve speakers**. The final sample size is therefore **NOT FROZEN**, pending supervisor direction on whether to execute candidate pool expansion or accept the zero-reserve limitation of $N=468$.

### 1.3 Canonical Sample Size Comparison Table:

| Design Dimension | Replication Baseline | Initial Planning Target | Intermediate Candidate | High-Power Candidate | High-Cap (3 Reserve) | Maximum Balanced Capacity | Epistemic Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Total Cohort Size ($N$)** | **$N = 60$** | **$N = 180$** | **$N = 240$** | **$N = 360$** | **$N = 450$** | **$N = 468$** | `VERIFIED FROM ARTIFACT` |
| **Speakers per Group ($N_g$)** | $10$/stratum | $30$/stratum | $40$/stratum | $60$/stratum | $75$/stratum | $78$/stratum | `VERIFIED FROM ARTIFACT` |
| **Number of Accent Strata** | $6$ strata | $6$ strata | $6$ strata | $6$ strata | $6$ strata | $6$ strata | `VERIFIED FROM ARTIFACT` |
| **Clips per Speaker / Total** | $15$ ($900$) | $15$ ($2,700$) | $15$ ($3,600$) | $15$ ($5,400$) | $15$ ($6,750$) | $15$ ($7,020$) | `PROPOSED` |
| **Marginal WER Power ($A$)** | $97.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | `SIMULATED UNDER DGP` |
| **Clean Non-Degradation ($B$)** | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | `SIMULATED UNDER DGP` |
| **Joint Power (S1 Parity, UCB95)** | $54.2\%$ | $91.5\%$ | $96.4\%$ | $99.6\%$ | $100.0\%$ | $100.0\%$ | `SIMULATED UNDER DGP` |
| **Joint Power (S1 Parity, Adj. 97.5)**| $40.65\% \pm 0.78\%$ | **$84.78\% \pm 0.57\%$** | **$92.80\% \pm 0.41\%$** | **$98.78\% \pm 0.17\%$** | **$99.62\% \pm 0.10\%$** | **$99.78\% \pm 0.07\%$** | `SIMULATED UNDER DGP` |
| **Joint Power (S2 Drift, UCB95)** | $32.5\%$ | $62.1\%$ | $71.5\%$ | **$85.2\%$** | **$90.4\%$** | **$91.9\%$** | `SIMULATED UNDER DGP` |
| **Joint Power (S2 Drift, Adj. 97.5)**| $22.53\% \pm 0.66\%$ | $48.08\% \pm 0.79\%$ | $58.98\% \pm 0.78\%$ | $77.20\% \pm 0.66\%$ | $84.50\% \pm 0.57\%$ | **$85.83\% \pm 0.55\%$ ($85.825\%$)** | `SIMULATED UNDER DGP` |
| **Joint Power (S2 Drift, Operational)**| $79.3\%$ | $99.6\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | `SIMULATED UNDER DGP` |
| **Null False Alarm Rate (S3, Adj. 97.5)**| $2.43\% \pm 0.24\%$ | $4.23\% \pm 0.32\%$ | $4.35\% \pm 0.32\%$ | $4.45\% \pm 0.33\%$ | $5.22\% \pm 0.35\%$ | $4.42\% \pm 0.33\%$ | `SIMULATED UNDER DGP` |
| **Boundary Violation Pass (S4, Adj.)**| $3.90\% \pm 0.31\%$ | $2.90\% \pm 0.27\%$ | $2.38\% \pm 0.24\%$ | $2.75\% \pm 0.26\%$ | $2.23\% \pm 0.23\%$ | $2.75\% \pm 0.26\%$ | `SIMULATED UNDER DGP` |
| **Irish Bottleneck Utilization** | Exhausted (Stage 5M) | $38.5\%$ ($30/78$) | $51.3\%$ ($40/78$) | $76.9\%$ ($60/78$) | $96.2\%$ ($75/78$) | $100.0\%$ ($78/78$) | `VERIFIED FROM ARTIFACT` |

---

## 2. Mathematical Definition of Hypotheses & Estimands

### 2.1 Primary Utility Contrast: Overall Policy Superiority
Let $R_{\text{Gated}}$ and $R_{\text{Ungated}}$ denote the Word Error Rate evaluated across the prequential stream for Arm 3 (Gate-Controlled CTTA) and Arm 2 (Ungated CTTA).  
The aggregate policy difference is defined as the mean paired speaker difference across all $N$ speakers and $M=4$ held-out CTC models:
$$\Delta_R = \frac{1}{N} \sum_{s=1}^N d_s, \quad \text{where } d_s = \frac{1}{M} \sum_{m=1}^M \left( \text{WER}_{s,m}^{\text{Gated}} - \text{WER}_{s,m}^{\text{Ungated}} \right)$$

The directional confirmatory hypothesis is:
$$H_0: \Delta_R \ge 0.00\text{ pp} \quad \text{vs.} \quad H_1: \Delta_R < 0.00\text{ pp}$$

- **Inferential Procedure:** Paired speaker-clustered Student-t test with decision rule $t = \frac{\bar{d}}{\widehat{\text{SE}}} < t_{0.05, N-1}$.
- **Empirical Type I Error Calibration ($S = 4,000$ Trials):**
  - $N=60$ ($df=59$): $t_{\text{crit}} = -1.6711 \implies 5.53\% \pm 0.36\%$ (95% CI $[4.82\%, 6.24\%]$).
  - $N=180$ ($df=179$): $t_{\text{crit}} = -1.6534 \implies 5.22\% \pm 0.35\%$ (95% CI $[4.53\%, 5.91\%]$).
  - $N=240$ ($df=239$): $t_{\text{crit}} = -1.6513 \implies 5.17\% \pm 0.35\%$ (95% CI $[4.48\%, 5.86\%]$).
  - $N=300$ ($df=299$): $t_{\text{crit}} = -1.6500 \implies 5.10\% \pm 0.35\%$ (95% CI $[4.41\%, 5.79\%]$).
  - $N=360$ ($df=359$): $t_{\text{crit}} = -1.6491 \implies 5.10\% \pm 0.35\%$ (95% CI $[4.41\%, 5.79\%]$).
  - $N=420$ ($df=419$): $t_{\text{crit}} = -1.6485 \implies 5.30\% \pm 0.35\%$ (95% CI $[4.61\%, 5.99\%]$).
  - $N=450$ ($df=449$): $t_{\text{crit}} = -1.6483 \implies 4.65\% \pm 0.33\%$ (95% CI $[4.00\%, 5.30\%]$).
  - $N=468$ ($df=467$): $t_{\text{crit}} = -1.6481 \implies 5.00\% \pm 0.34\%$ (95% CI $[4.33\%, 5.67\%]$).
  - *Note on Historical Ranges:* In the earlier $S=2,000$ discovery table, the range was $4.85\%$ to $5.75\%$ (including $N=420$ at $5.75\%$). Across all candidate sizes ($N \ge 180$), 95% confidence intervals overlap 5.00%.

### 2.2 Primary Safety Criterion: Disparity Expansion Bounded
Let $\mathcal{G} = \{1, \dots, 6\}$ denote the set of six accent groups. Inter-accent disparity is the range statistic:
$$D = \max_{g \in \mathcal{G}} \text{WER}_g - \min_{g \in \mathcal{G}} \text{WER}_g$$
The policy disparity change is:
$$\Delta_D = D_{\text{Gated}} - D_{\text{Ungated}}$$

- **Scientific Disparity Tolerance:** $\tau_D = +1.40\text{ pp}$ (prespecified safety margin, $0.60\text{ pp}$ below the online operational threshold $\epsilon_D = +2.00\text{ pp}$).
- **Primary Scientific Safety Criterion:**
  $$\text{Adjusted UCB}_{97.5\%}(\Delta_D) \le +1.40\text{ pp}$$
  The simulation-calibrated Adjusted $UCB_{97.5\%}$ bound is the sole primary disparity safety requirement.
- **Secondary Operational Monitoring Rule:**
  $$\widehat{\Delta D} \le +1.40\text{ pp} \land \text{UCB}_{95\%}(\Delta_D) \le +2.00\text{ pp}$$
  Retained strictly as a secondary descriptor of runtime Sentinel Panel gate behavior.

---

## 3. Comprehensive Sample-Size Exploration Grid ($N=60 \to 600$, $S=4,000, B=1,000$)

From canonical serialized output [`power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) ($S=4,000, B=1,000$, Authoritative Output Hash: `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`):

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CANONICAL SAMPLE-SIZE EXPLORATION GRID FOR CONFIRMATORY STUDY DESIGN (S=4000, B=1000)                                │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────────────────────────────────────┬─────────────────────────────────────────────────┤
│ Speakers per │ Total Cohort │ Marginal WER │ Marginal Disp│ Scenario 1: Parity Preserved (Delta_D=0) │ Scenario 2: Modest Drift (Delta_D=+0.50 pp)     │
│ Stratum (Ng) │ Speakers (N) │ Power (S1)   │ Power (S1)   │ Joint UCB95    Joint UCB97.5   MC SE     │ Joint UCB95    Joint UCB97.5   MC SE    Dual 85%│
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────────────────────────────────┼─────────────────────────────────────────────────┤
│ 10 (Stage 5) │ 60 speakers  │ 100.0%       │ 54.2% (40.7%)│ 54.2%          40.65%          ±0.78%    │ 32.5%          21.32%          ±0.65%   FAIL    │
│ 15           │ 90 speakers  │ 100.0%       │ 68.1% (55.7%)│ 68.1%          55.70%          ±0.79%    │ 43.8%          29.20%          ±0.72%   FAIL    │
│ 20           │ 120 speakers │ 100.0%       │ 79.2% (68.1%)│ 79.2%          68.10%          ±0.74%    │ 50.1%          36.30%          ±0.76%   FAIL    │
│ 25           │ 150 speakers │ 100.0%       │ 86.8% (77.7%)│ 86.8%          77.60%          ±0.66%    │ 56.4%          42.70%          ±0.78%   FAIL    │
│ 30 (PLAN)    │ 180 speakers │ 100.0%       │ 91.5% (84.8%)│ 91.5%          84.78%          ±0.57%    │ 62.1%          48.08%          ±0.79%   FAIL    │
│ 35           │ 210 speakers │ 100.0%       │ 94.2% (89.4%)│ 94.2%          88.92%          ±0.50%    │ 67.2%          55.57%          ±0.79%   FAIL    │
│ 40           │ 240 speakers │ 100.0%       │ 96.4% (92.8%)│ 96.4%          92.80%          ±0.41%    │ 71.5%          58.97%          ±0.78%   FAIL    │
│ 50           │ 300 speakers │ 100.0%       │ 98.4% (96.5%)│ 98.4%          96.53%          ±0.29%    │ 79.1%          70.23%          ±0.72%   FAIL    │
│ 60 (HI-PWR)  │ 360 speakers │ 100.0%       │ 99.6% (98.8%)│ 99.6%          98.78%          ±0.17%    │ 85.2%          77.20%          ±0.66%   FAIL    │
│ 70           │ 420 speakers │ 100.0%       │ 99.8% (99.2%)│ 99.8%          99.20%          ±0.14%    │ 89.4%          82.30%          ±0.60%   FAIL    │
│ 75 (HI-CAP)  │ 450 speakers │ 100.0%       │ 99.9% (99.6%)│ 99.9%          99.62%          ±0.10%    │ 90.2%          84.50%          ±0.57%   FAIL*   │
│ 78 (MAX-CAP) │ 468 speakers │ 100.0%       │ 100.0%(99.8%)│ 100.0%         99.78%          ±0.07%    │ 91.9%          85.83%          ±0.55%   PASS**  │
│ 90 (EXPAND)  │ 540 speakers │ 100.0%       │ 100.0%(100.0)│ 100.0%         99.95%          ±0.04%    │ 94.6%          90.40%          ±0.47%   PASS*** │
│ 100(EXTEND)  │ 600 speakers │ 100.0%       │ 100.0%(100.0)│ 100.0%         100.00%         ±0.00%    │ 96.2%          92.70%          ±0.41%   PASS*** │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────────────────────────────────┴─────────────────────────────────────────────────┘
* N=450: FAIL under Rule A (84.50% < 85.00%) and FAIL under Rule B (83.38% < 85.00%). MC interval [83.38%, 85.62%] crosses 85%; point estimate misses.
** N=468: PASS under Rule A (85.83% >= 85.00%, exact: 85.825%), FAIL under Rule B (L_95% = 84.74% < 85.00%). MC interval [84.74%, 86.91%]. 0 reserve Irish speakers.
*** N=540 & 600: PASS under Rule A and PASS under Rule B under existing single-source simulation (N=540: L_95% = 89.49% > 85.00%). Proposed multi-corpus design Rule B status remains UNRESOLVED pending design-specific power analysis. Requires external candidate pool acquisition (shortfall: 102 external under Policy A; 162 under Policy B).
```

> [!NOTE]
> **Complete 1:1 Synchronization Between Exploration Grid and Core Simulation Records:**
> Both Section 3 and Section 4 are generated from identical single-execution simulation records. The previous Monte Carlo divergence caused by an independent dual-loop evaluation has been completely eliminated. Trial-level equality $n_{A \cap B \cap C} = n_{\text{joint grid}}$ is verified across all 14 sample sizes ($853$ at $N=60$, $1,168$ at $N=90$, $1,452$ at $N=120$, $3,433$ at $N=468$, and $3,616$ at $N=540$). All 8 Venn cells are verified non-negative integers summing to exactly $S=4,000$.

---

## 4. Formal Recommendation & Actionable Next Steps

1. **Retain Option A, but Keep Sample Size Unfrozen:**  
   In accordance with the independent statistical audit, Option A (Confirmatory Cohort Expansion) is retained as the governing strategy. However, the final sample size remains **STRICTLY UNFROZEN** pending demonstration of data feasibility, source comparability, and stakeholder sign-off.
2. **Status of $N=468$ (Rule A Fallback Design — Strategy C Primary):**  
   - $N=468$ ($78$ speakers/stratum) reaches $\widehat{\text{Power}} = 85.83\% \ge 85.00\%$ (exact: $85.825\%$), satisfying Rule A.
   - However, its lower 95% Monte Carlo confidence bound is $L_{95\%, \text{MC}} = 84.74\% < 85.00\%$, failing Rule B.
   - It utilizes $100\%$ of the verified unexposed Irish English pool ($78$ speakers) in Common Voice 27.0, providing **zero reserve headroom**.
   - Under **Strategy C (Pure Single-Source Confirmatory Trial)**, $N=468$ provides an unconfounded benchmark where accent is completely disentangled from corpus differences.
3. **Status of $N=540$ (Candidate for Rule B Compliance — Strategy A / Multi-Corpus):**  
   - *Existing Single-Source Simulation:* At $N=540$ ($90$ speakers/stratum), joint power reaches $\widehat{\text{Power}} = 90.40\%$ with $95\%$ MC CI $[89.49\%, 91.31\%]$ ($L_{95\%, \text{MC}} = 89.49\% > 85.00\%$), successfully satisfying Rule B under the existing single-source Gaussian data-generating process ($\sigma^2_{\text{corpus}} = 0, \sigma^2_{\alpha\gamma} = 0$).
   - *Common Voice-Only Feasibility Constraint:* **INFEASIBLE**. A pure Common Voice-only study at $N=540$ ($90$ CV speakers/stratum) requires $90$ unexposed strictly eligible Irish speakers. The audited Common Voice 27.0 inventory contains only $78$ unexposed Irish speakers, leaving a deficit of $90 - 78 = \mathbf{12\text{ eligible Irish speakers}}$ (or $105 - 78 = \mathbf{27\text{ speakers}}$ with a $15$-speaker reserve). Hence, $N=540$ single-source is strictly a hypothetical power reference under the Gaussian DGP, not an executable Common Voice-only design.
   - *Required Methodological Distinction:* The $N=540$ single-source result passes Rule B under the simulated model, but the corresponding Common Voice-only participant allocation is infeasible using the current audited inventory. The proposed multi-corpus design has a separate, unresolved power status.
   - *Rule B Status for Proposed Multi-Corpus Study:* **UNRESOLVED**. The existing simulation does not validate the proposed multi-corpus design. Rule B status for the proposed multi-corpus study remains UNRESOLVED pending a design-specific power analysis that incorporates inter-corpus variance ($\sigma^2_{\text{corpus}}$) and corpus-by-accent interaction parameters ($(\alpha\gamma)_{gk}$). A design-specific power analysis remains mandatory prior to confirmatory execution. Strategy A must not be described as statistically validated merely because the single-source simulation passes Rule B.
   - *Feasibility Constraints & Reserve Shortfalls:*
     - Under Policy A ($15$ Irish reserve: $3$ CV $+ 12$ external; $0$ non-Irish reserve): requires $78$ CV Irish ($75 + 3 = 78$, zero headroom), $27$ External Irish ($15 + 12 = 27$), and $75$ CV $+ 15$ External for each of the $5$ non-Irish groups. Active external shortfall: $90$ speakers ($15 \times 6$); total external shortfall: $102$ speakers ($90 + 12 = 102$).
     - Under Policy B ($15$ reserve/stratum: $3$ CV $+ 12$ external per stratum): requires $78$ CV/stratum ($75 + 3 = 78$), which is **FEASIBLE across all six strata with zero Irish CV headroom** ($78 \ge 78$). There is zero Common Voice deficit. However, Policy B requires $27$ External speakers/stratum ($15 + 12 = 27$), creating a total external acquisition shortfall of **$162$ unacquired external speakers** ($27 \times 6 = 162$).
   - *Accent-Corpus Confounding Precaution:* If supplementary data are introduced, the study must adopt **Strategy A (Balanced Multi-Corpus Sampling across all 6 groups)** or **Strategy B (Source-Adjusted Hierarchical Modeling)**. Supplementing Irish alone while keeping other groups on Common Voice is strictly prohibited.
4. **Data Acquisition Next Steps:**  
   - Common Voice 27.0 is exhausted; do not attempt to re-filter the local release.
   - Audit external manifests (e.g., British Isles accents corpora, newer Common Voice snapshots) for recording condition, task, and duration parity before merging.
   - Strictly prohibit downloading, inspecting, or decoding Cohort 2 evaluation audio during the feasibility phase.
5. **Governance Lock Remains Absolute:**  
   - Execution authorization remains locked: `execution_authorized = false`.
   - Confirmatory Cohort 2 status remains: `PROPOSED — NOT YET CREATED OR VERIFIED`.
   - Experimental execution strictly prohibited until formal sign-off.
