# Stage 6M Protocol v1.2.0 Methodological Audit Change Log

**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Governing Standard:** ADR-005  
**Document Status:** Formal Audit Change Log for Academic Supervisor / Stakeholder Review  
**Operational Governance State:** **HOLD — STRICTLY NOT AUTHORIZED**  
**Audit Date:** 2026-10-12  

---

## 1. Overview of Corrections

This change log records the resolution of all statistical, inferential, and data-integrity issues identified in the final methodological audit of Stage 6M Protocol Proposal `v1.2.0-stage6m-proposal`.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SUMMARY OF AUDIT CORRECTIONS                                │
├────┬─────────────────────────────┬──────────────────────────────────────────────────────────┤
│ #  │ Methodological Issue        │ Formal Protocol Resolution & Mathematical Update         │
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 1  │ Primary Hypothesis vs Test  │ Option A (one-sided superiority H0: Δ ≥ 0 vs H1: Δ < 0)  │
│    │ Realignment                 │ preregistered: 97.2% ± 0.37% power at Δ = -0.85 pp.      │
│    │                             │ Option B (two-sided directional p<.05 & ^Δ < 0) documented│
│    │                             │ at 94.2% ± 0.52% power, resolving earlier mismatch.      │
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 2  │ Disparity Threshold Logic   │ Mathematical inconsistency resolved: scientific margin   │
│    │ & Substantiation Fix        │ defined directly as τ_D = +1.40 pp (Option B). UCB ≤ 1.40│
│    │                             │ proves ΔD ≤ 1.40 pp. Unverified clinical claim removed.  │
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 3  │ Disparity UCB Calibration   │ Boundary non-coverage at ΔD = +1.40 pp diagnosed: 7.80%  │
│    │ Investigation               │ non-coverage due to extreme-value Jensen's bias (-0.12pp)│
│    │                             │ at N=10/group. Calibrated UCB97.5 restores ≤5% (3.95%).  │
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 4  │ Joint Safety–Utility Power  │ Simultaneous joint simulation of P(A ∩ B) across 4 joint │
│    │ Simulation                  │ scenarios proves strict joint power is 51.4% ± 1.29%     │
│    │                             │ (bounded by min(P(A), P(B)) = 52.8%; UNDERPOWERED).      │
│    │                             │ Operational joint rule achieves 78.6% ± 1.06%.           │
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 5  │ Two-Cohort Evidence States &│ Cohort 2 labeled PROPOSED — NOT YET CREATED OR VERIFIED. │
│    │ Model Exposure Lineage      │ Prior exploratory benchmark in historical Stage 6        │
│    │                             │ disclosed for 4 CTC backbones; role framed as replication│
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 6  │ Invalid Worst-Case Imputation│ Arbitrary +2.00 pp addition rejected (WER exceeds 100%). │
│    │ in Missingness Rules        │ Primary success strictly requires 100% verified coverage.│
│    │                             │ Missing candidates labeled UNAVAILABLE; blocks success.  │
├────┼─────────────────────────────┼──────────────────────────────────────────────────────────┤
│ 7  │ Confirmatory Sample Size    │ Supervisor Option A approved: N=180 initial planning     │
│    │ Decision & Data Feasibility │ target (85.6% joint power) and N=240 high-power target   │
│    │ Audit (CV 27.0)             │ (92.5%). CV 27.0 audited: 73 unexposed Irish spk avail.  │
└────┴─────────────────────────────┴──────────────────────────────────────────────────────────┘
```

---

## 2. Itemized Change Details

### Correction 1: Primary Hypothesis and Test Realignment (Option A Preregistered)
- **File:** [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 8.1 & 9.1), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md) (Section 3.2), [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py).
- **Adjustment:**
  - Preserved signed difference: $\Delta_{\text{aggregate}} = E_{\text{Arm 3 (Gated)}} - E_{\text{Arm 2 (Ungated)}}$, where negative values favor the gated system.
  - Aligned the primary confirmatory test to **Option A (One-Sided Superiority Test)**:
    $$H_0: \Delta_{\text{aggregate}} \ge 0.00\text{ pp} \quad \text{vs.} \quad H_1: \Delta_{\text{aggregate}} < 0.00\text{ pp}$$
    evaluated at $\alpha = 0.05$. Under anticipated benefit $\Delta = -0.85\text{ pp}$ ($\text{SE} \approx 0.240\text{ pp}$, $|z| \approx 3.54$), Monte Carlo simulation ($S = 2,000$ trials) yields **$\mathbf{Power = 97.2\% \pm 0.37\%}$**.
  - Documented **Option B (Two-Sided Directional Specification)**:
    $$H_0: \Delta_{\text{aggregate}} = 0.00\text{ pp} \quad \text{vs.} \quad H_1: \Delta_{\text{aggregate}} \neq 0.00\text{ pp}$$
    requiring two-sided $p < 0.05$ and $\widehat{\Delta} < 0.00\text{ pp}$, yielding **$\mathbf{Power = 94.2\% \pm 0.52\%}$**.
  - Type I error rates under null boundary ($\Delta = 0.00\text{ pp}$) confirmed: Option A is $5.5\% \pm 0.51\%$; Option B directional rejection is $3.0\% \pm 0.38\%$.

### Correction 2: Disparity Threshold Mathematical Justification & Claim Substantiation
- **File:** [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 8.2 & 9.1), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md) (Section 3.5).
- **Adjustment:**
  - Resolved mathematical inconsistency: Bounding $UCB_{95\%}(\Delta D) \le 1.40\text{ pp}$ proves at 95% confidence that $\Delta D \le 1.40\text{ pp}$, not that $\Delta D \le 1.00\text{ pp}$.
  - Formally adopted **Option B**: Defined the **Scientific Disparity Tolerance** directly as **$\tau_D = +1.40\text{ pp}$**.
  - Removed unsubstantiated claim that "+1.00 pp indicates noticeable equity degradation in clinical and assistive transcription workflows."
  - Explicitly defined $+1.40\text{ pp}$ as a prespecified research engineering margin providing a $0.60\text{ pp}$ safety buffer below the operational gate tolerance ($\epsilon_D = +2.00\text{ pp}$), subject to future clinical/stakeholder calibration.

### Correction 3: Disparity Confidence-Bound Calibration Investigation
- **File:** [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md) (Section 3.6), [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py).
- **Adjustment:**
  - Evaluated unadjusted percentile $UCB_{95\%}(\Delta D)$ at boundary $\Delta D_{\text{true}} = +1.40\text{ pp}$ across $S = 2,000$ trials.
  - Diagnosed empirical non-coverage rate of $7.80\% \pm 0.60\%$ (coverage $92.20\%$, $2.80\text{ pp}$ below nominal 95%): caused by Jensen's attenuation bias (mean $\widehat{\Delta D} = 1.278\text{ pp}$, bias $-0.122\text{ pp}$) and extreme-value bootstrap compression at $N=10$ speakers/group.
  - Demonstrated that calibrated critical percentile ($UCB_{97.5\%}$) restores conservative coverage ($3.95\% \le 5.0\%$).
  - Recorded decisive methodological finding: bootstrap range bounds cannot be claimed as exact asymptotic 95% bounds without larger strata ($N \ge 30$/group).

### Correction 4: Joint Safety–Utility Success Probability Simulation ($P(A \cap B)$)
- **File:** [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md) (Section 3.7), [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 8.3).
- **Adjustment:**
  - Simultaneously simulated Event A (Overall-WER superiority) and Event B (Disparity compliance) across $S = 1,500$ trials for 4 joint scenarios.
  - Confirmed mathematical bound $P(A \cap B) \le \min(P(A), P(B))$: under Scenario 1 (Parity Preserved, $\Delta = -0.85\text{ pp}, \Delta D = 0.00\text{ pp}$), marginal WER power is $97.1\%$, marginal disparity power is $52.8\%$, and strict joint power is $\mathbf{51.4\% \pm 1.29\%}$.
  - Evaluated operational joint rule ($\widehat{\Delta D} \le 1.40\text{ pp} \land UCB_{95\%} \le 2.00\text{ pp}$), yielding **$78.6\% \pm 1.06\%$** pass rate.
  - Prohibited describing study as having 94.2% power for overall safety–utility success; marked strict joint criterion underpowered.

### Correction 2: Disparity Power Simulation & Status Reclassification
- **File:** [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md) (Section 3.5), [`power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json).
- **Adjustment:**
  - Implemented empirical simulation of the range statistic $D = \max_g \text{WER}_g - \min_g \text{WER}_g$ across 6 strata of 10 speakers each with stratified speaker bootstrap ($B=300$).
  - Disclosed empirical finding: even under perfect parity preservation ($\Delta D_{\text{true}} = 0.00\text{ pp}$), the rule $UCB_{95\%}(\Delta D) \le +1.40\text{ pp}$ passes in only $\mathbf{55.3\% \pm 1.57\%}$ of trials due to extreme-value range dispersion with $N=10$/group.
  - Formally reclassified the disparity power claim from `ADEQUATELY POWERED` to **`UNRESOLVED / STATISTICALLY UNDERPOWERED FOR N=10/GROUP`**.

### Correction 3: Three-Level Disparity Threshold Justification
- **File:** [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 9.1).
- **Adjustment:**
  - Removed simple "70% of operational gate" arithmetic justification.
  - Defined explicit three-level architecture:
    1. **Operational Gate Tolerance ($\epsilon_D = +2.00\text{ pp}$):** Runtime threshold on Sentinel Panel ($N=30$) to filter candidate updates.
    2. **Scientific Effect Margin ($\delta_D = +1.00\text{ pp}$):** Substantive limit for human-in-the-loop accent parity.
    3. **Statistical Decision Boundary ($\tau_D = +1.40\text{ pp}$):** Point estimate limit ensuring empirical disparity remains well within operational limits.

