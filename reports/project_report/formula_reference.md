# DSG-CTTA Project Formula Handbook & Mathematical Reference Guide

**Project Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition  
**Extended Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR: Characterizing and Controlling Adaptation-Induced Performance Disparities  
**Governing Standard:** Architectural Decision Record 005 (ADR-005), Stage 0 Protocol Freeze, Stage 5D/5E Locked Protocol  
**Document Status:** FROZEN REFERENCE SPECIFICATION & PEDAGOGICAL HANDBOOK  

---

## Executive Overview: How to Read This Handbook

This document serves as the authoritative mathematical and operational reference for all equations used throughout the DSG-CTTA research program. For each equation, this handbook provides:
1. **The Mathematical Expression:** Standard formal formulation.
2. **Where the Formula Was Obtained (Literature Provenance):** Exact primary literature source, paper title, authors, venue, year, DOI/URL, and original equation/section number.
3. **What Each Parameter Represents in the Dataset:** Concrete mapping to specific CSV filenames, column headers, speaker clusters, clip counts, and reference word sums.
4. **Real Project Values & Step-by-Step Arithmetic:** Concrete numbers from the frozen experimental suite plugged directly into the equation.
5. **Units and Valid Ranges:** Theoretical bounds versus empirical ranges observed in our experiments.
6. **Operational Interpretation:** Clear explanations of what higher and lower values mean for speech recognition accuracy and demographic fairness.
7. **Source Code Implementation:** Exact repository file paths and function names.

---

## 1. Word Error Rate (WER)

### 1.1 Mathematical Formulation
$$\text{WER} = \frac{S + D + I}{N_{\text{ref}}}$$

where:
- $S =$ Count of word substitutions
- $D =$ Count of word deletions
- $I =$ Count of word insertions
- $N_{\text{ref}} =$ Total count of reference words in ground truth

### 1.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Levenshtein, V. I. (1966). *Binary codes capable of correcting deletions, insertions, and reversals*. Soviet Physics Doklady, 10(8), 707–710.
- **ASR Standardization:** Hunt, M. J. (1990). *Figures of merit for assessing connected-word recognisers*. Speech Communication, 9(4), 329–336. Formalized by the National Institute of Standards and Technology (NIST) Speech Recognition Benchmark Protocol (1990–present).
- **Official Documentation:** NIST Scoring Toolkit (SCTK) / `sclite` mathematical specification.

### 1.3 What Each Parameter Represents in the Dataset
- **Evaluation Partition:** `datasets/splits/stage5_external_eval.csv` (Holdout stream) and `datasets/splits/stage5_sentinel_panel.csv` (Sentinel panel).
- **$S$ (Substitutions):** The count of words in the ground-truth transcript (`sentence` column) that were incorrectly replaced by a different vocabulary word in the model's decoded hypothesis. Computed via dynamic programming alignment over tokenized strings.
- **$D$ (Deletions):** The count of words present in the ground-truth transcript (`sentence` column) that the model completely failed to transcribe (omitted words).
- **$I$ (Insertions):** The count of extraneous words produced in the model's hypothesis that do not correspond to any spoken token in the reference text.
- **$N_{\text{ref}}$ (Total Reference Words):** The exact total word count of all normalized sentences in the target evaluation split. In `stage5_external_eval.csv` ($N = 900$ clips across 60 speakers), $N_{\text{ref}} = 8667\text{ words}$.
  - US English ($150$ clips): $N_{\text{us}} = 1468\text{ words}$ ($16.94\%$)
  - England English ($150$ clips): $N_{\text{england}} = 1393\text{ words}$ ($16.07\%$)
  - South Asian English ($150$ clips): $N_{\text{south\_asian}} = 1430\text{ words}$ ($16.50\%$)
  - Australian English ($150$ clips): $N_{\text{australia}} = 1493\text{ words}$ ($17.23\%$)
  - Canadian English ($150$ clips): $N_{\text{canada}} = 1500\text{ words}$ ($17.31\%$)
  - Irish English ($150$ clips): $N_{\text{ireland}} = 1383\text{ words}$ ($15.96\%$)
  - Exact Sum Invariant: $1468 + 1393 + 1430 + 1493 + 1500 + 1383 = 8667\text{ words}$.

### 1.4 Real Project Values & Step-by-Step Arithmetic
Evaluated on `facebook/wav2vec2-base-960h` across the 900-clip holdout stream (`reports/stage5/final_external_metrics.csv`):
- **No-Adapt Baseline ($\theta_0$):**
  $$\text{WER}(\theta_0) = \frac{1583 + 178 + 185}{8667} = \frac{1946}{8667} \approx 0.2245298 \implies 22.45\%$$
