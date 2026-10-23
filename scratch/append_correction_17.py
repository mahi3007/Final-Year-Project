import os

changelog_path = r"reports\stage6m\stage6m_v1_2_0_changelog.md"
with open(changelog_path, "r", encoding="utf-8") as f:
    text = f.read()

correction_17 = """

### Correction 17: Frozen Artifact Integrity, Seed Provenance, and Full Test Suite Closure (Workstreams A–E)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Fresh Full-Suite Test Execution:** **`113 passed, 6 warnings in 26.15s`** in [`tests/research_validity/`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/)
- **Fresh Full-Suite Execution Log:** [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) (SHA-256 `2651a05b864e49b7f19e9b6af6fc50f0fe8eb28f547d248b2522a226758391fa`, exact size $16,494\\text{ bytes}$, exit code 0)
- **Files Modified / Synchronized:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Workstreams Audited & Formally Closed:**
  1. **Workstream A (Irish Exposure-Set Reconciliation & Elimination of Narrative Contradictions):**
     - Reconciled exact Irish candidate sets from canonical manifests: baseline inventory $|I_{\\text{Irish}}| = 94$; strict quality exclusions $|Q_{\\text{Irish}}| = 2$ (`fc22fd45...` with $C_{\\text{inv}}=15, C_{\\text{strict}}=14$, unexposed; and `f3ea0447...` with $C_{\\text{inv}}=15, C_{\\text{strict}}=13$, exposed in $E_1$).
     - Reconciled strictly eligible Irish candidates: $94 - 2 = \\mathbf{92}$.
     - Reconciled exposed Irish speakers: Replication Cohort 1 ($E_1$) contains exactly $10$ Irish speakers ($1$ in $Q$, $9$ strictly eligible); Sentinel Panel ($E_S$) contains exactly $5$ Irish speakers (all $5$ strictly eligible).
     - Strictly eligible exposed Irish candidates: $9 + 5 = \\mathbf{14}$.
     - Reconciled available unexposed strictly eligible Irish pool:
       $$|I_{\\text{available}}| = 92 - 14 = \\mathbf{78}$$
       Equivalently, subtracting total exclusions without double-counting `f3ea0447...`:
       $$|I_{\\text{available}}| = 94 - 10\\text{ (Cohort 1)} - 5\\text{ (Sentinel)} - 1\\text{ (unexposed } Q) = \\mathbf{78}$$
     - Formally rejected and expunged historical exploratory notes that claimed $6$ Irish quality exclusions ($94 - 6 = 88$) or claimed that no Sentinel Panel speakers were Irish. Reaffirmed that the Sentinel Panel contains exactly $5$ Irish speakers per frozen split manifest [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv).
  2. **Workstream B (Frozen Checksum and Disk Byte Size Forensics):**
     - Performed cryptographic SHA-256 and exact byte-count verification on physical disk files:
       * [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): Exact size **$253,229\\text{ bytes}$**, SHA-256 **`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`**. (The previously reported hash `b13c7a36...` and size `239,942 bytes` were identified as an erroneous text-entry transcription in the audit prose; the physical file on disk was never modified and remains 100% identical to canonical hash `8fac4d32...`).
       * [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv): Exact size **$557,100\\text{ bytes}$**, SHA-256 **`e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a`**. (Matches Git HEAD commit `ac9657b` identically).
       * [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv): Exact size **$451,539\\text{ bytes}$**, SHA-256 **`41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32`**.
       * [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv): Exact size **$92,340\\text{ bytes}$**, SHA-256 **`665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543`**.
       * [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json): Exact size **$5,344\\text{ bytes}$**, SHA-256 **`4622b215b18c6b4de80fb7832788ce7286e88c5528f501e2bac62f935e570028`**.
     - Confirmed that zero frozen artifacts were modified; discrepancies in previous report tables stemmed entirely from stale draft table copy-paste entries.
  3. **Workstream C (Simulation Parameter & Random Seed Provenance Reconciliation):**
     - Fully reconciled simulation seeds from canonical file `power_simulation_results.json`:
       * Deterministic seed formula across all cohort sizes: $\\text{seed} = 1000 \\times \\text{scenario\\_idx} + 1000 + 42 + \\text{cohort\\_size}$.
       * Cohort $N=420$: $\\text{seed\\_s1} = 1462$, $\\text{seed\\_s2} = 2462$.
       * Cohort $N=450$: $\\text{seed\\_s1} = 1492$, $\\text{seed\\_s2} = 2492$.
       * Cohort $N=468$: $\\text{seed\\_s1} = 1510$, $\\text{seed\\_s2} = 2510$.
       * Cohort $N=540$: $\\text{seed\\_s1} = 1582$, $\\text{seed\\_s2} = 2582$.
     - Reconciled why earlier reports cited $1582 / 2582$ for $N=540$: that was the true canonical seed pair for $N=540$. The seeds $1462 / 2462$ belonged strictly to the $N=420$ cohort.
     - Confirmed DGP parameter identity for Scenario 2 across sample sizes: both $N=468$ and $N=540$ use identical parameters $\\Delta_R = -0.85\\text{ pp}$, $\\Delta D = +0.50\\text{ pp}$, $S=4,000, B=1,000$.
  4. **Workstream D (Fresh Full Test-Suite Execution & Tripartite Separation):**
     - Executed full test suite across all 12 modules in `tests/research_validity/`.
     - Full result: **`113 passed, 6 warnings in 26.15s`** (exit code 0).
     - Captured complete log with warnings to [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) (SHA-256 `2651a05b864e49b7f19e9b6af6fc50f0fe8eb28f547d248b2522a226758391fa`).
     - Maintained explicit tripartite distinction:
       1. Previous full suite (110 tests): `test_execution_research_validity_full.log` (SHA-256 `04d6752f...`).
       2. Stage 6M module run (20 tests): `test_execution_stage6m_proposal.log` (SHA-256 `e7509390...`).
       3. Current full suite run (113 tests): `test_execution_research_validity_v1_2_0.log` (SHA-256 `2651a05b...`).
  5. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.
"""

if "### Correction 17: Frozen Artifact Integrity" not in text:
    text = text.rstrip() + "\n" + correction_17

with open(changelog_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Appended Correction 17 successfully.")
