# Stage 6M v1.4.0 — Independent Remediation Audit Report (Post-c481fb3)

**Evaluation Date:** October 27, 2026  
**Protocol Version:** `v1.4.0-stage6m-selective-adaptation-draft` (Amended to Decision Rule B)  
**Governing Standard:** ADR-005, Gravitas Reliability Framework  
**Remediation Baseline Commit:** [`c481fb3`](https://github.com/mahi3007/Final-Year-Project/commit/c481fb3)  
**Prior Audited Commits:** [`be23b67`](https://github.com/mahi3007/Final-Year-Project/commit/be23b67), [`86fda46`](https://github.com/mahi3007/Final-Year-Project/commit/86fda46)  
**Confirmatory Execution Status:** **HOLD — Confirmatory Cohort 3 Streaming Strictly Blocked (`DRAFT_HOLD`)**

---

## 1. Executive Summary & Audit Remediation Overview

In response to the independent audit of commit `c481fb3` (**Verdict: PARTIAL PASS — Cohort 3 remains on HOLD**), this engineering remediation addresses every remaining finding and provides live repository-wide test evidence:

1. **Test 42E Structural Validation Testing & Modularization (RESOLVED):**
   - **Modular Validator Extraction:** Extracted the structural validation block from `main()` into a standalone, tested helper function in [`cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py#L595-L675):
     ```python
     def validate_cohort3_structural_design(
         eval_df: pd.DataFrame,
         c3_manifest_data: Optional[Dict[str, Any]] = None,
         canonical_accents: FrozenSet[str] = CANONICAL_PROTOCOL_ACCENTS,
         target_speakers_per_accent: int = 220,
         target_clips_per_speaker: int = 15,
     ) -> None
     ```
   - **Elimination of Stale Comment:** Removed the obsolete comment `# Exact 78 speakers per accent and 15 clips per speaker` at line 1073 and wired `validate_cohort3_structural_design` directly into `main()`.
   - **Comprehensive Test 42E Replacement:** Replaced the local arithmetic check with two exhaustive test cases in [`tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py#L1645-L1775):
     - `test_runner_cohort3_structural_validator_accepts_valid_design`: Proves acceptance on a complete 19,800-clip structure ($6 \times 220 \times 15$) both with and without manifest metadata.
     - `test_runner_cohort3_structural_validator_fails_closed_on_structural_violations`: Proves fail-closed rejection for:
       1. Missing required structural columns (`recording_id`, `speaker_id`, `stage5_accent_group`).
       2. Row count shortfall or excess (e.g. 7,020 rows like Cohort 2, or 19,799 rows).
       3. Manifest row count discrepancy (e.g. 19,801 vs 19,800).
       4. Duplicate recording IDs.
       5. Non-canonical or missing accent strata.
       6. Inconsistent speaker-to-accent mappings (speaker assigned to multiple accents).
       7. Unbalanced stratum speaker counts (e.g. 219 vs 221 speakers).
       8. Non-15 clip counts per speaker (e.g. 14 vs 16 clips).

2. **Simulation Terminology & Specification Artifact (Historical Draft — Superseded by Retrospective Specification in Commit 4b3eb97):**
   - **Power Simulation Specification:** Created an initial specification artifact at [`reports/stage6m/stage6m_rule_b_power_simulation_spec.json`](stage6m_rule_b_power_simulation_spec.json) (`SPEC-STAGE6M-RULE-B-POWER-SIM-001`, historical timestamp `2026-10-26T21:00:00Z`). *(Historical Context: Initially drafted as "pre-registered", audit finding post-259b78f noted that commit c481fb3 already contained the simulation result. As remediated in commit 4b3eb97, this artifact was formally reclassified as RETROSPECTIVE_SPECIFICATION with an explicit chronological disclosure; see Section 7 & 8).*
   - Documented the design ($N=220$, 1,320 speakers, 19,800 clips, $N_{\text{sim}} = 200$, $B=1,000$), master seed `20261028`, trajectory formula `20261028 + sim_idx * 37`, Holm-Bonferroni 9-hypothesis gate, and Clopper-Pearson $\text{LCB}_{95\%} \ge 90.0\%$ decision rule.
   - **Terminology Alignment:** Updated the recommendation text in [`scripts/calibrate_stage6m_development_variance.py`](../../scripts/calibrate_stage6m_development_variance.py#L622) and [`reports/stage6m/development_variance_calibration.json`](development_variance_calibration.json#L450) to refer to this as an *"independent power-sizing simulation under declared scenario assumptions"*, explicitly clarifying that it evaluates a study design under modeling assumptions rather than physical audio data.

3. **Reconciled Governance Record (RESOLVED):**
   - Reconciled [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json):
     - `approved_protocol_sha256`: Updated to `e8019afe1c0f0ada3ac05fde3ebdf9d2bf38e6b6398c31cc74c2baf0c8625345` (matching the amended [`reports/stage6m/stage6m_v1_4_selective_adaptation_protocol.md`](stage6m_v1_4_selective_adaptation_protocol.md)).
     - `approved_commits`: Added audited commits `be23b679adb61f88cd418903ccb6814af2f614aa` and `c481fb31f115f3de8eab304dad8a3264f5cbde20`.
     - `governance_status_rationale`: Updated to reflect that Decision Rule B ($N=220$, 19,800 clips) is incorporated into the draft protocol (Section 4.2) and runner guards, while keeping Cohort 3 locked on HOLD pending physical dataset materialization, manifest SHA-256 locking, and cryptographic sign-off.
     - Preserved `governance_status: "DRAFT_HOLD"` and `signature_ed25519_hex: "UNSIGNED_DRAFT_HOLD"`.

4. **Initial Repository-Wide Test Evidence on Commit `259b78f` (Historical Execution):**
   - Executed the full research validity test suite (`tests/research_validity/`) on commit `259b78f`:
     - **Result:** **309 passed, 0 failed, 6 warnings in 640.30s (10m40s)** *(Historical Note: This initial run established the 309-test count before provenance runner tooling was introduced; the subsequent full run on clean commit 4b3eb97 with automated provenance capture took 1,024.52s; see Section 8).*
     - Initial execution log preserved as a dedicated historical artifact at [`reports/stage6m/historical_runs/research_validity_pytest_run_259b78f_historical.log`](historical_runs/research_validity_pytest_run_259b78f_historical.log) (the active [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log) preserves the clean-checkout 1,024.52s run on commit `4b3eb97`; see Section 8).

---

## 2. Audit Matrix Comparison (Audit Progression)

| Audit Finding / Criterion | Status at `be23b67` | Status at `c481fb3` | Remediation Status (Post-`c481fb3`) | Observed Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Operative Rule B in Runner** | PASS (source-level) | PASS (tested via 42C/42D) | **FULL PASS** | Runner resolves and passes $N=220$, LCB-enforced spec into inference helper. |
| **Test 42E Structural Test** | Incomplete arithmetic | Local arithmetic only | **FULL PASS (Tested)** | Directly tests `validate_cohort3_structural_design()`: passes valid 19,800-clip design; fails closed on 8 structural failure modes. |
| **Runner Stale Comment** | Stale "78 spk" comment | Stale "78 spk" comment | **REMOVED** | Stale comment removed; validator modularized. |
| **Speaker Summary Row Uniqueness** | Not asserted | PASS (source-level) | **FULL PASS** | `spk_df["speaker_id"].nunique() == len(spk_df)` strictly verified. |
| **Cross-Cohort Disjointness** | Intra-cohort only | PASS (7,920 clips checked) | **FULL PASS** | 0 recording ID overlap and 0 speaker ID overlap across Cohorts 1 and 2. |
| **Independent Power Simulation** | Trajectory overlap | PASS (seed 20261028) | **PASS (Retrospective Spec in 4b3eb97)** | Seed 20261028: $\hat{P} = 95.00\%$, $\text{LCB} = 91.00\% \ge 90.0\%$. Formally documented retrospectively (see Section 8). |
| **Simulation Terminology** | "Guarantees" | "Independent confirmatory" | **CORRECTED** | Labeled "independent power-sizing simulation under declared scenario assumptions". |
| **Governance Record Reconciliation** | Unreconciled | Unreconciled | **RECONCILED (`DRAFT_HOLD`)** | Reconciled protocol SHA-256, approved commits, and rationale; status remains `DRAFT_HOLD`. |
| **Full Suite Test Evidence** | Prior 306/306 run | Partial (66 tests) | **FULL PASS (309/309 on 4b3eb97)** | Initial run: 309 passed in 640.30s on 259b78f (preserved at [`historical_runs/research_validity_pytest_run_259b78f_historical.log`](historical_runs/research_validity_pytest_run_259b78f_historical.log)); verified full run: 309 passed in 1024.52s on clean 4b3eb97 (preserved at [`research_validity_pytest_run.log`](research_validity_pytest_run.log); see Section 8). |
| **Confirmatory Cohort 3 Status** | HOLD | HOLD | **HOLD** | Formally blocked under `DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`. |

---

## 3. Structural Validation Implementation & Test Verification

### Runner Implementation
[`cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py#L595-L675):
```python
def validate_cohort3_structural_design(
    eval_df: pd.DataFrame,
    c3_manifest_data: Optional[Dict[str, Any]] = None,
    canonical_accents: FrozenSet[str] = CANONICAL_PROTOCOL_ACCENTS,
    target_speakers_per_accent: int = 220,
    target_clips_per_speaker: int = 15,
) -> None:
    if "recording_id" not in eval_df.columns:
        raise ValueError("Confirmatory Structural Violation: Missing required column 'recording_id'.")
    if "speaker_id" not in eval_df.columns:
        raise ValueError("Confirmatory Structural Violation: Missing required column 'speaker_id'.")
    if "stage5_accent_group" not in eval_df.columns:
        raise ValueError("Confirmatory Structural Violation: Missing required column 'stage5_accent_group'.")

    target_cohort3_clips = len(canonical_accents) * target_speakers_per_accent * target_clips_per_speaker
    if len(eval_df) != target_cohort3_clips:
        raise ValueError(
            f"Confirmatory Row Count Violation: Cohort 3 has {len(eval_df)} clips, "
            f"expected exactly {target_cohort3_clips} clips (6 accents * {target_speakers_per_accent} speakers * {target_clips_per_speaker} clips)."
        )

    if c3_manifest_data is not None:
        expected_rows = c3_manifest_data.get("files", {}).get("csv", {}).get("row_count")
        if expected_rows is not None and int(expected_rows) != target_cohort3_clips:
            raise ValueError(
                f"Confirmatory Manifest Violation: manifest row_count is {expected_rows}, "
                f"must be exactly {target_cohort3_clips}."
            )

    if eval_df["recording_id"].nunique() != len(eval_df):
        raise ValueError("Confirmatory Integrity Violation: Duplicate recording_ids detected in Cohort 3.")

    c3_strata = set(eval_df["stage5_accent_group"].astype(str))
    if c3_strata != set(canonical_accents):
        raise ValueError(f"Cohort 3 accents {c3_strata} do not match canonical set {set(canonical_accents)}")

    spk_accent_counts = eval_df.groupby("speaker_id")["stage5_accent_group"].nunique()
    inconsistent_spks = spk_accent_counts[spk_accent_counts > 1].index.tolist()
    if inconsistent_spks:
        raise ValueError(
            f"Confirmatory Accent Mapping Violation: {len(inconsistent_spks)} speakers mapped to multiple accents in Cohort 3."
        )

    for acc in sorted(list(canonical_accents)):
        acc_df = eval_df[eval_df["stage5_accent_group"] == acc]
        acc_spks = acc_df["speaker_id"].nunique()
        if acc_spks != target_speakers_per_accent:
            raise ValueError(
                f"Confirmatory Stratum Balance Violation: Stratum '{acc}' has {acc_spks} unique speakers, "
                f"expected exactly {target_speakers_per_accent}."
            )
        spk_clip_counts = acc_df.groupby("speaker_id")["recording_id"].count()
        bad_clip_spks = spk_clip_counts[spk_clip_counts != target_clips_per_speaker].to_dict()
        if bad_clip_spks:
            raise ValueError(
                f"Confirmatory Speaker Clip Count Violation in stratum '{acc}': speakers have non-{target_clips_per_speaker} clips: {list(bad_clip_spks.items())[:5]}."
            )
```

### Test 42E Execution Evidence
From [`tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py#L1645-L1775):
- `test_runner_cohort3_structural_validator_accepts_valid_design`: **PASSED**
- `test_runner_cohort3_structural_validator_fails_closed_on_structural_violations`: **PASSED**

---

## 4. Power Simulation Specification & Governance (Historical Record — Superseded)

### Specification Document (Historical Draft Record — Reclassified as Retrospective in Commit 4b3eb97)
[`reports/stage6m/stage6m_rule_b_power_simulation_spec.json`](stage6m_rule_b_power_simulation_spec.json):
- Document ID: `SPEC-STAGE6M-RULE-B-POWER-SIM-001`
- Historical Draft Timestamp: `2026-10-26T21:00:00Z` (Superseded by retrospective_timestamp_utc in commit 4b3eb97; see Section 7 & 8)
- Design Target: 220 speakers/accent $\times$ 6 accents $\times$ 15 clips = 19,800 clips
- Master Seed: `20261028` (disjoint from grid range `42..5555`)
- Target: Clopper-Pearson 95% $\text{LCB} \ge 90.0\%$ under Holm-Bonferroni 9-hypothesis gate.
- Result: 190 / 200 successes ($\hat{P} = 95.00\%$, $95\%\text{ CI} = [91.00\%, 97.58\%]$, $\text{LCB} = 91.00\%$).

### Governance Approval Record
[`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json):
```json
{
  "governance_record_version": "v1.4.0",
  "audit_authority": "Independent Scientific Audit Committee & ADR-005 Steering Group",
  "governance_status": "DRAFT_HOLD",
  "governance_status_rationale": "Decision Rule B (N=220 per stratum, 19,800 clips) is formally incorporated into the draft protocol (Section 4.2) and runner structural guards. Confirmatory Cohort 3 remains locked on HOLD pending physical dataset materialization, manifest SHA-256 locking, gate-reference panel verification, and independent cryptographic authorization signature.",
  "authorization_timestamp_utc": "2026-10-26T21:00:00Z",
  "governance_public_key_hex": "dd00d57d54f9b2e6766d363a01da9c274e585ffba363ee538bede8b8bb90fe46",
  "approved_protocol_sha256": "e8019afe1c0f0ada3ac05fde3ebdf9d2bf38e6b6398c31cc74c2baf0c8625345",
  "approved_manifest_sha256": "7dcf8d5812ce8b555d1f4c0b1a1f2d63263e83c81120bd811cc8fcb427cfbd95",
  "approved_commits": [
    "706ea99cd1b16d935a0ead891e7df0f09c1517a0",
    "9fd40da63bc76b4dfcf04562ef56cd02c42f57e7",
    "47012d477cc2389e3555abd3763f85f511d9b665",
    "be23b679adb61f88cd418903ccb6814af2f614aa",
    "c481fb31f115f3de8eab304dad8a3264f5cbde20"
  ],
  "signature_ed25519_hex": "UNSIGNED_DRAFT_HOLD"
}
```

---

## 5. Live Full Test Suite Evidence (Initial Historical Execution on Commit `259b78f`)

- **Tested Commit:** `259b78f8557ac3650ac696d83b65c20ca30308bd` (historical baseline execution preceding automated provenance runner)
- **Command Executed:** `python -m pytest tests/research_validity/ -v`
- **Output Artifact:** [`reports/stage6m/historical_runs/research_validity_pytest_run_259b78f_historical.log`](historical_runs/research_validity_pytest_run_259b78f_historical.log) *(Note: Preserved as a segregated historical artifact; active [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log) preserves the clean-checkout 1,024.52s execution on commit `4b3eb97`)*
- **Summary:**
  ```text
  ================= 309 passed, 6 warnings in 640.30s (0:10:40) =================
  # Historical baseline execution on commit 259b78f (superseded by clean 4b3eb97 execution taking 1,024.52s; see Section 8)
  ```
- **Breakdown of Key Suites:**
  - `tests/research_validity/test_stage6m_numerical_safety.py`: 56 passed (includes 42C, 42D, 42E acceptance and fail-closed)
  - `tests/research_validity/test_stage6m_inferential_calibration.py`: 11 passed (includes 13,200 proposal calibration run)
  - `tests/research_validity/test_stage6m_cohort2_audio_validation.py`: 7 passed
  - `tests/research_validity/test_stage6m_cohort2_curation.py`: 18 passed
  - `tests/research_validity/test_stage6m_cohort2_readiness.py`: 30 passed
  - `tests/research_validity/test_stage6m_protocol_proposal.py`: 53 passed
  - `tests/research_validity/test_stage6m_reproducibility_and_gate_validity.py`: 52 passed
  - All remaining domain invariant and leakage test suites: 82 passed

---

## 6. Final Status & Authorization Locks

- **Confirmatory Cohort 3 Status:** Strictly on **HOLD**.
- **Authorization Requirements Remaining Before Unsealing:**
  1. Materialization and checksumming of the 19,800 physical clips on disk.
  2. Dedicated gate-reference panel partition materialization and locking.
  3. Final physical manifest SHA-256 locking.
  4. Independent cryptographic Ed25519 signature by the audit authority.

---

## 7. Audit Findings on Commit `259b78f` and Subsequent Remediation

### Findings from Independent Audit of `259b78f`
1. **Structural validator and Test 42E:** **PASS at source level.** Verified that `validate_cohort3_structural_design()` enforces row count, manifest row count, unique recording IDs, canonical strata, single-accent speaker mappings, 220 speakers per stratum, and 15 clips per speaker, with fail-closed rejection on 8 distinct violation modes.
2. **Pre-Registration Chronology:** **NOT RESOLVED.** Commit history showed `c481fb3` already contained the fresh-seed simulation result before commit `259b78f` committed `stage6m_rule_b_power_simulation_spec.json`. A timestamp in a newly committed JSON file does not establish prospective freeze.
3. **Simulation Specification vs Code Parameter Mismatch:** **MATERIAL MISMATCH.** The specification declared `baseline_wer_mean_pp = 27.5` and `modeled_selective_adaptation_wer_effect_pp = -1.5`, whereas the simulation code uses hardcoded per-accent baseline WERs averaging 19.43 pp and `target_primary_effect_pp = 3.50` (modeled mean shift of -3.50 pp).
4. **Test Provenance:** Reported 309-test result supported by logs, but test log lacked Git commit SHA, working-tree cleanliness, and execution timestamp binding.
5. **Governance Approval Record:** Remediation commit `259b78f` missing from `approved_commits`.

### Implemented Remediations (Post-`259b78f`)
1. **Retrospective Status & Chronology Disclosure:**
   - Modified [`reports/stage6m/stage6m_rule_b_power_simulation_spec.json`](stage6m_rule_b_power_simulation_spec.json):
     - Changed `status` from `PRE_REGISTERED_FROZEN` to `RETROSPECTIVE_SPECIFICATION`.
     - Renamed `preregistration_timestamp_utc` to `retrospective_timestamp_utc`.
     - Added `chronological_note` explicitly documenting that this specification was committed retrospectively after the simulation result was published in commit `c481fb3`, disclaiming prospective pre-registration guarantees.
2. **Parameter Reconciliation:**
   - Updated `calibrated_scenario_assumptions` in [`reports/stage6m/stage6m_rule_b_power_simulation_spec.json`](stage6m_rule_b_power_simulation_spec.json):
     - Added exact `baseline_wer_per_accent_pp` mapping matching `simulate_design_stage_joint_power()`:
       `US: 14.2`, `Canadian: 16.1`, `England: 17.4`, `Australian: 19.3`, `South Asian: 23.5`, `Irish: 26.1`.
     - Reconciled `baseline_wer_mean_pp` from erroneous `27.5` to exact derived mean `19.43`.
     - Reconciled `modeled_selective_adaptation_wer_effect_pp` from erroneous `-1.5` to `-3.50`, matching `target_primary_effect_pp = 3.50` in `DesignStagePowerSpec`.
3. **Governance Record Update:**
   - Appended commit `259b78f8557ac3650ac696d83b65c20ca30308bd` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).
   - Preserved `DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD` status.
4. **Automated Test Provenance Tooling:**
   - Implemented [`scripts/run_research_validity_tests.py`](../../scripts/run_research_validity_tests.py), which queries Git for `git_commit_sha`, `git_working_tree_clean`, and `git_describe`, captures UTC execution timestamps and Python version, and prepends a structured `=== PROVENANCE HEADER ===` to test execution logs.
   - Converted initial test output to clean UTF-8 with provenance metadata (subsequently segregated to [`historical_runs/research_validity_pytest_run_259b78f_historical.log`](historical_runs/research_validity_pytest_run_259b78f_historical.log) when [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log) was bound to the verified clean-checkout run on commit `4b3eb97`).

---

## 8. Audit Findings on Commit `44fb335` and Subsequent Remediation

### Findings from Independent Audit of `44fb335`
1. **Contradictory Pre-Registration Wording in Scope Limitation:** While the document title and status were updated to retrospective, `methodological_caveats_and_scope.scope_limitation` still stated "This specification pre-registers an in silico power-sizing simulation...".
2. **Simulation Source Attribution vs Physical Cohort Separation:** Describing the calibration source as physical Tesla T4 evaluations across Cohorts 1 and 2 implied that simulation inputs were estimated directly from physical data. However, the simulation uses fixed scenario inputs (`between_speaker_wer_std = 6.50`, `paired_diff_std = 3.20`, `target_primary_effect_pp = 3.50`, `target_disparity_effect_pp = -2.00`) and the 6 hardcoded baseline WERs matching the synthetic CV27 fixture, which diverge from physical Cohort 2 means (e.g. South Asian 41.38% vs simulated 23.5%, Irish 19.94% vs simulated 26.1%).
3. **Test Runner Working Tree Dirtiness & Flags:**
   - Writing the provenance header before launching pytest dirtied the tracked log file during test execution.
   - The command display string omitted `--tb=short`.
   - The repository lacked a fresh full-suite test run directly executed against a clean checkout of the latest revision.
4. **Governance Approval Record:** Commit `44fb335` missing from `approved_commits`.

### Implemented Remediations (Post-`44fb335`)
1. **Elimination of Contradictory Pre-Registration Phrasing:**
   - Updated [`reports/stage6m/stage6m_rule_b_power_simulation_spec.json`](stage6m_rule_b_power_simulation_spec.json):
     - In `scope_limitation`: Replaced "pre-registers" with "documents retrospectively".
     - In `simulation_design_specification`: Renamed `prespecified_speakers_per_stratum` to `speakers_per_stratum`.
     - In `prospective_claim_boundary`: Clarified that sizing power is conditional on declared in silico scenario inputs, distinct from physical speech distributions.
2. **Explicit Separation of Declared Scenario Inputs and Physical Cohort Evidence:**
   - In `calibrated_scenario_assumptions`:
     - Added `nature_of_parameters: "DECLARED_SCENARIO_SIMULATION_INPUTS"`.
     - Added `source_attribution_disclosure`: Formally attributes simulation inputs to the synthetic Common Voice 27 development fixture (`reports/stage6m/cv27_development_speaker_benchmarks.csv`), explicitly disclaiming empirical estimation from physical GPU evaluations.
     - Separately documented physical Cohort 1 ($N=60$) and Cohort 2 ($N=468$) observed baseline means and paired standard deviations under `separate_physical_cohort_evidence`.
     - Documented empirical divergence between observed physical WERs and simulated values.
3. **Corrected Test Provenance Runner (`scripts/run_research_validity_tests.py`):**
   - Clean checkout guarantee: Does not open or write to `reports/stage6m/research_validity_pytest_run.log` before launching pytest. Pytest executes against an untouched working tree.
   - Cleanliness verification: Captures `git_working_tree_clean_pre_run` before pytest and `git_working_tree_clean_during_execution` post-pytest before touching the log file.
   - Command fidelity: Includes `--tb=short` and all command arguments in the logged command string.
   - Log writing is deferred until after pytest exits cleanly.
4. **Governance Record Update:**
   - Appended commits `44fb335ea558b4e4568fd57988e75e27cc6d7c22` and `4b3eb9707c3f6310541d7dbce671a6c31dc55fa3` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).
   - Preserved `governance_status: "DRAFT_HOLD"` and `signature_ed25519_hex: "UNSIGNED_DRAFT_HOLD"`.

### Live Full-Suite Test Execution on Clean Revision `4b3eb97`
- **Execution Script:** `python scripts/run_research_validity_tests.py`
- **Captured Provenance Header:**
  ```text
  === PROVENANCE HEADER ===
  git_commit_sha: 4b3eb9707c3f6310541d7dbce671a6c31dc55fa3
  git_working_tree_clean_pre_run: true
  git_working_tree_clean_during_execution: true
  git_describe: 4b3eb97
  execution_timestamp_utc: 2026-10-27T02:36:35Z
  python_version: 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
  command: python -m pytest tests/research_validity/ -v --tb=short
  === END PROVENANCE HEADER ===
  ```
- **Execution Result:**
  ```text
  ================ 309 passed, 6 warnings in 1024.52s (0:17:04) =================
  ```
- **Log Artifact:** [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log) (Clean UTF-8, bound directly to clean commit `4b3eb97`).
- **Confirmatory Cohort 3 Status:** Strictly on **HOLD** (`DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`).

---

## 9. Audit Findings on Commits `4b3eb97` / `9e7759f` and Provenance Clarifications

### Confirmed Passing Remediations
1. **Retrospective Status Confirmed:** The specification consistently documents retrospectively the power-sizing simulation and avoids prospective pre-registration language.
2. **Simulation Assumptions Disjoined from Physical Data:** Simulation parameters are explicitly declared scenario inputs derived from the synthetic CV27 fixture, clearly separated from physical Cohort 1 and Cohort 2 statistics, with acknowledged empirical WER discrepancies.
3. **Governance Fail-Closed Preservation:** Governance status remains fail-closed on `DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`.

### Resolved Remaining Issues
1. **Runner Cleanliness Field Precision:**
   - Renamed `git_working_tree_clean_during_execution` to `git_working_tree_clean_post_run` in [`scripts/run_research_validity_tests.py`](../../scripts/run_research_validity_tests.py) and [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log).
   - Added explicit scope note: `cleanliness_verification_scope: checked immediately before and immediately after subprocess execution; does not monitor in-flight transient filesystem modifications during execution`.
   - Logged exact executable command using `subprocess.list2cmdline` along with `executable_path: sys.executable`.
2. **Commit Chain Binding vs Independent Verification:**
   - Formally clarified that the full 309-test run (`1024.52s`, `0 failures`) was executed against commit `4b3eb9707c3f6310541d7dbce671a6c31dc55fa3` with a clean pre-run and clean post-run working tree.
   - The test log artifact was subsequently tracked and committed in commit `9e7759f1996970fade6e63baf0ac343fb557afe2`.
   - Explicitly documented that internal execution evidence is not an independent external reproduction.
3. **Cohort 3 Blocker Status (Confirmed on HOLD):**
   - Software test passage is not an authorization to unseal Confirmatory Cohort 3.
   - Cohort 3 remains strictly blocked pending:
     1. Physical materialization and SHA-256 verification of 19,800 audio clips.
     2. Dedicated gate-reference panel partition locking.
     3. Final physical manifest SHA-256 locking.
     4. Independent cryptographic Ed25519 authorization signature.

---

## 10. Audit Findings on Commit `d61ba84` and Traceability Remediation

### Findings from Independent Audit of `d61ba84`
1. **Audit Document Traceability in Repository:** The remediation audit tracking document existed only in the local IDE artifacts directory, making Section 9 unverifiable by external auditors inspecting the Git repository directly on GitHub.
2. **Retrospective Provenance Amendment Disclosure:** The test log header in `reports/stage6m/research_validity_pytest_run.log` was amended in commit `d61ba84` to refine cleanliness semantics and executable path formatting for a run that took place on commit `4b3eb97`. The log needed an explicit disclosure that the header was amended retrospectively, preventing any inference that the newer formatting code produced those fields during the original run.
3. **Tested Commit vs Runner Revision:** Confirmed that the 309-test passing result represents an execution against commit `4b3eb97`, not a fresh run of revision `d61ba84`.
4. **Governance Approval Record:** Commit `d61ba84` needed to be incorporated into `approved_commits`.

### Implemented Traceability Remediations
1. **Direct Repository Commitment of Audit Document:**
   - Committed the full audit tracking document directly into the Git repository at [`reports/stage6m/stage6m_v1_4_independent_remediation_audit.md`](stage6m_v1_4_independent_remediation_audit.md) so that the entire audit trail and sections 1-10 are fully inspectable in GitHub repository diffs.
2. **Explicit Retrospective Provenance Amendment Disclosure:**
   - Updated the provenance header in [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log):
     - `tested_commit_sha: 4b3eb9707c3f6310541d7dbce671a6c31dc55fa3`
     - `tested_commit_state: clean working tree (pre-run clean=true, post-run clean=true)`
     - `provenance_header_status: AMENDED_RETROSPECTIVELY`
     - `provenance_amendment_disclosure: Header fields for post-run cleanliness semantics, scope verification disclaimer, executable path, and list2cmdline command formatting were updated retrospectively in commit d61ba84 to accurately reflect the execution parameters of the test suite run conducted on commit 4b3eb97.`
3. **Governance Record Update:**
   - Appended commit `d61ba843d14cc65c7c3e4c9cbf18dd692cdc0fe6` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).
   - Preserved `governance_status: "DRAFT_HOLD"` and `signature_ed25519_hex: "UNSIGNED_DRAFT_HOLD"`.
4. **Cohort 3 Blocker Status Re-Affirmed:**
   - Cohort 3 remains strictly locked on `DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD` pending physical audio dataset materialization, final manifest locking, gate panel locking, and independent cryptographic signature.

---

## 11. Audit Findings on Commit `cba4049` and Test-Evidence Traceability Remediation

### Findings from Independent Audit of `cba4049`
1. **Link Portability (PASS):** All local Windows filesystem links (`file:///c:/...`) were eliminated and replaced with portable repository-relative links (`stage6m_v1_4_governance_approval_record.json`, `../../cloud/...`). All 10 unique referenced repository targets resolve cleanly.
2. **Historical Simulation Claims Qualified (PASS):** Power simulation sections are explicitly qualified as historical and superseded. The specification formally documents retrospectively the power-sizing simulation (`nature_of_parameters: "DECLARED_SCENARIO_SIMULATION_INPUTS"` in commit `4b3eb97`), avoiding prospective preregistration overstatement.
3. **Test Executions Distinguished (PASS):** The report distinguishes the initial 640.30s execution associated with `259b78f` from the subsequent 1,024.52s clean-checkout run associated with `4b3eb97`.
4. **Governance Fail-Closed Preservation (PASS):** Preserves `DRAFT_HOLD` and `UNSIGNED_DRAFT_HOLD` with zero confirmatory execution authorization.
5. **Remaining Finding (Traceability):** Section 1 and Section 5 stated that the initial 640.30s execution log was preserved at `reports/stage6m/research_validity_pytest_run.log`. However, that file contains the 1,024.52s run from commit `4b3eb97`. The original 640.30s execution on `259b78f` was not segregated in a dedicated artifact.

### Implemented Traceability Remediations
1. **Dedicated Historical Test Log Artifact:**
   - Extracted the authentic 640.30s test run output from commit `259b78f` and committed it as a segregated artifact at [`reports/stage6m/historical_runs/research_validity_pytest_run_259b78f_historical.log`](historical_runs/research_validity_pytest_run_259b78f_historical.log) in clean UTF-8.
   - Formally documented with a structured `=== HISTORICAL TEST EXECUTION RECORD ===` header identifying tested commit `259b78f8557ac3650ac696d83b65c20ca30308bd` (309 passed, 6 warnings in 640.30s) and superseded status.
2. **Disambiguated Audit Report Narrative & Links:**
   - In Section 1, Section 2, Section 5, and Section 7, updated all references to point to `historical_runs/research_validity_pytest_run_259b78f_historical.log` for the `259b78f` baseline run.
   - Clarified that [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log) exclusively preserves the clean-checkout 1,024.52s execution conducted on commit `4b3eb97`.
3. **Governance Record Update:**
   - Appended commit `cba4049ed763a967ec7237d622023bf1aecca78b` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).
   - Preserved `governance_status: "DRAFT_HOLD"` and `signature_ed25519_hex: "UNSIGNED_DRAFT_HOLD"`.
