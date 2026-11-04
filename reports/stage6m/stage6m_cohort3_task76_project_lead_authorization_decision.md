# Stage 6M Task 7.6 — Project-Lead Academic Authorization Decision for Full Cohort 3 Audio Acquisition

**Document Identifier:** `STAGE6M_COHORT3_TASK76_PROJECT_LEAD_AUTHORIZATION_DECISION`  
**Task Identifier:** `TASK_7_6`  
**Governing Standard:** Protocol Section 14.7 (*Project-Lead Academic Authorization*)  
**Protocol Version:** `v1.5-five-stratum-parity`  
**Execution Timestamp (UTC):** `2026-11-04T10:55:00Z`  
**Governing Status:** **DECISION_PENDING_PROJECT_LEAD_SIGN_OFF**  
**Formal Decision Disposition:** **`PENDING_FORMAL_PROJECT_LEAD_DECISION`**

---

## 1. Executive Summary & Purpose

This decision record formalizes the governance checkpoint required under **Protocol Section 14.7** before initiating physical materialization of the full 18,975-clip Stage 6M Cohort 3 evaluation partition.

In accordance with strict empirical research governance:
- Completing preliminary technical milestones (Tasks 7.4.4 through 7.5.3) establishes **technical feasibility** and **administrative readiness**, but **does NOT constitute authorization to acquire the full 18,975-clip cohort**.
- Physical acquisition of the full dataset remains strictly **`BLOCKED_PENDING_TASK_7_6_AUTHORIZATION`** until the Project Lead formally executes this decision.
- This document compiles the audited evidence base, records technical qualifications, defines the exact immutable scope of acquisition, and presents the formal decision framework for Project-Lead sign-off.

---

## 2. Approved Target Manifest Specification

Under the v1.5 Five-Stratum Parity protocol, physical acquisition is restricted to the exact provisional manifest established in Task 7.3:

- **Manifest File:** [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_provisional_manifest.json)
- **Authoritative Cryptographic SHA-256:**
  ```text
  b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547
  ```
- **Manifest Status:** `UNLOCKED (PROVISIONAL)` — formal locking is strictly deferred to Task 7.8 pending 100% physical validation of all downloaded audio recordings.
- **Evaluation Strata Allocation (Five-Stratum Parity):**

| Stratum Label | Target Speakers | Clips per Speaker | Total Target Clips | Target Audio Directory |
| :--- | :---: | :---: | :---: | :--- |
| **Australian English** | 253 | 15 | 3,795 | `datasets/external/common_voice_27/cohort3_audio` |
| **Canadian English** | 253 | 15 | 3,795 | `datasets/external/common_voice_27/cohort3_audio` |
| **England English** | 253 | 15 | 3,795 | `datasets/external/common_voice_27/cohort3_audio` |
| **South Asian English** | 253 | 15 | 3,795 | `datasets/external/common_voice_27/cohort3_audio` |
| **US English** | 253 | 15 | 3,795 | `datasets/external/common_voice_27/cohort3_audio` |
| **Total Cohort 3 Scale** | **1,265** | **15** | **18,975** | `datasets/external/common_voice_27/cohort3_audio` |

- **Substitutions Policy:** **Zero substitutions permitted.** Every one of the 18,975 recordings must match its manifest clip path, client ID, and recorded sentence text.

---

## 3. Comprehensive Evidence Audit Summary

Prior to this decision point, eight sequential verification milestones were completed and audited:

### 3.1 Source Corpus Availability (100.0% Match)
- **Source Release:** Mozilla Common Voice 27.0 English release (`cv-corpus-27.0-2026-03-08-en.tar.gz`).
- **Release Index:** `validated.tsv` (SHA-256: `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a`, $1,929,267$ rows).
- **Match Rate:** Exactly $18,975$ of $18,975$ provisional clips matched ($100.0\%$). Zero missing clips.

### 3.2 Historical Exposure Isolation ($0.00\%$ Overlap)
- **Historical Exposed Partitions Audited:**
  - `stage5_external_eval.csv` (Cohort 1 External Evaluation Panel: 60 unique speakers)
  - `stage5_sentinel_panel.csv` (Stage 5 Sentinel Panel: 30 unique speakers)
  - `stage6m_cohort2_audio.csv` (Cohort 2 Partition: 468 unique speakers)
- **Total Unique Historical Exposed Speakers:** **558 unique speakers**.
- **Pairwise Disjointness:** Historical partitions are 100% mutually disjoint.
- **Set Difference vs. Cohort 3 ($1,265$ speakers):** **Exactly 0 overlapping speakers ($0.00\%$)**. Total exposure isolation confirmed.

### 3.3 Physical Pilot Feasibility (75 / 75 Validated)
- **Execution Evidence:** Task 7.4.4 controlled physical pilot acquired 75 physical recordings across 5 speakers (1 speaker from each confirmatory stratum, 15 clips/speaker).
- **Audio Integrity:** All 75 clips verified for genuine MP3 container format, complete chunk decoding with zero late truncation, and valid MPEG Layer III frame completeness. Zero byte corruption, zero substitutions, zero SHA-256 mismatches.

