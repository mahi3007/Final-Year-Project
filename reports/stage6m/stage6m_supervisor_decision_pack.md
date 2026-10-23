# Stage 6M Supervisor Decision Pack: Confirmatory Protocol Governance & Methodological Roadmap

**Project Title:** *Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition*  
**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md)  
**Methodological Audit Reference:** [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED** (`execution_authorized = false`)  
**Document Classification:** **DRAFT FOR PRELIMINARY METHODOLOGICAL REVIEW ONLY**  
**Confirmatory Gate:** Fully Closed (No audio ingestion, no model evaluation, no Cohort 2 unblinding)

---

## 1. Executive Summary & Epistemic Status

This **Stage 6M Supervisor Decision Pack** compiles the complete technical, statistical, and empirical foundation required for the university research supervisor to conduct a **preliminary methodological review** regarding the confirmatory phase of this project.

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
EPISTEMIC NOTICE FOR SUPERVISOR REVIEW:
This Decision Pack is submitted as a DRAFT FOR METHODOLOGICAL DISCUSSION. It is NOT presented
as a finalized, approved, or execution-ready confirmatory protocol. A drafted decision is not an
approved decision. Several substantive design issues—most notably accent–corpus identifiability,
external-source candidate availability, and mandatory power-rule compliance—remain unresolved and
require supervisory guidance before any sample size is frozen or external data acquired.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

The research under investigation is:
> **Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition**

The primary contribution is **not** simply demonstrating that test-time adaptation lowers overall Word Error Rate (WER). Rather, it investigates whether continual test-time adaptation can be achieved **without exacerbating performance disparities across accent groups or inducing catastrophic subgroup regressions**. 

The evaluation encompasses **six English accent groups**:
1. Australian English (`australia`)
2. Canadian English (`canada`)
3. England English (`england`)
4. Irish English (`ireland`)
5. South Asian English (`south_asian`)
6. United States English (`us`)

### Key Epistemic Findings from Supervisory Audit:
1. **No Common Voice Candidate Meets Both Mandatory Power Rules:**  
   Under the existing simulation results:
   - $N=450$ fails both Rule A ($\widehat{P} = 84.50\% < 85\%$) and Rule B ($L_{95\%} = 83.38\% < 85\%$).
   - $N=468$ passes Rule A ($\widehat{P} = 85.83\% \ge 85\%$) but fails Rule B ($L_{95\%} = 84.74\% < 85\%$).
   - $N=540$ cannot be drawn from Common Voice alone due to the Irish-pool ceiling ($78$ unexposed speakers available vs. $90$ required), and its previous power estimate ($90.40\%$) belongs to a pooled single-source model that does not establish power for the decoupled two-tier architecture.  
   **Conclusion:** No currently listed Common Voice-only sample-size candidate has demonstrated compliance with both mandatory rules under the existing simulation results. Waiving Rule B for $N=468$ requires a formal protocol amendment.
2. **External Resource Accounting Reconciled:**  
   The allocation names **4 distinct external resources** (AusTalk, LibriTTS-R, OpenSLR 83, IndicTIMIT), of which **3 remain candidate sources** for further investigation (AusTalk, OpenSLR 83, IndicTIMIT; LibriTTS-R lacks verified dialect metadata for Canada and US). Currently, **0 external speakers** are verified or acquired in the workspace. All 90 external speakers remain a planning target.
3. **Six-Group External Portability Coverage Gap:**  
   Because Canadian and US assignments to LibriTTS-R remain unverified, the proposed external panel currently identifies potential routes for only Australia, South Asia, and UK/Ireland. **A six-group external portability benchmark is NOT yet feasible on current evidence.** The eventual external analysis may report only groups and corpora for which suitable speakers are actually obtained and verified.
4. **Primary-Design Scope:**  
   The single-source Common Voice design avoids pooling different corpus sources in the primary group comparisons. It reduces between-corpus confounding but does not eliminate potential confounding from within-corpus recording conditions, speaker composition, or other group-associated factors. Disparities are observational group differences, not isolated causal effects of accent.

---

## 2. Status of the Five Confirmatory Requirements

| Requirement | Scientific Objective | Current Epistemic Status in Decision Pack | Formal Action Requiring College Supervisor Approval |
| :--- | :--- | :--- | :--- |
| **1. Formal Supervisor Preregistration** | Establish an OSF-standard confirmatory research protocol with frozen hypotheses, estimands, and exclusion rules. | Drafted in [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md). Reclassified as **UNAPPROVED DRAFT**. | Professor must review, resolve open design questions, and approve. |
| **2. Final Sample-Size Decision** | Establish an adequately powered sample size satisfying both mandatory power rules (Rule A and Rule B). | Analyzed in **Document 1** ([`stage6m_design_consistency_memo.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_consistency_memo.md)). **STRICTLY UNFROZEN**: No CV-only candidate meets both rules. Baseline $N=540$ power does not transfer to decoupled design. | Supervisor decision on design architecture and power rule governance. |
| **3. Reserve-Policy Approval** | Select Policy A (Irish-focused) or Policy B (Balanced 6-group) and establish replacement protocols. | Articulated in **Document 1** ([`stage6m_design_consistency_memo.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_consistency_memo.md)). Classified as **UNRESOLVED**. | Supervisor selection based on operational capacity and risk tolerance. |
| **4. External Speech Data Acquisition** | Sourcing independent external speech data across target accent groups without Common Voice circularity. | Structured register created in **Document 2** ([`stage6m_external_corpus_feasibility_register.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_external_corpus_feasibility_register.md)). Classified as **PROPOSED TARGETS ONLY (4 NAMED / 3 CANDIDATE SOURCES; 0 VERIFIED/ACQUIRED; OVERLAP UNASSESSED)**. | Supervisor approval of candidate sources and non-CV quality criteria. |
| **5. Multi-Corpus Hierarchical Power Validation** | Validate statistical power under true multi-corpus structure ($\sigma_{\text{corp}}, \sigma_{gc}$). | Specified in **Document 3** ([`stage6m_hierarchical_power_analysis_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_hierarchical_power_analysis_spec.md)). Classified as **SPECIFICATION COMPLETE (SIMULATION PENDING)**. | Supervisor authorization to run design-specific simulation stress-test. |

---

## 3. Guide to the Stage 6M Decision Pack Documents

### Master Methodological Audit
- **File Link:** [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)
- **Key Findings:** 
  1. Identifiability analysis: Under an additive model with no interactions, Common Voice acts as a bridge identifying main effects; under an interaction model, external corpus effects and group interactions are not independently distinguishable.
  2. Causal scope: The single-source Common Voice design avoids pooling different corpus sources in primary comparisons. It reduces between-corpus confounding but does not eliminate potential within-corpus confounding or establish a causal effect of accent.
  3. Reconciles sample sizes against mandatory power rules: $N=450$ fails both rules, $N=468$ passes Rule A but fails Rule B, and pooled $N=540$ power cannot be transferred to a decoupled two-tier design.

### Document 1: Design Consistency & Feasibility Memo
- **File Link:** [`stage6m_design_consistency_memo.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_consistency_memo.md)
- **Key Findings:**
  1. Establishes five distinct sample-size symbols: $N_{\text{active}}$, $N_{\text{CV}}$, $N_{\text{external}}$, $N_{\text{reserve}}$, $N_{\text{inventory}}$.
  2. Resolves the ambiguity of "468": clarifies that $N_{\text{active}}=468$ represents a single-source Common Voice cohort ($78$/stratum), whereas in Policy B, $468$ represents the Common Voice acquisition inventory ($450\text{ active} + 18\text{ reserve}$).
  3. Proves that a pure Common Voice cohort of $N=540$ is **physically impossible** from CV 27.0 due to the Irish stratum ceiling ($78$ unexposed speakers available vs. $90$ required).
  4. Details the **Zero-Headroom Irish Constraint**: Both Policy A and Policy B require $75\text{ active} + 3\text{ reserve} = \mathbf{78\text{ Irish CV speakers}}$, committing $100\%$ of available candidates.
  5. Presents the **Two-Tier Decoupled Architecture (Option B)** as the recommended candidate to avoid flawed pooling of confounded external data.

### Document 2: External Corpus Feasibility Register
- **File Link:** [`stage6m_external_corpus_feasibility_register.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_external_corpus_feasibility_register.md)
- **Key Findings:**
  1. Distinguishes 4 named resources from 3 retained candidate sources (AusTalk, OpenSLR 83, IndicTIMIT) and 0 verified/acquired speakers. Current repository inventory contains **zero non-Common Voice candidates**.
  2. Documents external portability gap: Canadian and US assignments to LibriTTS-R remain unverified, meaning a 6-group external panel is not yet supported.
  3. Separates source population characteristics (e.g. 80 voice artists from 18 Indian nativities in IndicTIMIT) from verified South Asian English accent provenance (`UNVERIFIED`).
  4. Reclassifies source overlap risk as **`UNASSESSED`** pending empirical cross-corpus audits.
  5. Formulates the **External Quality Predicate $V_{\text{ext}}(r)$**: Explicitly marked as **`PROPOSED — NOT APPROVED FOR CONFIRMATORY SCREENING`**. Clarifies that CER is not a substitute for transcript verification, and flags forced-alignment confidence as a potential source of selective attrition bias.

### Document 3: Hierarchical Power Analysis Specification
- **File Link:** [`stage6m_hierarchical_power_analysis_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_hierarchical_power_analysis_spec.md)
- **Key Findings:**
  1. Identifies that the serialized baseline simulation assumed zero corpus variance ($\sigma^2_{\text{corp}} = 0, \sigma^2_{gc} = 0$). Power for $N=540$ under multi-corpus heterogeneity is **UNVALIDATED**.
  2. Clarifies that the existing $N=540$ power result ($90.40\%$) does **not** transfer to a decoupled architecture where Tier 1 consists of 450 Common Voice speakers.
  3. Reconciles mandatory rules: $N=450$ fails both rules, $N=468$ fails Rule B. Proposing to accept Rule B failure is a formal protocol change requiring supervisor approval.
  4. Explicitly classifies sensitivity ranges ($\sigma_{\text{corp}} \in [0, 2]\text{ pp}$, $\sigma_{gc} \in [0, 1]\text{ pp}$, $\rho \in [0.75, 0.95]$) as **analyst-selected assumptions**, not empirical estimates.

---

## 4. Formal Supervisor Decision Sheet

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

---

## 5. Formal Submission Message for Preliminary Methodological Review

The following email draft is prepared for the student to submit along with this decision pack:

***

**Subject:** Preliminary Methodological Review: Stage 6M Decision Pack & Identifiability Audit (Disparity-Aware CTTA)

**Dear Professor [Supervisor's Name],**

I have prepared the draft **Stage 6M Supervisor Decision Pack** for my final year research project, *Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition*. 

I want to emphasize at the outset that this pack is submitted as a **draft for preliminary methodological review**, not as a finalized or execution-ready protocol. In accordance with our governance protocol, the confirmatory gate remains **strictly locked** (`execution_authorized = false`), and no confirmatory audio has been ingested or evaluated.

During my recent methodological audit ([`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)), I identified several important design challenges that I would like to discuss with you before we freeze any protocol decisions:

