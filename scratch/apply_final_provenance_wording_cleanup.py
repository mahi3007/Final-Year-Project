import os

doc_path = "reports/stage6m/stage6m_residual_evidence_audit.md"
with open(doc_path, "r", encoding="utf-8") as fp:
    content = fp.read()

old_sec73 = """### 3. Preserved / Frozen Files (Untouched):
- [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) (SHA-256 `8fac4d32…`, size $253,229\\text{ B}$).
- [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) (SHA-256 `e964799b…`, size $557,100\\text{ B}$).
- [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) (SHA-256 `41cec79d…`, size $451,539\\text{ B}$).
- [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) (SHA-256 `665009a0…`, size $92,340\\text{ B}$).
- [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) (SHA-256 `4622b215…`, size $5,344\\text{ B}$).
- [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) and [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv).
- [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py) (SHA-256 `dddaf866…`).
- All audio files and raw recording directories."""

new_sec73 = """### 3. Preserved Baseline Files Status:
The six audited baseline paths have no reported working-tree modifications, and their normalized contents match the corresponding Git blobs. This does not establish that no temporary, uncommitted edits occurred and were subsequently reverted.
- [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) (SHA-256 `8fac4d32…`, size $253,229\\text{ B}$; execution provenance and historical immutability remain UNVERIFIED).
- [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) (Physical disk size $557,100\\text{ B}$, SHA-256 `e964799b…`; normalized LF size $550,194\\text{ B}$, SHA-256 `96534400…`).
- [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) (Physical disk size $451,539\\text{ B}$, SHA-256 `41cec79d…`; normalized LF size $450,638\\text{ B}$, SHA-256 `56cb4f9f…`).
- [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) (Physical disk size $92,340\\text{ B}$, SHA-256 `665009a0…`; normalized LF size $92,039\\text{ B}$, SHA-256 `612b7045…`).
- [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) (Physical disk size $5,344\\text{ B}$, SHA-256 `4622b215…`; normalized LF size $5,267\\text{ B}$, SHA-256 `63a189fd…`).
- [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) and [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv).
- [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py) (SHA-256 `dddaf866…`).
- All audio files and raw recording directories."""

assert old_sec73 in content, "old_sec73 not found"
content = content.replace(old_sec73, new_sec73)

with open(doc_path, "w", encoding="utf-8") as fp:
    fp.write(content)

print("Updated Section 7.3 in residual audit report successfully.")

# Now append Correction 21 to changelog
changelog_path = "reports/stage6m/stage6m_v1_2_0_changelog.md"
with open(changelog_path, "r", encoding="utf-8") as fp:
    cl_content = fp.read()

correction_21 = """

### Correction 21: Final Provenance Wording Cleanup
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Primary Report Updated:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md)
- **Wording Rectification Applied:**
  - Replaced ambiguous descriptions of baseline artifacts as \"clean and pristine\" with the precise governing statement:
    *\"The six audited baseline paths have no reported working-tree modifications, and their normalized contents match the corresponding Git blobs. This does not establish that no temporary, uncommitted edits occurred and were subsequently reverted.\"*
  - Preserved all verified checksum values, full SHA-256 logs in [`git_normalization_verification_v1_2_0.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/git_normalization_verification_v1_2_0.txt), Git object IDs, line-ending normalization results, speaker counts, simulation seeds, and test evidence.
  - Zero frozen datasets, split manifests, simulation outputs, or test execution logs were regenerated, re-run, or overwritten.
  - Governance state remains unchanged: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, Confirmatory Execution Verdict: **STRICT NO-GO**.
"""

if "### Correction 21:" not in cl_content:
    with open(changelog_path, "a", encoding="utf-8") as fp:
        fp.write(correction_21)
    print("Correction 21 appended to changelog successfully.")
else:
    print("Correction 21 already present.")
