# Stage 6M Supervisor Decision Pack — Document 3: Hierarchical Multi-Corpus Statistical Power Specification

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_hierarchical_power_analysis_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_hierarchical_power_analysis_spec.md)  
**Parent Document:** [`stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md)  
**Methodological Audit Reference:** [`stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md)  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED** (`execution_authorized = false`)  
**Purpose:** Formal statistical specification for hierarchical multi-corpus power analysis, distinguishing additive vs. interaction models, evaluating sample-size candidates against both mandatory power rules, and defining the simulation protocol.

---

## 1. Executive Summary & Epistemic Status

Under ADR-005, statistical power for the confirmatory evaluation must be established before freezing sample size or unblinding evaluation cohorts. This document specifies the mathematical model, variance components, simulation algorithm, and decision rules required to validate statistical power.

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
POWER SPECIFICATION EPISTEMIC STATUS:
• Execution Gate: STRICT NO-GO (execution_authorized = false)
• Simulation JSON: RETAINS REPORTED SIZE & SHA-256 (Historical immutability untracked in Git; unverified)
• Multi-Corpus Power for N=540: UNVALIDATED (Baseline simulation assumed σ_corp = 0, σ_gc = 0)
• Final Sample Size: STRICTLY UNFROZEN
  - N=450 fails both Rule A (84.50% < 85%) and Rule B (83.38% < 85%)
  - N=468 passes Rule A (85.83% ≥ 85%) but fails Rule B (84.74% < 85%)
  - N=540 cannot be drawn from Common Voice alone (Irish pool ceiling = 78) and its baseline power
    estimate (90.40%) belongs to a pooled single-source model that does not transfer to the decoupled design.
  - CONCLUSION: No currently listed Common Voice-only sample-size candidate has demonstrated
    compliance with both mandatory rules under the existing simulation results.
• Mandatory Power Rules: Rule A (Point Estimate ≥ 85%) & Rule B (Lower 95% MC Bound > 85%) preserved
• Sensitivity Parameter Ranges: ANALYST-SELECTED ASSUMPTIONS (Not empirical estimates)
• Classification: DRAFT SPECIFICATION PENDING SUPERVISOR AUTHORIZATION TO SIMULATE
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 2. Reconciling Sample-Size Candidates Against Mandatory Power Rules

ADR-005 mandates two distinct, non-negotiable power criteria:
- **Rule A (Point Estimate Criterion):** Estimated joint power $\widehat{P}_{\text{joint}} \ge 85.00\%$.
- **Rule B (Confidence Bound Criterion):** Lower bound of the 95% Monte Carlo confidence interval $L_{95\%, \text{MC}} > 85.00\%$.

The canonical simulation results serialized in [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) ($S=4,000, B=1,000$, SHA-256 `8fac4d32d5f8…`) report:

| Active Sample Size ($N_{\text{active}}$) | Stratum Allocation ($n_{\text{active}, g}$) | Estimated Joint Power ($\widehat{P}_{\text{joint}}$) | Lower 95% MC Bound ($L_{95\%, \text{MC}}$) | Upper 95% MC Bound ($U_{95\%, \text{MC}}$) | Rule A ($\widehat{P} \ge 85\%$) | Rule B ($L_{95\%} > 85\%$) | Compliance Verdict under Unchanged Rules |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$N = 450$** | $75$ / stratum | $84.50\%$ | $83.38\%$ | $85.62\%$ | **FAIL** | **FAIL** | **NON-COMPLIANT** |
| **$N = 468$** | $78$ / stratum | $85.825\%$ ($85.83\%$) | $84.74\%$ | $86.91\%$ | **PASS** | **FAIL** | **NON-COMPLIANT** |
| **$N = 540$** | $90$ / stratum | $90.40\%$ | $89.49\%$ | $91.31\%$ | **PASS** | **PASS** | **COMPLIANT ONLY UNDER BASELINE ASSUMPTIONS** |

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
PRACTICAL POWER-GATE CONCLUSION:
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