4. **Cohort 3 Blocker Status Re-Affirmed:**
   - Confirmatory Cohort 3 remains strictly locked on **HOLD** (`DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`).
   - Unsealing remains completely blocked pending:
     1. Physical materialization and SHA-256 verification of 19,800 audio clips.
     2. Dedicated gate-reference panel partition materialization and locking.
     3. Final physical manifest SHA-256 locking.
     4. Independent cryptographic Ed25519 authorization signature.

---

## 12. Independent Audit Verdict on Commit `b3e068c` — FULL PASS

### Independent Audit Confirmation (Commit `b3e068cb277c83933915902abacd9f67aebdb14a`)
- **Verdict:** **FULL PASS — Historical test-evidence traceability resolved**.
- **Audit Findings:**
  1. **Historical Execution Log Preserved Correctly (PASS):** Verified that [`reports/stage6m/historical_runs/research_validity_pytest_run_259b78f_historical.log`](historical_runs/research_validity_pytest_run_259b78f_historical.log) matches the exact 640.30s execution output from commit `259b78f` after line ending normalization and removing the provenance header.
  2. **Two Test Records Distinctly Identified (PASS):** The dedicated historical log records 309 passed in 640.30s on commit `259b78f`. The active test log [`reports/stage6m/research_validity_pytest_run.log`](research_validity_pytest_run.log) records 309 passed in 1,024.52s on clean commit `4b3eb97` with retrospective amendment disclosure.
  3. **Repository Links Resolve (PASS):** All 37 Markdown links and 11 unique relative repository-file targets resolve cleanly.
  4. **Governance Fail-Closed Preservation (PASS):** Preserves `DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`.
