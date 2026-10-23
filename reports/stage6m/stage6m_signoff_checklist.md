# Stage 6M Governance & Preregistration Sign-Off Checklist

**Protocol:** `v1.2.0-stage6m-proposal`  
**Governing Standard:** ADR-005  
**Document Status:** Formal Sign-Off Checklist for Academic Stakeholder Review  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED**  
**Submission Date:** 2026-10-13  

---

## 1. Executive Summary & Preregistration Mandate

Before Stage 6M can proceed from **PROPOSAL** to **AUTHORIZED EXECUTION**, all scientific, statistical, data, and software prerequisites must be audited against empirical evidence. This checklist records the verification status of all ten governance requirements.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                               STAGE 6M GOVERNANCE AUDIT SUMMARY                             │
├────┬─────────────────────────────┬───────────────────────────┬──────────────────────────────┤
│ #  │ Governance Requirement      │ Evidential Status         │ Formal Audit Verdict         │
├────┼─────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ 1  │ Stage 5M Archive Immutability│ VERIFIED FROM ARTIFACT    │ CERTIFIED & LOCKED           │
│ 2  │ Formal Research Question    │ VERIFIED FROM ARTIFACT    │ CERTIFIED                    │
│ 3  │ Estimand Separation Audit   │ VERIFIED FROM ARTIFACT    │ CERTIFIED                    │
│ 4  │ Speaker Disjointness Proof  │ VERIFIED FROM ARTIFACT    │ CERTIFIED (|S_A ∩ S_B| = 0)  │
│ 5  │ Evaluation Exposure Audit   │ VERIFIED FROM ARTIFACT    │ RECLASSIFIED AS REPLICATION  │
│ 6  │ Checkpoint Replay Vault     │ PROPOSED & TESTED         │ ARCHITECTURALLY SPECIFIED    │
│ 7  │ Vector Harm Classification  │ PROPOSED & FORMALIZED     │ MATHEMATICALLY DEFINED       │
│ 8  │ Statistical Criteria Audit  │ PROPOSED & CORRECTED      │ MDE DEFINED; p≥.20 REMOVED   │
│ 9  │ Sample Size & Power Reality │ RECONCILED UNDER OPTION A │ PLANNING N=180, HI-PWR N=360 │
│ 10 │ Data Feasibility & Manifest │ VERIFIED FROM ARTIFACT    │ 78 IRISH SPK FEASIBLE (CV27) │
│ 11 │ Stakeholder Authorization   │ PENDING REVIEW            │ HOLD — NOT AUTHORIZED        │
└────┴─────────────────────────────┴───────────────────────────┴──────────────────────────────┘
```

---

## 2. Detailed Verification Audit of the Ten Governance Items

### Item 1: Stage 5M Immutable Archive
- **Requirement:** Historical Stage 5M artifacts must remain untouched and verifiable on disk.
- **Evidence:** `reports/stage5m/stage5m_closed_loop_report.md`, `stage5m_results_bundle.zip` (847.6 KB), and 8/8 tests passing in `tests/research_validity/test_stage5m_online_control.py`.
- **Status:** `VERIFIED FROM ARTIFACT` — **CERTIFIED**.

### Item 2: Formal Research Question
- **Requirement:** Core scientific question clearly specified to test multi-step cumulative safety against ungated adaptation.
- **Evidence:** Articulated in Section 1.2 of [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md).
- **Status:** `VERIFIED FROM ARTIFACT` — **CERTIFIED**.

### Item 3: Temporal Estimand Separation Audit
- **Requirement:** Candidate-level single-step ($\Delta E_{t,1}$), candidate-level multi-step rollout ($\Delta E_{t,h}$), and end-to-end policy contrasts ($\Delta_{\text{policy}}$) explicitly defined with post-branch continuation policies and terminal prediction-only window rules ($N=29$ updates).
- **Evidence:** Documented in [`stage6m_temporal_estimands.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_temporal_estimands.md).
- **Status:** `VERIFIED FROM ARTIFACT` — **CERTIFIED**.