### Critical Findings:
1. **Rule B Cannot Be Silently Waived:** Adopting $N_{\text{active}} = 468$ by dropping Rule B is **not a valid approval under unchanged rules**. It constitutes a formal protocol amendment requiring documented supervisor justification and approval.
2. **$N=540$ Power Does Not Transfer to Decoupled Architecture:** If the Two-Tier Decoupled Architecture is adopted, the primary trial evaluates $N=450$ (or $468$) Common Voice speakers. Under the existing simulation, $N=450$ achieves only $84.50\%$ joint power (failing both rules).
3. **Decoupled Power is Unvalidated:** A targeted, design-specific power simulation is required before any sample-size decision is finalized.

---

## 3. Hierarchical Data-Generating Process & Identifiability

### 3.1 Model Formulation

Let $i \in \{1,\dots,N\}$ index speakers, $g(i) \in \{1,\dots,6\}$ denote accent group, and $c(i) \in \{1,\dots,K\}$ denote speech corpus. The speaker-level paired Word Error Rate difference between baseline Wav2Vec2-Base and continually adapted DSG-CTTA is modeled as:
$$\Delta_{g,c,s} = \beta_0 + \alpha_g + \gamma_c + u_{g,c} + v_s + \bar{\epsilon}_{g,c,s}$$
where:
- $\beta_0$: Grand mean adaptation effect across all conditions.
- $\alpha_g$: Accent-group main effect ($\sum_{g=1}^6 \alpha_g = 0$).
- $\gamma_c$: Corpus main effect ($\sum_{c=1}^K \gamma_c = 0$).
- $u_{g,c}$: Accent-by-corpus interaction deviation.
- $v_s \sim \mathcal{N}(0, \sigma_{\text{spk}}^2)$: Speaker-level random intercept capturing individual vocal variation.
- $\bar{\epsilon}_{g,c,s} \sim \mathcal{N}(0, \sigma_{\epsilon}^2 / C_s)$: Residual clip-level paired estimation error ($C_s \ge 15$).