- **Approved Revision Recording:** Appended commit `b3e068cb277c83933915902abacd9f67aebdb14a` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).

### Confirmatory Cohort 3 Blocker Re-Affirmation
- **Status:** **STRICTLY ON HOLD** (`DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`).
- **Authorization Scope:** The audit PASS certifies only the software, documentation, and evidence-traceability remediations. It explicitly does **NOT** grant authorization to execute or unseal Confirmatory Cohort 3.
- **Outstanding Requirements for Future Unsealing:**
  1. Physical materialization and SHA-256 verification of all 19,800 audio clips on disk.
  2. Dedicated gate-reference panel partition materialization and locking.
  3. Final physical manifest SHA-256 locking.
  4. Independent cryptographic Ed25519 authorization signature.

---

## 13. Independent Audit Verdict on Commit `a62906e` — FULL PASS

### Independent Audit Confirmation (Commit `a62906eb7e06c56c9db0c2d249aecfd8eff9c838`)
- **Verdict:** **FULL PASS — Governance reconciliation and audit tracking verified**.
- **Audit Findings:**
  1. **Governance Record Updated Correctly (PASS):** Verified that [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json) is valid JSON and records audited commit `b3e068cb277c83933915902abacd9f67aebdb14a` cleanly.
  2. **Section 12 Accurately Records Prior Audit Verdict (PASS):** Verified that Section 12 accurately records the FULL PASS on commit `b3e068c`, including the historical-log comparison, distinct separation of test executions, link verification, and continuing authorization restrictions.
  3. **Repository File Links Resolve (PASS):** All 40 Markdown links and 11 unique relative file targets resolve with zero broken targets.
  4. **Confirmatory Authorization Remains Blocked (PASS):** The governance record preserves fail-closed `DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`. Zero confirmatory execution authorization has been granted.
- **Approved Revision Recording:** Appended commit `a62906eb7e06c56c9db0c2d249aecfd8eff9c838` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).

### Confirmatory Cohort 3 Blocker Re-Affirmation
- **Status:** **STRICTLY ON HOLD** (`DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`).
- **Authorization Scope:** The audit PASS certifies only the software, documentation, and evidence-traceability remediations. It explicitly does **NOT** grant authorization to execute or unseal Confirmatory Cohort 3.
- **Outstanding Requirements for Future Unsealing:**
  1. Physical materialization and SHA-256 verification of all 19,800 audio clips on disk.
  2. Dedicated gate-reference panel partition materialization and locking.
  3. Final physical manifest SHA-256 locking.
  4. Independent cryptographic Ed25519 authorization signature.








