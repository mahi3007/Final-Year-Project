# Stage 6M v1.5 — Task 7.5.2 Governance Reconciliation & Readiness Evidence Audit

> **DOCUMENT ID:** `STAGE6M_COHORT3_TASK752_RECONCILIATION_AUDIT`  
> **TASK ID:** `TASK_7_5_2`  
> **TASK TITLE:** Governance Reconciliation & Full Materialization Readiness Evidence Audit  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol (`v1.5-five-stratum-parity`)  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **AUDIT DISPOSITION:** **RECONCILIATION COMPLETE — READINESS EVIDENCE HARDENED (TASK 7.6 PENDING)**  
> **GOVERNANCE STATUS:** **AUTHORIZED FOR DATA PREPARATION**  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:**  
> - **75-Clip Pilot:** `PILOT_COMPLETE_AND_VERIFIED`  
> - **Full 18,975-Clip Acquisition:** `BLOCKED_PENDING_TASK_7_6_AUTHORIZATION`  
> - **Final Manifest Lock:** `BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION`  
> - **GPU CTTA Adaptation:** `STRICTLY_BLOCKED`  
> - **Confirmatory Model Inference:** `STRICTLY_BLOCKED`  
> **TIMESTAMP (UTC):** `2026-11-04T09:55:00Z`  

---

## 1. Executive Summary & Audit Mandate

