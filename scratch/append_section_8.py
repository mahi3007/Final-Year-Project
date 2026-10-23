import os

section_8 = """
---

## 8. Supplemental Addendum: Final Integrity Wording, Simulation Provenance & Warning Diagnostics Correction

This supplemental addendum directly addresses the five specific tasks mandated by the supervisor's technical review:

### 8.1 Task 1 — Rectification of Git-Integrity Terminology & Normalization Proof
The previous draft erroneously used the phrase "byte-for-byte match with Git HEAD" to describe working-tree files whose physical byte count exceeded the repository blob size due to CRLF line endings on Windows (`core.autocrlf = true`). 

To eliminate any ambiguity, every tracked baseline artifact was re-evaluated by comparing raw disk bytes, normalized disk bytes (stripping `\\r`), and raw Git commit blobs retrieved directly via `git show HEAD:<path>`:

```
Command executed:
python -c "
import subprocess, hashlib
git_blob = subprocess.check_output(['git', 'show', f'HEAD:{path}'])
norm_disk = open(path, 'rb').read().replace(b'\\r\\n', b'\\n')
assert norm_disk == git_blob
"
```

#### Complete Tracked Baseline Audit Table:
| Baseline Artifact Path | Raw Working-Tree Size | Raw Working-Tree SHA-256 | CRLF Count | Standalone CR (`\\r` without `\\n`) | Normalized Size (LF) | Normalized SHA-256 Digest | Git Commit Blob Size | Git Commit Blob SHA-256 | Git Object ID (SHA-1) | Final Parity Finding |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- | :---: | :--- | :--- | :--- |
| [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | $557,100\\text{ B}$ | `e964799b50a8...` | $6,906$ | $0$ | $550,194\\text{ B}$ | `96534400161e...` | $550,194\\text{ B}$ | `96534400161e...` | `e327b481eea1...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) | $451,539\\text{ B}$ | `41cec79d913a...` | $901$ | $0$ | $450,638\\text{ B}$ | `56cb4f9fc7ab...` | $450,638\\text{ B}$ | `56cb4f9fc7ab...` | `d3e20c88ac91...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) | $92,340\\text{ B}$ | `665009a00660...` | $301$ | $0$ | $92,039\\text{ B}$ | `612b7045e3e6...` | $92,039\\text{ B}$ | `612b7045e3e6...` | `e9eea418fa14...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) | $5,344\\text{ B}$ | `4622b215b18c...` | $77$ | $0$ | $5,267\\text{ B}$ | `63a189fdefdb...` | $5,267\\text{ B}$ | `63a189fdefdb...` | `f49bec277f9b...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) | $39,689\\text{ B}$ | `c2a746db83e0...` | $121$ | $0$ | $39,568\\text{ B}$ | `652e0fadc045...` | $39,568\\text{ B}$ | `652e0fadc045...` | `113685050722...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv) | $19,210\\text{ B}$ | `7c1659433b2b...` | $61$ | $0$ | $19,149\\text{ B}$ | `8a3a7b0fff1f...` | $19,149\\text{ B}$ | `8a3a7b0fff1f...` | `f858ba45a7a6...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |

#### Strict Epistemic Boundaries:
1. **Raw Byte Equality:** **False**. The physical working-tree files and Git commit blobs differ in raw byte size and SHA-256 digest because of CRLF translation.
2. **Normalized Text Equality:** **Established (True)**. In all 6 files, the difference between physical size and blob size matches the CRLF count exactly, standalone CR count is strictly zero, and normalized disk bytes equal Git blob bytes 100%.
3. **Clean Git Working-Tree Status:** **Established (True)**. Working tree status is completely clean; `git diff` produces zero modifications.
4. **Historical Non-Modification:** Established by Git commit lineage showing a single initial commit (`ac9657b` / `5c748af`) with zero intermediate modifications.

---

### 8.2 Task 2 — Untracked Simulation JSON Provenance Qualification
The canonical power simulation results file [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) was audited for provenance:
- **Physical Verification:** Exact byte size $253,229\\text{ bytes}$, SHA-256 `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Git Tracking Status:** The file is **untracked** in Git (`git status` reports untracked).
- **Git History Search:** `git log -S 8fac4d32` yields zero commits. `git grep 8fac4d32 HEAD` confirms no tracked file in historical Git commits contains this digest.
- **Working Tree Documentation:** The canonical digest `8fac4d32…` was first established and documented during Stage 6M v1.2.0 proposal drafting across [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), and [`stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Epistemic Classification:**
  1. **Current Digest Match:** **VERIFIED**. The physical disk file matches the canonical serialization record identically.
  2. **Historical Immutability via Git:** **UNVERIFIED**. Because the file is untracked in Git, Git commit history cannot independently establish that the file was never modified historically.
- **Protocol Governance Action:** The simulation JSON was **NOT regenerated, re-run, or modified**. Its historical-immutability claim is formally recorded as **UNVERIFIED via Git**, while its current physical integrity is preserved.

---

### 8.3 Task 3 — Forensic Warning and Diagnostics Classification
Inspection of [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) lines 124–154 reveals the exact provenance of all diagnostics:

1. **Counted Pytest Warnings (Category A — Exactly 6 Warnings in Pytest Summary):**
   - 4 deprecation warnings in `torchvision/transforms/_functional_pil.py:245, 291, 307, 324` (`BILINEAR/NEAREST/BICUBIC deprecated in Pillow 10`).
   - 2 deprecation warnings in `<frozen importlib._bootstrap>:241` (`builtin type SwigPyPacked / SwigPyObject has no __module__ attribute`).
2. **Process Stderr Diagnostics (Category B — Not Counted in Pytest 6 Warnings Summary):**
   - 1 `RequestsDependencyWarning` in `requests/__init__.py:113` (`urllib3 (1.26.12) or chardet (7.4.3)/charset_normalizer (2.1.1) doesn't match a supported version!`).
   - 1 interpreter startup `DeprecationWarning` in `sys:1` (`builtin type swigvarlink has no __module__ attribute`).
3. **Provenance Finding:** Zero warnings or stderr diagnostics originate from project test or pipeline code; all 8 diagnostics originate entirely from upstream site-packages.

---

### 8.4 Task 4 — Preservation of All Reconciled Findings
All previously reconciled substantive findings remain verified and preserved:
- **Irish Candidate & Exposure Arithmetic:**
  - Inventory Irish: $94$
  - Strict quality failures: $2$ (`f3ea0447…` and `fc22fd45…`)
  - Strictly eligible Irish pool: $94 - 2 = 92$
  - Replication Cohort 1 Irish ($E_1$): $10$ ($1$ failing strict quality, $9$ strictly eligible)
  - Sentinel Panel Irish ($E_S$): $5$ (all $5$ strictly eligible)
  - Disjointness: $|E_1 \cap E_S| = 0$
  - Strictly eligible exposed Irish: $9 + 5 = 14$
  - Unexposed strictly eligible Irish capacity:
    $$|I_{\\text{available}}| = 92 - 14 = \\mathbf{78}$$
    $$|I_{\\text{available}}| = 94 - (10 + 5 + 1) = \\mathbf{78}$$
- **Clip-Level Quality Progression:**
  - Speaker `f3ea0447…`: $16\\text{ raw rows} - 1\\text{ baseline exclusion (`'Cllr.'`)} = 15\\text{ baseline clips}$; $15 - 2\\text{ strict exclusions (`down_votes = 2`)} = 13\\text{ strict clips} < 15$. (Exclusion is baseline $+1$, strict $+2$; single-word clip excluded before baseline inventory).
  - Speaker `fc22fd45…`: $15\\text{ raw rows} - 0\\text{ baseline exclusions} = 15\\text{ baseline clips}$; $15 - 1\\text{ strict exclusion (`down_votes = 2`)} = 14\\text{ strict clips} < 15$.
- **Simulation Seed Formula & Power Qualification:**
  - Formula from `scripts/simulate_stage6m_power.py` line 340: $\\text{seed} = 42 + \\text{cohort\\_n} + \\text{sc\\_id} \\times 1000$ with 1-based $\\text{sc\\_id} \\in \\{1, 2, 3, 4\\}$.
  - Seeds: $N=420 \\to 1462 / 2462$; $N=450 \\to 1492 / 2492$; $N=468 \\to 1510 / 2510$; $N=540 \\to 1582 / 2582$.
  - Power difference qualification: Because simulations use cohort-dependent seeds, random streams are independent. The observed power difference ($85.83\\%$ at $N=468$ vs. $90.40\\%$ at $N=540$) reflects **both sample-size scaling and Monte Carlo realization variation** (not an exclusively isolated "pure sample-size effect").
- **Research-Validity Test Suite:** 113/113 passed tests confirm software contract invariants, but do not validate scientific hypotheses or multi-corpus design adequacy.

---

### 8.5 Task 5 — Preservation of All Governance Holds & Gate Status
All governance restrictions remain strictly enforced:
- `execution_authorized = false`
- Stage 6M Status: `HOLD — STRICTLY NOT AUTHORIZED`
- Confirmatory Execution Verdict: **STRICT NO-GO**
- Cohort 2: `PROPOSED — NOT YET CREATED OR VERIFIED`
- Final Sample Size: `UNFROZEN` ($N=468$ vs $N=540$ unresolved)
- Reserve Policy: `UNRESOLVED` (Policy A vs Policy B pending written supervisor approval)
- External Speech Corpus Acquisition: `BLOCKED` (shortfall of $102$ or $162$ speakers)
- Multi-Corpus Hierarchical Power Validation: `REQUIRED`
- Formal Confirmatory Authorization: `ABSENT`

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
FINAL GOVERNANCE DECISION: HOLD — STRICTLY NOT AUTHORIZED
execution_authorized: false
Confirmatory Execution Verdict: STRICT NO-GO
Software and accounting invariants are verified; scientific hypotheses and multi-corpus
power models remain unpreregistered, unapproved, and blocked from execution.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```
"""

audit_doc = "reports/stage6m/stage6m_residual_evidence_audit.md"
with open(audit_doc, "r", encoding="utf-8") as fp:
    content = fp.read()

if "## 8. Supplemental Addendum:" not in content:
    with open(audit_doc, "a", encoding="utf-8") as fp:
        fp.write(section_8)
    print("Section 8 appended successfully.")
else:
    print("Section 8 already present.")