1. **Accent–Corpus Identifiability & Proposed Architecture:**  
   Under an additive model assuming no interactions, Common Voice acts as a bridge connecting the accent groups. However, if adaptation effects vary by accent across corpora (interaction model), external corpus effects and group interactions cannot be distinguished because each external source contributes to only one accent group. To avoid flawed pooling, I recommend the **Two-Tier Decoupled Architecture**: Tier 1 provides a single-source Common Voice primary analysis (which avoids pooling different corpus sources and reduces between-corpus confounding, without claiming causal effects of accent), while Tier 2 evaluates model portability across independent external corpora reported separately per corpus.

2. **Sample Size & Mandatory Power Rules:**  
   Our protocol specifies two mandatory rules: Rule A ($\widehat{P} \ge 85\%$) and Rule B ($L_{95\%, \text{MC}} > 85\%$). Under our baseline simulation:
   - $N=450$ fails both rules ($84.50\%$, $L_{95\%} = 83.38\%$).
   - $N=468$ passes Rule A but fails Rule B ($85.83\%$, $L_{95\%} = 84.74\%$).
   - $N=540$ cannot be drawn from Common Voice alone (Irish ceiling = 78), and its baseline power ($90.40\%$) does not transfer to the Two-Tier architecture where Tier 1 consists of 450 Common Voice speakers.  
   Therefore, **no currently listed Common Voice-only sample-size candidate has demonstrated compliance with both mandatory rules**. A new, design-specific power simulation is required.

