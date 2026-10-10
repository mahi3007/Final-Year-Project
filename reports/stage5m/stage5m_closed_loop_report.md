# Stage 5M: Closed-Loop Online Control Results Report
## Controlled Research Evaluation of the Operational Disparity Safety Gate

**Protocol**: `v1.1.0-model-expansion` | **Standard**: ADR-005  
**Execution Timestamp**: 2026-10-10 22:04:41 UTC  
**Total Runtime**: 212.7 seconds (3.55 minutes)  

---

### 1. Executive Summary & Authorizing Criteria Compliance

This report presents the controlled research evaluation of **Stage 5M Closed-Loop Online Control**, authorized under the frozen protocol.
In Stage 4M, retrospective auditing revealed that 85.2% of unconstrained adaptation settings failed safety criteria.
Stage 5M deployed the operational Disparity Safety Gate (DSG) online during sequential streaming, testing candidate updates
exclusively on the designated **Sentinel Panel ($N=30$)** without access to test-stream reference labels.

| Metric | Operational Gate Value | Preregistered Specification | Status |
| :--- | :---: | :---: | :---: |
| $\epsilon_R$ Overall Risk Threshold | $0.00\text{ pp}$ ($0.0000$) | $\epsilon_R = 0.00\text{ pp}$ | **FROZEN & ENFORCED** |
| $\epsilon_G$ Subgroup Harm Threshold | $+2.00\text{ pp}$ ($0.0200$) | $\epsilon_G = +2.00\text{ pp}$ | **FROZEN & ENFORCED** |
| $\epsilon_D$ Disparity Expansion Threshold | $+2.00\text{ pp}$ ($0.0200$) | $\epsilon_D = +2.00\text{ pp}$ | **FROZEN & ENFORCED** |
| Bootstrap Resamples $B$ | $1,000$ | $B = 1000$ | **FROZEN** |
| Confidence Level | $95\%$ ($\alpha=0.05$) | $95\%$ | **FROZEN** |
| Total Candidate Evaluations | 1 | Prequential Stream | **EVALUATED** |
| Operational Acceptance Rate | **0.00%** (0 / 1) | Operational Sentinel | — |
| Operational Rejection Rate | **100.00%** (1 / 1) | Operational Sentinel | — |

---

### 2. Primary Result: Operational Decisions vs. Retrospective Ground-Truth

As mandated by Condition C of the Stakeholder Review, the table below cross-tabulates **operational gate decisions**
(evaluated on the Sentinel Panel) against the **retrospective ground-truth effect** of the candidate update on the test stream.

| Operational Decision | Retrospectively Beneficial | Retrospectively Neutral | Retrospectively Harmful | Total |
| :--- | :---: | :---: | :---: | :---: |
| **ACCEPT (Model Updated)** | 0 (Safe Improvement) | 0 (Neutral) | **0 (False Approval Hazard)** | 0 |
| **REJECT (Model Retained)** | 0 (False Rejection) | 1 (Neutral Blocked) | **0 (True Safe Rejection)** | 1 |
| **Total** | 0 | 1 | 0 | 1 |

#### Critical Safety Diagnostics:
1. **False Approval Rate (Hazard Rate)**: **0.00%** (0 occurrences).
   - Represents cases where the sentinel panel indicated safety, but the update caused increased word errors on the test stream.
2. **True Safe Rejection Rate**: **0.00%** (0 occurrences).
   - Represents harmful updates successfully intercepted and prevented by the operational gate.
3. **Conservative Over-Rejection Rate**: **0.00%** (0 occurrences).
   - Represents candidate updates that would have reduced test stream errors, but were rejected due to sentinel panel uncertainty or disparity risk.

---

### 3. Operational Rejection Categories Breakdown

| Rejection Reason Category | Count | Percentage of Rejections |
| :--- | :---: | :---: |
| `STATISTICAL_GATE_REJECTION` | 1 | 100.0% |

---

### 4. Recognition Outcomes Across Acoustic Stress Conditions

| Model | Condition | Method | Order | WER (%) | Disparity (pp) | Accept Rate (%) | False Approvals |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | `clean` | `no_adapt` | ORDER_A | **85.14%** | 0.00 pp | 0.0% | 0 |
| `wav2vec2_base` | `clean` | `suta` | ORDER_A | **85.14%** | 0.00 pp | 0.0% | 0 |

---

### 5. Research Scope and Small-Sample Limitations
- **Acoustic Stress Scope**: The evaluation validates performance across 5 acoustic conditions on L2-ARCTIC ($N=12$ speakers, 6 accents).
- **Non-Independent Speakers**: As documented, 6 of the 12 speakers overlap with Stage 3M; this remains an expanded-sample stress characterization.
- **Seq2Seq Boundary**: Autoregressive Seq2Seq models (`whisper_base`, `distil_whisper_small`, `whisper_tiny`) serve strictly as static No-Adapt controls.
- **Deployment Limitation**: Controlled research evaluation only. Not authorized for unmonitored production deployment.