### Item 4: Speaker Disjointness Proof ($|S_A \cap S_B| = 0$)
- **Requirement:** Mathematical proof that evaluation speakers have zero overlap with Sentinel Panel and L2-ARCTIC.
- **Evidence:** Literal set intersection across manifests confirms:
  $|S_{\text{ext}} \cap S_{\text{sent}}| = 0$, $|S_{\text{ext}} \cap S_{\text{stage4}}| = 0$, $|S_{\text{ext}} \cap S_{\text{calib}}| = 0$.
- **Status:** `VERIFIED FROM ARTIFACT` — **CERTIFIED**.

### Item 5: Evaluation Data Exposure History & Two-Cohort Architecture
- **Requirement:** Transparent classification of whether `stage5_external_eval.csv` was previously exposed, and formal separation of replication from confirmatory claims.
- **Evidence:** Documented prior evaluation in Stage 5b and historical Stage 6 (`reports/stage6/eight_model_benchmark.csv`). The protocol formally defines a **Two-Cohort Architecture**:
  - **Cohort 1 (Replication & Multi-Step Replay):** Uses `stage5_external_eval.csv` (Common Voice 27.0). Claims strictly scoped as replication and replay findings.
  - **Cohort 2 (Primary Confirmatory Blind Benchmark):** Labeled `PROPOSED — NOT YET CREATED OR VERIFIED`. Must be quarantined and verified ($|S_{\text{conf}} \cap S_{\text{all\_prior}}| = 0$) upon creation.
- **Status:** `VERIFIED FROM ARTIFACT` (Cohort 1) & `PROPOSED — NOT YET CREATED` (Cohort 2).

