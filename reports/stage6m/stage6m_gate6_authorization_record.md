# Stage 6M: Formal Project Lead Authorization Record — Gate 6

**Decision Identifier:** `STAGE6M-GATE6-AUTH-DECISION-20261108`  
**Decision Date:** `2026-11-08`  
**Authority:** Project Lead (Dissertation Author)  
**Decision Status:** **`APPROVED — GATE 6 OFFLINE MULTIPLICITY SCORING ONLY`**  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `c423830`  
**Execution Platform:** Local Isolated Offline Environment (Zero Network / Zero Kaggle Exposure)  

---

## 1. Formal Authorization Context & Preceding Milestones

In accordance with Protocol Section 14.7, Gate 6 offline statistical multiplicity scoring is formally authorized following the verified completion of Gate 5 and the repository containment remediation:

| Milestone / Gate | Protocol Reference | Audit / Execution Status | Disposition |
| :--- | :---: | :---: | :---: |
| **Gate 1 — Scientific Admission** | Protocol Sec 14.1 | Approved | 5-stratum parity candidate admitted |
| **Gate 2 — Materializer Validation** | Protocol Sec 14.2 | Approved | Fail-closed streaming pipeline validated |
| **Gate 3A — Audio Materialization** | Protocol Sec 14.3 | Completed | 18,975 recordings materialized & verified |
| **Gate 3B — Final Manifest Lock** | Protocol Sec 14.4 | Completed | 18,000 permitted clips locked (`171815...`) |
| **Gate 4 — Kaggle GPU Readiness** | Protocol Sec 14.5 | Passed | Dual NVIDIA Tesla T4 acceleration validated |
| **Gate 5 — Confirmatory Benchmark** | Protocol Sec 14.6 | Completed | 4,125 / 4,125 windows ($K=4$, 16,500 clips) exit 0 |
| **Gate 5 — Closeout & Remediation** | Protocol Sec 14.6 | Passed | Repo private; sealed key excised from history |
| **Gate 6 — Offline Multiplicity Scoring** | Protocol Sec 14.7 | **APPROVED** | Authorized under this decision |

---

## 2. Authorized Activities & Scope Boundary

1. **Sealed Key Unsealing (Offline Exclusively):**  
   Offline access to [`datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json) (`SHA-256: f427ae7f...`) strictly inside local process memory.
2. **Alignment & Blinding Integrity Verification:**  
   Confirm exact 1:1 mapping across all 16,500 evaluation clips (1,100 speakers $\times$ 15 clips) between predictions, locked manifest, and reference transcripts.
3. **Three-Arm Levenshtein Scoring:**  
   Score Arm 1 (Static Baseline), Arm 2 (Ungated SUTA), and Arm 3 (DSG-gated SUTA) using canonical text normalization (`TextNormalizer.normalize`) and exact Levenshtein dynamic programming alignment.
4. **Registered Confirmatory Multiplicity Architecture ($M=8$):**  
   - Simultaneous single-step Bonferroni: $\alpha_{\text{family}} = 0.05$, $\alpha_{\text{adj}} = 0.05 / 8 = 0.00625$.
   - Simultaneous one-sided confidence percentile: $99.375\%$.
   - **Event A (Static Superiority):** Adjusted Wald linearized ratio $\text{UCB}_{99.375\%}(\Delta_{\text{static}}) < 0.00\text{ pp}$.
   - **Event B (Ungated Superiority):** Adjusted Wald linearized ratio $\text{UCB}_{99.375\%}(\Delta_{\text{ungated}}) < 0.00\text{ pp}$.
   - **Event C (Accent Safety Guards):** Adjusted Wald linearized ratio $\text{UCB}_{99.375\%}(\Delta_g) \le +2.00\text{ pp}$ across all 5 confirmatory strata.
   - **Event D (Disparity Non-Increase):** Stratified paired-cluster bootstrap with **$B = 20,000$ resamples** (seed = 42), requiring $\text{UCB}_{99.375\%}(\Delta D) \le 0.00\text{ pp}$.
5. **Supplementary Exploratory Analyses:**  
   Generalized Linear Mixed Models (GLMM) and trajectory analytics classified strictly as supplementary/exploratory and excluded from the formal confirmatory pass/fail gate.

---

## 3. Mandatory Invariants & Stop Conditions

- **Prediction Immutability:** [`results/stage6m_cohort3_results/prequential_stream_records.jsonl`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/results/stage6m_cohort3_results/prequential_stream_records.jsonl) (`SHA-256: 42fc02ce...`) is strictly read-only.
- **Model Invariance:** No retraining, fine-tuning, or adaptation can occur.
- **Data Isolation:** Sealed evaluation references must never be exposed outside the local scoring process. Zero upload to Kaggle, GitHub, or public endpoints.
- **Population Integrity:** Exactly 0 Australian reserve clips (975 clips) or Sentinel reference clips (1,500 clips) may enter primary evaluation scoring.

