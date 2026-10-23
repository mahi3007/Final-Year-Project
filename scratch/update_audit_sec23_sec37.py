import re

doc_path = r"reports\stage6m\stage6m_data_feasibility_audit.md"
with open(doc_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace Section 2.3
sec23_old = """### 2.3 Cryptographic Artifact Provenance Hashes

The candidate pool inventory, previous exposure splits, and sentinel manifests are verified against authoritative SHA-256 digests:

| Artifact Path | SHA-256 Checksum | Record / Speaker Count | Epistemic Role |
| :--- | :---: | :---: | :--- |
| [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | `e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a` | $6,905$ speakers | Canonical candidate pool ground truth |
| [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) | `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32` | $60$ speakers ($10$/group) | Cohort 1 replication evaluation stream |
| [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) | `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543` | $30$ speakers ($5$/group) | Online Sentinel Panel safety monitor |
| [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) | `4622b215b18c6b4de80fb7832788ce7286e88c5528f501e2bac62f935e570028` | $30$ speakers | Sentinel Panel metadata manifest |
| [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) | `c2a746db83e02e81289baf8ca5fcd95be254a6e1de312a3f76c9b44e8c899d03` | $24$ speakers | Stage 4 characterization split |
| [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv) | `7c1659433b2b3539aa02b079d30588210a799620c5182e99c2ea0a61de284ca2` | $16$ speakers | Stage 4 calibration split |"""

sec23_new = """### 2.3 Cryptographic Artifact Provenance Hashes and Byte Sizes

The candidate pool inventory, previous exposure splits, sentinel manifests, and canonical simulation results are verified against authoritative SHA-256 digests and exact disk byte sizes:

| Artifact Path | SHA-256 Checksum | Exact Disk Size | Record / Speaker Count | Epistemic Role |
| :--- | :---: | :---: | :---: | :--- |
| [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | `e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a` | $557,100\\text{ bytes}$ | $6,905$ speakers | Canonical candidate pool ground truth |
| [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) | `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32` | $451,539\\text{ bytes}$ | $60$ speakers ($10$/group) | Cohort 1 replication evaluation stream |
| [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) | `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543` | $92,340\\text{ bytes}$ | $30$ speakers ($5$/group) | Online Sentinel Panel safety monitor |
| [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) | `4622b215b18c6b4de80fb7832788ce7286e88c5528f501e2bac62f935e570028` | $5,344\\text{ bytes}$ | $30$ speakers | Sentinel Panel metadata manifest |
| [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) | `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad` | $253,229\\text{ bytes}$ | $S=4,000, B=1,000$ | Canonical serialized simulation results |
| [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) | `c2a746db83e02e81289baf8ca5fcd95be254a6e1de312a3f76c9b44e8c899d03` | $39,689\\text{ bytes}$ | $24$ speakers | Stage 4 characterization split |
| [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv) | `7c1659433b2b3539aa02b079d30588210a799620c5182e99c2ea0a61de284ca2` | $19,210\\text{ bytes}$ | $16$ speakers | Stage 4 calibration split |"""

if sec23_old in text:
    text = text.replace(sec23_old, sec23_new)
    print("Updated Section 2.3 successfully.")
else:
    print("Warning: Section 2.3 old text not matched.")

# Replace Section 3.7
sec37_old_pattern = re.compile(r"### 3\.7 Research-Validity Test Suite Execution & Qualified Warning Review.*?(?=---)", re.DOTALL)
sec37_new = """### 3.7 Research-Validity Test Suite Execution & Tripartite Test Provenance (Workstream D)

Following the addition of three regression unit tests to [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py) (expanding that module from 17 to 20 tests), the entire research-validity test directory was re-executed:

```powershell
python -m pytest tests/research_validity/ -v
```

#### Tripartite Test Suite Provenance Register:
1. **Previous Full Suite Run (110 Tests):** [`reports/stage6m/test_execution_research_validity_full.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_full.log) (SHA-256 `04d6752ff7a10229b73859cebf1684773bd55cc02b5e2ffc42db866de604da19`). Recorded 110 passed across 12 modules in $21.29\\text{ s}$ when Stage 6M had 17 tests.
2. **Stage 6M Module Verification Run (20 Tests):** [`reports/stage6m/test_execution_stage6m_proposal.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_stage6m_proposal.log) (SHA-256 `e7509390a9d9234b963178af42aefa7c6e7adce77b186e1a72e5dbde0aac8e7a`). Recorded 20 passed in $3.32\\text{ s}$ following the three new exposure and simulation regression tests.
3. **Current Full Suite Verification Run (113 Tests):** [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) (SHA-256 `2651a05b864e49b7f19e9b6af6fc50f0fe8eb28f547d248b2522a226758391fa`, exact size $16,494\\text{ bytes}$). Records **113 passed, 6 warnings in $26.15\\text{ s}$** (exit code 0, outer wall-clock $30.34\\text{ s}$).

#### Classification and Impact Analysis of All Six Warnings:

| Warning # | Warning Message & Source Location | Category / Origin | Correctness / Validity Impact | Remediation Required? |
| :---: | :--- | :--- | :--- | :---: |
| **W1** | `torchvision/transforms/_functional_pil.py:245: DeprecationWarning: BILINEAR is deprecated and will be removed in Pillow 10. Use Resampling.BILINEAR instead.` | Upstream Third-Party Deprecation (`torchvision` PIL integration) | **Zero Impact.** Image resampling interpolation enum inside external `torchvision` dependency; audio processing does not invoke PIL resampling. | **No.** External package deprecation; no project code invokes this path. |
| **W2** | `torchvision/transforms/_functional_pil.py:291: DeprecationWarning: NEAREST is deprecated and will be removed in Pillow 10. Use Resampling.NEAREST or Dither.NONE instead.` | Upstream Third-Party Deprecation (`torchvision` PIL integration) | **Zero Impact.** External library enum deprecation. | **No.** External site-package. |
| **W3** | `torchvision/transforms/_functional_pil.py:307: DeprecationWarning: NEAREST is deprecated and will be removed in Pillow 10. Use Resampling.NEAREST or Dither.NONE instead.` | Upstream Third-Party Deprecation (`torchvision` PIL integration) | **Zero Impact.** External library enum deprecation. | **No.** External site-package. |
| **W4** | `torchvision/transforms/_functional_pil.py:324: DeprecationWarning: BICUBIC is deprecated and will be removed in Pillow 10. Use Resampling.BICUBIC instead.` | Upstream Third-Party Deprecation (`torchvision` PIL integration) | **Zero Impact.** External library enum deprecation. | **No.** External site-package. |
| **W5** | `<frozen importlib._bootstrap>:241: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute` | Upstream SWIG C-Extension Bindings | **Zero Impact.** Python 3.11 C-extension module introspection warning on SWIG-generated wrapper types. | **No.** Standard Python 3.11 C-API warning. |
| **W6** | `<frozen importlib._bootstrap>:241: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute` | Upstream SWIG C-Extension Bindings | **Zero Impact.** Python 3.11 C-extension module introspection warning on SWIG-generated wrapper types. | **No.** Standard Python 3.11 C-API warning. |

#### Qualified Scientific Determination on Test Warnings:
All six warnings were attributed to third-party dependencies or extension wrappers. No effect on the reported research-validity test run was identified. The warnings are retained in the execution log rather than suppressed. Their classification does not establish the absence of all possible effects in untested execution paths. Zero warnings originate from project test files, data validation logic, statistical algorithms, or ASR pipeline code.

"""

text = sec37_old_pattern.sub(sec37_new, text)
print("Updated Section 3.7 successfully.")

with open(doc_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Saved updated stage6m_data_feasibility_audit.md successfully.")
