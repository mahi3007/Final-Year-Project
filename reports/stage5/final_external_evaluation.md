# Stage 5D/5E: Final External Evaluation & DSG Empirical Safety Report

**Document Identifier:** `reports/stage5/final_external_evaluation.md`  
**Execution Timestamp:** 2026-10-04T03:30:00Z  
**Governing Standard:** Pre-registered Protocol ADR-005, Stage 5 Amendment (`v1.0-cv27-amended`)  
**Evaluation Set:** Mozilla Common Voice 27.0 English holdout (`cv-corpus-27.0-2026-09-11`, MDC ID: `cmu5jplf300nwmh07iqvk9leo`)  
**Scale:** Exactly 900 clips | 60 speakers | 6 pre-specified accent strata (10 speakers/stratum, 15 clips/speaker)  
**Primary ASR Model:** `facebook/wav2vec2-base-960h`  
**Stream Protocol:** Prequential online streaming ($K=4$, 225 sequential streaming windows)  
**Software Verification Gate:** 90/90 tests passed (`pytest tests/ -v`, 0 failures)  

---

## 1. Executive Summary & Core Scientific Scope

This report presents the definitive evaluation of continual test-time adaptation (CTTA) across five comparative methods (`No-Adapt`, `SUTA`, `DSUTA`, `DMSUTA`, `DSG`) on the Mozilla Common Voice 27.0 external benchmark, incorporating the Stage 5D Evaluator Integrity Repair and Stage 5E Diagnostic Closure Pass.

### 1.1 Resolution of Stage 5B/5C Evaluator Artifact
In Stage 5B/5C, an audit revealed that all 225 DSG rejections were fail-closed caused by an unmaterialized audio artifact on disk (`FileNotFoundError`). In Stage 5D:
1. All 300 physical sentinel audio clips were materialized and cryptographically verified on disk against SHA-256 manifests.
2. Canonical path resolution was implemented in `SentinelAudioResolver` (`src/dsg_ctta/controller/resolver.py`).
3. The tripartite statistical gate ($\epsilon_R=0.0000, \epsilon_G=0.0200, \epsilon_D=0.0200$, $B=1000$ paired cluster bootstrap) was executed end-to-end on **physical acoustic data with 0 fail-closed evaluator errors**.

### 1.2 Scope of Empirical Findings
On the evaluated Common Voice 27.0 streaming benchmark:
- **Controlled Partial Adaptation:** The Disparity Safety Gate (DSG) accepted **9 out of 225 candidate updates (4.0%)** and statistically rejected **216 out of 225 candidate updates (96.0%)**.
- **Mitigating Adaptation Divergence:** Unconstrained test-time adaptation (`SUTA`) suffered substantial empirical regression, degrading corpus WER from **22.45% to 23.55%** ($+1.10$ percentage points, $+95$ net word errors) with localized degradation on Irish English ($+2.39$ percentage points).
- **Descriptive Error Reduction:** DSG reduced the net word-error increase observed under SUTA by **93.7%** (95 additional errors under SUTA versus 6 under DSG relative to No-Adapt), maintaining corpus WER at **22.52%** ($+0.07$ pp vs No-Adapt).
- **Disparity Reduction:** DSG reduced cross-accent performance disparity from **30.25% to 29.50%** ($\Delta_D = -0.75$ pp) and Character Error Rate (CER) from **10.22% to 9.55%**.
- **Risk Screening, Not Perfect Oracle:** One candidate update that satisfied all sentinel gate constraints produced a minor local increase in errors ($+1$ word) on its immediate external batch, demonstrating that the controller provides conservative risk screening under distribution shift rather than an infallible guarantee of external harm elimination.

---

## 2. Primary Method Comparison (Corpus-Level)

All metrics computed across exactly 8,667 reference words under strictly prequential evaluation ($K=4$, 225 sequential streaming windows):

| Adaptation Method | Corpus WER | Speaker-Macro WER | Corpus CER | Total Word Errors | Disparity $D$ | $\Delta_R$ (vs No-Adapt) | $\Delta_D$ | $\max_g \Delta_g$ | DSG Updates (Acc / Rej) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`No-Adapt`** | **22.45%** | **22.39%** | 10.22% | 1,946 | 30.25% | $+0.00\%$ | $+0.00\%$ | $+0.00\%$ | — |
| **`SUTA`** | 23.55% | 23.44% | 10.49% | 2,041 | 28.92% | $+1.10\%$ | $-1.32\%$ | **$+2.39\%$** | — |
| **`DSUTA`** | 22.55% | 22.44% | 10.16% | 1,954 | 28.76% | $+0.09\%$ | $-1.49\%$ | $+1.00\%$ | — |
| **`DMSUTA`** | 22.56% | 22.50% | 10.14% | 1,955 | 29.44% | $+0.10\%$ | $-0.81\%$ | $+0.67\%$ | — |
| **`DSG` (Ours)** | **22.52%** | **22.43%** | **9.55%** | **1,952** | **29.50%** | **$+0.07\%$** | **$-0.75\%$** | **$+0.47\%$** | **9 / 216 (96.0% Rej)** |