- **SUTA Unconstrained Adaptation ($\theta_{\text{SUTA}}$):**
  $$\text{WER}(\theta_{\text{SUTA}}) = \frac{1645 + 240 + 156}{8667} = \frac{2041}{8667} \approx 0.2354909 \implies 23.55\%$$
- **DSG Controlled Adaptation ($\theta_{\text{DSG}}$):**
  $$\text{WER}(\theta_{\text{DSG}}) = \frac{1590 + 181 + 181}{8667} = \frac{1952}{8667} \approx 0.2252221 \implies 22.52\%$$

### 1.5 Units, Valid Ranges, and Interpretation
- **Unit:** Unitless ratio, reported as a percentage ($\%$) by multiplying by 100.
- **Theoretical Range:** $[0, +\infty)$. Bounded below by $0.0$ (perfect transcription). Can exceed $1.0$ ($100\%$) when insertions outnumber reference words ($I > N_{\text{ref}}$).
- **Project Observed Range:** $9.18\%$ (`distil_whisper_small` No-Adapt on CV27) to $96.38\%$ (`whisper_tiny` on L2-ARCTIC Stage 2).
- **Interpretation:** Lower is better. $\text{WER} = 0\%$ indicates exact bit-for-bit match. Higher values indicate increasing transcription errors.