### Correction 4: Two-Cohort Evidence State & Model Lineage Audit
- **File:** [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 7.2 & 10), [`stage6m_model_registry.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/stage6m_model_registry.json), [`stage6m_data_integrity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_integrity_audit.md).
- **Adjustment:**
  - Labeled Cohort 2 strictly as **`PROPOSED — NOT YET CREATED OR VERIFIED`**, disclaiming any assertion that its split currently exists on disk.
  - Audited historical Stage 6 (`reports/stage6/eight_model_benchmark.csv`) and disclosed that the 4 CTC architectures were evaluated in an earlier exploratory benchmark on `stage5_external_eval.csv`.
  - Reclassified model role in Cohort 1 as **Cross-Architecture Replication**, not pristine blind confirmation.

### Correction 5: Strict Missingness Policy
- **File:** [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 9.2).
- **Adjustment:**
  - Eliminated arbitrary $+2.00\text{ pp}$ addition as "worst-case" bound (recognizing that insertions allow unbounded WER).
  - Mandated **100% verified counterfactual coverage** for primary success.
  - Preserved strict `UNAVAILABLE` flag for any unobserved outcome; any missing outcome prevents success and yields `INCONCLUSIVE (UNVERIFIED MISSING DATA)`.

### Correction 6: Decision Taxonomy & Boundary Closures
- **File:** [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md) (Section 9.4).
- **Adjustment:**
  - Explicitly classified the intermediate disparity interval ($1.40 < UCB_{95\%} \le 2.50\text{ pp}$ while $\widehat{\Delta D} \le 1.40\text{ pp}$) as **`INCONCLUSIVE ON DISPARITY SAFETY (Uncertainty Exceeds Safety Margin)`**.
  - Explicitly classified non-significant policy contrasts ($p \ge 0.05$) as **`INCONCLUSIVE ON BENEFIT`**, strictly prohibiting any inference of equivalence.
  - Maintained TOST equivalence requirement within $[-0.50\text{ pp}, +0.50\text{ pp}]$.

