# Stage 3 CTTA Discovery Report (Revised & Extended)

**Project Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition  
**Extended Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR: Characterizing and Controlling Adaptation-Induced Performance Disparities  
**Protocol Version:** `v1.0.0-canonical`  
**Evaluation Partition:** `final_test` (60 real recordings, 6 speakers, 552 reference words across 6 speech variety groups)  
**Primary Track A Backbone:** `facebook/wav2vec2-base-960h`  
**Evaluation Scope:** All 4 CTTA Methods (`no_adapt`, `suta`, `dsuta`, `dmsuta`) $\times$ 3 Stream Orderings (`ORDER_A`, `ORDER_B`, `ORDER_C`)  
**Execution Timestamp:** 2026-09-29T15:52:00Z  

---

## 1. Executive Summary & Scientific Verdict

Stage 3 is technically successful as a **CTTA discovery pilot**, but it is **not strong enough to conclude that adaptation-induced disparity does not occur**. 

### Core Verdict & Canonical Progression:
1. **Pilot Status:** Stage 3 establishes a rigorous, mathematically verified prequential evaluation pipeline and empirical pilot baseline for continual test-time adaptation on real accented speech.
2. **Definitive Decision:** We approve moving forward to **Stage 4 (Phenomenon Characterization & Protocol Strengthening)**, but we explicitly **do NOT approve moving directly to Stage 5 (DSG)**.
3. **No-Manufactured-Intervention Rule:** The static Stage 2 disparity baseline ($D_0$) is treated strictly as the pre-adaptation reference ($\theta_0$), not as evidence that DSG is necessary. Building a disparity safety gate before adaptation-induced disparity growth is demonstrated would manufacture an unjustified solution.

---

## 2. Research Logic

The research progression follows a strictly decoupled, hypothesis-driven hierarchy:

```
Stage 2: Static Disparity Baseline (D_0 exists across fixed models)
                │
                ▼
Stage 3: CTTA Discovery Pilot (Test existing CTTA on incoming speech stream)
                │
                ├───────────────────────────────────────────┐
                ▼                                           ▼
Canonical Stream (ORDER_A):                  Alternative Orderings (ORDER_B, ORDER_C):
Small overall WER gains (ΔR ≤ -0.37%)        Order-dependent subgroup regression (+1.09%)
Disparity slightly reduced (ΔD ≤ -1.08%)      Disparity flat to slightly decreased (ΔD ≤ 0)
No subgroup regression observed (max Δg = 0)  1-word localized shift across 92 reference words
                │                                           │
                └─────────────────────┬─────────────────────┘
                                      │
                                      ▼
                       Does CTTA amplify disparity?
                       NOT demonstrated on this pilot stream
                                      │
                                      ▼
             STAGE 4: Mechanism & Phenomenon Characterization
             (Data-scale expansion, calibrated δ, K sweep, stress tests)
                        /                            \
                       ▼                              ▼
            If coupling demonstrated:        If coupling NOT demonstrated:
            Proceed to Stage 5 (DSG)         Legitimate boundary finding
```

---

## 3. Prequential Protocol & Invariant Verification vs Scientific Power

All streaming evaluations strictly enforce the **prequential evaluation invariant**:
$$\boxed{ B_t \xrightarrow{\theta_t} \text{Record Live Prediction } \hat{Y}_t \xrightarrow{\text{Offline Scoring}} (S, D, I, N) \implies B_t \xrightarrow{\text{Unlabeled Adapt}} \theta_{t+1} }$$

### Invariants Enforced and Verified:
1. **Strict Evaluation Precedence:** Window $B_t$ is evaluated exclusively with live parameters $\theta_t$. Window $B_t$ is **never** evaluated using the adapted model $\theta_{t+1}$.
2. **Strict Label Isolation (Air-Gap):** The online runtime receives only an `UnlabeledAudioBatch` containing raw audio tensors, sample rate, and durations. Reference text, normalized transcripts, speaker IDs, group IDs, and error metrics are quarantined from the online process and joined strictly during offline evaluation.
3. **Sequential Parameter Chaining:** Parameter mutations accumulate across windows: $\theta_0 \to \theta_1 \dots \to \theta_T$, verified via cryptographic SHA-256 state hashes.
4. **Deterministic Orderings:** Cryptographically confirmed stream hashes:
   - `ORDER_A`: `stream_order_a_k4_s42` (Hash: `e02b45a1fd007011...`)
   - `ORDER_B`: `stream_order_b_k4_s42` (Hash: `e45bd9d0921c06db...`)
   - `ORDER_C`: `stream_order_c_k4_s42` (Hash: `5dc02804e713625a...`)

