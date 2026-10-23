from pathlib import Path
import re

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")
audit_file = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_data_feasibility_audit.md"

content = audit_file.read_text(encoding="utf-8")

# 1. Update Key Empirical Audit Findings in Section 2.1 to clarify the 89 vs 90 exposed speakers and dispell the 84 artifact
old_finding_2 = """2. **Prior Exposure Overlap with Quality Exclusions:**
   Across all $90$ previously exposed speakers ($15$/stratum: $10$ in Cohort 1 $E_1$, $5$ in Sentinel Panel $E_S$), exactly **$1$ speaker** (`f3ea04475e301f84785710b9…` in Irish Cohort 1) failed the strict clip-count threshold ($C_{\text{strict}} = 13 < 15$). All other $89$ exposed speakers ($14$ Irish + $75$ non-Irish) satisfy strict eligibility ($C_{\text{strict}} \ge 15$)."""

new_finding_2 = """2. **Prior Exposure Overlap with Quality Exclusions & Mathematical Reconciliation of the "89" Figure:**
   Across all six accent strata, the frozen evaluation splits contribute exactly **$90$ unique previously exposed speakers**:
   - Replication Cohort 1 ($E_1$): Exactly $60$ unique speakers ($10$ speakers per stratum across all $6$ strata, $900$ clips total).
   - Sentinel Panel ($E_S$): Exactly $30$ unique speakers ($5$ speakers per stratum across all $6$ strata, $300$ clips total).
   - Strict Disjointness: $|E_1 \cap E_S| = 0$.
   - Inventory Inclusion: All $90$ exposed speakers belong to candidate inventory $I$ ($|(E_1 \cup E_S) \cap I| = 90$).
   - Overlap with Strict Quality Failures: Exactly **$1$ exposed speaker** (`f3ea04475e301f84785710b9…` in Irish Cohort 1) failed the strict clip-count threshold ($C_{\text{strict}} = 13 < 15$, failing strict clip count due to $2$ clips with `down_votes = 2` and $1$ single-word clip). All $89$ other exposed speakers ($14$ Irish + $75$ non-Irish: $15$ Australian, $15$ Canadian, $15$ England, $15$ South Asian, $15$ US) satisfy strict eligibility ($C_{\text{strict}} \ge 15$).
   - **Origin and Meaning of the Reported Figure "89":** The number $89$ represents the **strictly eligible previously exposed speakers** ($|(E_1 \cup E_S) \setminus Q| = 90 - 1 = 89$). It is NOT "Cohort 1 (84) + Sentinel Panel (5)". Cohort 1 contains exactly $60$ speakers (not $84$). The number $84$ was an exploratory intermediate count representing unexposed Irish candidates remaining after Cohort 1 selection ($94 - 10 = 84$), which was conflated in an earlier uncommitted draft. The true exposure exclusions are strictly $60$ in $E_1$ ($59$ strictly eligible $+ 1$ failing strict) and $30$ in $E_S$ ($30$ strictly eligible), totaling $90$ exposed speakers ($89$ strictly eligible $+ 1$ failing strict)."""

if old_finding_2 in content:
    content = content.replace(old_finding_2, new_finding_2)
    print("Updated Finding 2 in Section 2.1.")
else:
    print("Finding 2 not matched exactly; searching...")