Following the completion of **Task 7.5.1** (Commit [`34eb1b1`](https://github.com/mahi3007/Final-Year-Project/commit/34eb1b1)), which enforced fail-closed authorization checks ahead of all physical audio acquisition paths and eliminated the `--audit-json` CLI parameter override, **Task 7.5.2** reconciles all governance records and evidence before the Project-Lead convenes the formal **Task 7.6** full-cohort acquisition decision.

This audit accomplishes four critical governance objectives under **Protocol Section 14.7**:
1. **Reconciliation of Execution Holds:** Replaces all stale `BLOCKED_PENDING_COHORT3_READINESS_REVIEW` hold statuses across the repository with `BLOCKED_PENDING_TASK_7_6_AUTHORIZATION`, reflecting the completion of Task 7.5 while strictly retaining the full-acquisition block.
2. **Comprehensive 558-Speaker Historical Exposure Audit:** Expands the historical exposure isolation audit from the preliminary 60-speaker Stage 5 external evaluation set to the complete union of **558 unique historical exposed speakers** across Cohort 1, Stage 5 Sentinel, and Cohort 2 partitions, proving **100% pairwise disjointness** and **zero overlap** with the 1,265 provisional Cohort 3 speakers.
3. **Storage Projection Qualification:** Explicitly reframes the file-size projections as **operational planning estimates** derived from an empirical sample ($N=75$ recordings across 5 speakers), explicitly disqualifying claims of formal 95% upper confidence bounds or guaranteed maximums, and records a fresh filesystem capacity measurement ($22.02$ GB free space, $7.72\times$ operational headroom ratio).
4. **Archive Termination Qualification:** Formally distinguishes automated engineering unit test verifications (which confirmed full gzip stream decompression and `decompressor.eof == True` enforcement) from the physical pilot boundary (which terminated upon acquiring 75/75 target clips up to archive member #1,188,858 without consuming the entire ~95 GB archive).
5. **Integration Test Strengthening:** Introduces three end-to-end integration tests proving that both in-process Python `main()` invocations and independent OS subprocess executions invoke the authorization gate before copying any file or contacting any network endpoint.

---

## 2. Reconciled Governance Gating Table

All execution restrictions across repository artifacts have been harmonized under Protocol Section 14.7:

| Execution Stage | Required Governance Status | Reconciled Status | Gate Enforcement Rationale |
| :--- | :---: | :---: | :--- |
| **Controlled 75-Clip Pilot** | `PILOT_COMPLETE_AND_VERIFIED` | **`PILOT_COMPLETE_AND_VERIFIED`** | All 75 clips acquired, decoded, and hash-verified across 5 strata; does not authorize new downloads |
| **Full 18,975-Clip Acquisition** | `BLOCKED_PENDING_TASK_7_6_AUTHORIZATION` | **`BLOCKED_PENDING_TASK_7_6_AUTHORIZATION`** | Technical readiness established; physical download strictly held pending formal Project-Lead decision |
| **Final Manifest Lock** | `BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION` | **`BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION`** | Manifest cannot be locked prior to 100% physical materialization and bitwise hash verification |
| **GPU CTTA Adaptation** | `STRICTLY_BLOCKED` | **`STRICTLY_BLOCKED`** | GPU adaptation strictly forbidden during data preparation phase |
| **Confirmatory Model Inference** | `STRICTLY_BLOCKED` | **`STRICTLY_BLOCKED`** | Model evaluation strictly forbidden prior to full confirmatory protocol execution authorization |
| **Readiness Review Disposition** | `READY_PENDING_PROJECT_LEAD_ACQUISITION_AUTHORIZATION` | **`READY_PENDING_PROJECT_LEAD_ACQUISITION_AUTHORIZATION`** | Technical and administrative readiness complete; awaiting Task 7.6 executive decision |

---

## 3. Comprehensive Historical Exposure Isolation Audit (558 Speakers)

To eliminate any risk of historical data leakage across prior model training, tuning, or evaluation benchmarks, the complete historical exposure inventory was retrieved, normalized, and audited against the provisional Cohort 3 manifest:

### 3.1 Historical Partition Inventory & Bitwise Provenance
Every historical partition was audited directly from its canonical CSV file in `datasets/splits/`:

```powershell
# Independent Verification Command
python -c "
import csv, hashlib
from pathlib import Path
for name in ['stage5_external_eval.csv', 'stage5_sentinel_panel.csv', 'stage6m_cohort2_audio.csv']:
    p = Path('datasets/splits') / name
    spks = set(row['speaker_id'].strip() for row in csv.DictReader(open(p, encoding='utf-8')) if row.get('speaker_id'))
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    print(f'{name}: {len(spks)} unique speakers, SHA-256={h}')
"
```

| Historical Partition | Panel Role | Unique Speakers | File Bytes | Cryptographic SHA-256 Digest |
| :--- | :--- | :---: | :---: | :--- |
| [`stage5_external_eval.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage5_external_eval.csv) | Cohort 1 External Evaluation | 60 | 451,539 | `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32` |
| [`stage5_sentinel_panel.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage5_sentinel_panel.csv) | Stage 5 Sentinel Adaptation | 30 | 92,340 | `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543` |
| [`stage6m_cohort2_audio.csv`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort2_audio.csv) | Cohort 2 Evaluation Partition | 468 | 2,591,054 | `dd837e249b15588cb15b7a3b234e820e08699722569cc24e57d119a868854f70` |

### 3.2 Pairwise Disjointness & Union Calculation
- **Pairwise Intersection Tests:**
  - $\text{Stage 5 External Eval} \cap \text{Stage 5 Sentinel} = \emptyset$ ($0$ overlapping speakers).
  - $\text{Stage 5 External Eval} \cap \text{Cohort 2} = \emptyset$ ($0$ overlapping speakers).
  - $\text{Stage 5 Sentinel} \cap \text{Cohort 2} = \emptyset$ ($0$ overlapping speakers).
- **True Union of Unique Exposed Speakers:**
  $$\left| S_{\text{C1}} \cup S_{\text{Sent}} \cup S_{\text{C2}} \right| = 60 + 30 + 468 = \mathbf{558\text{ unique speakers}}$$

### 3.3 Overlap Verification Against Cohort 3 Provisional Manifest
- **Cohort 3 Target Population:** Exactly $1,265$ unique speakers from [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json) (SHA-256: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`).
- **Overlap Result:**
  $$\left| S_{\text{Cohort 3}} \cap S_{\text{Historical Union}} \right| = \mathbf{0\text{ speakers (0.00\%)}}$$
- **Exposure Isolation Verdict:** **PASS — 100% strict isolation confirmed.** Zero historical speakers appear in Cohort 3.

---

## 4. Storage & Operational Planning Qualification

### 4.1 Planning Estimate Disclaimers
> [!IMPORTANT]
> **OPERATIONAL PLANNING ESTIMATE NOTICE:**  
> The storage projections below are derived from an empirical sample of $N=75$ physical recordings from $5$ speakers acquired during Task 7.4.4. Multiplying the sample's $P_{95}$ file size by $18,975$ does **not** establish a formal 95% upper confidence bound for total cohort size. Similarly, the mean plus three standard deviations scenario is a conservative planning envelope rather than a guaranteed maximum. They serve as engineering planning estimates to size host storage headroom.

### 4.2 Empirical Sample Distribution ($N=75$)
- **Sample File Count:** $75$ MP3 files across $5$ speakers ($15$ clips/speaker).
- **Total Physical Sample Bytes:** $3,397,743$ bytes ($3.24$ MiB / $3.40$ MB).
- **Mean Clip Size ($\mu$):** $45,303.2$ bytes ($44.24$ KiB / $45.30$ KB).
- **Median Clip Size:** $44,397.0$ bytes ($43.36$ KiB / $44.40$ KB).
- **Standard Deviation ($\sigma$):** $17,710.9$ bytes ($17.30$ KiB / $17.71$ KB).
- **Minimum Clip Size:** $14,637$ bytes ($14.29$ KiB / $14.64$ KB).
- **Maximum Clip Size:** $83,373$ bytes ($81.42$ KiB / $83.37$ KB).
- **95th Percentile ($P_{95}$):** $78,573$ bytes ($76.73$ KiB / $78.57$ KB).

### 4.3 Full-Cohort Planning Scenarios ($18,975$ Clips)
| Scenario | Calculation Basis | Projected Bytes | Projected MiB | Planning GB |
| :--- | :--- | :---: | :---: | :---: |
| **Mean Planning Estimate** | $18,975 \times \mu$ | $859,628,979$ | $819.81$ MiB | **$0.86$ GB** |
| **95th Percentile Estimate** | $18,975 \times P_{95}$ | $1,490,922,675$ | $1,421.85$ MiB | **$1.49$ GB** |
| **Conservative 3σ Planning Envelope** | $18,975 \times (\mu + 3\sigma)$ | $1,867,823,803$ | $1,781.29$ MiB | **$1.87$ GB** |

### 4.4 Fresh Filesystem Capacity Audit
- **Host Drive Audited:** `C:`
- **Audit Timestamp (UTC):** `2026-11-04T09:46:12.790237+00:00`
- **Available Free Disk Space (Historical Evidence):** **$23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB)** recorded at audit timestamp.
- **Operational Headroom Budget:** **$3.05$ decimal GB** (reconciled conservative audio $2.00$ GB + ledgers $0.05$ GB + streaming buffers $0.50$ GB + recovery headroom $0.50$ GB).
- **Safety Margin Ratio:**
  $$\frac{23.65\text{ GB}}{3.05\text{ GB}} \approx \mathbf{7.75\times\text{ headroom margin}}$$
- **Historical Evidence Qualification:** The $23,646,322,688$ bytes ($22.02$ GiB / $23.65$ decimal GB) free space represents historical capacity evidence captured at timestamp `2026-11-04T09:46:12Z`. It does not constitute an operational guarantee of free space when eventual materialization begins; host storage must be re-checked prior to physical download in Task 7.7.
- **Verdict:** **PASS — Substantial operational capacity confirmed on recorded evidence.**

### 4.5 Network Operational Parameters
- **Estimated Compressed Stream Traversal:** Up to ~95 GB (gzip-compressed Common Voice 27 release).
- **Estimated Acquisition Duration:** $3.5$ to $8.0$ hours depending on network throughput, MDC server response latency, and HTTP Range resume overhead.
- **Network Interruption Resilience:** Proven during Task 7.4.4 execution (seamless socket recovery at compressed byte offset $4,731,764,736$ B).

---

## 5. Archive Termination Qualification Boundary

To maintain complete clarity regarding archive stream verification:
1. **Engineering Decompression Unit Tests:**
   - Automated unit test `test_streaming_resume_range_validation` validated that `ThreadedResilientGzipStream` strictly enforces `self._decompressor.eof == True` before returning EOF ($0$ bytes) to callers. Truncated gzip archives ending prematurely are strictly rejected with an `IOError`.
2. **Physical Pilot Operational Boundary:**
   - The physical pilot materializer acquired and verified all $75$ target clips upon encountering target archive members up to member #1,188,858. At that point, materialization reached 100% and the reader terminated cleanly.
   - **Boundary Definition:** The physical pilot did **not** traverse the remainder of the ~95 GB archive through its final gzip EOF marker. Full-archive traversal remains documented as an operational boundary for Task 7.6 full-cohort execution.

---

## 6. Strengthened CLI Integration Test Suite

Three new integration tests were added to `tests/research_validity/test_stage6m_cohort3_audio_materialization.py`, executing the real CLI entrypoint through both in-process `main()` and independent OS subprocesses:

| Test ID | Test Name | Execution Modes Tested | Assertions Verified | Verdict |
| :---: | :--- | :--- | :--- | :---: |
| **T7.5.2-01** | `test_cli_integration_pilot_source_dir_unauthorized_rejected_before_copy` | `main()` in-process + OS `subprocess.run` | Unauthorized status raises `PermissionError` before file copy; destination directory remains strictly empty ($0$ bytes copied) | **PASS** |
| **T7.5.2-02** | `test_cli_integration_full_cohort_source_dir_unauthorized_rejected_before_copy` | `main()` in-process + OS `subprocess.run` | Unauthorized status raises `PermissionError` before file copy; destination directory remains strictly empty ($0$ bytes copied) | **PASS** |
| **T7.5.2-03** | `test_cli_integration_validate_only_succeeds_without_authorization` | `main()` in-process + OS `subprocess.run` | `--validate-only` succeeds cleanly ($0$ exit code) without authorization, produces audit reports, and copies zero audio | **PASS** |

### Test Suite Execution Output
```
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_target_manifest_scale_and_fields PASSED [  4%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_validate_audio_file_genuine_mp3_and_boundaries PASSED [  8%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_speaker_completeness_accounting_zero_audio PASSED [ 12%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_local_sourcing_and_completeness_tracking PASSED [ 16%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_streaming_resume_range_validation PASSED [ 20%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_downstream_acoustic_resampling_contract PASSED [ 25%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_materialization_reports_exist_and_consistent PASSED [ 29%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_historical_v1_4_0_execution_engine_immutability PASSED [ 33%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_speaker_and_clip_selection PASSED [ 37%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_cli_execution_and_report_isolation PASSED [ 41%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_mock_materialization_verification PASSED [ 45%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_committed_pilot_reports_exist_and_clean_zero_audio PASSED [ 50%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_materialization_authorization_fails_closed PASSED [ 54%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_stream_acquisition_requires_authorization PASSED [ 58%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_source_dir_acquisition_requires_authorization PASSED [ 62%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_full_cohort_source_dir_acquisition_requires_authorization PASSED [ 66%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pilot_complete_does_not_authorize_new_pilot_download PASSED [ 70%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_arbitrary_audit_json_path_cannot_be_injected_via_cli PASSED [ 75%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_validate_only_requires_no_authorization PASSED [ 79%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_pending_governance_statuses_all_deny_acquisition PASSED [ 83%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_full_cohort_acquisition_blocked_under_canonical_governance PASSED [ 87%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_cli_integration_pilot_source_dir_unauthorized_rejected_before_copy PASSED [ 91%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_cli_integration_full_cohort_source_dir_unauthorized_rejected_before_copy PASSED [ 95%]
tests/research_validity/test_stage6m_cohort3_audio_materialization.py::test_cli_integration_validate_only_succeeds_without_authorization PASSED [100%]

============================= 24 passed in 20.57s =============================
```

---

## 7. Cryptographic Invariants Audit

The immutable anchors of the repository were independently validated:
1. **Frozen Historical Inference Engine:**
   ```powershell
   git hash-object src/dsg_ctta/evaluation/paired_cluster_inference.py
   # Output: 58d456fbcce43b5322d56df80e4077a32d7f4cca
   ```
   Diff against baseline commit `a7a3b79`: **0 lines changed (100% byte-identical)**.
2. **Provisional Selection Manifest:**
   - Manifest path: [`datasets/splits/stage6m_cohort3_provisional_manifest.json`](file:///C:/Users/venka/Downloads/final year project main/datasets/splits/stage6m_cohort3_provisional_manifest.json)
   - Manifest SHA-256: `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`
   - Manifest row count: Exactly $18,975$ clips across $1,265$ speakers ($15$ clips/speaker).
   - Manifest lock status: **UNLOCKED (PROVISIONAL)**.

---

## 8. Milestone Conclusion & Task 7.6 Positioning

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                    TASK 7.5.2 AUDIT VERDICT: RECONCILIATION COMPLETE                 ║
║                                                                                      ║
║  1. All 558 historical exposed speakers verified with 0 overlap with Cohort 3.       ║
║  2. File-size projections qualified as operational planning estimates (N=75).       ║
║  3. Fresh host disk measurement confirms 22.02 GB free (7.72x headroom ratio).       ║
║  4. Archive termination qualified: engineering EOF verified, pilot boundary clear.  ║
║  5. CLI integration tests prove fail-closed rejection before file copy or network.   ║
║  6. Frozen inference engine (58d456f...) and manifest (b9a03e2...) 100% immutable.  ║
║                                                                                      ║
║  IMPORTANT: Full 18,975-clip acquisition remains STRICTLY BLOCKED.                   ║
║  Task 7.6 Project-Lead Authorization Decision is the next formal milestone.          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