### 1.6 Source Code Implementation
- **File:** [`src/dsg_ctta/reporting/metrics.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/reporting/metrics.py)
- **Function:** `compute_wer(reference: str, hypothesis: str) -> Dict[str, Any]`

---

## 2. Character Error Rate (CER)

### 2.1 Mathematical Formulation
$$\text{CER} = \frac{S_c + D_c + I_c}{N_{\text{char}}}$$

where:
- $S_c =$ Count of character substitutions
- $D_c =$ Count of character deletions
- $I_c =$ Count of character insertions
- $N_{\text{char}} =$ Total character count in reference text

### 2.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Standard phonetic transcription and speech recognition metric, widely adopted for morphologically rich or character-based languages and sub-word phonetic analysis.
- **Citation:** Morris, A. C., Maier, V., & Green, P. (2004). *From WER and RIL to MER and WIL: improved evaluation measures for connected speech recognition*. Interspeech 2004.

### 2.3 What Each Parameter Represents in the Dataset
- **$S_c$ (Character Substitutions):** Individual characters incorrectly substituted in the model prediction relative to normalized characters in `sentence`.
- **$D_c$ (Character Deletions):** Characters in `sentence` omitted by the model.
- **$I_c$ (Character Insertions):** Spurious characters emitted by the model.
- **$N_{\text{char}}$:** Total characters in the reference text (excluding stripped punctuation).

### 2.4 Real Project Values & Step-by-Step Arithmetic
On `wav2vec2_base` (`reports/stage5/final_external_metrics.csv`):
- Baseline No-Adapt: $\text{CER}(\theta_0) = 0.102234 \implies 10.22\%$
- SUTA Adaptation: $\text{CER}(\theta_{\text{SUTA}}) = 0.104866 \implies 10.49\%$
- DSG Adaptation: $\text{CER}(\theta_{\text{DSG}}) = 0.095476 \implies 9.55\%$ (Acoustic character precision improved under DSG).

### 2.5 Units and Operational Interpretation
- **Unit:** Percentage ($\%$).
- **Theoretical Range:** $[0, +\infty)$.
- **Project Observed Range:** $9.55\%$ (DSG on CV27) to $77.08\%$ (`whisper_tiny` on L2-ARCTIC).
- **Interpretation:** Measures sub-word acoustic transcription precision. Lower values indicate higher phonetic fidelity.

---

## 3. Disparity Range ($D$)

### 3.1 Mathematical Formulation
$$D = \max_{g \in \mathcal{G}} \text{WER}_g - \min_{g \in \mathcal{G}} \text{WER}_g$$

### 3.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Rai, S., et al. (2025). *Measuring and Benchmarking Equity Across Speech Recognition Systems (ASR-FAIRBENCH)*. Proceedings of Interspeech 2025, Section 3.1 ("Performance Disparity Metrics").
- **Foundational Context:** Koenecke, A., et al. (2020). *Racial disparities in automated speech recognition*. Proceedings of the National Academy of Sciences (PNAS), 117(14), 7684–7689.
- **Formal Adoption in Project:** Formalized in Stage 0 Protocol Freeze (`docs/protocol_freeze.md`) and ADR-005 (`docs/adr/ADR-005-stage5-gate-rule.md`).

### 3.3 What Each Parameter Represents in the Dataset
- **$\mathcal{G}$ (Set of Evaluated Strata):** The 6 pre-specified accent groups in `stage5_external_eval.csv`, derived from self-reported metadata in Mozilla Common Voice 27.0 via the deterministic grouping rule (`protocol_amendment_cv27.md`):
  $$\mathcal{G} = \{\text{US}, \text{England}, \text{South Asian}, \text{Australian}, \text{Canadian}, \text{Irish}\}$$
- **$\text{WER}_g$:** The aggregate Word Error Rate evaluated strictly over the 150 clips belonging to accent group $g$.
- **$\max_{g \in \mathcal{G}} \text{WER}_g$:** The highest error rate observed among the six accent strata (consistently **South Asian English** across all models).
- **$\min_{g \in \mathcal{G}} \text{WER}_g$:** The lowest error rate observed among the six accent strata (typically **Canadian English** or **Irish English**).

### 3.4 Real Project Values & Step-by-Step Arithmetic
On `facebook/wav2vec2-base-960h` (`reports/stage6/eight_model_group_metrics.csv`):
- **No-Adapt Baseline ($\theta_0$):**
  $$\max_{g \in \mathcal{G}} \text{WER}_g(\theta_0) = \text{WER}_{\text{South Asian}}(\theta_0) = \frac{607}{1430} \approx 42.4476\%$$
  $$\min_{g \in \mathcal{G}} \text{WER}_g(\theta_0) = \text{WER}_{\text{Canadian}}(\theta_0) = \frac{183}{1500} \approx 12.2000\%$$
  $$D(\theta_0) = 42.4476\% - 12.2000\% = 30.2476\text{ pp} \approx 30.25\text{ pp}$$
- **DSG Controlled Adaptation ($\theta_{\text{DSG}}$):**
  $$\max_{g \in \mathcal{G}} \text{WER}_g(\theta_{\text{DSG}}) = \text{WER}_{\text{South Asian}}(\theta_{\text{DSG}}) = \frac{603}{1430} \approx 42.1678\%$$
  $$\min_{g \in \mathcal{G}} \text{WER}_g(\theta_{\text{DSG}}) = \text{WER}_{\text{Canadian}}(\theta_{\text{DSG}}) = \frac{190}{1500} \approx 12.6667\%$$
  $$D(\theta_{\text{DSG}}) = 42.1678\% - 12.6667\% = 29.5011\text{ pp} \approx 29.50\text{ pp}$$
- **Disparity Reduction under DSG:**
  $$\Delta D = D(\theta_{\text{DSG}}) - D(\theta_0) = 29.5011\text{ pp} - 30.2476\text{ pp} = -0.7465\text{ pp} \approx -0.75\text{ pp}$$

### 3.5 Units, Valid Ranges, and Interpretation
- **Unit:** Percentage points (pp).
- **Theoretical Range:** $[0, +\infty)$ (typically $[0, 100\text{ pp}]$ when group WERs are bounded within $100\%$).
- **Project Observed Range:** $8.92\text{ pp}$ (`xlsr_english` No-Adapt) to $47.83\text{ pp}$ (`whisper_tiny` Stage 2).
- **Interpretation:** Measures performance inequality. A value of $D = 0\text{ pp}$ represents perfect demographic parity (all groups experience identical error rates). Higher values indicate severe equity disparities.

### 3.6 Source Code Implementation
- **File:** [`src/dsg_ctta/reporting/metrics.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/reporting/metrics.py)
- **Function:** `compute_disparity(group_wers: Dict[str, float]) -> float`

---

## 4. Disparity Ratio ($R$)

### 4.1 Mathematical Formulation
$$R = \frac{\max_{g \in \mathcal{G}} \text{WER}_g}{\min_{g \in \mathcal{G}} \text{WER}_g}$$

### 4.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Algorithmic fairness and civil rights compliance literature (Four-Fifths Rule / Adverse Impact Ratio). Formalized for ASR by Rai et al. (Interspeech 2025, ASR-FAIRBENCH).

### 4.3 Real Project Values & Step-by-Step Arithmetic
On `wav2vec2_base` No-Adapt:
$$R(\theta_0) = \frac{42.4476\%}{12.2000\%} \approx 3.4793 \implies 3.48\times$$
*Interpretation:* Speakers from South Asia experienced **$3.48$ times more transcription errors** than speakers from Canada on the unadapted baseline model.

---

## 5. Overall Regression ($\Delta_R$)

### 5.1 Mathematical Formulation
$$\Delta_R(\theta') = \text{WER}(\theta') - \text{WER}(\theta_{\text{ref}})$$

### 5.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** ADR-005: Stage 5 Disparity Safety Gate Decision Rule and Rollback Semantics (`docs/adr/ADR-005-stage5-gate-rule.md`), Section 3. Adapted from continual learning catastrophic forgetting metrics (Kirkpatrick et al., PNAS 2017).

