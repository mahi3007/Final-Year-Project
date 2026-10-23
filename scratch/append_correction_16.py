import os

correction_16_text = """

### Correction 16: Independent Technical Audit Reconciliation (Workstreams A–E)
- **Protocol Version:** `v1.2.0-stage6m-proposal`
- **Authoritative Test Pass:** `20 passed in 3.60s` in [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py)
- **Files Modified / Updated:** [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Workstreams Audited & Closed:**
  1. **Workstream A (Reaffirmation of Frozen Clip Eligibility Criteria):**
     - Formally reaffirmed authoritative baseline predicate $B_0(r)$ requiring stratum accent match, valid `client_id`, non-empty & globally unique audio path, reference word count $\\ge 2$, and homogeneous speaker accent ($15$ valid baseline clips required for inventory $I$).
     - Formally reaffirmed authoritative strict quality predicate $V(r)$ requiring $\\operatorname{locale}(r) = \\text{'en'}$, $\\operatorname{up\\_votes}(r) \\ge 2$, and $\\operatorname{down\\_votes}(r) < 2$ ($15$ valid strict clips required for strict candidate eligibility).
     - Explicitly rejected unapproved exploratory additions: (1) `down_votes == 0` is an unauthorized post-hoc tightening (the frozen protocol explicitly allows $0$ or $1$ down-vote); (2) audio duration ($1\\text{--}10\\text{ s}$) and SNR ($\\ge 12\\text{ dB}$) are acoustic characterization metrics absent from Mozilla Common Voice `validated.tsv` metadata. They are formally designated as **`[UNAPPROVED EXPLORATORY ACOUSTIC AUDIT]`** with zero authority over governing feasibility.
  2. **Workstream B (Exact Exposure-Set Reconciliation Using Frozen Splits):**
     - Reconciled exact speaker sets: Replication Cohort 1 ($E_1$) contains exactly $60$ unique speakers ($10$ per stratum across all $6$ strata, $900$ clips total); Sentinel Panel ($E_S$) contains exactly $30$ unique speakers ($5$ per stratum across all $6$ strata, $300$ clips total).
     - Verified disjointness: $|E_1 \\cap E_S| = 0$. Total prior exposed speakers across all strata: $|E_1 \\cup E_S| = 90$ ($15$ per stratum).
     - Evaluated intersection with quality exclusions ($|Q| = 61$ failing $C_{\\text{strict}} \\ge 15$): exactly $1$ exposed speaker (`f3ea04475e301f84785710b9…` in Irish $E_1$, $C_{\\text{strict}} = 13 < 15$) fails strict clip filtering. In the other five strata, $|Q \\cap (E_1 \\cup E_S)| = 0$.
     - Reconciled the reported figure **"89"**: represents the **strictly eligible exposed speakers** ($|(E_1 \\cup E_S) \\setminus Q| = 90 - 1 = 89$: $14$ Irish $+ 75$ non-Irish, $15$ in each of the other five groups).
     - Traced and disproved the erroneous phrase `"Cohort 1 (84)"`: $84$ was the unexposed Irish candidate pool count remaining after Cohort 1 extraction ($94 - 10 = 84$) in an early preliminary note, NOT the size of Cohort 1.
     - Established exact unexposed strictly eligible pool: $|I \\setminus (E_1 \\cup E_S \\cup Q)| = 6,844 - 89 = \\mathbf{6,755}$ speakers ($383$ Australian, $496$ Canadian, $1,198$ England, $78$ Irish, $731$ South Asian, $3,869$ US).
  3. **Workstream C (Rectification of Policy A and Policy B Reserve Allocations):**
     - Restored canonical Policy A definition (Irish-only reserve): Active: $450$ Common Voice ($75$/group) $+ 90$ External ($15$/group); Reserve: $3$ Common Voice (Irish only) $+ 12$ External (Irish only). Totals: $N_{\\text{CV}} = 450 + 3 = \\mathbf{453}$; $N_{\\text{external}} = 90 + 12 = \\mathbf{102}$; $N_{\\text{total}} = 453 + 102 = \\mathbf{555}$. Rectified the erroneous display of $462$ CV speakers. External shortfall: $\\mathbf{102}$ speakers.
     - Reaffirmed canonical Policy B definition (Stratum-balanced reserve across all $6$ groups): Active: $450$ Common Voice ($75$/group) $+ 90$ External ($15$/group); Reserve: $18$ Common Voice ($3$/group) $+ 72$ External ($12$/group). Totals: $N_{\\text{CV}} = 450 + 18 = \\mathbf{468}$; $N_{\\text{external}} = 90 + 72 = \\mathbf{162}$; $N_{\\text{total}} = 468 + 162 = \\mathbf{630}$. External shortfall: $\\mathbf{162}$ speakers.
     - Retained Policy A versus Policy B as formally **`[UNRESOLVED]`** pending supervisory preregistration.
  4. **Workstream D (Baseline Frozen Inventory vs. Exploratory TSV Parsing Comparison):**
     - Verified that [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) (SHA-256 `e964799b…`) is the authoritative, immutable frozen inventory: Australian ($400$), Canadian ($511$), England ($1,223$), Irish ($94$), South Asian ($764$), US ($3,913$) totaling $6,905$.
     - Reconciled exploratory raw TSV re-scans ($517$ Canadian, $753$ South Asian, $3,918$ US): confirmed aggregate conservation $(+6) + (-11) + (+5) = 0$ ($6,905$ total). Documented root cause as dialect string parsing variation on unnormalized raw metadata. Designated re-scans as **`[UNAPPROVED EXPLORATORY RECLASSIFICATION]`** with zero authority to alter frozen files.
  5. **Workstream E (Verification of Canonical Scenario 2 Parameters Across Sample Sizes):**
     - Verified canonical simulation file [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json): both `cohort_468` ($85.825\\%$) and `cohort_540` ($90.40\\%$) use **IDENTICAL** DGP parameters: $\\Delta_R = -0.85\\text{ pp}$, $\\Delta D = +0.50\\text{ pp}$, $S = 4,000$, $B = 1,000$.
     - Corrected isolated changelog typographical error in line 393 that read $+0.80\\text{ pp}$ instead of $+0.50\\text{ pp}$. Confirmed that the power difference between $N=468$ ($85.825\\%$) and $N=540$ ($90.40\\%$) is a genuine, pure sample-size effect under identical DGP conditions.
  6. **Unit Test Suite Expansion:**
     - Implemented three new regression tests in [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py):
       * `test_stage6m_six_group_prior_exposure_reconciliation`: validates $E_1=60, E_S=30, E_1 \\cap E_S = \\emptyset, \\text{strictly eligible exposed} = 89$.
       * `test_stage6m_reserve_policy_allocations`: validates Policy A ($453 + 102 = 555$) and Policy B ($468 + 162 = 630$) totals and shortfalls.
       * `test_stage6m_scenario2_canonical_parameters`: validates $\\Delta D = +0.50\\text{ pp}$ identity across $N=468$ and $N=540$.
     - Full module test suite: **20 passed in 3.60s**.
  7. **Governance Invariants:** Retained execution lock: `execution_authorized = false`, `STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED`, `Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`, `Final sample size = UNFROZEN`. Confirmatory execution decision: **STRICT NO-GO**.
"""

changelog_path = r"reports\stage6m\stage6m_v1_2_0_changelog.md"
with open(changelog_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix any corrupted dashes in line 402 if present
content = content.replace("STAGE 6M STATUS = HOLD  STRICTLY NOT AUTHORIZED", "STAGE 6M STATUS = HOLD — STRICTLY NOT AUTHORIZED")
content = content.replace("Cohort 2 = PROPOSED  NOT YET CREATED OR VERIFIED", "Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED")

if "### Correction 16: Independent Technical Audit Reconciliation" not in content:
    content = content.rstrip() + "\n" + correction_16_text

with open(changelog_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated changelog successfully.")