*Definitions: Disparity $D = \max_{g \in \mathcal{G}} \text{WER}_g - \min_{g \in \mathcal{G}} \text{WER}_g$. $\Delta_R = \text{WER}_{\text{method}} - \text{WER}_{\text{No-Adapt}}$.*

---

## 3. Stratum-Level Word Error Rates ($\text{WER}_g$)

Breakdown across the 6 pre-specified accent strata derived from Common Voice 27.0 metadata (150 clips, 10 speakers per stratum):

| Pre-Specified Stratum | Ref Words | `No-Adapt` | `SUTA` | `DSUTA` | `DMSUTA` | `DSG` (Ours) | DSG Delta ($\Delta_g$) | SUTA Delta ($\Delta_g$) | Net Error Shielding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 1,493 | 22.91% | 24.05% | 22.97% | 22.44% | 23.17% | $+0.27\%$ | $+1.14\%$ | $+13$ words saved |
| **Canadian English** | 1,500 | 12.20% | 13.73% | 13.20% | 12.87% | 12.67% | $+0.47\%$ | $+1.53\%$ | $+16$ words saved |
| **England English** | 1,393 | 20.32% | 21.82% | 20.17% | 20.60% | 20.46% | $+0.14\%$ | $+1.51\%$ | $+19$ words saved |
| **Irish English** | 1,383 | 15.62% | 18.00% | 15.55% | 15.69% | **15.33%** | **$-0.29\%$** | **$+2.39\%$** | **$+37$ words saved** |
| **South Asian English** | 1,430 | 42.45% | 42.66% | 41.96% | 42.31% | **42.17%** | **$-0.28\%$** | $+0.21\%$ | $+7$ words saved |
| **US English** | 1,468 | 21.46% | 21.32% | 21.59% | 21.66% | 21.53% | $+0.07\%$ | $-0.14\%$ | $-3$ words |

### Key Stratum Findings:
1. **Reduction of Largest Observed Subgroup Regression:** Under unconstrained SUTA, Irish English suffered substantial degradation ($15.62\% \rightarrow 18.00\%$, $+33$ errors). DSG prevented this localized regression and achieved **15.33%** ($-4$ errors vs No-Adapt, saving 37 words relative to SUTA).
2. **South Asian English Accuracy:** South Asian English improved from $42.45\%$ to **42.17%** under DSG, outperforming both No-Adapt and SUTA.
3. **Subgroup Practical Tolerance Comparison:** SUTA's worst-case subgroup regression was $+2.39$ pp. The observed external maximum subgroup regression under DSG was **$+0.47$ pp**, which is numerically below the pre-registered 2 pp practical tolerance ($\epsilon_G = 0.0200$, applied internally to the sentinel UCB).

---

## 4. Disparity Safety Gate Decision Audit

### 4.1 Decision Breakdown (N=225 Windows)
- **Total Candidate Updates Evaluated:** 225
- **Accepted Updates ($\theta_{t+1} \leftarrow \theta_{\text{cand}}$):** **9 (4.0%)** (Windows 0, 2, 7, 8, 24, 27, 57, 81, and 83)
- **Statistical Gate Rejections ($\text{UCB} > \epsilon$):** **216 (96.0%)**
- **Fail-Closed Evaluator Errors:** **0 (0.0%)**
- **Live Model Parameter Hash Transitions:** Live model mutated exactly 9 times on accepted windows, remaining strictly frozen bit-for-bit on all 216 rejected windows.

```
225 Candidate Updates
      │
      ├── 9 ACCEPTED (4.0%)  [Acoustic sentinel criteria satisfied]
      │
      └── 216 REJECTED (96.0%) [Statistical constraint violation]
                │
                ├── 0 Fail-closed evaluator errors
                ├── 0 Silent promotions
                └── 0 Live-model mutations on rejection
```

### 4.2 Retrospective External Outcome Diagnostic Classification
Post-hoc diagnostic comparison between gate decisions and external window error deltas:

| Audit Classification | Windows | Percentage | Research Interpretation |
| :--- | :---: | :---: | :--- |
| `STATISTICALLY_REJECTED_AND_EXTERNALLY_NEUTRAL` | 199 | 88.4% | Candidate had identical external error count; gate rejected based on conservative sentinel bound. |
| `STATISTICALLY_REJECTED_AND_EXTERNALLY_HARMFUL` | 9 | 4.0% | Candidate added word errors on external stream; **gate successfully caught and rejected update**. |
| `ACCEPTED_AND_EXTERNALLY_NEUTRAL` | 8 | 3.6% | Candidate satisfied all bounds and had neutral immediate external impact. |
| `STATISTICALLY_REJECTED_AND_EXTERNALLY_BENEFICIAL` | 8 | 3.6% | Conservative sentinel UCB rejected update that had transient local gain on external batch. |
| `ACCEPTED_AND_EXTERNALLY_HARMFUL` | 1 | 0.4% | Candidate satisfied bounds on sentinel panel but had minor local error (+1 word) on external batch. |

---

## 5. Diagnostic Trace: Mechanism of Subgroup Improvements

A key diagnostic question arises from Section 4.2:
> *If zero accepted updates were retrospectively classified as `ACCEPTED_AND_EXTERNALLY_BENEFICIAL` at the immediate window level, how did DSG produce final subgroup improvements on Irish English ($-0.29$ pp) and South Asian English ($-0.28$ pp)?*

