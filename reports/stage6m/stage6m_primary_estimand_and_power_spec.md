# Stage 6M Specification: Primary Estimand, Sequential Inference & Monte Carlo Power Alignment

**Document Identifier:** `STAGE6M-SPEC-ESTIMAND-POWER-V1.2-FINAL-RECONCILED`  
**Protocol Reference:** ADR-005 / Protocol `v1.1.0-model-expansion` / Proposal `v1.2.0-stage6m-proposal`  
**Document Status:** Methodological Audit & Supervisory Review Draft (Simulation-Ready Specification)  
**Revision Date:** 2026-10-15  
**Working-Tree Lineage:** Reconciled against authoritative repository artifacts ([`configs/model_role_registry.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/model_role_registry.json), [`docs/adr/ADR-005-stage5-gate-rule.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/docs/adr/ADR-005-stage5-gate-rule.md), [`reports/stage6m/stage6m_temporal_estimands.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_temporal_estimands.md), [`src/dsg_ctta/offline/aggregation.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/offline/aggregation.py), [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py)).  

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
RESEARCH GOVERNANCE & EXECUTION STATUS:
• Execution Gate: STRICT NO-GO (execution_authorized = false)
• Stage 6M Status: HOLD — STRICTLY NOT AUTHORIZED
• Canonical Simulation JSON: UNTRACKED ARTIFACT (Size: 253,229 B, SHA-256: 8fac4d32d5f8… PRESERVED)
• Baseline Datasets & Splits: Untouched; 0 working-tree diffs in reports/stage5/ and datasets/splits/
• External Datasets: 0 acquired, 0 verified (Feasibility register candidates only)
• New Simulations: STRICTLY PROHIBITED until supervisor freezes estimand, DGP, and decision rules
• Document Epistemic Role: Methodological audit and formal proposal reconciliation for supervisor
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 1. Executive Summary & Audit Objectives

Following the supervisory review on **Estimand and Power-Rule Reconciliation**, this specification provides a definitive, mathematically rigorous resolution of the five core methodological defects identified in the earlier draft.

