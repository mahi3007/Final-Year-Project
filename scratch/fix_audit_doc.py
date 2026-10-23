from pathlib import Path

p = Path("reports/stage6m/stage6m_data_feasibility_audit.md")
content = p.read_text(encoding="utf-8")

# Correct the formula in subsection 6
bad_sec = r"""#### 6. Formal Protocol Reaffirmation & Rejection of Unauthorized Predicates (Workstream A):
To resolve any ambiguity introduced in recent draft discussions, the project formally reaffirms the authoritative criteria established in ADR-005, CV 27 protocol amendment (`protocol_amendment_cv27.md`), and `phase3_external_eval_curation.py`:

1. **Authoritative Baseline Predicate $B_0(r)$:**
   $$B_0(r) \iff \left[ \operatorname{accent}(r) = 	ext{Stratum} ight] \land \left[ \operatorname{client\_id}(r) 
\ne \emptyset ight] \land \left[ \operatorname{path}(r) 	ext{ non-empty \& globally unique} ight] \land \left[ \operatorname{words}(\operatorname{sentence}(r)) \ge 2 ight] \land \left[ \operatorname{homogeneous\_accent}(s) = 1 ight]$$
   - Baseline candidate inventory qualification requires $C_{	ext{inventory}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r)] \ge 15$.
   - This criterion defines the frozen candidate pool $|I| = 6,905$ ($94$ Irish).
2. **Authoritative Strict Quality Predicate $V(r)$:**
   $$V(r) \iff \left[ \operatorname{locale}(r) = 	ext{'en'} ight] \land \left[ \operatorname{up\_votes}(r) \ge 2 ight] \land \left[ \operatorname{down\_votes}(r) < 2 ight]$$
   - Strict clip count is $C_{	ext{strict}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r) \land V(r)]$.
   - Strict speaker eligibility requires $C_{	ext{strict}}(s) \ge 15$.
3. **Rejection of Unauthorized Predicate Alterations:**
   - **Rejection of `down_votes == 0`:** Requiring zero down-votes is an unauthorized, post-hoc narrowing of the frozen protocol rule `down_votes < 2` (which explicitly permits clips with $0$ or $1$ down-vote).
   - **Rejection of Audio Duration (1–10s) and SNR ($\ge 12	ext{ dB}$) in Metadata Filtering:** Mozilla Common Voice `validated.tsv` does not record acoustic Signal-to-Noise Ratio (SNR) or duration. Audio duration and SNR thresholds belong strictly to offline acoustic characterization of audio waveforms (e.g. Stage 4 L2-ARCTIC acoustics in `data_scale_feasibility.md`). Introducing them into metadata curation is technically impossible on TSV alone and constitutes an unapproved protocol change. They are formally designated as **`[UNAPPROVED EXPLORATORY ACOUSTIC AUDIT]`** and have zero authority over governing sample feasibility.
4. **Conclusion:** All governing sample allocations, stratum capacities, and exposure accounting remain strictly governed by the canonical predicates $B_0(r)$ and $V(r)$."""

good_sec = r"""#### 6. Formal Protocol Reaffirmation & Rejection of Unauthorized Predicates (Workstream A):
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
4. **Conclusion:** All governing sample allocations, stratum capacities, and exposure accounting remain strictly governed by the canonical predicates $B_0(r)$ and $V(r)$."""

if bad_sec in content:
    content = content.replace(bad_sec, good_sec)
    print("Cleaned up LaTeX in Section 3.1 subsection 6.")
else:
    print("bad_sec not matched directly, doing regex replace...")
    # Find the subsection and replace
    start_tag = "#### 6. Formal Protocol Reaffirmation & Rejection of Unauthorized Predicates (Workstream A):"
    end_tag = "4. **Conclusion:** All governing sample allocations, stratum capacities, and exposure accounting remain strictly governed by the canonical predicates $B_0(r)$ and $V(r)$."
    idx_start = content.find(start_tag)
    idx_end = content.find(end_tag)
    if idx_start != -1 and idx_end != -1:
        content = content[:idx_start] + good_sec + content[idx_end + len(end_tag):]
        print("Replaced subsection 6 using indices.")

# Also update Section 2.1 finding 2 cleanly
old_finding_start = "2. **Prior Exposure Overlap with Quality Exclusions:**"
old_finding_end = "satisfy strict eligibility ($C_{\\text{strict}} \\ge 15$)."

