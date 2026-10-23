# Stage 6M Methodological Audit: Design Validity, Identifiability & External Data Governance

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)  
**Parent Document:** [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md)  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED** (`execution_authorized = false`)  
**Audit Purpose:** Targeted scientific consistency and identifiability audit of the Stage 6M Supervisor Decision Pack, reconciling external corpus counts, distinguishing candidate resources from verified speakers, separating source characteristics from accent provenance, correcting primary-design language, qualifying external portability coverage, reconciling sample-size candidates with mandatory power rules, and providing qualified provenance statements.

---

## 1. Executive Summary & Epistemic Status

In response to supervisory reviews of the Stage 6M Decision Pack, this audit provides a critical methodological evaluation of the proposed confirmatory study design:
> **Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition**

The primary contribution of this research is not simply demonstrating that test-time adaptation lowers overall Word Error Rate (WER). Rather, it investigates whether continual test-time adaptation can be achieved **without exacerbating performance disparities across accent groups or inducing catastrophic subgroup regressions**. 

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
AUDIT VERDICT & GOVERNANCE STATE:
• Confirmatory Execution Gate: STRICT NO-GO (execution_authorized = false)
• Cohort 2 Status: PROPOSED — UNCREATED AND UNMANIFESTED
• Final Sample Size: STRICTLY UNFROZEN
  - N=450 fails both Rule A (84.50% < 85%) and Rule B (83.38% < 85%)
  - N=468 passes Rule A (85.83% ≥ 85%) but fails Rule B (84.74% < 85%)
  - N=540 cannot be drawn from Common Voice alone (Irish pool ceiling = 78) and baseline power (90.40%)
    belongs to a pooled single-source model that does not establish power for the decoupled design.
  - CONCLUSION: No currently listed Common Voice-only sample-size candidate has demonstrated
    compliance with both mandatory rules under the existing simulation results.
• Mandatory Power Rules: Rule A (Point Estimate ≥ 85%) & Rule B (Lower 95% MC Bound > 85%) preserved
• Reserve Policy: UNRESOLVED (Neither Policy A nor Policy B approved)
• External Resources: 4 named, 3 retained as candidates, 0 verified, 0 acquired
• External Portability: 6-group external coverage NOT yet feasible on current evidence (Canada & US gap)
• Decision Pack Classification: DRAFT FOR PRELIMINARY METHODOLOGICAL REVIEW ONLY
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

This audit resolves seven critical scientific issues identified during supervisory review:
1. **Reconciliation of External-Corpus Counts:** Distinguishes the **4 named resources** (AusTalk, LibriTTS-R, OpenSLR 83, IndicTIMIT) from the **3 retained candidate sources** (AusTalk, OpenSLR 83, IndicTIMIT; LibriTTS-R lacks verified dialect metadata for Canada and US) and the **0 verified/acquired external sources**.
2. **South Asian Accent Provenance:** Moves "18 Indian nativities" to source-level characteristics, clarifying that documented nativities do not establish verified South Asian English accent provenance under project criteria.
3. **Separation of Corpus Size from Speaker Counts:** Separates total corpus size, reported utterance lines, documented unique speakers, verified accent provenance, and eligible speaker counts ($C \ge 15$). Replaces inferred speaker counts with `UNVERIFIED`.
4. **Primary-Design Language Correction:** Replaces "unconfounded at dataset level" with precise wording: the single-source Common Voice design avoids pooling different corpus sources in primary comparisons, reducing between-corpus confounding, but does not eliminate potential within-corpus confounding or establish a causal effect of accent.
5. **Explicit External Portability Coverage Gaps:** Explicitly documents that a six-group external portability benchmark is not yet feasible because Canadian and US external speaker assignments remain unverified.
6. **Prominent Power-Rule Consequences:** Reconciles the sample-size candidates against both mandatory rules (Rule A and Rule B). Confirms that no currently listed Common Voice-only candidate meets both rules.
7. **Corrected Provenance Statement:** Explicitly states that the six audited baseline paths have no reported working-tree modifications and their LF-normalized content matches the corresponding Git blobs (establishing current content parity without proving that no temporary uncommitted edits occurred and were subsequently reverted), while the untracked simulation JSON retains its reported size and digest but its historical immutability and execution provenance remain unverified.

---

## 2. Task 1: Mathematical Identifiability Analysis (Additive vs. Interaction Models)