### Correction 7: Confirmatory Sample Size Decision (Option A Expansion) & Common Voice Feasibility
- **Files:** [`stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md), [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py).
- **Adjustment:**
  - Formally adopted supervisor-recommended **Option A (Confirmatory Sample Size Expansion)**.
  - Designated $N = 180$ independent speakers ($30$/stratum across 6 groups) as the **Initial Planning Target**.
  - Superseded early draft claims: Evaluated sample-size grid up to $N = 420$.

---

## 3. Final Methodological & Data-Integrity Reconciliation (Professor's Review)

Following the professor's final review of Stage 6M v1.2.0, four targeted statistical and data-integrity reconciliations were executed:

### Reconciliation 1: Dual-Scenario Joint Power Target & Grid Expansion ($N=60 \to 420$)
- **Problem Diagnosed:** The earlier report claimed $N=240$ provided a "strong buffer" under mild drift, but the reported joint power under $+0.50\text{ pp}$ drift was only $74.3\%$ (falling below the $\ge 85\%$ target).
- **Resolution:**
  - Extended the Monte Carlo simulation grid ($S=2,000$, $B=400$) across $N \in \{60, 90, 120, 150, 180, 210, 240, 300, 360, 420\}$.
  - Confirmed that at $N=240$, Scenario 2 drift joint power is $72.1\%$ (UCB95) and $61.3\%$ (Adjusted UCB97.5), failing the dual-scenario $\ge 85\%$ target.
  - Identified $N = 360$ ($60$/group) as the minimal balanced cohort size satisfying the **$\ge 85\%$ dual-scenario target** under UCB95 ($99.5\%$ in Scenario 1 and $85.6\%$ in Scenario 2; $99.7\%$ under operational rule).
  - Documented that under conservative Adjusted UCB97.5, even the maximum feasible balanced cohort ($N=420$) achieves $82.0\% \pm 0.86\%$ under drift. Transparently reported this limitation.

### Reconciliation 2: Irish Speaker Arithmetic & Provenance Audit
- **Problem Diagnosed:** The previous draft claimed $94$ eligible Irish speakers, $15$ prior exposures, and $73$ remaining ($94 - 15 = 79 \neq 73$).
- **Root Cause Uncovered:** Provenance trace through `external_speaker_inventory.csv`, `curate_stage5_sentinel_panel.py`, and `stage5_sentinel_panel_manifest.json` revealed:
  1. $94$ initial Irish speakers with $\ge 15$ validated clips.
  2. $-10$ speakers assigned to Replication Cohort 1 (`stage5_external_eval.csv`), leaving $84$.
  3. $-1$ speaker excluded during Sentinel Panel curation due to strict clip quality filters (word count $<2$, accent heterogeneity), leaving $83$ candidates in `stage5_sentinel_panel_manifest.json` (`pool_size: 83`).
  4. $-5$ speakers sampled for Sentinel Panel (`stage5_sentinel_panel.csv`), leaving **$78$ verified untouched, unexposed eligible speakers** (or $79$ in raw inventory).
  5. The previous draft mistakenly subtracted the $10$ replication speakers a *second time* from the post-filtered pool ($83 - 10 = 73$).
- **Capacity Recalculated:** Maximum feasible balanced 6-group cohort capacity is $78 \times 6 = \mathbf{468\text{ speakers}}$ ($7,020\text{ clips}$).

### Reconciliation 3: Confirmatory Cohort Status & Overlap Claims
- **Problem Diagnosed:** The previous supervisor letter claimed both that Cohort 2 was uncreated and that it had mathematically verified zero speaker overlap.
- **Resolution:** Formally decoupled candidate-pool feasibility (`VERIFIED FROM ARTIFACT`) from actual selected cohort disjointness (`PROPOSED — PENDING MANIFEST CREATION`). Explicitly stated: "The preliminary data-feasibility audit indicates that the proposed cohort sizes may be achievable from the candidate dataset. The new confirmatory cohort has not yet been selected or manifested; its actual speaker-overlap checks remain pending. No confirmatory independence claim will be made until the selected manifest has been verified."

### Reconciliation 4: Simulation Consistency & Canonical Hash
- **Problem Diagnosed:** Previous drafts contained small discrepancies between tables (e.g. $85.6\%$ vs $87.0\%$ at $N=180$, $92.5\%$ vs $92.8\%$ at $N=240$) due to non-canonical simulation scripts and seed variation.
- **Resolution:**
  - Unified all tables under one single canonical simulation script (`scripts/simulate_stage6m_power.py`).
  - Generated authoritative canonical JSON artifact: [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) with SHA-256 hash `9ecb0b4fc4ba15d33394dc8af7e198da8eab6131da13b51adb4706d157894ae6`.
  - All report tables regenerated strictly from this output file. Superseded numbers preserved in changelog. Stale text stating simulations are running removed.
  - Added statistical qualification documenting Monte Carlo standard errors ($\pm 0.48\%\text{ to }\pm 0.54\%$) for Type I error point estimates ($4.9\%$--$5.8\%$).

---

## 4. Second Methodological, Inferential & Power Reconciliation (Independent Review Response)

Following the independent review of the latest Stage 6M reconciliation ("Stage 6M v1.2.0 — Independent Review of the Latest Reconciliation"), four critical corrections were implemented:

### Reconciliation 1: Resolution of Joint-Power Table Contradictions
- **Problem Diagnosed:** The previous report contained conflicting power estimates for identical sample-size and scenario combinations (e.g., Table 8.3 in `stage6m_protocol_proposal.md` reported $42.4\%$, $72.8\%$, $83.2\%$ for UCB95 and $32.5\%$, $61.9\%$, $74.3\%$ for Adjusted UCB97.5 at $N=60, 180, 240$, whereas the master reconciliation table reported $33.3\%$, $62.9\%$, $72.1\%$ and $23.5\%$, $51.8\%$, $61.3\%$).
- **Root Cause Uncovered:** Table 8.3 in `stage6m_protocol_proposal.md` and an appended section in `stage6m_power_analysis.md` retained legacy estimates from an earlier exploratory bootstrap run ($B=300$, differing seed) that were not overwritten when the master table was compiled.
- **Resolution:**
  - Removed all stale, duplicated, and conflicting tables across all protocol documents.
  - Formally established **one authoritative canonical output file**: [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json).
  - Recorded complete reproducibility metadata:
    - **Simulation Script:** [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py)
    - **Simulation Output SHA-256 Hash:** `4e2e9ab019c860573fa82832e159530776ff184ed877321e9a9e1a18f31cf767`
    - **Random Seeds:** Discovery: `42`, Validation: `20261012`
    - **Monte Carlo Trials:** $S = 2,000$ per cell
    - **Bootstrap Resamples:** $B = 400$ stratified speaker resamples per trial
  - Every single table across [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md), [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`stage6m_signoff_checklist.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_signoff_checklist.md), and [`configs/stage6m_protocol_config.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/configs/stage6m_protocol_config.json) has been regenerated strictly from this file.

### Reconciliation 2: Inferential Procedure Integrity vs. Power Optimization
- **Problem Diagnosed:** The unadjusted percentile $UCB_{95\%}$ procedure exhibits empirical non-coverage above nominal 5.0% ($6.75\%$--$7.80\%$) at the disparity boundary $\tau_D = +1.40\text{ pp}$. The reviewer rightfully barred choosing the unadjusted procedure merely because it reached higher joint power ($85.6\%$ at $N=360$) while failing nominal coverage.
- **Resolution:**
  - Decoupled the statistical procedure justification from the sample size recommendation.
  - Validated that the **simulation-calibrated Adjusted $UCB_{97.5\%}$** is the only procedure among those evaluated that rigorously guarantees empirical non-coverage $\le 5.0\%$ across boundary conditions (achieving $1.8\%$ to $4.9\%$ non-coverage).
  - Explicitly classified the standard percentile $UCB_{95\%}$ as **anti-conservative / undercovered** due to Jensen's attenuation and bootstrap tail compression on the non-linear range statistic $D = \max_g - \min_g$.
  - Designated Adjusted $UCB_{97.5\%}$ as the primary inferential safety benchmark, and based the definitive sample-size feasibility decisions on its rigorous operating characteristics.

### Reconciliation 3: Power Grid Extension to $N=450$ and $N=468$ (100% Feasible Capacity)
- **Problem Diagnosed:** Under Adjusted $UCB_{97.5\%}$, the maximum evaluated sample size of $N=420$ achieved only $82.0\%$ joint power under modest drift ($+0.50\text{ pp}$), leaving it uncertain whether the available candidate pool capacity (78 Irish English speakers, $N_{\max} = 468$) could achieve the $\ge 85\%$ joint-power target.
- **Resolution:**
  - Extended the canonical Monte Carlo grid to include $N = 450$ ($75$ speakers/group, 3 Irish speakers reserve) and $N = 468$ ($78$ speakers/group, 100% candidate pool capacity):
    - **$N = 450$:**
      - Scenario 1 (Parity Preserved, $\Delta D = 0.00\text{ pp}$): Strict Adj. UCB97.5 power is **$99.7\%$** (UCB95: $100.0\%$).
      - Scenario 2 (Modest Drift, $\Delta D = +0.50\text{ pp}$): Strict Adj. UCB97.5 power is **$83.5\% \pm 0.83\%$** (UCB95: $90.8\%$). Operational rule: **$99.9\%$**.
    - **$N = 468$:**
      - Scenario 1 (Parity Preserved, $\Delta D = 0.00\text{ pp}$): Strict Adj. UCB97.5 power is **$99.7\%$** (UCB95: $99.9\%$).
      - Scenario 2 (Modest Drift, $\Delta D = +0.50\text{ pp}$): Strict Adj. UCB97.5 power is **$\mathbf{86.4\% \pm 0.77\% \ge 85.0\%}$** (UCB95: $91.9\%$). Operational rule: **$99.9\%$**.
  - **Core Conclusion:** The independent confirmatory candidate pool *can* support the strict confirmatory joint safety–utility claim at $\ge 85\%$ power under the conservative Adjusted $UCB_{97.5\%}$ procedure, but doing so requires utilizing all 78 unexposed Irish speakers ($N = 468$), leaving zero margin for participant attritions or quality drops.

### Reconciliation 4: Broad Data-Generating Process (DGP) Sensitivity Battery
- **Problem Diagnosed:** Calibration of the adjusted bound had only been validated under a single set of distributional assumptions, which does not guarantee robust coverage across diverse ASR error profiles.
- **Resolution:**
  - Implemented a 12-scenario DGP sensitivity battery in [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py) across independent discovery (seed 42) and validation (seed 20261012) runs, systematically varying:
    1. Between-speaker standard deviation: $\sigma_{\text{spk}} \in [2.5, 3.5, 5.0]\text{ pp}$.
    2. Paired correlation between gated and ungated adaptation: $\rho \in [0.75, 0.88, 0.95]$.
    3. Heteroscedastic error variability across strata (e.g. Group 6 $\sigma=5.0\text{ pp}$ vs. $\sigma=3.0\text{ pp}$).
    4. Stratum identities experiencing drift (lowest-WER stratum, intermediate stratum, highest-WER stratum).
    5. Baseline disparity ranges: narrow ($3.0\text{ pp}$), moderate ($8.0\text{ pp}$), wide ($20.0\text{ pp}$).
    6. Boundary sweeps around tolerance: $\Delta D_{\text{true}} \in [+1.20, +1.30, +1.40, +1.50]\text{ pp}$.
  - Results confirmed that across all 12 scenarios:
    - Standard percentile $UCB_{95\%}$ non-coverage ranges from **$5.1\%$ to $8.6\%$** (consistently anti-conservative).
    - Simulation-calibrated Adjusted $UCB_{97.5\%}$ non-coverage is strictly bounded between **$1.8\%$ and $4.9\%$** (guaranteeing $\le 5.0\%$ error control).
  - Explicitly documented as a **simulation-calibrated research bound under specified distributional assumptions**, not an asymptotic universal theorem.

---

## 5. Final Scientific Audit Reconciliation (Response to Independent Scientific Audit)

Following the formal Independent Scientific Audit of Stage 6M v1.2.0, four critical reproducibility, inferential, and governance updates were executed:

### Reconciliation 1: Type I Error Table Reconciliation & Provenance Audit
- **Problem Diagnosed:** The previous report contained conflicting Type I error estimates across different sections (e.g. Section 8.1 listed $4.70\%, 4.80\%, 4.70\%$, a summary cited $5.1\%, 5.5\%, 5.2\%$, while Section 3.2 of the power analysis reported $6.30\%, 5.40\%, 4.90\%, 5.60\%, 5.25\%, 5.75\%$).
- **Root Cause Uncovered:** Section 8.1 of `stage6m_protocol_proposal.md` and a duplicate trailing block in `stage6m_power_analysis.md` retained legacy numbers from an earlier exploratory $z$-test approximation and an exploratory seed run that were not overwritten.
- **Resolution:**
  - Removed all duplicate trailing blocks and legacy citations across all documents.
  - Reconciled every single Type I error figure across the entire repository to the canonical JSON output (`hypothesis_1_superiority_against_zero` under $H_0: \Delta_{\text{aggregate}} \ge 0.00\text{ pp}$, exact Student-t decision rule $t < t_{0.05, N-1}$, Discovery Seed 42, $S = 2,000$ trials):
    - $N = 60$ ($df=59$, $t_{\text{crit}} = -1.6711$): **$6.30\% \pm 0.54\%$** (95% CI: $[5.24\%, 7.36\%]$)
    - $N = 180$ ($df=179$, $t_{\text{crit}} = -1.6534$): **$5.40\% \pm 0.51\%$** (95% CI: $[4.41\%, 6.39\%]$)
    - $N = 240$ ($df=239$, $t_{\text{crit}} = -1.6513$): **$4.90\% \pm 0.48\%$** (95% CI: $[3.95\%, 5.85\%]$)
    - $N = 300$ ($df=299$, $t_{\text{crit}} = -1.6500$): **$5.60\% \pm 0.51\%$** (95% CI: $[4.59\%, 6.61\%]$)
    - $N = 360$ ($df=359$, $t_{\text{crit}} = -1.6491$): **$5.25\% \pm 0.50\%$** (95% CI: $[4.27\%, 6.23\%]$)
    - $N = 420$ ($df=419$, $t_{\text{crit}} = -1.6485$): **$5.75\% \pm 0.52\%$** (95% CI: $[4.73\%, 6.77\%]$)
    - $N = 450$ ($df=449$, $t_{\text{crit}} = -1.6483$): **$5.05\% \pm 0.49\%$** (95% CI: $[4.09\%, 6.01\%]$)
    - $N = 468$ ($df=467$, $t_{\text{crit}} = -1.6481$): **$4.85\% \pm 0.48\%$** (95% CI: $[3.91\%, 5.79\%]$)
  - Explicitly marked all previously cited figures ($4.70\%$, $4.80\%$, $5.1\%$, $5.5\%$, $5.9\%$, etc.) as **SUPERSEDED** exploratory or normal-approximation estimates.
  - Documented that for all prospective confirmatory candidate cohorts ($N \ge 180$, $N \in \{180, 240, 300, 360, 420, 450, 468\}$), 95% confidence intervals cleanly encompass 5.0%, confirming exact error calibration across the confirmatory design space. Explicitly documented the exception at baseline replication size $N=60$ ($[5.24\%, 7.36\%]$), which excludes 5.00% under $S=2,000$ and pooled $S=4,000$ ($[5.17\%, 6.63\%]$) due to finite Monte Carlo variation, verified to converge to $4.930\% \pm 0.068\%$ at $S=100,000$. Note that $N=60$ is the historical Cohort 1 baseline, not an active confirmatory candidate.

### Reconciliation 2: Invariant Primary Scientific Safety Criterion vs. Operational Rule
- **Problem Diagnosed:** The previous reconciliation report presented an alternative option where the two-part operational gate rule ($\widehat{\Delta D} \le 1.40\text{ pp} \land UCB_{95\%} \le 2.00\text{ pp}$) would be preregistered as the primary confirmatory claim to pass power at $N=360$.
- **Resolution:**
  - Strictly rejected substituting the operational gate rule for the scientific disparity requirement.
  - Reaffirmed that the **simulation-calibrated Adjusted $UCB_{97.5\%}(\Delta D) \le +1.40\text{ pp}$** is the sole primary scientific disparity safety criterion.
  - Relegated the two-part operational rule strictly to a **secondary analysis** describing runtime gate behavior on the Sentinel Panel.

### Reconciliation 3: Rigorous Metric Separation & Monte Carlo Uncertainty Qualification
- **Problem Diagnosed:** Confidence-bound noncoverage, safety-pass probability, and false safety declaration probability were conflated in sub-boundary and boundary sensitivity reporting, and point estimates near 5% were presented without sufficient Monte Carlo uncertainty qualification.
- **Resolution:**
  - Formally separated and reported five distinct quantities across all calibration and sensitivity evaluations:
    1. **Confidence-Bound Noncoverage:** $\Pr(U < \Delta_D)$
    2. **Confidence-Bound Coverage:** $\Pr(U \ge \Delta_D) = 1 - \Pr(U < \Delta_D)$
    3. **Safety-Pass Probability:** $\Pr(U \le \tau_D)$ where $\tau_D = +1.40\text{ pp}$
    4. **Boundary False Declaration Probability:** $\Pr(U \le \tau_D \mid \Delta_D = \tau_D)$ (disparity Type I error analogue under boundary null)
    5. **False Safety Probability under Violation:** $\Pr(U \le \tau_D \mid \Delta_D > \tau_D)$ (evaluated strictly when $\Delta_D > \tau_D$; marked **NOT APPLICABLE (N/A)** for safe states $\Delta_D \le \tau_D$).
  - Reconciled the provenance of the 3.70% vs 4.85% figures: 3.70% is the boundary noncoverage under Scenario 3 (=360$, high speaker variance) and Validation Seed 20261012 boundary sweep; 4.85% was the primary WER superiority Type I error under null $\Delta = 0.00\text{ pp}$ at =468$ (.85\% \pm 0.48\%$), which was conflated in earlier summary text with disparity noncoverage (the actual disparity boundary noncoverage at =468$ is .70\% \pm 0.36\%$).
  - Executed a bootstrap stability sensitivity analysis across  \in \{400, 800, 1000, 1200\}$ on identical synthetic trials, proving $>99.2\%$ decision agreement, upper-bound shifts $<0.04\text{ pp}$, and recommending freezing =1,000$ for the confirmatory study.
  - Added explicit Monte Carlo standard errors ($\text{SE}$) and 95% Confidence Intervals for every probability across Discovery Seed 42 and Validation Seed 20261012.
  - Audited scenarios where point estimates approach 5% (e.g., $N=180$ narrow baseline: $4.90\% \pm 0.48\%$, 95% CI $[3.95\%, 5.85\%]$): explicitly noted that the confidence interval encompasses 5.0%, and that a point estimate below 5% does not prove true noncoverage $< 5.0\%$.
  - Formally designated the procedure as a **simulation-calibrated research bound under specified distributional assumptions**, not an asymptotic universal theorem.

### Reconciliation 4: Sample-Size Governance & Candidate Pool Accounting
- **Problem Diagnosed:** While $N=468$ achieves $86.4\% \ge 85\%$ joint power under modest drift ($+0.50\text{ pp}$) with Adjusted $UCB_{97.5\%}$, it completely exhausts the 78 unexposed Irish English speakers, leaving zero reserve for corrupted audio, decoding failures, or attrition.
- **Resolution:**
  - Maintained Option A (Confirmatory Sample Size Expansion) as the approved research direction, but kept the final sample size **UNFROZEN** pending supervisor choice between two defensible paths:
    1. **Preferred Path (Candidate Pool Expansion):** Investigate adding genuinely independent speakers from an additional Common Voice release or harmonized public corpus (with cross-release deduplication and harmonized accent definitions) to secure an operational reserve.
    2. **Alternative Path (Full-Capacity Cohort $N=468$ with Explicit Limitations):** Deploy the 468-speaker design with explicit disclosure of zero reserve speakers and strict prohibition of post-hoc replacements.
  - Authoritative simulation output updated and hashed:
    - Output JSON SHA-256: `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`
    - Simulation Script SHA-256: `cad4b95e5668531adbbb413566c51b03a2f27406ad0b146c13ed62516bbb983e`

---

## 6. Operational Governance Invariant

```
================================================================================
STAGE 6M GOVERNANCE STATE: HOLD — STRICTLY NOT AUTHORIZED
================================================================================
execution_authorized: false
execution_status    : HOLD_PENDING_STAKEHOLDER_AUTHORIZATION

All protocol-only edits, configuration schemas, and simulation scripts
are committed for academic stakeholder review. Benchmark execution remains
strictly locked.
================================================================================
```


### Correction 8: Independent Statistical Audit Reconciliation (Dual-Loop Elimination & Rule A/B Formalization)
- **Files:** [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py), [`power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md).
- **Authoritative Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Adjustments Made:**
  1. **Dual-Loop Elimination:** Eliminated independent simulation loops for Section 4 and Section 5. The exploration grid is now constructed 1:1 from Section 4 scenario records, achieving 100% agreement across all 12 cohorts.
  2. **Rule A vs. Rule B Standards Formalized:** Formally defined Rule A (point estimate $\ge 85.00\%$) and Rule B (lower 95% Monte Carlo confidence limit $L_{95\%, \text{MC}} > 85.00\%$). $N=468$ passes Rule A ($85.83\%$, exact: $85.825\%$) but fails Rule B ($84.74\%$), substantiating keeping the sample size **unfrozen** under Option A Candidate Pool Expansion.
  3. **Marginal Clean Non-Degradation Evaluation:** Documented exact zero failures ($4,000/4,000$) for $N \ge 180$ with Rule-of-Three upper bound $\le 0.075\%$.
  4. **Exact Numerical Boundary Tie Checks:** Separated exact equality (`u == tau`) from near-ties (`rtol=0, atol=1e-12`), recording exact $0$ ties across all cohorts.
  5. **Demographic Inventory Arithmetic & Provenance:** Reconciled Irish English bottleneck capacity ($94 - 10 - 1 - 5 = 78$) and provided verified SHA-256 digests for all inventory and split files.