A forensic downstream audit ([`reports/stage5/stage5e_accepted_updates_trace.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5e_accepted_updates_trace.md)) explains this mechanism:

1. **Immediate Window vs. Cumulative Stream Estimands:**
   - The immediate window audit evaluated each candidate **only on its own 4 adaptation utterances ($B_t$)** against the live model $\theta_t$. This captures local batch memorization.
   - However, in prequential streaming, an accepted update mutates the live model parameters $\theta_{t+1}$, which **persist down the stream and transcribe all subsequent utterances**.
2. **Propagation Across Live Model State Intervals:**
   - The final accepted update occurred at Window 83 (Clip 335).
   - The resulting model state $\theta_{84}$ was frozen for the remainder of the deployment, transcribing **Windows 84 through 224 (564 clips, 62.7% of the entire stream)**.
3. **Downstream Utterance Gains:**
   - **Irish English (Windows 200–224):** Transcribed entirely by $\theta_{84}$. The adapted weights achieved fewer word errors than No-Adapt on 5 separate utterances (e.g. `stage5ext_00805`, `00810`, `00828`, `00834`, `00844`) while being worse on only 1 utterance, yielding a net reduction of 4 word errors ($15.62\% \rightarrow 15.33\%$).
   - **South Asian English (Windows 75–112):** Transcribed by $\theta_{58}$ and $\theta_{84}$. The adapted states made fewer errors than No-Adapt on 9 separate utterances while being worse on 5, yielding a net reduction of 4 word errors ($42.45\% \rightarrow 42.17\%$).
4. **The Window 81 Adverse Update:**
   - Window 81 satisfied all sentinel constraints ($\Delta_R = -0.000342$, $\text{UCB}_R = 0.0000$) but produced 31 errors vs 30 on batch $B_{81}$ (+1 word).
   - This empirically confirms that sentinel risk screening is a conservative statistical filter, not a guarantee against all transient local errors under acoustic distribution shift.

---

## 6. Statistical Rigor & Estimand Reconciliation

### 6.1 Sample Size Clarification: Two Distinct Populations
- **External Evaluation Sample:** $N = 60$ speakers (10 speakers/group $\times$ 6 strata, 15 clips/speaker, 900 clips total).
- **DSG Sentinel Panel Sample:** $N = 30$ speakers (5 speakers/group $\times$ 6 strata, 10 clips/speaker, 300 clips total).
- **Independence:** The 30 sentinel speakers and 60 external evaluation speakers are strictly disjoint ($S_{\text{sentinel}} \cap S_{\text{external}} = \emptyset$).

### 6.2 Explicit Confidence Interval and Upper Confidence Bound Constructions
- **Two-Sided 95% Confidence Interval:** Central percentile bootstrap interval at quantiles $\alpha/2 = 0.025$ and $1 - \alpha/2 = 0.975$ of the $B=1,000$ replicate distribution $\{M^{(b)}\}_{b=1}^B$:
  $$\text{CI}_{95\%} = \left[ q_{0.025}\left(\{M^{(b)}\}\right), \; q_{0.975}\left(\{M^{(b)}\}\right) \right]$$
- **One-Sided 95% Upper Confidence Bound ($\text{UCB}_{95}$):** Pre-registered conservative criterion defined as the $(1 - \alpha) = 0.950$ empirical percentile:
  $$\text{UCB}_{95}(M) = q_{0.950}\left(\{M^{(b)}\}\right)$$
- **Nonlinear Maximum and Jensen's Inequality:** In the paired cluster bootstrap, resamples can cause different groups to achieve the maximum replicate regression. While Jensen's inequality establishes that $\mathbb{E}[\max_g X_g] \ge \max_g \mathbb{E}[X_g]$ for random vectors under the resampling distribution, the divergence between the bootstrap mean and the observed pooled maximum reflects cluster-level variance across strata rather than sample bias.

---

## 7. Thesis Contributions & Scientific Conclusions

This research delivers three distinct scientific contributions to continual test-time adaptation for speech recognition:

### Contribution 1: Characterization of CTTA Vulnerability (Phenomenon)
We empirically demonstrate that unconstrained test-time adaptation algorithms (such as SUTA) are vulnerable to severe performance degradation under realistic acoustic drift. On the Common Voice 27.0 external stream, SUTA degraded corpus WER from $22.45\%$ to $23.55\%$ ($+95$ net word errors) and induced substantial localized regression on Irish English ($15.62\% \rightarrow 18.00\%$, $+2.39$ pp).

### Contribution 2: Tripartite Statistical Safety Architecture (Controller)
We formulate the Disparity Safety Gate (DSG), a controller combining:
1. Tripartite risk bounds ($\Delta_R \le \epsilon_R$, $\max_g \Delta_g \le \epsilon_G$, $\Delta_D \le \epsilon_D$).
2. Paired speaker-cluster bootstrap bounds ($B=1,000$, confidence $0.95$) accounting for clustering.
3. Air-gapped reference panel validation and shadow-candidate parameter isolation.

### Contribution 3: Empirical Validation on Physical Acoustic Data
The controller is neither a blind pass-through nor a hard-coded rejection switch. On physical acoustic data, DSG:
- Admitted 9 candidate updates (4.0%) and rejected 216 (96.0%) based on empirical bootstrap bounds.
- Reduced the net word-error increase observed under SUTA by 93.7% (from $+95$ errors to $+6$ errors relative to No-Adapt).
- Reduced maximum observed subgroup regression from $2.39$ pp to $0.47$ pp.
- Decreased overall cross-accent disparity from $30.25$ pp to $29.50$ pp.

### Final Balanced Scientific Conclusion
> On the external Common Voice 27.0 stream, the risk-controlled DSG admitted 9 of 225 candidate updates and rejected 216 based on the frozen sentinel constraints. Compared with unconstrained SUTA, DSG reduced the net increase in word errors from 95 to 6 and reduced the maximum observed subgroup regression from 2.39 pp to 0.47 pp, while decreasing the overall disparity from 30.25 pp to 29.50 pp. However, DSG remained slightly worse than No-Adapt in overall WER (+0.07 pp), and one accepted update produced a minor adverse external outcome, indicating that the controller provides conservative risk screening rather than a guarantee of harm elimination.

---

## 8. Final Research Artifacts & QA Sign-Off

All final data tables, logs, reports, and QA documentation are committed and locked:
- **Master Evaluation Report:** [`reports/stage5/final_external_evaluation.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/final_external_evaluation.md)
- **Downstream State Trajectory Audit:** [`reports/stage5/stage5e_accepted_updates_trace.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5e_accepted_updates_trace.md)
- **QA Runtime Warnings Forensic Audit:** [`reports/stage5/stage5e_qa_warning_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5e_qa_warning_audit.md)
- **Corpus-Level Benchmark CSV:** [`reports/stage5/final_external_metrics.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/final_external_metrics.csv)
- **Stratum-Level Benchmark CSV:** [`reports/stage5/final_group_metrics.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/final_group_metrics.csv)
- **Decision Audit CSV (225 Windows):** [`reports/stage5/stage5d_final_decision_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5d_final_decision_audit.csv)
- **External Diagnostic Outcome CSV:** [`reports/stage5/stage5d_external_outcome_audit.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5d_external_outcome_audit.csv)
- **Forensic Trace:** [`reports/stage5/stage5d_forensic_trace.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5d_forensic_trace.md)
- **Smoke Test Verification:** [`reports/stage5/stage5d_sentinel_smoke_test.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/stage5d_sentinel_smoke_test.md)

$$\boxed{\textbf{EXPERIMENTAL\_PHASE\_OFFICIALLY\_FROZEN\_AND\_COMPLETE}}$$
