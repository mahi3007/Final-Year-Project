# Research Protocol Freeze (Stage 0)

**Project Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition  
**Extended Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR: Characterizing and Controlling Adaptation-Induced Performance Disparities  
**Protocol Version:** `v1.0.0-canonical`  
**Status:** FROZEN  

---

## 1. Core Problem & Scientific Hypotheses

Continual Test-Time Adaptation (CTTA) enables automatic speech recognition (ASR) models to update parameters unsupervised on incoming audio streams $B_t$. However, unsupervised adaptation objectives (e.g. entropy minimization, teacher-student pseudolabeling) optimized over the global stream may inadvertently cause **subgroup regression** (a degradation in accuracy for specific speaker groups) and **disparity amplification** (widening performance gaps between best- and worst-performing groups), even while global average WER appears to improve.

### 1.1 Primary Research Questions
- **RQ-S (Scientific Question):** How does continual test-time adaptation change group-level ASR performance and disparity after accounting for measurable acoustic/metadata confounders?
- **RQ-I (Intervention Question):** Can a risk-controlled update policy limit group regression and disparity growth while retaining useful adaptation gain?
- **RQ1 (Confounder Impact):** How much raw group disparity remains after controlling for measurable acoustic factors such as SNR, speech rate, and recording device?
- **RQ2 (Sentinel Predictiveness):** Can a small, frozen, labeled sentinel panel predict whether an unlabeled adaptation update will be harmful or beneficial on unseen future data?
- **RQ3 (Trade-off Space):** What is the multi-dimensional Pareto trade-off between adaptation gain ($\Delta_R$), maximum group regression ($\max_g \Delta_g$), disparity growth ($\Delta_D$), controller acceptance rate, and compute cost?

---

## 2. Terminology & Label Invariant

> **CRITICAL RULE:** The system and research paper must use the group label actually provided and validated by the dataset metadata.
> - If the dataset provides `state`, `district`, `native_region`, or geographical tags without validated phonological/dialectal annotations, all analyses must be designated as **regional disparity** or **native-region disparity**.
> - The codebase must **NEVER** infer or assign accent labels from geographic tags (e.g., mapping `Telangana` $\to$ `Telugu-English`) unless that exact mapping is documented and validated within the dataset release.

---

## 3. Mathematical Metric Definitions

### 3.1 Word Error Rate (WER) and Character Error Rate (CER)
For reference word sequence $R$ and hypothesis sequence $H$:
$$\text{WER} = \frac{S + D + I}{N}$$
where $S$ is substitutions, $D$ is deletions, $I$ is insertions, and $N = |R|$ is the count of reference words.
- **Corpus WER:** Total pooled $(S_{\text{tot}} + D_{\text{tot}} + I_{\text{tot}}) / N_{\text{tot}}$.
- **Speaker-Macro WER:** Mean of individual speaker WERs: $\frac{1}{|U_{\text{spk}}|} \sum_{s \in U_{\text{spk}}} \text{WER}_s$.
- **Group WER ($WER_g$):** Word error rate restricted to utterances from group $g$.

### 3.2 Adaptation Changes and Disparities
Let $\theta$ be the current live model and $\theta'$ be the candidate adapted model:
- **Group-level change:** $\Delta_g = \text{WER}_g(\theta') - \text{WER}_g(\theta)$
  - $\Delta_g < 0 \implies$ group $g$ improves
  - $\Delta_g > 0 \implies$ group $g$ regresses
- **Overall change:** $\Delta_R = \text{WER}_{\text{overall}}(\theta') - \text{WER}_{\text{overall}}(\theta)$
- **Group Disparity:** $D = \max_g \text{WER}_g - \min_g \text{WER}_g$
- **Disparity Change:** $\Delta_D = D(\theta') - D(\theta)$

### 3.3 Safety Gate Constraints (DSG-CTTA)
A candidate update $\theta'$ evaluated on the frozen sentinel panel is accepted if and only if all three Upper Confidence Bounds (UCB) satisfy their pre-registered tolerance bounds:
$$\text{UCB}(\Delta_R) \le \epsilon_R$$
$$\text{UCB}(\max_g \Delta_g) \le \epsilon_G$$
$$\text{UCB}(\Delta_D) \le \epsilon_D$$

Confidence bounds are computed using **paired speaker-cluster bootstrap** across sentinel panel recordings.

---

## 4. Partitioning & Leakage Invariants

The data pipeline divides the dataset into **five strictly speaker-disjoint partitions**:

```
                          FULL DATASET
                               │
            ┌──────────────────┼──────────────────┐
            ↓                  ↓                  ↓
       Development        Calibration         Final Test
            │                  │
            └─────────→ Sentinel Panel
            
                      + External Validation
```

1. **Development:** Implementation, pipeline validation, baseline development.
2. **Calibration:** Selecting controller parameters (tolerances $\epsilon_R, \epsilon_G, \epsilon_D$, window size $K$, sentinel panel configuration).
3. **Sentinel Panel:** Frozen, balanced, labeled subset used strictly for candidate checkpoint safety evaluation.
4. **Final Test Stream:** Untouched, single-pass prequential evaluation. Never used for hyperparameter tuning.
5. **External Validation:** Separate dataset from an independent source/corpus for cross-dataset generalization.

### Invariants:
- $\text{Speakers}(A) \cap \text{Speakers}(B) = \emptyset$ for all distinct partitions $A, B$.
- Sentinel speakers must never appear in adaptation streams.
- Online adaptation code has zero access to reference transcripts or offline evaluation routines.

---

## 5. Prequential Evaluation Protocol

At each time-step $t$ for incoming window $B_t$:
1. **Predict:** Generate transcripts for $B_t$ using the current live model $\theta_t$.
2. **Record:** Log prequential predictions and acoustic metadata.
3. **Isolate:** Ground-truth labels for $B_t$ are strictly hidden from the online process.
4. **Adapt:** Compute unsupervised adaptation updates on unlabeled audio of $B_t$, producing candidate $\theta'$.
5. **Evaluate Sentinel:** Evaluate $\theta'$ against $\theta_t$ on the frozen sentinel panel.
6. **Safety Gate Decision:**
   - **ACCEPT:** $\theta_{t+1} = \theta'$
   - **REJECT / ROLLBACK:** $\theta_{t+1} = \theta_t$ (candidate discarded, model state rolled back).
7. **Offline Evaluation:** Only after the entire stream completes are prequential predictions compared against ground truth.

---

## 6. Confound Analysis: Count-based GLMM

Primary statistical analysis of ASR error counts $E_{ij} = S_{ij} + D_{ij} + I_{ij}$ is conducted via Generalized Linear Mixed Models (GLMM):
$$\log(\lambda_{ij}) = \beta_0 + \beta_{\text{group}} + \beta_{\text{SNR}} + \beta_{\text{speech\_rate}} + \beta_{\text{device}} + u_{\text{speaker}} + \log(N_{ij})$$
where:
- Model family: Poisson (with dispersion check) or Negative Binomial if overdispersed ($\alpha > 0$).
- Offset: $\log(N_{ij})$ where $N_{ij}$ is the reference word count.
- $u_{\text{speaker}} \sim \mathcal{N}(0, \sigma^2_u)$ is the speaker random intercept.
- Reports Rate Ratios ($\text{RR} = e^\beta$) with 95% confidence intervals and Holm-Bonferroni adjusted multiple comparisons.
