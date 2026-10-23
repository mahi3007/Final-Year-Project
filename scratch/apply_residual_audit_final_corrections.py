import re

doc_path = "reports/stage6m/stage6m_residual_evidence_audit.md"
with open(doc_path, "r", encoding="utf-8") as fp:
    content = fp.read()

# 1. Update Section 1 seed table entry if needed
content = content.replace(
    "Script uses `np.random.seed(42 + cohort_n + sc_id * 1000)` ($1$-based `sc_id \\in \\{1,2,3,4\\}$; $0$-based index $+ 1000$).",
    "Script uses `np.random.seed(42 + cohort_n + sc_id * 1000)` ($\\\\text{seed} = 42 + N + 1000\\\\,\\\\text{sc\\\\_id}$ with $1$-based $\\\\text{sc\\\\_id} \\\\in \\\\{1,2,3,4\\\\}$). Different seed initializations produce different pseudorandom sequences."
)

# 2. Update Section 3.3 power qualification text
old_s33 = """#### Statistical Tempering: Monte Carlo Variation vs. Sample-Size Effect
Because the random seed formula incorporates `+ cohort_n`, the simulations for $N=468$ (seed $2510$) and $N=540$ (seed $2582$) instantiate **independent pseudorandom streams**. 

> [!IMPORTANT]
> **Qualified Statistical Finding on Sample-Size Scaling:**  
> The simulations use identical specified data-generating process parameters ($\Delta_R = -0.85\text{ pp}, \Delta D = +0.50\text{ pp}, \sigma_{\text{spk}} = 3.80\text{ pp}, \rho = 0.88$). The observed power difference ($85.825\%$ at $N=468$ vs. $90.40\%$ at $N=540$) is consistent with sample-size scaling. However, because independent random seeds were used, the observed difference reflects **both sample-size scaling and Monte Carlo realization variation**. It must not be characterized as an exclusively isolated or "pure" sample-size effect."""

new_s33 = """#### Statistical Tempering: Seed Initializations, Pseudorandom Sequences vs. Sample-Size Effect
Because the random seed formula incorporates `+ cohort_n`, the simulations for $N=468$ (seed $2510$) and $N=540$ (seed $2582$) use different seed initializations and therefore different pseudorandom sequences.

> [!IMPORTANT]
> **Qualified Statistical Finding on Sample-Size Scaling:**  
> The simulations use identical specified data-generating process parameters ($\Delta_R = -0.85\text{ pp}, \Delta D = +0.50\text{ pp}, \sigma_{\text{spk}} = 3.80\text{ pp}, \rho = 0.88$). The simulations use different seed initializations and therefore different pseudorandom sequences. The observed power difference ($85.825\%$ at $N=468$ vs. $90.40\%$ at $N=540$) reflects **both sample-size effects and Monte Carlo realization variation**. It must not be characterized as an exclusively isolated or "pure" sample-size effect."""

content = content.replace(old_s33, new_s33)

# 3. Update Section 4.1 note to reference git_normalization_verification_v1_2_0.txt
old_s41_note = "*Note:* In every tracked file, the byte size difference ($\text{Disk Size} - \text{Git Blob Size}$) equals the exact CRLF count, standalone CR count is strictly $0$, and `norm_disk == git_blob` evaluates to `True`."
new_s41_note = "*Note:* In every tracked file, the byte size difference ($\text{Disk Size} - \text{Git Blob Size}$) equals the exact CRLF count, standalone CR count is strictly $0$, and `norm_disk == git_blob` evaluates to `True`. The complete machine-readable verification record containing full SHA-256 digests and Git blob object IDs is published in [`reports/stage6m/git_normalization_verification_v1_2_0.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/git_normalization_verification_v1_2_0.txt) (SHA-256 `fa898d76e808...`, size $6,134\\text{ bytes}$)."
content = content.replace(old_s41_note, new_s41_note)

# 4. Update Section 4.2 text
old_s42 = """- **Epistemic Classification:**
  1. **Current Digest Match:** **VERIFIED**. The physical file on disk matches the previously recorded canonical digest `8fac4d32…` byte-for-byte.
  2. **Historical Immutability via Git:** **UNVERIFIED**. Because the file is untracked in Git, Git history cannot independently establish that the file was never modified historically. The artifact was generated deterministically by [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py), but claims of historical immutability derived from Git are unwarranted and marked **UNVERIFIED**."""