### Methodological Invariant vs Scientific Power:
All 25 automated pipeline tests pass (100%). However:
> **Critical Methodological Distinction:**  
> Passing 25/25 automated tests proves that the software implementation strictly obeys programmed invariants. It does **not** prove that the scientific sample is sufficiently powered to establish a null result.

---

## 4. Benchmark Stream Scale & Word-Level Sensitivity

The Stage 3 evaluation stream consists of:
- **Corpus:** L2-ARCTIC (real speech recordings).
- **Scale:** 60 utterances, 6 speakers, 552 reference words.
- **Subgroups:** 6 groups (Arabic, Hindi, Korean, Mandarin, Spanish, Vietnamese), exactly 10 utterances and $\approx 92$ reference words per group.

### Word-Level Sensitivity Quantification:
Because each subgroup comprises approximately 92 reference words:
$$\Delta WER_g = \frac{1 \text{ word error}}{92 \text{ reference words}} \times 100\% = 1.087\% \approx 1.09\%$$
- The observed $+1.09\%$ subgroup regression under alternative orderings corresponds **literally to a single word alteration**.
- A $+1.09\%$ change is a real observed numerical change, but you **cannot call it practically meaningful or statistically negligible simply from that number**.
- Establishing whether such small effects represent systematic adaptation harm or benign stochastic variation requires confidence intervals and larger-scale multi-speaker evaluation (Stage 4).

---

## 5. Speech Variety Terminology & Confound Context

In L2-ARCTIC, the six evaluated groups (Arabic, Hindi, Korean, Mandarin, Spanish, Vietnamese) represent **L1-associated English speech varieties**, not isolated causal accent variables.
- Speakers' native language phonology, English proficiency, individual vocal tract characteristics, and acoustic recording environments are naturally intertwined.
- The Stage 2 GLMM analysis confirmed that group-level error differences remain statistically significant ($p < 0.001$) after adjusting for signal-to-noise ratio (SNR) and speech rate (WPM).
- However, confound adjustment does not make accent a pure causal variable. In publication, these are strictly described as *L1-associated English speech varieties*.

---

## 6. Window Size Protocol ($K=4$) & Stage 4 Calibration Plan

### Rationale for $K=4$ in Stage 3:
- The choice of window size $K=4$ was the pre-registered default configuration in `configs/default_config.yaml`.
- For a 60-utterance stream with 6 speakers (10 utterances per speaker block), $K=4$ cleanly partitions the stream into exactly 15 sequential windows ($60 / 4 = 15$), providing regular adaptation checkpoints across speaker transitions without intra-window speaker contamination.
- It was chosen for engineering reproducibility on the benchmark pilot, not derived from statistical calibration.

### Stage 4 Granularity Protocol:
In Stage 4, the window size operating point will **not** be chosen arbitrarily. Instead:
1. Window size sweeps will be evaluated across $K \in \{1, 4, 5, 10\}$.
2. The optimal $K$-selection procedure will be frozen using development and calibration partitions before untouched evaluation on the final test stream.

---

## 7. Status of Practical Difference Thresholds ($\delta_G, \delta_D$)

In accordance with Section 18 of the canonical protocol:
> **PRACTICAL SIGNIFICANCE THRESHOLD STATUS:**  
> `UNKNOWN: delta not frozen sufficiently for final discovery`

- We deliberately refuse to retroactively manufacture $\delta$ from test-stream observations.
- Therefore, we distinguish between what can and cannot be claimed:
  - **What CAN be said:** *"No practically meaningful coupling was demonstrated under the current pilot conditions."*
  - **What CANNOT be said:** *"We proved that CTTA does not cause disparity amplification."*
- In Stage 4, $\delta_G$ and $\delta_D$ will be formally frozen via paired speaker-cluster power analysis on calibration data prior to running the decisive experiment.

---

## 8. Canonical ORDER_A Results (Track A, $K=4$)