### 2.1 The Multilevel Model Formulation

Consider the proposed linear model of speaker-level adaptation effect on Word Error Rate:
$$\Delta_{g,c,s} = \beta_0 + \alpha_g + \gamma_c + u_{g,c} + v_s + \bar{\epsilon}_{g,c,s}$$
where:
- $\beta_0$: Grand mean adaptation effect across all speakers, accents, and corpora.
- $\alpha_g$: Accent-group main effect ($g \in \{1,\dots,6\}$, with $\sum_{g=1}^6 \alpha_g = 0$).
- $\gamma_c$: Corpus-source main effect ($c \in \{1,\dots,K\}$, with $\sum_{c=1}^K \gamma_c = 0$).
- $u_{g,c}$: Accent-by-corpus interaction deviation.
- $v_s \sim \mathcal{N}(0, \sigma_{\text{spk}}^2)$: Speaker-level random intercept.
- $\bar{\epsilon}_{g,c,s}$: Residual paired error across clips.

### 2.2 Identifiability Under the Additive Model (No-Interaction Assumption)

Suppose we enforce the restrictive assumption that there are **no accent-by-corpus interactions** ($u_{g,c} = 0 \quad \forall g, c$):
$$\mathbb{E}[\Delta_{g,c}] = \beta_0 + \alpha_g + \gamma_c$$

