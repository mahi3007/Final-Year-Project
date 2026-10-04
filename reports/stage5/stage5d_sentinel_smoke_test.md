# Stage 5D Sentinel Safety Evaluator Smoke Test Report

- **Execution Timestamp:** 2026-10-03T18:17:45Z
- **Live Model Parameter Hash:** `fac0f00dbcd84cf1`
- **Candidate Parameter Hash:** `9c088c2c18050754`
- **Evaluation Duration:** 312.24s
- **Decision:** **`REJECT`**
- **Decision Reason:** `STATISTICAL_GATE_REJECTION`
- **Rejection Reasons:** `Overall risk violation: UCB95(Delta_R) = 0.0017 > epsilon_R (0.0000)`

## Empirical Metrics & Upper Confidence Bounds

| Metric | Point Estimate | 95% UCB | Threshold | Margin | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Overall Risk ($\Delta_R$)** | +0.0007 | +0.0017 | $\le 0.0000$ | -0.0017 | VIOLATION |
| **Subgroup Regression ($\max_g \Delta_g$)** | +0.0039 | +0.0078 | $\le 0.0200$ | +0.0122 | PASS |
| **Disparity Growth ($\Delta_D$)** | +0.0000 | +0.0000 | $\le 0.0200$ | +0.0200 | PASS |

## Stratum-Level Deltas

| Stratum | Observed $\Delta_g$ |
| :--- | :---: |
| Australian English | +0.0039 |
| Canadian English | +0.0000 |
| England English | +0.0000 |
| Irish English | +0.0000 |
| South Asian English | +0.0000 |
| US English | +0.0000 |

## 12 Smoke Test Verification Criteria

| Criterion | Result | Evidence / Detail |
| :--- | :---: | :--- |
| 1. Sentinel Audio Files Loaded via Resolver | **PASS** | `Resolved without FileNotFoundError` |
| 2. Stream Label Isolation Enforced | **PASS** | `No labels accessible to adaptation loop` |
| 3 & 4. Live & Candidate Predictions Generated | **PASS** | `Delta_R computed: +0.000683` |
| 5. Delta_R is Finite | **PASS** | `+0.000683` |
| 6. All 6 Group Deltas Finite | **PASS** | `Groups: ['Australian English', 'Canadian English', 'England English', 'Irish English', 'South Asian English', 'US English']` |
| 7. Delta_D is Finite | **PASS** | `+0.000000` |
| 8. 1000 Bootstrap Replicates Computed | **PASS** | `B = 1000` |
| 9. Zero Strata Omitted | **PASS** | `6/6 strata monitored` |
| 10. UCBs Finite | **PASS** | `UCB_R=+0.0017, UCB_max=+0.0078, UCB_D=+0.0000` |
| 11. Statistical Decision Produced | **PASS** | `Decision: REJECT (STATISTICAL_GATE_REJECTION)` |
| 12. Zero Evaluator Exceptions | **PASS** | `Decision Reason: STATISTICAL_GATE_REJECTION` |

## Verdict

**OVERALL VERDICT: PASSED -- Evaluator is functioning properly and ready for full 225-window execution.**