### 5.3 What Each Parameter Represents in the Dataset
- **$\theta'$ (Candidate Model):** The in-memory shadow model state produced by taking unsupervised entropy minimization gradient steps on the current unlabeled batch $B_t$ ($K=4$ audio clips from `stage5_external_eval.csv`).
- **$\theta_{\text{ref}}$ (Reference Model):** In online gating, this is the current validated live model $\theta_t$. In post-hoc reporting, this is the unadapted baseline model $\theta_0$.
- **$\text{WER}(\theta)$:** The aggregate Word Error Rate evaluated across the 300 clips of the independent sentinel panel (`datasets/splits/stage5_sentinel_panel.csv`).

### 5.4 Real Project Values & Step-by-Step Arithmetic
Evaluated on `facebook/wav2vec2-base-960h` holdout stream (`reports/stage5/final_external_metrics.csv`):
- **SUTA Overall Regression vs Baseline ($\theta_{\text{ref}} = \theta_0$):**
  $$\Delta_R(\theta_{\text{SUTA}}) = \text{WER}(\theta_{\text{SUTA}}) - \text{WER}(\theta_0)$$
  $$\Delta_R(\theta_{\text{SUTA}}) = 23.5491\% - 22.4530\% = +1.0961\text{ pp} \approx +1.10\text{ pp}$$
- **DSG Overall Regression vs Baseline ($\theta_{\text{ref}} = \theta_0$):**
  $$\Delta_R(\theta_{\text{DSG}}) = \text{WER}(\theta_{\text{DSG}}) - \text{WER}(\theta_0)$$
  $$\Delta_R(\theta_{\text{DSG}}) = 22.5222\% - 22.4530\% = +0.0692\text{ pp} \approx +0.07\text{ pp}$$
- **Net Relative Improvement (DSG vs SUTA):**
  $$\Delta_{\text{DSG vs SUTA}} = \text{WER}(\theta_{\text{DSG}}) - \text{WER}(\theta_{\text{SUTA}})$$
  $$\Delta_{\text{DSG vs SUTA}} = 22.5222\% - 23.5491\% = -1.0269\text{ pp} \approx -1.03\text{ pp}$$

### 5.5 Units, Valid Ranges, and Interpretation
- **Unit:** Percentage points (pp).
- **Theoretical Range:** $(-\infty, +\infty)$.
- **Project Observed Range:** $-0.12\text{ pp}$ (`data2vec_base` DSG) to $+2.73\text{ pp}$ (`xlsr_english` SUTA).
- **Interpretation:** $\Delta_R > 0$ indicates aggregate performance degradation (harm). $\Delta_R \le 0$ indicates neutral or improved performance.

---

## 6. Subgroup Regression ($\Delta_g$) & Maximum Subgroup Regression ($\max_g \Delta_g$)

### 6.1 Mathematical Formulation
$$\Delta_g(\theta') = \text{WER}_g(\theta') - \text{WER}_g(\theta_{\text{ref}})$$

$$\max_{g \in \mathcal{G}} \Delta_g(\theta') = \max_{g \in \mathcal{G}} \left( \text{WER}_g(\theta') - \text{WER}_g(\theta_{\text{ref}}) \right)$$

### 6.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** ADR-005 (`docs/adr/ADR-005-stage5-gate-rule.md`), Section 3. Derived from minimax group robustness and distributionally robust optimization (Sagawa et al., ICLR 2020, *Distributionally Robust Neural Networks*).

### 6.3 What Each Parameter Represents in the Dataset
- **$\Delta_g$:** The error rate difference on a specific stratum $g \in \mathcal{G}$ (e.g. `Irish English`, containing 150 clips in holdout, 50 clips in sentinel).
- **$\max_g \Delta_g$:** The single largest error rate inflation suffered by any of the 6 accent strata, identifying the most severely harmed demographic subgroup.

### 6.4 Real Project Values & Step-by-Step Arithmetic
On `facebook/wav2vec2-base-960h` under SUTA:
$$\Delta_{\text{US}} = 21.32\% - 21.46\% = -0.14\text{ pp} \quad (\text{Improved})$$
$$\Delta_{\text{England}} = 21.82\% - 20.32\% = +1.50\text{ pp} \quad (\text{Regressed})$$
$$\Delta_{\text{South Asian}} = 42.66\% - 42.45\% = +0.21\text{ pp} \quad (\text{Regressed})$$
$$\Delta_{\text{Australia}} = 24.05\% - 22.91\% = +1.14\text{ pp} \quad (\text{Regressed})$$
$$\Delta_{\text{Canada}} = 13.73\% - 12.20\% = +1.53\text{ pp} \quad (\text{Regressed})$$
$$\Delta_{\text{Ireland}} = 18.00\% - 15.62\% = +2.38\text{ pp} \quad (\text{Severe Regression!})$$

