# Stage 6M Task 6.4 — Monte Carlo Acceptance-Rule Reconciliation Audit

> **DOCUMENT STATUS:** Authoritative Statistical Reconciliation & Acceptance Rule Decision Audit
> **GOVERNANCE STATUS:** DRAFT_HOLD (Cohort 3 Materialization Blocked)
> **EVALUATION BRANCH:** `stage6m-five-stratum-parity` (Starting commit `8c636f9`)
> **FINAL GOVERNANCE VERDICT:** **CONDITIONAL HOLD**

---

## Executive Summary

Task 6.4 resolves the statistical question raised in Task 6.3 regarding the Monte Carlo confidence-bound definition:
1. **Ambiguity Identified (Task A):** A subtle but important divergence exists between the candidate protocol specification text and its historical implementation code:
   - The written protocol specification states that the design must achieve: $\text{LCB}_{95\%} \ge 90.00\%$ ('exact Clopper-Pearson 95% lower confidence bound').
   - The implementation code in `stage6m_v1_5_sample_size_power_sweep.py` evaluated `clopper_pearson_interval(..., alpha=0.05)`, which extracts the lower endpoint of a **two-sided 95% confidence interval** (tail area $\alpha/2 = 0.025$).
2. **Exact Numerical Reproduction (Task B):** Under the primary confirmation ($N_g = 220$, $9,058 / 10,000$ successes):
   - **One-Sided 95% LCB (Tail $\alpha = 0.05$):** **`90.085739%`** ($\ge 90.00\% \implies \mathbf{PASS}$ by $+0.0857$ pp).
   - **Two-Sided 95% CI Lower Endpoint (Tail $\alpha/2 = 0.025$):** **`89.990601%`** ($< 90.00\% \implies \mathbf{MISS}$ by $-0.0094$ pp).
   - At 10,000 trials, the two-sided threshold requires $k \ge 9,059$ successes; the observed count was $k = 9,058$ (**a shortfall of exactly 1 trajectory out of 10,000**).
3. **Governance Recommendation (Task C):**
   - In standard statistical methodology and regulatory validation (FDA, EMA), verifying whether power exceeds a minimum threshold ($H_1: P \ge 0.90$) is universally treated as a **one-sided test at level $\alpha = 0.05$**.
   - Rather than silently reinterpreting the rule to force a PASS, this audit formally documents the ambiguity and presents a principled recommendation for Project-Lead sign-off.
   - Overall governance status remains **`CONDITIONAL HOLD`** pending Project-Lead authorization.
4. **Candidate Positioning Re-Affirmed (Task D):**
   - $N_g = 220$ remains the primary candidate because it preserves a **65-speaker buffer (+21.3%)** under Australian Common Voice 27 capacity.
   - $N_g = 285$ is strictly designated a **supplemental benchmark** (2,500 trials evaluated; consumes 100% of capacity).
   - The original Task 5 95.35% power estimate is formally documented as superseded by the calibrated 90.58% result.

---

## 1. Task A — Candidate Protocol Inspection & Ambiguity Audit

### Protocol Specification Text
In `reports/stage6m/stage6m_v1_5_candidate_five_stratum_protocol_spec.md` (Section 5.2):
> *'To qualify for consideration under Project-Lead Academic Authorization, the candidate design must demonstrate:*
> *$$\widehat{P}_{\text{joint}} \ge 0.90 \quad \text{AND} \quad \text{LCB}_{95\%}(\widehat{P}_{\text{joint}}) \ge 0.90$$*
> *where $\text{LCB}_{95\%}$ is the exact Clopper-Pearson 95% lower confidence bound from at least $S = 10,000$ Monte Carlo trials with $B = 20,000$ bootstrap replicates.'*

### Code Implementation & Historical Precedent
- In `scripts/stage6m_v1_5_sample_size_power_sweep.py` (line 137 and 539):
  ```python
  def clopper_pearson_interval(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
      low = float(sp_stats.beta.ppf(alpha / 2.0, k, n - k + 1))
      high = float(sp_stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
      return low, high
  ```
  The function assigns `lcb, ucb = clopper_pearson_interval(...)` and evaluates `pass_lcb = bool(lcb >= 0.90)`.
- In `tests/research_validity/test_stage6m_sample_size_power_sweep.py` (lines 147–149):
  ```python
  # Exact threshold: k = 9060 out of 10,000 achieves LCB >= 0.90
  l_pass, _ = clopper_pearson_interval(9060, 10000, alpha=0.05)
  assert l_pass >= 0.90
  ```
- In `stage6m_v1_5_candidate_five_stratum_protocol_spec.md` (Section 5.3):
  `Joint Power: 95.35% (95% CI: [94.92%, 95.75%], LCB = 94.92% >= 90.00%)`
  The quoted LCB of $94.92\%$ was verbatim the lower endpoint of the two-sided 95% CI.

**Conclusion:** The text specified a '95% lower confidence bound', but the code and cited tables evaluated the **lower endpoint of a two-sided 95% confidence interval** (which corresponds to a 97.5% one-sided confidence bound).

---

## 2. Task B — Exact Numerical Reproduction ($N_g = 220$)

For $k = 9,058$ successful joint trajectories out of $n = 10,000$ trials:

| Confidence Bound Method | Statistical Formula | Tail Probability ($\alpha$) | Effective One-Sided Confidence | Exact Unrounded Value | Rounded Value | Required Minimum $k$ ($n = 10,000$) | Result vs 90.00% Threshold |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Two-Sided 95% CI Lower Endpoint** | $\operatorname{Beta}(\alpha/2; k, n-k+1)$ | $\alpha/2 = 0.025$ | 97.5% LCB | `0.89990601` | **`89.9906%`** | $k \ge 9059$ ($90.59\%$) | **SHORTFALL (-0.0094 pp; -1 trial)** |
| **One-Sided 95% LCB** | $\operatorname{Beta}(\alpha; k, n-k+1)$ | $\alpha = 0.050$ | 95.0% LCB | `0.90085739` | **`90.0857%`** | $k \ge 9050$ ($90.50\%$) | **PASS (+0.0857 pp; +8 trials)** |

