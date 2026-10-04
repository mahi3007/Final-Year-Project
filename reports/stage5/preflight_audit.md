# Stage 5 Pre-Flight Validation Audit Report

**Project Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition  
**Protocol Version:** `v1.0.0-canonical`  
**Evaluation Scope:** Stage 5 Pre-Flight Readiness, Data Holdout Feasibility, and Protocol Integrity  
**Date of Audit:** 2026-09-30  
**Lead Auditor:** Lead Research Engineer & Reproducibility Suite  
**Audit Outcome:** `STAGE 5 CONTROLLER IMPLEMENTATION IS BLOCKED`

---

## 1. Executive Summary

In accordance with the mandatory protocol directive, the lead research engineering suite has executed a comprehensive **Stage 5 Pre-Flight Audit** prior to writing any controller implementation code. 

The audit confirms that while empirical phenomenon characterization, consecutive-window persistence, and gate decision rules have been successfully formalized, **the proposed Stage 5 data allocation fails the fundamental speaker independence invariant**. Specifically, the proposed Stage 5 final evaluation partition reuses six calibration speakers, introducing circularity. Furthermore, mathematical analysis demonstrates that a balanced, 5-way speaker-disjoint partition across the 6 accent groups requires 30 speakers, exceeding the 24 speakers available in L2-ARCTIC.

Consequently, **Stage 5 controller implementation is formally BLOCKED** until the external holdout dataset architecture is approved and provisioned.

---

## 2. Pre-Flight Verification Checklist

| Audit Item | Protocol Requirement | Current Status | Supporting Artifact |
| :--- | :--- | :---: | :--- |
| **Stage 4 Stress Bootstrap** | $B=1,000$ paired speaker-cluster CIs & UCBs | **PASS** | `reports/stage4/stage4e_stress_speaker_cluster_bootstrap.csv` |
| **Threshold Provenance** | Frozen $\delta_G = 0.02, \delta_D = 0.02$ from calibration | **PASS** | `configs/stage4_thresholds.json`, `reports/stage4/delta_calibration_report.md` |
| **Consecutive Persistence** | Systematic harm across consecutive prequential windows | **PASS** | `reports/stage5/predecessor_persistence.csv`, `reports/stage5/predecessor_persistence.md` |
| **$K=4$ Discrepancy** | Forensic trace of blank-token representation dynamics | **PASS** | `reports/stage4/k_sweep_provenance_analysis.md` |
| **Stage 5 Data Allocation** | Mutual speaker disjointness across all roles | **FAIL** | `reports/stage5/data_feasibility_report.md` |
| **Final Eval Independence** | $\mathcal{S}_{\text{cal}} \cap \mathcal{S}_{\text{eval}} = \emptyset$ | **FAIL** | 6 of 6 proposed final evaluation speakers are calibration speakers |
| **Sentinel Independence** | $\mathcal{S}_{\text{adapt}} \cap \mathcal{S}_{\text{sentinel}} = \emptyset$ | **PASS** | Clean 6 vs 6 split of the 12 non-dev/non-cal speakers |
| **Gate Decision Rule** | Canonical $UCB \le \epsilon$ rule vs $LCB > 0$ reconciled | **PASS** | `docs/adr/ADR-005-stage5-gate-rule.md` |
| **Rollback Semantics** | Shadow candidate, reject $\to \theta_{t+1}=\theta_t$ (never $\theta_{t-1}$) | **PASS** | `docs/adr/ADR-005-stage5-gate-rule.md` |
| **$\delta$ vs $\epsilon$ Separation** | $\delta$ (scientific threshold) $\neq \epsilon$ (operating tolerance) | **PASS** | `docs/adr/ADR-005-stage5-gate-rule.md` |
| **Automated Test Suite** | 31/31 unit, integration, and validity tests passing | **PASS** | Test suite passing (46.13s execution time) |

---

## 3. Detailed Answers to Core Protocol Questions

### 1. Were the proposed final evaluation speakers previously used for calibration?
**YES (100% OVERLAP).**  
Inspection of `datasets/splits/calibration.csv` confirms its speakers are:
$$\mathcal{S}_{\text{cal}} = \{\text{HJK}, \text{HKK}, \text{MPXM}, \text{SKA}, \text{TNI}, \text{TNT}\}$$
The Stage 4.1 allocation plan proposed evaluating the final Stage 5 controller on:
$$\mathcal{S}_{\text{eval}} = \{\text{SKA}, \text{HKK}, \text{HJK}, \text{MPXM}, \text{TNI}, \text{TNT}\}$$
Because $\delta_G$, $\delta_D$, and adaptation window size $K=4$ were derived directly on these speakers, evaluating the final controller on them breaks air-gapping and invalidates claims of generalizable safety.

---