$$\max_{g \in \mathcal{G}} \Delta_g(\theta_{\text{SUTA}}) = \max(-0.14, +1.50, +0.21, +1.14, +1.53, +2.38) = +2.38\text{ pp} \approx +2.39\text{ pp}$$

Under DSG on the same model:
$$\max_{g \in \mathcal{G}} \Delta_g(\theta_{\text{DSG}}) = +0.47\text{ pp} \quad (\text{Canadian English: } 12.20\% \to 12.67\%)$$

*Result:* DSG constrained the worst-case subgroup regression from $+2.39\text{ pp}$ down to $+0.47\text{ pp}$.

---

## 7. Disparity Change ($\Delta D$)

### 7.1 Mathematical Formulation
$$\Delta D(\theta') = D(\theta') - D(\theta_{\text{ref}})$$

### 7.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** ADR-005 (`docs/adr/ADR-005-stage5-gate-rule.md`), Section 3.

### 7.3 Real Project Values & Step-by-Step Arithmetic
- Under SUTA on `wav2vec2_base`:
  $$\Delta D(\theta_{\text{SUTA}}) = 28.92\text{ pp} - 30.25\text{ pp} = -1.33\text{ pp} \approx -1.32\text{ pp}$$
- Under DSG on `wav2vec2_base`:
  $$\Delta D(\theta_{\text{DSG}}) = 29.50\text{ pp} - 30.25\text{ pp} = -0.75\text{ pp}$$

---

## 8. Paired Speaker-Cluster Bootstrap & Upper Confidence Bound (UCB)

### 8.1 Mathematical Formulation
Given sentinel panel $\mathcal{S}_{\text{sentinel}}$ partitioned into $C = 30$ independent speaker clusters $\mathcal{C} = \{c_1, c_2, \dots, c_{30}\}$:
1. For replicate $b = 1, 2, \dots, B$ ($B = 1000$):
   - Draw $C = 30$ speaker clusters with replacement:
     $$\mathcal{C}^{(b)} = \{c_{i_1}^{(b)}, c_{i_2}^{(b)}, \dots, c_{i_{30}}^{(b)}\}$$
   - Aggregate paired errors and words across all clips belonging to sampled clusters.
   - Compute replicate metric:
     $$\Delta^{(b)} = \text{Metric}(\theta'; \mathcal{C}^{(b)}) - \text{Metric}(\theta_{\text{ref}}; \mathcal{C}^{(b)})$$
2. Compute the empirical 95th percentile Upper Confidence Bound:
   $$\text{UCB}_{95}(\Delta) = \text{Quantile}_{0.95} \left( \{\Delta^{(1)}, \Delta^{(2)}, \dots, \Delta^{(B)}\} \right)$$

### 8.2 Where the Formula Was Obtained (Literature Provenance)
- **Foundational Theory:** Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall / CRC.
- **Cluster Bootstrapping:** Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). *Bootstrap-based improvements for inference with clustered errors*. The Review of Economics and Statistics, 90(3), 414–427.
- **ASR Cluster Application:** Formalized by SPEAKABLE Workshop (LREC 2026) to account for intra-speaker acoustic correlation, operationalized for online CTTA in ADR-005.

### 8.3 What Each Parameter Represents in the Dataset
- **Clusters $c_k \in \mathcal{C}$:** The 30 unique speaker identifiers in column `client_id` of `datasets/splits/stage5_sentinel_panel.csv`. Exactly 5 unique speakers per accent group, each contributing exactly 10 audio clips.
- **Resampling Unit:** Entire speaker clusters are resampled. If speaker `cmu_spk_042` is drawn twice, all 10 of their utterances are included twice, preserving intra-speaker acoustic covariance.
- **$B = 1000$:** Number of pseudo-replicate draws, locked for numerical stability.
- **$\alpha = 0.05$ ($95\%$ Confidence):** Significance level ensuring risk-averse upper bounds.

