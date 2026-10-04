# ADR-005: Stage 5 Disparity Safety Gate (DSG) Decision Rule and Rollback Semantics

**Status:** PROPOSED FOR FORMAL PROTOCOL APPROVAL  
**Date:** 2026-09-30  
**Authors:** Lead Research Engineer & Reproducibility Suite  
**Deciders:** Lead Research Engineer, Principal Investigator  
**Applies To:** Stage 5 Controller Implementation & Online Evaluation  

---

## 1. Context and Problem Statement

In Stage 0 (`protocol_freeze.md`), the Disparity Safety Gate (DSG) was defined as a tripartite acceptance policy over Upper Confidence Bounds (UCBs):
$$\text{UCB}(\Delta_R) \le \epsilon_R \quad \land \quad \text{UCB}(\max_g \Delta_g) \le \epsilon_G \quad \land \quad \text{UCB}(\Delta_D) \le \epsilon_D$$

However, in the Stage 4.1 closure documentation, an alternative formulation was introduced:
$$\text{Reject} \iff \text{LCB}_{95}(\Delta_R) > 0 \quad \lor \quad \text{UCB}_{95}(\max_g \Delta_g) > \delta_G \quad \lor \quad \text{UCB}_{95}(\Delta_D) > \delta_D$$

Furthermore, some textual descriptions ambiguously referred to rollback as "reverting to $\theta_{t-1}$", which would erroneously discard previously accepted, beneficial updates if a candidate at time $t$ were rejected.

Before beginning Stage 5 controller implementation, this architectural decision record (ADR) formally harmonizes these definitions, establishes the conceptual separation between scientific discovery thresholds ($\delta$) and controller operating tolerances ($\epsilon$), and specifies exact, fail-closed rollback semantics.

---

## 2. Decision: Conceptual Separation of $\delta$ and $\epsilon$

To prevent methodological conflation, two distinct parameter classes are established:

### 2.1 Scientific Discovery Thresholds ($\delta$)
- **Definitions:** $\delta_G = 0.0200$ (2.00% subgroup regression), $\delta_D = 0.0200$ (2.00% disparity amplification).
- **Purpose:** Pre-registered, scientific boundary criteria used for offline phenomenon characterization to distinguish genuine algorithmic harm from measurement noise (e.g. discrete word granularity floors).
- **Invariance:** $\delta_G$ and $\delta_D$ are immutable physical constants of the evaluation protocol; they are never tuned to make a controller appear effective.

### 2.2 Controller Operating Tolerances ($\epsilon$)
- **Definitions:** $\epsilon_R$ (overall risk tolerance), $\epsilon_G$ (subgroup regression tolerance), $\epsilon_D$ (disparity growth tolerance).
- **Purpose:** Engineering control parameters of the online safety gate. They define the risk profile of the deployment (e.g. strict zero-tolerance $\epsilon=0$ vs conservative slack $\epsilon = \delta$).
- **Ablation Scope:** Stage 5 and Stage 6 evaluate Pareto trade-off curves across grids of $\epsilon \in \{0.00, 0.01, 0.02\}$.
- **Default Operating Point:** For primary intervention validation, $\epsilon_R = 0.0000$ (zero tolerance for overall degradation), $\epsilon_G = \delta_G = 0.0200$, and $\epsilon_D = \delta_D = 0.0200$.

---

## 3. Decision: Formal Gate Acceptance & Rejection Logic

Let $\theta_t$ be the current live model at prequential window $t$. Let $\theta'$ be the candidate adapted model produced by unsupervised CTTA on unlabeled batch $B_t$. Both models are evaluated on the frozen sentinel panel $\mathcal{S}_{\text{sentinel}}$.

For each metric $M \in \{\Delta_R, \max_g \Delta_g, \Delta_D\}$, paired speaker-cluster bootstrapping ($B=1,000$ resamples) computes the empirical 95th percentile Upper Confidence Bound ($UCB_{95}$):