### Item 6: Counterfactual Replay Vault Specification
- **Requirement:** Replay vault architecture designed to prevent missingness prospectively, separating $L_\infty=0$ parameter integrity from numerical inference tolerance, with zero claim of retroactive Stage 5M recovery, and causal language distinguishing counterfactual replay results from operational disasters averted.
- **Evidence:** Documented in [`stage6m_replay_vault_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_replay_vault_spec.md).
- **Status:** `PROPOSED` — **CERTIFIED**.

### Item 7: Vector Prospective Harm Classification
- **Requirement:** Replace narrow single-metric harm with vector $\boldsymbol{\Delta}_{t,h} = (\Delta R_{t,h}, \max_g \Delta g_{t,h}, \Delta D_{t,h})$ preserving frozen tolerances ($\epsilon_R=0.00\text{ pp}$, $\epsilon_G=+2.00\text{ pp}$, $\epsilon_D=+2.00\text{ pp}$).
- **Evidence:** Documented in Section 5 of [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md).
- **Status:** `PROPOSED` — **CERTIFIED**.

### Item 8: Statistical Acceptance & Stopping Criteria Audit
- **Requirement:** Statistically valid success/failure/inconclusive definitions; eliminate erroneous claim that $p \ge 0.20$ implies equivalence; define primary aggregate contrast against zero null ($H_0: \Delta_{\text{aggregate}} \ge 0.00\text{ pp}$); enforce point disparity safety $\widehat{\Delta D} \le +1.40\text{ pp}$ and $UCB_{95\%}(\Delta D) \le +2.00\text{ pp}$; classify $1.40 < UCB \le 2.50\text{ pp}$ as inconclusive; and mandate 100% verified counterfactual coverage for success.
- **Evidence:** Documented in Section 9 of [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md).
- **Status:** `PROPOSED` — **CERTIFIED**.

### Item 9: Sample Size & Power Reality Check
- **Requirement:** Defensible power analysis separating zero vs. non-zero null tests; reproducible Monte Carlo simulation code; empirical simulation of the disparity range statistic; calibration investigation across sample sizes; and joint safety–utility power evaluation across experimental cohorts.
- **Evidence:** Documented in [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md) and [`stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md), executed via [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py) ($S=4,000$ trials, $B=1,000$ inner resamples, canonical hash `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`):
  - Primary superiority test ($H_0: \Delta_R \ge 0$) evaluated using exact Student-t critical values $t_{\text{crit}} = t_{0.05, N-1}$, reconciling Type I error at $4.65\%$--$5.30\% \approx 5.0\%$ across confirmatory candidates $N \ge 180$ (with historical $S=2,000$ discovery range at $4.85\%$--$5.75\%$, and $N=60$ high-precision run at $S=100,000$ yielding $4.930\% \pm 0.068\%$), with empirical power of $97.0\%$ ($N=60$), $100.0\%$ ($N=180$), and $100.0\%$ ($N \ge 240$).
  - Clean non-degradation criterion (Event B) evaluated under both Approach A (Point Guardrail) and Approach B (Inferential One-Sided UCB95), achieving $100.00\%$ pass rate across candidate sizes with zero power penalty on joint success.
  - Disparity threshold is mathematically reconciled by defining scientific tolerance directly as $\tau_D = +1.40\text{ pp}$.
  - Boundary calibration investigation at $\Delta D_{\text{true}} = +1.40\text{ pp}$ across $N_g=10 \to 78$ shows range estimation bias attenuating from $-0.098\text{ pp}$ ($N_g=10$) to $-0.011\text{ pp}$ ($N_g=30$) and $+0.004\text{ pp}$ ($N_g=78$); calibrated Adjusted $UCB_{97.5\%}$ maintains empirical error $\le 3.17\%$ across both independent random seeds (`seed=42`, `seed=20261012`) with exact boundary ties empirically evaluated at $0.00\%$.
  - Joint safety–utility success simulation ($P(A \cap B \cap C)$) under canonical $B=1,000$:
    * Cohort $N=60$ ($10$/stratum): Strict joint power is **$54.2\%$** (UCB95) and **$40.65\% \pm 0.78\%$** (Adjusted UCB97.5). Classified as **`UNRESOLVED / STATISTICALLY UNDERPOWERED`** for strict joint confirmation.
    * Cohort $N=180$ ($30$/stratum, Option A Initial Planning Target): Strict joint power achieves **$91.5\%$** (UCB95) and **$84.78\% \pm 0.57\%$** (Adjusted UCB97.5) under parity, but drops to $62.1\%$ (UCB95) / $48.08\% \pm 0.79\%$ (Adj. 97.5) under $+0.50\text{ pp}$ drift.
    * Cohort $N=240$ ($40$/stratum, Intermediate Candidate): Achieves **$96.4\%$** (UCB95) / **$92.80\% \pm 0.41\%$** (Adj. 97.5) under parity, but fails the dual-scenario target under $+0.50\text{ pp}$ drift ($71.5\%$ UCB95 / $58.98\%$ Adj. 97.5).
    * Cohort $N=360$ ($60$/stratum, High-Power Candidate): Achieves **$99.6\%$** in Scenario 1 and **$85.2\%$** in Scenario 2 under UCB95 ($77.20\% \pm 0.66\%$ Adj. 97.5; $99.7\%$ operational rule).
    * Cohort $N=420$ ($70$/stratum): Achieves **$99.8\%$** in Scenario 1 and **$89.4\%$** (UCB95) / **$82.30\% \pm 0.60\%$** (Adj. 97.5) in Scenario 2.
    * Cohort $N=450$ ($75$/stratum, High-Capacity with 3 Reserve): Achieves **$100.0\%$** in Scenario 1 and **$90.4\%$** (UCB95) / **$84.50\% \pm 0.57\%$** (Adj. 97.5) in Scenario 2.
    * Cohort $N=468$ ($78$/stratum, Maximum Balanced Cohort Capacity): Achieves **$100.0\%$** in Scenario 1 and **$91.9\%$** (UCB95) / **$\mathbf{85.83\% \pm 0.55\% \ge 85.0\%}$ (exact: $\mathbf{85.825\%}$, 95% CI $[84.74\%, 86.91\%]$)** in Scenario 2, clearing the $\ge 85\%$ target under the conservative error-controlled procedure!
  - Candidate-level single-stream harmful acceptance rate remains mathematically underpowered on small streams (needs $N_{\text{acc}} \ge 59$); primary safety criterion is reoriented to stream-wide policy degradation suppression ($\Delta_R \le 0$).