### 3.4 Operational Storage Budget Reconciliation
- **Conservative 3σ Planning Envelope:** Derived from empirical pilot distribution ($N=75$, $\mu = 45,303.2$ B, $\sigma = 17,710.9$ B) as $18,975 \times (\mu + 3\sigma) = \mathbf{1.87\text{ GB}}$ ($1,781.29$ MiB).
- **Operational Headroom Budget Allocation:**
  - Raw Audio Storage Reserve: **$2.00$ GB** (reconciled to round up from $1.87$ GB)
  - Materialization Ledgers & Reports: **$0.05$ GB**
  - Streaming / Decompression Buffers: **$0.50$ GB**
  - Validation & Recovery Headroom: **$0.50$ GB**
  - **Total Operational Headroom Budget:** **$3.05$ decimal GB** ($2.84$ GiB).
- **Host Filesystem Capacity Evidence:**
  - Host Drive: `C:`
  - Recorded Timestamp (UTC): `2026-11-04T09:46:12Z`
  - Available Free Disk Space: **$23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB)**.
  - Reconciled Capacity Margin Ratio:
    $$\text{Safety Margin Ratio} = \frac{23.65\text{ decimal GB}}{3.05\text{ decimal GB}} \approx \mathbf{7.75\times\text{ headroom margin}}$$
    *(or in binary units: $\frac{22.02\text{ GiB}}{2.84\text{ GiB}} \approx 7.75\times$)*.
  - Substantial capacity confirmed on recorded historical evidence.

### 3.5 Streaming Resilience & Socket Auto-Recovery
- Materializer's HTTP Range resume mechanism and socket auto-recovery were proven under simulated and physical interruptions during Task 7.4.4.
- Maximum traversal: Up to ~95 GB compressed gzip archive stream.

### 3.6 Authorization Security Hardening
- Canonical governance path unconditionally pinned in production code:
  ```python
  HARDENING_AUDIT_JSON = REPORTS_DIR / "stage6m_cohort3_materializer_hardening_audit.json"
  ```
- Environment variable overrides completely removed.
- Adversarial integration tests ([`test_adversarial_cli_env_var_cannot_authorize_pilot`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_cohort3_audio_materialization.py#L1449) and [`test_adversarial_cli_env_var_cannot_authorize_full_cohort`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_cohort3_audio_materialization.py#L1511)) prove that forged authorized JSONs in environment variables are strictly ignored, exiting non-zero with `PermissionError` and zero destination files written.

### 3.7 Historical Inference Engine Immutability
- Frozen inference engine ([`src/dsg_ctta/evaluation/paired_cluster_inference.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/src/dsg_ctta/evaluation/paired_cluster_inference.py)) verified via Git object hash:
  ```text
  58d456fbcce43b5322d56df80e4077a32d7f4cca
  ```
- Exactly 0 diff lines vs. historical v1.4.0 baseline.

---

## 4. Operational Qualifications & Boundaries

Before executing the authorization decision, the following qualifications are formally documented:

1. **Archive Decompression Boundary:**  
   The physical pilot acquired 75 targets and terminated early without decompressing the full 95 GB archive. Full archive traversal will occur during full materialization (Task 7.7).
2. **Historical Capacity Evidence Qualification:**  
   The $23.65$ GB measurement represents historical capacity evidence captured at `2026-11-04T09:46:12Z`. Available host free disk space must be independently re-verified immediately prior to starting full download in Task 7.7.
3. **Execution Gating Boundary:**  
   Authorizing full acquisition authorizes **audio materialization only**. It does **NOT** authorize:
   - Final manifest locking (requires 100% physical validation in Task 7.8)
   - GPU CTTA adaptation (strictly blocked)
   - Threshold tuning or hyperparameter adjustment (strictly blocked)
   - Confirmatory model inference (strictly blocked)

---

## 5. Formal Project-Lead Decision Framework

### 5.1 Decision Options
Under Protocol Section 14.7, the Project Lead may select one of three formal dispositions:
1. **`AUTHORIZE_FULL_ACQUISITION`**: Formally authorize execution of Task 7.7 (physical acquisition of 18,975 clips under the provisional manifest).
2. **`EXTEND_HOLD_PENDING_FURTHER_AUDIT`**: Maintain hold and request additional audit evidence or infrastructure verification.
3. **`REJECT_FULL_ACQUISITION`**: Deny full acquisition and mandate protocol revision.

### 5.2 Current Status: PENDING
At this juncture, the decision record is initialized in the **`PENDING_FORMAL_PROJECT_LEAD_DECISION`** state:
```json
{
  "execution_gating": {
    "controlled_pilot_download": "PILOT_COMPLETE_AND_VERIFIED",
    "full_audio_materialization": "BLOCKED_PENDING_TASK_7_6_AUTHORIZATION",
    "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
    "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
    "confirmatory_inference": "STRICTLY_BLOCKED"
  }
}
```

### 5.3 Next Actions Upon Project-Lead Authorization
When the Project Lead formally issues the authorization:
1. Update `execution_gating.full_audio_materialization` to `"AUTHORIZED_BY_PROJECT_LEAD"` in [`reports/stage6m/stage6m_cohort3_materializer_hardening_audit.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_cohort3_materializer_hardening_audit.json).
2. Re-verify host free disk space on drive `C:`.
3. Launch Task 7.7 physical acquisition via [`scripts/materialize_stage6m_cohort3_audio.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/materialize_stage6m_cohort3_audio.py).
4. Monitor streaming extraction, SHA-256 ledger generation, and speaker completeness tracking.