$$\text{ACCEPT}(\theta') \iff \begin{cases} 
\text{UCB}_{95}(\Delta_R(\mathcal{S}_{\text{sentinel}})) \le \epsilon_R \\ 
\land \\ 
\text{UCB}_{95}(\max_g \Delta_g(\mathcal{S}_{\text{sentinel}})) \le \epsilon_G \\ 
\land \\ 
\text{UCB}_{95}(\Delta_D(\mathcal{S}_{\text{sentinel}})) \le \epsilon_D 
\end{cases}$$

Conversely, candidate update $\theta'$ is **REJECTED** if any single safety constraint is breached:
$$\text{REJECT}(\theta') \iff \left[ \text{UCB}_{95}(\Delta_R) > \epsilon_R \right] \lor \left[ \text{UCB}_{95}(\max_g \Delta_g) > \epsilon_G \right] \lor \left[ \text{UCB}_{95}(\Delta_D) > \epsilon_D \right]$$

### 3.1 Resolving the Overall Risk Condition ($\text{UCB}_{95}(\Delta_R) \le \epsilon_R$ vs $\text{LCB}_{95}(\Delta_R) > 0$)
- In Stage 4.1, $\text{LCB}_{95}(\Delta_R) > 0$ was suggested as an overall harm criterion. However, testing $\text{LCB} > 0$ requires 95% confidence that the model degraded before rejecting, making it dangerously permissive of negative drift.
- **Canonical Decision:** The controller must be risk-averse. Requiring $\text{UCB}_{95}(\Delta_R) \le \epsilon_R$ (with default $\epsilon_R = 0$) ensures that updates are rejected unless there is 95% confidence that degradation does **not** exceed $\epsilon_R$. This guarantees fail-safe operation.

---

## 4. Decision: Shadow Candidate Architecture & Rollback Semantics

To ensure absolute integrity of the live adaptation stream:

1. **Live Immutability:** The live model $\theta_t$ is **NEVER** modified in-place during adaptation.
2. **Shadow Cloning:** An in-memory shadow clone $\theta'$ is instantiated for candidate adaptation on $B_t$.
3. **State Transition Rule:**
   $$\theta_{t+1} = \begin{cases} 
   \theta' & \text{if } \text{GateDecision} = \text{ACCEPT} \\ 
   \theta_t & \text{if } \text{GateDecision} = \text{REJECT} 
   \end{cases}$$
4. **Correction of $\theta_{t-1}$ Phrasing:** Rejection does **NOT** roll back to $\theta_{t-1}$. Discarding the candidate simply preserves the current validated checkpoint $\theta_t$. This prevents the unintended erasure of previously validated adaptations.
5. **Bit-for-Bit Determinism:** A unit test must enforce that after a REJECT decision, the parameter hash of $\theta_{t+1}$ is byte-for-byte identical to $\theta_t$:
   $$\text{SHA256}(\theta_{t+1}) \equiv \text{SHA256}(\theta_t)$$

---

## 5. Decision: Fail-Closed Policy

The safety controller must operate under strict fail-closed guarantees. A candidate update $\theta'$ is automatically **REJECTED** and the live model $\theta_t$ retained if any of the following occur:
1. Sentinel panel audio or transcripts are missing, corrupt, or hash-mismatched.
2. Bootstrap resampling encounters numerical instability, division by zero, or rank deficiency.
3. Candidate parameter tensors contain `NaN`, `Inf`, or abnormal gradient divergence.
4. Model architecture or vocabulary mismatch between live model and sentinel evaluator.
5. Timeout during sentinel inference or gate calculation.

Under no circumstances may a software exception or edge case result in an unverified candidate $\theta'$ being accepted.

---

## 6. Consequences & Verification

- **Positive:** Protocol is mathematically unified. Scientific thresholds ($\delta$) are air-gapped from operating tolerances ($\epsilon$). Live adaptation state cannot be corrupted by failed updates.
- **Negative:** Requires maintaining two copies of adapter weights in memory during prequential steps ($\theta_t$ and $\theta'$), incurring modest RAM overhead (~15 MB for Wav2Vec2 adapter layers).
- **Verification Plan:**
  - `tests/unit/test_gate_contract.py`
  - `tests/research_validity/test_shadow_candidate_isolation.py`
  - `tests/research_validity/test_fail_closed_gate.py`