3. **External Dataset Feasibility & Coverage Gaps:**  
   The allocation names 4 distinct external resources (AusTalk, LibriTTS-R, OpenSLR 83, IndicTIMIT), of which 3 remain candidate sources (AusTalk, OpenSLR 83, IndicTIMIT). LibriTTS-R lacks verified dialect metadata for both Canada and the US. Therefore, **a six-group external portability benchmark is not yet feasible on current evidence**. All 90 external speakers remain a planning target (0 verified or acquired in the workspace). Overlap risk with CV 27.0 is classified as `UNASSESSED`.

4. **External Quality Predicate Qualification:**  
   I have marked the external filter predicate ($V_{\text{ext}}$) as `PROPOSED — NOT APPROVED FOR CONFIRMATORY SCREENING`. I have qualified WADA-SNR $\ge 12\text{ dB}$ as an analyst-proposed heuristic requiring empirical calibration, and flagged that automated forced-alignment confidence thresholds risk introducing selective attrition bias against non-native or regional accents.

I would welcome the opportunity to discuss these findings with you and receive your guidance on the enclosed **Supervisor Decision Sheet**.

Thank you very much for your time, mentorship, and support.

**Sincerely,**  
[Student's Name]  
Final Year Research Student  
Project Repository: `mahi3007/Final-Year-Project`

***

---

## 6. Governance Verification & Artifact Integrity Ledger

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

| Document | File Path | Status | Verification Check |
| :--- | :--- | :---: | :--- |
| **Methodological Audit** | [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md) | **COMPLETE** | Reconciled counts, qualified scope, prominent power consequences, qualified provenance |
| **Supervisor Decision Pack** | [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md) | **COMPLETE** | Preliminary review briefing & updated decision sheet |
| **Document 1: Design Memo** | [`stage6m_design_consistency_memo.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_consistency_memo.md) | **COMPLETE** | Primary-design language, power-rule compliance, Two-Tier proposal |
| **Document 2: External Register** | [`stage6m_external_corpus_feasibility_register.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_external_corpus_feasibility_register.md) | **COMPLETE** | 4 named / 3 candidate resources, targets vs. verified, qualified $V_{\text{ext}}$ |
| **Document 3: Power Specification** | [`stage6m_hierarchical_power_analysis_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_hierarchical_power_analysis_spec.md) | **COMPLETE** | Rule A & B reconciliation, decoupled power unvalidated |
| **Protocol Proposal** | [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) | **REVIEWED** | Unapproved draft under ADR-005 |
| **Canonical Power JSON** | [`power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) | **UNTRACKED ARTIFACT** | Retains size and SHA-256 `8fac4d32d5f8…`; historical immutability unverified |
| **Audited Baseline Paths** | 6 tracked baseline paths in `reports/stage5/` and `datasets/splits/` | **AUDITED BASELINE** | No working-tree modifications; LF-normalized content matches Git blobs |
| **Confirmatory Execution Gate** | `execution_authorized = false` | **LOCKED** | `HOLD — STRICTLY NOT AUTHORIZED` |