### 2. Is a speaker-independent Stage 5 allocation possible using L2-ARCTIC alone?
**NO (MATHEMATICALLY IMPOSSIBLE).**  
Stage 5 requires 5 distinct partitions, each containing at least 1 speaker from each of the 6 accent groups (`Arabic`, `Hindi`, `Korean`, `Mandarin`, `Spanish`, `Vietnamese`) to compute $\max_g \Delta_g$ and disparity $D$:
$$N_{\text{required}} = |\mathcal{S}_{\text{dev}}| + |\mathcal{S}_{\text{cal}}| + |\mathcal{S}_{\text{adapt}}| + |\mathcal{S}_{\text{sentinel}}| + |\mathcal{S}_{\text{eval}}| = 6 \times 5 = 30 \text{ speakers}$$
Because L2-ARCTIC contains exactly 24 speakers (4 per group), the Pigeonhole Principle dictates:
$$\forall g \in G, \quad n_g = 4 < 5 \text{ partitions}$$
An external speech dataset matching the demographic accent groups (e.g. Mozilla Common Voice accented English or SpeechOcean762) is **strictly required** to populate $\mathcal{S}_{\text{eval}}$.

---

### 3. Is the consecutive-window persistence criterion explicitly demonstrated?
**YES (CONFIRMED AND DOCUMENTED).**  
Consecutive-window persistence analysis across the 3 primary stress conditions was evaluated and documented in `reports/stage5/predecessor_persistence.csv` and `reports/stage5/predecessor_persistence.md`:
- **SUTA + Reverberation (Vietnamese):** Across all 4 consecutive window transitions ($w_{25} \to w_{26} \to w_{27} \to w_{28} \to w_{29}$), subgroup regression never drops below $+3.26\%$, strictly exceeding $\delta_G = 2.00\%$ throughout (100% persistence).
- **DSUTA + Severe Noise 5 dB (Vietnamese):** Across all 4 consecutive window transitions, $\Delta_g \ge +2.17\% > 2.00\%$ persistently (100% persistence).
- **DMSUTA + Babble Noise 15 dB (Hindi):** Across all 24 consecutive window transitions from window 5 through window 29, $\Delta_g \ge +8.15\% \gg 2.00\%$ persistently (100% persistence).

---

### 4. Is the gate decision rule consistent with the canonical protocol?
**YES (FORMALIZED IN ADR-005).**  
The protocol mismatch between the canonical $UCB \le \epsilon$ rule and the Stage 4.1 $LCB > 0$ rule has been resolved in `docs/adr/ADR-005-stage5-gate-rule.md`.  
The overly permissive $LCB > 0$ rule has been formally rejected. The canonical tripartite rule is frozen:
$$\text{ACCEPT}(\theta') \iff UCB_{95}(\Delta_R) \le \epsilon_R \quad \land \quad UCB_{95}(\max_g \Delta_g) \le \epsilon_G \quad \land \quad UCB_{95}(\Delta_D) \le \epsilon_D$$
Candidate updates breaching any bound are immediately rejected.

---

### 5. Are the rollback semantics safe?
**YES (SHADOW CANDIDATE ARCHITECTURE FROZEN IN ADR-005).**  
The erroneous phrasing suggesting rollback to $\theta_{t-1}$ has been eliminated. The architecture enforces:
1. Live model $\theta_t$ is immutable and never modified during adaptation.
2. Candidate $\theta'$ is adapted in an isolated shadow clone.
3. If ACCEPT: $\theta_{t+1} \leftarrow \theta'$.
4. If REJECT: $\theta_{t+1} \leftarrow \theta_t$ (candidate discarded, current live model retained).
This ensures that a rejection at window $t$ never erases previously accepted adaptations from windows $0 \dots t-1$.

---

### 6. Are $\delta$ and $\epsilon$ properly separated?
**YES.**  
As established in ADR-005:
- $\delta_G = 0.0200$ and $\delta_D = 0.0200$ are pre-registered scientific discovery thresholds representing minimum meaningful empirical shifts.
- $\epsilon_R, \epsilon_G, \epsilon_D$ are engineering operating tolerances defining the gate's decision boundary. For the primary intervention validation, $\epsilon_R = 0.0000$, $\epsilon_G = 0.0200$, and $\epsilon_D = 0.0200$.

---

### 7. What exact files and configurations must change?
1. **`reports/stage4/stage5_data_allocation_plan.md`:** Must be updated to revoke the assignment of calibration speakers to $\mathcal{S}_{\text{eval}}$.
2. **`datasets/splits/stage5_eval.csv`:** A new split must be generated from an approved external accented English corpus (e.g. Common Voice) with 6 accent groups matching L2-ARCTIC.
3. **`configs/stage5_gate_config.json`:** A new configuration manifest freezing $\epsilon_R, \epsilon_G, \epsilon_D$, $B=1,000$, and panel IDs based on ADR-005.
4. **`src/dsg_ctta/controller/`:** Implement the controller contracts and shadow candidate architecture in accordance with Stage 5A–5D.

---

## 4. Formal Recommendation & Next Actions

Stage 5 controller implementation is **PAUSED** at the pre-flight gate. 

To unblock Stage 5:
1. User confirms Strategy A (External corpus ingestion for $\mathcal{S}_{\text{eval}}$).
2. Curate and verify the external 6-group evaluation partition (`datasets/splits/stage5_eval.csv`).
3. Cryptographically verify 0 speaker leakage between L2-ARCTIC (all 24 speakers) and the external evaluation partition.
4. Proceed to Phase 6 (Stage 5A Controller Contract Interfaces).