# 2. Add Section 2.4: Baseline Frozen Inventory vs. Exploratory TSV Parsing Comparison
sec24_text = """

### 2.4 Baseline Frozen Inventory vs. Exploratory TSV Parsing Comparison (Workstream D)

To ensure absolute transparency regarding candidate inventory counts, the table below compares the governing baseline inventory in [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) against exploratory raw TSV re-scans:

| Accent Stratum Name | Stratum Code | Frozen Baseline Candidate Inventory (`external_speaker_inventory.csv`) | Exploratory Raw TSV Parsing Count | Discrepancy ($\Delta$) | Root Cause & Methodological Resolution |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Australian English** | `australia` | $400$ | $400$ | $0$ | Exact 1:1 match across both methods. |
| **Canadian English** | `canada` | $511$ | $517$ | $+6$ | Variation due to dialect string normalization of multi-region entries in raw TSV. |
| **England English** | `england` | $1,223$ | $1,223$ | $0$ | Exact 1:1 match across both methods. |
| **Irish English** | `ireland` | $94$ | $94$ | $0$ | Exact 1:1 match across both methods. Bottleneck capacity strictly preserved. |
| **South Asian English** | `south_asian` | $764$ | $753$ | $-11$ | Variation due to multi-subregion parentheses parsing (`India, Pakistan, Sri Lanka`). |
| **US English** | `us` | $3,913$ | $3,918$ | $+5$ | Variation due to generic North American entries in raw TSV text. |
| **Total All 6 Strata** | **All 6** | **$6,905$** | **$6,905$** | **$0$** | **Exact aggregate conservation: $(+6) + (-11) + (+5) = 0$.** |

#### Epistemic Ruling on Inventory Group Counts:
1. **Governing Standard:** The frozen candidate inventory [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) (SHA-256 `e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a`), established during Stage 5 curation with exact counts of **$400, 511, 1223, 94, 764, 3913$**, is the authoritative, immutable baseline inventory.
2. **Exploratory Status of Re-Scans:** The alternative counts ($517, 753, 3918$) represent an unapproved exploratory re-grouping arising from dialect string variation in raw `validated.tsv`. They are formally designated as **`[UNAPPROVED EXPLORATORY RECLASSIFICATION]`**.
3. **Immutability of Frozen Assets:** In accordance with research integrity governance, frozen inventory files are NOT modified. All governing feasibility analyses, sample-size calculations, and exposure set-theoretic intersections are derived strictly from the canonical $6,905$-speaker baseline inventory.
"""

target_sec2_end = "### 2.3 Cryptographic Artifact Provenance Hashes"
if "### 2.4 Baseline Frozen Inventory vs. Exploratory TSV Parsing Comparison" not in content:
    # Insert before Section 3
    idx_sec3 = content.find("## 3. Bottleneck Analysis & Multi-Corpus Feasibility")
    assert idx_sec3 != -1, "Section 3 not found"
    content = content[:idx_sec3] + sec24_text + "\n---\n\n" + content[idx_sec3:]
    print("Inserted Section 2.4.")

# 3. Add subsection 6 in Section 3.1: Reaffirmation of Frozen Criteria & Rejection of Unauthorized Predicates
sec31_reaffirm = """

#### 6. Formal Protocol Reaffirmation & Rejection of Unauthorized Predicates (Workstream A):
To resolve any ambiguity introduced in recent draft discussions, the project formally reaffirms the authoritative criteria established in ADR-005, CV 27 protocol amendment (`protocol_amendment_cv27.md`), and `phase3_external_eval_curation.py`:

1. **Authoritative Baseline Predicate $B_0(r)$:**
   $$B_0(r) \iff \left[ \operatorname{accent}(r) = \text{Stratum} \right] \land \left[ \operatorname{client\_id}(r) \ne \emptyset \right] \land \left[ \operatorname{path}(r) \text{ non-empty \& globally unique} \right] \land \left[ \operatorname{words}(\operatorname{sentence}(r)) \ge 2 \right] \land \left[ \operatorname{homogeneous\_accent}(s) = 1 \right]$$
   - Baseline candidate inventory qualification requires $C_{\text{inventory}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r)] \ge 15$.
   - This criterion defines the frozen candidate pool $|I| = 6,905$ ($94$ Irish).
2. **Authoritative Strict Quality Predicate $V(r)$:**
   $$V(r) \iff \left[ \operatorname{locale}(r) = \text{'en'} \right] \land \left[ \operatorname{up\_votes}(r) \ge 2 \right] \land \left[ \operatorname{down\_votes}(r) < 2 \right]$$
   - Strict clip count is $C_{\text{strict}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r) \land V(r)]$.
   - Strict speaker eligibility requires $C_{\text{strict}}(s) \ge 15$.
3. **Rejection of Unauthorized Predicate Alterations:**
   - **Rejection of `down_votes == 0`:** Requiring zero down-votes is an unauthorized, post-hoc narrowing of the frozen protocol rule `down_votes < 2` (which explicitly permits clips with $0$ or $1$ down-vote).
   - **Rejection of Audio Duration (1–10s) and SNR ($\ge 12\text{ dB}$) in Metadata Filtering:** Mozilla Common Voice `validated.tsv` does not record acoustic Signal-to-Noise Ratio (SNR) or duration. Audio duration and SNR thresholds belong strictly to offline acoustic characterization of audio waveforms (e.g. Stage 4 L2-ARCTIC acoustics in `data_scale_feasibility.md`). Introducing them into metadata curation is technically impossible on TSV alone and constitutes an unapproved protocol change. They are formally designated as **`[UNAPPROVED EXPLORATORY ACOUSTIC AUDIT]`** and have zero authority over governing sample feasibility.
4. **Conclusion:** All governing sample allocations, stratum capacities, and exposure accounting remain strictly governed by the canonical predicates $B_0(r)$ and $V(r)$.
"""

