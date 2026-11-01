# Stage 6M — Five-Stratum Candidate Sample-Size Power Sweep Report (v1.5.0-Candidate)
====================================================================================

| Parameter | Specification |
|:---|:---|
| **Document State** | `SAMPLE_SIZE_POWER_SWEEP_REPORT` (Pre-Registration Draft) |
| **Governance Standard** | ADR-005; Protocol Section 14.7 (`PROJECT_LEAD_ACADEMIC_AUTHORIZATION`) |
| **Governance Status** | `DRAFT_HOLD` (Confirmatory Audio Materialization Strictly Blocked) |
| **Branch** | `stage6m-five-stratum-parity` |
| **Target Confirmatory Accents** | K = 5 (Australian English, Canadian English, England English, South Asian English, US English) |
| **Simultaneous Multiplicity** | M = 8 One-Sided Hypotheses, Bonferroni alpha_adj = 0.00625 |
| **Simultaneous Confidence Level** | 99.375% Upper Confidence Bounds |
| **Screening Methodology** | B = 2,000 Bootstrap Replicates, Nested Subsets, Common Random Numbers |
| **Confirmation Methodology** | B = 20,000 Bootstrap Replicates, 10,000 Outer Trials, Exact Clopper-Pearson 95% CI |
| **Final Feasibility Verdict** | **PASS** |

---

## 1. Executive Summary & Verification Purpose

This audit determines whether the proposed **Five-Stratum Candidate Protocol (v1.5)** can achieve at least
**90% joint confirmatory power** with an exact 95% Monte Carlo lower confidence bound LCB_95 >= 0.90,
while remaining strictly within the verified speaker capacity envelope of Mozilla Common Voice 27.0.

### Key Findings:
1. **Limiting Capacity Envelope:** Australian English sets the structural ceiling at **N_g = 285 evaluation speakers** (1,425 total confirmatory speakers across 5 strata).
2. **Exploratory Screening Curve:** Across the evaluated range N_g in [220, 285], estimated joint power increases monotonically from **94.65%** at N_g = 220 to **98.85%** at N_g = 285.
3. **Limiting Criterion:** Primary superiority (Events A and B) and per-accent safety (Event C) achieved **100.0% power** across all tested sample sizes. The disparity safety guard (**Event D**) is the sole limiting criterion.
4. **Final Confirmation at N_g = 285 (B = 20,000, 10,000 Trials):**
   - **Estimated Joint Power:** `98.74%` (9874 / 10000 trials)
   - **Exact 95% Clopper-Pearson Confidence Interval:** `[98.50%, 98.95%]`
   - **Threshold Satisfaction:** Joint Power >= 0.90 (PASS) and LCB_95 >= 0.90 (PASS).

---

## 2. Task A: Speaker Capacity Reconciliation & Upper Bound Constraint

The confirmatory protocol requires balanced representation (N_g speakers per stratum across all 5 strata).
Based on Mozilla Common Voice 27.0 speaker eligibility records, deducting 20 reserved gate speakers yields:

| Accent Stratum | Total Eligible Speakers | Gate Reserve | Max Unexposed Eval Capacity | Status |
|:---|:---:|:---:|:---:|:---|
| **Australian English** | 305 | 20 | **285** | **LIMITING CONSTRAINT** |
| **Canadian English** | 418 | 20 | **398** | Surplus Capacity |
| **England English** | 1120 | 20 | **1100** | Surplus Capacity |
| **South Asian English** | 653 | 20 | **633** | Surplus Capacity |
| **US English** | 3791 | 20 | **3771** | Surplus Capacity |

> **Capacity Invariant:**
> The Australian English stratum admits at most N_g = 285 evaluation speakers.
> Therefore, the maximal feasible study size for balanced confirmatory inference is N_total = 1425 speakers.
> This capacity remains provisional pending formal manifest reconciliation.

---

## 3. Tasks B, C & D: Exploratory Screening Sweep (B = 2,000 Replicates)

The exploratory screening sweep evaluated N_g in {220, 230, 240, 250, 260, 270, 280, 285} across
2000 outer Monte Carlo trials per grid point, using common random numbers
and nested speaker subsets ([:N_g] prefix of the maximal 285-speaker panel).