Under primary stream ordering `ORDER_A` (Arabic $\to$ Hindi $\to$ Korean $\to$ Mandarin $\to$ Spanish $\to$ Vietnamese):

| Method | Live Corpus WER | $\Delta_R$ (vs No-Adapt) | Disparity $D$ | $\Delta_D$ | Worst Regressed Group | $\max_g \Delta_g$ | Updates | Resets |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-Adapt (Control)** | **85.51%** | $0.00\%$ | **20.65%** | $0.00\%$ | None | $0.00\%$ | 0 | 0 |
| **SUTA** | **85.14%** | **-0.37%** | **19.57%** | **-1.08%** | None | $0.00\%$ | 15 | 0 |
| **DSUTA** | **85.33%** | **-0.18%** | **19.57%** | **-1.08%** | None | $0.00\%$ | 15 | 1 |
| **DMSUTA** | **85.51%** | **0.00%** | **20.65%** | **0.00%** | None | $0.00\%$ | 15 | 0 |

### Group-Level Breakdown on ORDER_A:
- **Arabic:** No-Adapt = 89.13%, SUTA = 89.13% ($\Delta_g = 0.00\%$), DSUTA = 89.13% ($\Delta_g = 0.00\%$), DMSUTA = 89.13% ($\Delta_g = 0.00\%$).
- **Hindi:** No-Adapt = 97.83%, SUTA = 96.74% ($\Delta_g = -1.09\%$), DSUTA = 96.74% ($\Delta_g = -1.09\%$), DMSUTA = 97.83% ($\Delta_g = 0.00\%$).
- **Korean:** No-Adapt = 82.61%, SUTA = 82.61% ($\Delta_g = 0.00\%$), DSUTA = 82.61% ($\Delta_g = 0.00\%$), DMSUTA = 82.61% ($\Delta_g = 0.00\%$).
- **Mandarin:** No-Adapt = 77.17%, SUTA = 77.17% ($\Delta_g = 0.00\%$), DSUTA = 77.17% ($\Delta_g = 0.00\%$), DMSUTA = 77.17% ($\Delta_g = 0.00\%$).
- **Spanish:** No-Adapt = 85.87%, SUTA = 85.87% ($\Delta_g = 0.00\%$), DSUTA = 85.87% ($\Delta_g = 0.00\%$), DMSUTA = 85.87% ($\Delta_g = 0.00\%$).
- **Vietnamese:** No-Adapt = 80.43%, SUTA = 79.35% ($\Delta_g = -1.08\%$), DSUTA = 80.43% ($\Delta_g = 0.00\%$), DMSUTA = 80.43% ($\Delta_g = 0.00\%$).

---

## 9. Full Multi-Order Robustness Matrix (4 Methods $\times$ 3 Stream Orders)

To resolve the Stage 3 scope deficit, all primary CTTA methods—not only SUTA—were evaluated across three stream orderings:
- `ORDER_A`: Arabic $\to$ Hindi $\to$ Korean $\to$ Mandarin $\to$ Spanish $\to$ Vietnamese (Canonical)
- `ORDER_B`: Vietnamese $\to$ Spanish $\to$ Mandarin $\to$ Korean $\to$ Hindi $\to$ Arabic (Reverse)
- `ORDER_C`: Hindi $\to$ Mandarin $\to$ Arabic $\to$ Vietnamese $\to$ Korean $\to$ Spanish (Permuted)

### Complete 12-Cell Experimental Matrix:

| Stream Order | Adaptation Method | Corpus WER | $\Delta_R$ (vs No-Adapt) | Disparity $D$ | $\Delta_D$ | Max Group Regression $\max_g \Delta_g$ | Worst Regressed Group |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ORDER_A** | **No-Adapt** | 85.51% | $0.00\%$ | 20.65% | $0.00\%$ | $0.00\%$ | None |
| **ORDER_A** | **SUTA** | 85.14% | **-0.37%** | 19.57% | **-1.08%** | $0.00\%$ | None |
| **ORDER_A** | **DSUTA** | 85.33% | **-0.18%** | 19.57% | **-1.08%** | $0.00\%$ | None |
| **ORDER_A** | **DMSUTA** | 85.51% | $0.00\%$ | 20.65% | $0.00\%$ | $0.00\%$ | None |
| **ORDER_B** | **No-Adapt** | 85.51% | $0.00\%$ | 20.65% | $0.00\%$ | $0.00\%$ | None |
| **ORDER_B** | **SUTA** | 85.69% | **+0.18%** | 20.65% | $0.00\%$ | **+1.09%** | Arabic |
| **ORDER_B** | **DSUTA** | 85.14% | **-0.37%** | 19.57% | **-1.08%** | **+1.09%** | Vietnamese |
| **ORDER_B** | **DMSUTA** | 85.51% | $0.00\%$ | 19.57% | **-1.08%** | **+1.09%** | Arabic |
| **ORDER_C** | **No-Adapt** | 85.51% | $0.00\%$ | 20.65% | $0.00\%$ | $0.00\%$ | None |
| **ORDER_C** | **SUTA** | 85.51% | $0.00\%$ | 20.65% | $0.00\%$ | **+1.09%** | Spanish |
| **ORDER_C** | **DSUTA** | 85.14% | **-0.37%** | 20.65% | $0.00\%$ | **0.00%** | None |
| **ORDER_C** | **DMSUTA** | 85.33% | **-0.18%** | 20.65% | $0.00\%$ | **+1.09%** | Vietnamese |

### Key Multi-Order Findings:
1. **Method Robustness:** SUTA, DSUTA, and DMSUTA all exhibit sensitivity to stream arrival ordering.
2. **Order-Dependent Regression:** While no method produced subgroup regression on `ORDER_A`, localized $+1.09\%$ regressions (1 word) occurred on `ORDER_B` (Arabic for SUTA and DMSUTA; Vietnamese for DSUTA) and `ORDER_C` (Spanish for SUTA; Vietnamese for DMSUTA).
3. **Disparity Invariance:** Across all 9 adapted runs, $\Delta_D \le 0.00\%$ (disparity either contracted by $-1.08\%$ or remained unchanged). **Zero disparity amplification was observed under any tested stream ordering.**

---

## 10. Paired Speaker-Cluster Bootstrap Uncertainty Analysis

To provide rigorous uncertainty analysis for Stage 3 discovery quantities, we executed non-parametric paired speaker-cluster bootstrapping ($B = 1,000$ replicates, $\alpha = 0.05$) across all methods and stream orderings:

| Stream Order | Adaptation Method | Metric | Point Estimate | Bootstrap Mean | Bootstrap Std Error | 95% Confidence Interval | 95% UCB |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **ORDER_A** | **SUTA** | $\Delta_R$ (Overall) | -0.37% | -0.35% | 0.20% | `[-0.72%, 0.00%]` | 0.00% |
| **ORDER_A** | **SUTA** | $\Delta_D$ (Disparity) | -1.08% | -0.72% | 0.52% | `[-1.09%, 0.00%]` | 0.00% |
| **ORDER_A** | **SUTA** | $\max_g \Delta_g$ (Regression) | 0.00% | 0.00% | 0.00% | `[0.00%, 0.00%]` | 0.00% |
| **ORDER_A** | **DSUTA** | $\Delta_R$ (Overall) | -0.18% | -0.17% | 0.16% | `[-0.54%, 0.00%]` | 0.00% |
| **ORDER_A** | **DSUTA** | $\Delta_D$ (Disparity) | -1.08% | -0.71% | 0.52% | `[-1.09%, 0.00%]` | 0.00% |
| **ORDER_A** | **DSUTA** | $\max_g \Delta_g$ (Regression) | 0.00% | 0.00% | 0.00% | `[0.00%, 0.00%]` | 0.00% |
| **ORDER_A** | **DMSUTA** | $\Delta_R$ (Overall) | 0.00% | 0.00% | 0.00% | `[0.00%, 0.00%]` | 0.00% |
| **ORDER_A** | **DMSUTA** | $\Delta_D$ (Disparity) | 0.00% | 0.00% | 0.00% | `[0.00%, 0.00%]` | 0.00% |
| **ORDER_A** | **DMSUTA** | $\max_g \Delta_g$ (Regression) | 0.00% | 0.00% | 0.00% | `[0.00%, 0.00%]` | 0.00% |
| **ORDER_B** | **SUTA** | $\Delta_R$ (Overall) | +0.18% | +0.18% | 0.16% | `[0.00%, +0.54%]` | +0.54% |
| **ORDER_B** | **SUTA** | $\Delta_D$ (Disparity) | 0.00% | +0.29% | 0.48% | `[0.00%, +1.09%]` | +1.09% |
| **ORDER_B** | **SUTA** | $\max_g \Delta_g$ (Regression) | +1.09% | +0.74% | 0.51% | `[0.00%, +1.09%]` | +1.09% |
| **ORDER_B** | **DSUTA** | $\Delta_R$ (Overall) | -0.37% | -0.37% | 0.32% | `[-0.91%, +0.36%]` | +0.18% |
| **ORDER_B** | **DSUTA** | $\Delta_D$ (Disparity) | -1.08% | -1.07% | 0.16% | `[-1.09%, -1.09%]` | -1.09% |
| **ORDER_B** | **DSUTA** | $\max_g \Delta_g$ (Regression) | +1.09% | +0.73% | 0.51% | `[0.00%, +1.09%]` | +1.09% |
| **ORDER_B** | **DMSUTA** | $\Delta_R$ (Overall) | 0.00% | +0.01% | 0.25% | `[-0.54%, +0.54%]` | +0.36% |
| **ORDER_B** | **DMSUTA** | $\Delta_D$ (Disparity) | -1.08% | -0.42% | 0.96% | `[-1.09%, +1.09%]` | +1.09% |
| **ORDER_B** | **DMSUTA** | $\max_g \Delta_g$ (Regression) | +1.09% | +0.74% | 0.51% | `[0.00%, +1.09%]` | +1.09% |
| **ORDER_C** | **SUTA** | $\Delta_R$ (Overall) | 0.00% | 0.00% | 0.25% | `[-0.54%, +0.54%]` | +0.36% |
| **ORDER_C** | **SUTA** | $\Delta_D$ (Disparity) | 0.00% | -0.22% | 0.58% | `[-1.09%, +1.09%]` | +1.09% |
| **ORDER_C** | **SUTA** | $\max_g \Delta_g$ (Regression) | +1.09% | +0.74% | 0.51% | `[0.00%, +1.09%]` | +1.09% |
| **ORDER_C** | **DSUTA** | $\Delta_R$ (Overall) | -0.37% | -0.37% | 0.21% | `[-0.72%, 0.00%]` | 0.00% |
| **ORDER_C** | **DSUTA** | $\Delta_D$ (Disparity) | 0.00% | -0.36% | 0.51% | `[-1.09%, 0.00%]` | 0.00% |
| **ORDER_C** | **DSUTA** | $\max_g \Delta_g$ (Regression) | 0.00% | 0.00% | 0.00% | `[0.00%, 0.00%]` | 0.00% |
| **ORDER_C** | **DMSUTA** | $\Delta_R$ (Overall) | -0.18% | -0.19% | 0.39% | `[-1.09%, +0.54%]` | +0.36% |
| **ORDER_C** | **DMSUTA** | $\Delta_D$ (Disparity) | 0.00% | -0.58% | 0.96% | `[-2.17%, 0.00%]` | 0.00% |
| **ORDER_C** | **DMSUTA** | $\max_g \Delta_g$ (Regression) | +1.09% | +0.73% | 0.51% | `[0.00%, +1.09%]` | +1.09% |

### Statistical Inference from Confidence Intervals:
1. **Zero-Spanning CIs:** Under `ORDER_B` and `ORDER_C`, the 95% confidence intervals for $\Delta_R$ and $\Delta_D$ consistently span zero or include zero (e.g. SUTA ORDER_C $\Delta_R \in [-0.54\%, +0.54\%]$, $\Delta_D \in [-1.09\%, +1.09\%]$).
2. **Regression Uncertainty:** For runs showing localized regression ($\max_g \Delta_g = +1.09\%$), the bootstrap 95% CI is $[0.00\%, +1.09\%]$, confirming that the effect is bounded by a single word shift.
3. **Formal Statistical Conclusion:** We can empirically distinguish observed numerical shifts from robust, statistically significant effects: the observed shifts are small relative to benchmark scale, but the current sample lacks sufficient statistical power to conclude that adaptation is harmless across broader populations.

---

## 11. What Stage 3 Has vs Has NOT Demonstrated

To maintain absolute scientific transparency, we explicitly record the exact boundary of findings:

### NOT Demonstrated:
- ❌ CTTA causes disparity amplification ($\Delta_D > \delta_D$)
- ❌ CTTA causes systematic subgroup regression ($\max_g \Delta_g > \delta_G$)
- ❌ SUTA is harmful
- ❌ DSUTA is harmful
- ❌ DMSUTA is safe
- ❌ DSG is necessary
- ❌ DSG will improve fairness

### Demonstrated / Observed:
- ✅ CTTA can slightly change overall WER ($\Delta_R \in [-0.37\%, +0.18\%]$)
- ✅ SUTA produced small improvements on `ORDER_A` (-0.37%)
- ✅ DSUTA produced small improvements on `ORDER_A` (-0.18%)
- ✅ DMSUTA produced no aggregate change on `ORDER_A` (0.00%)
- ✅ Small order-dependent subgroup regression was observed (+1.09%, 1 word) under alternative stream orderings
- ✅ No meaningful disparity amplification was demonstrated on any tested stream ($\Delta_D \le 0.00\%$)
- ✅ The prequential/label-isolation implementation passed all 25 automated validity tests

---

## 12. Coupling Assessment & Scientific Determination

In accordance with the updated research standard:

> **CANONICAL SCIENTIFIC DETERMINATION:**  
> **"Meaningful coupling is not demonstrated on the current benchmark stream. The observed changes are small, and the current sample size and unfrozen practical-effect threshold prevent a stronger conclusion regarding the absence of adaptation-induced subgroup harm."**

- We deliberately replace the earlier phrasing ("shifts are within measurement noise") with this precise formulation.
- Stage 3 stands as a valid, reproducible discovery pilot that bounds the phenomenon under clean acoustic conditions on a 60-utterance stream.

---

## 13. Stage 4 Roadmap: Phenomenon Characterization

Stage 4 is formally chartered to resolve every weakness identified in Stage 3:

```
STAGE 4A: Data-Scale Expansion
(Maximize independent disjoint speakers across Dev, Cal, Sentinel, Final Test)
        │
        ▼
STAGE 4B: Freeze δ_G and δ_D via Calibration
(Statistically derived practical thresholds from speaker-level power simulation)
        │
        ▼
STAGE 4C: Window Granularity Sweeps
(Evaluate K ∈ {1, 4, 5, 10} under pre-registered protocol)
        │
        ▼
STAGE 4D: Complete Multi-Order Adaptation
(All CTTA methods evaluated across distinct stream permutations)
        │
        ▼
STAGE 4E: Controlled Acoustic Stress Testing
(Acoustic shifts: Additive babble, SNR degradation, non-stationary drift)
        │
        ▼
STAGE 4F: Paired Speaker-Cluster Uncertainty
(Full 95% CIs and UCBs for ΔR, Δg, ΔD across all conditions)
        │
        ▼
STAGE 4G: Condition-Wise Characterization
(Map exact multidimensional boundaries: Method × Order × K × Shift Severity)
        │
        ▼
STAGE 4H: Formal GO / NO-GO Decision for DSG
(Proceed to Stage 5 ONLY if coupling is demonstrated under characterized conditions)
```

---

## 14. Reproducibility & Provenance Checklist

| Verification Metric | Value / Cryptographic Fingerprint | Invariant Status |
| :--- | :--- | :---: |
| **Stream ORDER_A Hash** | `e02b45a1fd007011f1816e88907de3507d4b29bb883c58b4...` | Deterministic |
| **Stream ORDER_B Hash** | `e45bd9d0921c06db18d80f68e09f5fa414a383b0fce04bda...` | Distinct Order |
| **Stream ORDER_C Hash** | `5dc02804e713625afae2cfbbd8e03e7d446b0b2e3e6015ca...` | Distinct Permutation |
| **Prequential Invariant** | Window $B_t$ evaluated strictly with $\theta_t$ before adaptation | Strictly Enforced |
| **Label Isolation** | Air-gapped `UnlabeledAudioBatch` (0 labels, 0 metadata) | Strictly Enforced |
| **Automated Test Suite** | 25 / 25 Passing (100%) | Verified |
| **Bootstrap Confidence Analysis** | 1,000 paired speaker-cluster replicates | Completed |
| **Full Multi-Order Matrix** | 4 Methods $\times$ 3 Stream Orders (12 experimental cells) | Completed |
| **DSG Controller Logic** | Excluded from Stage 3 discovery pipeline | Strictly Preserved |
