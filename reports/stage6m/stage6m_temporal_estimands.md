# Stage 6M Methodological Specification: Temporal Estimands, Counterfactual Rollouts & Policy Contrasts

**Protocol:** `v1.2.0-stage6m-proposal`  
**Governing Standard:** ADR-005  
**Document Status:** Formal Estimand Specification for Stakeholder Review  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED**  
**Submission Date:** 2026-10-12  

---

## 1. Executive Summary & Estimand Separation Mandate

A central finding of the Stage 5M post-execution audit is that **same-window diagnostic fit, single-step prospective impact, multi-step cumulative trajectory health, and end-to-end streaming policy performance represent fundamentally distinct mathematical objects**. Evaluating one cannot substitute for evaluating another.

This document establishes the formal mathematical definitions of all temporal estimands for Stage 6M, specifying the post-branch continuation policy, prequential streaming sequence, and terminal-window accounting.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   TEMPORAL ESTIMAND TAXONOMY                                │
├────────────────────────┬──────────────────────┬─────────────────────────────────────────────┤
│ Level                  │ Notation             │ Exact Operational Definition                │
├────────────────────────┼──────────────────────┼─────────────────────────────────────────────┤
│ Diagnostic             │ ΔE_t^same            │ Error delta on the adaptation window audio  │
│ (Same-Window)          │                      │ audio B_t used to compute gradients         │
├────────────────────────┼──────────────────────┼─────────────────────────────────────────────┤
│ Candidate-Level        │ ΔE_{t,1}^cand        │ Paired counterfactual difference on the     │
│ (One-Step Prospective) │                      │ immediate next streaming window B_{t+1}     │
├────────────────────────┼──────────────────────┼─────────────────────────────────────────────┤
│ Candidate-Level        │ ΔE_{t,h}^cand        │ Cumulative divergence over h future windows │
│ (Multi-Step Rollout)   │                      │ under a specified post-branch policy        │
├────────────────────────┼──────────────────────┼─────────────────────────────────────────────┤
│ End-to-End Policy      │ Δ_policy             │ Stream-wide trajectory contrast across      │
│ (Full Trajectory)      │                      │ full sequence of windows B_0 ... B_{T-1}    │
└────────────────────────┴──────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. Candidate-Level Estimands

Let $\theta_t$ denote the retained live parameter state of the streaming model prior to the decision at window $t$. Let $\theta'_t = \operatorname{Adapt}(\theta_t, X_t)$ denote the candidate model adapted on unlabeled audio $X_t$.

