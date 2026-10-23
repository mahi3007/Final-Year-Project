import os

doc_path = "reports/stage6m/stage6m_residual_evidence_audit.md"
with open(doc_path, "r", encoding="utf-8") as fp:
    content = fp.read()

# 1. Correction 1: Fix Seed Formula Notation
# In line 19 / Executive Summary
content = content.replace(
    "(\\text{seed} = 42 + N + 1000\\,\\text{sc\\_id} with $1$-based \\text{sc\\_id} \\in \\{1,2,3,4\\})",
    "($\\\\text{seed} = 42 + N + 1000 \\\\cdot \\\\text{sc\\\\_id}$ with $1$-based $\\\\text{sc\\\\_id} \\\\in \\\\{1, 2, 3, 4\\\\}$)"
)
content = content.replace(
    "($\\text{seed} = 42 + N + 1000\\,\\text{sc\\_id}$ with $1$-based $\\text{sc\\_id} \\in \\{1,2,3,4\\}$)",
    "($\\\\text{seed} = 42 + N + 1000 \\\\cdot \\\\text{sc\\\\_id}$ with $1$-based $\\\\text{sc\\\\_id} \\\\in \\\\{1, 2, 3, 4\\\\}$)"
)
content = content.replace(
    "$$\\text{seed} = \\text{seed\\_discovery} + \\text{cohort\\_n} + \\text{sc\\_id} \\times 1000 = 42 + \\text{cohort\\_n} + \\text{sc\\_id} \\times 1000$$",
    "$$\\\\text{seed} = \\\\text{seed\\\\_discovery} + \\\\text{cohort\\\\_n} + 1000 \\\\cdot \\\\text{sc\\\\_id} = 42 + N + 1000 \\\\cdot \\\\text{sc\\\\_id}$$"
)
content = content.replace(
    "$$\\text{seed} = 1000 \\times \\text{scenario\\_idx} + 1042 + \\text{cohort\\_size}$$",
    "$$\\\\text{seed} = 1000 \\\\cdot \\\\text{scenario\\\\_idx} + 1042 + N$$"
)
content = content.replace(
    "- Formula from `scripts/simulate_stage6m_power.py` line 340: $\\text{seed} = 42 + \\text{cohort\\_n} + \\text{sc\\_id} \\times 1000$ with 1-based $\\text{sc\\_id} \\in \\{1, 2, 3, 4\\}$.",
    "- Formula from `scripts/simulate_stage6m_power.py` line 340: $\\\\text{seed} = 42 + N + 1000 \\\\cdot \\\\text{sc\\\\_id}$ with 1-based $\\\\text{sc\\\\_id} \\\\in \\\\{1, 2, 3, 4\\\\}$."
)

# 2. Correction 2: Distinguish Baseline-Path Working-Tree Status from Global Working Tree Status
old_status_text_1 = "3. **Clean Git Working-Tree Status:** **Established (True)**. `git status -uno` confirms no modifications to tracked files; `git diff` shows zero content changes."
new_status_text_1 = "3. **Audited Baseline Working-Tree Status:** The six audited baseline paths have no reported working-tree modifications. The repository's overall working-tree status is a separate matter and may include changes to audit reports, the changelog, and newly created evidence files."
content = content.replace(old_status_text_1, new_status_text_1)

old_status_text_2 = "3. **Clean Git Working-Tree Status:** **Established (True)**. Working tree status is completely clean; `git diff` produces zero modifications."
new_status_text_2 = "3. **Audited Baseline Working-Tree Status:** The six audited baseline paths have no reported working-tree modifications. The repository's overall working-tree status is a separate matter and may include changes to audit reports, the changelog, and newly created evidence files."
content = content.replace(old_status_text_2, new_status_text_2)

# 3. Correction 3: Refine Warning Attribution
old_warn_1 = "**Summary of Provenance:** Zero warnings or stderr diagnostics originate from project test or pipeline code; all 8 messages (6 pytest warnings + 2 stderr diagnostics) originate from upstream site-packages."
new_warn_1 = "**Summary of Provenance:** All eight messages are attributed to third-party dependencies or runtime diagnostics. No project-code origin was identified in the inspected log."
content = content.replace(old_warn_1, new_warn_1)

old_warn_2 = "3. **Provenance Finding:** Zero warnings or stderr diagnostics originate from project test or pipeline code; all 8 diagnostics originate entirely from upstream site-packages."
new_warn_2 = "3. **Provenance Finding:** All eight messages are attributed to third-party dependencies or runtime diagnostics. No project-code origin was identified in the inspected log."
content = content.replace(old_warn_2, new_warn_2)

with open(doc_path, "w", encoding="utf-8") as fp:
    fp.write(content)

print("Applied 3 documentation corrections to stage6m_residual_evidence_audit.md successfully.")
