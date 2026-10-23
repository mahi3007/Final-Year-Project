import json
from pathlib import Path

doc_path = Path("reports/stage6m/stage6m_sample_size_decision.md")
with open(doc_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update Comparison Table in Section 1.3
old_table_1_3_marker = "### 1.3 Canonical Sample Size Comparison Table:"
old_section_2_marker = "## 2. Mathematical Definition of Hypotheses & Estimands"

new_table_1_3 = """### 1.3 Canonical Sample Size Comparison Table:

| Design Dimension | Replication Baseline | Initial Planning Target | Intermediate Candidate | UCB95 Dual Candidate | High-Cap (3 Reserve) | Maximum Balanced Capacity | Epistemic Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Total Cohort Size ($N$)** | **$N = 60$** | **$N = 180$** | **$N = 240$** | **$N = 360$** | **$N = 450$** | **$N = 468$** | `VERIFIED FROM ARTIFACT` |
| **Speakers per Group ($N_g$)** | $10$/stratum | $30$/stratum | $40$/stratum | $60$/stratum | $75$/stratum | $78$/stratum | `VERIFIED FROM ARTIFACT` |
| **Number of Accent Strata** | $6$ strata | $6$ strata | $6$ strata | $6$ strata | $6$ strata | $6$ strata | `VERIFIED FROM ARTIFACT` |
| **Clips per Speaker / Total** | $15$ ($900$) | $15$ ($2,700$) | $15$ ($3,600$) | $15$ ($5,400$) | $15$ ($6,750$) | $15$ ($7,020$) | `PROPOSED` |
| **Marginal WER Power ($A$)** | $97.2\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | `SIMULATED UNDER DGP` |
| **Joint Power (S1 Parity, UCB95)** | $54.8\% \pm 1.11\%$ | **$91.2\% \pm 0.63\%$** | **$96.2\% \pm 0.43\%$** | **$99.5\% \pm 0.15\%$** | **$100.0\%$** | **$99.9\% \pm 0.07\%$** | `SIMULATED UNDER DGP` |
| **Joint Power (S1 Parity, Adj. 97.5)**| $41.7\% \pm 1.10\%$ | **$84.8\% \pm 0.80\%$** | **$92.5\% \pm 0.59\%$** | **$98.6\% \pm 0.26\%$** | **$99.7\% \pm 0.12\%$** | **$99.7\% \pm 0.12\%$** | `SIMULATED UNDER DGP` |
| **Joint Power (S2 Drift, UCB95)** | $33.3\% \pm 1.05\%$ | $62.9\% \pm 1.08\%$ | $72.1\% \pm 1.00\%$ | **$85.6\% \pm 0.79\%$** | **$90.8\% \pm 0.65\%$** | **$91.9\% \pm 0.61\%$** | `SIMULATED UNDER DGP` |
| **Joint Power (S2 Drift, Adj. 97.5)**| $23.5\% \pm 0.95\%$ | $51.8\% \pm 1.12\%$ | $61.3\% \pm 1.09\%$ | $77.0\% \pm 0.94\%$ | $83.5\% \pm 0.83\%$ | **$86.4\% \pm 0.77\%$** | `SIMULATED UNDER DGP` |
| **Joint Power (S2 Drift, Operational)**| $62.1\% \pm 1.09\%$ | $95.1\% \pm 0.48\%$ | $98.0\% \pm 0.31\%$ | $99.7\% \pm 0.12\%$ | $99.8\% \pm 0.10\%$ | $99.9\% \pm 0.07\%$ | `SIMULATED UNDER DGP` |
| **Null False Alarm Rate (S3, UCB95)**| $3.2\% \pm 0.39\%$ | $4.6\% \pm 0.47\%$ | $5.0\% \pm 0.49\%$ | $5.9\% \pm 0.53\%$ | $4.3\% \pm 0.45\%$ | $4.7\% \pm 0.47\%$ | `SIMULATED UNDER DGP` |
| **Boundary Violation Pass (S4, Adj.)**| $4.0\% \pm 0.44\%$ | $3.6\% \pm 0.42\%$ | $3.4\% \pm 0.41\%$ | $2.8\% \pm 0.37\%$ | $2.9\% \pm 0.38\%$ | $3.1\% \pm 0.39\%$ | `SIMULATED UNDER DGP` |
| **Irish Bottleneck Utilization** | Exhausted (Stage 5M) | $38.5\%$ ($30/78$) | $51.3\%$ ($40/78$) | $76.9\%$ ($60/78$) | $96.2\%$ ($75/78$) | $100.0\%$ ($78/78$) | `VERIFIED FROM ARTIFACT` |

---

"""

# 2. Update Exploration Grid in Section 3
old_grid_marker = "### 3. Comprehensive Sample-Size Exploration Grid"
old_section_4_marker = "## 4. Analysis of Scenarios & Target Justifications"

new_grid_content = """## 3. Comprehensive Sample-Size Exploration Grid ($N=60 \\to 468$)

Evaluated across $S = 2,000$ Monte Carlo simulation trials per sample size with $B = 400$ stratum bootstrap resamples under the preregistered DGP ($\sigma_{\\text{spk}} = 3.80\\text{ pp}, \\rho = 0.88, \\sigma_{\\text{diff}} = 1.862\\text{ pp}, \\sigma_{\\text{noise}} = 1.316\\text{ pp}$), serialized in [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json):

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CANONICAL SAMPLE-SIZE EXPLORATION GRID FOR CONFIRMATORY STUDY DESIGN (S=2000, B=400)                                 │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────────────────────────────────────┬─────────────────────────────────────────────────┤
│ Speakers per │ Total Cohort │ Marginal WER │ Marginal Disp│ Scenario 1: Parity Preserved (Delta_D=0) │ Scenario 2: Modest Drift (Delta_D=+0.50 pp)     │
│ Stratum (Ng) │ Speakers (N) │ Power (S1)   │ Power (S1)   │ Joint UCB95    Joint UCB97.5   MC SE     │ Joint UCB95    Joint UCB97.5   MC SE    Dual 85%│
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────────────────────────────────┼─────────────────────────────────────────────────┤
│ 10 (Stage 5) │ 60 speakers  │ 97.2%        │ 56.2% (42.8%)│ 54.8%          41.7%           ±1.10%    │ 33.3%          24.4%           ±0.96%   FAIL    │
│ 15           │ 90 speakers  │ 99.7%        │ 68.4% (57.4%)│ 68.1%          57.1%           ±1.11%    │ 44.2%          33.3%           ±1.05%   FAIL    │
│ 20           │ 120 speakers │ 100.0%       │ 79.1% (68.3%)│ 79.1%          68.2%           ±1.04%    │ 50.2%          38.8%           ±1.09%   FAIL    │
│ 25           │ 150 speakers │ 100.0%       │ 86.6% (78.0%)│ 86.6%          78.0%           ±0.93%    │ 56.7%          44.6%           ±1.11%   FAIL    │
│ 30 (TARGET)  │ 180 speakers │ 100.0%       │ 91.2% (84.8%)│ 91.2%          84.8%           ±0.80%    │ 62.9%          52.3%           ±1.12%   FAIL    │
│ 35           │ 210 speakers │ 100.0%       │ 93.7% (88.6%)│ 93.7%          88.5%           ±0.71%    │ 66.9%          54.1%           ±1.11%   FAIL    │
│ 40           │ 240 speakers │ 100.0%       │ 96.3% (92.5%)│ 96.2%          92.5%           ±0.59%    │ 72.1%          62.0%           ±1.09%   FAIL    │
│ 50           │ 300 speakers │ 100.0%       │ 98.1% (96.1%)│ 98.1%          96.1%           ±0.43%    │ 78.9%          69.0%           ±1.03%   FAIL    │
│ 60 (HI-PWR)  │ 360 speakers │ 100.0%       │ 99.5% (98.6%)│ 99.5%          98.6%           ±0.26%    │ 85.6%          76.8%           ±0.94%   PASS*   │
│ 70           │ 420 speakers │ 100.0%       │ 99.6% (99.2%)│ 99.6%          99.2%           ±0.20%    │ 89.6%          82.7%           ±0.85%   PASS*   │
│ 75 (HI-CAP)  │ 450 speakers │ 100.0%       │ 100.0%(99.7%)│ 100.0%         99.7%           ±0.12%    │ 90.8%          84.5%           ±0.81%   PASS*   │
│ 78 (MAX-CAP) │ 468 speakers │ 100.0%       │ 99.9% (99.7%)│ 99.9%          99.7%           ±0.12%    │ 91.9%          86.7%           ±0.76%   PASS**  │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────────────────────────────────┴─────────────────────────────────────────────────┘
* Note: At N=360 to N=450, Dual 85% Target PASSES under the strict UCB95 criterion (85.6% to 90.8%).
** Under conservative Adjusted UCB97.5, drift power clears the >=85% target at N=468 (86.7% +/- 0.76% in exploration grid, 86.4% +/- 0.77% in core battery).
   Under the two-part operational rule, Scenario 2 power is 95.1% at N=180, 99.7% at N=360, and 99.9% at N=468.
```

---

"""

# 3. Update Section 4.4, 4.5 and add 4.6
old_s4_start = "### 4.4 Why $N=360$ Is the Recommended Dual-Scenario Candidate"
old_section_5_marker = "## 5. False Rejection Rates & Safety Suppression at the Boundary"

new_s4_content = """### 4.4 Why $N=360$ Is the UCB95 Dual-Scenario Candidate
At $N=360$ ($60$ speakers/group):
1. **Meets Dual 85% Target under UCB95:** Joint power reaches **$99.5\%$** in Scenario 1 (Parity) and **$85.6\%$** in Scenario 2 (Modest Drift), successfully clearing the $\ge 85\%$ target across both prespecified acceptable conditions.
2. **Deficit under Conservative Adjusted UCB97.5:** Under Adjusted UCB97.5, joint power under $+0.50\\text{ pp}$ drift reaches **$77.0\% \\pm 0.94\%$**, which is $8.0\\text{ pp}$ below the $85\%$ target.
3. **High Power under Operational Rule:** Under the two-part operational rule ($\widehat{\\Delta D} \\le +1.40\\text{ pp} \\land UCB_{95\\%} \\le +2.00\\text{ pp}$), joint power reaches **$99.7\%$** in Scenario 2.
4. **Feasibility:** Utilizes $60$ of $78$ unexposed Irish speakers ($76.9\%$ capacity), leaving $18$ reserve speakers.

### 4.5 The High-Capacity Frontier with Buffer: $N=450$
At $N=450$ ($75$ speakers/group):
1. **Preserves Bottleneck Reserve:** Utilizes $75$ of $78$ unexposed Irish speakers, maintaining a safety margin of $3$ untouched speakers in reserve.
2. **Performance:** Joint power reaches **$90.8\%$** under UCB95 and **$83.5\% \\pm 0.83\%$** under conservative Adjusted UCB97.5 ($99.8\%$ operational rule).

### 4.6 Maximum Balanced Cohort Capacity: $N=468$
At $N=468$ ($78$ speakers/group):
1. **Exhaustion of Limiting Bottleneck:** Deploys all $78$ verified unexposed Irish speakers across 6 strata ($100\\%$ pool capacity).
2. **Clears Dual 85% Target under Adjusted UCB97.5:** Joint power under $+0.50\\text{ pp}$ drift reaches **$86.4\% \\pm 0.77\\%$** ($86.7\\%$ in grid), definitively clearing the $\\ge 85\\%$ target under the conservative error-controlled procedure!
3. **Dual 85% Pass Summary:**
   - Under standard percentile UCB95: $91.9\\%$.
   - Under Adjusted UCB97.5: $86.4\\%$.
   - Under operational gate rule: $99.9\\%$.

---

"""

# 4. Update Section 5 Table
old_s5_table_marker = "| Scenario & Condition | Cohort $N=60$"
old_s5_end_marker = "> [!NOTE]\n> **Safety Suppression Finding"

new_s5_table = """| Scenario & Condition | Cohort $N=60$ | Cohort $N=180$ | Cohort $N=240$ | Cohort $N=300$ | Cohort $N=360$ | Cohort $N=420$ | Cohort $N=450$ | Cohort $N=468$ | Safety Requirement |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 3: Null Benchmark ($\Delta=0, \Delta D=0$, UCB95)** | $3.2\%$ | $4.6\%$ | $5.0\%$ | $4.8\%$ | $5.9\%$ | $4.8\%$ | $4.3\%$ | $4.7\%$ | Must be $\le 5.0\%$ (controlled) |
| **Scenario 4: Boundary Violation ($\Delta D = +1.40\\text{ pp}$, UCB95)** | $8.0\%$ | $5.8\%$ | $5.9\%$ | $6.2\%$ | $5.1\%$ | $5.1\%$ | $5.1\%$ | $5.6\%$ | Rejects safety $\ge 94\%$ |
| **Scenario 4: Boundary Violation (Adjusted UCB97.5)** | **$4.0\%$** | **$3.6\%$** | **$3.4\%$** | **$3.2\%$** | **$2.8\%$** | **$2.8\%$** | **$2.9\%$** | **$3.1\%$** | **$\ge 96.9\%$ suppressed!** |

"""

# 5. Update Section 6
old_s6_marker = "## 6. Formal Sample Size Decision Recommendation"

new_s6_content = """## 6. Formal Sample Size Decision Recommendation

1. **Option A Retained — Sample Size Conditional on Statistical Alignment:**  
   In accordance with the supervisor's decision, Option A (Confirmatory Cohort Expansion) is selected, but the final sample size is **not yet frozen pending supervisor choice of primary inferential criterion**.
2. **Initial Planning Baseline ($N=180$):**  
   Retained as the initial planning baseline ($30$/group), providing $\ge 85\%$ joint power under Parity Preservation ($91.2\%$).
3. **The Core Statistical Trade-Off for Supervisor Decision:**  
   - **Path 1 (Standard UCB95 Criterion):** Set $N = 360$ ($60$/group). Achieves $99.5\%$ (Parity) and $85.6\%$ (Drift) joint power. Caveat: $UCB_{95\\%}$ non-coverage on the boundary is $5.1\\%$--$8.6\\%$ (undercovered).
   - **Path 2 (Adjusted UCB97.5 Conservative Criterion):** Set $N = 468$ ($78$/group). Achieves $99.9\%$ (Parity) and $86.4\\%$ (Drift) joint power, with verified non-coverage $\le 5.0\\%$ across all DGP stress tests. Fully exhausts the unexposed Irish cohort.
   - **Path 3 (High-Capacity Buffer Target):** Set $N = 450$ ($75$/group). Achieves $90.8\\%$ (UCB95) and $83.5\\%$ (Adj. UCB97.5), preserving $3$ unexposed Irish speakers in reserve.
   - **Path 4 (Operational Gate Preregistration):** Preregister the runtime two-part rule ($\widehat{\\Delta D} \\le 1.40\\text{ pp} \\land UCB_{95\\%} \\le 2.00\\text{ pp}$) as the primary safety gate outcome, achieving $>99\\%$ power at $N = 360$ to $468$.
4. **Preserve Absolute Governance Hold:**  
   Execution flag remains locked: `execution_authorized = false`. No confirmatory data may be materialized, manifested, or evaluated until supervisor preregistration sign-off is completed.
"""

# Replace sections
idx1 = text.find(old_table_1_3_marker)
idx2 = text.find(old_section_2_marker)
assert idx1 != -1 and idx2 != -1
text = text[:idx1] + new_table_1_3 + text[idx2:]

idx3 = text.find("## 3. Comprehensive Sample-Size Exploration Grid")
idx4 = text.find(old_section_4_marker)
assert idx3 != -1 and idx4 != -1
text = text[:idx3] + new_grid_content + text[idx4:]

idx5 = text.find(old_s4_start)
idx6 = text.find(old_section_5_marker)
assert idx5 != -1 and idx6 != -1
text = text[:idx5] + new_s4_content + text[idx6:]

idx7 = text.find(old_s5_table_marker)
idx8 = text.find(old_s5_end_marker)
assert idx7 != -1 and idx8 != -1
text = text[:idx7] + new_s5_table + text[idx8:]

idx9 = text.find(old_s6_marker)
assert idx9 != -1
text = text[:idx9] + new_s6_content

with open(doc_path, "w", encoding="utf-8") as f:
    f.write(text)

print("[OK] stage6m_sample_size_decision.md successfully updated!")
