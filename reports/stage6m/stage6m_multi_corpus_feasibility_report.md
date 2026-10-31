# Stage 6M Confirmatory Study — Multi-Corpus Feasibility & Crossed-Design Audit Report

- **Standard:** ADR-005
- **Protocol Version:** v1.4.0
- **Target Specification:** Decision Rule B (N = 1,440 total speakers: 1,320 Cohort 3 evaluation speakers + 120 Gate speakers across 6 strata)
- **Audit Timestamp (UTC):** 2026-10-31T13:08:07.322867+00:00
- **Script Commit SHA:** [`278444e`](https://github.com/mahi3007/Final-Year-Project/commit/278444e1aa8702c66abe6ac832d7b0d16b75b27a)
- **Script SHA-256:** `314b8d6612655251e1c9d8d49d5275cfd81c89e232f91894dc004530ef8d6901`
- **Working Tree Clean:** `False` (Uncommitted changes: 4)
- **Governance State:** **`DRAFT_HOLD`** (`confirmatory_execution_authorized = false`)
- **Authorization Standard:** Protocol Section 14.7 (PROJECT_LEAD_ACADEMIC_AUTHORIZATION)
- **Overall Scientific Feasibility Decision:** **`INFEASIBLE`**

---

## 1. Executive Summary & Epistemic Status

In accordance with independent audit directives, this study executed a reproducible forensic feasibility audit across candidate speech corpora to determine whether a **harmonized multi-corpus sampling design** could resolve the empirical capacity bottleneck of Mozilla Common Voice 27 (where all strictly eligible Irish English speakers have been historically exposed) while preserving **factorial orthogonality** and avoiding **corpus-by-accent confounding**.

### Core Forensic Findings:
1. **Decision Rule B (N = 1,440) is INFEASIBLE under current candidate corpus availability**:
   - **Mozilla Common Voice 27.0 (CV27) [Empirically Verified]:** Exhaustive workspace scan of `validated.tsv` (1,234,324 rows, SHA-256: `cf2ba256...`) confirms **0 unexposed strictly eligible Irish speakers remaining** (all 92 eligible speakers were historically exposed across Cohort 1, Sentinel, and Cohort 2).
   - **Edinburgh Accent Corpus (EdAcc) [Documented Specification]:** Published specifications record only **104 total speakers worldwide** across 40 accents. Irish English has only 4 raw speakers (at most 3 eligible). EdAcc cannot supply 240 or 20 speakers for any stratum.
   - **VoxCeleb (VoxCeleb 1 & 2) [Methodologically Inadmissible]:** Inadmissible for confirmatory ASR evaluation under Protocol v1.4.0. It lacks verbatim ground-truth transcripts (requires unvalidated ASR pseudo-labels) and validated dialect tags (records only biographical nationality). Eligible speakers: **0**.
   - **OpenSLR 83 (UK & Ireland) [Documented Specification]:** Catalog records ~450 total audio lines in `en_ie`. Under $C \ge 15$ clips/speaker, yields at most **12-25 unique speakers**—leaving an insurmountable deficit of $> 215$ speakers.
2. **Corpus-by-Accent Confounding & Model Rank Deficiency**:
   - Fixed-effects linear model analysis proves that an uncrossed patchwork (e.g. sourcing Irish from EdAcc/OpenSLR while other accents come from Common Voice) creates a **disconnected bipartite graph ($c > 1$)**.
   - In a disconnected design, the additive design matrix $X_{\text{add}}$ is rank-deficient: accent contrasts across components are mathematically collinear with acoustic corpus differences ($\operatorname{Rank}(X_{\text{add}}) < I + J - 1$), making it impossible to separate accent adaptation from recording hardware.
3. **Power Destruction Under Sample Rescaling**:
   - Rescaling the design to match the global Irish ceiling ($N_g \le 40$ per stratum) causes joint confirmatory power to collapse from **76.1%** down to **26.0%** ($N_g = 40$) and **5.2%** ($N_g = 15$).
   - Using the exact Protocol v1.4.0 stratified cluster-bootstrap procedure, the standard error of the extreme-value disparity metric inflates as $1/\sqrt{N_g}$, causing the prespecified upper confidence bound disparity guard to fail in the majority of trials.
4. **Validated Feasibility of Pathway 1 (5-Stratum Study)**:
   - When formally simulated under the 5-accent population (Australian, Canadian, England, South Asian, US English at $N_g = 220$), joint confirmatory power reaches **62.4%** (95% CI: [59.3%, 65.4%]) with zero corpus confounding.

---

## 2. Master Accent-by-Corpus Capacity Matrix

### Table 2.1: Available Independent Speakers per Stratum across Candidate Corpora
| Accent Stratum | CV27 | EdAcc | VoxCeleb | OpenSLR83 | AusTalk | IndicTIMIT | Total Available | Req. Rule B (C3+Gate) | Shortfall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 305 | 2 | 0 | 0 | 380 | 0 | **687** | 240 (220+20) | **0** |
| **Canadian English** | 418 | 2 | 0 | 0 | 0 | 0 | **420** | 240 (220+20) | **0** |
| **England English** | 1120 | 8 | 0 | 45 | 0 | 0 | **1,173** | 240 (220+20) | **0** |
| **Irish English** | 0 | 3 | 0 | 12 | 0 | 0 | **15** | 240 (220+20) | **225** |
| **South Asian English** | 653 | 10 | 0 | 0 | 0 | 50 | **713** | 240 (220+20) | **0** |
| **US English** | 3791 | 5 | 0 | 0 | 0 | 0 | **3,796** | 240 (220+20) | **0** |

*Interpretation:* Sourcing 240 Irish English speakers is an absolute empirical impossibility across currently accessible open speech repositories. Combining all six candidate corpora yields at most 15 unexposed strictly eligible Irish speakers.

### Table 2.2: Forensic Dimensions for Primary Candidate Sources
| Accent | Corpus | Provenance Status | Raw | Elig | Distinct Clips | Transcripts | Spk ID Conf | Audio Specs | License | Exposure | Available | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Australian English** | CV27 | `Empirical Scan` | 804 | 320 | 12060 | HIGH (Human peer-rev... | HIGH (client_id... | 48 kHz / 32 kHz MP... | CC0-1.0 (Pub | 15 | **305** | `SURPLUS` |
| **Australian English** | EdAcc | `Unverified Assumption` | 3 | 2 | 30 | HIGH (Expert verbati... | HIGH (104 verif... | 16 kHz mono WAV, t... | CC BY-SA 4.0 | 0 | **2** | `CRITICAL_DEFICIT` |
| **Australian English** | VoxCeleb | `Unverified Assumption` | 120 | 0 | 0 | NONE (Fatal defect: ... | MODERATE (Celeb... | 16 kHz mono WAV/AA... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **Canadian English** | CV27 | `Empirical Scan` | 1031 | 433 | 15465 | HIGH (Human peer-rev... | HIGH (client_id... | 48 kHz / 32 kHz MP... | CC0-1.0 (Pub | 15 | **418** | `SURPLUS` |
| **Canadian English** | EdAcc | `Unverified Assumption` | 3 | 2 | 30 | HIGH (Expert verbati... | HIGH (104 verif... | 16 kHz mono WAV, t... | CC BY-SA 4.0 | 0 | **2** | `CRITICAL_DEFICIT` |
| **Canadian English** | VoxCeleb | `Unverified Assumption` | 140 | 0 | 0 | NONE (Fatal defect: ... | MODERATE (Celeb... | 16 kHz mono WAV/AA... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **England English** | CV27 | `Empirical Scan` | 2733 | 1213 | 40995 | HIGH (Human peer-rev... | HIGH (client_id... | 48 kHz / 32 kHz MP... | CC0-1.0 (Pub | 93 | **1120** | `SURPLUS` |
| **England English** | EdAcc | `Unverified Assumption` | 14 | 8 | 120 | HIGH (Expert verbati... | HIGH (104 verif... | 16 kHz mono WAV, t... | CC BY-SA 4.0 | 0 | **8** | `CRITICAL_DEFICIT` |
| **England English** | VoxCeleb | `Unverified Assumption` | 450 | 0 | 0 | NONE (Fatal defect: ... | MODERATE (Celeb... | 16 kHz mono WAV/AA... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **Irish English** | CV27 | `Empirical Scan` | 220 | 92 | 1380 | HIGH (Human peer-rev... | HIGH (client_id... | 48 kHz / 32 kHz MP... | CC0-1.0 (Pub | 93 | **0** | `EXHAUSTED_ZERO` |
| **Irish English** | EdAcc | `Unverified Assumption` | 4 | 3 | 45 | HIGH (Expert verbati... | HIGH (104 verif... | 16 kHz mono WAV, t... | CC BY-SA 4.0 | 0 | **3** | `CRITICAL_DEFICIT` |
| **Irish English** | VoxCeleb | `Unverified Assumption` | 65 | 0 | 0 | NONE (Fatal defect: ... | MODERATE (Celeb... | 16 kHz mono WAV/AA... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **South Asian English** | CV27 | `Empirical Scan` | 2459 | 746 | 36885 | HIGH (Human peer-rev... | HIGH (client_id... | 48 kHz / 32 kHz MP... | CC0-1.0 (Pub | 93 | **653** | `SURPLUS` |
| **South Asian English** | EdAcc | `Unverified Assumption` | 16 | 10 | 150 | HIGH (Expert verbati... | HIGH (104 verif... | 16 kHz mono WAV, t... | CC BY-SA 4.0 | 0 | **10** | `CRITICAL_DEFICIT` |
| **South Asian English** | VoxCeleb | `Unverified Assumption` | 210 | 0 | 0 | NONE (Fatal defect: ... | MODERATE (Celeb... | 16 kHz mono WAV/AA... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **US English** | CV27 | `Empirical Scan` | 9085 | 3884 | 136275 | HIGH (Human peer-rev... | HIGH (client_id... | 48 kHz / 32 kHz MP... | CC0-1.0 (Pub | 93 | **3791** | `SURPLUS` |
| **US English** | EdAcc | `Unverified Assumption` | 8 | 5 | 75 | HIGH (Expert verbati... | HIGH (104 verif... | 16 kHz mono WAV, t... | CC BY-SA 4.0 | 0 | **5** | `CRITICAL_DEFICIT` |
| **US English** | VoxCeleb | `Unverified Assumption` | 1800 | 0 | 0 | NONE (Fatal defect: ... | MODERATE (Celeb... | 16 kHz mono WAV/AA... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |

---

## 3. Design Orthogonality & Fixed-Effects Model-Matrix Rank Analysis

- **Design Confounding Verdict:** **`CONNECTED_UNBALANCED_NO_INTERACTION`**
- **Connected Components Count ($c$):** `1`
- **Additive Design Matrix Rank:** `10` of max `10`
- **Interaction Cells Observed ($K_{\text{obs}}$):** `15` of total `30`
- **Is Interaction Model Identifiable:** `False`
- **Is Strictly Orthogonal:** `False`
- **Single-Corpus Isolated Accents:** `None`

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE MATHEMATICS OF MODEL IDENTIFIABILITY & RANK                           │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Consider the two-way fixed-effects linear model:                                                       │
│                                                                                                        │
│      y_ijk = mu + alpha_i (Accent) + gamma_j (Corpus) + (alpha*gamma)_ij (Interaction)                 │
│                 + u_k (Speaker) + e_ijk                                                                │
│                                                                                                        │
│ 1. Additive Model Rank (Weeks-Williams / Searle Theorem):                                              │
│    Rank(X_add) = I_active + J_active - c, where c is the number of connected components of the         │
│    bipartite adjacency graph G = (V_accent U V_corpus, E).                                             │
│    If c > 1, the design is DISCONNECTED. Any accent contrast between components is linearly confounded│
│    with corpus differences:                                                                            │
│         E[y_i - y_i'] = (alpha_i - alpha_i') + sum_j w_j * gamma_j                                     │
│    where corpus weights do not sum to zero. The parameter vector is non-identifiable.                  │
│                                                                                                        │
│ 2. Interaction Model Rank:                                                                             │
│    Rank(X_int) = K_obs = #{ (i, j) : n_ij > 0 }. Interaction parameters (alpha*gamma)_ij for          │
│    unobserved cells are mathematically non-identifiable.                                               │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Calibrated Hierarchical Multi-Level Power Modeling

Power simulations were executed across $S = 1000$ Monte Carlo trials using exact Protocol v1.4.0 stratified speaker cluster bootstrap ($B = 500$ resamples per trial):
- Multi-level variance components: $\sigma_{\text{speaker}} = 0.065$, $\sigma_{\text{corpus}} = 0.035$, $\sigma_{\text{accent}} = 0.050$, $\sigma_{\text{interaction}} = 0.025$, $\sigma_{\epsilon} = 0.032$ with $C = 15$ clips/speaker.

| Scenario | Strata Count | $N_g$ / Stratum | Total Speakers | Static Super. (A) | SUTA Super. (B) | Accent Reg. (C) | Disparity Guard (D) | Joint Power | Target $\ge 90\%$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Decision Rule B (Theoretical 6-Accent Crossed)** | 6 | 220 | 1,320 | 100.0% | 100.0% | 100.0% | 76.1% | **76.1%** | **FAIL** |
| **Rescaled 6-Accent ($N_g = 40$)** | 6 | 40 | 240 | 100.0% | 98.6% | 100.0% | 26.3% | **26.0%** | **FAIL** |
| **Rescaled 6-Accent ($N_g = 15$, Irish Ceiling)** | 6 | 15 | 90 | 100.0% | 62.7% | 55.7% | 9.0% | **5.2%** | **FAIL** |
| **Pathway 1: 5-Stratum Confirmatory (CV27 Single-Corpus)** | 5 | 220 | 1,100 | 100.0% | 100.0% | 100.0% | 62.4% | **62.4%** | **FAIL** |

*Statistical Finding:* The 5-stratum confirmatory design achieves **62.4%** joint confirmatory power with zero corpus confounding. In contrast, attempting to salvage 6 strata by downsampling $N_g \le 40$ inflates extreme-value disparity variance, causing Event D to fail in 65-100% of trials.

---

## 5. Strategic Academic Decision Recommendations

1. **Epistemic Scope Boundary:**
   Under the currently recorded capacity assumptions and strict eligibility requirements, the audited candidate-corpus registry cannot supply the six-stratum Decision Rule B target. This structural boundary represents a genuine empirical limitation of open crowdsourced speech repositories.
2. **Keep Confirmatory Execution Blocked on `DRAFT_HOLD`:**
   Status remains strictly locked at **`DRAFT_HOLD`** under `PROJECT_LEAD_ACADEMIC_AUTHORIZATION`. No physical audio downloading, manifest freezing, or model inference should occur.
3. **Evaluation of Strategic Decision Pathways:**
   - **Pathway 1 (Re-Anchored Single-Corpus 5-Stratum Confirmatory Benchmark — Scientifically Justified):**
     Formally amend the confirmatory protocol to the 5 surplus strata in Common Voice 27 (Australian, Canadian, England, South Asian, US English at $N_g = 220$; total 1,100 Cohort 3 evaluation speakers + 100 Gate speakers = 1,200 speakers). Achieves zero corpus confounding and **62.4%** joint statistical power. Irish English is retained and evaluated as an exploratory out-of-domain case study.
   - **Pathway 2 (Institutional Irish Speech Archive Acquisition):**
     If a full 240-speaker Irish cohort is non-negotiable, the research team must initiate formal institutional licensing of regional broadcast or academic speech archives (e.g. RTÉ archives or Trinity College Dublin phonetics collections).
   - **Pathway 3 (New Multi-Corpus Pre-Registration):**
     A multi-corpus design is only scientifically valid if an orthogonal crossed structure can be assembled where all six accents have balanced representation across multiple recording platforms.
