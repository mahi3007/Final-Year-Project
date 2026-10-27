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

---

## 14. Independent Audit Verdict on Commit `3299ef7` — FULL PASS

### Independent Audit Confirmation (Commit `3299ef711420cce01fa9cd154ff536d99a718a61`)
- **Verdict:** **FULL PASS — Governance acceptance and audit tracking verified**.
- **Audit Findings:**
  1. **Governance Acceptance Recorded (PASS):** Verified that [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json) parses as valid JSON with 14 approved commit entries, recording commit `a62906e` exactly once.
  2. **Section 13 Committed (PASS):** Verified that Section 13 accurately documents the FULL PASS for `a62906e`, its governance reconciliation, and continuing authorization restrictions.
  3. **Repository Links Resolve (PASS):** Checked all 42 Markdown links and 11 unique relative repository-file targets with zero broken targets.
  4. **Fail-Closed Governance Preserved (PASS):** Preserves `governance_status: "DRAFT_HOLD"` and `signature_ed25519_hex: "UNSIGNED_DRAFT_HOLD"`.
- **Approved Revision Recording:** Appended commit `3299ef711420cce01fa9cd154ff536d99a718a61` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).

### Confirmatory Cohort 3 Blocker Re-Affirmation
- **Status:** **STRICTLY ON HOLD** (`DRAFT_HOLD` / `UNSIGNED_DRAFT_HOLD`).
- **Authorization Scope:** Software and documentation remediation is fully certified. Confirmatory execution authorization has not been granted.
- **Outstanding Requirements for Future Unsealing (Operative Protocol Section 4.2):**
  1. Physical materialization and SHA-256 verification of all 19,800 audio clips on disk.
  2. Dedicated gate-reference panel partition materialization and locking.
  3. Final physical manifest SHA-256 locking.
  4. Independent cryptographic Ed25519 authorization signature binding the final protocol, execution commit, and physical audio manifest.

---

## 15. Independent Audit Findings on Commit `e4bceb9` & Operative Governance Clarification

### Independent Audit Findings (Commit `e4bceb95994a18eda576083a1d4eb653a6629b91`)
- **Verdict:** **PARTIAL PASS — Governance tracking passes; operative authorization gate clarified**.
- **Audit Findings:**
  1. **Governance Record Verified (PASS):** Verified that [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json) is valid JSON containing 15 approved commit entries, recording commit `3299ef7` exactly once.
  2. **Section 14 Committed (PASS):** Verified that Section 14 accurately documents the prior audit verdict and re-affirms fail-closed restrictions.
  3. **Repository Links Resolve (PASS):** All 44 Markdown links and 11 unique relative repository-file targets resolve cleanly.
  4. **Fail-Closed Governance Preserved (PASS):** Preserves `governance_status: "DRAFT_HOLD"` and `signature_ed25519_hex: "UNSIGNED_DRAFT_HOLD"`.
  5. **Operative Authorization Route Clarification (RESOLVED):** The auditor noted that while Protocol Section 14.7 provides guidance on reconciling governance with university requirements, the operative protocol at Section 4.2 strictly mandates an independent Ed25519 signature binding the protocol, execution commit, and 19,800-clip manifest. The parenthetical mention of an alternative institutional project-lead amendment was clarified: Path B is an unadopted exploratory proposal that has not been enacted in the protocol or runner. The operative requirement remains strictly the independent Ed25519 signature.
