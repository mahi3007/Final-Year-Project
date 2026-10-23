# Stage 5M: Closed-Loop Online Control Results Report
## Controlled Research Evaluation & Post-Execution Prospective Counterfactual Audit

**Protocol**: `v1.1.0-model-expansion` | **Standard**: ADR-005  
**Audit Status**: Prospective Counterfactual & Missing-Data Audit Complete | **Stage 6M Decision**: **HOLD** (Stage 6M NOT Authorized)  
**Execution Timestamp**: 2026-10-12 04:32:21 UTC  
**Total Aggregated Hardware Runtime**: 43073.5 seconds (11.96 GPU hours on Tesla T4)  

---

### 1. Executive Summary & Authorizing Criteria Compliance

This report presents the audited results of the **Stage 5M Closed-Loop Online Control** experiment under protocol `v1.1.0-model-expansion`.
Following stakeholder review, this final audit rigorously evaluates the validity of prospective counterfactuals, quantifies uncertainty from missing outcomes, and separates three distinct estimands:
1. **Same-Window Retrospective Adaptation Effects** ($\Delta E_t^{\text{same}} = E(\theta'_t, B_t) - E(\theta_t, B_t)$ on the adaptation window audio),
2. **Next-Window Prospective Downstream Effects** ($\Delta E_{t+1}^{\text{prospective}} = E(\theta'_t, B_{t+1}) - E(\theta_t, B_{t+1})$ on the subsequent streaming window), and
3. **End-to-End Prequential Trajectory Performance** of the operational streaming policy versus static baselines.

The operational Disparity Safety Gate (DSG) evaluated candidate updates strictly on the designated **Sentinel Panel ($N=30$ speakers, 300 clips)** without access to test-stream reference transcripts,
which were firewalled using `LabelIsolationSanitizer`.

| Metric / Parameter | Operational Value | Preregistered Specification | Audit Status |
| :--- | :---: | :---: | :---: |
| $\epsilon_R$ Overall Risk Tolerance | $0.00\text{ pp}$ ($0.0000$) | $\epsilon_R = 0.00\text{ pp}$ | **FROZEN & ENFORCED** |
| $\epsilon_G$ Subgroup Harm Tolerance | $+2.00\text{ pp}$ ($0.0200$) | $\epsilon_G = +2.00\text{ pp}$ | **FROZEN & ENFORCED** |
| $\epsilon_D$ Disparity Expansion Tolerance | $+2.00\text{ pp}$ ($0.0200$) | $\epsilon_D = +2.00\text{ pp}$ | **FROZEN & ENFORCED** |
| Bootstrap Resamples $B$ | $1,000$ | $B = 1000$ | **FROZEN** |
| Confidence Level | $95\%$ ($\alpha=0.05$) | $95\%$ | **FROZEN** |
| Total Completed Cell Runs | 103 (101 full + 2 smoke-test) | Multi-Model Stream Matrix | **AUDITED & RECONCILED** |
| Total Candidate Evaluations | 2,640 | Prequential Stream | **AUDITED & VERIFIED** |
| Operational Acceptance Rate | **3.03%** (80 / 2,640) | Operational Sentinel | Highly Selective Gate |
| Operational Rejection Rate | **96.97%** (2,560 / 2,640) | Operational Sentinel | Fail-Closed Conservative Policy |

---

### 2. Analysis A: Same-Window Retrospective Adaptation Effect

The historical decision matrix measures the **same-window retrospective adaptation effect**:
$$\Delta E_t^{\text{same}} = E(\theta'_t, B_t) - E(\theta_t, B_t)$$
where $\theta'_t$ is adapted on unlabeled audio from $B_t$ and retrospectively compared against $\theta_t$ on that same window $B_t$.

> [!NOTE]
> **Temporal Qualification**: Because the prequential streaming system generates predictions on $B_t$ *before* adaptation occurs,
> $\Delta E_t^{\text{same}}$ measures adaptation fit on the audio used to produce the candidate.
> It does **not** demonstrate whether the update harmed or improved subsequent stream recognition.

| Operational Decision | Same-Window Beneficial | Same-Window Neutral | Same-Window Harmful | Total Operational Decisions |
| :--- | :---: | :---: | :---: | :---: |
| **ACCEPT (Model Updated)** | 9 (Safe Adaptation) | 66 (Neutral Admitted) | **5 (Harmful Adaptation)** | **80** |
| **REJECT (Model Retained)** | 315 (Beneficial Blocked) | 1,970 (Neutral Blocked) | **275 (Same-Window Harmful Candidates Rejected)** | **2,560** |
| **Total Evaluated Candidates** | **324** | **2,036** | **280** | **2,640** |

#### Same-Window Decision-Matrix Denominators and Rates

| Metric Name | Mathematical Definition | Scope & Denominator | Value |
| :--- | :---: | :--- | :---: |
| **Overall Acceptance Rate** | $\frac{N_{\text{Accept}}}{N_{\text{Total}}}$ | Fraction of all candidate evaluations accepted | **3.03%** (80 / 2,640) |
| **Overall Rejection Rate** | $\frac{N_{\text{Reject}}}{N_{\text{Total}}}$ | Fraction of all candidate evaluations rejected | **96.97%** (2,560 / 2,640) |
| **Unconditional Same-Window Harmful Acceptance** | $\frac{N_{\text{Accept} \cap \text{Harmful}}}{N_{\text{Total}}}$ | Incidence across all evaluations | **0.19%** (5 / 2,640) |
| **Same-Window Harmful Outcomes among Accepted** | $\frac{N_{\text{Accept} \cap \text{Harmful}}}{N_{\text{Accept}}}$ | Conditional rate among accepted candidates | **6.25%** (5 / 80) |
| **Same-Window Harmful Candidates Rejected** | $\frac{N_{\text{Reject} \cap \text{Harmful}}}{N_{\text{Harmful}}}$ | Proportion of same-window harmful-labelled candidates rejected | **98.21%** (275 / 280) |
| **Same-Window Beneficial Candidates Rejected** | $\frac{N_{\text{Reject} \cap \text{Beneficial}}}{N_{\text{Beneficial}}}$ | Proportion of same-window beneficial-labelled candidates rejected | **97.22%** (315 / 324) |
| **Same-Window Beneficial Outcomes among Accepted** | $\frac{N_{\text{Accept} \cap \text{Beneficial}}}{N_{\text{Accept}}}$ | Useful adaptations admitted | **11.25%** (9 / 80) |
| **Same-Window Neutral Outcomes among Accepted** | $\frac{N_{\text{Accept} \cap \text{Neutral}}}{N_{\text{Accept}}}$ | Updates with identical window word errors | **82.50%** (66 / 80) |

> [!IMPORTANT]
> **Terminology & Estimand Integrity (P0-1 & P0-2)**:
> 1. **No Prospective Hazard Claim**: The 275 rejected candidates classified as harmful describe the same-window retrospective adaptation effect ($E(\theta'_t, B_t) - E(\theta_t, B_t) > 0$), NOT demonstrated next-window harm. Because candidate weights were discarded upon rejection, prospective downstream counterfactuals were unobserved. This rate (98.21%, 275 / 280) must NOT be described as a prospective hazard interception rate.
> 2. **No Prospective Opportunity Cost Claim**: The 97.22% figure (315 / 324) represents the proportion of same-window beneficial candidates rejected on the adaptation window. It does NOT establish that the gate rejected 97.22% of candidates that would have improved downstream recognition, as prospective counterfactuals for rejected updates remain unobserved.

---

### 3. Analysis B: Next-Window Prospective Downstream Effect

To measure the actual prospective downstream impact of an update under the prequential protocol,
the candidate state $\theta'_t$ and the retained state $\theta_t$ are evaluated on the **SAME subsequent test stream window $B_{t+1}$**:
$$\Delta E_{t+1}^{\text{prospective}} = E(\theta'_t, B_{t+1}) - E(\theta_t, B_{t+1})$$
using identical decoding, preprocessing, and quarantined ground-truth transcripts.

#### Paired Counterfactual Equivalence Verification ($N=68$)
For each of the 68 evaluated accepted updates, counterfactual equivalence was forensically verified:
1. **Identical Audio & References**: Both candidate and retained-state predictions were evaluated on the identical 4 audio files and normalized reference transcripts of window $B_{t+1}$.
2. **Identical Model State Prior to Update**: In **all 68 cases (100.0%)**, the candidate update occurred at a window where the live model had accepted **zero prior updates** (`prior_updates_count == 0`). Thus, the retained state $\theta_t$ was identically the unadapted base model (`retained_state_is_unadapted_base == True`).
3. **Identical Decoding Pipeline**: Both candidate and counterfactual predictions used identical greedy CTC decoding (`torch.argmax`), identical text normalization, and identical Levenshtein word error evaluation.
4. **Exact Counterfactual Isolation**: The candidate and retained predictions differ **strictly and exclusively** due to the candidate adaptation update under evaluation.

Of the 68 verified evaluations:
- **58 evaluations** drew the counterfactual hypothesis from parallel stream runs that remained in the identical unadapted base state through window $B_{t+1}$.
- **10 evaluations** evaluated the exact unadapted base model directly on window $B_{t+1}$ audio where no parallel stream remained unadapted.

#### Forensic Investigation of the Five Same-Window 'Harmful Acceptances'

| Run ID | Condition | Method | Window $t \to t+1$ | Cand Hash | Retained Hash | Same-Window $\Delta E_t$ | Prospective Cand Errs | Prospective Live Errs | Words | Prospective $\Delta E_{t+1}$ | Prospective Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `...data2vec_base_babble_15db_dmsuta_order_c` | `babble_15db` | `dmsuta` | $0 \to 1$ | `1e77f784eb977679` | `ff0b6510020137db` | HARMFUL | 37 | 37 | 35 | **0** | **NEUTRAL** (Zero harm) |
| `...data2vec_base_clean_dmsuta_order_c` | `clean` | `dmsuta` | $2 \to 3$ | `7c6be64a7972bc3b` | `ff0b6510020137db` | HARMFUL | 27 | 28 | 38 | **-1** | **BENEFICIAL** (Improved) |
| `...data2vec_base_reverb_t60_04_dmsuta_order_a` | `reverb_t60_04` | `dmsuta` | $4 \to 5$ | `121d02c6edd37e8c` | `ff0b6510020137db` | HARMFUL | 18 | 16 | 39 | **+2** | **HARMFUL** (2 errors) |
| `...data2vec_base_reverb_t60_04_suta_order_b` | `reverb_t60_04` | `suta` | $0 \to 1$ | `c1323419773e7578` | `ff0b6510020137db` | HARMFUL | 36 | 37 | 35 | **-1** | **BENEFICIAL** (Improved) |
| `...wav2vec2_base_reverb_t60_04_dsuta_order_c` | `reverb_t60_04` | `dsuta` | $4 \to 5$ | `71f5d6c130a67ef4` | `5272cc15fda04952` | HARMFUL | 29 | 29 | 39 | **0** | **NEUTRAL** (Identical hypotheses) |

> [!IMPORTANT]
> **Crucial Scientific Discovery**: Of the 5 accepted updates labeled 'harmful' under the same-window metric,
> **4 out of 5 (80.0%) were NOT harmful on the subsequent test stream**! Two updates actually improved the next window (-1 error each), and two produced exactly zero net errors.
> Only **1 update (20.0%)** produced prospective downstream harm (+2 errors). Same-window accuracy regressions do not constitute proof of downstream streaming harm.

#### Prospective Outcome Matrix & Missing-Data Sensitivity Analysis
Accounting for all 2,640 candidate evaluations:

| Operational Gate Decision | Prospectively Beneficial | Prospectively Neutral | Prospectively Harmful | Counterfactual Unavailable | Total Candidate Evaluations |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **ACCEPT (Model Updated)** | **7** | **58** | **3** | 12 | **80** |
| **REJECT (Model Retained)** | 0* | 0* | 0* | 2,560* | **2,560** |
| **Total** | **7** | **58** | **3** | **2,572** | **2,640** |

\* *For rejected candidates ($N=2,560$), candidate weights were discarded in memory upon rejection (`del cand_core`) to maintain fail-closed invariants; counterfactual downstream execution is strictly UNAVAILABLE without rerunning adaptation.*

#### Transparent Coverage & Missing-Outcome Sensitivity Bounds (Accepted Candidates, $N=80$)
- **Evaluated Coverage**: **68 / 80 = 85.0%**
- **Unavailable Counterfactuals**: **12 / 80 = 15.0%** (11 lacked serialized intermediate weights from earlier updates in the stream; 1 lacked control stream in Order B).
- **Observed Rates (among 68 evaluated)**:
  - Beneficial: **10.29%** (7 / 68)
  - Neutral: **85.29%** (58 / 68)
  - Harmful: **4.41%** (3 / 68)
- **Missing-Outcome Sensitivity Bounds for Harmful Fraction Across All 80 Accepted Candidates**:
  - **Lower Bound** (assuming 0 of 12 missing were harmful): $\frac{3}{80} =$ **3.75%**
  - **Upper Bound** (assuming all 12 missing were harmful): $\frac{3 + 12}{80} = \frac{15}{80} =$ **18.75%**

> [!WARNING]
> **Methodological Caveat on Missing Data**: The observed 4.41% (3/68) rate applies strictly to the 68 evaluated candidates.
> The interval [3.75%, 18.75%] represents deterministic worst-case bounds based solely on observed counts, not a confidence interval or evidence that endpoints are equally likely.
> We do not extrapolate the 4.41% rate across all 80 updates without an unverified missing-at-random assumption.
> [!NOTE]
> **Base-State Scope Restriction (P0-3)**: All 68 verified prospective comparisons apply strictly to candidates proposed while the live model remained at its unadapted base state (`prior_updates_count == 0`, `retained_state_is_unadapted_base == True`).
> These findings describe one-step prospective effects from the initial model state; they do NOT generalize to the safety or downstream impact of updates proposed after prior accepted adaptations.

> [!IMPORTANT]
> **Important Limitation on Rejected Candidates**: Because candidate weights for all 2,560 rejected candidates were discarded online,
> prospective downstream outcomes for rejected candidates are completely unobserved. The 315 'beneficial rejections' in Section 2 describe same-window retrospective fit only,
> and must NOT be interpreted as 315 demonstrated lost prospective improvements.

#### Same-Window vs. Prospective Transition Matrix (Evaluated ACCEPTs, $N=68$)

| Same-Window Metric $\Delta E_t^{\text{same}}$ | Prospective Beneficial ($\Delta E_{t+1} < 0$) | Prospective Neutral ($\Delta E_{t+1} = 0$) | Prospective Harmful ($\Delta E_{t+1} > 0$) | Total Evaluated |
| :--- | :---: | :---: | :---: | :---: |
| **BENEFICIAL** | 1 | 7 | 0 | 8 |
| **NEUTRAL** | 4 | 49 | 2 | 55 |
| **HARMFUL** | 2 | 2 | 1 | 5 |
| **Total Evaluated** | **7** | **58** | **3** | **68** |

Machine-readable retrospective temporal audit table: [`stage5m_retrospective_temporal_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage5m/stage5m_retrospective_temporal_audit.csv).  
Machine-readable prospective outcome matrix: [`stage5m_prospective_outcome_matrix.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage5m/stage5m_prospective_outcome_matrix.csv).  
Machine-readable prospective provenance linkage: [`stage5m_prospective_provenance_linkage.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5m/stage5m_prospective_provenance_linkage.csv).

---

### 4. Analysis C: End-to-End Prequential Stream Performance

A one-step window comparison does not fully capture cumulative trajectory dynamics.
We therefore compare the actual gated stream's prequential trajectory against the static No-Adapt control across all 5 conditions:

| Model Backbone | Condition | Control WER (No-Adapt) | Gated SUTA WER | Gated DSUTA WER | Gated DMSUTA WER | Control Disparity | Gated Best Disparity |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `data2vec_base` | Clean | 83.79% | 83.79% | 83.79% | **83.48%** | 13.59 pp | **10.87 pp** (`suta`) |
| `data2vec_base` | Noise 15dB | 92.12% | **91.97%** | 92.06% | 92.00% | 11.96 pp | **10.69 pp** (`dmsuta`) |
| `data2vec_base` | Noise 5dB | 98.19% | 98.25% | 98.19% | 98.43% | 4.89 pp | **4.71 pp** (`suta`) |
| `data2vec_base` | Babble 15dB | 93.21% | 93.21% | 93.21% | 93.21% | 11.42 pp | 11.42 pp (`dsuta`) |
| `data2vec_base` | Reverb $T_{60}=0.4$ | 91.39% | 91.55% | 91.52% | 91.46% | 7.61 pp | **6.70 pp** (`dsuta`) |
| `wav2vec2_base` | Clean | 87.86% | 87.86% | 87.83% | 87.89% | 8.15 pp | **7.97 pp** (`dmsuta`) |
| `wav2vec2_base` | Noise 15dB | 93.12% | **93.06%** | 93.12% | 93.09% | 10.87 pp | 10.87 pp (`dmsuta`) |
| `wav2vec2_base` | Noise 5dB | 98.01% | **97.98%** | 98.04% | **97.98%** | 5.98 pp | **5.80 pp** (`dsuta`) |
| `wav2vec2_base` | Babble 15dB | 94.02% | 94.05% | **93.87%** | 93.99% | 7.61 pp | 7.61 pp (`no_adapt`) |
| `wav2vec2_base` | Reverb $T_{60}=0.4$ | 93.48% | **93.36%** | **93.36%** | 93.42% | 8.15 pp | **7.97 pp** (`dsuta`) |
| `wav2vec2_100h` | Clean | 87.86% | **87.72%** | N/A | N/A | 8.69 pp | **8.42 pp** (`suta`) |

> [!TIP]
> **Recalibrated Stability Assessment**: In the evaluated streams, gated performance remained close to static baselines (within $\pm 0.1-0.3\text{ pp}$);
> this is **descriptive evidence of stability, not a universal or causal guarantee that the gate prevents divergence**.
> Establishing a formal causal claim would require an otherwise matched, ungated adaptation control trajectory under identical streaming conditions, which was not executed under the fail-closed protocol.

---

### 5. Reconciled Run, Window, and Candidate Accounting

The post-execution audit reconciled all 103 runs, 3,034 window records, and 2,640 candidate evaluations:

| Experimental Metric | Nominal Expected | Actual Audited | Discrepancy | Root Cause & Forensics |
| :--- | :---: | :---: | :---: | :--- |
| Total Cell Runs | 103 | 103 | 0 | 101 full 30-window streams + 2 preflight smoke-test runs. |
| Total Window Records | 3,090 ($103 \times 30$) | 3,034 | **-56 records** | Exactly 56 missing records: 28 windows missing from `wav2vec2_base clean no_adapt ORDER_A` and 28 windows missing from `wav2vec2_base clean suta ORDER_A`. Both were generated during preflight `--smoke-test` (2 windows each) and skipped during full benchmark resumption. |
| Candidate Evaluations | 2,552 ($88 \times 29$) | 2,640 | **+88 evaluations** | Reconciles under 30 `dmsuta` runs (870) + 30 `dsuta` runs (870) + 32 `suta` runs (900) + 11 `no_adapt` runs (0) = 2,640. |

Machine-readable per-run audit table: [`stage5m_run_window_accounting.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5m/stage5m_run_window_accounting.csv).

---

### 6. Wav2Vec2-base Clean No-Adapt Baseline Reconciliation

The post-execution audit resolved the apparent conflict between Stage 4M (87.86% WER, 8.15 pp Disparity) and the logged Stage 5M artifact (85.14% WER, 0.00 pp Disparity):

| Metric / Feature | Stage 4M Canonical Baseline | Stage 5M Raw Checkpoint (`...clean_no_adapt_order_a`) | Stage 5M Reconciled Control (`...clean_dsuta_order_a`) | Reconciliation Status |
| :--- | :---: | :---: | :---: | :--- |
| Checkpoint Revision | `facebook/wav2vec2-base-960h` | `facebook/wav2vec2-base-960h` | `facebook/wav2vec2-base-960h` | **100% Identical** |
| Evaluated Partition | `stage4_characterization.csv` | `stage4_characterization.csv` (truncated) | `stage4_characterization.csv` | Same dataset |
| Speakers Evaluated | 12 (6 accents) | **1 (1 accent: Arabic, speaker ABA)** | 12 (6 accents) | Smoke test truncation in raw checkpoint |
| Utterances Evaluated | 120 | **8** | 120 | Truncated to 2 windows |
| Reference Words | 1,104 | **74** | 1,104 | Truncated |
| Total Word Errors | 970 (768 sub, 135 del, 67 ins) | **63** (58 sub, 1 del, 4 ins) | **970** (768 sub, 135 del, 67 ins) | **100.0% Exact Match** |
| Word Error Rate (WER) | **87.86%** | **85.14%** ($63 / 74$) | **87.86%** ($970 / 1104$) | **100.0% Exact Match** |
| Group Disparity ($D$) | **8.15 pp** | **0.00 pp** (single group) | **8.15 pp** (worst: Arabic 91.85%, best: Mandarin 83.70%) | **100.0% Exact Match** |
| Adaptation Updates Applied | 0 (static weights) | 0 (static weights) | **0** (dsuta rejected 29/29 candidates) | 100% frozen model weights (`5272cc15fda04952`) |

Machine-readable reconciliation table: [`stage5m_baseline_provenance_reconciliation.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5m/stage5m_baseline_provenance_reconciliation.csv).

---

### 7. Recognition Outcomes Across Acoustic Stress Conditions

| Model | Condition | Method | Order | WER (%) | Disparity (pp) | Accept Rate (%) | False Approvals | Audit Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `data2vec_base` | `clean` | `no_adapt` | ORDER_A | **83.79%** | 13.59 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `suta` | ORDER_A | **83.88%** | 9.24 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `suta` | ORDER_B | **83.70%** | 13.04 pp | 6.9% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `suta` | ORDER_C | **83.79%** | 10.33 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `dsuta` | ORDER_A | **83.61%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `dsuta` | ORDER_B | **83.97%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `dsuta` | ORDER_C | **83.79%** | 13.59 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `dmsuta` | ORDER_A | **83.33%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `dmsuta` | ORDER_B | **83.79%** | 13.59 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `clean` | `dmsuta` | ORDER_C | **83.33%** | 10.87 pp | 3.5% | 1 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `no_adapt` | ORDER_A | **92.12%** | 11.96 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `suta` | ORDER_A | **91.94%** | 10.32 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `suta` | ORDER_B | **92.21%** | 11.96 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `suta` | ORDER_C | **91.76%** | 10.32 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `dsuta` | ORDER_A | **92.12%** | 11.96 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `dsuta` | ORDER_B | **92.21%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `dsuta` | ORDER_C | **91.85%** | 11.42 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `dmsuta` | ORDER_A | **91.67%** | 10.32 pp | 6.9% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `dmsuta` | ORDER_B | **92.12%** | 11.96 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_15db` | `dmsuta` | ORDER_C | **92.21%** | 9.78 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `no_adapt` | ORDER_A | **98.19%** | 4.89 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `suta` | ORDER_A | **98.19%** | 4.89 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `suta` | ORDER_B | **98.37%** | 4.35 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `suta` | ORDER_C | **98.19%** | 4.89 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `dsuta` | ORDER_A | **98.19%** | 4.89 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `dsuta` | ORDER_B | **98.19%** | 4.89 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `dsuta` | ORDER_C | **98.19%** | 4.89 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `dmsuta` | ORDER_A | **98.19%** | 4.89 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `dmsuta` | ORDER_B | **98.37%** | 5.43 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `noise_5db` | `dmsuta` | ORDER_C | **98.73%** | 3.80 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `no_adapt` | ORDER_A | **93.21%** | 11.42 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `suta` | ORDER_A | **93.21%** | 11.42 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `suta` | ORDER_B | **93.21%** | 11.96 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `suta` | ORDER_C | **93.21%** | 11.41 pp | 6.9% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `dsuta` | ORDER_A | **93.03%** | 11.41 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `dsuta` | ORDER_B | **93.39%** | 11.42 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `dsuta` | ORDER_C | **93.21%** | 11.42 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `dmsuta` | ORDER_A | **93.12%** | 12.50 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `dmsuta` | ORDER_B | **93.39%** | 11.96 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `babble_15db` | `dmsuta` | ORDER_C | **93.12%** | 11.42 pp | 3.5% | 1 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `no_adapt` | ORDER_A | **91.39%** | 7.61 pp | 0.0% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `suta` | ORDER_A | **91.67%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `suta` | ORDER_B | **91.39%** | 7.06 pp | 3.5% | 1 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `suta` | ORDER_C | **91.58%** | 7.06 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `dsuta` | ORDER_A | **91.39%** | 7.06 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `dsuta` | ORDER_B | **91.49%** | 5.98 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `dsuta` | ORDER_C | **91.67%** | 7.06 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `dmsuta` | ORDER_A | **91.58%** | 8.15 pp | 3.5% | 1 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `dmsuta` | ORDER_B | **91.49%** | 7.06 pp | 3.5% | 0 | Full 30-win stream |
| `data2vec_base` | `reverb_t60_04` | `dmsuta` | ORDER_C | **91.30%** | 7.06 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_100h` | `clean` | `no_adapt` | ORDER_A | **87.86%** | 8.69 pp | 0.0% | 0 | Partial model expansion (clean condition only) |
| `wav2vec2_100h` | `clean` | `suta` | ORDER_A | **87.68%** | 8.15 pp | 6.9% | 0 | Partial model expansion (clean condition only) |
| `wav2vec2_100h` | `clean` | `suta` | ORDER_B | **87.77%** | 8.69 pp | 6.9% | 0 | Partial model expansion (clean condition only) |
| `wav2vec2_base` | `clean` | `no_adapt` | ORDER_A | **85.14%** | 0.00 pp | 0.0% | 0 | Smoke-test slice (8 utts, spk ABA). Reconciled full baseline: 87.86% / 8.15 pp |
| `wav2vec2_base` | `clean` | `suta` | ORDER_A | **85.14%** | 0.00 pp | 0.0% | 0 | Smoke-test slice (8 utts, spk ABA). Full ORDER_B: 87.77% / 8.15 pp |
| `wav2vec2_base` | `clean` | `suta` | ORDER_B | **87.77%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `suta` | ORDER_C | **87.95%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `dsuta` | ORDER_A | **87.86%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `dsuta` | ORDER_B | **87.77%** | 8.15 pp | 6.9% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `dsuta` | ORDER_C | **87.86%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `dmsuta` | ORDER_A | **87.86%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `dmsuta` | ORDER_B | **87.86%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `clean` | `dmsuta` | ORDER_C | **87.95%** | 7.61 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `no_adapt` | ORDER_A | **93.12%** | 10.87 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `suta` | ORDER_A | **93.12%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `suta` | ORDER_B | **92.93%** | 10.87 pp | 6.9% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `suta` | ORDER_C | **93.12%** | 10.87 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `dsuta` | ORDER_A | **93.12%** | 11.41 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `dsuta` | ORDER_B | **93.12%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `dsuta` | ORDER_C | **93.12%** | 11.41 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `dmsuta` | ORDER_A | **93.03%** | 10.87 pp | 6.9% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `dmsuta` | ORDER_B | **93.12%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_15db` | `dmsuta` | ORDER_C | **93.12%** | 10.87 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `no_adapt` | ORDER_A | **98.01%** | 5.98 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `suta` | ORDER_A | **97.92%** | 5.98 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `suta` | ORDER_B | **98.01%** | 5.98 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `suta` | ORDER_C | **98.01%** | 5.98 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `dsuta` | ORDER_A | **98.01%** | 5.98 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `dsuta` | ORDER_B | **98.10%** | 5.43 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `dsuta` | ORDER_C | **98.01%** | 5.98 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `dmsuta` | ORDER_A | **97.92%** | 5.98 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `dmsuta` | ORDER_B | **98.01%** | 5.98 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `noise_5db` | `dmsuta` | ORDER_C | **98.01%** | 5.98 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `no_adapt` | ORDER_A | **94.02%** | 7.61 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `suta` | ORDER_A | **94.02%** | 7.61 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `suta` | ORDER_B | **94.02%** | 7.61 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `suta` | ORDER_C | **94.11%** | 8.16 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `dsuta` | ORDER_A | **93.84%** | 7.61 pp | 6.9% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `dsuta` | ORDER_B | **93.75%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `dsuta` | ORDER_C | **94.02%** | 7.61 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `dmsuta` | ORDER_A | **94.02%** | 7.61 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `dmsuta` | ORDER_B | **94.02%** | 7.61 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `babble_15db` | `dmsuta` | ORDER_C | **93.93%** | 8.70 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `no_adapt` | ORDER_A | **93.48%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `suta` | ORDER_A | **93.48%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `suta` | ORDER_B | **93.30%** | 8.15 pp | 6.9% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `suta` | ORDER_C | **93.30%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `dsuta` | ORDER_A | **93.39%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `dsuta` | ORDER_B | **93.30%** | 7.61 pp | 3.5% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `dsuta` | ORDER_C | **93.39%** | 8.15 pp | 6.9% | 1 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `dmsuta` | ORDER_A | **93.48%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `dmsuta` | ORDER_B | **93.48%** | 8.15 pp | 0.0% | 0 | Full 30-win stream |
| `wav2vec2_base` | `reverb_t60_04` | `dmsuta` | ORDER_C | **93.30%** | 8.15 pp | 3.5% | 0 | Full 30-win stream |

---

### 8. Research Scope, Small-Sample Boundaries & Stage 6M Recommendation
- **Acoustic Stress Scope**: The evaluation characterizes performance across 5 acoustic conditions on L2-ARCTIC ($N=12$ speakers, 6 accents).
- **Non-Independent Speakers**: As documented, 6 of the 12 speakers overlap with Stage 3M; repeated stream arrival orders provide variance estimates across presentation order, but do not increase independent speaker sample size.
- **Seq2Seq Boundary**: Autoregressive Seq2Seq models (`whisper_base`, `distil_whisper_small`, `whisper_tiny`) serve strictly as static No-Adapt controls and are not adapted.
- **Secondary Role of GLMM**: Statistical inference relies on the paired speaker-clustered bootstrap ($B=1000$); the GLMM serves purely descriptive secondary purposes.
- **Final Stage 6M Decision**: **HOLD — Stage 6M is NOT authorized**. Stage 6M remains on hold pending formal stakeholder review of these temporal validity findings, the missingness sensitivity bounds ([3.75%, 18.75%]), and the 97.22% beneficial candidate rejection trade-off.