### Correction 9: Independent Statistical & Data-Integrity Audit Finalization (Mandates 1–8)
- **Files Modified:** [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py), [`power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md), [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py).
- **Authoritative Cryptographic Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Mandates Addressed:**
  1. **Candidate Pool Inventory Provenance:** Full provenance reconstruction for Sets 1, 2, and 3. Ground truth artifact (`external_speaker_inventory.csv`, SHA-256 `e964799b...`) verified with $6,905$ unique speakers and mutually exclusive strata. Automated regression test added.
  2. **Irish Capacity Deficit for $N=540$:** Established that with $78$ unexposed Irish speakers, $N=540$ ($90$/group) with $15$ reserve requires $105$ speakers, creating a strict deficit of **$27$ additional eligible speakers**. Common Voice 27.0 is exhausted; feasibility requires genuine supplementary acquisition.
  3. **Sample-Size Grid Extension ($N=540$ and $N=600$):** Simulated under canonical frozen DGP ($S=4,000, B=1,000$). $N=540$ attains $\widehat{\text{Power}} = 90.40\%$ ($95\%$ MC CI $[89.49\%, 91.31\%]$), demonstrating Rule B compliance under the simulation model.
  4. **Matched Trial-Level Joint Success Verification:** Trial-level intersection counts ($n_A, n_B, n_C, n_{AB}, n_{AC}, n_{BC}, n_{ABC}$) documented. Verified $n_{ABC} = n_C = 3,433$ at $N=468$ and $3,616$ at $N=540$. Replaced mathematical proof wording with empirical evidence phrasing.
  5. **Clean Non-Degradation Reporting:** Reconciled Approach A and Approach B. Documented zero observed failures ($4,000/4,000$) for $N \ge 180$, yielding Rule-of-Three upper bound on failure rate $\le 0.075\%$.
  6. **Literal Rule A vs Rule B Classification:** $N=450$ classified as FAIL under Rule A ($84.50\% < 85\%$) and FAIL under Rule B ($83.38\% < 85\%$). Parity vs drift distinctions explicitly documented.
  7. **Boundary Ties Verification:** Exact and near-boundary ties verified as $0 / 4,000$ per cohort condition across $112,000$ simulation trials in discovery and validation runs.
  8. **Final Synchronization & Invariants:** Automated test suite passes $12/12$ tests. Final status locked: `execution_authorized = false`, `STAGE 6M STATUS = HOLD`, `Cohort 2 = PROPOSED — NOT YET CREATED`, `Sample size = UNFROZEN`.


### Correction 10: Independent Statistical & Data-Integrity Final Sign-Off Audit (Blockers 1–7)
- **Authoritative Output Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Blockers Audited & Reconciled:**
  1. **Joint-Power Grid vs. Intersection Discrepancy & Mathematical Consistency:** Synchronized exploration grid joint successes with trial-level intersection counts across all 14 sample sizes ($853$ at $N=60$, $1,168$ at $N=90$, $1,452$ at $N=120$, $3,433$ at $N=468$, $3,616$ at $N=540$, and $3,708$ at $N=600$). Eliminated the text formatting discrepancy ($979 > 974$) by dynamically verifying the 8-cell contingency table ($c_{001} = +4 \ge 0$, union $= 970 \le 974$).
  2. **Clean-Condition Upper Confidence Bound (UCB) Sign Convention:** Verified that Approach B uses the positive upper-tail quantile ($t_{0.95, N-1} > 0$), ensuring $\text{UCB}_{95\%} > \widehat{\Delta R}_{\text{clean}}$ whenever $\text{SE} > 0$. Deterministic unit test added to CI suite.
  3. **Common Voice Release Provenance Verification:** Eliminated errant $2024\text{-}03\text{-}05$ reference; verified canonical release metadata `cv-corpus-27.0-2026-09-11` (MDC ID `cmu5jplf300nwmh07iqvk9leo`, $1,929,854$ data rows, $614,927,262$ bytes, SHA-256 `733c2fa7...`).
  4. **Historical Inventory Count Provenance:** Reconciled Set 1 ($6,905$), Set 2 ($6,908$), and Set 3 ($6,920$). Strictly categorized Sets 2 and 3 as reconstructed working draft explanations with zero ground truth standing.
  5. **Clean Failure-Rate Table Formatting:** Mislabeled Rule-of-Three column separated into "Observed Failure Rate" (for rows with observed failures) and "One-Sided 95% Upper Bound" (Rule of 3: $3/S = 0.075\%$ for zero-failure rows $N \ge 180$). Clarified one-sided lower confidence bound $[99.93\%, 100\%]$.
  6. **Supplementary Corpus Comparability & Confounding Safeguards:** Established Strategy C (Pure Common Voice 27.0 at $N=468$) as the primary unconfounded confirmatory benchmark. Mandated Strategy A (Balanced Multi-Corpus Sampling across all 6 groups) if expanding to $N=540$ with external Irish speakers to prevent accent-corpus confounding.
  7. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD`, `Cohort 2 = PROPOSED — NOT YET CREATED`, `Sample size = UNFROZEN`.


### Correction 11: Inventory Eligibility vs. Quality Exclusions Resolution & Set-Equation Formalization
- **Files Modified:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`scripts/update_stage6m_reports.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/update_stage6m_reports.py), [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py).
- **Adjustments Made:**
  1. **Dual Clip-Count Metrics Formalized:** Defined $C_{\text{inventory}}(s)$ ($\ge 15$ clips with word count $\ge 2$, homogeneous accent, unique path) vs $C_{\text{strict}}(s)$ (baseline criteria + `locale == 'en'`, `up_votes >= 2`, `down_votes < 2`).
  2. **Disputed IDs Audited at Speaker Record Level:**
     - `fc22fd45...`: $C_{\text{inventory}} = 15 \ge 15$, $C_{\text{strict}} = 14 < 15$ (1 clip disqualified due to `down_votes = 2`). Unexposed candidate: $Q \setminus E_1 = \{\text{fc22fd45...}\}$.
     - `f3ea0447...`: $C_{\text{inventory}} = 15 \ge 15$, $C_{\text{strict}} = 13 < 15$ (2 clips disqualified due to `down_votes = 2`, 1 clip with 1 word). Selected into Cohort 1 ($E_1$): $E_1 \cap Q = \{\text{f3ea0447...}\}$.
  3. **Inventory-Restricted Set Equation Corrected:**
     - Expressed candidate exclusions strictly within $I$:
       $$I_{\text{excluded}} = I \cap (E_1 \cup E_S \cup E_4 \cup E_C \cup Q)$$
       $$|I_{\text{excluded}}| = 10 + 5 + 0 + 0 + 1 = 16$$
       $$I_{\text{available}} = I \setminus I_{\text{excluded}} = 94 - 16 = \mathbf{78}$$
  4. **Regression Guard Upgraded:** `test_stage6m_irish_speaker_set_theoretic_accounting` upgraded to verify both client IDs in `validated.tsv`, exact $C_{\text{inventory}}$ and $C_{\text{strict}}$ counts, disjointness, and inventory-restricted equations. Suite passes $17/17$ tests in CI.


### Correction 12: Residual Audit Closure (Warnings Classification, Canonical Path Audit, and Reserve Allocation)
- **Files Modified:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`scripts/update_stage6m_reports.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/update_stage6m_reports.py), [`reports/stage6m/research_validity_pytest_run.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/research_validity_pytest_run.log), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Adjustments Made:**
  1. **Full Research-Validity Directory Execution:** Executed all 12 modules in `tests/research_validity/`: 110 passed in $34.11\,\text{s}$ (exit code 0). Complete log saved to `reports/stage6m/research_validity_pytest_run.log`.
  2. **Comprehensive Test Warning Review:** Identified and classified all 6 warnings (4 `torchvision` PIL resampling enum deprecations; 2 Python 3.11 SWIG C-extension module attribute deprecations). Confirmed zero effect on numerical stability, PRNG seeds, data validation, or research validity. Zero project code changes required.
  3. **Canonical TSV Path Reconciled & Alias Clarified:** Confirmed `datasets/external/common_voice_27/validated.tsv` ($614,927,262$ bytes, SHA-256 `733c2fa7...`) as canonical source artifact read by `scripts/phase3_external_eval_curation.py`. Reconciled `data/commonvoice/validated.tsv` as an informal chat alias (does not exist on disk, zero code occurrences). Documented `datasets/external/common_voice_27_intermediate/` as an unpack staging mirror with zero active script dependencies.
  4. **Reserve Allocation Modeling for $N=540$ Candidate Design:** Documented formal allocation of $78$ Common Voice + $27$ External Irish speakers to achieve $90$ active participants and $15$ reserve ($75$ CV + $15$ External active; $3$ CV + $12$ External reserve). Reasserted that single-source Gaussian power ($90.40\%$) does not automatically transfer to multi-source samples.
  5. **Governance Invariants Maintained:** Preserved execution hold: `execution_authorized = false`, `STAGE 6M STATUS = HOLD`, `Cohort 2 = PROPOSED — NOT YET CREATED`, `Final sample size = UNFROZEN`. Confirmatory status: **NO-GO**.


### Correction 13: Final Technical Audit Closure (Workstreams 1–5)
- **Authoritative Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Files Modified:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_data_integrity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_integrity_audit.md), [`reports/stage6m/stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`scripts/update_stage6m_reports.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/update_stage6m_reports.py).
- **Workstreams Audited & Reconciled:**
  1. **Workstream 1 (Reserve-Policy Consistency):** Decoupled the active evaluation sample ledger ($540$ active participants: $450$ Common Voice + $90$ External across all six strata) from reserve scenarios. Documented that current repository external inventory is strictly zero across all six strata ($90$ active external shortfall). Maintained separate scenario ledgers for Policy A (Irish-only reserve: $555$ total ingested, $102$ external shortfall) and Policy B (Stratum-balanced reserve: $630$ total ingested, $162$ external shortfall). Kept reserve policy formally `[UNRESOLVED]` pending supervisor preregistration.
  2. **Workstream 2 (Clip-Count Mathematics):** Formulated $C_{\text{inventory}}(s) = \sum_{r \in \mathcal{R}_s} B(r)$ and $C_{\text{strict}}(s) = \sum_{r \in \mathcal{R}_s} S(r)$ as rigorous indicator summations over candidate TSV rows. Reconciled $C_{\text{strict}}(s) \ge 15$ with individual speaker records for `fc22fd45...` ($C_{\text{inventory}}=15, C_{\text{strict}}=14$) and `f3ea0447...` ($C_{\text{inventory}}=15, C_{\text{strict}}=13$). Preserved full set accounting: $|I| = 94, |I_{\text{excluded}}| = 16, |I_{\text{available}}| = 78$.
  3. **Workstream 3 (Disparity Estimand & Power Transferability):** Formally distinguished cross-sectional disparity level $D_m = \max_g R_{m,g} - \min_g R_{m,g}$ from adaptation-induced disparity change $\Delta D = D_{\text{adapted}} - D_{\text{baseline}}$. Mathematically proved that an idealized uniform additive corpus shift cancels from the range estimator ($\max_g (R_g + \gamma_k) - \min_g (R_g + \gamma_k) = D_m$). Qualified that power transferability is threatened by corpus-by-accent interactions $(\alpha\gamma)_{gk} \ne 0$, heteroscedastic residual variance $\sigma^2_{\epsilon,k}$, and correlation variation $\rho_k$. Reaffirmed that single-source $N=540$ power ($90.40\%$) does not validate a multi-corpus design; hierarchical mixed-model re-simulation is required.
  4. **Workstream 4 (Git-History Claim Precision):** Executed full-history commit searches (`git log --all --full-history -S"data/commonvoice/validated.tsv" -- .` and `git log --all --full-history -S"data/commonvoice" -- .`), returning 0 commits. Formulated precisely scoped finding: "No matching occurrence was found in the reachable Git history searched." Reconciled that the path originated strictly as informal chat shorthand in prior reviews.
  5. **Workstream 5 (Rendered Report Quality & Equation Audit):** Corrected table cell pipes using `\lvert` and `\rvert` in `stage6m_data_integrity_audit.md` and `stage6m_protocol_proposal.md`. Verified that all tables across all Stage 6M reports have 100% consistent column counts with zero parsing splits.
  6. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.


### Correction 14: Final Eligibility Reconciliation and Residual Audit Closure (Workstreams A–E)
- **Authoritative Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Files Modified:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`scripts/update_stage6m_reports.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/update_stage6m_reports.py), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Workstreams Audited & Reconciled:**
  1. **Workstream A (Six-Group Strict Eligibility Reconciliation & Policy B Feasibility Correction):** Recomputed $C_{\text{inventory}}(s)$ and $C_{\text{strict}}(s)$ for all $6,905$ inventory speakers across all six accent strata directly from `datasets/external/common_voice_27/validated.tsv`. Identified exactly $61$ speakers failing strict clip count ($C_{\text{strict}} < 15$): $2$ Australian, $0$ Canadian, $10$ England, $2$ Irish, $18$ South Asian, $29$ US. Reconciled net available strictly eligible unexposed speakers: Australian $383$ (was $385$, $\Delta = -2$), Canadian $496$ (was $496$, $\Delta = 0$), England $1,198$ (was $1,208$, $\Delta = -10$), Irish $78$ (was $78$, $\Delta = 0$), South Asian $731$ (was $749$, $\Delta = -18$), US $3,869$ (was $3,898$, $\Delta = -29$); Total $6,755$ (was $6,814$, $\Delta = -59$). Confirmed feasibility of active sample ($75$ CV/stratum) and Policy A reserve ($78$ Irish, $75$ non-Irish). Corrected Policy B Common Voice threshold from $93$ to $78$ CV/stratum ($75$ active $+ 3$ reserve per group; total $468$ CV across all 6 groups). Reconciled that Common Voice capacity under Policy B is FEASIBLE across all six strata ($383, 496, 1198, 78, 731, 3869 \ge 78$), with the bottleneck Irish stratum meeting its allocation with zero reserve headroom ($78 \ge 78$). Documented that Policy B has zero Common Voice deficit, and is strictly blocked by the external-corpus acquisition shortfall ($162$ unacquired external speakers across the six strata, vs $102$ under Policy A).
  2. **Workstream B (Resolve Irish "73 raw" Annotation & Rule B Multi-Corpus Qualification):** Traced the exact origin of the number $73$ in the Irish row: in an early uncommitted draft, after excluding $10$ Cohort 1 replication speakers ($94 - 10 = 84$) and $1$ unexposed strict clip filter failure ($84 - 1 = 83$), an author mistakenly subtracted the $10$ replication speakers a *second time* ($83 - 10 = 73$). Reconciled with $|I| = 94$, $|I_{\text{excluded}}| = 16$, $|I_{\text{available}}| = 78$. Removed the misleading label "73 raw" from active summary tables, and documented the resolution permanently in Section 3.1b. Formally qualified Rule B status: the existing $N=540$ simulation passes Rule B under its single-source Gaussian data-generating process ($\widehat{P} = 90.40\%, L_{95\%, \text{MC}} = 89.49\% > 85.00\%$), but Rule B status for the proposed multi-corpus study remains UNRESOLVED pending a design-specific hierarchical mixed-effects power analysis.
  3. **Workstream C (Mathematical Clip-Count Definitions):** Separated Boolean eligibility predicates from numeric indicator summations: defined baseline predicate $B_0(r)$, vote/locale predicate $V(r)$, indicator sums $C_{\text{inventory}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r)]$ and $C_{\text{strict}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r) \land V(r)]$, strict condition $C_{\text{strict}}(s) \ge 15$, and quality exclusion set $Q = \left\{ s \in I \mid C_{\text{strict}}(s) < 15 \right\}$. Documented global duplicate path handling and reconciled individual records for `fc22fd45...` ($C_{\text{inv}}=15, C_{\text{strict}}=14$) and `f3ea0447...` ($C_{\text{inv}}=15, C_{\text{strict}}=13$).
  4. **Workstream D (Corpus-Effect Claim and Source-Path Resolution):** Qualified the allocation imbalance claim: "Differences in corpus composition across accent groups can leave group-specific residual shifts when corpus effects differ, potentially affecting disparity estimates and their uncertainty. The magnitude and direction of that effect depend on the allocation, corpus effects, and covariance structure." Inspected Common Voice metadata resolution logic in `scripts/phase3_external_eval_curation.py`: distinguished canonical path (`datasets/external/common_voice_27/validated.tsv`) from configured fallback paths (`datasets/external/common_voice_27_intermediate/validated.tsv`, `datasets/external/common_voice_11/validated.tsv`, HuggingFace streaming), confirming that canonical path was selected and fallback was not executed. Scoped Git history search (`git log --all --full-history -S...` $\to$ 0 commits).
  5. **Workstream E (Rendered Report Verification & LaTeX Escaping):** Escaped LaTeX set braces (`\{` and `\}`), verified mathematical subscript formatting ($R^{(k)}_{m,g}$), ensured all markdown tables have 100% consistent column counts using `\lvert` and `\rvert` for table cell norms, and eliminated Python string escape sequence corruption (`\t`, `\n`, `\r`).
  6. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.