new_s42 = """- **Epistemic Classification & Provenance Qualification:**
  The current simulation JSON has the reported SHA-256 digest (`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`) and size ($253,229\\text{ bytes}$), matching the previously recorded canonical digest. Its reported contents are consistent with the proposal tables. Because the JSON is untracked and no independent version-controlled historical digest record was located, its historical immutability and execution provenance remain **UNVERIFIED**. The file was **not** regenerated or re-run to settle this question."""

content = content.replace(old_s42, new_s42)

# 5. Update Section 4.3 claim 4
old_s43_4 = """4. **Evidence of Historical Non-Modification:**
   - **Tracked Artifacts:** Established by Git commit log confirming single initial commits (`ac9657b` / `5c748af`) with zero intermediate revisions.
   - **Untracked Simulation JSON:** **UNVERIFIED via Git**. Current file digest matches the canonical documentation, but Git provides no historical tracking record."""

new_s43_4 = """4. **Historical Non-Modification Qualification:**
   No intermediate committed changes were found in the inspected Git history. The current working-tree content matches the corresponding Git blob after line-ending normalization. These checks do not establish that no temporary, uncommitted edits occurred and were subsequently reverted. (For the untracked simulation JSON, historical immutability and execution provenance are UNVERIFIED because it lacks version-controlled lineage)."""

content = content.replace(old_s43_4, new_s43_4)

# 6. Update Section 8.1 claim 4
old_s81_4 = "4. **Historical Non-Modification:** Established by Git commit lineage showing a single initial commit (`ac9657b` / `5c748af`) with zero intermediate modifications."
new_s81_4 = "4. **Historical Non-Modification Qualification:** No intermediate committed changes were found in the inspected Git history. The current working-tree content matches the corresponding Git blob after line-ending normalization. These checks do not establish that no temporary, uncommitted edits occurred and were subsequently reverted."
content = content.replace(old_s81_4, new_s81_4)

# 7. Update Section 8.2 wording
old_s82 = """- **Epistemic Classification:**
  1. **Current Digest Match:** **VERIFIED**. The physical disk file matches the canonical serialization record identically.
  2. **Historical Immutability via Git:** **UNVERIFIED**. Because the file is untracked in Git, Git commit history cannot independently establish that the file was never modified historically.
- **Protocol Governance Action:** The simulation JSON was **NOT regenerated, re-run, or modified**. Its historical-immutability claim is formally recorded as **UNVERIFIED via Git**, while its current physical integrity is preserved."""

new_s82 = """- **Epistemic Classification & Provenance Qualification:**
  The current simulation JSON has the reported SHA-256 digest (`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`) and size ($253,229\\text{ bytes}$), matching the previously recorded canonical digest. Its reported contents are consistent with the proposal tables. Because the JSON is untracked and no independent version-controlled historical digest record was located, its historical immutability and execution provenance remain **UNVERIFIED**.
- **Protocol Governance Action:** The simulation JSON was **NOT regenerated, re-run, or modified**. Its execution provenance and historical immutability remain formally recorded as **UNVERIFIED**, while its current physical integrity is preserved."""

content = content.replace(old_s82, new_s82)

# 8. Update Section 8.4 seed text
old_s84 = """  - Power difference qualification: Because simulations use cohort-dependent seeds, random streams are independent. The observed power difference ($85.83\%$ at $N=468$ vs. $90.40\%$ at $N=540$) reflects **both sample-size scaling and Monte Carlo realization variation** (not an exclusively isolated "pure sample-size effect")."""
new_s84 = """  - Power difference qualification: The simulations use different seed initializations and therefore different pseudorandom sequences. The observed power difference ($85.83\%$ at $N=468$ vs. $90.40\%$ at $N=540$) reflects **both sample-size effects and Monte Carlo realization variation** (not an exclusively isolated "pure sample-size effect")."""
content = content.replace(old_s84, new_s84)

# 9. Update Deliverable File Inventory to include git_normalization_verification_v1_2_0.txt
old_inv = """- [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md): This report (comprehensive residual audit artifact).
- [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log): Full terminal output for 113 tests in 26.15s (SHA-256 `2651a05b…`)."""

new_inv = """- [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md): This report (comprehensive residual audit artifact).
- [`reports/stage6m/git_normalization_verification_v1_2_0.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/git_normalization_verification_v1_2_0.txt): Complete machine-readable normalization verification log with full SHA-256 digests and Git blob IDs (SHA-256 `fa898d76e808...`, size $6,134\\text{ bytes}$).
- [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log): Full terminal output for 113 tests in 26.15s (SHA-256 `2651a05b…`)."""

content = content.replace(old_inv, new_inv)

with open(doc_path, "w", encoding="utf-8") as fp:
    fp.write(content)

print("Applied final residual audit corrections successfully.")