new_finding_2 = r"""2. **Prior Exposure Overlap with Quality Exclusions & Mathematical Reconciliation of the "89" Figure:**
   Across all six accent strata, the frozen evaluation splits contribute exactly **$90$ unique previously exposed speakers**:
   - Replication Cohort 1 ($E_1$): Exactly $60$ unique speakers ($10$ speakers per stratum across all $6$ strata, $900$ clips total).
   - Sentinel Panel ($E_S$): Exactly $30$ unique speakers ($5$ speakers per stratum across all $6$ strata, $300$ clips total).
   - Strict Disjointness: $|E_1 \cap E_S| = 0$.
   - Inventory Inclusion: All $90$ exposed speakers belong to candidate inventory $I$ ($|(E_1 \cup E_S) \cap I| = 90$).
   - Overlap with Strict Quality Failures: Exactly **$1$ exposed speaker** (`f3ea04475e301f84785710b9…` in Irish Cohort 1) failed the strict clip-count threshold ($C_{\text{strict}} = 13 < 15$, failing strict clip count due to $2$ clips with `down_votes = 2` and $1$ single-word clip). All $89$ other exposed speakers ($14$ Irish + $75$ non-Irish: $15$ Australian, $15$ Canadian, $15$ England, $15$ South Asian, $15$ US) satisfy strict eligibility ($C_{\text{strict}} \ge 15$).
   - **Origin and Meaning of the Reported Figure "89":** The number $89$ represents the **strictly eligible previously exposed speakers** ($|(E_1 \cup E_S) \setminus Q| = 90 - 1 = 89$). It is NOT "Cohort 1 (84) + Sentinel Panel (5)". Cohort 1 contains exactly $60$ speakers (not $84$). The number $84$ was an exploratory intermediate count representing unexposed Irish candidates remaining after Cohort 1 selection ($94 - 10 = 84$), which was conflated in an earlier uncommitted draft. The true exposure exclusions are strictly $60$ in $E_1$ ($59$ strictly eligible $+ 1$ failing strict) and $30$ in $E_S$ ($30$ strictly eligible), totaling $90$ exposed speakers ($89$ strictly eligible $+ 1$ failing strict)."""

idx_f_start = content.find(old_finding_start)
if idx_f_start != -1:
    idx_f_end = content.find(old_finding_end, idx_f_start)
    if idx_f_end != -1:
        content = content[:idx_f_start] + new_finding_2 + content[idx_f_end + len(old_finding_end):]
        print("Updated Finding 2 in Section 2.1.")

# Update Section 3.1b for 84 provenance
sec31b_start = "### 3.1b Provenance Reconciliation of the Historical \"73 raw\" Irish Annotation (Workstream B)"
idx_31b = content.find(sec31b_start)
if idx_31b != -1:
    end_31b = content.find("### 3.2 Evaluation of Planning Target Capacities:", idx_31b)
    if end_31b != -1:
        new_31b_full = r"""### 3.1b Provenance Reconciliation of the Historical "73 raw" and "84" Irish Annotations (Workstream B)

Earlier draft versions of the protocol proposal and feasibility reports included parenthetical annotations in the Irish capacity row: `"(78 available; 73 raw)"` and descriptions of exposure sets as `"Replication Cohort 1 (84)"`. An exhaustive forensic trace of project calculations identified the precise mathematical origin of both figures:

1. **Origin in Exploratory Draft Accounting (Reconciliation of the "84" and "73 raw" Figures):**
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
   - $73$ was an arithmetic artifact of subtracting the $10$ replication speakers twice ($83 - 10 = 73$).
3. **Formal Resolution:**
   - The verified candidate capacity is strictly $|I_{\text{available}}| = \mathbf{78}$ untouched, unexposed strictly eligible speakers.
   - The misleading label `"73 raw"` and ambiguous phrase `"Cohort 1 (84)"` have been removed from all active summary tables and report templates.
   - This record documents the discrepancy and permanently resolves the historical question without modifying frozen archival records.

---

"""
        content = content[:idx_31b] + new_31b_full + content[end_31b:]
        print("Updated Section 3.1b completely.")

p.write_text(content, encoding="utf-8")
print("Saved stage6m_data_feasibility_audit.md successfully.")