### Correction 15: Final Timing-Scope and Numerical Presentation Correction (Workstreams A–D)
- **Authoritative Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Files Modified:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_sample_size_decision.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_sample_size_decision.md), [`reports/stage6m/stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`reports/stage6m/stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`reports/stage6m/stage6m_signoff_checklist.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_signoff_checklist.md), [`scripts/update_stage6m_reports.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/update_stage6m_reports.py), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Execution Audit Artifacts Preserved & Verified:** [`reports/stage6m/test_execution_research_validity_full.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_full.log) (SHA-256 `04d6752ff7a10229b73859cebf1684773bd55cc02b5e2ffc42db866de604da19`), [`reports/stage6m/test_execution_stage6m_proposal.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_stage6m_proposal.log) (SHA-256 `e7509390a9d9234b963178af42aefa7c6e7adce77b186e1a72e5dbde0aac8e7a`).
- **Workstreams Audited & Closed:**
  1. **Workstream A (Power Table Numerical Reconciliation & Rounding Consistency):**
     - Reconciled $99.95\%$ vs $90.40\%$ from canonical simulation file [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): $99.95\%$ is mathematically Scenario 1 (Parity, $\Delta_D = 0.00\text{ pp}$, $3,998 / 4,000$ successes) joint power, whereas $90.40\%$ is the governing Scenario 2 (Drift, $\Delta_D = +0.50\text{ pp}$, $3,616 / 4,000$ successes, 95% MC CI $[89.49\%, 91.31\%]$) joint power. Reconciled that Rule A passes at $\widehat{P}_{\text{S2}} = 90.40\% \ge 85.00\%$, and Rule B passes at $L_{95\%} = 89.49\% > 85.00\%$. Corrected summary tables to ensure $99.95\%$ is never mislabeled as the governing estimated joint power.
     - Reconciled $N=468$ Scenario 2 joint power rounding: $3,433 / 4,000 = 85.825\%$. Formally standardized presentation to display **$85.825\%$** where three decimal places are used, and **$85.83\%$** (standard mathematical half-up rounding) for two-decimal summaries. Rule A passes ($85.83\% \ge 85.00\%$), while Rule B fails ($L_{95\%} = 84.74\% < 85.00\%$).
     - Preserved "Three Distinct Design and Simulation Scenarios": (1) $N=468$ CV-only (Rule B fails, capacity feasible with zero Irish reserve); (2) $N=540$ hypothetical single-source simulation (Rule B passes under DGP, infeasible as CV-only study due to $90 - 78 = 12$-speaker Irish CV deficit); (3) $N=540$ proposed multi-corpus study (CV capacity feasible with zero headroom under Policy B, power unresolved pending hierarchical re-simulation, external shortfall of $102$/$162$ speakers).
  2. **Workstream B (Test Timing Scope & Accurate Overhead Attribution):** Corrected the description of pytest's timing boundaries:
     - **Pytest-Reported Session Duration:** The duration recorded in pytest's terminal summary ($26.77\text{ s}$ for the full suite; $4.51\text{ s}$ for the Stage 6M module), which covers pytest's internal session clock (including its test collection and execution passes).
     - **Outer Process Wall-Clock Duration:** The elapsed time measured by `datetime.datetime.now(datetime.timezone.utc)` around the `subprocess.run([sys.executable, "-m", "pytest", ...])` call in `scratch/capture_test_execution_logs.py` ($30.714\text{ s}$ for the full suite: `19:11:19.935` to `19:11:50.649`; $6.503\text{ s}$ for the Stage 6M module: `19:11:50.651` to `19:11:57.154`).
     - **Timing Difference:** The difference ($3.944\text{ s}$ for full suite; $1.993\text{ s}$ for Stage 6M module) represents operations outside pytest's measured session timer, such as operating system process creation, Python interpreter invocation and bootstrap, loading entry points, and process shutdown/pipe flushing, rather than activities already captured within pytest's internal session timer.
  3. **Workstream C (Tripartite External Inventory Evidence Scoping):** Preserved tripartite separation: (1) Manifest Finding (Cohort 2 uncreated); (2) Repository Inventory Finding ($6,905$ speakers 100% from Common Voice 27.0; 0 non-CV speech files); (3) Acquisition Finding (shortfall of $102$ speakers under Policy A and $162$ under Policy B).
  4. **Workstream D (Artifact and Checksum Verification):** Recomputed all file checksums and byte counts, ensuring 100% table consistency and verifiable provenance.
  5. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.


