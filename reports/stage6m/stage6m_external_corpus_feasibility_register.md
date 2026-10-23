# Stage 6M Supervisor Decision Pack — Document 2: External Corpus Feasibility Register

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_external_corpus_feasibility_register.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_external_corpus_feasibility_register.md)  
**Parent Document:** [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md)  
**Methodological Audit Reference:** [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED** (`execution_authorized = false`)  
**Purpose:** Forensic feasibility evaluation of external candidate speech corpora, distinguishing planned targets from verified speakers, reconciling resource counts, separating source characteristics from accent provenance, establishing non-CV quality control criteria, and assessing cross-corpus overlap.

---

## 1. Executive Summary & Epistemic Status

Under ADR-005, evaluating the cross-corpus generalization and out-of-distribution robustness of continual test-time adaptation requires independent speech evaluation data. However, strict scientific governance dictates that **no external audio may be ingested, decoded, or screened until the university research supervisor approves the source register and eligibility criteria**.

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
EXTERNAL CORPUS REGISTER EPISTEMIC STATUS:
• Confirmatory Acquisition Gate: STRICT NO-GO (execution_authorized = false)
• Physical Audio Ingested: ZERO (0 external audio files in workspace)
• External Inventory Status: ZERO (reports/stage5/external_speaker_inventory.csv is 100% Common Voice)
• Named External Resources in Proposed Allocation: 4 (AusTalk, LibriTTS-R, OpenSLR 83, IndicTIMIT)
• Candidate Sources Retained for Investigation: 3 (AusTalk, OpenSLR 83, IndicTIMIT)
• Resources with Verified Eligible External Speakers: 0
• 90 External Evaluation Speakers: PROPOSED PLANNING TARGET ONLY (UNACQUIRED / UNVERIFIED)
• External Portability Coverage: Six-group external coverage NOT yet feasible on current evidence
• Non-CV Quality Filter: PROPOSED — NOT APPROVED FOR CONFIRMATORY SCREENING
• Cross-Corpus Overlap Risk: UNASSESSED (Pending empirical hash and transcript audits)
• Decision Pack Role: DRAFT FOR PRELIMINARY METHODOLOGICAL REVIEW ONLY
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 2. Reconciled External Resource Accounting

The allocation matrix names **four distinct external resources**:
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

---

## 3. Evidence-Based Candidate Allocation Matrix

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

---

## 4. Corpus Profiles & Feasibility Evaluations

### 4.1 Australia: AusTalk
- **Institution:** Big Australian Speech Corpus Consortium / HCSNet.
- **Access / Licensing:** Academic research access via AWAU (Australian Wright Audio Unit) / ELRA license.
- **Documented Characteristics:** 861 adult speakers recorded across 15 regional Australian locations.
- **Feasibility Assessment:** High potential for genuine regional Australian English. However, data access requires academic institutional approval. Unique speakers meeting $C \ge 15$ remain **`UNVERIFIED`** until candidate audio is licensed and screened.

### 4.2 Canada: LibriTTS-R (`canada`) — Feasibility Failure
- **Institution:** Google LLC / LibriVox volunteers (Koizumi et al., Interspeech 2023).
- **Access / Licensing:** CC BY 4.0.
- **Documented Characteristics:** 585 hours of restored audiobooks across 2,456 total speakers.
- **Feasibility Assessment:** **FATAL DEFECT.** Official LibriTTS-R metadata contain **no Canadian accent tag**. The LibriVox source catalog records volunteer country only sporadically. Inferring Canadian English without narrator biographical verification is invalid: **`UNVERIFIED — DO NOT COUNT TOWARDS ACQUISITION`**.

### 4.3 England & Ireland: OpenSLR 83 (Crowdsourced UK & Ireland English)
- **Institution:** Google LLC / OpenSLR (Guevara-Rukoz et al., 2020).
- **Access / Licensing:** CC BY-SA 4.0.
- **Documented Characteristics:** High-quality crowdsourced mobile and web recordings across the UK and Ireland.
- **Feasibility Assessment:**  
  - *England Subset:* Contains thousands of lines. Unique speaker count and regional dialect mapping remain **`UNVERIFIED`**.
  - *Irish Subset:* Published documentation lists ~450 lines for Irish English male utterances. A count of 450 lines does not establish 15 unique eligible speakers ($C \ge 15$). Sourcing 15 Irish speakers meeting $C \ge 15$ from OpenSLR 83 remains **`UNVERIFIED`**.

### 4.4 South Asian English: IndicTIMIT
- **Institution:** Indian Institute of Science (IISc), Bangalore.
- **Access / Licensing:** Academic research use.
- **Documented Characteristics:** ~240 hours of read speech from 80 voice artists across 18 Indian nativities.
- **Feasibility Assessment:** The source documentation reports 80 voice artists from 18 Indian nativities. However, speaker-level mapping to the project's South Asian English group and eligibility criteria remains **`UNVERIFIED`**. English-accent group membership cannot be inferred automatically from nationality or nativity.

### 4.5 United States: LibriTTS-R (`us`)
- **Institution:** Google LLC / LibriVox.
- **Access / Licensing:** CC BY 4.0.
- **Documented Characteristics:** 585 hours across 2,456 total speakers.
- **Feasibility Assessment:** While many LibriVox readers are US-based, narrator-specific regional dialect provenance is untagged in the official metadata. Sourcing 15 verified General American speakers requires manual narrator audit: **`UNVERIFIED`**.

### 4.6 External Portability Coverage Gaps

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
CRITICAL DEFECT: EXTERNAL PORTABILITY PANEL IS NOT SIX-GROUP
The currently retained candidate sources (AusTalk, OpenSLR 83, IndicTIMIT) provide potential routes
for Australia, South Asia, and UK/Ireland only.
Because Canadian and US assignments to LibriTTS-R remain unverified, the proposed external panel
currently lacks verified external sources for two of the six target groups.
THE FULL SIX-GROUP EXTERNAL PORTABILITY BENCHMARK IS NOT YET FEASIBLE ON CURRENT EVIDENCE.
The eventual external analysis may report only groups and corpora for which suitable speakers
are actually obtained and verified. Assumed speakers must NOT be used to fill missing groups.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

### 4.7 Rejection of Ineligible Corpora
1. **GLOBE Corpus:** GLOBE V3 is derived from Mozilla Common Voice 21.0. Using GLOBE violates cross-corpus independence. Sourcing external data from GLOBE is **strictly prohibited**.
2. **Core AccentDB:** Official TFDS documentation confirms core AccentDB contains **only 8 non-native speakers** ($2$ per accent across Bangla, Hindi, Malayalam, Telugu). Core AccentDB cannot supply 15 independent speakers: **`INELIGIBLE (8 < 15)`**.

---

## 5. Non-Common Voice Quality Control Predicate

Mozilla Common Voice eligibility relies on community peer review:
$$V_{\text{CV}}(r) = \mathbf{1}(\text{up\_votes}(r) \ge 2 \land \text{down\_votes}(r) < 2)$$

Because external corpora lack up-voting metadata, an alternative acoustic and linguistic filter predicate is proposed. This predicate is formally designated as:
> **`V_ext = PROPOSED — NOT APPROVED FOR CONFIRMATORY SCREENING`**

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        PROPOSED NON-CV QUALITY CONTROL PREDICATE V_ext(r)                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ A candidate external recording r is provisionally acceptable iff ALL four conditions hold:             │
│                                                                                                        │
│   V_ext(r) = 1( WADA-SNR(r) ≥ 12.0 dB )                                                               │
│            ∧ 1( ClippingFraction(r) < 0.001 )                                                         │
│            ∧ 1( 1.0s ≤ NonSilentDuration(r) ≤ 15.0s )                                                  │
│            ∧ 1( AlignerConfidence(r) ≥ 0.80 )                                                          │
│                                                                                                        │
│ STATUS: PROPOSED — NOT APPROVED FOR CONFIRMATORY SCREENING. REQUIRES SUPERVISORY SIGN-OFF.             │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Dimension | Proposed Threshold | Operational Measurement | Methodological Evidence & Failure Modes | Bias Risk Across Accents | Calibration Requirement |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **WADA-SNR** | $\ge 12.0\text{ dB}$ | Waveform Amplitude Distribution Analysis SNR estimator. | Proposed heuristic from speech enhancement literature (Kim & Stern, 2008). Not a universal standard. Fails on soft speakers or non-stationary noise. | **UNASSESSED RISK:** Differential rejection across home vs. studio setups. | Must evaluate empirical SNR distribution on dev data. |
| **Digital Clipping** | $< 0.1\%$ of samples | Ratio of samples where $\|x[n]\| \ge 0.999$. | Prevents severe harmonic distortion in acoustic features from ADC saturation. | Low accent bias; reflects recording hardware gain staging. | Verify candidate audio has not undergone peak normalization. |
| **Speech Duration** | $1.0\text{s} \le t \le 15.0\text{s}$ | Non-silent duration from Voice Activity Detection (VAD). | Ensures sufficient context for CTTA without exceeding receptive field limits. | Slight risk: may affect slower speech rates in non-native speakers. | Align VAD parameters with Stage 5 prequential pipeline windowing. |
| **Forced-Alignment Confidence** | $\ge 0.80$ | Mean phoneme posterior probability from frozen acoustic aligner. | Proposed proxy to replace Common Voice voting by verifying transcript matches audio. | **SEVERE HYPOTHESIZED RISK:** Pre-trained aligners trained on US/UK English assign lower scores to South Asian or Irish speech! | **MANDATORY CALIBRATION:** Must measure false rejection rates across all 6 accents before adoption. |

*Transcript Verification Method:* Character Error Rate (CER) cannot substitute for forced-alignment confidence because CER measures text-to-text edit distance, conflating transcription error with ASR model error. Independent transcript verification requires human-verified reference splits or double-pass validation with an independent high-capacity model on development data.

---

## 6. Cross-Corpus Overlap Governance

To protect confirmatory replication validity, overlap risk between external candidate sources and Mozilla Common Voice 27.0 is formally designated as:
> **`OVERLAP RISK = UNASSESSED`**

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              MANDATORY CROSS-CORPUS OVERLAP AUDIT PROTOCOL                             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Before any external candidate speaker is accepted into the confirmatory pool:                         │
│ 1. Audio Bit-Stream Hash Verification:                                                                 │
│    Compute MD5 and SHA-256 digests on raw PCM audio streams; cross-reference against all 6,905 local   │
│    Common Voice audio files. Any match is an immediate disqualification.                               │
│ 2. Normalized Text Transcript Collision Audit:                                                         │
│    Normalize external text transcripts and compute collision rates against frozen Common Voice splits  │
│    to detect shared prompt sets that could cause prompt memorization.                                  │
│ 3. Contributor ID & Metadata Cross-Reference:                                                          │
│    Verify that external recording session IDs, volunteer handles, or speaker IDs do not overlap with   │
│    Common Voice client_ids.                                                                            │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Actionable Supervisory Recommendations

1. **Acknowledge External Coverage Limitation:** Recognize that a six-group external portability benchmark is not yet supported. Canadian and US external sources remain unverified.
2. **Authorize Pre-Confirmatory Access to AusTalk and OpenSLR 83:** Authorize the student to initiate academic licensing requests for AusTalk and download sample splits of OpenSLR 83 and IndicTIMIT for development screening.
3. **Reject Fixed Aligner Confidence Threshold:** Direct empirical calibration of the proposed quality filter ($V_{\text{ext}}$) on development data before applying it to confirmatory screening.
4. **Preserve Current Status:** Maintain `execution_authorized = false`. No external data may be ingested into confirmatory manifests until candidate screening is complete.