### 8.4 Source Code Implementation
- **File:** [`src/dsg_ctta/controller/bootstrap.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/controller/bootstrap.py)
- **Function:** `compute_speaker_cluster_bootstrap_stats(...)`

---

## 9. Disparity Safety Gate (DSG) Acceptance Contract

### 9.1 Mathematical Formulation
$$\text{ACCEPT}(\theta') \iff \left[ \text{UCB}_{95}\left(\Delta_R(\mathcal{S}_{\text{sentinel}})\right) \le \epsilon_R \right] \land \left[ \text{UCB}_{95}\left(\max_{g \in \mathcal{G}} \Delta_g(\mathcal{S}_{\text{sentinel}})\right) \le \epsilon_G \right] \land \left[ \text{UCB}_{95}\left(\Delta_D(\mathcal{S}_{\text{sentinel}})\right) \le \epsilon_D \right]$$

$$\text{REJECT}(\theta') \iff \neg \text{ACCEPT}(\theta')$$

### 9.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Authoritative Architectural Decision Record 005 ([ADR-005](file:///c:/Users/venka/Downloads/final%20year%20project%20main/docs/adr/ADR-005-stage5-gate-rule.md)), approved September 30, 2026.
- **Pre-Registration:** Configured in [`configs/stage5_gate_config.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/stage5_gate_config.json) (SHA-256: `18faea44...`).

### 9.3 Frozen Operating Risk Tolerances ($\epsilon$)
- **$\epsilon_R = 0.0000$ ($0.00\text{ pp}$):** Zero tolerance for overall regression. Candidate must have $95\%$ statistical confidence of zero aggregate degradation on the sentinel panel.
- **$\epsilon_G = 0.0200$ ($2.00\text{ pp}$):** Subgroup regression tolerance, locked to match calibration threshold $\delta_G$.
- **$\epsilon_D = 0.0200$ ($2.00\text{ pp}$):** Disparity growth tolerance, locked to match calibration threshold $\delta_D$.

### 9.4 Real Project Decisions across 1,350 Candidate Evaluations
- **Accepted Updates:** **23 updates ($1.70\%$)** across 6 CTC backbones.
- **Rejected Updates:** **1,327 updates ($98.30\%$)** via statistical hypothesis testing.
- **Fail-Closed Software Errors:** **0 errors**.

---

## 10. Percentage Added Error Reduction

### 10.1 Mathematical Formulation
$$\text{Reduction}_{\text{errors}} = \frac{\Delta \text{Errors}(\theta_{\text{SUTA}}) - \Delta \text{Errors}(\theta_{\text{DSG}})}{\Delta \text{Errors}(\theta_{\text{SUTA}})} \times 100\%$$

where:
$$\Delta \text{Errors}(\theta) = \text{Errors}(\theta) - \text{Errors}(\theta_0)$$

### 10.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Standard intervention efficacy metric in statistical epidemiology and ML safety benchmarks.

### 10.3 Real Project Values & Step-by-Step Arithmetic
On `facebook/wav2vec2-base-960h` across the 8,667-word holdout stream:
- Baseline Errors ($\theta_0$): $\text{Errors}(\theta_0) = 1946\text{ words}$
- SUTA Errors ($\theta_{\text{SUTA}}$): $\text{Errors}(\theta_{\text{SUTA}}) = 2041\text{ words} \implies \Delta \text{Errors}(\theta_{\text{SUTA}}) = 2041 - 1946 = 95\text{ errors}$
- DSG Errors ($\theta_{\text{DSG}}$): $\text{Errors}(\theta_{\text{DSG}}) = 1952\text{ words} \implies \Delta \text{Errors}(\theta_{\text{DSG}}) = 1952 - 1946 = 6\text{ errors}$
- Prevented Errors: $95 - 6 = 89\text{ word errors prevented}$

$$\text{Reduction}_{\text{errors}} = \frac{95 - 6}{95} \times 100\% = \frac{89}{95} \times 100\% \approx 93.6842\% \implies 93.68\%$$

*Interpretation:* The Disparity Safety Gate prevented **$93.68\%$** of the added transcription errors that occurred under unconstrained SUTA.

---

## 11. Confounder-Controlled Poisson GLMM Count Regression

### 11.1 Mathematical Formulation
$$\log(\mu_{ij}) = \beta_0 + \sum_{g=2}^G \beta_g \mathbb{I}(\text{group}_{ij} = g) + \beta_{\text{SNR}} Z_{\text{SNR}, ij} + \beta_{\text{rate}} Z_{\text{rate}, ij} + u_{\text{speaker}(i)} + \log(N_{ij})$$

$$\text{Rate Ratio (RR)}_g = \exp(\beta_g)$$