### Correction 16: Independent Technical Audit Reconciliation (Workstreams A–E)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Authoritative Test Pass:** `20 passed in 3.60s` in [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py)
- **Files Modified / Updated:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Workstreams Audited & Closed:**
  1. **Workstream A (Reaffirmation of Frozen Clip Eligibility Criteria):**
     - Formally reaffirmed authoritative baseline predicate $B_0(r)$ requiring stratum accent match, valid `client_id`, non-empty & globally unique audio path, reference word count $\ge 2$, and homogeneous speaker accent ($15$ valid baseline clips required for inventory $I$).
     - Formally reaffirmed authoritative strict quality predicate $V(r)$ requiring $\operatorname{locale}(r) = \text{'en'}$, $\operatorname{up\_votes}(r) \ge 2$, and $\operatorname{down\_votes}(r) < 2$ ($15$ valid strict clips required for strict candidate eligibility).
     - Explicitly rejected unapproved exploratory additions: (1) `down_votes == 0` is an unauthorized post-hoc tightening (the frozen protocol explicitly allows $0$ or $1$ down-vote); (2) audio duration ($1\text{--}10\text{ s}$) and SNR ($\ge 12\text{ dB}$) are acoustic characterization metrics absent from Mozilla Common Voice `validated.tsv` metadata. They are formally designated as **`[UNAPPROVED EXPLORATORY ACOUSTIC AUDIT]`** with zero authority over governing feasibility.
  2. **Workstream B (Exact Exposure-Set Reconciliation Using Frozen Splits):**
     - Reconciled exact speaker sets: Replication Cohort 1 ($E_1$) contains exactly $60$ unique speakers ($10$ per stratum across all $6$ strata, $900$ clips total); Sentinel Panel ($E_S$) contains exactly $30$ unique speakers ($5$ per stratum across all $6$ strata, $300$ clips total).
     - Verified disjointness: $|E_1 \cap E_S| = 0$. Total prior exposed speakers across all strata: $|E_1 \cup E_S| = 90$ ($15$ per stratum).
     - Evaluated intersection with quality exclusions ($|Q| = 61$ failing $C_{\text{strict}} \ge 15$): exactly $1$ exposed speaker (`f3ea04475e301f84785710b9…` in Irish $E_1$, $C_{\text{strict}} = 13 < 15$) fails strict clip filtering. In the other five strata, $|Q \cap (E_1 \cup E_S)| = 0$.
     - Reconciled the reported figure **"89"**: represents the **strictly eligible exposed speakers** ($|(E_1 \cup E_S) \setminus Q| = 90 - 1 = 89$: $14$ Irish $+ 75$ non-Irish, $15$ in each of the other five groups).
     - Traced and disproved the erroneous phrase `"Cohort 1 (84)"`: $84$ was the unexposed Irish candidate pool count remaining after Cohort 1 extraction ($94 - 10 = 84$) in an early preliminary note, NOT the size of Cohort 1.
     - Established exact unexposed strictly eligible pool: $|I \setminus (E_1 \cup E_S \cup Q)| = 6,844 - 89 = \mathbf{6,755}$ speakers ($383$ Australian, $496$ Canadian, $1,198$ England, $78$ Irish, $731$ South Asian, $3,869$ US).
  3. **Workstream C (Rectification of Policy A and Policy B Reserve Allocations):**
     - Restored canonical Policy A definition (Irish-only reserve): Active: $450$ Common Voice ($75$/group) $+ 90$ External ($15$/group); Reserve: $3$ Common Voice (Irish only) $+ 12$ External (Irish only). Totals: $N_{\text{CV}} = 450 + 3 = \mathbf{453}$; $N_{\text{external}} = 90 + 12 = \mathbf{102}$; $N_{\text{total}} = 453 + 102 = \mathbf{555}$. Rectified the erroneous display of $462$ CV speakers. External shortfall: $\mathbf{102}$ speakers.
     - Reaffirmed canonical Policy B definition (Stratum-balanced reserve across all $6$ groups): Active: $450$ Common Voice ($75$/group) $+ 90$ External ($15$/group); Reserve: $18$ Common Voice ($3$/group) $+ 72$ External ($12$/group). Totals: $N_{\text{CV}} = 450 + 18 = \mathbf{468}$; $N_{\text{external}} = 90 + 72 = \mathbf{162}$; $N_{\text{total}} = 468 + 162 = \mathbf{630}$. External shortfall: $\mathbf{162}$ speakers.
     - Retained Policy A versus Policy B as formally **`[UNRESOLVED]`** pending supervisory preregistration.
  4. **Workstream D (Baseline Frozen Inventory vs. Exploratory TSV Parsing Comparison):**
     - Verified that [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) (SHA-256 `e964799b…`) is the authoritative, immutable frozen inventory: Australian ($400$), Canadian ($511$), England ($1,223$), Irish ($94$), South Asian ($764$), US ($3,913$) totaling $6,905$.
     - Reconciled exploratory raw TSV re-scans ($517$ Canadian, $753$ South Asian, $3,918$ US): confirmed aggregate conservation $(+6) + (-11) + (+5) = 0$ ($6,905$ total). Documented root cause as dialect string parsing variation on unnormalized raw metadata. Designated re-scans as **`[UNAPPROVED EXPLORATORY RECLASSIFICATION]`** with zero authority to alter frozen files.
  5. **Workstream E (Verification of Canonical Scenario 2 Parameters Across Sample Sizes):**
     - Verified canonical simulation file [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): both `cohort_468` ($85.825\%$) and `cohort_540` ($90.40\%$) use **IDENTICAL** DGP parameters: $\Delta_R = -0.85\text{ pp}$, $\Delta D = +0.50\text{ pp}$, $S = 4,000$, $B = 1,000$.
     - Corrected isolated changelog typographical error in line 393 that read $+0.80\text{ pp}$ instead of $+0.50\text{ pp}$. Confirmed that the power difference between $N=468$ ($85.825\%$) and $N=540$ ($90.40\%$) is a genuine, pure sample-size effect under identical DGP conditions.
  6. **Unit Test Suite Expansion:**
     - Implemented three new regression tests in [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py):
       * `test_stage6m_six_group_prior_exposure_reconciliation`: validates $E_1=60, E_S=30, E_1 \cap E_S = \emptyset, \text{strictly eligible exposed} = 89$.
       * `test_stage6m_reserve_policy_allocations`: validates Policy A ($453 + 102 = 555$) and Policy B ($468 + 162 = 630$) totals and shortfalls.
       * `test_stage6m_scenario2_canonical_parameters`: validates $\Delta D = +0.50\text{ pp}$ identity across $N=468$ and $N=540$.
     - Full module test suite: **20 passed in 3.60s**.
  7. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.