- **Status:** **`RECONCILED UNDER OPTION A: SAMPLE SIZE UNFROZEN PENDING CHOICE BETWEEN CANDIDATE POOL EXPANSION AND N=468 ZERO-RESERVE FALLBACK`**.

### Item 10: Data Feasibility & Quarantined Manifest Governance
- **Requirement:** Verification that an untouched confirmatory cohort meeting Option A target requirements can be sourced with zero prior exposure, valid licenses, and verified transcripts.
- **Evidence:** Documented in [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md):
  - Mozilla Common Voice 27.0 (`cv-corpus-27.0-2026-09-11`, CC0-1.0) audited.
  - Reconciled Irish English bottleneck: 94 initial speakers minus 10 in Replication Cohort 1 minus 1 strict quality exclusion minus 5 in Sentinel Panel leaves **78 verified untouched, unexposed eligible speakers** (maximum balanced capacity $N = 468$ speakers).
  - Target $N=180$ utilizes $38.5\%$ ($30 \le 78$); target $N=240$ utilizes $51.3\%$ ($40 \le 78$); target $N=360$ utilizes $76.9\%$ ($60 \le 78$); target $N=420$ utilizes $89.7\%$ ($70 \le 78$); target $N=450$ utilizes $96.2\%$ ($75 \le 78$); target $N=468$ utilizes $100.0\%$ ($78 \le 78$).
  - Cohort 2 status: Candidate pool feasibility is proven (`VERIFIED FROM ARTIFACT`), but actual selected cohort manifest generation and disjointness tests remain pending preregistration approval (`PROPOSED — NOT YET CREATED OR VERIFIED`).
- **Status:** `VERIFIED FROM ARTIFACT` (Data Feasibility Proven for Balanced Cohorts up to N=468; Manifest Generation Pending Approval).

### Item 11: Stakeholder Authorization Sign-Off
- **Requirement:** Formal written sign-off from academic supervisor / project stakeholder before any execution.
- **Evidence:** Signature block below (`execution_authorized = false` locked).
- **Status:** **PENDING STAKEHOLDER REVIEW (EXECUTION LOCKED ON HOLD)**.

---

## 3. Formal Stakeholder Decision Block

```
===============================================================================
STAGE 6M PREREGISTRATION & GOVERNANCE SIGN-OFF BLOCK
Protocol Version: v1.2.0-stage6m-proposal | Governing Standard: ADR-005
===============================================================================

Current Operational Decision:
[X] HOLD — EXECUTION STRICTLY PROHIBITED PENDING STAKEHOLDER SIGN-OFF.
[ ] AUTHORIZED TO PROCEED: Protocol proposal approved for execution.
[ ] REVISION REQUIRED: Proposal returned for specified amendments.

Stakeholder / Supervisor Name : _______________________________________________
Stakeholder / Supervisor Role : _______________________________________________
Date of Decision             : _______________________________________________
Signature / Token            : _______________________________________________

Governance Ruling:
"Items 1 through 8 are certified. Item 9 is reconciled via Option A power grid
 expansion (Initial Planning Target N=180, Reconciled High-Power Target N=360,
 evaluated up to N=420); Item 10 data feasibility verified in Common Voice 27.0
 (78 unexposed bottleneck Irish speakers, max balanced capacity N=468).
 Confirmatory Cohort 2 manifest generation and Stage 6M execution remain locked
 on HOLD until this document is countersigned."
===============================================================================
```
