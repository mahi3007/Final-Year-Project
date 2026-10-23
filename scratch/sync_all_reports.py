from pathlib import Path

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")
S6_DIR = PROJECT_ROOT / "reports" / "stage6m"

# 1. Update stage6m_v1_2_0_changelog.md
chg_path = S6_DIR / "stage6m_v1_2_0_changelog.md"
chg_text = chg_path.read_text(encoding="utf-8")

correction_14 = """

### Correction 14: Final Eligibility Reconciliation and Residual Audit Closure (Workstreams A–E)
- **Authoritative Hash:** `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Files Modified:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`scripts/update_stage6m_reports.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/update_stage6m_reports.py), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Workstreams Audited & Reconciled:**
  1. **Workstream A (Six-Group Strict Eligibility Reconciliation):** Recomputed $C_{\\text{inventory}}(s)$ and $C_{\\text{strict}}(s)$ for all $6,905$ inventory speakers across all six accent strata directly from `datasets/external/common_voice_27/validated.tsv`. Identified exactly $61$ speakers failing strict clip count ($C_{\\text{strict}} < 15$): $2$ Australian, $0$ Canadian, $10$ England, $2$ Irish, $18$ South Asian, $29$ US. Reconciled net available strictly eligible unexposed speakers: Australian $383$ (was $385$, $\\Delta = -2$), Canadian $496$ (was $496$, $\\Delta = 0$), England $1,198$ (was $1,208$, $\\Delta = -10$), Irish $78$ (was $78$, $\\Delta = 0$), South Asian $731$ (was $749$, $\\Delta = -18$), US $3,869$ (was $3,898$, $\\Delta = -29$); Total $6,755$ (was $6,814$, $\\Delta = -59$). Confirmed feasibility of active sample ($75$ CV/stratum) and Policy A reserve ($78$ Irish, $75$ non-Irish). Documented that Policy B reserve ($93$ CV/stratum) is strictly infeasible due to the Irish bottleneck ($78 < 93$, shortfall of $15$ speakers).
  2. **Workstream B (Resolve Irish "73 raw" Annotation):** Traced the exact origin of the number $73$ in the Irish row: in an early uncommitted draft, after excluding $10$ Cohort 1 replication speakers ($94 - 10 = 84$) and $1$ unexposed strict clip filter failure ($84 - 1 = 83$), an author mistakenly subtracted the $10$ replication speakers a *second time* ($83 - 10 = 73$). Reconciled with $|I| = 94$, $|I_{\\text{excluded}}| = 16$, $|I_{\\text{available}}| = 78$. Removed the misleading label "73 raw" from active summary tables, and documented the resolution permanently in Section 3.1b.
  3. **Workstream C (Mathematical Clip-Count Definitions):** Separated Boolean eligibility predicates from numeric indicator summations: defined baseline predicate $B_0(r)$, vote/locale predicate $V(r)$, indicator sums $C_{\\text{inventory}}(s) = \\sum_{r \\in \\mathcal{R}_s} \\mathbf{1}[B_0(r)]$ and $C_{\\text{strict}}(s) = \\sum_{r \\in \\mathcal{R}_s} \\mathbf{1}[B_0(r) \\land V(r)]$, strict condition $C_{\\text{strict}}(s) \\ge 15$, and quality exclusion set $Q = \\{s \\in I \\mid C_{\\text{strict}}(s) < 15\\}$. Documented global duplicate path handling and reconciled individual records for `fc22fd45...` ($C_{\\text{inv}}=15, C_{\\text{strict}}=14$) and `f3ea0447...` ($C_{\\text{inv}}=15, C_{\\text{strict}}=13$).
  4. **Workstream D (Corpus-Effect Claim and Source-Path Resolution):** Qualified the allocation imbalance claim: "Differences in corpus composition across accent groups can leave group-specific residual shifts when corpus effects differ, potentially affecting disparity estimates and their uncertainty. The magnitude and direction of that effect depend on the allocation, corpus effects, and covariance structure." Inspected Common Voice metadata resolution logic in `scripts/phase3_external_eval_curation.py`: distinguished canonical path (`datasets/external/common_voice_27/validated.tsv`) from configured fallback paths (`datasets/external/common_voice_27_intermediate/validated.tsv`, `datasets/external/common_voice_11/validated.tsv`, HuggingFace streaming), confirming that canonical path was selected and fallback was not executed. Scoped Git history search (`git log --all --full-history -S...` $\\to$ 0 commits).
  5. **Workstream E (Rendered Report Verification & LaTeX Escaping):** Escaped LaTeX set braces (`\\{` and `\\}`), verified mathematical subscript formatting ($R^{(k)}_{m,g}$), ensured all markdown tables have 100% consistent column counts using `\\lvert` and `\\rvert` for table cell norms, and eliminated Python string escape sequence corruption (`\\t`, `\\n`, `\\r`).
  6. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.
"""

if "### Correction 14: Final Eligibility Reconciliation and Residual Audit Closure (Workstreams A–E)" not in chg_text:
    chg_text = chg_text.strip() + "\n" + correction_14
    chg_path.write_text(chg_text, encoding="utf-8")
    print("Updated stage6m_v1_2_0_changelog.md with Correction 14.")
else:
    print("Correction 14 already present in changelog.")

# 2. Update update_stage6m_reports.py
upd_script_path = PROJECT_ROOT / "scripts" / "update_stage6m_reports.py"
upd_text = upd_script_path.read_text(encoding="utf-8")

# Make update_data_feasibility_audit() invoke generate_feasibility_report logic cleanly
feas_src = (PROJECT_ROOT / "scratch" / "generate_feasibility_report.py").read_text(encoding="utf-8")

idx1 = upd_text.find("def update_data_feasibility_audit():")
idx2 = upd_text.find("def update_protocol_proposal():")

if idx1 != -1 and idx2 != -1:
    new_func = """def update_data_feasibility_audit():
    p = S6_DIR / "stage6m_data_feasibility_audit.md"
    from scratch.generate_feasibility_report import content
    p.write_text(content, encoding="utf-8")
    print("Updated stage6m_data_feasibility_audit.md successfully.")


"""
    upd_text = upd_text[:idx1] + new_func + upd_text[idx2:]
    upd_script_path.write_text(upd_text, encoding="utf-8")
    print("Updated scripts/update_stage6m_reports.py successfully.")
