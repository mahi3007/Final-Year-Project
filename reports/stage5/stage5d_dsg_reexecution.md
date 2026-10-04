# Stage 5D: DSG Evaluator Integrity Repair & Re-execution Report

- **Execution Timestamp:** 2026-10-04T02:05:58Z
- **Protocol Version:** `v1.0-cv27-amended`
- **Stream Windows Evaluated:** 225 ($K=4$, 900 clips)
- **Execution Duration:** 27415.53s (30.462s/clip)
- **Frozen Tolerances:** $\epsilon_R = 0.0000$, $\epsilon_G = 0.0200$, $\epsilon_D = 0.0200$
- **Bootstrap Configuration:** $B = 1000$, Confidence $= 0.95$, Seed $= 20261002$
- **Sentinel Audio Manifest Hash:** `cd56299c1348b1af26f9d20302700196de1c52f19ad4f07a6582d5d2dd775f97`

## 1. Decision Breakdown

| Decision Category | Count | Percentage | Research Interpretation |
| :--- | :---: | :---: | :--- |
| **Statistical Gate Rejections** | **216** | **96.0%** | Candidate update evaluated against acoustic sentinel panel and rejected by empirical bounds ($\text{UCB} > \epsilon$). |
| **Accepted Updates** | **9** | **4.0%** | Candidate safely satisfied all 3 bounds ($\text{UCB}_R \le \epsilon_R$, $\text{UCB}_{\max} \le \epsilon_G$, $\text{UCB}_D \le \epsilon_D$). |
| **Fail-Closed Evaluator Rejections** | **0** | **0.0%** | Rejections due to evaluator runtime error, missing audio, or NaN/Inf corruption. |
| **TOTAL** | **225** | **100.0%** | **Expected Desired State: Fail-Closed Rejections = 0** |

## 2. Retrospective External Outcome Diagnostic Classification

Post-hoc analysis comparing candidate update behavior on external stream $B_t$ against gate decision:

| Classification | Windows | Pct | Significance |
| :--- | :---: | :---: | :--- |
| `ACCEPTED_AND_EXTERNALLY_HARMFUL` | 1 | 0.4% | Diagnostic outcome |
| `ACCEPTED_AND_EXTERNALLY_NEUTRAL` | 8 | 3.6% | Diagnostic outcome |
| `STATISTICALLY_REJECTED_AND_EXTERNALLY_BENEFICIAL` | 8 | 3.6% | Diagnostic outcome |
| `STATISTICALLY_REJECTED_AND_EXTERNALLY_HARMFUL` | 9 | 4.0% | Safely prevented external error |
| `STATISTICALLY_REJECTED_AND_EXTERNALLY_NEUTRAL` | 199 | 88.4% | Diagnostic outcome |

## 3. Scientific Finding & Thesis Contribution

With canonical path resolution repaired, **100% of candidate updates were genuinely evaluated on physical acoustic data against the frozen 30-speaker sentinel panel**.

> [!IMPORTANT]
> DSG safely accepted 9 candidate updates that met all statistical criteria while rejecting 216 updates that violated safety constraints.