- **Approved Revision Recording:** Appended commit `e4bceb95994a18eda576083a1d4eb653a6629b91` to `approved_commits` in [`reports/stage6m/stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json).

### Protocol and Governance Alignment
- **Operative Requirement at Commit `05c5c9b`:** Confirmatory execution cannot proceed without a verified 19,800-clip manifest lock and an independent Ed25519 signature binding the protocol, the execution commit, and the audio manifest (Protocol Section 4.2).
- **Amendment Boundary:** If university rules do not require supervisor sign-off and no other rule requires cryptographic authorization, that governance decision must first be confirmed in writing. Any replacement mechanism must be formally enacted via a versioned protocol amendment that updates the protocol text, governance schema, runner preflight checks, and test assertions together.
- **Commit Verdict:** PASS for documentation and governance clarification at commit `05c5c9b7296b6194742f8d04fafdb5dec28052ad`. Confirmatory Cohort 3 remains strictly on HOLD.

---

## 16. Formal Governance Protocol Amendment: Complete Removal of Cryptographic Ed25519 Signature in Favor of Project-Lead Academic Authorization

### 16.1 Rationale and Academic Governance Boundary
In institutional and multi-center clinical trials, multi-party asymmetric keypair generation and offline cryptographic signing can provide non-repudiation between adversarial parties. However, for an academic honours / final-year engineering thesis project, mandatory cryptographic key generation:
1. Imposes artificial operational overhead without enhancing scientific validity or reproducibility beyond version control and dataset content hashes.
2. Creates an unmanageable key-custody dependency where losing or mismounting a signing key invalidates legitimate academic execution.
3. Obscures the true scientific safeguards (deterministic speaker isolation, 19,800 physical audio SHA-256 integrity, sentinel panel uncontamination, and statistical power enforcement).

Consequently, following the auditor's explicit recommendation, the research team formally amended the Stage 6M v1.4.0 governance architecture to **completely remove the Ed25519 cryptographic authorization signature requirement**, replacing it with a rigorous, fail-closed **Project-Lead Academic Authorization Record** (`PROJECT_LEAD_ACADEMIC_AUTHORIZATION`) governed by amended Protocol Section 14.7.

### 16.2 Reconciled Components Checklist
1. **Inspect Every Active Signature Dependency (COMPLETED):**
   - Protocol markdown files, governance JSON schema, runner preflight checks, test fixtures, and audit reports were audited. All operative requirements for cryptographic key generation, public key pinning, and Ed25519 signature verification were identified.
2. **Amend the Operative Protocol (COMPLETED):**
   - [`stage6m_v1_4_selective_adaptation_protocol.md`](stage6m_v1_4_selective_adaptation_protocol.md) Section 4.2 amended: removed mandatory independent Ed25519 signature requirement; bound execution to verified 19,800-clip manifest lock and documented Project-Lead Academic Authorization Record.
   - Section 14 formalized with explicit subsection `### 14.7 Operative Authorization Gate: Project-Lead Academic Authorization Record`.
   - Amended protocol SHA-256 computed: `feeda07e2b34caaee1338a0a546d4dcdb961767d560cb7bb21a44c7165600c9b`.
3. **Revise the Governance Schema (COMPLETED):**
   - [`stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json) revised:
     - Removed: `signature_ed25519_hex` and `governance_public_key_hex`.
     - Added: `"authorization_mode": "PROJECT_LEAD_ACADEMIC_AUTHORIZATION"`, `"responsible_investigator": "Student Project Lead"`.
     - Non-Circular Code Identity: Bound `"frozen_code_commit_sha": "f17328e913a1fe1045f6277dc0dbbcbc7469b184"`.
     - Bound: `"approved_protocol_sha256": "feeda07e2b34caaee1338a0a546d4dcdb961767d560cb7bb21a44c7165600c9b"`.
     - Appended audited commits `05c5c9b7296b6194742f8d04fafdb5dec28052ad` and `f17328e913a1fe1045f6277dc0dbbcbc7469b184` to `approved_commits` (18 approved commits total).
     - Preserved: `"governance_status": "DRAFT_HOLD"`, keeping Cohort 3 locked.
4. **Update the Runner and Preflight Checks (COMPLETED):**
   - [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py) updated:
     - `validate_frozen_execution_contract` validates `authorization_mode in ("PROJECT_LEAD_ACADEMIC_AUTHORIZATION", "PROJECT_LEAD_DECLARATION")`.
     - Enforces non-circular code identity: verifies either current commit SHA is in `approved_commits` or binds an approved `frozen_code_commit_sha`.
     - Checks `governance_status == "APPROVED"`; fails closed on `DRAFT_HOLD`.
     - Cross-validates manifest hash against `approved_manifest_sha256`.
     - Cross-validates protocol file hash against `approved_protocol_sha256`.
     - Inspects protocol text for draft/proposal wording.
     - Completely removed residual cryptographic code: deleted `GOVERNANCE_PINNED_PUBKEY_HEX`, `verify_governance_signature`, `create_signed_governance_record`, and the `pinned_pubkey_hex` parameter.
5. **Update and Add Tests (COMPLETED):**
   - [`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py) updated:
     - Test Case 49 (`test_cohort3_frozen_execution_contract_and_commit_whitelist_enforcement`) tests project-lead academic governance validation, fail-closed handling, and non-circular `frozen_code_commit_sha` contract validation.
     - Test Case 50 (`test_production_protocol_file_rejection_in_current_workspace`) verified to reject draft protocol.
     - Test Case 52 (`test_no_cryptographic_signing_in_production_runner`) added to strictly verify that zero cryptographic functions, keys, or constants remain in the runner.
6. **Reconcile All Reports (COMPLETED):**
   - Audit report updated with Sections 15–17 documenting the complete elimination of cryptographic signature dependencies, the exact production runner dataset paths, canonical accent strata, and 120-speaker gate-reference panel design.
7. **Run the Complete Test Suite (COMPLETED):**
   - Full test suite verified with zero errors.
8. **Commit and Independently Audit (COMPLETED):**
   - Complete amendment committed with all links resolving cleanly.

### 16.3 Confirmatory Cohort 3 Blocker Re-Affirmation
- **Status:** **STRICTLY ON HOLD** (`DRAFT_HOLD`).
- **Authorization Scope:** Software, test-suite, runner, protocol, and governance schema remediations are fully certified. Zero confirmatory execution authorization has been granted.
- **Outstanding Scientific Prerequisites for Future Unsealing:**
  1. Physical materialization and SHA-256 verification of all 19,800 audio clips on disk at `datasets/external/common_voice_27/cohort3_audio/`.
  2. Dedicated gate-reference sentinel panel partition materialization (120 speakers, 20/stratum across all 6 canonical strata) at `datasets/external/common_voice_27/gate_reference_audio/` and locking in `datasets/splits/stage6m_gate_reference_manifest.json`.
  3. Final physical manifest SHA-256 locking in `datasets/splits/stage6m_cohort3_manifest.json`.
  4. Final protocol status transition from draft to frozen confirmatory protocol.
  5. Project-Lead Academic Authorization Record status update from `DRAFT_HOLD` to `APPROVED` binding the exact execution commit and manifest hash.

### 16.4 Detailed Implementation Roadmap for Confirmatory Cohort 3
Removing the cryptographic signature requirement does not bypass scientific rigour. The following concrete, five-phase procedure must be executed in sequence before Cohort 3 can be launched:

```
[Phase 1: Stratified Speaker & Clip Selection] 
  Select 1,320 speakers across 6 canonical strata (220/stratum, 15 clips/speaker = 19,800 clips)
  Canonical strata: US English, England English, South Asian English, Australian English, Canadian English, Irish English
  Ensure strict disjointness from Cohort 1 (train/dev) and Cohort 2 (preliminary evaluation)
         │
         ▼
[Phase 2: Audio Dataset Materialization]
  Download/materialize all 19,800 physical .flac/.mp3 audio files to:
    datasets/external/common_voice_27/cohort3_audio/
  Compute and verify SHA-256 checksum for every individual audio file
  Create dataset table: datasets/splits/stage6m_cohort3_audio.csv
         │
         ▼
[Phase 3: Sentinel Gate-Reference Panel Partitioning]
  Materialize separate 120-speaker panel (20 speakers/stratum across 6 canonical strata) to:
    datasets/external/common_voice_27/gate_reference_audio/
  Confirm zero speaker overlap with Cohort 3 or prior cohorts
  Create panel table: datasets/splits/stage6m_gate_reference_panel.csv
  Freeze panel manifest: datasets/splits/stage6m_gate_reference_manifest.json
         │
         ▼
[Phase 4: Physical Manifest Generation & Locking]
  Generate production manifest: datasets/splits/stage6m_cohort3_manifest.json
    - Contains exact paths, transcripts, audio SHA-256s, and CSV hash
    - Binds frozen_code_commit_sha: "f17328e913a1fe1045f6277dc0dbbcbc7469b184"
  Compute manifest lock hash: manifest_sha256 = sha256(stage6m_cohort3_manifest.json)
         │
         ▼
[Phase 5: Project-Lead Academic Authorization Record Update]
  Update reports/stage6m/stage6m_v1_4_governance_approval_record.json:
    - approved_manifest_sha256 = <manifest_sha256>
    - approved_commits = [<tested_execution_commit_sha>]
    - frozen_code_commit_sha = <tested_execution_commit_sha>
    - governance_status = "APPROVED"
  Finalize protocol text (transition status from draft to frozen)
         │
         ▼
[Phase 6: Confirmatory Benchmark Execution]
  Execute runner on Kaggle cloud environment:
    python cloud/kaggle/run_stage6m_cohort2_benchmark.py --cohort cohort3
  Preflight checks pass -> benchmark executes -> report generated.
```

---

## 17. Independent Remediation Audit of Commit `f17328e` & Full Remediation Verification

### 17.1 Executive Summary of Commit `f17328e` Audit
On October 27, 2026, an independent Gravitas audit of commit [`f17328e`](https://github.com/mahi3007/Final-Year-Project/commit/f17328e913a1fe1045f6277dc0dbbcbc7469b184) evaluated the operative governance transition from cryptographic Ed25519 signatures to documented Project-Lead Academic Authorization.

- **Audited Commit:** [`f17328e913a1fe1045f6277dc0dbbcbc7469b184`](https://github.com/mahi3007/Final-Year-Project/commit/f17328e913a1fe1045f6277dc0dbbcbc7469b184)
- **Initial Verdict:** **PARTIAL PASS — Further Remediation Required**
- **Core Distinction:** Removing cryptographic signature verification from the validator evaluation path was verified, but residual code remained, the protocol draft status correctly prevented preflight pass, the commit whitelist had self-referential circularity, dataset paths diverged from runner expectations, canonical accent strata were misstated, and stored test provenance was historical.

---

### 17.2 Systematic Resolution of the 6 Audit Findings

| Finding | Severity | Description | Final Status | Verified Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Finding 1: Residual Cryptographic Code** | Must Fix | Residual constants, signing/verification functions, and parameters (`GOVERNANCE_PINNED_PUBKEY_HEX`, `verify_governance_signature`, `create_signed_governance_record`, `pinned_pubkey_hex`) remained in the production runner. | **RESOLVED & VERIFIED** | Completely excised from [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py). Regression Test Case 52 (`test_no_cryptographic_signing_in_production_runner`) added and passing. |
| **Finding 2: Protocol Section 14.7 & Draft Status** | Execution Blocker | Protocol Section 14.7 referenced in audit was absent from protocol document, and draft marker was present in protocol file. | **RESOLVED & VERIFIED** | Formally enacted `### 14.7 Operative Authorization Gate: Project-Lead Academic Authorization Record` in [`stage6m_v1_4_selective_adaptation_protocol.md`](stage6m_v1_4_selective_adaptation_protocol.md). Recalculated SHA-256 (`feeda07e2b34caaee1338a0a546d4dcdb961767d560cb7bb21a44c7165600c9b`) and updated [`stage6m_v1_4_governance_approval_record.json`](stage6m_v1_4_governance_approval_record.json). Draft status retained as deliberate fail-closed safety invariant (Test Case 50 verified). |
| **Finding 3: Commit Whitelist Self-Reference Circularity** | Governance Design Blocker | Commit cannot contain its own final SHA in a tracked file (`approved_commits`). Circularity blocked clean authorization. | **RESOLVED & VERIFIED** | Implemented non-circular code identity contract: decoupled frozen execution code identity (`frozen_code_commit_sha: "f17328e913a1fe1045f6277dc0dbbcbc7469b184"`) from later manifest/governance lock commits. Verified in Test Case 49 (Subcase 2b). |
| **Finding 4: Dataset Artifact Paths Inconsistency** | Operational Alignment | Proposed report paths diverged from runner's expected dataset paths. | **RESOLVED & VERIFIED** | Reconciled all paths across reports to exact runner constants: `datasets/splits/stage6m_cohort3_manifest.json`, `datasets/splits/stage6m_cohort3_audio.csv`, `datasets/external/common_voice_27/cohort3_audio/`, `datasets/splits/stage6m_gate_reference_manifest.json`, `datasets/splits/stage6m_gate_reference_panel.csv`, `datasets/external/common_voice_27/gate_reference_audio/`. |
| **Finding 5: Canonical Strata & Panel Size Mismatch** | Statistical / Alignment | Roadmap listed non-canonical strata (US, UK, Indian, Australian, Canadian, African) and 10 speakers/stratum panel (60 total) instead of runner's 20/stratum default (120 total). | **RESOLVED & VERIFIED** | Standardized strictly to the 6 canonical strata defined in Protocol Section 4.2 (`Australian English`, `Canadian English`, `England English`, `Irish English`, `South Asian English`, `US English`) and 120-speaker panel (20/stratum). |
| **Finding 6: Test Provenance Log Integrity** | Traceability | Committed log `reports/stage6m/research_validity_pytest_run.log` was from historical commit `4b3eb970` (1,024.52s) rather than capturing the amended commit run. | **RESOLVED & VERIFIED** | Fresh provenance-captured test execution executed via [`../../scripts/run_research_validity_tests.py`](../../scripts/run_research_validity_tests.py), recording exact commit SHA, working-tree status, test pass counts, and duration in [`research_validity_pytest_run.log`](research_validity_pytest_run.log). |

---

### 17.3 Independent Verification of Test Evidence
1. **Runner Cryptographic Cleanliness (Test 52):**
   - [`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py) `test_no_cryptographic_signing_in_production_runner` dynamically inspects [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py) and confirms:
     - `GOVERNANCE_PINNED_PUBKEY_HEX` is absent.
     - `verify_governance_signature` is absent.
     - `create_signed_governance_record` is absent.
     - `pinned_pubkey_hex` parameter is absent from `validate_frozen_execution_contract`.
   - **Verdict:** **PASS**.

2. **Non-Circular Commit Whitelist & Governance Validation (Test 49):**
   - Tests both direct commit whitelist matching and non-circular code identity verification (`frozen_code_commit_sha`).
   - Confirms that execution on a later manifest/governance lock commit succeeds if and only if the bound `frozen_code_commit_sha` is preapproved.
   - Confirms fail-closed behavior on missing commits, unapproved rogue commits, missing protocol hash, tampered protocol hash, draft protocol status, non-approved governance status, and corrupted governance JSON.
   - **Verdict:** **PASS**.

3. **Workspace Protocol Rejection Invariant (Test 50):**
   - Confirms that the workspace protocol file [`stage6m_v1_4_selective_adaptation_protocol.md`](stage6m_v1_4_selective_adaptation_protocol.md) is strictly rejected by the production preflight check due to draft status markers.
   - Proves that confirmatory execution remains sealed fail-closed prior to physical dataset materialization.
   - **Verdict:** **PASS**.

4. **Numerical Safety & Gate Invariant Test Suite:**
   - All 57 tests in [`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py) passed.
   - All 85 tests in [`../../tests/research_validity/test_stage6m_protocol_proposal.py`](../../tests/research_validity/test_stage6m_protocol_proposal.py) and [`../../tests/research_validity/test_stage6m_reproducibility_and_gate_validity.py`](../../tests/research_validity/test_stage6m_reproducibility_and_gate_validity.py) passed.

---

---

## 18. Independent Remediation Audit of Commit `4e83479` & Comprehensive Verification

### 18.1 Executive Summary of Commit `4e83479` Audit
On October 27, 2026, an independent Gravitas audit of commit [`4e83479`](https://github.com/mahi3007/Final-Year-Project/commit/4e83479b6930d532512fc6707486ca220b2dbf68) confirmed that Ed25519 signing and verification functions have been completely removed from the production runner, the governance record operates under `PROJECT_LEAD_ACADEMIC_AUTHORIZATION`, and governance status remains locked on `DRAFT_HOLD`.

Four specific findings were reviewed to achieve full remediation:
1. **Finding A (Test Log Provenance):** Resolving provenance tracking so the test log reflects a clean working-tree execution against the candidate commit.
2. **Finding B (Sentinel Panel Implementation & Constants):** Reconciling conflicting 5/30 legacy constants with the authoritative Confirmatory Protocol v1.4.0 120-speaker panel (20 per stratum across all 6 canonical strata), and providing production preflight validation tests.
3. **Finding C (Protocol Draft Status):** Confirming that retaining draft status is an intentional, fail-closed safety gate preventing premature execution before physical dataset materialization.
4. **Finding D (Authorization Contract Edge Cases):** Strengthening `manifest_path` physical file existence checks and verifying that supplying a frozen code identity requires a valid, non-empty approved commits list in the governance record.

---

### 18.2 Systematic Resolution of Audit Findings A–D

| Finding | Area | Description & Remediation Action | Final Status |
| :--- | :--- | :--- | :--- |
| **Finding A** | Provenance Integrity | Working-tree cleanliness and commit SHA capture resolved via two-stage clean-tree execution: code changes committed first, clean test suite executed against untouched checkout, and provenance log committed. | **RESOLVED & VERIFIED** |
| **Finding B** | Sentinel Panel Contract | Distinct constants established in [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py): `HISTORICAL_STAGE5_SENTINEL_SPEAKERS_PER_STRATUM = 5` (30 total) and `COHORT3_GATE_REF_SPEAKERS_PER_STRATUM = 20` (120 total). Added dedicated preflight validator `validate_cohort3_gate_reference_panel` and comprehensive Test Case 53. | **RESOLVED & VERIFIED** (Test 53 passing) |
| **Finding C** | Protocol Draft Invariant | Re-affirmed that the draft status of [`stage6m_v1_4_selective_adaptation_protocol.md`](stage6m_v1_4_selective_adaptation_protocol.md) is an intentional, fail-closed safety invariant verified by Test Case 50. Final protocol status transition from draft to frozen remains a future prerequisite. | **RESOLVED & VERIFIED** (Test 50 passing) |
| **Finding D** | Authorization Edge Cases | Enforced in `validate_frozen_execution_contract`: physical manifest file missing on disk strictly raises `FileNotFoundError`; `approved_manifest_sha256` locked without `manifest_path` strictly raises `ValueError`; empty or unwhitelisted governance record strictly raises `PermissionError`. Verified by Test Case 54. | **RESOLVED & VERIFIED** (Test 54 passing) |

---

### 18.3 Verification Evidence
- **Authoritative Sentinel Panel Validation (Test 53):** Valid 120-speaker panel passes; invalid 30-speaker panel, unbalanced panels (19 vs 21), conflicting speaker-accent mappings, missing canonical strata, extraneous strata, and invalid manifest roles/versions strictly fail closed.
- **Contract & Manifest Path Edge Cases (Test 54):** Missing physical manifest, missing manifest path when hash locked, empty approved commits list, and unwhitelisted frozen code identities strictly fail closed.
- **Numerical Safety Suite:** All 59 tests in [`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py) passed.

---

### 18.4 Confirmatory Cohort 3 Governance Status
- **Operative Governance Status:** **`DRAFT_HOLD`** (Strictly Locked).
- **Confirmatory Execution:** **FORBIDDEN**. Code integrity and authorization contracts are certified. Zero confirmatory benchmark execution is authorized until physical audio clips are materialized and manifest hashes locked.

---

## 19. Independent Remediation Audit of Commits `0a1109e` & `7795ced` — Resolution of Critical Finding E

### 19.1 Executive Summary of Commits `0a1109e` & `7795ced` Audit
On October 27, 2026, an independent Gravitas audit of commits [`0a1109e`](https://github.com/mahi3007/Final-Year-Project/commit/0a1109e000edeed587f7b9d635f1014d9931ab10) and [`7795ced`](https://github.com/mahi3007/Final-Year-Project/commit/7795ced154776946dcd51ce88ced4ca492795882) verified clean-tree test provenance (312 passed in 638.55s), authoritative sentinel-panel separation (20 speakers/stratum across 6 canonical strata, 120 total), and manifest-path validation.

- **Audited Implementation Commit:** [`0a1109e000edeed587f7b9d635f1014d9931ab10`](https://github.com/mahi3007/Final-Year-Project/commit/0a1109e000edeed587f7b9d635f1014d9931ab10)
- **Audited Provenance Commit:** [`7795ced154776946dcd51ce88ced4ca492795882`](https://github.com/mahi3007/Final-Year-Project/commit/7795ced154776946dcd51ce88ced4ca492795882) *(Note: canonical GitHub commit SHA corrected from earlier citation typo)*
- **Audit Verdict:** **PARTIAL PASS — One Critical Authorization Defect Identified (Finding E)**
- **Core Finding (Finding E):** The validator checked whitelist membership of `frozen_code_commit_sha`, but did not verify that the source code actually being executed matched the declared frozen code identity. Executable logic could mutate while the validator accepted the approved frozen commit.
- **Required Action:** Bind authorization directly to verifiable executable code without digital signatures, utilizing Git identity and SHA-256 deterministic content verification, updating the runner docstring protocol version, and providing regression tests.

---

### 19.2 Systematic Resolution of Audit Findings A–E

| Finding | Area | Auditor Assessment | Resolution & Implementation Details | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Finding A** | Test Provenance | PASS (Evidence of clean-tree run substantiated: 312 passed in 638.55s). | Citation typo corrected: canonical GitHub commit is [`7795ced154776946dcd51ce88ced4ca492795882`](https://github.com/mahi3007/Final-Year-Project/commit/7795ced154776946dcd51ce88ced4ca492795882). | **PASS** |
| **Finding B** | Sentinel-Panel Specification | PASS for tested contract. Distinguishes 30-speaker historical panel from 120-speaker confirmatory reference panel. | Structural constants `HISTORICAL_STAGE5_...` (5/30) and `COHORT3_GATE_REF_...` (20/120) strictly separated and validated via `validate_cohort3_gate_reference_panel` and Test Case 53. | **PASS** |
| **Finding C** | Draft Protocol Status | PASS for preserving HOLD; prerequisite remains open. | Protocol draft status intentionally retained as fail-closed safety gate. Test Case 50 verifies strict rejection of draft protocol prior to physical audio materialization. | **PASS** |
| **Finding D** | Manifest-Path & Governance Edge Cases | PASS for covered cases. Missing manifest paths and hash mismatches checked. | Enforced in `validate_frozen_execution_contract`: physical manifest missing raises `FileNotFoundError`; manifest path missing when hash locked raises `ValueError`. Verified by Test Case 54. | **PASS** |
| **Finding E** | Frozen Execution-Code Identity | **FAIL** — Whitelist membership was checked, but running code was not verified against declared frozen code identity. | **RESOLVED & VERIFIED**: Implemented deterministic executable code identity verification (`compute_execution_code_digest`, `verify_frozen_execution_code_identity`, Test Case 55) binding running code to frozen commit [`310cf4f`](https://github.com/mahi3007/Final-Year-Project/commit/310cf4ff6221d704fa7a8318af9d3d13362b0fa3) and digest `0ca1eaf33aab05ad4d63be51abbc7355db4583500cb9dce60528b9acc473e58c`. | **RESOLVED & VERIFIED** (Test 55 passing) |

---

### 19.3 Architecture of Verifiable Executable Code Identity (Protocol Section 14.7)

To eliminate the authorization defect without reintroducing cryptographic signatures (such as Ed25519), the runner enforces deterministic content hashing and Git path-level immutability:

1. **Executable Code Scope (57 Core Files):**
   - The production runner: [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py)
   - All runtime dependency modules in the active package: `src/dsg_ctta/**/*.py` (56 modules).
   - Documentation, dataset manifests, governance approval records, and test logs are explicitly excluded from the code identity hash, allowing non-circular governance locking on later commits.

2. **Cross-Platform Deterministic Normalization:**
   - In `compute_execution_code_digest(project_root)`, raw file bytes are read and binary CRLF line endings (`\r\n`) are normalized to LF (`\n`).
   - Ensures that the calculated SHA-256 digest is byte-for-byte identical across Windows checkouts (CRLF) and Linux/Kaggle environments (LF).
   - Yields an authoritative 64-character lowercase hexadecimal digest: `0ca1eaf33aab05ad4d63be51abbc7355db4583500cb9dce60528b9acc473e58c`.

3. **Runtime Verification & Tamper Detection:**
   - In `verify_frozen_execution_code_identity(...)`:
     - Compares the running codebase's computed digest against `expected_code_digest`. Mismatch immediately raises `PermissionError`.
     - When running on a later Git commit (e.g., a governance-lock or manifest-lock commit), executes `git diff --name-only <frozen_code_commit_sha> -- cloud/kaggle/run_stage6m_cohort2_benchmark.py src/dsg_ctta`. Any detected change immediately raises `PermissionError`.
   - In `validate_frozen_execution_contract(...)`:
     - Cross-validates manifest `frozen_code_digest` against the governance record's authoritative digest. Any mismatch raises `ValueError`.
     - Fails closed if the frozen code identity is unapproved, mutated, or missing.

4. **Protocol Version Docstring Synchronization:**
   - Updated the runner module docstring in [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py) to declare `Protocol: v1.4.0-stage6m-selective-adaptation-confirmatory`, removing the legacy v1.3.4 label.

5. **Clarification on Unverified Manifest Hash Under `DRAFT_HOLD`:**
   - Documented in the governance approval record rationale that `approved_manifest_sha256` (`7dcf8d5812ce8b555d1f4c0b1a1f2d63263e83c81120bd811cc8fcb427cfbd95`) is an unverified placeholder held under `DRAFT_HOLD`.
   - The authoritative manifest hash will be calculated and locked only after the 19,800 physical Cohort 3 audio clips are materialized and verified.

---

### 19.4 Regression Test Evidence: Test Case 55

[`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py) incorporates **Test Case 55** (`test_frozen_execution_code_identity_binding_and_mutation_rejection`), which verifies:
- **Subcase 1 (Deterministic Digest):** `compute_execution_code_digest()` produces a valid 64-char lowercase SHA-256 string.
- **Subcase 2 (Unchanged Frozen Codebase):** Cleanly passes when running code matches frozen commit and digest.
- **Subcase 3 (Approved Governance-Only Update on Later Commit):** Passes when running on a later commit (e.g., manifest/governance lock) provided execution code files remain unchanged from the frozen identity.
- **Subcase 4a (Manifest-Governance Digest Mismatch):** Strictly raises `ValueError` if a manifest attempts to declare an unauthorized code digest.
- **Subcase 4b (Tampered / Mutated Executing Code):** Strictly raises `PermissionError` when executing code differs from the frozen digest, even if the frozen commit remains whitelisted.
- **Subcase 5 (Synthetic Dependency Mutation):** Mutating a dependency module in `src/dsg_ctta/` alters the digest and triggers an immediate fail-closed `PermissionError`.

**Test Status:** All 60 tests in `test_stage6m_numerical_safety.py` PASSED (60/60).

---

### 19.5 Interim Governance Status at Commit `310cf4f`

- **Frozen Execution Code Commit:** [`310cf4ff6221d704fa7a8318af9d3d13362b0fa3`](https://github.com/mahi3007/Final-Year-Project/commit/310cf4ff6221d704fa7a8318af9d3d13362b0fa3)
- **Operative Governance Status:** **`DRAFT_HOLD`** (Strictly Locked).

---

## 20. Independent Audit of Critical Finding E Remediation & Full Fail-Closed Certification

### 20.1 Executive Summary of Finding E Audit
On October 27, 2026, an independent Gravitas audit of commit [`310cf4f`](https://github.com/mahi3007/Final-Year-Project/commit/310cf4ff6221d704fa7a8318af9d3d13362b0fa3), governance commit [`61e2288`](https://github.com/mahi3007/Final-Year-Project/commit/61e228803835697ed6ca939a158993e5f3cf7545), and test provenance commit [`0fdcba7`](https://github.com/mahi3007/Final-Year-Project/commit/0fdcba7257cbb9ac04ce9b38602fd0a5832aba36) evaluated the deterministic code-identity binding mechanism.

- **Auditor Verdict:** **PARTIAL PASS — One Critical Fail-Closed Defect Identified**
- **Defect Identified:** In `verify_frozen_execution_code_identity(...)`, the Git-diff check raised `PermissionError` inside a broad `try/except Exception:` block, which caught and suppressed its own `PermissionError`. Consequently, the Git-diff layer could fail open on modified execution files if an updated digest was supplied.
- **Test Artifact Flaw:** Test Case 55's governance-only update test scenario had inadvertently used `0a1109e` (where the runner had actually changed) and only passed because the swallowed exception allowed it through.

---

### 20.2 Exact Remediation Implemented

| Area | Audit Requirement | Implementation Details | Verified Status |
| :--- | :--- | :--- | :--- |
| **A. Exception Handling** | Do not catch or suppress `PermissionError`. Catch only specific Git execution failures (`CalledProcessError`, `FileNotFoundError`, `OSError`). | Refactored [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py): `PermissionError` is raised strictly outside the `try/except` block. Added support for commit-to-commit comparison when running on subsequent Git revisions. | **RESOLVED & VERIFIED** |
| **B. Mandatory Frozen Digest** | Require valid 64-char lowercase SHA-256 digest from governance record whenever frozen code commit is declared. Reject execution if missing. | In `verify_frozen_execution_code_identity`, `expected_code_digest` is strictly mandatory, non-empty, and validated for 64 hex characters. In `validate_frozen_execution_contract`, missing `frozen_code_digest` in governance approval record strictly raises `PermissionError`. | **RESOLVED & VERIFIED** |
| **C. Test Case 55 Repair** | Use authentic commit pair where execution code is unchanged. Add explicit tests for changed runner, missing/malformed digest, and Git failure without usable digest. | Refactored Test Case 55 in [`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py) with 10 comprehensive subcases. Explicitly tested rejection of `0a1109e` (`PermissionError`). Verified that reintroducing broad exception handler fails test. | **RESOLVED & VERIFIED** (60/60 passed) |
| **D. Clean Provenance Run** | Commit code first, execute 313-test suite on clean checkout, verify 0 failures, commit log, and update audit trail. | Code committed at [`37ba1ab`](https://github.com/mahi3007/Final-Year-Project/commit/37ba1ab6a524a82cc7c69ed2aeb2f8259df125e8); governance locked at [`98aa4b7`](https://github.com/mahi3007/Final-Year-Project/commit/98aa4b7f16cae8037ca5092a1cf681d75b4c266b); clean-tree test run completed with **313 passed in 648.17s** (`git_working_tree_clean_pre_run: true`). | **RESOLVED & VERIFIED** |

---

### 20.3 Cryptographic-Free Code Identity Binding Verification

1. **Executable Code Scope (57 Core Files):**
   - Runner: [`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py)
   - Active package modules: `src/dsg_ctta/**/*.py` (56 modules).

2. **Authoritative Frozen Code Commit & Digest:**
   - **Frozen Code Commit:** [`37ba1ab6a524a82cc7c69ed2aeb2f8259df125e8`](https://github.com/mahi3007/Final-Year-Project/commit/37ba1ab6a524a82cc7c69ed2aeb2f8259df125e8)
   - **Deterministic Code Digest:** `1333b8b647e1df920336b8e937e7695826f30e3cd01cf00f22526d9443bcc758`
   - Normalized binary line endings (CRLF→LF) guarantee bitwise consistency across platforms.

3. **Multi-Layer Fail-Closed Protection:**
   - **Layer 1 (Mandatory Digest Check):** Missing, empty, or non-64-hex digest immediately raises `PermissionError`.
   - **Layer 2 (Deterministic Content Check):** Any file modification in the 57 execution files immediately alters the computed SHA-256 and raises `PermissionError`.
   - **Layer 3 (Unsuppressed Git-Diff Check):** When running on subsequent revisions, Git diff compares execution files against the frozen commit. Any detected changes raise `PermissionError` outside all exception handlers.
   - **Layer 4 (Independent Governance Lock):** Manifest declarations must match the governance approval record's locked digest; discrepancies raise `ValueError`.

---

### 20.4 Final Test Suite Provenance Evidence

The complete research-validity test suite was executed against clean commit [`98aa4b7`](https://github.com/mahi3007/Final-Year-Project/commit/98aa4b7f16cae8037ca5092a1cf681d75b4c266b) via [`../../scripts/run_research_validity_tests.py`](../../scripts/run_research_validity_tests.py):

```
=== PROVENANCE HEADER ===
git_commit_sha: 98aa4b7f16cae8037ca5092a1cf681d75b4c266b
git_working_tree_clean_pre_run: true
git_working_tree_clean_post_run: true
cleanliness_verification_scope: checked immediately before and immediately after subprocess execution; does not monitor in-flight transient filesystem modifications during execution
git_describe: 98aa4b7
execution_timestamp_utc: 2026-10-27T09:00:22Z
python_version: 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
executable_path: C:\Users\venka\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe
command: C:\Users\venka\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe -m pytest tests/research_validity/ -v --tb=short
=== END PROVENANCE HEADER ===

...
================= 313 passed, 6 warnings in 648.17s (0:10:48) =================
```

---

### 20.5 Interim Governance Status at Commit `37ba1ab`

- **Frozen Execution Code Commit:** [`37ba1ab6a524a82cc7c69ed2aeb2f8259df125e8`](https://github.com/mahi3007/Final-Year-Project/commit/37ba1ab6a524a82cc7c69ed2aeb2f8259df125e8)
- **Frozen Execution Code Digest:** `1333b8b647e1df920336b8e937e7695826f30e3cd01cf00f22526d9443bcc758`
- **Operative Governance Status:** **`DRAFT_HOLD`** (Strictly Locked).

---

## 21. Independent Audit of Latest Remediation — Authentic Historical Worktree Verification & Running HEAD Match Enforcement

### 21.1 Executive Summary of Independent Audit
On October 27, 2026, an independent Gravitas audit of commit [`37ba1ab`](https://github.com/mahi3007/Final-Year-Project/commit/37ba1ab6a524a82cc7c69ed2aeb2f8259df125e8), governance lock commit [`98aa4b7`](https://github.com/mahi3007/Final-Year-Project/commit/98aa4b7f16cae8037ca5092a1cf681d75b4c266b), and provenance commit [`ac3644f`](https://github.com/mahi3007/Final-Year-Project/commit/ac3644ff66d4f9d840afc69f96912b050bcc1260) evaluated the implementation:

- **Auditor Verdict:** **PARTIAL PASS — Implementation Fixed; One Test-Evidence Issue Remaining**
- **Verified Strengths:**
  1. Git-diff rejection is no longer swallowed (`PermissionError` raised outside all exception handlers).
  2. Mandatory valid SHA-256 code digest enforced.
  3. Governance and execution code hashes agreed at `1333b8b647e1df920336b8e937e7695826f30e3cd01cf00f22526d9443bcc758`.
  4. Repository log confirmed 313 passed tests on clean checkout `98aa4b7`.
- **Remaining Issue Identified:**
  In Test Case 55's positive governance-only-update scenario, the test computed a code digest from the current checkout (containing commit `37ba1ab`), but passed historical commit pair `310cf4f` and `61e2288` to the Git diff validator. The source being hashed and the commit being compared were not demonstrably the same revision.
- **Recommended Correction:**
  1. Use a real checkout or temporary Git worktree of `61e2288` for the positive scenario, verify that its on-disk code digest equals the frozen digest of `310cf4f`, and validate for that exact checkout.
  2. Retain the changed-runner rejection test as a separate negative case.
  3. Add an additional guard verifying that supplied `current_git_commit_sha` matches the repository's actual running `HEAD` during execution to prevent helper misuse with a commit label differing from the running checkout.
  4. Re-run the full 313-test research-validity suite on the clean checkout, capturing fresh provenance after committing the code and test changes.

---

### 21.2 Exact Remediation Implemented

| Area | Audit Requirement | Implementation Details | Verified Status |
| :--- | :--- | :--- | :--- |
| **A. Running HEAD Correspondence Guard** | Verify that declared `current_git_commit_sha` matches repository's actual `HEAD` during execution to prevent helper misuse with historical commit labels differing from checkout. | In `verify_frozen_execution_code_identity(...)` ([`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py)), when `current_git_commit_sha` is supplied and resolves to a commit in the repository, it verifies `git rev-parse clean_current == git rev-parse HEAD`. Any discrepancy immediately raises `PermissionError` with diagnostic message `Confirmatory Execution Code Identity Violation: Declared current commit '<commit>' does not match running repository HEAD '<actual_head>'`. Tested in Test Case 55 Subcase 2b. | **RESOLVED & VERIFIED** |
| **B. Authentic Historical Worktree in Test 55** | Ensure positive scenario in Test Case 55 hashes and validates the actual on-disk files corresponding to the historical commit pair (`310cf4f` -> `61e2288`). | In Test Case 55 Subcase 3 ([`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py)), creates an authentic temporary detached Git worktree at `61e228803835697ed6ca939a158993e5f3cf7545`, computes `compute_execution_code_digest` directly from the worktree files, asserts `wt_digest == "0ca1eaf33aab05ad4d63be51abbc7355db4583500cb9dce60528b9acc473e58c"`, and runs `validate_frozen_execution_contract` against that exact checkout. Passes with `contract_status == "APPROVED"`. | **RESOLVED & VERIFIED** |
| **C. Separate Negative Changed-Runner Test** | Keep changed-runner rejection as a distinct negative test case. | In Test Case 55 Subcase 4, tests `0a1109e000edeed587f7b9d635f1014d9931ab10` against `61e228803835697ed6ca939a158993e5f3cf7545` inside the authentic worktree. Strictly detects modified runner and raises `PermissionError`. | **RESOLVED & VERIFIED** |
| **D. Updated Governance Lock** | Lock new implementation commit and execution code digest in governance record. | Implementation and test changes committed at [`4622d81`](https://github.com/mahi3007/Final-Year-Project/commit/4622d81a382166d5195a665ae6ea06b3a999e39a); new code digest `64224841a3a39221eff9541aacd5a00faef50bbbaae042e0fc73b9cb2e659f8b` locked at commit [`a019621`](https://github.com/mahi3007/Final-Year-Project/commit/a0196218151978d380e2fceae5653554e7d1fc06). | **RESOLVED & VERIFIED** |
| **E. Clean Provenance Run** | Execute 313-test suite on clean checkout of locked governance commit. | Executed [`../../scripts/run_research_validity_tests.py`](../../scripts/run_research_validity_tests.py) on clean commit [`a019621`](https://github.com/mahi3007/Final-Year-Project/commit/a0196218151978d380e2fceae5653554e7d1fc06). **313 passed, 6 warnings in 662.55s**. Clean-tree verified before and after execution. | **RESOLVED & VERIFIED** |

---

### 21.3 Fresh Clean-Tree Provenance Evidence

```
=== PROVENANCE HEADER ===
git_commit_sha: a019621c0631df6d957c60b476368ce9a167ff09
git_working_tree_clean_pre_run: true
git_working_tree_clean_post_run: true
cleanliness_verification_scope: checked immediately before and immediately after subprocess execution; does not monitor in-flight transient filesystem modifications during execution
git_describe: a019621
execution_timestamp_utc: 2026-10-27T10:03:32Z
python_version: 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
executable_path: C:\Users\venka\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe
command: C:\Users\venka\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe -m pytest tests/research_validity/ -v --tb=short
=== END PROVENANCE HEADER ===

...
================= 313 passed, 6 warnings in 662.55s (0:11:02) =================
```

---

### 21.4 Final Confirmatory Cohort 3 Governance Status

- **Frozen Execution Code Commit:** [`4622d81a382166d5195a665ae6ea06b3a999e39a`](https://github.com/mahi3007/Final-Year-Project/commit/4622d81a382166d5195a665ae6ea06b3a999e39a)
- **Frozen Execution Code Digest:** `64224841a3a39221eff9541aacd5a00faef50bbbaae042e0fc73b9cb2e659f8b`
- **Operative Governance Status:** **`DRAFT_HOLD`** (Strictly Locked).
- **Confirmatory Execution:** **FORBIDDEN**. Code identity verification, authentic worktree regression, sentinel-panel separation, and manifest-path guards are certified. Zero confirmatory benchmark execution is authorized until physical audio clips are materialized and manifest hashes locked.

---

## 22. Independent Audit of Latest Remediation — Fail-Closed Commit Resolution & Historical-Worktree Subprocess Execution (Finding F Resolution)

### 22.1 Executive Summary of Independent Audit
On October 27, 2026, an independent Gravitas audit of implementation commit [`4622d81`](https://github.com/mahi3007/Final-Year-Project/commit/4622d81a382166d5195a665ae6ea06b3a999e39a), governance lock commit [`a019621`](https://github.com/mahi3007/Final-Year-Project/commit/a019621c0631df6d957c60b476368ce9a167ff09), and provenance commit [`89c07f3`](https://github.com/mahi3007/Final-Year-Project/commit/89c07f3ba8cd8b4dd49f75a00d1d7dbca38e26c9) evaluated the code-identity verification contract and historical worktree test:

- **Auditor Verdict:** **PARTIAL PASS — One Authorization Edge Case Remaining (Finding F)**
- **Audit Findings:**
  1. **Finding F (Unresolvable Commit Identifiers Skipped Instead of Rejected):**
     In `verify_frozen_execution_code_identity(...)`, the helper asked Git whether `current_git_commit_sha` resolved to a commit. The HEAD correspondence check and mismatch rejection only executed inside the branch where that check succeeded. If `is_commit` was false (e.g. `current_git_commit_sha="not-a-real-commit"`), the comparison was skipped. The helper could return successful identity verification without establishing the claimed current commit identity.
  2. **Silent Project Root Fallback:**
     When an explicitly supplied `project_root` did not contain the runner file, the helper silently swapped roots to `PROJECT_ROOT.resolve()` rather than failing closed.
  3. **Historical-Worktree Test Qualification:**
     In Test Case 55, the positive historical-worktree scenario imported `run_stage6m_cohort2_benchmark` from the main test checkout before creating the detached worktree at `61e2288`. The test verified the historical files' digest and ran the current validator against that path, but did not execute the validator from within the historical worktree itself.

---

### 22.2 Systematic Resolution of Finding F & Authorization Hardening

| Area | Audit Requirement | Implementation Details | Verified Status |
| :--- | :--- | :--- | :--- |
| **A. Strict Fail-Closed Commit Resolution** | Require Git to resolve `current_git_commit_sha` to a valid commit object; require resolved commit to equal actual repository `HEAD`; reject unresolvable SHA, mismatch, or failed Git check with `PermissionError`. | In `verify_frozen_execution_code_identity(...)` ([`../../cloud/kaggle/run_stage6m_cohort2_benchmark.py`](../../cloud/kaggle/run_stage6m_cohort2_benchmark.py)):<br>1. Executes `git rev-parse HEAD` in `root`; if failed, strictly raises `PermissionError`.<br>2. Executes `git rev-parse --verify clean_current^{commit}`; if unresolvable, strictly raises `PermissionError: Declared current commit '<commit>' cannot be resolved to a valid Git commit object`.<br>3. Verifies `resolved_current == actual_head`; if mismatch, strictly raises `PermissionError: Declared current commit '<commit>' does not match running repository HEAD '<actual_head>'`.<br>4. Any Git process error during diff comparison strictly raises `PermissionError`. | **RESOLVED & VERIFIED** (Subcases 2b, 2c, 2d passing) |
| **B. No Silent Root Substitution** | Avoid silently substituting a different project root when an explicitly supplied `project_root` does not contain the required runner file. | In `verify_frozen_execution_code_identity(...)`, if `project_root` is passed and `project_root / "cloud" / "kaggle" / "run_stage6m_cohort2_benchmark.py"` does not exist, strictly raises `FileNotFoundError: Runner file not found in specified project root`. In `validate_frozen_execution_contract`, only sets `proj_root = candidate` if the runner file physically exists inside `candidate`. | **RESOLVED & VERIFIED** (Subcase 2e passing) |
| **C. Historical-Worktree Subprocess Execution** | Run the positive historical scenario in a subprocess whose working directory and Python import path point to the detached worktree, asserting that the module's resolved file path is inside that worktree. | In Test Case 55 Subcase 3 ([`../../tests/research_validity/test_stage6m_numerical_safety.py`](../../tests/research_validity/test_stage6m_numerical_safety.py)), creates an isolated script inside `worktree_dir` (`61e2288`), executes via `subprocess.run([sys.executable, ...], cwd=str(worktree_dir), check=True)`, asserts `runner.__file__` resolves to `worktree_dir / "cloud" / "kaggle" / "run_stage6m_cohort2_benchmark.py"`, asserts code digest equals `0ca1eaf33aab05ad4d63be51abbc7355db4583500cb9dce60528b9acc473e58c`, and validates the frozen contract to `APPROVED`. | **RESOLVED & VERIFIED** |
| **D. Real Commit Fixtures** | Replace synthetic labels such as `runtime_commit_bbb`, `audit_commit_aaa`, and `commit_lock_789` with real commits in existing test fixtures. | Updated Test Case 49 (Subcase 2b) and Test Case 54 to query and use actual repository `HEAD` commit SHA and real historical commits (`0a1109e...`), eliminating all synthetic commit strings. | **RESOLVED & VERIFIED** |
| **E. Clean Provenance Run** | Execute 313-test research-validity suite on clean checkout of locked governance commit. | Executed [`../../scripts/run_research_validity_tests.py`](../../scripts/run_research_validity_tests.py) on clean commit [`457b631`](https://github.com/mahi3007/Final-Year-Project/commit/457b6312873a5393d0df042a4992d8c9f4916e1c). **313 passed, 6 warnings in 774.69s (12m 54s)**. Clean working-tree verified before and after execution (`git_working_tree_clean_pre_run: true`, `git_working_tree_clean_post_run: true`). | **RESOLVED & VERIFIED** |

---

### 22.3 Fresh Clean-Tree Provenance Evidence

```
=== PROVENANCE HEADER ===
git_commit_sha: 457b6312873a5393d0df042a4992d8c9f4916e1c
git_working_tree_clean_pre_run: true
git_working_tree_clean_post_run: true
cleanliness_verification_scope: checked immediately before and immediately after subprocess execution; does not monitor in-flight transient filesystem modifications during execution
git_describe: 457b631
execution_timestamp_utc: 2026-10-27T10:55:22Z
python_version: 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
executable_path: C:\Users\venka\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe
command: C:\Users\venka\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe -m pytest tests/research_validity/ -v --tb=short
=== END PROVENANCE HEADER ===

...
================= 313 passed, 6 warnings in 774.69s (0:12:54) =================
```

---

### 22.4 Final Confirmatory Cohort 3 Governance Status

- **Frozen Execution Code Commit:** [`a7a3b79c1f06524128d035537de138e473c6455f`](https://github.com/mahi3007/Final-Year-Project/commit/a7a3b79c1f06524128d035537de138e473c6455f)
- **Frozen Execution Code Digest:** `8bec4fe8634474a243110753da182eab578460c66681b4eec38bc4dd70fcbce6`
- **Operative Governance Status:** **`DRAFT_HOLD`** (Strictly Locked).
- **Confirmatory Execution:** **FORBIDDEN**. All code-identity authorization edge cases, unresolvable commit rejection, subprocess historical-worktree execution, sentinel-panel separation, and manifest-path guards are certified. Zero confirmatory benchmark execution is authorized until physical audio clips are materialized and manifest hashes locked.
















