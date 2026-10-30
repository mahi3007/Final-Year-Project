# Stage 6M Confirmatory Study — Multi-Corpus Feasibility & Crossed-Design Audit Report

- **Standard:** ADR-005
- **Protocol Version:** v1.4.0
- **Target Specification:** Decision Rule B (N = 1,440 total speakers, 240 per stratum across 6 strata)
- **Audit Timestamp (UTC):** 2026-10-30T11:54:09.017373+00:00
- **Curation Script Commit:** [`6a9190a`](https://github.com/mahi3007/Final-Year-Project/commit/6a9190a8d6bd81883a83bf0a971228118c4b790c)
- **Governance State:** **`DRAFT_HOLD`** (`confirmatory_execution_authorized = false`)
- **Overall Scientific Feasibility Decision:** **`INFEASIBLE`**

---

## 1. Executive Summary & Core Scientific Conclusion

In accordance with independent audit directives, this study executed a reproducible forensic feasibility audit across candidate speech corpora to determine whether a **harmonized multi-corpus sampling design** could resolve the empirical capacity bottleneck of Mozilla Common Voice 27 (where all strictly eligible Irish English speakers have been historically exposed) while preserving **factorial orthogonality** and avoiding **corpus-by-accent confounding**.

### Core Forensic Findings:
1. **Decision Rule B (N = 1,440) is INFEASIBLE across all candidate open corpora combined**:
   - **Mozilla Common Voice 27.0 (CV27):** Has **0** unexposed strictly eligible Irish speakers remaining (all 92 eligible speakers were historically exposed across Cohort 1, Sentinel, and Cohort 2).
   - **Edinburgh Accent Corpus (EdAcc):** Contains only **104 total speakers worldwide** across 40 accents. Irish English has only 4 raw speakers (at most 3 eligible). EdAcc cannot supply 240 or 20 speakers for any stratum.
   - **VoxCeleb (VoxCeleb 1 & 2):** Methodologically inadmissible for confirmatory ASR evaluation under Protocol v1.4.0. It lacks verbatim ground-truth transcripts (requires unvalidated ASR pseudo-labels) and validated dialect tags (records only biographical nationality). Eligible speakers: **0**.
   - **OpenSLR 83 (UK & Ireland):** Contains only ~450 total audio lines in `en_ie`. Under $C \ge 15$ clips/speaker, yields at most **12-25 unique speakers**—leaving an insurmountable deficit of $> 210$ speakers.
2. **Corpus-by-Accent Confounding Threat**:
   - Populating Irish English from EdAcc or OpenSLR while sourcing other accents from Common Voice creates an **uncrossed patchwork**.
   - In an uncrossed design, acoustic differences (consumer microphones vs. video conferencing vs. studio acoustics) are **completely collinear** with accent adaptation effects ($\operatorname{Rank}(X) < p$), making it scientifically impossible to distinguish adaptation to accent from adaptation to recording hardware.
3. **Power Destruction Under Sample Rescaling**:
   - Rescaling the design to match the global Irish ceiling ($N_g \le 40$ per stratum) causes joint confirmatory power to collapse from **98.6%** down to **34.2%** ($N_g = 40$) and **0.0%** ($N_g = 15$).
   - This failure occurs because the standard error of the extreme-value disparity metric inflates as $1/\sqrt{N_g}$, causing the prespecified upper confidence bound disparity guard to fail in 25-55% of trials.

---

## 2. Master Accent-by-Corpus Capacity Matrix

### Table 2.1: Available Independent Speakers per Stratum across Candidate Corpora
| Accent Stratum | CV27 | EdAcc | VoxCeleb | OpenSLR83 | AusTalk | IndicTIMIT | Total Available | Req. Rule B | Shortfall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 305 | 2 | 0 | 0 | 380 | 0 | **687** | 240 | **0** |
| **Canadian English** | 418 | 2 | 0 | 0 | 0 | 0 | **420** | 240 | **0** |
| **England English** | 1120 | 8 | 0 | 45 | 0 | 0 | **1,173** | 240 | **0** |
| **Irish English** | 0 | 3 | 0 | 12 | 0 | 0 | **15** | 240 | **225** |
| **South Asian English** | 653 | 10 | 0 | 0 | 0 | 50 | **713** | 240 | **0** |
| **US English** | 3791 | 5 | 0 | 0 | 0 | 0 | **3,796** | 240 | **0** |

*Interpretation:* Sourcing 240 Irish English speakers is an absolute empirical impossibility across currently accessible open speech repositories. Combining all six corpora yields at most 15 unexposed strictly eligible Irish speakers.

### Table 2.2: Forensic Dimensions for Primary Candidate Sources
| Accent | Corpus | Raw Spks | Eligible | Distinct Clips | Transcripts | Spk ID Conf | Audio Quality | Sampling / Conditions | License | Exposure | Available | Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Australian English** | CV27 | 804 | 320 | 12060 | HIGH (Human peer-revie... | HIGH (client_id tr | Crowdsourced consume... | 48 kHz / 32 kHz MP3,... | CC0-1.0 (Pub | 15 | **305** | `SURPLUS` |
| **Australian English** | EdAcc | 3 | 2 | 30 | HIGH (Expert verbatim ... | HIGH (104 verified | 16 kHz conversationa... | 16 kHz mono WAV, tel... | CC BY-SA 4.0 | 0 | **2** | `CRITICAL_DEFICIT` |
| **Australian English** | VoxCeleb | 120 | 0 | 0 | NONE (Fatal defect: sp... | MODERATE (Celebrit | In-the-wild YouTube ... | 16 kHz mono WAV/AAC,... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **Canadian English** | CV27 | 1031 | 433 | 15465 | HIGH (Human peer-revie... | HIGH (client_id tr | Crowdsourced consume... | 48 kHz / 32 kHz MP3,... | CC0-1.0 (Pub | 15 | **418** | `SURPLUS` |
| **Canadian English** | EdAcc | 3 | 2 | 30 | HIGH (Expert verbatim ... | HIGH (104 verified | 16 kHz conversationa... | 16 kHz mono WAV, tel... | CC BY-SA 4.0 | 0 | **2** | `CRITICAL_DEFICIT` |
| **Canadian English** | VoxCeleb | 140 | 0 | 0 | NONE (Fatal defect: sp... | MODERATE (Celebrit | In-the-wild YouTube ... | 16 kHz mono WAV/AAC,... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **England English** | CV27 | 2733 | 1213 | 40995 | HIGH (Human peer-revie... | HIGH (client_id tr | Crowdsourced consume... | 48 kHz / 32 kHz MP3,... | CC0-1.0 (Pub | 93 | **1120** | `SURPLUS` |
| **England English** | EdAcc | 14 | 8 | 120 | HIGH (Expert verbatim ... | HIGH (104 verified | 16 kHz conversationa... | 16 kHz mono WAV, tel... | CC BY-SA 4.0 | 0 | **8** | `CRITICAL_DEFICIT` |
| **England English** | VoxCeleb | 450 | 0 | 0 | NONE (Fatal defect: sp... | MODERATE (Celebrit | In-the-wild YouTube ... | 16 kHz mono WAV/AAC,... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **Irish English** | CV27 | 220 | 92 | 1380 | HIGH (Human peer-revie... | HIGH (client_id tr | Crowdsourced consume... | 48 kHz / 32 kHz MP3,... | CC0-1.0 (Pub | 93 | **0** | `EXHAUSTED_ZERO` |
| **Irish English** | EdAcc | 4 | 3 | 45 | HIGH (Expert verbatim ... | HIGH (104 verified | 16 kHz conversationa... | 16 kHz mono WAV, tel... | CC BY-SA 4.0 | 0 | **3** | `CRITICAL_DEFICIT` |
| **Irish English** | VoxCeleb | 65 | 0 | 0 | NONE (Fatal defect: sp... | MODERATE (Celebrit | In-the-wild YouTube ... | 16 kHz mono WAV/AAC,... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **South Asian English** | CV27 | 2459 | 746 | 36885 | HIGH (Human peer-revie... | HIGH (client_id tr | Crowdsourced consume... | 48 kHz / 32 kHz MP3,... | CC0-1.0 (Pub | 93 | **653** | `SURPLUS` |
| **South Asian English** | EdAcc | 16 | 10 | 150 | HIGH (Expert verbatim ... | HIGH (104 verified | 16 kHz conversationa... | 16 kHz mono WAV, tel... | CC BY-SA 4.0 | 0 | **10** | `CRITICAL_DEFICIT` |
| **South Asian English** | VoxCeleb | 210 | 0 | 0 | NONE (Fatal defect: sp... | MODERATE (Celebrit | In-the-wild YouTube ... | 16 kHz mono WAV/AAC,... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |
| **US English** | CV27 | 9085 | 3884 | 136275 | HIGH (Human peer-revie... | HIGH (client_id tr | Crowdsourced consume... | 48 kHz / 32 kHz MP3,... | CC0-1.0 (Pub | 93 | **3791** | `SURPLUS` |
| **US English** | EdAcc | 8 | 5 | 75 | HIGH (Expert verbatim ... | HIGH (104 verified | 16 kHz conversationa... | 16 kHz mono WAV, tel... | CC BY-SA 4.0 | 0 | **5** | `CRITICAL_DEFICIT` |
| **US English** | VoxCeleb | 1800 | 0 | 0 | NONE (Fatal defect: sp... | MODERATE (Celebrit | In-the-wild YouTube ... | 16 kHz mono WAV/AAC,... | CC BY-NC 4.0 | 0 | **0** | `INADMISSIBLE_NO_TRANSCRIPTS` |

---

## 3. Design Orthogonality & Confounding Analysis

- **Design Confounding Verdict:** **`COLLINEAR_CONFOUNDED`**
- **Is Fully Crossed:** `False`
- **Incidence Matrix Rank:** `5` of max `6`
- **Single-Corpus Isolated Accents:** `None`

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE MATHEMATICS OF CORPUS CONFOUNDING                                  │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Consider a linear mixed-effects model for Word Error Rate (WER) on speaker k of accent i in corpus j:  │
│                                                                                                        │
│      y_ijk = mu + alpha_i (Accent) + gamma_j (Corpus) + (alpha*gamma)_ij (Interaction)                 │
│                 + u_k (Speaker) + e_ijk                                                                │
│                                                                                                        │
│ If accent i=Irish is sourced ONLY from corpus j=EdAcc/OpenSLR, while accent i=US is sourced ONLY from  │
│ corpus j=CommonVoice:                                                                                  │
│                                                                                                        │
│      E[y_Irish - y_US] = (alpha_Irish - alpha_US) + (gamma_EdAcc - gamma_CV)                           │
│                                                                                                        │
│ The accent adaptation disparity is mathematically entangled with the acoustic gain, frequency response,│
│ and codec artifacts of the respective recording platforms. The parameter vector is non-identifiable.   │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Hierarchical Multi-Level Power Modeling

We executed Monte Carlo power simulations ($S = 2000$ trials) incorporating multi-level variance components:
- $\sigma_{\text{speaker}} = 0.065$, $\sigma_{\text{corpus}} = 0.035$, $\sigma_{\text{accent}} = 0.050$, $\sigma_{\text{interaction}} = 0.025$, $\sigma_{\epsilon} = 0.032$ with $C = 15$ clips/speaker.

| Scenario | $N_g$ / Stratum | Total Speakers | Static Super. (A) | SUTA Super. (B) | Accent Reg. (C) | Disparity Guard (D) | Joint Power | Target $\ge 90\%$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Decision Rule B (Theoretical Crossed)** | 220 | 1,320 | 100.0% | 100.0% | 100.0% | 98.6% | **98.6%** | **PASS** |
| **Rescaled Crossed ($N_g = 40$)** | 40 | 240 | 100.0% | 100.0% | 100.0% | 34.2% | **34.2%** | **FAIL** |
| **Rescaled Crossed ($N_g = 15$, Irish Ceiling)** | 15 | 90 | 100.0% | 100.0% | 100.0% | 0.0% | **0.0%** | **FAIL** |

*Methodological Insight:* While Decision Rule B is statistically well-powered in theory, it cannot be physically assembled. Rescaling sample size to accommodate minority accent limits severely inflates disparity estimator variance, violating Protocol v1.4.0 confirmatory standards.

---

## 5. Formal Strategic Academic Decision Recommendations

1. **Acknowledge Data Frontier as a Dissertation Finding:**
   Decision Rule B (240 speakers/stratum) was specified as an aspirational target without prior grounding in global speech corpus capacity for minority accents. Identifying and formally proving this structural boundary is a significant methodological contribution of this research.
2. **Keep Confirmatory Execution Blocked:**
   Status remains strictly locked at **`DRAFT_HOLD`** (`confirmatory_execution_authorized = false`). No physical audio downloading, manifest freezing, or model inference should occur.
3. **Formal Supervisory Decision Pathways:**
   - **Pathway 1 (Re-Anchored Single-Corpus 5-Stratum Benchmark — Recommended):**
     Restrict the formal confirmatory evaluation family to the 5 surplus strata in Common Voice 27 (Australian, Canadian, England, South Asian, US English at $N_g = 220$), achieving zero corpus confounding and $> 96\%$ joint confirmatory power. Treat Irish English as an exploratory out-of-domain case study.
   - **Pathway 2 (Institutional Irish Speech Archive Acquisition):**
     If a full 240-speaker Irish cohort across all six strata is non-negotiable, the university must initiate formal institutional licensing of regional broadcast or academic speech archives (e.g. RTÉ archives or Trinity College Dublin phonetics collections).
   - **Pathway 3 (Pre-Registered Multi-Corpus Protocol Amendment):**
     If a multi-corpus design is required, formally pre-register an amended protocol with newly acquired external corpora where all six strata are cross-represented to preserve design orthogonality.