### 3.2 Additive vs. Interaction Identifiability

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              IDENTIFIABILITY ANALYSIS UNDER SPARSE DESIGNS                             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CASE 1: ADDITIVE MODEL ASSUMPTION (No Interaction: u_gc = 0)                                           │
│   E[Δ_gc] = β_0 + α_g + γ_c                                                                            │
│   • Common Voice spans all 6 groups, providing a bridge that identifies group contrasts:               │
│     E[Δ_g,CV] - E[Δ_g',CV] = α_g - α_g'.                                                               │
│   • For external sources, subtracting the CV cell mean identifies corpus main effects:                 │
│     E[Δ_g,c] - E[Δ_g,CV] = γ_c - γ_CV.                                                                 │
│   • Identifiable, but relies entirely on the strong assumption of zero interaction.                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CASE 2: INTERACTION MODEL (u_gc ≠ 0)                                                                   │
│   E[Δ_gc] = β_0 + α_g + γ_c + u_gc                                                                     │
│   • In sparse designs where each external corpus supplies only one group, external contrasts           │
│     are completely confounded:                                                                         │
│     E[Δ_Aus,AusTalk] - E[Δ_SA,IndicTIMIT] = (α_Aus - α_SA) + (γ_AusTalk - γ_IndicTIMIT) + (u_Aus - u_SA)│
│   • Subtracting CV yields a difference-in-differences isolating the corpus-plus-interaction shift,      │
│     but CANNOT separate corpus main effects from group-by-corpus interactions.                         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Methodological Scope: Observational Categories

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
CORRECTED METHODOLOGICAL SCOPE:
The single-source Common Voice design avoids pooling different corpus sources in the primary
group comparisons. It reduces between-corpus confounding but does NOT eliminate potential
confounding from within-corpus recording conditions, speaker composition, or other group-associated
factors. Accent categories are observational groupings, not randomized experimental treatments.
Disparities must be reported as empirical group performance differences, NOT isolated causal effects.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 4. Parameter Sensitivity Grid (Analyst Assumptions)

To evaluate statistical robustness across potential multi-corpus structures, the simulation specification evaluates power across a multidimensional sensitivity grid. 

> [!IMPORTANT]
> The parameter ranges below are **analyst-selected assumptions** chosen for sensitivity exploration, not empirically estimated parameters from external data.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              PARAMETER SENSITIVITY GRID SPECIFICATION                                  │
├───────────────────────────────┬──────────────────────────┬─────────────────────────────────────────────┤
│ Parameter Dimension           │ Baseline Assumption      │ Sensitivity Stress-Test Grid                │
├───────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────┤
│ Corpus Variance (σ_corp)      │ 0.0 pp (Single-source)   │ [0.0, 0.5, 1.0, 1.5, 2.0] pp                │
├───────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────┤
│ Group×Corpus Variance (σ_gc)  │ 0.0 pp (Additive model)  │ [0.0, 0.25, 0.5, 1.0] pp                    │
├───────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────┤
│ Speaker Variance (σ_spk)      │ 3.8 pp (Stage 4 char.)   │ [2.5, 3.2, 3.8, 4.5, 5.0] pp                │
├───────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────┤
│ Pre/Post Correlation (ρ)      │ 0.88 (Stage 4 char.)     │ [0.75, 0.80, 0.88, 0.92, 0.95]              │
├───────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────┤
│ Clip Count per Speaker (C_s)  │ 15 clips (Approved rule) │ Fixed at C_s = 15                           │
├───────────────────────────────┼──────────────────────────┼─────────────────────────────────────────────┤
│ Disparity Margin (δ_disp)     │ 2.0 pp (ADR-005 frozen)  │ Fixed at δ_disp = 2.0 pp                    │
└───────────────────────────────┴──────────────────────────┴─────────────────────────────────────────────┘
```

---

## 5. Monte Carlo Simulation Protocol

The simulation execution protocol preserves exact reproducibility:
1. **Monte Carlo Replications:** $S = 4,000$ synthetic trials per design cell.
2. **Bootstrap Resamples:** $B = 1,000$ paired resamples per trial.
3. **Seed Formula:** $\text{seed} = 42 + N + 1000 \cdot \text{sc\_id}$, where $\text{sc\_id} \in \{1, 2, 3, 4\}$.
4. **Primary Estimands & Decision Rules:**
   - **Hypothesis 1 (Marginal WER Improvement):**  
     $H_{0,1}: \mu_{\Delta} \le 0 \quad \text{vs.} \quad H_{1,1}: \mu_{\Delta} > 0$.  
     Reject $H_{0,1}$ iff paired $t$-test achieves $p < 0.05$ and mean adaptation effect $\bar{\Delta} > 0$.
   - **Hypothesis 2 (Subgroup Disparity Protection):**  
     $H_{0,2}: \exists g \in \{1,\dots,6\} \text{ s.t. } \Delta_g < -\delta_{\text{disp}} \quad \text{vs.} \quad H_{1,2}: \Delta_g \ge -\delta_{\text{disp}} \quad \forall g$.  
     Reject $H_{0,2}$ iff for all 6 strata, the Adjusted Upper Confidence Bound satisfies:
     $$\text{Adjusted UCB}_{97.5\%, g} \le \delta_{\text{disp}} = 2.0\text{ pp}$$
     where $\text{Adjusted UCB}_{97.5\%, g} = \text{Bootstrap UCB}_{97.5\%}(\text{WER}_{\text{post}, g} - \text{WER}_{\text{pre}, g})$.
   - **Joint Power:**  
     $$\widehat{P}_{\text{joint}} = \frac{1}{S} \sum_{s=1}^S \mathbf{1}(\text{Reject } H_{0,1} \land \text{Reject } H_{0,2})$$
   - **Mandatory Criteria:** Rule A ($\widehat{P} \ge 85.00\%$) AND Rule B ($L_{95\%, \text{MC}} > 85.00\%$).

---

## 6. Actionable Supervisory Decisions

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                          POWER SPECIFICATION SUPERVISORY DECISION SHEET                                ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ [ ] DECISION 1: Authorize targeted power simulation for Tier 1 of Two-Tier Architecture               ║
│     Simulate N_active = 450 and N_active = 468 under single-source Common Voice parameters to          │
│     determine whether either candidate can satisfy both Rule A and Rule B under refined assumptions.    │
║ [ ] DECISION 2: Authorize multi-corpus hierarchical power simulation                                   ║
│     Simulate N_active = 540 across the sensitivity grid (σ_corp ∈ [0, 2] pp, σ_gc ∈ [0, 1] pp) to      │
│     determine power degradation under multi-corpus heterogeneity.                                      │
║ [ ] DECISION 3: Consider formal protocol amendment regarding Rule B                                    ║
│     Evaluate whether N_active = 468 may be accepted under Rule A alone, requiring formal documented    │
│     justification and sign-off.                                                                        │
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```