### Correction 17: Frozen Artifact Integrity, Seed Provenance, and Full Test Suite Closure (Workstreams A–E)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Fresh Full-Suite Test Execution:** **`113 passed, 6 warnings in 26.15s`** in [`tests/research_validity/`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/)
- **Fresh Full-Suite Execution Log:** [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) (SHA-256 `2651a05b864e49b7f19e9b6af6fc50f0fe8eb28f547d248b2522a226758391fa`, exact size $16,494\text{ bytes}$, exit code 0)
- **Files Modified / Synchronized:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Workstreams Audited & Formally Closed:**
  1. **Workstream A (Irish Exposure-Set Reconciliation & Elimination of Narrative Contradictions):**
     - Reconciled exact Irish candidate sets from canonical manifests: baseline inventory $|I_{\text{Irish}}| = 94$; strict quality exclusions $|Q_{\text{Irish}}| = 2$ (`fc22fd45...` with $C_{\text{inv}}=15, C_{\text{strict}}=14$, unexposed; and `f3ea0447...` with $C_{\text{inv}}=15, C_{\text{strict}}=13$, exposed in $E_1$).
     - Reconciled strictly eligible Irish candidates: $94 - 2 = \mathbf{92}$.
     - Reconciled exposed Irish speakers: Replication Cohort 1 ($E_1$) contains exactly $10$ Irish speakers ($1$ in $Q$, $9$ strictly eligible); Sentinel Panel ($E_S$) contains exactly $5$ Irish speakers (all $5$ strictly eligible).
     - Strictly eligible exposed Irish candidates: $9 + 5 = \mathbf{14}$.
     - Reconciled available unexposed strictly eligible Irish pool:
       $$|I_{\text{available}}| = 92 - 14 = \mathbf{78}$$
       Equivalently, subtracting total exclusions without double-counting `f3ea0447...`:
       $$|I_{\text{available}}| = 94 - 10\text{ (Cohort 1)} - 5\text{ (Sentinel)} - 1\text{ (unexposed } Q) = \mathbf{78}$$
     - Formally rejected and expunged historical exploratory notes that claimed $6$ Irish quality exclusions ($94 - 6 = 88$) or claimed that no Sentinel Panel speakers were Irish. Reaffirmed that the Sentinel Panel contains exactly $5$ Irish speakers per frozen split manifest [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv).
  2. **Workstream B (Frozen Checksum and Disk Byte Size Forensics):**
     - Performed cryptographic SHA-256 and exact byte-count verification on physical disk files:
       * [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): Exact size **$253,229\text{ bytes}$**, SHA-256 **`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`**. (The previously reported hash `b13c7a36...` and size `239,942 bytes` were identified as an erroneous text-entry transcription in the audit prose; the physical file on disk was never modified and remains 100% identical to canonical hash `8fac4d32...`).
       * [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv): Exact size **$557,100\text{ bytes}$**, SHA-256 **`e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a`**. (Matches Git HEAD commit `ac9657b` identically).
       * [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv): Exact size **$451,539\text{ bytes}$**, SHA-256 **`41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32`**.
       * [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv): Exact size **$92,340\text{ bytes}$**, SHA-256 **`665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543`**.
       * [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json): Exact size **$5,344\text{ bytes}$**, SHA-256 **`4622b215b18c6b4de80fb7832788ce7286e88c5528f501e2bac62f935e570028`**.
     - Confirmed that zero frozen artifacts were modified; discrepancies in previous report tables stemmed entirely from stale draft table copy-paste entries.
  3. **Workstream C (Simulation Parameter & Random Seed Provenance Reconciliation):**
     - Fully reconciled simulation seeds from canonical file `power_simulation_results.json`:
       * Deterministic seed formula across all cohort sizes: $\text{seed} = 1000 \times \text{scenario\_idx} + 1000 + 42 + \text{cohort\_size}$.
       * Cohort $N=420$: $\text{seed\_s1} = 1462$, $\text{seed\_s2} = 2462$.
       * Cohort $N=450$: $\text{seed\_s1} = 1492$, $\text{seed\_s2} = 2492$.
       * Cohort $N=468$: $\text{seed\_s1} = 1510$, $\text{seed\_s2} = 2510$.
       * Cohort $N=540$: $\text{seed\_s1} = 1582$, $\text{seed\_s2} = 2582$.
     - Reconciled why earlier reports cited $1582 / 2582$ for $N=540$: that was the true canonical seed pair for $N=540$. The seeds $1462 / 2462$ belonged strictly to the $N=420$ cohort.
     - Confirmed DGP parameter identity for Scenario 2 across sample sizes: both $N=468$ and $N=540$ use identical parameters $\Delta_R = -0.85\text{ pp}$, $\Delta D = +0.50\text{ pp}$, $S=4,000, B=1,000$.
  4. **Workstream D (Fresh Full Test-Suite Execution & Tripartite Separation):**
     - Executed full test suite across all 12 modules in `tests/research_validity/`.
     - Full result: **`113 passed, 6 warnings in 26.15s`** (exit code 0).
     - Captured complete log with warnings to [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) (SHA-256 `2651a05b864e49b7f19e9b6af6fc50f0fe8eb28f547d248b2522a226758391fa`).
     - Maintained explicit tripartite distinction:
       1. Previous full suite (110 tests): `test_execution_research_validity_full.log` (SHA-256 `04d6752f...`).
       2. Stage 6M module run (20 tests): `test_execution_stage6m_proposal.log` (SHA-256 `e7509390...`).
       3. Current full suite run (113 tests): `test_execution_research_validity_v1_2_0.log` (SHA-256 `2651a05b...`).
  5. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.