### 2.1 Single-Step Prospective Effect ($h = 1$)
The immediate one-step prospective effect on subsequent window $B_{t+1}$ is:
$$\Delta E_{t,1}^{\text{cand}} = E(\theta'_t, B_{t+1}) - E(\theta_t, B_{t+1})$$
where:
- $E(\theta, B) = \frac{\text{LevenshteinErrors}(f_\theta(X_B), Y_B)}{N_{\text{words}}(Y_B)}$ is the word error rate evaluated with quarantined ground-truth transcripts $Y_B$.
- **Causal Interpretation Boundary for Rejected Updates:** A rejected candidate update evaluated on subsequent window $B_{t+1}$ with $\Delta E_{t,1}^{\text{cand}} > 0$ is formally designated as **Rejection of a Counterfactually Harmful Candidate State**, *not* a proven operational catastrophe averted. Because the candidate model was rejected and not deployed into the live streaming trajectory, its real-world cumulative divergence was unobserved. The term denotes an offline counterfactual contrast on identical audio.
- **Status:** `PROPOSED` (validated in Stage 5M for single updates from base state; `REQUIRES EMPIRICAL VALIDATION` for cumulative states).

### 2.2 Multi-Step Cumulative Rollout ($h > 1$)
To measure whether an individual update causes cumulative divergence or delayed benefits over a horizon $h \in \{3, 5\}$, the protocol defines two distinct continuation policies:

#### Policy A: Frozen-Weights Rollout (Static Horizon Evaluation)
In Policy A, both the candidate state $\theta'_t$ and retained state $\theta_t$ are evaluated across windows $B_{t+1}, \dots, B_{t+h}$ **without performing further adaptation gradient steps**:
$$\Delta E_{t,h}^{\text{cand,frozen}} = \frac{1}{\sum_{k=1}^h N_w(B_{t+k})} \sum_{k=1}^h \left[ \text{Errors}(f_{\theta'_t}(X_{t+k}), Y_{t+k}) - \text{Errors}(f_{\theta_t}(X_{t+k}), Y_{t+k}) \right]$$
- **Scientific Interpretation:** Measures the persistence of the specific parameter perturbation $\Delta \theta'_t$ on future acoustic segments under fixed inference.
- **Status:** `PROPOSED`.

#### Policy B: Active-Branch Rollout (Dynamic Continuation)
In Policy B, the candidate branch (initialized with $\theta'_t$) and the retained branch (initialized with $\theta_t$) **each continue streaming and adapting independently** on subsequent windows $B_{t+1}, \dots, B_{t+h}$ according to the assigned streaming rule (e.g., ungated or gated):
$$\Delta E_{t,h}^{\text{cand,active}} = \frac{1}{\sum_{k=1}^h N_w(B_{t+k})} \sum_{k=1}^h \left[ \text{Errors}(f_{\theta_{t+k}^{(\text{cand})}}(X_{t+k}), Y_{t+k}) - \text{Errors}(f_{\theta_{t+k}^{(\text{ret})}}(X_{t+k}), Y_{t+k}) \right]$$
- **Scientific Interpretation:** Measures the true causal divergence between the trajectory initiated by accepting the candidate versus the trajectory initiated by rejecting it.
- **Status:** `PROPOSED` (Requires isolated counterfactual replay execution).

> [!CRITICAL]
> **Inferential Non-Equivalence**: It is scientifically invalid to assert that a candidate is cumulatively safe across multi-step streaming based solely on $\Delta E_{t,1}^{\text{cand}} \le 0$. An update that improves window $t+1$ may destabilize representations such that window $t+2$ collapses. Stage 6M strictly prohibits conflating $h=1$ outcomes with $h > 1$ rollout outcomes.

---

## 3. End-to-End Policy-Level Contrasts

Policy-level estimands measure the aggregate trajectory performance across the entire stream of $T$ windows ($B_0, B_1, \dots, B_{T-1}$).

### 3.1 Primary Contrast: Gated CTTA vs. Ungated CTTA
The primary scientific contrast evaluates whether the Disparity Safety Gate protects against unconstrained adaptation drift:
$$\Delta_{\text{Gated-Ungated}} = E_{\text{Arm 3 (Gated)}}(B_{0:T-1}) - E_{\text{Arm 2 (Ungated)}}(B_{0:T-1})$$
- **Effect Direction:** Negative values ($\Delta < 0$) favor the Gated method (fewer word errors).
- **Practical Interpretation:** Quantifies the net harm mitigated by filtering updates through the Sentinel Panel.
- **Disparity Safety Requirement:** To establish safety, the trajectory contrast must also satisfy the one-sided 95% upper confidence bound constraint:
  $$UCB_{95\%}(\Delta D) \le +1.40\text{ pp}$$
  (bounding inter-group disparity expansion to clinically/operationally negligible levels, representing 70% of the operational gate threshold $\epsilon_D = +2.00\text{ pp}$).
- **Status:** `PROPOSED`.

### 3.2 Secondary Contrast: Gated CTTA vs. Static No-Adapt
The secondary contrast evaluates whether adaptive updates yield a net improvement over a static unadapted model:
$$\Delta_{\text{Gated-Static}} = E_{\text{Arm 3 (Gated)}}(B_{0:T-1}) - E_{\text{Arm 1 (Static)}}(B_{0:T-1})$$
- **Effect Direction:** Negative values ($\Delta < 0$) indicate adaptation was beneficial overall.
- **Scientific Caveat:** A gated system may successfully outperform ungated adaptation ($\Delta_{\text{Gated-Ungated}} < 0$) while still underperforming the static baseline ($\Delta_{\text{Gated-Static}} > 0$) if adaptation in general degrades performance on that stream. Both contrasts must be reported side-by-side.
- **Status:** `PROPOSED`.

---

## 4. Prequential Streaming Sequence & Label Isolation Firewall

At every window index $t \in \{0, 1, \dots, T-1\}$, the operational system enforces the strict chronological execution sequence:

```
Step 1: Ingest Unlabeled Audio Batch X_t (K=4 clips, duration ~15s)
Step 2: Emit Live Prediction Ŷ_t = f(X_t; θ_t) using CURRENT live weights θ_t
Step 3: Transmit Ŷ_t to Quarantined Evaluation Vault (Offline scoring with Y_t)
Step 4: Execute Unsupervised CTTA Adaptation: θ'_t = Adapt(θ_t, X_t) [NO LABELS]
Step 5: Present θ'_t and θ_t to Sentinel Panel S (N=30 disjoint speakers)
Step 6: Compute Bootstrap UCBs (ΔR, max_g Δg, ΔD) over Sentinel Panel
Step 7: Operational Gate Decision:
        - If ACCEPT: θ_{t+1} ← θ'_t
        - If REJECT: θ_{t+1} ← θ_t
Step 8: Serialize θ'_t and θ_t to Isolated Research Replay Vault
Step 9: Proceed to Window t+1
```

- **Invariant Check:** Ground-truth references $Y_t$ are never accessible in memory during Steps 4, 5, 6, or 7.
- **Status:** `VERIFIED FROM ARTIFACT` (Implemented in `LabelIsolationSanitizer` and verified in Stage 5M tests).

---

## 5. Terminal-Window Accounting & Invariants

A rigorous streaming benchmark must explicitly specify the boundary conditions at the end of the stream.

### 5.1 Terminal Prediction-Only Window Rule
In a stream of $T = 30$ windows ($B_0, B_1, \dots, B_{29}$):
1. **Windows $t = 0 \dots 28$ ($29$ windows):**
   - Ingest audio, generate prediction, adapt candidate $\theta'_t$, make gate decision, update or retain state.
2. **Terminal Window $t = 29$ ($1$ window):**
   - Transcribe audio with live parameters $\theta_{29}$.
   - Score prediction offline.
   - **NO ADAPTATION UPDATE IS INITIATED.** Generating a candidate $\theta'_{29}$ after processing the final window of the stream is mathematically undefined for prospective evaluation because no window $B_{30}$ exists to evaluate its downstream consequence.

### 5.2 Exact Candidate Count Reconciliation
Under this rule, candidate evaluation accounting per stream is exact:
$$N_{\text{candidates\_per\_stream}} = T - 1 = 30 - 1 = \mathbf{29\text{ candidate evaluations}}$$
For an experiment with $M$ models, $C$ acoustic conditions, and $O$ presentation orders:
$$N_{\text{total\_candidates}} = M \times C \times O \times 29$$
- **Status:** `VERIFIED FROM ARTIFACT` (Reconciled in `stage5m_run_window_accounting.csv`: $101 \text{ runs} \times 29 = 2,929$ nominal, plus smoke tests = $2,640$ active evaluations).

---

## 6. Audit Trail & Claim Status

| Claim / Component | Description | Status | Verification Reference |
| :--- | :--- | :---: | :--- |
| **Separation of 4 Estimands** | Same-window, 1-step prospective, multi-step rollout, and policy | `PROPOSED` | Section 1 taxonomy |
| **Policy A Rollout** | Frozen-weights multi-window evaluation | `PROPOSED` | Section 2.2 |
| **Policy B Rollout** | Active-branch counterfactual replay | `PROPOSED` | Section 2.2 |
| **Prequential Invariant** | Prediction precedes adaptation; references firewalled | `VERIFIED FROM ARTIFACT` | `tests/research_validity/test_stage5m_online_control.py` |
| **Terminal Window Rule** | Final window prediction-only; exactly $T-1$ candidate updates | `VERIFIED FROM ARTIFACT` | `stage5m_run_window_accounting.csv` |
| **Multi-step Claims from 1-step** | Conflation of single-step with cumulative stability | `REFUTED & PROHIBITED` | Section 2.2 |