Under this additive model:
- Mozilla Common Voice 27.0 provides observations across **all six accent groups** ($g \in \{1,\dots,6\}$).
- For each group $g$, the Common Voice cell mean is $\mathbb{E}[\Delta_{g, \text{CV}}] = \beta_0 + \alpha_g + \gamma_{\text{CV}}$.
- The contrast between any two accent groups $g$ and $g'$ within Common Voice is:
  $$\mathbb{E}[\Delta_{g, \text{CV}}] - \mathbb{E}[\Delta_{g', \text{CV}}] = \alpha_g - \alpha_{g'}$$
  which directly identifies the accent contrasts.
- For an external source $c$ that supplies speakers to accent group $g$, the cell mean is $\mathbb{E}[\Delta_{g, c}] = \beta_0 + \alpha_g + \gamma_c$.
- Subtracting the Common Voice cell mean for the same group $g$ yields:
  $$\mathbb{E}[\Delta_{g, c}] - \mathbb{E}[\Delta_{g, \text{CV}}] = \gamma_c - \gamma_{\text{CV}}$$
  which identifies the corpus main effect $\gamma_c$ relative to Common Voice.

**Conclusion on Additive Identifiability:**  
Because Common Voice spans all six groups, it acts as a bridge connecting the accent groups. Under the strict assumption that the adaptation effect does not vary by accent across corpora ($u_{g,c} = 0$), the additive main effects $\alpha_g$ and $\gamma_c$ are mathematically identifiable.

### 2.3 Identifiability Failure Under the Full Interaction Model

The primary research question of this project is whether adaptation behaviour and disparity mitigation generalize across diverse speech sources. In reality, acoustic environments (studio vs. mobile), recording tasks (prompted sentences vs. spontaneous speech), and background noise interact with accent pronunciations.

When we allow group-by-corpus interactions ($u_{g,c} \neq 0$):
$$\mathbb{E}[\Delta_{g,c}] = \beta_0 + \alpha_g + \gamma_c + u_{g,c}$$

Consider the proposed external allocation where each external corpus supplies speakers to only one (or two) accent groups:
- AusTalk supplies external speakers *only* to Australia ($g=\text{Aus}$).
- IndicTIMIT supplies external speakers *only* to South Asia ($g=\text{SA}$).

In the external sample, the cell means are:
$$\mathbb{E}[\Delta_{\text{Aus, AusTalk}}] = \beta_0 + \alpha_{\text{Aus}} + \gamma_{\text{AusTalk}} + u_{\text{Aus, AusTalk}}$$
$$\mathbb{E}[\Delta_{\text{SA, IndicTIMIT}}] = \beta_0 + \alpha_{\text{SA}} + \gamma_{\text{IndicTIMIT}} + u_{\text{SA, IndicTIMIT}}$$

Evaluating the contrast between external Australian and external South Asian speech yields:
$$\mathbb{E}[\Delta_{\text{Aus, AusTalk}}] - \mathbb{E}[\Delta_{\text{SA, IndicTIMIT}}] = (\alpha_{\text{Aus}} - \alpha_{\text{SA}}) + (\gamma_{\text{AusTalk}} - \gamma_{\text{IndicTIMIT}}) + (u_{\text{Aus, AusTalk}} - u_{\text{SA, IndicTIMIT}})$$

**The Identifiability Failure:**
Because AusTalk contains no South Asian speakers and IndicTIMIT contains no Australian speakers:
1. The external-source difference $(\gamma_{\text{AusTalk}} - \gamma_{\text{IndicTIMIT}})$ cannot be separated from the accent difference $(\alpha_{\text{Aus}} - \alpha_{\text{SA}})$.
2. The interaction term $u_{\text{Aus, AusTalk}}$ cannot be distinguished from the source main effect $\gamma_{\text{AusTalk}}$ from that single cell alone.
3. Subtracting the Common Voice contrast yields a difference-in-differences estimator:
   $$\Big(\mathbb{E}[\Delta_{\text{Aus, AusTalk}}] - \mathbb{E}[\Delta_{\text{Aus, CV}}]\Big) - \Big(\mathbb{E}[\Delta_{\text{SA, IndicTIMIT}}] - \mathbb{E}[\Delta_{\text{SA, CV}}]\Big) = (\gamma_{\text{AusTalk}} - \gamma_{\text{IndicTIMIT}}) + (u_{\text{Aus, AusTalk}} - u_{\text{SA, IndicTIMIT}})$$
   which isolates the differential corpus-plus-interaction shift, but **cannot separate the corpus effect from the interaction effect**.

**Summary of Identifiability Finding:**
The terms in the proposed hierarchical model cannot simply be declared identifiable because they have been written down. With the current sparse source-by-accent allocation, group-by-corpus interactions and separate corpus versus interaction variance components require additional design information or explicit identifying assumptions.

### 2.4 Causal Scope of Single-Corpus Evaluation

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
CORRECTED METHODOLOGICAL SCOPE: OBSERVATIONAL ACCENT CATEGORIES
The single-source Common Voice design avoids pooling different corpus sources in the primary
group comparisons. It reduces between-corpus confounding but does NOT eliminate potential
confounding from within-corpus recording conditions, microphone variations, speaker demographics,
speech rates, or participant recruitment mechanisms across groups.
Accent groups are observational categories, not randomly assigned experimental treatments.
Observed performance differences must be interpreted as group-specific empirical disparities,
NOT as isolated causal effects of accent alone.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

### 2.5 Recommended Architecture: Two-Tier Decoupled Architecture

In light of the identifiability analysis, the **Two-Tier Decoupled Architecture** is recommended as a candidate for supervisory review:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              RECOMMENDED TWO-TIER DECOUPLED ARCHITECTURE                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 1: Common Voice Primary Confirmatory Trial                                                       │
│   • Evaluates primary disparity-aware adaptation comparisons entirely within Mozilla Common Voice.     │
│   • Uses the six frozen group definitions and the approved prequential protocol.                       │
│   • Avoids pooling different corpus sources in the primary group comparisons.                          │
│   • Results are reported as within-corpus group-specific performance disparities.                     │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: Decoupled External Portability Benchmark                                                       │
│   • Evaluates the frozen adapted models on independently sourced external corpora.                     │
│   • Performance is reported separately by corpus and accent group (e.g. AusTalk Australia, IndicTIMIT).│
│   • Does not claim to establish six-group portability until all six groups have verified sources.      │
│   • Does not force artificial joint ANOVA pooling across confounded external cells.                    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Task 2: Revised Source-by-Accent Matrix (Reconciled Resource Counts & Provenance)

### 3.1 External Resource Accounting Reconciled

The source matrix names **four distinct external resources**:
1. **AusTalk**
2. **LibriTTS-R**
3. **OpenSLR 83**
4. **IndicTIMIT**

OpenSLR 83 appears under both England and Ireland, and LibriTTS-R appears under Canada and the US. These are repeated uses of unified corpora. 

| Interpretation | Count | Meaning & Governance Status |
| :--- | :---: | :--- |
| **Distinct external resources named in the proposed allocation** | **4** | AusTalk, LibriTTS-R, OpenSLR 83, and IndicTIMIT |
| **External resources retained as candidate sources in proposed design** | **3** | AusTalk, OpenSLR 83, and IndicTIMIT (LibriTTS-R lacks verified dialect tags) |
| **Resources verified to contain required eligible and acquired speakers** | **0** | No external speakers are currently verified or present in the workspace |

Neither the count of 4 named resources nor the count of 3 candidate sources establishes eligible-speaker availability. All 90 external speakers remain a **planning target**.

### 3.2 Evidence-Based Source-by-Accent Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   EVIDENCE-BASED SOURCE-BY-ACCENT CANDIDATE ALLOCATION MATRIX                                              │
├───────────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬───────────────┤
│ Metric / Source   │ Australia    │ Canada       │ England      │ Ireland      │ South Asian  │ US English   │ Total Target │ Verification  │
│ Dimension         │ (australia)  │ (canada)     │ (england)    │ (ireland)    │ (south_asian)│ (us)         │ Across Strata│ Status        │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Target CV Active  │ 75           │ 75           │ 75           │ 75           │ 75           │ 75           │ 450          │ Local CV 27.0 │
│ Target Ext Active │ 15           │ 15           │ 15           │ 15           │ 15           │ 15           │  90          │ Planning Goal │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Proposed External │ AusTalk      │ LibriTTS-R   │ OpenSLR 83   │ OpenSLR 83   │ IndicTIMIT   │ LibriTTS-R   │ 4 Named /    │ 4 Named;      │
│ Corpus Resource   │              │ (Unverified) │ (UK Subset)  │ (Irish Sub.) │              │ (US Subset)  │ 3 Candidate  │ 3 Retained    │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Documented Corpus │ 861 adult    │ 585 hours    │ Crowdsourced │ Crowdsourced │ ~240 hours   │ 585 hours    │ Published    │ Published     │
│ Characteristics   │ speakers;    │ restored     │ mobile/web   │ mobile/web   │ read speech; │ restored     │ source specs │ source specs  │
│                   │ 15 locations │ audiobooks   │ audio        │ audio        │ 80 artists   │ audiobooks   │              │               │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Reported Line /   │ Multiple     │ Thousands of │ Thousands of │ ~450 lines   │ ~240 hours   │ Thousands of │ Published    │ Utterance     │
│ Utterance Count   │ speech tasks │ utterances   │ lines        │ (utterances) │ speech audio │ utterances   │ counts       │ documentation │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Documented Unique │ 861 adult    │ 2,456 total  │ UNVERIFIED   │ UNVERIFIED   │ 80 voice     │ 2,456 total  │ Documented   │ Unique speaker│
│ Speaker Count     │ speakers     │ speakers     │ (lines ≠ spk)│ (~450ln≠spk) │ artists      │ speakers     │ unique spks  │ accounting    │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Unique Speakers   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ 0 verified   │ Accent-tag    │
│ with Verified     │ (screening   │ (NO CANADIAN │ (dialect map │ (dialect map │ (80 artists; │ (regional US │ in workspace │ audit         │
│ Accent Provenance │ pending)     │ ACCENT TAG)  │ required)    │ & audit req) │ mapping unv) │ audit req)   │              │ required      │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Speakers Meeting  │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ UNVERIFIED   │ 0 verified   │ Audio clip    │
│ Approved C ≥ 15   │ (screening   │ (screening   │ (screening   │ (screening   │ (screening   │ (screening   │ in workspace │ audit         │
│ Eligibility Rule  │ pending)     │ pending)     │ pending)     │ pending)     │ pending)     │ pending)     │              │ required      │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Speakers Acquired │ 0 speakers   │ 0 speakers   │ 0 speakers   │ 0 speakers   │ 0 speakers   │ 0 speakers   │ 0 speakers   │ Audited       │
│ and in Workspace  │              │              │              │              │              │              │              │ Inventory     │
├───────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ Overlap Risk with │ UNASSESSED   │ UNASSESSED   │ UNASSESSED   │ UNASSESSED   │ UNASSESSED   │ UNASSESSED   │ UNASSESSED   │ Cross-corpus  │
│ Common Voice 27.0 │              │              │              │              │              │              │              │ hash audit req│
└───────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴───────────────┘
```

### 3.3 Critical Provenance & Feasibility Notes
1. **South Asian English Entry Clarification:** The source documentation reports 80 voice artists from 18 Indian nativities. Speaker-level mapping to the project's South Asian English group and eligibility criteria remains `UNVERIFIED`. English-accent group membership cannot be inferred automatically from nationality or nativity.
2. **OpenSLR 83 Line Counts:** The published documentation lists ~450 lines for Irish English male utterances. A count of 450 lines does not establish 15 eligible speakers; the unique-speaker count remains `UNVERIFIED`.
3. **LibriTTS-R Canada & US:** Published documentation (Koizumi et al., Interspeech 2023) establishes no Canadian accent tag (`UNVERIFIED`). US regional dialect provenance is also untagged (`UNVERIFIED`).
4. **External Portability Panel Coverage Gap:** Because Canadian and US assignments to LibriTTS-R remain unverified, the proposed Tier 2 external panel currently identifies potential routes for only Australia, South Asia, and UK/Ireland. **A six-group external portability benchmark is NOT yet feasible on current evidence.** The eventual external analysis may report only groups and corpora for which suitable speakers are actually obtained and verified.
5. **Overlap Risk Reclassification:** The external-corpus overlap risk is formally designated as **`UNASSESSED`** pending empirical hash and text audits against CV 27.0.

---

## 4. Task 4: Reconciliation of Sample-Size Candidates with Mandatory Power Rules

### 4.1 Reconciled Simulation Evidence Table

ADR-005 establishes two distinct, mandatory power criteria:
- **Rule A:** Estimated joint power $\widehat{P}_{\text{joint}} \ge 85.00\%$.
- **Rule B:** Lower bound of the 95% Monte Carlo confidence interval $L_{95\%, \text{MC}} > 85.00\%$.

The canonical simulation results serialized in [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) ($S=4,000, B=1,000$, SHA-256 `8fac4d32d5f8…`) report:

| Active Sample Size ($N_{\text{active}}$) | Stratum Allocation ($n_{\text{active}, g}$) | Estimated Joint Power ($\widehat{P}_{\text{joint}}$) | Lower 95% MC Bound ($L_{95\%, \text{MC}}$) | Upper 95% MC Bound ($U_{95\%, \text{MC}}$) | Rule A ($\widehat{P} \ge 85\%$) | Rule B ($L_{95\%} > 85\%$) | Compliance Verdict under Unchanged Rules |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$N = 450$** | $75$ / stratum | $84.50\%$ | $83.38\%$ | $85.62\%$ | **FAIL** | **FAIL** | **NON-COMPLIANT** |
| **$N = 468$** | $78$ / stratum | $85.825\%$ ($85.83\%$) | $84.74\%$ | $86.91\%$ | **PASS** | **FAIL** | **NON-COMPLIANT** |
| **$N = 540$** | $90$ / stratum | $90.40\%$ | $89.49\%$ | $91.31\%$ | **PASS** | **PASS** | **COMPLIANT ONLY UNDER BASELINE ASSUMPTIONS** |

### 4.2 Prominent Power-Rule Consequences

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
PRACTICAL CONSEQUENCE OF POWER-GATE AUDIT:
If the primary confirmatory analysis uses only Common Voice and the existing eligibility ceiling
remains unchanged:
1. N=450 fails both Rule A and Rule B under the existing simulation.
2. N=468 passes Rule A but fails Rule B under that simulation.
3. N=540 cannot be drawn from Common Voice alone due to the Irish-pool ceiling (78 speakers available
   vs. 90 required), and its previous power estimate belongs to a pooled single-source model that
   does not establish power for the decoupled two-tier architecture.
CONCLUSION: NO CURRENTLY LISTED COMMON VOICE-ONLY SAMPLE-SIZE CANDIDATE HAS DEMONSTRATED COMPLIANCE
WITH BOTH MANDATORY RULES UNDER THE EXISTING SIMULATION RESULTS.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

- **Rule B Cannot Be Silently Dropped:** Adopting $N=468$ by waiving Rule B is not a valid approval under unchanged rules. It constitutes a formal protocol amendment requiring documented supervisor justification and approval.
- **Two-Tier Architecture Power is Unvalidated:** If Tier 1 consists of 450 Common Voice speakers, that primary trial has an estimated power of only $84.50\%$, failing both rules. A new, design-specific power simulation is required.

---

## 5. Task 5: Evidence-Qualified External Quality Predicate

The external speech quality filter predicate remains formally designated as:
> **`V_ext = PROPOSED — NOT APPROVED FOR CONFIRMATORY SCREENING`**

| Criterion / Measure | Proposed Threshold | Operational Pipeline Definition | Rationale & Evidence | Potential Failure Modes | Accent-Dependent Exclusion Risk | Calibration Requirements | Supervisor Decision |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **WADA-SNR** | $\ge 12.0\text{ dB}$ | Waveform Amplitude Distribution Analysis SNR estimator ($dB$). | Proposed heuristic from speech enhancement literature (Kim & Stern, 2008). Not a universal standard. | False rejection: quiet speakers in low-noise rooms. False acceptance: non-stationary noise. | **UNASSESSED RISK:** Differential exclusion across acoustic environments must be measured. | Evaluate SNR distribution on authorized development data. | **Approve, tune threshold, or defer to dev audit.** |
| **Digital Clipping** | $< 0.1\%$ of samples | Ratio of samples where $|x[n]| \ge 0.999$ over total samples. | Rejects severe ADC saturation that creates harmonic distortion in acoustic features. | False rejection: loud plosives. False acceptance: clipped audio that was re-normalized. | Low accent bias; primarily reflects recording hardware gain staging. | Verify that candidate audio has not undergone lossy peak normalization. | **Approve as standard acoustic check.** |
| **Speech Duration** | $1.0\text{s} \le t \le 15.0\text{s}$ | Non-silent duration from Voice Activity Detection (VAD). | Ensures sufficient phonetic context for adaptation without exceeding CTC model receptive fields. | False rejection: short valid phrases. False acceptance: long unsegmented pauses. | Slight risk: may affect slower speech rates in non-native speakers. | Align VAD parameters with Stage 5 prequential pipeline windowing. | **Approve duration bounds.** |
| **Forced-Alignment Confidence** | $\ge 0.80$ | Mean phoneme posterior probability from frozen pre-trained aligner. | Proposed proxy to replace Common Voice voting by verifying transcript matches audio. | Rejection of valid speech with dialectal or non-native phonological variations. | **SEVERE HYPOTHESIZED RISK:** Automated forced aligners trained on standard US/UK English may assign lower scores to South Asian or Irish speech! | **MANDATORY CALIBRATION:** Must measure false rejection rates across all 6 accents on dev data before adoption. | **REJECT AS FIXED THRESHOLD; calibrate empirically or require manual reference audit.** |

*Transcript Verification Method:* Character Error Rate (CER) cannot substitute for forced-alignment confidence because CER measures text-to-text edit distance, conflating transcription error with ASR model error. Independent transcript verification requires human-verified reference splits or double-pass validation with an independent high-capacity model on development data.

---

## 6. Task 6: Corrected Provenance and Working-Tree Statement

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
CORRECTED REPOSITORY PROVENANCE & WORKING-TREE STATEMENT:
The six audited baseline paths (reports/stage5/external_speaker_inventory.csv,
datasets/splits/stage5_external_eval.csv, datasets/splits/stage5_sentinel_panel.csv,
datasets/splits/stage5_sentinel_panel_manifest.json, datasets/splits/stage4_characterization.csv,
datasets/splits/calibration.csv) have no reported working-tree modifications, and their
LF-normalized content matches the corresponding Git blobs. This establishes current content
parity but does not establish that no temporary, uncommitted edits occurred and were
subsequently reverted.

The untracked simulation JSON (reports/stage6m/power_simulation_results.json) retains its reported
size and SHA-256 digest. Because it is untracked in Git, its historical immutability and execution
provenance remain unverified.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 7. Deliverable: Changed-versus-Untouched File Inventory

| File Path | Status in this Audit Pass | Epistemic Role & Verification Status |
| :--- | :---: | :--- |
| [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md) | **UPDATED** | Master methodological audit report (reconciled counts, provenance, and power) |
| [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md) | **UPDATED** | Master briefing & revised supervisor decision sheet |
| [`stage6m_design_consistency_memo.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_consistency_memo.md) | **UPDATED** | Sample-size nomenclature, power-rule compliance, Two-Tier proposal |
| [`stage6m_external_corpus_feasibility_register.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_external_corpus_feasibility_register.md) | **UPDATED** | Targets vs. verified, 4 named / 3 candidate resources, qualified $V_{\text{ext}}$ |
| [`stage6m_hierarchical_power_analysis_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_hierarchical_power_analysis_spec.md) | **UPDATED** | Multi-corpus power unvalidated status, Rule A & B reconciliation |
| `reports/stage5/external_speaker_inventory.csv` | **AUDITED BASELINE** | Frozen baseline inventory ($6,905$ CV records; no working-tree diff, LF-normalized matches Git blob) |
| `datasets/splits/stage5_external_eval.csv` | **AUDITED BASELINE** | Frozen Replication Cohort 1 ($60$ speakers; no working-tree diff, LF-normalized matches Git blob) |
| `datasets/splits/stage5_sentinel_panel.csv` | **AUDITED BASELINE** | Frozen Sentinel Panel ($30$ speakers; no working-tree diff, LF-normalized matches Git blob) |
| `datasets/splits/stage5_sentinel_panel_manifest.json` | **AUDITED BASELINE** | Frozen Sentinel Panel manifest (no working-tree diff, LF-normalized matches Git blob) |
| `datasets/splits/stage4_characterization.csv` | **AUDITED BASELINE** | Frozen Stage 4 Characterization ($60$ speakers; no working-tree diff, LF-normalized matches Git blob) |
| `datasets/splits/calibration.csv` | **AUDITED BASELINE** | Frozen calibration data (no working-tree diff, LF-normalized matches Git blob) |
| `reports/stage6m/power_simulation_results.json` | **UNTRACKED ARTIFACT** | Canonical simulation artifact ($S=4,000, B=1,000$, SHA-256 `8fac4d32d5f8…`; historical immutability unverified) |

