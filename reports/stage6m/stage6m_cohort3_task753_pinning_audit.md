# Stage 6M Task 7.5.3 — Canonical Authorization Source Pinning & Storage Budget Reconciliation Audit

**Document Identifier:** `STAGE6M_COHORT3_TASK753_PINNING_AUDIT`  
**Task Identifier:** `TASK_7_5_3`  
**Governing Standard:** Protocol Section 14.7 (*Project-Lead Academic Authorization*)  
**Protocol Version:** `v1.5-five-stratum-parity`  
**Execution Timestamp (UTC):** `2026-11-04T10:45:00Z`  
**Branch Baseline:** `main` / `stage6m-five-stratum-parity` synchronized at commit `6ebb02c`  
**Audit Disposition:** **PINNING_AND_RECONCILIATION_COMPLETE_TASK76_PENDING**

---

## 1. Executive Summary

Task 7.5.3 implements two critical corrections identified during the Project-Lead review of Task 7.5.2 (`6ebb02c`):
1. **Canonical Authorization Source Pinning (Security Boundary Integrity):**
   - Eliminated the `STAGE6M_HARDENING_AUDIT_JSON` environment-variable lookup from `scripts/materialize_stage6m_cohort3_audio.py`.
   - Production materialization CLI unconditionally evaluates the canonical governance artifact (`reports/stage6m/stage6m_cohort3_materializer_hardening_audit.json`).
   - Added adversarial integration tests demonstrating that when an operator/adversary fabricates an authorized audit JSON and points `STAGE6M_HARDENING_AUDIT_JSON` to it, the production CLI strictly rejects acquisition with `PermissionError`, exits non-zero, and leaves the destination directory completely untouched.
2. **Storage Budget Arithmetic Reconciliation:**
   - Reconciled the raw audio storage allocation from $1.80$ GB to $2.00$ GB to properly encompass the $1.87$ GB conservative 3-sigma planning envelope ($18,975 \times [\mu + 3\sigma]$).
   - Updated the total operational headroom budget from $2.85$ GB to $3.05$ GB ($2.00 + 0.05 + 0.50 + 0.50 = 3.05$ GB).
   - Updated the safety margin ratio against recorded free space ($23.65$ decimal GB / $22.02$ GiB) to $\mathbf{7.75\times}$ ($\frac{23.65}{3.05} \approx 7.75$).
   - Qualified the $23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB) disk measurement as historical capacity evidence captured at `2026-11-04T09:46:12Z`, rather than a perpetual operational guarantee; host free disk space must be independently re-verified prior to physical acquisition in Task 7.7.

All core scientific and cryptographic invariants remain strictly preserved. Full audio materialization remains **`BLOCKED_PENDING_TASK_7_6_AUTHORIZATION`**.

---

## 2. Issue 1 — Authorization Source Integrity & Hardening

### 2.1 Problem Analysis
In Task 7.5.1, the CLI argument `--audit-json` was removed to prevent operators from supplying alternative audit paths. However, the production materializer retained:
```python
_AUDIT_ENV = os.environ.get("STAGE6M_HARDENING_AUDIT_JSON")
HARDENING_AUDIT_JSON = (
    Path(_AUDIT_ENV)
    if _AUDIT_ENV
    else (REPORTS_DIR / "stage6m_cohort3_materializer_hardening_audit.json")
)
```
This environment variable lookup reopened the same authorization bypass: an operator could forge a JSON file with `full_audio_materialization: "AUTHORIZED_BY_PROJECT_LEAD"`, set `$env:STAGE6M_HARDENING_AUDIT_JSON`, and bypass repository governance. Furthermore, earlier tests set this environment variable to a *blocked* file, proving that a blocked file fails, but failing to prove that an authorized file in the environment variable is ignored by production.

### 2.2 Remediation
In `scripts/materialize_stage6m_cohort3_audio.py`:
- Removed `_AUDIT_ENV = os.environ.get("STAGE6M_HARDENING_AUDIT_JSON")` entirely.
- Pinned `HARDENING_AUDIT_JSON` unconditionally to `REPORTS_DIR / "stage6m_cohort3_materializer_hardening_audit.json"`.
- Retained the `audit_json_path: Path = HARDENING_AUDIT_JSON` parameter on `verify_pilot_materialization_authorization` and `verify_full_cohort_materialization_authorization` for direct programmatic unit testing and in-process `monkeypatch` testing only.

### 2.3 Adversarial Integration Test Evidence
Two adversarial integration tests were added to `tests/research_validity/test_stage6m_cohort3_audio_materialization.py`:

| Test Identifier | Adversarial Attack Scenario | Expected Production Behavior | Observed Result |
| :--- | :--- | :--- | :---: |
| **`test_adversarial_cli_env_var_cannot_authorize_pilot`** | Adversary sets `STAGE6M_HARDENING_AUDIT_JSON` to a fake JSON claiming `controlled_pilot_download: "AUTHORIZED_BY_PROJECT_LEAD"`. | Production CLI evaluates canonical audit (`PILOT_COMPLETE_AND_VERIFIED`), raises `PermissionError`, exits with returncode $\neq 0$, destination directory empty. | **PASS** (Zero files copied) |
| **`test_adversarial_cli_env_var_cannot_authorize_full_cohort`** | Adversary sets `STAGE6M_HARDENING_AUDIT_JSON` to a fake JSON claiming `full_audio_materialization: "AUTHORIZED_BY_PROJECT_LEAD"`. | Production CLI evaluates canonical audit (`BLOCKED_PENDING_TASK_7_6_AUTHORIZATION`), raises `PermissionError`, exits with returncode $\neq 0$, destination directory empty. | **PASS** (Zero files copied) |