target_sec31_end = "The subtraction $94 - 16 = \\mathbf{78}$ rigorously deduplicates the quality exclusion overlapping Cohort 1 (`f3ea0447...`), avoiding double-counting."
if "#### 6. Formal Protocol Reaffirmation & Rejection of Unauthorized Predicates" not in content:
    idx_sub = content.find(target_sec31_end)
    assert idx_sub != -1, "Target in Section 3.1 not found"
    end_of_target = idx_sub + len(target_sec31_end)
    content = content[:end_of_target] + sec31_reaffirm + content[end_of_target:]
    print("Inserted Section 3.1 subsection 6.")

# 4. Enhance Section 3.1b to explicitly address the "84" artifact
old_31b = """1. **Origin in Exploratory Draft Accounting:**
   In early working drafts preceding the formalization of inventory-restricted set equations:
   - Total baseline Irish inventory: $|I| = 94$.
   - Prior exposure to Replication Cohort 1: $|E_1| = 10$.
   - Pre-filtered pool before sentinel panel construction: $94 - 10 = 84$.
   - Exclusion of unexposed strict filter failure `fc22fd45...` ($C_{\text{strict}} = 14 < 15$): $84 - 1 = 83$ candidates in [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) (`pool_size: 83`).
   - The Sentinel Panel drew $5$ unexposed speakers ($|E_S| = 5$), leaving $83 - 5 = 78$ untouched, strictly eligible speakers.
   - **The Error:** An exploratory uncommitted draft inadvertently subtracted the $10$ replication speakers a *second time* from the post-filtered pool:
     $$83 - 10 = \mathbf{73}$$
2. **Epistemic Classification:**
   The number $73$ was neither a clip count nor an alternative stage of curation; it was an arithmetic artifact of subtracting the $10$ replication speakers twice in an exploratory draft."""

new_31b = """1. **Origin in Exploratory Draft Accounting (Reconciliation of the "84" and "73 raw" Figures):**
   In early working drafts preceding the formalization of inventory-restricted set equations:
   - Total baseline Irish inventory: $|I| = 94$.
   - Prior exposure to Replication Cohort 1: exactly $|E_1 \cap I_{\text{Irish}}| = 10$ speakers ($900$ clips total across $60$ Cohort 1 speakers, $10$ per stratum).
   - **The Origin of the Number 84:** After selecting the $10$ Cohort 1 Irish speakers, exactly $94 - 10 = \mathbf{84}$ candidate Irish speakers remained in the pre-filtered inventory before sentinel panel curation. In an early working draft, this remaining pool count was misattributed as the size of Cohort 1 itself ("Cohort 1 (84)"). Cohort 1 has never contained $84$ speakers; its frozen manifest contains exactly $60$ speakers ($10$ per stratum).
   - Exclusion of unexposed strict filter failure `fc22fd45...` ($C_{\text{strict}} = 14 < 15$): $84 - 1 = 83$ candidate speakers in [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) (`pool_size: 83`).
   - The Sentinel Panel drew $5$ unexposed speakers ($|E_S| = 5$), leaving $83 - 5 = \mathbf{78}$ untouched, strictly eligible speakers.
   - **The Origin of the Number 73:** An exploratory uncommitted draft inadvertently subtracted the $10$ replication speakers a *second time* from the post-filtered pool:
     $$83 - 10 = \mathbf{73}$$
2. **Epistemic Classification:**
   Neither $84$ nor $73$ represents an alternative candidate pool or differing protocol rule:
   - $84$ was the intermediate count of unexposed Irish candidates before Sentinel extraction ($94 - 10 = 84$).
   - $73$ was an arithmetic artifact of subtracting the $10$ replication speakers twice ($83 - 10 = 73$)."""

if old_31b in content:
    content = content.replace(old_31b, new_31b)
    print("Updated Section 3.1b for 84 and 73 provenance.")
else:
    print("Section 3.1b text not matched exactly.")

audit_file.write_text(content, encoding="utf-8")
print("Saved updated stage6m_data_feasibility_audit.md.")
