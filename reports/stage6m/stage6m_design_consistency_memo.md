# Stage 6M Supervisor Decision Pack — Document 1: Design Consistency & Feasibility Memo

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_design_consistency_memo.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_consistency_memo.md)  
**Parent Document:** [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md)  
**Methodological Audit Reference:** [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED** (`execution_authorized = false`)  
**Purpose:** Reconcile sample-size nomenclature, evaluate sample-size candidates against mandatory power rules, analyze the Zero-Headroom Irish Common Voice constraint, and present study design options for supervisory decision.

---

## 1. Executive Summary & Epistemic Status

This memorandum addresses the critical statistical and operational dependencies governing sample-size determination, reserve policies, and multi-corpus study design in Stage 6M:
> **Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition**

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
MEMORANDUM GOVERNANCE & EPISTEMIC STATUS:
• Confirmatory Execution Gate: STRICT NO-GO (execution_authorized = false)
• Cohort 2 Manifests: UNCREATED (Creating Cohort 2 before supervisor sign-off is prohibited)
• Final Sample Size: STRICTLY UNFROZEN
  - N=450 fails both Rule A (84.50% < 85%) and Rule B (83.38% < 85%)
  - N=468 passes Rule A (85.83% ≥ 85%) but fails Rule B (84.74% < 85%)
  - N=540 cannot be drawn from Common Voice alone (Irish pool ceiling = 78) and its baseline power
    estimate (90.40%) belongs to a pooled single-source model that does not transfer to the decoupled design.
  - CONCLUSION: No currently listed Common Voice-only sample-size candidate has demonstrated
    compliance with both mandatory rules under the existing simulation results.
• Mandatory Power Rules: Rule A (Point Estimate ≥ 85%) & Rule B (Lower 95% MC Bound > 85%) preserved
• Reserve Policy: UNRESOLVED (Policy A vs. Policy B pending supervisor selection)
• Classification: DRAFT FOR PRELIMINARY METHODOLOGICAL REVIEW ONLY
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 2. Definitive Five-Variable Sample-Size Nomenclature

To permanently resolve ambiguity between active evaluation cohorts, reserve buffers, and acquisition inventories, the confirmatory protocol formally defines five distinct symbols:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DEFINITIVE SAMPLE-SIZE NOMENCLATURE                                       │
├───────────────────┬────────────────────────────────────────────────────────────────────────────────────┤
│ Variable Symbol   │ Operational Definition & Methodological Function                                   │
├───────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
│ N_active          │ Active confirmatory evaluation cohort evaluated in primary statistical tests.     │
│                   │ Evaluates H_0,1 (Marginal WER) and H_0,2 (Subgroup Disparity Protection).         │
├───────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
│ N_CV              │ Number of active evaluation speakers sourced from Mozilla Common Voice 27.0.       │
│                   │ Sourced from local pool of strictly eligible unexposed speakers.                  │
├───────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
│ N_external        │ Number of active evaluation speakers sourced from independent external corpora.    │
│                   │ Proposed planning target: 90 speakers across 6 strata (0 verified in workspace).   │
├───────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
│ N_reserve         │ Contingency buffer held in blinded reserve to replace dropped speakers.            │
│                   │ Sourced under Policy A (Irish-focused) or Policy B (Balanced 6-stratum).           │
├───────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
│ N_inventory       │ Total physical speaker acquisition inventory required before confirmatory freeze.   │
│                   │ N_inventory = N_active + N_reserve = (N_CV + N_external) + N_reserve.              │
└───────────────────┴────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Evaluating Sample-Size Candidates Against Mandatory Power Rules

ADR-005 establishes two distinct, non-negotiable power criteria:
- **Rule A (Point Estimate Criterion):** $\widehat{P}_{\text{joint}} \ge 85.00\%$.
- **Rule B (Confidence Bound Criterion):** $L_{95\%, \text{MC}} > 85.00\%$.

The canonical simulation results from [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) ($S=4,000, B=1,000$, SHA-256 `8fac4d32d5f8…`) report:

| Candidate Configuration | Stratum Allocation | Estimated Joint Power ($\widehat{P}_{\text{joint}}$) | Lower 95% MC Bound ($L_{95\%, \text{MC}}$) | Rule A ($\widehat{P} \ge 85\%$) | Rule B ($L_{95\%} > 85\%$) | Compliance Verdict under Unchanged Rules |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Candidate 1: $N_{\text{active}} = 450$** | $75$ / stratum | $84.50\%$ | $83.38\%$ | **FAIL** | **FAIL** | **NON-COMPLIANT** |
| **Candidate 2: $N_{\text{active}} = 468$** | $78$ / stratum | $85.825\%$ ($85.83\%$) | $84.74\%$ | **PASS** | **FAIL** | **NON-COMPLIANT** |
| **Candidate 3: $N_{\text{active}} = 540$** | $90$ / stratum | $90.40\%$ | $89.49\%$ | **PASS** | **PASS** | **COMPLIANT ONLY UNDER BASELINE ASSUMPTIONS** |

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
PRACTICAL POWER-GATE CONSEQUENCE:
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

### Critical Methodological Findings:
1. **Rule B Cannot Be Silently Dropped:**  
   $N_{\text{active}} = 468$ passes Rule A ($\widehat{P} = 85.83\%$), but fails Rule B ($84.74\% < 85.00\%$). Proposing to adopt $N=468$ by waiving Rule B is **not a valid approval under unchanged rules**; it represents a formal protocol amendment requiring documented supervisor justification and approval.
2. **$N=540$ Power Does Not Transfer to Decoupled Architecture:**  
   The $90.40\%$ result applies strictly to a pooled single-source Gaussian model of 540 speakers ($\sigma_{\text{corp}} = 0$). In the Two-Tier Decoupled Architecture, the primary confirmatory trial consists of $N_{\text{active}} = 450$ (or $468$) Common Voice speakers. Under the existing simulation, $N=450$ achieves only $84.50\%$ joint power (failing both rules).
3. **Decoupled Power Unvalidated:**  
   Power for the primary tier of the Two-Tier Decoupled Architecture has not been validated under compliant parameters. A targeted design-specific power simulation is required.

---

## 4. The Zero-Headroom Irish Common Voice Constraint

The total strictly eligible Irish speaker capacity in Mozilla Common Voice 27.0 is **strictly 78 unexposed speakers**:
$$\text{Available Strictly Eligible Capacity} = 92 - 14 = \mathbf{78\text{ speakers}}$$

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE ZERO-HEADROOM IRISH OPERATIONAL PARADOX                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ • Total Available Unexposed Strictly Eligible Irish CV Speakers: 78                                    │
│ • Proposed Active Irish CV Speakers Required (N_CV, ireland):     75                                    │
│ • Proposed Irish CV Contingency Reserve Required (N_reserve, ire):  3                                   │
│ • Total Irish Common Voice Commitment:                            75 + 3 = 78                          │
│ • Remaining Uncommitted Irish CV Headroom:                        78 - 78 = 0 (EXACTLY ZERO)           │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ OPERATIONAL CONSEQUENCE:                                                                               │
│ If even ONE candidate Irish CV speaker is disqualified during audio decoding, speech activity          │
│ verification, or text normalization, the Irish active cohort drops to 74 or consumes the reserve.     │
│ Sourcing a 79th Irish speaker from Common Voice 27.0 is MATHEMATICALLY IMPOSSIBLE without relaxing    │
│ the strict eligibility threshold (C_strict ≥ 15) or violating exposure blinding.                       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Contingency Reserve Policies: Policy A vs. Policy B

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CONTINGENCY RESERVE POLICY COMPARISON MATRIX                                                   │
├───────────────────────────────┬──────────────────────────────────────────┬───────────────────────────────────────────────────────┤
│ Dimension                     │ Policy A: Asymmetric Irish-Focused       │ Policy B: Balanced Six-Stratum Reserve                │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Architectural Concept         │ Concentrates reserves on the bottleneck  │ Allocates uniform contingency reserve across all six  │
│                               │ Irish stratum; relies on deep CV pools.  │ strata (15 reserve speakers per stratum).             │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Active Confirmatory Cohort    │ N_active = 540 (450 CV + 90 External)    │ N_active = 540 (450 CV + 90 External)                 │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Contingency Reserve Buffer    │ N_reserve = 15 (Irish only: 3 CV + 12 Ext│ N_reserve = 90 (15/stratum: 18 CV + 72 External)       │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Total Acquisition Inventory   │ N_inventory = 555 speakers               │ N_inventory = 630 speakers                            │
│                               │ (453 CV + 102 External)                  │ (468 CV + 162 External)                               │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ External Acquisition Target   │ 102 External Speakers                    │ 162 External Speakers                                 │
│                               │ (90 Active + 12 Irish Reserve)           │ (90 Active + 72 Balanced Reserve)                     │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Common Voice Acquisition      │ 453 CV Speakers                          │ 468 CV Speakers                                       │
│                               │ (450 Active + 3 Irish Reserve)           │ (450 Active + 18 Non-Irish Reserve)                   │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ External Feasibility Burden   │ Lower external acquisition shortfall:    │ Substantially higher external acquisition shortfall:  │
│                               │ 102 speakers required across corpora.    │ 162 speakers required across corpora.                 │
├───────────────────────────────┼──────────────────────────────────────────┼───────────────────────────────────────────────────────┤
│ Sourcing Status in Workspace  │ 0 external speakers verified/acquired;   │ 0 external speakers verified/acquired;                │
│                               │ Entire external inventory is unacquired. │ Entire external inventory is unacquired.              │
└───────────────────────────────┴──────────────────────────────────────────┴───────────────────────────────────────────────────────┘
```

---

## 6. Study Architecture Options for Supervisory Review

### Option A: Fully Crossed Multi-Corpus Factorial Design
- **Concept:** Every candidate speech corpus contains speakers from all six accent groups.
- **Identifiability:** Fully identifiable. Accent main effects, corpus main effects, and interactions can be separated.
- **Feasibility:** **Extremely difficult or infeasible** with available academic corpora. Neither AusTalk (Australia only) nor IndicTIMIT (India only) contains Canadian or UK speakers.

### Option B: Two-Tier Decoupled Architecture (Recommended Candidate)
- **Concept:** Separate the confirmatory evaluation into two scientifically rigorous, unconfounded tiers:
  - **Tier 1 (Single-Source Common Voice Primary Trial):**  
    The primary confirmatory test of disparity-aware adaptation is conducted entirely within Mozilla Common Voice 27.0 ($N_{\text{active}} = 450$ or $468$).  
    *Methodological Scope:* The single-source Common Voice design avoids pooling different corpus sources in the primary group comparisons. It reduces between-corpus confounding but does not eliminate potential confounding from within-corpus recording conditions, speaker composition, or other group-associated factors. Disparities are observational group differences, not isolated causal effects of accent.
  - **Tier 2 (Decoupled External Portability Benchmark):**  
    The frozen adapted models from Tier 1 are evaluated on independent external corpora (AusTalk, IndicTIMIT, OpenSLR 83) as out-of-distribution portability benchmarks, reported separately per corpus.  
    *Coverage Limitation:* Because Canadian and US assignments to LibriTTS-R remain unverified, **a six-group external portability panel is not yet feasible on current evidence**. The eventual external analysis may report only groups and corpora for which suitable speakers are actually obtained and verified.
- **Advantage:** Preserves internal validity of the primary confirmatory trial, eliminates flawed pooling of sparse external data, and avoids conflating source effects with accent disparities.

---

## 7. Actionable Decision Items for Supervisor Sign-Off

1. **Architecture Item:** Select between the **Two-Tier Decoupled Architecture (Option B)** and retaining the sparse additive multi-corpus model.
2. **Sample-Size Item:** Acknowledge that no CV-only sample-size candidate currently meets both mandatory power rules. Direct a targeted, design-specific power simulation, or consider a documented protocol amendment regarding Rule B.
3. **Reserve Policy Item:** Approve **Policy A** ($N_{\text{inv}}=555$, external shortfall 102) or **Policy B** ($N_{\text{inv}}=630$, external shortfall 162), acknowledging that candidate external data screening must occur before freeze.
4. **External Quality Predicate Item:** Review the proposed criteria ($V_{\text{ext}}(r)$), qualify WADA-SNR as an analyst heuristic, and direct empirical calibration on development data before applying automated forced-alignment filtering.