---

## 8. Revised Supervisor Decision Sheet

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                            REVISED STAGE 6M SUPERVISOR DECISION SHEET                                   ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ DECISION 1: STUDY ARCHITECTURE & RESOLUTION OF IDENTIFIABILITY                                         ║
║ [ ] OPTION 1A (Recommended Candidate): Adopt Two-Tier Decoupled Architecture.                          ║
│     Tier 1: Single-source Common Voice primary analysis (avoids pooling different corpus sources       │
│             in primary group comparisons; reduces between-corpus confounding without claiming causal    │
│             effects of accent).                                                                        │
│     Tier 2: Decoupled external portability benchmark (reports separately on corpora with verified       │
│             speakers; acknowledges 6-group external coverage is not yet feasible).                     │
║ [ ] OPTION 1B: Attempt Fully Crossed Multi-Corpus Factorial Design.                                     ║
│     Requires external corpora that each contain all 6 target accent groups (high acquisition barrier).  │
║ [ ] OPTION 1C: Retain Multi-Corpus Strategy A under an additive model, accepting no-interaction bounds.║
║                                                                                                        ║
║ DECISION 2: SAMPLE-SIZE DIRECTION & POWER-RULE GOVERNANCE                                              ║
║ [ ] OPTION 2A: Direct a new, design-specific power simulation for the Two-Tier Architecture             ║
│     (evaluating whether Tier 1 sample size meets both Rule A and Rule B).                              │
║ [ ] OPTION 2B: Formal protocol amendment to consider N=468 under Rule A only (waiving Rule B).         ║
│     Requires formal written justification and documented supervisor sign-off.                          │
║ [ ] OPTION 2C: Defer all sample-size decisions until Decision 1 is resolved.                           ║
║                                                                                                        ║
║ DECISION 3: CONTINGENCY RESERVE POLICY                                                                 ║
║ [ ] OPTION 3A: Policy B (Balanced 6-stratum reserve: 15 reserves/group = 90 total; shortfall: 162 ext).║
║ [ ] OPTION 3B: Policy A (Irish-focused reserve: 15 reserves for Irish only; shortfall: 102 ext).        ║
║ [ ] OPTION 3C: Defer reserve policy until candidate external speech screening yields verified speakers. ║
║                                                                                                        ║
║ DECISION 4: EXTERNAL QUALITY PREDICATE GOVERNANCE                                                      ║
║ [ ] OPTION 4A: Authorize empirical calibration of candidate V_ext(r) thresholds on development data.   ║
║ [ ] OPTION 4B: Reject forced-alignment confidence threshold; mandate independent transcript audit.     ║
║ [ ] OPTION 4C: Restrict external filtering strictly to acoustic SNR, clipping, and duration bounds.     ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```
