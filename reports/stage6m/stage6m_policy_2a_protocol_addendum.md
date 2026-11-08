# Stage 6M Protocol Addendum: Policy 2A Physical Integrity & Decodability Benchmark Specification

**Document ID:** `STAGE6M_PROTOCOL_ADDENDUM_POLICY_2A`<br>
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)<br>
**Governing Branch / Base Commit:** `stage6m-five-stratum-parity` @ [`baee3b8`](https://github.com/mahi3007/Final-Year-Project/commit/baee3b8381389ffde38e907dc137623748c254a8)<br>
**Document Status:** **APPROVED_PROTOCOL_ADDENDUM (Executed under Gate 1 by Project Lead)**<br>
**Project Lead:** Venkata Akhil Kumar<br>
**Timestamp (UTC):** 2026-11-07T12:29:19.019247+00:00<br>

> [!IMPORTANT]
> **Authoritative Notice:** This document is an APPROVED protocol addendum formally executed by the Project Lead (Venkata Akhil Kumar) on 2026-11-07 under Gate 1 (Scientific Admission Decision Record). Policy 2A is formally adopted as the governing scientific admission policy for the Stage 6M v1.5 benchmark. Crucially, Gate 1 authorizes solely the formal scientific admission criteria and target dataset definition; it does NOT authorize Task 7.7.4 implementation, audio mutations, manifest locking, or GPU CTTA execution. Task 7.7.4 requires a separate, explicit Gate 2 authorization.

---

## 1. Target Population Definition and Research Scope

**Target Population:** The target speech audio population for the Stage 6M confirmatory benchmark is defined strictly as the speech recordings of Mozilla Common Voice 27.0 (en) as distributed, packaged, and accessible to the scientific community, possessing valid MPEG bitstream synchronization and clean PCM decodability.

**Scientific Research Objective:** To evaluate whether Dynamic Spectral Guidance (DSG) provides statistically significant Word Error Rate (WER) reductions and cross-accent disparity safety during Continuous Test-Time Adaptation (CTTA) on real-world, community-contributed natural speech audio without incurring catastrophic accent-specific regression.

### Four-Level Audio Integrity & Completeness Hierarchy

To prevent conflation of distinct technical, decoding, container, and acoustic phenomena, the protocol enforces a strict four-level forensic taxonomy:

| Hierarchy Level | Forensic Dimension | Technical Definition | Empirical Status Across 18,975 Recordings |
| :---: | :--- | :--- | :--- |
| **Level 1** | **Current-File Structural Validity Through Observed EOF** | All available recording files passed the documented MPEG structural checks through their observed file boundaries (valid frame sync headers 0xFFE/0xFFF to EOF, uncorrupted frame synchronization, and complete physical container structure). This does not establish completeness relative to an original recording session or master recording. | **VERIFIED (18,975 of 18,975 recordings, 100.0%)** |
| **Level 2** | **Full-File Decoder / PCM Success** | Clean, finite floating-point PCM decompression without decoding errors or aborts. Verified file-by-file via SoundFile (libmpg123) for all 18,845 accepted recordings in reports/stage6m/stage6m_cohort3_task772b_validator_impact_assessment.json, and verified file-by-file across three independent decoders (SoundFile, PyAV, miniaudio) with sample-exact agreement for all 130 discrepancy-screened recordings in reports/stage6m/stage6m_cohort3_task771_mp3_forensic_triage.json. Full 3-decoder verification across all 18,845 recordings is scheduled under Task 7.7.4 materialization. | **VERIFIED (18,975 of 18,975 recordings: 18,845 via SoundFile/libmpg123; 130 via 3-way multi-decoder exact match)** |
| **Level 3** | **Completeness Relative to Original Masters (Claim B)** | Absence of upstream audio shortening or client-side truncation relative to the uncompressed original microphone capture prior to MP3 compression. | **UNVERIFIED FOR ALL 18,975 RECORDINGS (Authoritative original masters are unavailable in Common Voice 27.0)** |
| **Level 4** | **Recording-Stage Acoustic Clipping** | Saturation or non-linear distortion occurring at the contributor's physical microphone diaphragm or ADC during the physical recording event. | **PHYSICALLY IRRECOVERABLE (Cannot be disproven even if an uncompressed master were available)** |

> [!IMPORTANT]
> **Evidentiary Status:** Current-file structural integrity and PCM decoding have been evaluated using the documented validation procedures. Original-source completeness relative to the uncompressed master recordings remains unverified for all 18,975 recordings because authoritative master references are unavailable. The 130 quarantined recordings additionally have documented duration-estimation discrepancies, which are not, by themselves, proof of physical truncation.

> [!WARNING]
> **Epistemic Boundary:** Clean decoding and current-file integrity do NOT prove complete original recording capture or zero recording truncation. An audio file can decode cleanly to PCM even if audio was previously shortened at a valid MPEG frame boundary prior to distribution. Under Policy 2A, the dissertation explicitly discloses that Claim B remains unverified across all 18,975 recordings.

---

## 2. Preservation of Registered Balanced Experimental Design

This protocol addendum preserves in full the registered balanced sampling design authorized under Section 14.7. Admitting all 18,975 recordings under Policy 2A maintains the exact sample and cluster counts:

- **Confirmatory Strata:** Exactly 5 distinct accent groups (Australian English, Canadian English, England English, South Asian English, United States English).
- **Evaluation Speakers:** Exactly **220 speakers per stratum** across all 5 strata = **1,100 total evaluation speakers**.
- **Clips per Evaluation Speaker:** Exactly **15 recordings per speaker** ($C = 15$) = **16,500 evaluation clips**.
- **Sentinel Gate-Reference Panel:** Exactly **100 speakers** (20 per stratum $\times$ 15 clips = 1,500 clips). Exclusively calibrate adaptation gating and candidate model acceptance; strictly isolated from evaluation estimands.
- **Australian Reserve Pool:** Exactly **65 speakers** (975 clips). Dedicated Australian English replacement pool; strictly preserved and isolated.
- **Total Dataset Assets:** Exactly **18,975 audio recordings**.

### Cohort Structure & Balance Matrix

| Accent Stratum | Evaluation Speakers | Evaluation Clips | Gate Speakers | Gate Clips | Reserve Speakers | Reserve Clips | Total Audio Clips |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 220 | 3,300 | 20 | 300 | 65 | 975 | **4,575** |
| **Canadian English** | 220 | 3,300 | 20 | 300 | 0 | 0 | **3,600** |
| **England English** | 220 | 3,300 | 20 | 300 | 0 | 0 | **3,600** |
| **South Asian English** | 220 | 3,300 | 20 | 300 | 0 | 0 | **3,600** |
| **United States English** | 220 | 3,300 | 20 | 300 | 0 | 0 | **3,600** |
| **Total Confirmatory Cohort** | 1,100 | 16,500 | 100 | 1500 | 65 | 975 | **18,975** |

### Separation of Logical Admission Status and Physical Storage Location

Under Policy 2A, all 18,975 recordings are logically admitted as Common Voice assets, while the 130 discrepancy-screened recordings remain physically in the quarantine directory. Those are two different concepts:

| Measure | Policy 2A Disposition |
| :--- | :---: |
| **Logically admitted dataset assets** | **18,975** |
| **Assets under admission hold** | **0** |
| **Files in the ordinary accepted directory** | **18,845** |
| **Files physically retained in quarantine** | **130** |
| **Original-source completeness verified** | **0** |

- **130 Discrepancy-Screened Recordings Disposition:** `ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY`
- **18,845 Accepted Recordings Disposition:** `ADMITTED_CLAIM_A_VALID_ORIGIN_UNVERIFIED`

> [!NOTE]
> **Physical Isolation Rationale:** Under Policy 2A, all 18,975 recordings are logically admitted as Common Voice assets, while the 130 discrepancy-screened recordings remain physically in the quarantine directory (cohort3_rejected_quarantine). Those are two different concepts. The 130 files carry the explicit admission disposition ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY, retaining their original physical location until a separate Gate 2 authorization permits any materialization operation. This avoids accidentally suggesting that the 130 recordings are excluded from the research population merely because they remain in quarantine.

---

## 3. Exact Primary Estimand and Mathematical Specifications

The primary inferential estimand follows the pre-registered specification under **Protocol Section 14.7 / ADR-005 Pre-Registered Primary Inferential Estimand**.

### 3.1 Speaker-Level Word Error Rate (WER) Calculation

**Registered Definition:** Approach 2: Pooled Speaker Errors Divided by Pooled Reference Words

$$WER_{a, s} = \frac{\sum_{c=1}^{C_s} (S_{a, sc} + D_{a, sc} + I_{a, sc})}{\sum_{c=1}^{C_s} N_{sc}^{\text{ref}}} \times 100\%$$

> **Protocol Alignment:** This pooled-speaker formula matches the production implementation in src/dsg_ctta/offline/aggregation.py (spk_wer = (s_s + s_d + s_i) / s_n) and tests/research_validity/test_stage6m_reproducibility_and_gate_validity.py. It prevents small-denominator distortion from single-word clips and avoids changing the pre-registered estimand.

### 3.2 Paired Differences and Stratum Aggregation

For each speaker $s$, the paired adaptation impact is:
$$\Delta_s = \text{WER}_{3, s} - \text{WER}_{1, s} = \frac{\sum_{c=1}^{15} (E_{3, sc} - E_{1, sc})}{\sum_{c=1}^{15} N_{sc}^{\text{ref}}} \times 100\%$$

The stratum-level contrast is the unweighted average across all $N_g = 220$ speakers in stratum $g$:
$$\Delta_g = \frac{1}{N_g} \sum_{s \in \text{Stratum } g} \Delta_s$$

### 3.3 Primary Confirmatory Contrasts & Bonferroni Decision Rules

The confirmatory benchmark enforces a **Fixed Single-Step Simultaneous Bonferroni Procedure** across $M = 8$ one-sided hypotheses ($lpha_{	ext{family}} = 0.05, lpha_{	ext{adj}} = 0.00625$, simultaneous confidence percentile = $99.375\%$):

| Event / Hypothesis | Target Comparison | Mathematical Estimand | Null & Alternative | Confirmatory Acceptance Rule ($99.375\%$ UCB) |
| :--- | :--- | :--- | :--- | :--- |
| **CRITERION_1_EVENT_A** | DSG-Gated vs Static Baseline (Primary Utility) | $$\Delta_{\text{static}} = \text{WER}_{3} - \text{WER}_{1} = \frac{\sum_{s,c} (E_{3,sc} - E_{1,sc})}{\sum_{s,c} N_{sc}^{\text{ref}}} \times 100\%$$ | $$H_{0, A}: \Delta_{\text{static}} \ge 0.00\text{ pp}$$ vs $$H_{1, A}: \Delta_{\text{static}} < 0.00\text{ pp}$$ | `\text{UCB}_{99.375\%}(\Delta_{\text{static}}) < 0.00\text{ pp}` |
| **CRITERION_2_EVENT_B** | DSG-Gated vs Ungated SUTA (Primary Utility) | $$\Delta_{\text{ungated}} = \text{WER}_{3} - \text{WER}_{2} = \frac{\sum_{s,c} (E_{3,sc} - E_{2,sc})}{\sum_{s,c} N_{sc}^{\text{ref}}} \times 100\%$$ | $$H_{0, B}: \Delta_{\text{ungated}} \ge 0.00\text{ pp}$$ vs $$H_{1, B}: \Delta_{\text{ungated}} < 0.00\text{ pp}$$ | `\text{UCB}_{99.375\%}(\Delta_{\text{ungated}}) < 0.00\text{ pp}` |
| **CRITERION_3_EVENT_C** | Per-Accent Non-Inferiority across All 5 Strata (Fairness Guards) | $$\Delta_g = \text{WER}_{3, g} - \text{WER}_{1, g} \quad \forall g \in \{1, 2, 3, 4, 5\}$$ | $$H_{0, C, g}: \Delta_g > +2.00\text{ pp}$$ vs $$H_{1, C, g}: \Delta_g \le +2.00\text{ pp}$$ | `\text{UCB}_{99.375\%}(\Delta_g) \le +2.00\text{ pp} \quad \forall g \in \{1, 2, 3, 4, 5\}` |
| **CRITERION_4_EVENT_D** | Cross-Accent Disparity Non-Increase (Fairness Safety) | $$D = \max_{g \in \mathcal{G}} \text{WER}_g - \min_{g \in \mathcal{G}} \text{WER}_g, \quad \Delta D = D_{\text{Arm 3}} - D_{\text{Arm 1}}$$ | $$H_{0, D}: \Delta D > 0.00\text{ pp}$$ vs $$H_{1, D}: \Delta D \le 0.00\text{ pp}$$ | `\text{UCB}_{99.375\%}(\Delta D) \le 0.00\text{ pp} \quad (\text{with diagnostic monitoring boundary } \le +1.40\text{ pp})` |

### Composite Joint Success Rule
> **Stage 6M confirmatory CTTA success is declared IF AND ONLY IF all 8 hypotheses pass simultaneously:**
> $$\text{SUCCESS} \iff \text{Event A} \land \text{Event B} \land \text{Event C} \land \text{Event D}$$
> **Multiplicity Framework:** `Fixed Single-Step Simultaneous Bonferroni (M = 8, alpha_family = 0.05, alpha_adj = 0.00625, UCB percentile = 99.375%)`

### 3.4 Relationship Between Estimands & Proof of Non-Identity under Variable Word Counts

In speech recognition evaluation, three distinct aggregation levels exist:
- **Clip-Macro WER:** $$\text{WER}_{\text{clip}} = \frac{1}{S \cdot C} \sum_{s=1}^S \sum_{c=1}^C \frac{E_{sc}}{N_{sc}}$$. Weights every audio clip equally ($1 / (S \cdot C)$).
- **Pooled Speaker WER (Approach 2):** $$\text{WER}_s = \frac{\sum_{c=1}^C E_{sc}}{\sum_{c=1}^C N_{sc}} = \sum_{c=1}^C \left( \frac{N_{sc}}{W_s} \right) \text{WER}_{sc}$$. Weights clips within a speaker by their reference-word counts.
- **Speaker-Macro WER:** $$\text{WER}_{\text{speaker}} = \frac{1}{S} \sum_{s=1}^S \text{WER}_s$$. Weights each speaker equally ($1/S$).
- **Corpus Word-Micro WER:** $$\text{WER}_{\text{word}} = \frac{\sum_{s,c} E_{sc}}{\sum_{s,c} N_{sc}}$$. Weights each word equally; speakers weighted by total words.

> [!IMPORTANT]
> **Proof of Non-Identity:** Under constant $C = 15$ clips per speaker, speaker-macro and clip-macro are identical **as mathematical aggregation functions** if and only if every clip of speaker $s$ contains the exact same number of reference words ($N_{sc} = W_s / C$). While accidental numerical equality can theoretically occur on a single realized dataset through fortuitous cancellation, they are fundamentally distinct estimands with different weighting structures. In natural speech corpora like Common Voice, sentence lengths vary naturally. Therefore, equal clip counts per speaker do **NOT** make pooled speaker-macro functionally identical to clip-macro.

#### Concrete Numerical Counterexample
- **Scenario:** Consider a minimal cohort with S = 1 speaker and C = 2 clips (balanced clip count):
  - Clip 1: `N_11 = 2 reference words, E_11 = 2 errors -> WER_11 = 2/2 = 100.0%`
  - Clip 2: `N_12 = 10 reference words, E_12 = 0 errors -> WER_12 = 0/10 = 0.0%`
- **Clip-Macro Outcome:** `WER_clip = (1/2) * (100.0% + 0.0%) = 50.0%`
- **Pooled Speaker-Macro Outcome:** `WER_s = (2 + 0) / (2 + 10) = 2/12 = 16.67%`
- **Observed Discrepancy:** **WER_speaker (16.67%) != WER_clip (50.0%) by 33.33 percentage points despite balanced C=2.**

> **Protocol Specification:** The registered Section 14.7 protocol specifies Speaker-Macro over Pooled Speaker WERs (Approach 2). This preserves equal speaker weighting (1/S) across the evaluation cohort without distorting estimates by single short utterances, but must NOT be described as mathematically identical to clip-macro.

---

## 4. Statistical Power Status and Decision Boundaries

### 4.1 Calibrated Statistical Power
- **Registered Sample Size:** N_g = 220 speakers per stratum (N = 1,100, C = 15, M = 16,500 clips)
- **Multiplicity Architecture:** `M = 8 One-Sided Hypotheses, Fixed Bonferroni alpha_adj = 0.00625, Percentile = 99.375%`
- **Simulation Depth:** 10,000 Monte Carlo trajectories, B = 20,000 bootstrap resamples per trajectory
- **Calibrated Disparity Effect:** -2.0 percentage points
- **Observed Joint Empirical Power:** **90.58%**
- **Exact Clopper-Pearson Bounds:** One-sided 95% LCB = **90.085739%** (LCB_95 >= 90.000000% (Passed by +0.0857 pp / +8 trajectories)). Two-sided 95% CI: `[89.990601%, 91.145641%]`.

> [!WARNING]
> **Conditional Simulation Boundary:** The calibrated 90.58% joint power result was calculated under the exact M = 8 simultaneous Bonferroni decision architecture with simultaneous one-sided 99.375% bounds. It is strictly conditional on its pre-registered simulation assumptions: between-speaker standard deviation sigma_between = 6.50 pp, within-speaker paired difference standard deviation sigma_paired = 3.20 pp, and target disparity effect Delta D = -2.00 pp. This result demonstrates that the registered balanced sample size (N_g=220) is statistically adequate to detect the targeted effect sizes under Monte Carlo simulation; it does NOT constitute proof of observed DSG efficacy or guarantee real-world adaptation success on the physical confirmatory run.

### 4.2 Reconciliation of Nominal vs. Authoritative Simultaneous Confidence Levels

The project reports have previously referenced both nominal unadjusted bounds (e.g. 97.5% for accent non-inferiority, 95% for disparity safety) and simultaneous Bonferroni bounds ($99.375\%$). The table below reconciles these quantities against the authoritative frozen five-stratum protocol (`src/dsg_ctta/evaluation/paired_cluster_inference_v15.py`):

| Evaluation Metric | Nominal / Exploratory Level | Confirmatory Bonferroni Architecture ($M = 8$) | Operative Status |
| :--- | :--- | :--- | :--- |
| **Event A (Superiority vs. Static)** | $\Delta_{\text{static}} < 0.00\text{ pp}$ (nominal) | $\text{UCB}_{99.375\%}(\Delta_{\text{static}}) < 0.00\text{ pp}$ | Confirmatory Gate |
| **Event B (Superiority vs. Ungated SUTA)** | $\Delta_{\text{ungated}} < 0.00\text{ pp}$ (nominal) | $\text{UCB}_{99.375\%}(\Delta_{\text{ungated}}) < 0.00\text{ pp}$ | Confirmatory Gate |
| **Event C (Accent Regression Guards)** | $97.5\%\text{ UCB} \le +2.00\text{ pp}$ (per-comparison) | $\text{UCB}_{99.375\%}(\Delta_g) \le +2.00\text{ pp} \quad \forall g \in \{1..5\}$ | Confirmatory Gate (5 Strata) |
| **Event D (Disparity Safety)** | $95.0\%\text{ UCB} \le +1.40\text{ pp}$ (diagnostic) | $\text{UCB}_{99.375\%}(\Delta D) \le 0.00\text{ pp}$ | Confirmatory Gate |

> [!IMPORTANT]
> **Power Alignment:** In the authoritative Stage 6M v1.5 confirmatory benchmark (src/dsg_ctta/evaluation/paired_cluster_inference_v15.py), multiplicity across all M = 8 confirmatory hypotheses is controlled via a single-step simultaneous Bonferroni procedure: alpha_family = 0.05, alpha_adjusted = 0.05 / 8 = 0.00625, simultaneous one-sided UCB percentile = 99.375%. All confirmatory decisions are governed by simultaneous 99.375% bounds (Event A: static UCB < 0.00 pp; Event B: ungated UCB < 0.00 pp; Event C: 5 accent regression UCBs <= +2.00 pp; Event D: disparity bootstrap UCB <= 0.00 pp). Crucially, the Task 6.3 calibrated power result of 90.58% (Clopper-Pearson 95% LCB = 90.085739%) evaluated this exact simultaneous M = 8, 99.375% Bonferroni criterion. The nominal 97.5% and 95.0% levels are exploratory only and do NOT govern confirmatory gate decisions.

### 4.3 Preserved Decision Thresholds

| Gate / Confirmatory Dimension | Pre-Registered Threshold Invariant |
| :--- | :--- |
| **Multiplicity Family** | `M = 8 Hypotheses, alpha_family = 0.05, alpha_adj = 0.00625` |
| **Simultaneous UCB Percentile** | `99.375% (1 - 0.00625)` |
| **Event A (Superiority vs Static)** | `UCB_99.375%(Delta_static) < 0.00 pp` |
| **Event B (Superiority vs Ungated SUTA)** | `UCB_99.375%(Delta_ungated) < 0.00 pp` |
| **Event C (Accent Regression Guards)** | `UCB_99.375%(Delta_g) <= +2.00 pp for all 5 strata` |
| **Event D (Disparity Safety)** | `UCB_99.375%(Delta_D) <= 0.00 pp (nominal) / <= +1.40 pp (diagnostic)` |
| **Candidate Loss Sanity** | `Scalar loss is finite; grad_norm < 100.0; non-zero update norm` |

---

## 5. Governance Status & Execution Preconditions

**Operative Status:** `ACTIVE / APPROVED UNDER GATE 1 (Executed 2026-11-07)`

### Mandatory Preconditions Before Activation:
- 1. Project Lead formally executes Gate 1 (Scientific Admission Decision Record for Policy 2A) — COMPLETE (2026-11-07).
- 2. Project Lead independently executes Gate 2 (Task 7.7.4 Non-Destructive Materialization Authorization) — PENDING.
- 3. Reconciled dataset assets are validated without destructive deletion or file mutation.
- 4. Final execution manifest is generated, verified, and locked under Gate 3 (STATUS: LOCKED).
- 5. Software environment, models, and configuration are verified via non-confirmatory smoke tests (Gate 4).

### Strictly Prohibited Operations:
- No automatic authorization of Task 7.7.4 upon Gate 1 approval.
- No GPU CTTA execution on confirmatory audio.
- No unsealing of evaluation transcripts.
- No promotion or mutation of audio assets prior to independent Gate 2 authorization.
- No git commit or push without explicit instruction.

---

## 6. Project Lead Gate 1 Decision Record

```markdown
# GATE 1: SCIENTIFIC ADMISSION POLICY (POLICY 2A) — DECISION RECORD

Decision Authority: Project Lead (Venkata Akhil Kumar)
Governing Scope:    Authorizes formal scientific admission criteria and target dataset definition only.
                    Implementation and execution of Task 7.7.4 require separate Gate 2 authorization.

Decision Status:    [X] APPROVED AS ACTIVE PROTOCOL ADDENDUM (Gate 1 Passed)
                    [ ] REJECTED / RETURNED FOR REVISION
                    [ ] AWAITING DETERMINATION

Selected Policy:    [X] Policy 2A (Physical Integrity & Decodability Benchmark)
                    [ ] Policy 1  (Claim B Prerequisite)
                    [ ] Policy 2B (Estimation Discrepancy Screen)

Decision Rationale: Evaluates Mozilla Common Voice 27.0 (en) as distributed to the speech recognition
                    research community across five balanced accent strata (Australian, Canadian,
                    England, South Asian, US English) without asserting unverified claims regarding
                    original recording capture or master completeness.
Research Scope:     Mozilla Common Voice 27.0 (en) as distributed across five balanced accent strata
Claim Limitations:  Claim A: Current-file structural validity through observed EOF (Verified 18,975/18,975)
                    Claim B: Original-source completeness relative to uncompressed masters (Unverified for all 18,975)

Dataset Admission & Physical Storage Disposition (Policy 2A):
| Measure                                  | Policy 2A disposition |
| Logically admitted dataset assets        | 18,975                |
| Assets under admission hold              | 0                     |
| Files in the ordinary accepted directory | 18,845                |
| Files physically retained in quarantine  | 130                   |
| Original-source completeness verified    | 0                     |

130 Discrepancy-Screened Files Disposition: ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY
(Physically retained in quarantine directory until separate Gate 2 materializer authorization)

Decision Date:      2026-11-07
```