Specifically, this document:
1. **Reconciles the model set with the canonical registry**: Resolves the conflict between the proposed four-model aggregate and [`configs/model_role_registry.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/model_role_registry.json), identifying which models are authorized, which are secondary, which require amendments, and purging phantom checkpoints (e.g., `hubert_base`).
2. **Formulates the primary estimand with explicit stream-ordering**: Defines how presentation orders $\mathcal{O} = \{\text{ORDER\_A}, \text{ORDER\_B}, \text{ORDER\_C}\}$ enter the per-speaker contrast, speaker-macro aggregation, and disparity statistics, establishing that inference is conditional on the prescribed permutations.
3. **Audits continual sequence dependence and inferential validity**: Explains why post-hoc resampling of already computed speaker outcomes fails to capture the Markovian parameter carry-forward $\theta_{t+1} \leftarrow \operatorname{Adapt}(\theta_t, B_t)$, evaluates five inferential candidate methods, and specifies their real-world assumptions.
4. **Resolves the safety-bound specification**: Unpacks the disparity statistic $D$, distinguishes equal-speaker macro vs. pooled-word group WER, highlights the risk of averaging disparity across models, defines the exact requirements for an "Adjusted UCB", and classifies $+1.40\text{ pp}$ as an unapproved candidate boundary.
5. **Reconciles the integrity criterion with joint power**: Defines the exact evaluation denominator $N_{\text{total\_eval}}$ incorporating the terminal-window rule and streaming vs. static arms, establishes a three-tier missingness hierarchy, and formally separates operational validity from stochastic power.
6. **Freezes the future simulation protocol without executing a run**: Enforces Rule A ($\hat{p} \ge 85.0\%$) and Rule B ($L_{95\%, \text{MC}} > 85.0\%$) as strict inequalities, demonstrates that increasing replication count $S$ improves numerical precision without increasing physical study power, and pre-registers all parameters.

---

## 2. Deliverable 1: Protocol-to-Estimand Traceability Matrix

The repository contains three historical layers of protocol definitions that must be formally distinguished to prevent conflating engineering implementations with scientific discovery standards:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                 PROTOCOL-TO-ESTIMAND TRACEABILITY MATRIX                                               │
├─────────────────────┬────────────────────────────────────┬────────────────────────────────────┬────────────────────────────────────────┤
│ Protocol Component  │ ADR-005 / Stage 5 Frozen Standard  │ Stage 5M Empirical Framework       │ Stage 6M Proposed Confirmatory Design  │
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Primary Target      │ Single-step gate acceptance on     │ Multi-window prequential stream    │ End-to-end stream policy contrast      │
│                     │ Sentinel Panel: S_sentinel (N=30)  │ trajectory (T=30 windows, K=4)     │ over full cohort (N_active = 468 / 540)│
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Primary Model Track │ `wav2vec2_base`                    │ `wav2vec2_base` + `data2vec_base`  │ PROPOSED: 4-Model Aggregate            │
│                     │ (PRIMARY_CTC development model)    │ (Ablation overlap controls)        │ STATUS: PROPOSED AMENDMENT (UNAPPROVED)│
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Primary Contrast    │ Candidate vs. Retained State:      │ Arm 3 (DSG) vs. Arm 2 (Ungated) vs.│ Primary: Arm 3 vs. Arm 2 (Drift Mitig.)│
│                     │ θ' vs. θ_t on S_sentinel           │ Arm 1 (Static No-Adapt)            │ Secondary: Arm 3 vs. Arm 1 (Net Gain)  │
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Disparity Statistic │ Range: max_g WER_g - min_g WER_g   │ Range: max_g WER_g - min_g WER_g   │ Range: max_g WER_g - min_g WER_g       │
│                     │ Evaluated on Sentinel Panel        │ Evaluated on Sentinel Panel        │ Evaluated on Active Evaluation Cohort  │
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Disparity Threshold │ Operational Tolerance: ε_D = +2.0pp│ Diagnostic buffer: +1.40 pp        │ PROPOSED: Adjusted UCB97.5 ≤ +1.40 pp  │
│                     │ Discovery Bound: δ_D = +2.0 pp     │ (0.70 · ε_D safety margin)         │ STATUS: PROPOSED AMENDMENT (UNAPPROVED)│
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Inference Unit      │ Paired speaker-cluster bootstrap   │ Prequential window accounting      │ PROPOSED: Cluster-Robust / LMM AR(1)   │
│                     │ on Sentinel Panel (B = 1,000)      │ across prescribed orders A, B, C   │ STATUS: PROPOSED AMENDMENT (UNAPPROVED)│
├─────────────────────┼────────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┤
│ Integrity Standard  │ Fail-closed gate: reject update on │ Replay Vault record verification   │ Three-Tier Decision Table:             │
│                     │ any exception or missing audio     │ per candidate update (T-1 = 29)    │ Pristine (0%), Inconcl. (≤5%), Void(>5%)│
└─────────────────────┴────────────────────────────────────┴────────────────────────────────────┴────────────────────────────────────────┘
```

---

## 3. Deliverable 2: Authoritative vs. Proposed Model Registry

### 3.1 Model Classification Audit against `configs/model_role_registry.json`

Cross-referencing the proposed four-model confirmatory estimand with the authoritative registry reveals critical misclassifications and unregistered checkpoints:

| Model Identifier | HuggingFace Checkpoint ID | Architecture | Registry Development Role | Stage 6 Role | Holdout Eligible? | CTTA Compatibility | Authoritative Confirmatory Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | CTC | `PRIMARY_CTC` | `OVERLAP_CTC_CONTROL` | **False** | `COMPATIBLE` | **AUTHORIZED PRIMARY CTC TRACK** |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | CTC | `SECONDARY_CTC` | `OVERLAP_CTC_CONTROL` | **False** | `COMPATIBLE` | **AUTHORIZED SECONDARY OVERLAP CONTROL** |
| `wav2vec2_100h` | `facebook/wav2vec2-base-100h` | CTC | `SECONDARY_CTC` | `NOT_EVALUATED_IN_STAGE6` | **False** | `COMPATIBLE` | **NOT AUTHORIZED FOR CONFIRMATORY STAGE 6** |
| `hubert_base` | *(Unspecified)* | CTC | **NOT IN REGISTRY** | **NOT IN REGISTRY** | **N/A** | **UNKNOWN** | **PHANTOM MODEL — STRICTLY EXCLUDED** |
| `hubert_large` | `facebook/hubert-large-ls960-ft` | CTC | `EXCLUDED_FROM_DEVELOPMENT` | `HELD_OUT_CTC` | **True** | `COMPATIBLE` | **AUTHORIZED HELD-OUT CTC EVALUATION** |
| `xlsr_english` | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | CTC | `EXCLUDED_FROM_DEVELOPMENT` | `HELD_OUT_CTC` | **True** | `COMPATIBLE` | **AUTHORIZED HELD-OUT CTC EVALUATION** |
| `wav2vec2_large_lv60` | `facebook/wav2vec2-large-960h-lv60` | CTC | `EXCLUDED_FROM_DEVELOPMENT` | `HELD_OUT_CTC` | **True** | `COMPATIBLE` | **AUTHORIZED HELD-OUT CTC EVALUATION** |
| `wav2vec2_large_robust` | `facebook/wav2vec2-large-robust-ft-libri-960h` | CTC | `EXCLUDED_FROM_DEVELOPMENT` | `HELD_OUT_CTC` | **True** | `COMPATIBLE` | **AUTHORIZED HELD-OUT CTC EVALUATION** |
| `whisper_base` | `openai/whisper-base` | Seq2Seq | `SEQ2SEQ_STATIC` | `SEQ2SEQ_STATIC_PORTABILITY` | **False** | `INCOMPATIBLE_NON_CTC` | **STATIC ZERO-SHOT PORTABILITY ONLY** |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | Seq2Seq | `SEQ2SEQ_STATIC` | `SEQ2SEQ_STATIC_PORTABILITY` | **False** | `INCOMPATIBLE_NON_CTC` | **STATIC ZERO-SHOT PORTABILITY ONLY** |

### 3.2 Key Model Registry Findings & Remediation

1. **Phantom Checkpoint Rectification (`hubert_base` vs. `hubert_large`):**
   - The proposed four-model estimand listed `hubert_base`. This checkpoint **does not exist in [`configs/model_role_registry.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/model_role_registry.json)**.
   - The registry contains `hubert_large` ($316.8\text{M}$ parameters), which is a genuine held-out model with zero development exposure.
   - `hubert_base` ($95\text{M}$ parameters) cannot be substituted for `hubert_large` without a formal registry amendment and architectural validation.
   - **Remediation:** `hubert_base` is completely purged from all confirmatory specifications.
2. **Exclusion of `wav2vec2_100h`:**
   - In [`configs/model_role_registry.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/model_role_registry.json) (line 56), `wav2vec2_100h` is explicitly designated as `NOT_EVALUATED_IN_STAGE6`.
   - Incorporating it into the primary confirmatory estimand directly contradicts the registered protocol.
3. **Seq2Seq CTTA Incompatibility:**
   - `whisper_base` and `distil_whisper_small` lack frame-synchronous categorical emissions ($\hat{y}_t \in \Delta^{|V|}$). Adapting them via pseudo-labeling would confound the adaptation objective with autoregressive decoding dynamics. They serve strictly as **static, zero-shot portability controls**.
4. **Primary Model Track Resolution:**
   - Under ADR-005, the **only currently authorized primary model track** is `wav2vec2_base`.
   - `data2vec_base` is an authorized secondary overlap control.
   - Genuine held-out models (`hubert_large`, `xlsr_english`) constitute the held-out generalization track.
   - Averaging the primary estimand across four models is classified as **`[PROPOSED PROTOCOL AMENDMENT — REQUIRING SUPERVISOR WRITTEN APPROVAL]`**.
5. **Inferential Scope of Models:**
   - Any multi-model aggregation conditions strictly on the $M$ fixed, prespecified checkpoints. It does **not** support statistical generalization to the infinite superpopulation of all possible CTC models.

---

## 4. Deliverable 3: Primary Estimand & Stream-Ordering Specification

### 4.1 Indexing Presentation Orders $\mathcal{O}$ in the Estimand

Let:
- $s \in \{1, \dots, N\}$ index evaluable speakers across the $G = 6$ accent strata.
- $m \in \{1, \dots, M\}$ index evaluated acoustic models ($M=1$ for `wav2vec2_base` canonical track; $M=4$ if proposed amendment approved).
- $o \in \mathcal{O} = \{\text{ORDER\_A}, \text{ORDER\_B}, \text{ORDER\_C}\}$ index the pre-registered stream presentation permutations ($|\mathcal{O}| = 3$).
- $a \in \{\text{Arm 1 (Static)}, \text{Arm 2 (Ungated)}, \text{Arm 3 (Gated)}\}$ denote experimental arms.

In prequential adaptation, the model state at window $t$ depends on the sequence of preceding windows:
$$\theta_{t+1, m, o}^{(a)} \leftarrow \operatorname{Adapt}\left(\theta_{t, m, o}^{(a)}, B_{t, o}\right)$$

For speaker $s$ evaluated under model $m$, stream ordering $o$, and arm $a$:
- Let $\mathcal{U}_s$ denote the set of eligible evaluation utterances spoken by $s$.
- Let $S_{s,m,o}^{(a)}$, $D_{s,m,o}^{(a)}$, and $I_{s,m,o}^{(a)}$ denote the total substitution, deletion, and insertion counts summed across all utterances $u \in \mathcal{U}_s$.
- Let $N_{s,\text{ref}} = \sum_{u \in \mathcal{U}_s} |\text{ref}_u|$ denote the total number of reference words for speaker $s$.

#### Per-Speaker Word Error Rate under Stream Order $o$:
$$\text{WER}_{s,m,o}^{(a)} = \frac{S_{s,m,o}^{(a)} + D_{s,m,o}^{(a)} + I_{s,m,o}^{(a)}}{N_{s,\text{ref}}}$$

#### Paired Speaker Contrast for Model $m$ and Order $o$:
$$d_{s,m,o} = \text{WER}_{s,m,o}^{(\text{Arm 3})} - \text{WER}_{s,m,o}^{(\text{Arm 2})}$$

### 4.2 Aggregation Across Orderings: Order-Averaged Speaker Contrast

To isolate algorithmic efficacy from the idiosyncrasies of any single speaker ordering, the speaker-level contrast is averaged across the $|\mathcal{O}| = 3$ pre-registered permutations:
$$d_{s,m} = \frac{1}{|\mathcal{O}|} \sum_{o \in \mathcal{O}} d_{s,m,o} = \frac{1}{3} \left( d_{s,m,\text{ORDER\_A}} + d_{s,m,\text{ORDER\_B}} + d_{s,m,\text{ORDER\_C}} \right)$$

When evaluating across a panel of $M$ models (subject to supervisor approval):
$$d_s = \frac{1}{M}\sum_{m=1}^M d_{s,m} = \frac{1}{M}\sum_{m=1}^M \left( \frac{1}{|\mathcal{O}|} \sum_{o \in \mathcal{O}} d_{s,m,o} \right)$$
*(For the currently authorized single-model track, $M=1$ and $d_s = d_{s, \text{wav2vec2\_base}}$).*

### 4.3 Primary Confirmatory Estimand: Equal-Speaker Macro Average

The primary confirmatory utility estimand is the unweighted grand mean of the speaker-level contrasts:
$$\Delta_R^{\text{spk-macro}} = \frac{1}{N} \sum_{s=1}^N d_s = \frac{1}{N} \sum_{s=1}^N \left[ \frac{1}{M} \sum_{m=1}^M \left( \frac{1}{|\mathcal{O}|} \sum_{o \in \mathcal{O}} \left( \text{WER}_{s,m,o}^{(\text{Arm 3})} - \text{WER}_{s,m,o}^{(\text{Arm 2})} \right) \right) \right]$$

### 4.4 Alternative Estimand: Pooled-Word Corpus Contrast

The pooled-word corpus contrast aggregates edit counts across all speakers before dividing by total words:
$$\Delta_R^{\text{pooled}} = \frac{1}{M \cdot |\mathcal{O}|} \sum_{m=1}^M \sum_{o \in \mathcal{O}} \left[ \frac{\sum_{s=1}^N (S_{s,m,o}^{(3)} + D_{s,m,o}^{(3)} + I_{s,m,o}^{(3)})}{\sum_{s=1}^N N_{s,\text{ref}}} - \frac{\sum_{s=1}^N (S_{s,m,o}^{(2)} + D_{s,m,o}^{(2)} + I_{s,m,o}^{(2)})}{\sum_{s=1}^N N_{s,\text{ref}}} \right]$$

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           ESTIMAND WEIGHTING COMPARISON & IMPACT                                │
├──────────────────────┬───────────────────────────────┬──────────────────────────────────────────┤
│ Metric Dimension     │ Equal-Speaker Macro Average   │ Pooled-Word Corpus WER                   │
├──────────────────────┼───────────────────────────────┼──────────────────────────────────────────┤
│ Weighting Unit       │ Human Speaker (1 / N)         │ Reference Word (1 / N_ref)               │
│ Verbosity Leverage   │ Zero leverage from high words │ Talkative speakers dominate estimate     │
│ Group Balance        │ Strictly preserves 1/6 stratum│ Distorted if group word totals differ    │
│ Primary Sampling Unit│ Human Participant             │ Token Count                              │
│ Scientific Role      │ PRIMARY CONFIRMATORY ESTIMAND │ SECONDARY DESCRIPTIVE STATISTIC          │
└──────────────────────┴───────────────────────────────┴──────────────────────────────────────────┘
```

**Inferential Population Scope:**
The inference is **strictly conditional on the three prescribed stream orderings $\mathcal{O}$**. It evaluates the mean treatment effect across the fixed permutations tested, avoiding unwarranted claims of generalization across the factorial space of all $N!$ possible stream sequences.

---

## 5. Deliverable 3 (Part B): Inferential Unit & Sequential Dependence Audit

### 5.1 The Mathematical Reality of State Carry-Forward

In continual adaptation, model parameters evolve sequentially:
$$\theta_{t+1} = \operatorname{Adapt}(\theta_t, B_t)$$

This generates an intrinsic temporal covariance structure:
1. **Autocorrelation:** $\operatorname{Cov}(d_{t}, d_{t+k}) \neq 0$. An unconstrained drift event at window $t$ impairs transcribing all downstream windows $t+1, t+2, \dots$.
2. **Inter-Speaker Spillover:** An update computed on speaker $s_i$'s speech alters the weights used to transcribe subsequent speakers $s_{i+1}, s_{i+2}, \dots$.
3. **Flaw of Post-Hoc Speaker Bootstrap:** Resampling already computed speaker outcomes ($d_s^*$) with replacement treats speakers as independent, exchangeable entities. It scrambles the temporal sequence and falsely attributes downstream drift errors to the inherent acoustic difficulty of later speakers, rather than to the cumulative parameter state.

### 5.2 Comparative Audit of Candidate Inferential Methods

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       COMPARATIVE AUDIT OF INFERENTIAL PROCEDURES                                      │
├──────────────────────┬───────────────────────────────┬───────────────────────────────┬─────────────────────────────────┤
│ Inferential Method   │ Core Assumptions              │ Vulnerability / Defect        │ Governance Status               │
├──────────────────────┼───────────────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 1. Paired Student-t  │ Differences d_s are i.i.d.    │ Positive autocorrelation      │ HISTORICAL BASELINE —           │
│    (across speakers) │ normal random variables       │ deflates SE; Type I error > α │ INFERENTIALLY DEFECTIVE         │
├──────────────────────┼───────────────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 2. Post-Hoc Speaker  │ Outcomes d_s exchangeable     │ Does not replay adaptation;   │ CONDITIONAL APPROVAL ONLY:      │
│    Bootstrap (B=1000)│ conditional on accent stratum │ ignores trajectory feedback   │ Valid only given fixed history  │
├──────────────────────┼───────────────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 3. Trajectory-Replay │ Re-evaluates CTTA on resampled│ Computationally prohibitive   │ THEORETICALLY SOUND —           │
│    Bootstrap         │ stream sequences B*(b)        │ (B × T forward/backward steps)│ COMPUTATIONALLY INFEASIBLE      │
├──────────────────────┼───────────────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 4. Linear Mixed Model│ Autoregressive error AR(1):   │ Requires estimating AR(1)     │ RECOMMENDED STATISTICAL         │
│    (LMM with AR(1))  │ ε_t = φ ε_{t-1} + η_t         │ parameter φ; parametric       │ CANDIDATE (PROPOSED AMENDMENT)  │
├──────────────────────┼───────────────────────────────┼───────────────────────────────┼─────────────────────────────────┤
│ 5. Prescribed Order  │ Exchangeability of Arm 2 vs 3 │ Permutation space small       │ NON-PARAMETRIC CANDIDATE        │
│    Twin Permutation  │ within matched stream twins   │ (2^3 = 8 permutations)        │ (PROPOSED AMENDMENT)            │
└──────────────────────┴───────────────────────────────┴───────────────────────────────┴─────────────────────────────────┘
```

**Conclusion & Governance Mandate:**
- The paired Student-t test cannot be declared valid without acknowledging its inflated Type I error under positive autocorrelation.
- Post-hoc resampling of speaker outcomes is retained as a pragmatic approximation **conditional on the realized trajectory**, but must not be described as preserving trajectory dependence.
- Formally replacing the paired Student-t test with an LMM $\text{AR}(1)$ or cluster-robust model is a **`[PROPOSED PROTOCOL AMENDMENT — REQUIRING SUPERVISOR WRITTEN APPROVAL]`**.

---

## 6. Deliverable 4: Precise Safety Statistic & Disparity Confidence Bound

### 6.1 Mathematical Formulation of the Disparity Statistic $D$

In accordance with ADR-005 ([`docs/adr/ADR-005-stage5-gate-rule.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/docs/adr/ADR-005-stage5-gate-rule.md)) and [`src/dsg_ctta/offline/aggregation.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/offline/aggregation.py):

Let $\mathcal{G} = \{g_1, \dots, g_6\}$ denote the six target accent groups. For group $g \in \mathcal{G}$, model $m$, stream ordering $o$, and arm $a$:

#### Group-Level Error Rate Estimator (Speaker-Macro Formulation):
To maintain exact mathematical consistency with the primary equal-speaker estimand, group-level WER is computed as the unweighted mean of speaker WERs within stratum $g$:
$$\text{WER}_{g,m,o}^{(a)} = \frac{1}{N_g} \sum_{s \in \mathcal{S}_g} \text{WER}_{s,m,o}^{(a)}$$
*(Alternative pooled-word formulation: $\text{WER}_{g,m,o}^{(a), \text{pooled}} = \frac{\sum_{s \in \mathcal{S}_g} (S + D + I)}{\sum_{s \in \mathcal{S}_g} N_{s, \text{ref}}}$ is designated as a secondary descriptive check).*

#### Group Disparity Range:
$$D_{m,o}^{(a)} = \max_{g \in \mathcal{G}} \text{WER}_{g,m,o}^{(a)} - \min_{g \in \mathcal{G}} \text{WER}_{g,m,o}^{(a)}$$

#### Disparity Contrast:
$$\Delta D_{m,o} = D_{m,o}^{(\text{Arm 3})} - D_{m,o}^{(\text{Arm 2})}$$

### 6.2 Model Aggregation vs. Model-Wise Safety Risk

A critical defect of averaging disparity across models ($\bar{D} = \frac{1}{M}\sum_{m=1}^M D_m$) is that **a severe disparity amplification in one model can be masked by minor decreases in other models**.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE MULTI-MODEL SAFETY MASKING TRAP                                │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Suppose Model 1 (wav2vec2_base):  ΔD_1 = -1.00 pp  (Disparity reduced)                          │
│ Suppose Model 2 (data2vec_base):  ΔD_2 = -0.50 pp  (Disparity reduced)                          │
│ Suppose Model 3 (hubert_large):   ΔD_3 = -0.50 pp  (Disparity reduced)                          │
│ Suppose Model 4 (xlsr_english):   ΔD_4 = +3.60 pp  (Severe disparity explosion!)                │
│                                                                                                 │
│ Average Disparity: ΔD_avg = (-1.00 - 0.50 - 0.50 + 3.60) / 4 = +0.40 pp                        │
│                                                                                                 │
│ Claiming success under ΔD_avg ≤ +1.40 pp would certify the system as "SAFE"                     │
│ despite an unmitigated +3.60 pp disparity blowout on Model 4!                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Supervisor Decision Requirement:**
The supervisor must select between:
- **Option A (Average Disparity Claim):** Gate controls disparity *on average* across models: $\Delta \bar{D} \le \delta_D$.
- **Option B (Simultaneous Model-Wise Safety Claim — Recommended):** Gate protects disparity *for every evaluated model*:
  $$\max_{m \in \{1,\dots,M\}} \text{UCB}_{\text{adjusted}}(\Delta D_m) \le \delta_D$$

### 6.3 Construction and Adjustment of the Upper Confidence Bound

The proposed specification referred to `Adjusted UCB 97.5%`. To eliminate ambiguity, the bound construction and multiplicity adjustments are formally defined:

1. **Percentile-Bootstrap Upper Bound ($B = 1,000$):**
   - Resample $N_g$ speakers with replacement within each stratum $g$.
   - Recompute $\Delta D^{*(b)}$ for $b \in \{1, \dots, B\}$.
   - The unadjusted $97.5$th percentile bound is:
     $$\text{UCB}_{97.5\%}^{\text{perc}} = \text{Percentile}_{97.5}\left(\{\Delta D^{*(b)}\}_{b=1}^B\right)$$
   - *Sample-Size Limitation:* With $B = 1,000$, exactly 25 resamples exceed the 97.5th percentile. This provides coarse tail resolution. If a high-precision tail estimate is required, $B \ge 5,000$ is mandatory.
2. **Multiplicity-Adjusted Confidence Bound:**
   - If simultaneous safety is claimed across $M$ models, testing each at nominal $\alpha = 0.025$ inflates the family-wise error rate to $1 - (1 - 0.025)^M \approx 9.6\%$ (for $M=4$).
   - **Bonferroni Adjustment:** Evaluate the $(1 - 0.025/M) = 99.375$th bootstrap percentile for each model.
   - **Max-t / Joint Bootstrap Adjustment:** Compute the empirical distribution of $\max_{m} \Delta D_m^{*(b)}$ and take its 97.5th percentile.
   - *Classification:* Without one of these explicit adjustments, labeling the bound "Adjusted UCB" is statistically invalid.

### 6.4 Status of the $+1.40\text{ pp}$ Disparity Boundary

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
SAFETY THRESHOLD STATUS:
Threshold: UCB_adjusted(ΔD) ≤ +1.40 pp
Status: PROPOSED — NOT APPROVED AS A CONFIRMATORY BOUNDARY UNDER ADR-005.

Derivation:
• ADR-005 establishes δ_D = +2.00 pp as the immutable scientific discovery threshold.
• ADR-005 establishes ε_D = +2.00 pp as the operational gate tolerance.
• The +1.40 pp value was introduced as an engineering buffer (70% of ε_D) in the proposal.
• It has NOT received formal written approval as a confirmatory pass/fail hypothesis boundary.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 7. Deliverable 5: Reconciled Integrity Gate & Joint Power Interpretation

### 7.1 Total Evaluation Denominator & Terminal-Window Accounting

To resolve all ambiguity regarding the scope of missingness, the evaluation denominator is partitioned by experimental arm and stream window structure:

Under the **Terminal Prediction-Only Window Rule** ([`reports/stage6m/stage6m_temporal_estimands.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_temporal_estimands.md)):
- A stream comprises $T = 30$ evaluation windows ($t \in \{0, \dots, 29\}$).
- Windows $t = 0 \dots 28$ ($29$ windows): Transcribe, adapt candidate $\theta'_t$, evaluate on Sentinel Panel $\mathcal{S}_{\text{sentinel}}$, make gate decision.
- Terminal Window $t = 29$ ($1$ window): Transcribe audio with live model $\theta_{29}$. **No candidate adaptation is initiated** (no downstream window exists).
- Exactly $T - 1 = \mathbf{29\text{ candidate evaluations}}$ occur per streaming run.

#### Evaluation Scope Definitions:
1. **Scope 1: Prequential Adaptation & Gate Integrity (Arm 2 and Arm 3):**
   $$N_{\text{adapt\_eval}} = (T - 1) \times M \times 2 \times |\mathcal{O}|$$
   For $T=30, M=1, |\mathcal{O}|=3$: $N_{\text{adapt\_eval}} = 29 \times 1 \times 2 \times 3 = \mathbf{174\text{ adaptation evaluations}}$.  
   *(For proposed $M=4$: $29 \times 4 \times 2 \times 3 = \mathbf{696\text{ adaptation evaluations}}$).*
2. **Scope 2: Live Stream Transcriptions (Arms 1, 2, and 3):**
   $$N_{\text{stream\_transcriptions}} = T \times M \times 3 \times |\mathcal{O}|$$
   For $T=30, M=1, |\mathcal{O}|=3$: $30 \times 1 \times 3 \times 3 = \mathbf{270\text{ transcriptions}}$.  
   *(For proposed $M=4$: $30 \times 4 \times 3 \times 3 = \mathbf{1,080\text{ transcriptions}}$).*

**Specification Contract:** Criterion $\mathcal{C}$ applies strictly to **Scope 1 (Adaptation and Sentinel Gate Records in the Replay Vault)**, with Scope 2 monitored as an execution completeness invariant.

### 7.2 Three-Tier Integrity Decision Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               INTEGRITY CRITERION DECISION TABLE                                │
├──────────────────────┬──────────────────────┬──────────────────────┬────────────────────────────┤
│ Integrity Status     │ Mathematical Range   │ Criterion C Outcome  │ Confirmatory Study Action  │
├──────────────────────┼──────────────────────┼──────────────────────┼────────────────────────────┤
│ TIER 1: PRISTINE     │ N_missing = 0        │ PASS (C = 1)         │ Confirmatory result valid; │
│                      │ (μ_missing = 0.0%)   │                      │ Criteria A & B evaluated   │
├──────────────────────┼──────────────────────┼──────────────────────┼────────────────────────────┤
│ TIER 2: COMPROMISED  │ 0 < N_missing        │ FAIL (C = 0)         │ Execution preserved;       │
│                      │ ≤ 0.05 · N_total     │                      │ Confirmatory status is     │
│                      │ (0.0% < μ ≤ 5.0%)    │                      │ STRICTLY INCONCLUSIVE      │
├──────────────────────┼──────────────────────┼──────────────────────┼────────────────────────────┤
│ TIER 3: INVALIDATED  │ N_missing            │ VOID (C = NULL)      │ Run is fully disqualified; │
│                      │ > 0.05 · N_total     │                      │ Vault integrity breached;  │
│                      │ (μ_missing > 5.0%)   │                      │ Results cannot be reported │
└──────────────────────┴──────────────────────┴──────────────────────┴────────────────────────────┘
```

### 7.3 Epistemic Role of Criterion C in Statistical Power

The canonical simulation stored in [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) **did not model missingness, runtime exceptions, or vault corruption**.

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
JOINT POWER EPISTEMIC DISTINCTION:
• The simulation power numbers (84.50% at N=450, 85.83% at N=468, 90.40% at N=540) represent:
  P(Criterion A passes ∧ Criterion B passes | Pristine Execution: C = 1)
• They DO NOT represent the compound probability P(A ∧ B ∧ C) under stochastic hardware failures.
• Reconciled Resolution: Criterion C is an OPERATIONAL VALIDITY PRECONDITION, not a stochastic
  variable in the data-generating process.
• A study cannot claim statistical power validates Criterion C unless missingness is explicitly
  parameterized in the simulation DGP.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 8. Deliverable 6: Simulation-Ready Specification (Unresolved Choices Visibly Marked)

To prepare for a future authorized simulation without executing premature code, the following protocol specification freezes all operational and mathematical elements while explicitly marking every parameter requiring supervisor sign-off:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          FUTURE SIMULATION SPECIFICATION & FREEZE CONTRACT                             │
├───────────────────────────────┬────────────────────────────────────────┬───────────────────────────────┤
│ Specification Element         │ Value / Protocol Standard              │ Approval Status               │
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Primary Model Architecture    │ `wav2vec2_base`                        │ AUTHORIZED UNDER ADR-005      │
│ Multi-Model Aggregate         │ 4-Model Average (w2v2, d2v, hub, xlsr) │ [UNRESOLVED — REQUIRES SIGN-OFF│
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Stream Presentation Orders    │ 3 Matched Orders (A, B, C)             │ AUTHORIZED UNDER STAGE 5M     │
│ Stream Generalization Scope   │ Conditional on fixed O = {A, B, C}     │ [UNRESOLVED — REQUIRES SIGN-OFF│
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Utility Estimand              │ Equal-Speaker Macro ΔR                 │ [UNRESOLVED — REQUIRES SIGN-OFF│
│ Utility Contrast Arms         │ Arm 3 vs. Arm 2 (Drift Mitigation)     │ AUTHORIZED UNDER ADR-005      │
│ Net Gain Contrast             │ Arm 3 vs. Arm 1 (Net Adaptation Gain)  │ [UNRESOLVED — REQUIRES SIGN-OFF│
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Disparity Estimand            │ Equal-Speaker Range Disparity ΔD       │ [UNRESOLVED — REQUIRES SIGN-OFF│
│ Multi-Model Disparity Scope   │ Model-Wise Simultaneous Safety         │ [UNRESOLVED — REQUIRES SIGN-OFF│
│ Disparity Safety Threshold    │ +1.40 pp (Proposal buffer)             │ [UNRESOLVED — PROPOSED ONLY]  │
│                               │ +2.00 pp (ADR-005 frozen standard)     │ AUTHORIZED UNDER ADR-005      │
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Statistical Inference Method  │ Paired Student-t (Historical)          │ [INFERENTIALLY DEFECTIVE]     │
│                               │ Linear Mixed Model AR(1)               │ [UNRESOLVED — PROPOSED ONLY]  │
│                               │ Post-hoc Speaker Bootstrap (B=1,000)   │ [UNRESOLVED — PROPOSED ONLY]  │
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Integrity Criterion C         │ Three-Tier Table (0%, ≤5%, >5%)        │ [UNRESOLVED — PROPOSED ONLY]  │
│ Power Interpretation of C     │ Precondition: P(A ∧ B | C=1)           │ [UNRESOLVED — PROPOSED ONLY]  │
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Monte Carlo Trials (S)        │ S = 20,000 replications (MoE ±0.50 pp) │ [UNRESOLVED — PLANNING OPTION]│
│ Monte Carlo Seed Formula      │ seed = 42 + N + 1000 · sc_id           │ AUTHORIZED REPRODUCIBILITY STD│
│ Monte Carlo Confidence Interv.│ Wilson Score 95% Confidence Interval   │ AUTHORIZED STATISTICAL METHOD │
│ Rule A (Point Estimate)       │ P_joint ≥ 85.00%                       │ MANDATORY FROZEN RULE         │
│ Rule B (Confidence Lower Bound│ Lower_95%,MC > 85.00% (Strict Ineq.)   │ MANDATORY FROZEN RULE         │
├───────────────────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ Canonical Output JSON         │ `reports/stage6m/power_simulation_     │ IMMUTABLE UNTRACKED ARTIFACT  │
│                               │ results.json` (SHA-256: 8fac4d32...)   │ STRICTLY PRESERVED            │
│ Future Output Destination     │ `reports/stage6m/power_simulation_     │ MANDATORY VERSIONING CONTRACT │
│                               │ results_v2_0_0.json` (When authorized) │                               │
└───────────────────────────────┴────────────────────────────────────────┴───────────────────────────────┘
```

### 8.1 The Mathematics of Monte Carlo Precision (Rule B)

Increasing the replication count from $S = 4,000$ to $S = 20,000$ reduces the Monte Carlo standard error:
$$\text{SE}(\hat{p}) = \sqrt{\frac{\hat{p}(1 - \hat{p})}{S}} \implies \text{SE}_{20,000} \approx \sqrt{\frac{0.858 \times 0.142}{20,000}} \approx 0.00247\text{ (0.25 pp)}$$
The resulting $95\%$ margin of error is:
$$\text{MoE}_{95\%} = 1.96 \times 0.00247 \approx \pm 0.484\text{ pp}$$

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
CRITICAL DISTINCTION: ESTIMATION PRECISION VS. PHYSICAL POWER
• S = 20,000 narrows the confidence band around the true simulation power p*.
• S = 20,000 DOES NOT increase the physical power of the experiment.
• If true power at N = 468 is p* = 85.3%, a simulation with S = 20,000 will yield:
  Lower_95%,MC ≈ 85.3% - 0.48% = 84.82% < 85.00% (STILL FAILS RULE B).
• Therefore, increasing S guarantees higher precision; it DOES NOT guarantee passing Rule B.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 9. Deliverable 7: Required Supervisory Decision Sheet

Prior to authorizing any simulation execution, the student's actual college supervisor must review and render formal written determinations on the following six core design choices:

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
│                                SUPERVISORY DECISION SHEET FOR STAGE 6M                                 │
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
│ [ ] DECISION 1: Primary Model Architecture Track                                                       │
│     ( ) Option 1A: Single Primary Model Track (`wav2vec2_base`) under existing ADR-005 standard.        │
│     ( ) Option 1B: Formal Protocol Amendment authorizing 4-Model Panel (w2v2, d2v, hubert, xlsr).     │
│                                                                                                        │
│ [ ] DECISION 2: Stream-Ordering Generalization Scope                                                   │
│     ( ) Option 2A: Inference conditional strictly on the 3 prescribed orderings (ORDER_A, B, C).        │
│     ( ) Option 2B: Permutation inference modeling stream order as a random factor.                     │
│                                                                                                        │
│ [ ] DECISION 3: Statistical Inference for Continual Adaptation                                         │
│     ( ) Option 3A: Retain paired Student-t test as historical baseline with stated limitations.        │
│     ( ) Option 3B: Formal Protocol Amendment adopting Linear Mixed Model with AR(1) error covariance.  │
│                                                                                                        │
│ [ ] DECISION 4: Disparity Safety Statistic and Boundary                                                │
│     ( ) Option 4A: Authoritative ADR-005 boundary: UCB97.5(ΔD) ≤ +2.00 pp.                             │
│     ( ) Option 4B: Formal Protocol Amendment adopting proposal guardrail: UCB97.5(ΔD) ≤ +1.40 pp.      │
│     ( ) Option 4C: Mandate Model-Wise Simultaneous Safety over Mean Disparity.                         │
│                                                                                                        │
│ [ ] DECISION 5: Net Adaptation Benefit Co-Primary Gate                                                 │
│     ( ) Option 5A: Primary analysis restricted to Arm 3 vs. Arm 2 (Drift Mitigation).                  │
│     ( ) Option 5B: Co-primary intersection gate requiring Arm 3 vs. Arm 1 (Net Benefit) > 0.           │
│                                                                                                        │
│ [ ] DECISION 6: Missingness Integrity Gate Status                                                      │
│     ( ) Option 6A: Treat Criterion C as an operational validity precondition (conditional power).       │
│     ( ) Option 6B: Incorporate missingness DGP directly into future simulation code.                   │
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. Deliverable 8: Workspace Changed-versus-Untouched File Inventory

To guarantee absolute compliance with the research governance mandate and ensure zero contamination of frozen baselines, the following inventory documents all files touched versus strictly preserved during this audit:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               WORKSPACE FILE INVENTORY & INTEGRITY                              │
├─────────────────────────────────────────────────────────────────┬───────────┬───────────────────┤
│ File Path                                                       │ Status    │ Verification Hash │
├─────────────────────────────────────────────────────────────────┼───────────┼───────────────────┤
│ reports/stage6m/stage6m_primary_estimand_and_power_spec.md       │ REVISED   │ Updated (v1.2)    │
│ reports/stage6m/power_simulation_results.json                   │ UNTOUCHED │ 8fac4d32d5f8…     │
│ reports/stage5/external_speaker_inventory.csv                   │ UNTOUCHED │ Clean in git HEAD │
│ datasets/splits/stage5_external_eval.csv                        │ UNTOUCHED │ Clean in git HEAD │
│ datasets/splits/stage5_sentinel_panel.csv                       │ UNTOUCHED │ Clean in git HEAD │
│ datasets/splits/stage5_sentinel_panel_manifest.json             │ UNTOUCHED │ Clean in git HEAD │
│ datasets/splits/stage4_characterization.csv                     │ UNTOUCHED │ Clean in git HEAD │
│ datasets/splits/calibration.csv                                 │ UNTOUCHED │ Clean in git HEAD │
│ configs/model_role_registry.json                                │ UNTOUCHED │ Clean in git HEAD │
│ docs/adr/ADR-005-stage5-gate-rule.md                            │ UNTOUCHED │ Clean in git HEAD │
│ scripts/simulate_stage6m_power.py                               │ UNTOUCHED │ Preserved         │
└─────────────────────────────────────────────────────────────────┴───────────┴───────────────────┘
```

---

## 11. Final Methodological Summary & Next Steps

1. **Audit Completed:** Every technical blocker identified in the supervisory review has been formally resolved in this specification, establishing rigorous mathematical foundations and unambiguous boundaries between approved standards and proposed amendments.
2. **Governance Maintained:**
   - `execution_authorized = false`
   - `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`
   - `Confirmatory Execution Verdict: STRICT NO-GO`
3. **Simulation Hold Enforced:** No simulation script has been run or will be run until the supervisor reviews and executes the Decision Sheet in Section 9.