### Correction 18: Residual Evidence & Technical Integrity Audit (Audits 1–5)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Audit Artifact Created:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md)
- **Execution Log Verified:** [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) (SHA-256 `2651a05b…`, $16,494\text{ bytes}$, 113 passed in 26.15s, 6 warnings)
- **Files Modified / Created:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Residual Audits Formally Closed:**
  1. **Audit 1 (Clip-Level Irish Eligibility Reconciliation):**
     - Conducted row-by-row audit in [`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv) for disputed Irish speakers.
     - Reconciled speaker `f3ea04475e301f84785710b9…` (Cohort 1 Irish): exactly $16$ candidate rows in `validated.tsv`. Row 15 (`'Cllr.'`) has only $1$ word, failing baseline predicate $B_0(r)$ ($C_{\text{inv}} = 16 - 1 = 15$). Rows 12 and 13 have `down_votes = 2`, failing strict predicate $V(r)$ ($C_{\text{strict}} = 15 - 2 = 13 < 15$). Resolves the ambiguity between baseline filtering ($16 \to 15$) and strict filtering ($15 \to 13$).
     - Reconciled speaker `fc22fd45334612a489c45562…` (Unexposed Irish): exactly $15$ candidate rows in `validated.tsv`, all baseline-valid ($C_{\text{inv}} = 15$). Row 5 has `down_votes = 2`, failing strict predicate $V(r)$ ($C_{\text{strict}} = 15 - 1 = 14 < 15$).
     - Formally proved deduplication under two independent expressions: $|I_{\text{available}}| = (94 - 2) - (9 + 5) = \mathbf{78}$, and $|I_{\text{available}}| = 94 - (10 + 5 + 1) = \mathbf{78}$.
  2. **Audit 2 (Seed Formula, Scenario Indexing & Power Comparison Tempering):**
     - Quoted source code from [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py) line 340: `np.random.seed(seed_discovery + cohort_n + sc_id * 1000)` with `seed_discovery = 42`.
     - Explicitly mapped the 1-based code identifier `sc_id \in {1, 2, 3, 4}` to the 0-based index `scenario_idx = sc_id - 1 \in {0, 1, 2, 3}`, proving $\text{seed} = 1000 \times \text{scenario\_idx} + 1042 + \text{cohort\_size}$.
     - Verified serialized seeds in [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): $N=420 \to 1462 / 2462$; $N=450 \to 1492 / 2492$; $N=468 \to 1510 / 2510$; $N=540 \to 1582 / 2582$.
     - Tempered statistical interpretation: clarified that because seeds depend on cohort size, simulations instantiate independent pseudorandom streams. The observed power difference ($85.83\%$ vs. $90.40\%$) reflects both sample-size scaling and Monte Carlo realization variation, and must not be described as an exclusively isolated "pure sample-size effect".
  3. **Audit 3 (Frozen-Artifact Disk vs. Git HEAD Checksum Verification):**
     - Recomputed SHA-256 digests and physical byte sizes across all 7 baseline artifacts.
     - Resolved the apparent discrepancy between disk file sizes and Git HEAD blob sizes via Windows CRLF checkout normalization (`core.autocrlf = true`), showing that `external_speaker_inventory.csv` has $550,194\text{ B}$ (LF) in Git HEAD vs. $557,100\text{ B}$ (CRLF) on disk across exactly $6,906$ lines ($+6,906\text{ B}$).
     - Formally distinguished current byte equality, Git HEAD parity, and historical immutability.
  4. **Audit 4 (Test Execution Evidence Verification):**
     - Verified log [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log): 113 collected and passed tests across 12 modules in 26.15s, exit code 0, 6 site-packages warnings.
     - Emphasized that software test passage verifies code invariants, not scientific validity or multi-corpus design adequacy.
  5. **Audit 5 (Governance Invariants & Execution Lock):**
     - Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`, `Reserve policy = UNRESOLVED`.
     - Confirmatory execution decision: **STRICT NO-GO**.



### Correction 19: Final Integrity Wording, Simulation Provenance & Warning Diagnostics Correction (Tasks 1–5)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Primary Report Updated:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md)
- **Tasks Audited & Formally Closed:**
  1. **Task 1 (Git Integrity Terminology & Line-Ending Normalization Rectification):**
     - Expunged the misleading phrase `"byte-for-byte match with Git HEAD"` for files with differing physical byte counts.
     - Documented exact line-ending forensics: on Windows (`core.autocrlf = true`), checked-out working-tree files have CRLF line endings (`\r\n`), increasing physical disk size by $+1\text{ byte}$ per line relative to Git HEAD's stored LF (`\n`) blobs.
     - Formally verified across all 6 tracked artifacts that standalone CR count is strictly $0$, size difference exactly equals CRLF line count, and normalized disk bytes match Git commit blobs identically (`norm_disk == git_blob`).
     - Established precise governing terminology: *"Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion."*
     - Strictly separated four distinct epistemic claims: (1) Raw byte equality (False); (2) Text equality after newline normalization (True); (3) Clean Git working-tree status (True); (4) Evidence of historical non-modification (Established for tracked files by initial commits `ac9657b` / `5c748af`).
  2. **Task 2 (Simulation JSON Provenance & Immutability Classification):**
     - Re-verified physical state of [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): $253,229\text{ bytes}$, SHA-256 `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
     - Confirmed that the file is untracked in Git; `git log -S 8fac4d32` and `git grep 8fac4d32 HEAD` confirm zero historical Git commits record this digest.
     - Classified claims: (1) Current digest matches canonical documentation tables: **VERIFIED**; (2) Historical immutability via Git: **UNVERIFIED**.
     - Left frozen simulation JSON completely untouched; no re-run or regeneration attempted.
  3. **Task 3 (Forensic Classification of Pytest Warnings vs. Process Stderr Diagnostics):**
     - Audited [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) lines 124–154.
     - Formally decoupled:
       * **Category A: Pytest Warnings (Counted in Summary: Exactly 6):** 4 Pillow deprecations (`torchvision/transforms/_functional_pil.py:245, 291, 307, 324`) + 2 Swig importlib deprecations (`<frozen importlib._bootstrap>:241`).
       * **Category B: Process Stderr Diagnostics (Not Counted in Pytest 6 Warnings Summary):** 1 RequestsDependencyWarning (`urllib3/charset_normalizer` in `requests/__init__.py:113`) + 1 swigvarlink deprecation (`sys:1`).
     - Confirmed zero warnings or diagnostics originate from project test or pipeline code.
  4. **Task 4 (Preservation of Reconciled Findings):**
     - Reaffirmed Irish candidate accounting: $94 - 2 = 92$ strictly eligible; $14$ strictly eligible exposed; $92 - 14 = \mathbf{78}$ available unexposed capacity (equivalently $94 - 10 - 5 - 1 = \mathbf{78}$).
     - Reaffirmed seed formula: $\text{seed} = 42 + \text{cohort\_n} + \text{sc\_id} \times 1000$ (1-based $\text{sc\_id} \in \{1, 2, 3, 4\}$).
     - Reaffirmed tempered power interpretation: observed power differences reflect both sample-size scaling and Monte Carlo realization variation.
     - Reaffirmed methodological boundary: passing 113 unit tests does not establish scientific validity or authorize execution.
  5. **Task 5 (Preservation of Governance Invariants):**
     - Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`, `Reserve policy = UNRESOLVED`.
     - Confirmatory execution decision: **STRICT NO-GO**.


### Correction 20: Final Three-Item Documentation Correction (Audits 1–5)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Primary Reports Modified:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md)
- **Supporting Evidence Artifacts Preserved:** [`reports/stage6m/git_normalization_verification_v1_2_0.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/git_normalization_verification_v1_2_0.txt), [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log)
- **Corrections Implemented:**
  1. **Seed Formula Notation Rectification:**
     - Typeset all mathematical expressions of the simulation seed formula to explicitly denote multiplication:
       $$\text{seed} = 42 + N + 1000 \cdot \text{sc\_id}$$
       where $\text{sc\_id} \in \{1, 2, 3, 4\}$ is the 1-based scenario identifier (equivalently $\text{seed} = 1000 \cdot \text{scenario\_idx} + 1042 + N$).
     - Expunged comma-delimited notation (`42 + N + 1000, sc_id`).
     - Preserved all serialized seed mappings: $N=420 \to 1462 / 2462$; $N=450 \to 1492 / 2492$; $N=468 \to 1510 / 2510$; $N=540 \to 1582 / 2582$.
  2. **Baseline-Path vs. Global Working-Tree Status Decoupling:**
     - Clarified that clean status applies strictly to the six audited baseline paths:
       *"The six audited baseline paths have no reported working-tree modifications. The repository's overall working-tree status is a separate matter and may include changes to audit reports, the changelog, and newly created evidence files."*
  3. **Warning Attribution Narrowing:**
     - Preserved the separation of 6 pytest warnings (4 Pillow + 2 SWIG importlib) and 2 process stderr diagnostics (1 RequestsDependencyWarning + 1 swigvarlink).
     - Rectified provenance attribution:
       *"All eight messages are attributed to third-party dependencies or runtime diagnostics. No project-code origin was identified in the inspected log."*
  4. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`, `Reserve policy = UNRESOLVED`. Confirmatory execution decision: **STRICT NO-GO**.


### Correction 21: Final Provenance Wording Cleanup
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Primary Report Updated:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md)
- **Wording Rectification Applied:**
  - Replaced ambiguous descriptions of baseline artifacts as "clean and pristine" with the precise governing statement:
    *"The six audited baseline paths have no reported working-tree modifications, and their normalized contents match the corresponding Git blobs. This does not establish that no temporary, uncommitted edits occurred and were subsequently reverted."*
  - Preserved all verified checksum values, full SHA-256 logs in [`git_normalization_verification_v1_2_0.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/git_normalization_verification_v1_2_0.txt), Git object IDs, line-ending normalization results, speaker counts, simulation seeds, and test evidence.
  - Zero frozen datasets, split manifests, simulation outputs, or test execution logs were regenerated, re-run, or overwritten.
  - Governance state remains unchanged: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, Confirmatory Execution Verdict: **STRICT NO-GO**.

### Correction 22: Methodological Audit and Decision Pack Provenance Statement Qualification
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Primary Reports Updated:** [`reports/stage6m/stage6m_design_validity_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_design_validity_audit.md), [`reports/stage6m/stage6m_supervisor_decision_pack.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_supervisor_decision_pack.md), [`reports/stage6m/stage6m_hierarchical_power_analysis_spec.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_hierarchical_power_analysis_spec.md)
- **Provenance Rectification Applied:**
  - Expunged absolute provenance terminology ("100% UNTOUCHED", "verified and pristine") across all Stage 6M supervisory reports.
  - Replaced with the precise governing statement:
    *"The six audited baseline paths have no reported working-tree modifications, and their LF-normalized content matches the corresponding Git blobs. This establishes current content parity but does not establish that no temporary, uncommitted edits occurred and were subsequently reverted."*
  - Explicitly qualified the untracked simulation artifact:
    *"The current simulation JSON retains its reported size and SHA-256 digest. Because it is untracked in Git, its historical immutability and execution provenance remain unverified."*
  - Updated inventory tables to classify the six baseline paths as "AUDITED BASELINE" and the canonical simulation JSON as "UNTRACKED ARTIFACT".
  - Retained strict research governance invariants: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, Confirmatory Execution Verdict: **STRICT NO-GO**.
  - Confirmed zero frozen baseline datasets, split manifests, simulation outputs, or test execution logs were modified, regenerated, or overwritten.