### Mathematical Explanation of the Discrepancy
The numerical difference of **`0.095138 percentage points`** arises strictly from the probability mass in the tail:
$$p_{L,\text{1-sided}} = \operatorname{Beta}(0.050; 9058, 943) = 0.90085739$$
$$p_{L,\text{2-sided}} = \operatorname{Beta}(0.025; 9058, 943) = 0.89990601$$
- Testing whether power exceeds 90% is intrinsically a **one-sided validation hypothesis**: $H_0: P < 0.90$ versus $H_1: P \ge 0.90$.
- When one allocates $2.5\%$ to the lower tail, one is demanding that the true power be above $90.00\%$ with **97.5% confidence**, not 95% confidence.

---

## 3. Task C — Acceptance Decision & Governance Options

As mandated by `/gravitas` reliability principles, we do not arbitrarily choose whichever formula yields a PASS. We submit two clearly defined decision pathways for Project-Lead Academic Authorization:

| Decision Pathway | Statistical Definition | Outcome for $N_g = 220$ | Methodological Justification | Recommended Action |
| :--- | :--- | :---: | :--- | :--- |
| **Option 1 (Recommended): Standard One-Sided 95% LCB** | One-sided 95% Clopper-Pearson LCB (tail $\alpha = 0.05$) | **PASS** ($90.09\% \ge 90.00\%$) | Aligns with standard clinical and regulatory trial practice for demonstrating adequacy against a minimum power threshold; matches literal text of protocol spec. | Formalize protocol wording to explicitly state one-sided $\alpha = 0.05$ Beta bound. |
| **Option 2 (Conservative): Two-Sided Lower Endpoint** | Lower endpoint of two-sided 95% Clopper-Pearson CI (tail $\alpha/2 = 0.025$) | **SHORTFALL** ($89.99\% < 90.00\%$) | Maintains byte-level continuity with the historical Task 5 code implementation. Misses threshold by 1 trial out of 10,000 (0.0094 pp). | Either: (a) Expand primary sample size to $N_g = 225$ (preserves 60 buffer speakers in Australia), or (b) Run 20,000 trials. |

### Authoritative Recommendation
We recommend that the Project Lead adopt **Option 1**, clarifying in the pre-registration specification that the Monte Carlo lower confidence bound is evaluated as an exact one-sided 95% Clopper-Pearson lower bound at significance level $\alpha = 0.05$.

---

## 4. Task D — Sample-Size Positioning Reconciliation

| Evaluation Candidate | Confirmatory Evaluation Speakers | Gate Reserve | Total Unexposed Required | Total CV27 Australian Capacity | Australian Reserve Margin | Confirmed Joint Power | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$N_g = 220$ (PRIMARY)** | **1,100** | **20** | **240** | **305** | **+65 speakers (+21.3%)** | **90.58%** (10,000 trials) | **BUFFERED (Recommended)** |
| **$N_g = 285$ (BENCHMARK)** | 1,425 | 20 | 305 | 305 | 0 speakers (0.0%) | 96.96% (2,500 trials) | EXHAUSTED (Supplemental Benchmark Only) |

### Key Sample-Size Principles
1. **Operational Buffer Over Negligible Differences:** $N_g = 220$ is preferred because it preserves **65 eligible Australian evaluation speakers** to absorb decoding drops, corrupt recordings, or quality exclusions during physical Common Voice 27 curation.
2. **Benchmark Status of $N_g = 285$:** At 2,500 trials, $N_g = 285$ achieves $96.96\%$ power, but it remains a supplemental capacity benchmark rather than a fully confirmed alternative until subjected to full 10,000-trial confirmatory depth.
3. **Superseded Historical Estimates:** The earlier Task 5 joint power estimate of **$95.35\%$** is formally marked as superseded by the calibrated **$90.58\%$** result.
4. **Conditional Power Disclosure:** All reported power figures are conditional development scenario assumptions, not guarantees of physical DSG performance.

---

## 5. Frozen Code Immutability & Multiplicity Invariants

1. **Frozen Production Code Immutability:** `src/dsg_ctta/evaluation/paired_cluster_inference.py` has **0 lines diff** against `origin/main`.
2. **Candidate Inference Engine:** Bounded within `src/dsg_ctta/evaluation/paired_cluster_inference_v15.py`.
3. **Multiplicity Family Architecture:** $M = 8$, $\alpha = 0.05$, $\alpha_{\text{adj}} = 0.00625$, simultaneous percentile = $99.375\%$.
4. **Disparity Decision Rule:** $\text{UCB}_D \le 0.0000$ pp (inclusive).

---

## Final Governance Verdict

```
FINAL VERDICT: CONDITIONAL HOLD
GOVERNANCE STATUS: DRAFT_HOLD PRESERVED
PRIMARY CANDIDATE: N_g = 220 SPEAKERS PER ACCENT (1,100 CONFIRMATORY SPEAKERS)
MONTE CARLO BOUNDS (N_g = 220, 10k TRIALS):
  - One-Sided 95% LCB: 90.0857% (PASSES >= 90.00% by +0.0857 pp)
  - Two-Sided 95% CI Lower Endpoint: 89.9906% (MISSES >= 90.00% by -0.0094 pp; 1 trial)
GOVERNANCE ACTION: Formal Project-Lead Sign-Off on Confidence-Bound Definition Required Prior to Authorization
```