| Speakers / Stratum (N_g) | Total Speakers | P(A) Static Sup. | P(B) SUTA Sup. | P(C) Accent Safety | P(D) Disp. Safety | **Joint Power P_joint** | Exact 95% Clopper-Pearson CI | LCB >= 90%? | Limiting Event |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **220** | 1100 | 100.0% | 100.0% | 100.0% | 94.7% | **94.65%** | [93.57%, 95.59%] | PASS | Event D |
| **230** | 1150 | 100.0% | 100.0% | 100.0% | 95.8% | **95.80%** | [94.83%, 96.64%] | PASS | Event D |
| **240** | 1200 | 100.0% | 100.0% | 100.0% | 96.7% | **96.70%** | [95.82%, 97.44%] | PASS | Event D |
| **250** | 1250 | 100.0% | 100.0% | 100.0% | 97.2% | **97.25%** | [96.44%, 97.92%] | PASS | Event D |
| **260** | 1300 | 100.0% | 100.0% | 100.0% | 98.1% | **98.10%** | [97.40%, 98.65%] | PASS | Event D |
| **270** | 1350 | 100.0% | 100.0% | 100.0% | 98.4% | **98.35%** | [97.69%, 98.86%] | PASS | Event D |
| **280** | 1400 | 100.0% | 100.0% | 100.0% | 98.5% | **98.50%** | [97.87%, 98.99%] | PASS | Event D |
| **285** | 1425 | 100.0% | 100.0% | 100.0% | 98.9% | **98.85%** | [98.28%, 99.27%] | PASS | Event D |

### Key Observations from Screening:
- **Monotonic Power Scaling:** Power scales monotonically with sample size from 94.7% at N_g = 220 to 98.9% at N_g = 285.
- **Disparity Guard Sensitivity:** Event D is the exclusive bottleneck for joint success across the entire curve.
- **Sample Sizes Meeting 90% Requirement:** All sample sizes N_g >= 220 achieve joint power >= 90.0%.
- **LCB Requirement:** Sample sizes with exact Clopper-Pearson lower bound LCB_95 >= 90.0% in screening include all N_g >= 230.

---

## 4. Task E: Final Confirmatory Power Confirmation (B = 20,000, 10,000 Trials)

To establish rigorous confirmatory power without screening approximations, the maximum-capacity candidate
design point (N_g = 285 speakers per stratum, N_total = 1425 speakers) was evaluated
at production depth (B = 20000 bootstrap replicates) across **10000 independent Monte Carlo trials**:

| Confirmation Parameter | Measured Value | Standard Required | Status |
|:---|:---:|:---:|:---:|
| **Speakers per Stratum (N_g)** | `285` | <= 285 (Australian Capacity) | **SATISFIED** |
| **Total Confirmatory Speakers** | `1425` | <= 1,425 | **SATISFIED** |
| **Outer Monte Carlo Trials** | `10000` | >= 10,000 | **SATISFIED** |
| **Bootstrap Depth (B)** | `20000` | 20,000 Replicates | **SATISFIED** |
| **Event A Power (Static Superiority)** | `100.00%` | — | High Power |
| **Event B Power (SUTA Superiority)** | `100.00%` | — | High Power |
| **Event C Power (Per-Accent Safety)** | `100.00%` | — | High Power |
| **Event D Power (Disparity Guard)** | `98.74%` | — | Limiting Event |
| **Joint Confirmatory Power P_joint** | **`98.74%`** | >= 90.0% | **PASS** |
| **Exact 95% Clopper-Pearson CI** | `[98.50%, 98.95%]` | — | — |
| **Exact 95% Lower Confidence Bound (LCB)** | **`98.50%`** | >= 90.0% | **PASS** |
| **Scientific Feasibility Verdict** | **`PASS`** | Formal Authorization Standard | **CONFIRMED** |

---

## 5. Epistemic Separation of Uncertainty Dimensions

1. **Bootstrap Monte Carlo Precision (Task 4 & 4.1):**
   - Audited at B = 20,000 with between-stream standard deviation of 0.01350 pp and zero decision flips.
2. **Outer Simulation Uncertainty (Audited in Task 5):**
   - With 10,000 outer Monte Carlo trials, the standard error of estimated power is ~0.099% (9.9 basis points).
   - The exact Clopper-Pearson interval spans `[98.50%, 98.95%]`, confirming that random simulation error cannot drop joint power below the 90.0% threshold.
3. **Scientific Uncertainty (Scenario Assumptions):**
   - **Critical Caveat:** Achieving >= 90% joint power in simulation confirms that the statistical architecture is sufficiently powered *under the calibrated data-generating scenario* (-3.5 pp superiority, -2.0 pp disparity reduction).
   - **It does not prove that the real physical DSG model will achieve these effect sizes in the wild.**

---

## 6. Recommendations & Transition to Task 6

1. **Design Point Recommendation:**
   - The candidate design point **N_g = 285 speakers per stratum** (N_total = 1,425 speakers) achieves **98.74% joint power** with an exact 95% lower bound of **98.50%**, exceeding the 90% pre-registration threshold.
2. **Governance Status:**
   - Status remains **`DRAFT_HOLD`**.
   - Manifest generation, audio download, and adaptation execution remain blocked pending formal Project-Lead review in Task 6.