---

## 3. Issue 2 — Storage Budget Arithmetic Reconciliation

### 3.1 Planning Envelope vs. Allocation Reconciled
- **Empirical Pilot Sample ($N=75$ clips across 5 speakers):**
  - Mean file size $\mu = 45,303.2$ bytes ($43.20$ KiB)
  - Standard deviation $\sigma = 17,710.9$ bytes ($16.89$ KiB)
  - 95th percentile $P_{95} = 78,573$ bytes ($74.93$ KiB)
- **Cohort 3 Scale ($18,975$ clips):**
  - Mean planning estimate: $0.86$ GB ($819.81$ MiB)
  - 95th percentile planning estimate: $1.49$ GB ($1,421.85$ MiB)
  - Conservative 3σ planning envelope: **$1.87$ GB** ($1,781.29$ MiB)

### 3.2 Headroom Budget Table ($3.05$ GB)
To ensure the raw audio allocation strictly encompasses the $1.87$ GB planning envelope, the raw audio reserve was rounded up to **$2.00$ GB**:

| Operational Component | Previous Budget | Reconciled Budget | Justification |
| :--- | :---: | :---: | :--- |
| **Conservative Raw Audio Reserve** | $1.80$ GB | **$2.00$ GB** | Properly encompasses the $1.87$ GB 3σ planning envelope ($18,975 \times [\mu + 3\sigma]$) |
| **Materialization Ledgers & Reports** | $0.05$ GB | **$0.05$ GB** | $18,975$-row SHA-256 CSV, speaker reports, audit JSON/MD |
| **Streaming / Decompression Buffers** | $0.50$ GB | **$0.50$ GB** | In-memory ring buffers, tar extraction chunk buffers, stream pipes |
| **Validation & Recovery Headroom** | $0.50$ GB | **$0.50$ GB** | Temporary soundfile decodes, checksum logs, retry caches |
| **Total Operational Headroom Budget** | **$2.85$ GB** | **$3.05$ GB** | **Total host disk headroom required ($2.00 + 0.05 + 0.50 + 0.50$)** |

### 3.3 Safety Margin & Historical Evidence Qualification
- **Recorded Host Free Space (`C:`):** **$23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB)** at `2026-11-04T09:46:12Z`.
- **Reconciled Margin Ratio:**
  $$\text{Safety Margin Ratio} = \frac{23.65\text{ GB}}{3.05\text{ GB}} \approx \mathbf{7.75\times\text{ headroom margin}}$$
- **Historical Capacity Evidence Notice:**
  > The recorded $23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB) free space represents historical capacity evidence captured at timestamp `2026-11-04T09:46:12Z`. It does not constitute a guaranteed maximum or perpetual reservation; available host disk space must be independently re-verified before full physical acquisition begins in Task 7.7.

---

## 4. Preservation of Invariants

| Invariant Item | Canonical Value / Standard | Observed Value | Status |
| :--- | :--- | :--- | :---: |
| **Historical Exposed Speakers** | 558 unique speakers across Cohorts 1 & 2 | Exactly 558 unique speakers | **PASS** |
| **Cohort 3 Exposure Overlap** | Zero historical overlap permitted | 0 overlap across all 1,265 speakers | **PASS** |
| **Provisional Manifest SHA-256** | `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` | Exact match confirmed | **PASS** |
| **Frozen Inference Engine Blob** | `58d456fbcce43b5322d56df80e4077a32d7f4cca` | Exact match confirmed (0 diff lines) | **PASS** |
| **Pilot Archive Qualification** | Documented early gzip termination | Preserved in JSON and Markdown | **PASS** |
| **Full Acquisition Gating** | `BLOCKED_PENDING_TASK_7_6_AUTHORIZATION` | Fail-closed in all governance records | **PASS** |
| **Final Manifest Lock Gate** | `BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION` | Maintained | **PASS** |
| **GPU Adaptation & Inference** | `STRICTLY_BLOCKED` | Maintained | **PASS** |

---

## 5. Verification Hierarchy & Regression Evidence

The complete 5-module Stage 6M targeted regression suite was executed:
1. `tests/research_validity/test_stage6m_cohort3_audio_materialization.py` (26 tests, including 2 new adversarial tests)
2. `tests/research_validity/test_stage6m_cohort3_source_audit.py` (10 tests)
3. `tests/research_validity/test_stage6m_cohort3_curation.py` (16 tests)
4. `tests/research_validity/test_stage6m_project_lead_authorization_package.py` (7 tests)
5. `tests/research_validity/test_historical_immutability.py` (7 tests)

**Suite Result:** **66 / 66 passed (100%)**

---

## 6. Final Recommendation

With canonical authorization source pinning strictly enforced, adversarial environment bypass tests passing, and storage budget arithmetic reconciled to $3.05$ GB ($7.75\times$ headroom on historical evidence), Task 7.5.3 is complete.

**Next Milestone:** **Task 7.6 — Project-Lead Acquisition Decision** under Protocol Section 14.7.