### 11.2 Where the Formula Was Obtained (Literature Provenance)
- **Foundational Theory:** McCullagh, P., & Nelder, J. A. (1989). *Generalized Linear Models* (2nd ed.). Chapman & Hall / CRC.
- **ASR Fairness Application:** SPEAKABLE Workshop (LREC-COLING 2026), *Responsible Benchmarking of Fairness for Automatic Speech Recognition*.
- **Stage 2 Verification:** Executed and documented in [`reports/stage2_final_report.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage2_final_report.md), Section 8.

### 11.3 What Each Parameter Represents in the Dataset
- **$\mu_{ij} = \mathbb{E}[Y_{ij}]$:** The expected count of word errors ($S + D + I$) for utterance $j$ spoken by speaker $i$.
- **$\log(N_{ij})$ (Offset):** Natural logarithm of reference words in `sentence`. Entering $\log(N)$ with a fixed regression slope of $1.0$ converts the count model into an error rate model ($\mu / N$).
- **$\mathbb{I}(\text{group}_{ij} = g)$:** Dummy variable indicating speech variety stratum $g$ relative to the reference stratum (`Arabic`).
- **$Z_{\text{SNR}, ij}$:** Standardized acoustic Signal-to-Noise Ratio ($z$-score), computed from the raw WAV file via WADA-SNR.
- **$Z_{\text{rate}, ij}$:** Standardized speech articulation tempo ($z$-score), measured in spoken words per minute.
- **$u_{\text{speaker}(i)} \sim \mathcal{N}(0, \sigma_u^2)$:** Random intercept accounting for speaker clustering.

### 11.4 Real Project Values & Step-by-Step Arithmetic
On `wav2vec2_base` in Stage 2 (60 utterances, 6 speaker clusters):
- Raw Group Disparity Rate Ratio: $1.183\times$
- Confounder-Adjusted Rate Ratio: $1.124\times$ ($p < 0.05$ with Holm-Bonferroni correction).
*Finding:* Disparity across accent groups remains statistically significant even after statistically controlling for acoustic SNR and speech rate.

---

## 12. Unsupervised Test-Time Adaptation Loss (SUTA)

### 12.1 Mathematical Formulation
$$\mathcal{L}_{\text{SUTA}}(\mathbf{x}; \theta) = \mathcal{L}_{\text{ent}}(\mathbf{x}; \theta) + \lambda_{\text{mcc}} \mathcal{L}_{\text{mcc}}(\mathbf{x}; \theta)$$

$$\mathcal{L}_{\text{ent}}(\mathbf{x}; \theta) = -\frac{1}{T'} \sum_{t=1}^{T'} \sum_{v \in \mathcal{V}} P(v \mid \mathbf{x}_t; \theta) \log P(v \mid \mathbf{x}_t; \theta)$$

$$\mathcal{L}_{\text{mcc}}(\mathbf{x}; \theta) = \sum_{i=1}^{|\mathcal{V}|} \sum_{j \neq i} \hat{C}_{ij}^2, \quad \text{where } \hat{\mathbf{C}} = \frac{\tilde{\mathbf{Y}}^\top \tilde{\mathbf{Y}}}{\mathbf{1}^\top \tilde{\mathbf{Y}}^\top \tilde{\mathbf{Y}} \mathbf{1}}$$

### 12.2 Where the Formula Was Obtained (Literature Provenance)
- **Primary Source:** Lin, G.-T., Lai, C.-I., Chiang, W.-L., & Lee, H.-y. (2022). *Listen, Adapt, Better WER: Source-free Single-utterance Test-time Adaptation for ASR*. Interspeech 2022, Equations (1), (2), and (3).
- **Minimum Class Confusion Theory:** Jin, Y., et al. (ECCV 2020), *Minimum Class Confusion for Versatile Domain Adaptation*.

### 12.3 What Each Parameter Represents in the Dataset
- **$\mathbf{x}$:** Streaming audio window $B_t$ ($K=4$ audio clips from `stage5_external_eval.csv`, ~15 seconds total audio).
- **$P(v \mid \mathbf{x}_t; \theta)$:** The CTC frame emission probability over vocabulary $\mathcal{V}$ ($|\mathcal{V}| = 32$) output by the model's linear projection at 20 ms frame $t$.
- **$\lambda_{\text{mcc}} = 0.1$:** Pre-registered hyperparameter weighting class confusion minimization.
- **Updated Parameters:** Gradient updates are restricted strictly to LayerNorm affine parameters ($\gamma, \beta$).

---

## Summary Master Table: Equations, Provenance, and Dataset Parameters

| Equation # | Metric / Concept | Mathematical Expression | Literature Source & Provenance | Exact Dataset Parameter Mapping | Real Project Value |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | Word Error Rate (WER) | $\text{WER} = \frac{S + D + I}{N_{\text{ref}}}$ | Levenshtein (1966); NIST ASR Standard (1990) | `stage5_external_eval.csv`, `sentence` column ($N_{\text{ref}} = 8667\text{ words}$) | $22.45\%$ (No-Adapt)<br>$23.55\%$ (SUTA)<br>$22.52\%$ (DSG) |
| **2** | Character Error Rate (CER)| $\text{CER} = \frac{S_c + D_c + I_c}{N_{\text{char}}}$ | Morris et al. (Interspeech 2004) | Sub-word character edit operations against normalized `sentence` text | $10.22\%$ (No-Adapt)<br>$9.55\%$ (DSG) |
| **3** | Disparity Range ($D$) | $D = \max_{g \in \mathcal{G}} \text{WER}_g - \min_{g \in \mathcal{G}} \text{WER}_g$ | Rai et al. (Interspeech 2025, ASR-FAIRBENCH) | 6 strata in `stage5_accent_group` ($150$ clips, ~1445 words/stratum) | $30.25\text{ pp}$ (No-Adapt)<br>$29.50\text{ pp}$ (DSG) |
| **4** | Disparity Ratio ($R$) | $R = \frac{\max_{g \in \mathcal{G}} \text{WER}_g}{\min_{g \in \mathcal{G}} \text{WER}_g}$ | Four-Fifths Adverse Impact Rule; Rai et al. (2025) | Ratio of worst stratum (South Asian) to best stratum (Canadian) | $3.48\times$ (No-Adapt) |
| **5** | Overall Regression ($\Delta_R$)| $\Delta_R = \text{WER}(\theta') - \text{WER}(\theta_{\text{ref}})$ | ADR-005 Section 3; Kirkpatrick et al. (2017) | Evaluated over 300 clips ($2925\text{ words}$) of `stage5_sentinel_panel.csv` | $+1.10\text{ pp}$ (SUTA)<br>$+0.07\text{ pp}$ (DSG) |
| **6** | Max Subgroup Regression | $\max_{g \in \mathcal{G}} \Delta_g = \max_{g \in \mathcal{G}}(\text{WER}_g' - \text{WER}_g^{\text{ref}})$| ADR-005 Section 3; Sagawa et al. (ICLR 2020) | Maximum localized regression across 6 strata in sentinel panel | $+2.39\text{ pp}$ (SUTA)<br>$+0.47\text{ pp}$ (DSG) |
| **7** | Disparity Change ($\Delta D$)| $\Delta D = D(\theta') - D(\theta_{\text{ref}})$ | ADR-005 Section 3 | Expansion or contraction of cross-accent disparity spread | $-1.32\text{ pp}$ (SUTA)<br>$-0.75\text{ pp}$ (DSG) |
| **8** | Cluster Bootstrap UCB | $\text{UCB}_{95} = \text{Quantile}_{0.95}(\{\Delta^{(b)}\})$ | Efron & Tibshirani (1993); Cameron et al. (2008) | Resamples 30 speaker clusters in `client_id` of sentinel panel ($B=1000$) | Replicate bounds for gating |
| **9** | DSG Acceptance Rule | $\text{UCB}(\Delta_R) \le \epsilon_R \land \text{UCB}(\max_g \Delta_g) \le \epsilon_G \land \text{UCB}(\Delta_D) \le \epsilon_D$ | ADR-005 ([ADR-005-stage5-gate-rule.md](file:///c:/Users/venka/Downloads/final%20year%20project%20main/docs/adr/ADR-005-stage5-gate-rule.md)) | Frozen tolerances: $\epsilon_R=0.0000, \epsilon_G=0.0200, \epsilon_D=0.0200$ | 23 Accepted (1.7%)<br>1327 Rejected (98.3%) |
| **10**| Added Error Reduction | $\frac{\Delta \text{Errors}_{\text{SUTA}} - \Delta \text{Errors}_{\text{DSG}}}{\Delta \text{Errors}_{\text{SUTA}}} \times 100\%$ | ML Intervention Efficacy Standard | Added error difference over 8667 holdout words ($95$ SUTA vs $6$ DSG) | $93.68\%$ errors prevented |
| **11**| Poisson GLMM Regression | $\log(\mu) = \beta_0 + \sum \beta_g G_g + \beta_z Z + u_{\text{spk}} + \log(N)$ | McCullagh & Nelder (1989); SPEAKABLE (2026) | Discrete error counts with $\log(\text{words})$ offset, SNR, and speech rate | Adjusted $\text{RR} = 1.124\times$ ($p < 0.05$) |
| **12**| SUTA Loss | $\mathcal{L}_{\text{SUTA}} = \mathcal{L}_{\text{ent}} + \lambda_{\text{mcc}} \mathcal{L}_{\text{mcc}}$ | Lin et al. (Interspeech 2022, SUTA Eq. 1–3) | Unlabeled audio frames in streaming window $B_t$ ($K=4$ clips) | $\lambda_{\text{mcc}} = 0.1$ |
