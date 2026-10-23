content = """# Stage 6M Confirmatory Data Feasibility & Speaker Capacity Audit

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md)  
**Governance Status:** `HOLD — STRICTLY NOT AUTHORIZED` (`execution_authorized = false`)  
**Target Architecture:** **Two-Cohort Protocol Architecture (Option A Expansion)**  
**Planning Targets Audited:** $N = 180$ speakers ($30$/group) and $N = 240$ speakers ($40$/group)  
**Candidate Evaluation Corpus:** Mozilla Common Voice Scripted Speech 27.0 English (`cv-corpus-27.0-2026-09-11`)

---

## 1. Executive Summary & Feasibility Verdict

| Feasibility Dimension | Audit Finding | Methodological Verification | Epistemic Status |
| :--- | :---: | :--- | :--- |
| **Candidate Corpus** | Mozilla Common Voice 27.0 | Official release (`cv-corpus-27.0-2026-09-11`, MDC ID `cmu5jplf300nwmh07iqvk9leo`) | `VERIFIED FROM ARTIFACT` |
| **License & Permitted Research** | CC0 1.0 Universal | Full public domain commercial/research use permitted | `VERIFIED FROM ARTIFACT` |
| **Prespecified Groups ($G=6$)** | Exactly 6 demographic strata | US, England, South Asian, Canadian, Australian, Irish | `VERIFIED FROM ARTIFACT` |
| **Total Baseline Inventory ($C_{\text{inventory}} \ge 15$)** | $6,905$ speakers | Verified in [`external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | `VERIFIED FROM ARTIFACT` |
| **Strictly Eligible Candidates ($C_{\text{strict}} \ge 15$)** | $6,844$ speakers | Recomputed across all 6 strata from `validated.tsv` ($61$ fail $C_{\text{strict}} \ge 15$) | `VERIFIED FROM ARTIFACT` |
| **Prior Project Exposures ($E_1 \cup E_S$)** | $90$ speakers ($15$/stratum) | $30$ in Sentinel Panel + $60$ in Replication Cohort 1 ($89$ strict-eligible, $1$ in $Q$) | `VERIFIED FROM ARTIFACT` |
| **Net Available Strictly Eligible Pool** | $6,755$ speakers | Recomputed unexposed candidate pool across all six demographic strata | `VERIFIED FROM ARTIFACT` |
| **Bottleneck Group Capacity** | Irish English (`ireland`) | **$78$ untouched, unexposed strictly eligible speakers remaining** ($94 - 16 = 78$) | `VERIFIED FROM ARTIFACT` |
| **Feasibility of $N=180$ ($30$/group)** | **FEASIBLE** | Requires $30 / 78$ Irish speakers ($38.5\%$ bottleneck utilization) | `VERIFIED FROM ARTIFACT` |
| **Feasibility of $N=240$ ($40$/group)** | **FEASIBLE** | Requires $40 / 78$ Irish speakers ($51.3\%$ bottleneck utilization) | `VERIFIED FROM ARTIFACT` |
| **Feasibility of $N=300$ ($50$/group)** | **FEASIBLE** | Requires $50 / 78$ Irish speakers ($64.1\%$ bottleneck utilization) | `VERIFIED FROM ARTIFACT` |
| **Feasibility of $N=360$ ($60$/group)** | **FEASIBLE** | Requires $60 / 78$ Irish speakers ($76.9\%$ bottleneck utilization) | `VERIFIED FROM ARTIFACT` |
| **Feasibility of $N=420$ ($70$/group)** | **FEASIBLE** | Requires $70 / 78$ Irish speakers ($89.7\%$ bottleneck utilization) | `VERIFIED FROM ARTIFACT` |
| **Maximum Feasible 6-Group Balanced Cohort** | **$N = 468$ speakers** | Constrained by Irish stratum bottleneck ($78 \times 6 = 468$) | `VERIFIED FROM ARTIFACT` |
| **Confirmatory Cohort Readiness** | **PROPOSED** | Not yet selected or manifested; overlap audit pending | `PROPOSED` |

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
FEASIBILITY VERDICT: PASS FOR CANDIDATE POOL CAPACITY UP TO N = 420 SPEAKERS (MAX N = 468).
The candidate Common Voice 27.0 pool contains sufficient unexposed speakers to construct
balanced cohorts up to N = 420 (70/group). However, Cohort 2 has NOT yet been selected or manifested.
Actual speaker-disjointness verification remains strictly pending cohort creation.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 2. Demographic Strata & Six-Group Strict Eligibility Ledger (Workstream A)

In accordance with [`reports/stage5/common_voice_metadata_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/common_voice_metadata_audit.md) and [`reports/stage5/protocol_amendment_cv27.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/protocol_amendment_cv27.md), all candidates must satisfy:
1. **Verified Accent Stratum:** Self-reported accent metadata mapping cleanly to one of the six prespecified target accents.
2. **Audio Volume Invariant:** Minimum of $15$ validated, non-empty audio clips with valid reference transcriptions ($\ge 2$ words).
3. **Cryptographic Integrity:** Verified audio SHA-256 hashes and sample rate $\ge 16\,\text{kHz}$.

### 2.1 Complete Six-Group Strict Eligibility Reconciliation Table:

The candidate speaker inventory was audited by directly recomputing both $C_{\text{inventory}}(s)$ and $C_{\text{strict}}(s)$ from the canonical Common Voice 27.0 dataset ([`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv), $1,929,854$ rows) for all $6,905$ inventory speakers across all six accent strata:

| Accent Group Name | Stratum Code | Baseline Inventory $\lvert I_g \rvert$ | Failing Strict $\lvert Q_g \rvert$ ($C_{\text{strict}} < 15$) | Strictly Eligible Total ($C_{\text{strict}} \ge 15$) | Strictly Eligible Exposed ($E_1 \cup E_S$) | Failing Strict Exposed ($Q \cap E_1$) | Other Exclusions ($E_4 / E_C$) | Net Available Unexposed Strictly Eligible | Previous Reported Available | Discrepancy ($\Delta$) | Feasibility Active CV ($75$/gp) | Feasibility Policy A Reserve | Feasibility Policy B Reserve |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | `australia` | $400$ | $2$ | $398$ | $15$ | $0$ | $0$ | **$383$** | $385$ | $-2$ | **PASS** ($383 \ge 75$) | **PASS** ($383 \ge 75$) | **PASS** ($383 \ge 78$) |
| **Canadian English** | `canada` | $511$ | $0$ | $511$ | $15$ | $0$ | $0$ | **$496$** | $496$ | $0$ | **PASS** ($496 \ge 75$) | **PASS** ($496 \ge 75$) | **PASS** ($496 \ge 78$) |
| **England English** | `england` | $1,223$ | $10$ | $1,213$ | $15$ | $0$ | $0$ | **$1,198$** | $1,208$ | $-10$ | **PASS** ($1,198 \ge 75$) | **PASS** ($1,198 \ge 75$) | **PASS** ($1,198 \ge 78$) |
| **Irish English** | `ireland` | $94$ | $2$ | $92$ | $14$ | $1$ | $0$ | **$78$** | $78$ | $0$ | **PASS** ($78 \ge 75$) | **PASS** ($78 \ge 78$) | **PASS** ($78 \ge 78$, zero headroom) |
| **South Asian English** | `south_asian` | $764$ | $18$ | $746$ | $15$ | $0$ | $0$ | **$731$** | $749$ | $-18$ | **PASS** ($731 \ge 75$) | **PASS** ($731 \ge 75$) | **PASS** ($731 \ge 78$) |
| **US English** | `us` | $3,913$ | $29$ | $3,884$ | $15$ | $0$ | $0$ | **$3,869$** | $3,898$ | $-29$ | **PASS** ($3,869 \ge 75$) | **PASS** ($3,869 \ge 75$) | **PASS** ($3,869 \ge 78$) |
| **Total All 6 Groups** | **All 6** | **$6,905$** | **$61$** | **$6,844$** | **$89$** | **$1$** | **$0$** | **$6,755$** | **$6,814$** | **$-59$** | **PASS** ($6,755 \ge 450$) | **PASS** ($6,755 \ge 453$) | **PASS** ($6,755 \ge 468$, CV feasible across all 6 strata; External shortfall: $162$) |

#### Key Empirical Audit Findings:
1. **Methodological Source of Discrepancies:**
   Earlier draft reports calculated available non-Irish speakers by simply subtracting $15$ exposed speakers from baseline inventory totals ($400-15=385$, $511-15=496$, $1223-15=1208$, $764-15=749$, $3913-15=3898$). The recomputation reveals that across the five non-Irish groups, exactly $59$ speakers satisfy baseline inventory qualification ($C_{\text{inventory}} \ge 15$) but fail strict quality filtering ($C_{\text{strict}} < 15$ due to down-votes $\ge 2$ or up-votes $< 2$).
2. **Prior Exposure Overlap with Quality Exclusions:**
   Across all $90$ previously exposed speakers ($15$/stratum: $10$ in Cohort 1 $E_1$, $5$ in Sentinel Panel $E_S$), exactly **$1$ speaker** (`f3ea04475e301f84785710b9…` in Irish Cohort 1) failed the strict clip-count threshold ($C_{\text{strict}} = 13 < 15$). All other $89$ exposed speakers ($14$ Irish + $75$ non-Irish) satisfy strict eligibility ($C_{\text{strict}} \ge 15$).
3. **Allocation Feasibility Across Strata:**
   - **Active Study ($N_{\text{active}}=540$, $75$ CV/stratum):** Fully feasible across all six strata ($383, 496, 1198, 78, 731, 3869 \ge 75$).
   - **Reserve Policy A (Irish-only reserve: $78$ CV Irish, $75$ non-Irish):** Fully feasible across all six strata ($78 \ge 78$, others $\ge 75$). External acquisition shortfall: $102$ unacquired external speakers.
   - **Reserve Policy B (Balanced reserve: $78$ CV/stratum = $75$ active + $3$ reserve):** Common Voice capacity is **FEASIBLE** across all six strata ($383, 496, 1198, 78, 731, 3869 \ge 78$), with the bottleneck Irish stratum meeting its Common Voice allocation with **zero reserve headroom** ($78 \ge 78$). The $18$ Common Voice reserve speakers are distributed uniformly across all six strata ($3$ per group), not assigned to a single stratum. There is zero Common Voice deficit. Policy B remains strictly blocked by the external-corpus acquisition shortfall ($162$ unacquired external speakers across the six strata).

### 2.2 Complete Speaker-Level Reconciliation of All 61 Quality Excluded IDs ($|Q| = 61$):
- **Australian English ($2$ IDs):**
  - `4fe0eb6706bbcb9c916c8e3a…`: $C_{\text{inventory}} = 15$, $C_{\text{strict}} = 12$ ($3$ clips with `down_votes >= 2`). Unexposed candidate: $Q \setminus (E_1 \cup E_S)$.
  - `b835db39bd1c209687467f26…`: $C_{\text{inventory}} = 15$, $C_{\text{strict}} = 13$ ($2$ clips with `down_votes >= 2`). Unexposed candidate: $Q \setminus (E_1 \cup E_S)$.
- **Canadian English ($0$ IDs):** Zero quality exclusions; all $511$ inventory speakers satisfy $C_{\text{strict}} \ge 15$.
- **England English ($10$ IDs):**
  - `64b66251…` ($16 \to 14$), `847a6ca4…` ($15 \to 14$), `04e6c290…` ($15 \to 13$), `d66c4a40…` ($19 \to 14$), `108d8f54…` ($15 \to 13$), `4ac92e02…` ($15 \to 14$), `3cc097e8…` ($16 \to 8$), `062d40cd…` ($15 \to 13$), `eef81ebc…` ($15 \to 14$), `f2f0f9aa…` ($15 \to 14$). All $10$ IDs belong to $Q \setminus (E_1 \cup E_S)$ (unexposed).
- **Irish English ($2$ IDs):**
  - `fc22fd45334612a489c45562…`: $C_{\text{inventory}} = 15$, $C_{\text{strict}} = 14$ ($1$ clip with `down_votes = 2`). Unexposed candidate: $Q \setminus E_1$.
  - `f3ea04475e301f84785710b9…`: $C_{\text{inventory}} = 15$, $C_{\text{strict}} = 13$ ($2$ clips with `down_votes = 2`, $1$ single-word clip). Cohort 1 exposure: $Q \cap E_1$.
- **South Asian English ($18$ IDs):**
  - `68f6a6d4…` ($15 \to 14$), `c82e9104…` ($17 \to 13$), `e6333591…` ($17 \to 14$), `d80376b4…` ($15 \to 14$), `6cd76534…` ($15 \to 13$), `aeeab502…` ($15 \to 14$), `aeb2ce73…` ($15 \to 14$), `ab60eac2…` ($15 \to 13$), `07004fed…` ($15 \to 14$), `08db8832…` ($17 \to 14$), `95f6d62f…` ($17 \to 14$), `e1cb092c…` ($15 \to 14$), `0a0db76f…` ($18 \to 12$), `197db23b…` ($21 \to 3$), `e78fb513…` ($15 \to 13$), `50bfe8d6…` ($15 \to 13$), `25949e8d…` ($15 \to 13$), `a7a33ab5…` ($17 \to 14$). All $18$ IDs belong to $Q \setminus (E_1 \cup E_S)$ (unexposed).
- **US English ($29$ IDs):**
  - $29$ speakers satisfy $C_{\text{inventory}} \ge 15$ but fail $C_{\text{strict}} \ge 15$ (e.g., `435fb74c…` with $C_{\text{inv}}=28, C_{\text{strict}}=0$ due to down-votes, `b3ab209d…` $17 \to 9$, `6fd13ac1…` $16 \to 11$, `0e8fc131…` $16 \to 8$, and $25$ others with $C_{\text{strict}} \in [8, 14]$). All $29$ IDs belong to $Q \setminus (E_1 \cup E_S)$ (unexposed).

### 2.3 Cryptographic Artifact Provenance Hashes

The candidate pool inventory, previous exposure splits, and sentinel manifests are verified against authoritative SHA-256 digests:

| Artifact Path | SHA-256 Checksum | Record / Speaker Count | Epistemic Role |
| :--- | :---: | :---: | :--- |
| [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | `e964799b50a84fa564173393ab55948afc3166b882e032d0ad0be7f880b7c94a` | $6,905$ speakers | Canonical candidate pool ground truth |
| [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) | `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32` | $60$ speakers ($10$/group) | Cohort 1 replication evaluation stream |
| [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) | `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543` | $30$ speakers ($5$/group) | Online Sentinel Panel safety monitor |
| [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) | `4622b215b18c6b4de80fb7832788ce7286e88c5528f501e2bac62f935e570028` | $30$ speakers | Sentinel Panel metadata manifest |
| [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) | `c2a746db83e02e81289baf8ca5fcd95be254a6e1de312a3f76c9b44e8c899d03` | $24$ speakers | Stage 4 characterization split |
| [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv) | `7c1659433b2b3539aa02b079d30588210a799620c5182e99c2ea0a61de284ca2` | $16$ speakers | Stage 4 calibration split |

---

## 3. Bottleneck Analysis & Multi-Corpus Feasibility

Because balanced subgroup representation across all six strata is required to evaluate the inter-group range statistic, the maximum attainable balanced cohort size from Common Voice 27.0 alone is strictly governed by the smallest available stratum (Irish English).

### 3.1 Rigorous Mathematical Definition of Clip-Count Metrics (Workstream C)

To eliminate any ambiguity between speaker-level counts and clip-level filters, the qualification metrics are formulated rigorously by separating Boolean eligibility predicates from numeric indicator summations over candidate TSV rows in [`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv).

Let $\mathcal{R}_s$ denote the set of candidate TSV rows associated with speaker $s$.

#### 1. Baseline Boolean Predicate and Inventory Clip Count ($C_{\text{inventory}}(s)$):
Define the baseline Boolean predicate $B_0(r)$ indicating whether clip row $r \in \mathcal{R}_s$ satisfies the baseline requirements:
$$B_0(r) \iff \left[ \operatorname{accent}(r) = \text{Stratum} \right] \land \left[ \operatorname{client\_id}(r) \ne \emptyset \right] \land \left[ \operatorname{path}(r) \text{ non-empty \& globally unique} \right] \land \left[ \operatorname{words}(\operatorname{sentence}(r)) \ge 2 \right] \land \left[ \operatorname{homogeneous\_accent}(s) = 1 \right]$$

The speaker-level inventory qualification clip count is the indicator summation:
$$C_{\text{inventory}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r)]$$

A candidate speaker qualifies for baseline candidate inventory $I$ if and only if they possess at least 15 valid baseline clips:
$$s \in I \iff C_{\text{inventory}}(s) \ge 15$$
Applying this criterion yields exactly $|I| = \mathbf{94}$ Irish English speakers in [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv).

#### 2. Strict Quality Boolean Predicate and Strict Clip Count ($C_{\text{strict}}(s)$):
Let $V(r)$ represent the Boolean predicate evaluating strict vote and locale requirements for clip row $r \in \mathcal{R}_s$:
$$V(r) \iff \left[ \operatorname{locale}(r) = \text{'en'} \right] \land \left[ \operatorname{up\_votes}(r) \ge 2 \right] \land \left[ \operatorname{down\_votes}(r) < 2 \right]$$

The strict quality clip count for speaker $s$ is the indicator summation over rows satisfying both baseline and strict predicates:
$$C_{\text{strict}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r) \land V(r)]$$

The strict speaker eligibility condition is:
$$s \text{ passes strict clip eligibility} \iff C_{\text{strict}}(s) \ge 15$$

The quality-exclusion set $Q$ within inventory $I$ consists strictly of speakers whose strict clip count falls below 15:
$$Q = \left\{ s \in I \mid C_{\text{strict}}(s) < 15 \right\}$$

#### 3. Path Uniqueness & Duplicate Handling:
Path uniqueness is evaluated as a global property of candidate audio paths across the dataset: the first encountered occurrence of a clip path is accepted, and all subsequent duplicate occurrences are discarded globally across the corpus, consistent with `build_eligible_speaker_pools` in [`scripts/phase3_external_eval_curation.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/phase3_external_eval_curation.py).

#### 4. Speaker-Level Audit of Disputed Quality-Excluded IDs:
Both disputed Irish speakers satisfy baseline inventory qualification ($C_{\text{inventory}} = 15$), but fail strict qualification ($C_{\text{strict}} < 15$):

| Speaker Identifier (`client_id`) | Truncated Prefix | $C_{\text{inventory}}$ | $C_{\text{strict}}$ | Disqualified Clip Reasons | Membership $I$ | Membership $E_1$ | Membership $E_S$ | Exclusion Category & Status |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| `fc22fd45334612a489c45562...` | `fc22fd45334612a489c45562…` | $15$ | $14$ | 1 clip with `down_votes = 2` (`common_voice_en_619904.mp3`) | $\in I$ | $\notin E_1$ | $\notin E_S$ | **Unexposed Quality Exclusion:** $Q \setminus E_1$ (1 ID) |
| `f3ea04475e301f84785710b9...` | `f3ea04475e301f84785710b9…` | $15$ | $13$ | 2 clips with `down_votes = 2`; 1 clip with 1 word | $\in I$ | $\in E_1$ | $\notin E_S$ | **Cohort 1 Overlap Exclusion:** $E_1 \cap Q$ (1 ID) |

#### 5. Inventory-Restricted Set Equation & Deduplication:
Because $E_4$ and $E_C$ contain L2-ARCTIC speakers outside the Irish inventory, candidate exclusions must be formulated strictly within $I$:
$$I_{\text{excluded}} = I \cap (E_1 \cup E_S \cup E_4 \cup E_C \cup Q)$$

Expanding across disjoint subsets within $I$:
$$\begin{aligned}
|I_{\text{excluded}}| &= |I \cap E_1| + |I \cap E_S| + |I \cap E_4| + |I \cap E_C| + |I \cap (Q \setminus E_1)| \\
&= 10 + 5 + 0 + 0 + 1 \\
&= \mathbf{16}
\end{aligned}$$

The net eligible, unexposed Common Voice Irish English speakers available for Stage 6M Cohort 2 is:
$$I_{\text{available}} = I \setminus (E_1 \cup E_S \cup E_4 \cup E_C \cup Q) = I \setminus I_{\text{excluded}}$$
$$|I_{\text{available}}| = |I| - |I_{\text{excluded}}| = 94 - 16 = \mathbf{78}$$

The subtraction $94 - 16 = \mathbf{78}$ rigorously deduplicates the quality exclusion overlapping Cohort 1 (`f3ea0447...`), avoiding double-counting.

---

### 3.1b Provenance Reconciliation of the Historical "73 raw" Irish Annotation (Workstream B)

Earlier draft versions of the protocol proposal and feasibility reports included a parenthetical annotation in the Irish capacity row: `"(78 available; 73 raw)"`. An exhaustive forensic trace of project calculations identified the precise mathematical origin of the number $73$:

1. **Origin in Exploratory Draft Accounting:**
   In early working drafts preceding the formalization of inventory-restricted set equations:
   - Total baseline Irish inventory: $|I| = 94$.
   - Prior exposure to Replication Cohort 1: $|E_1| = 10$.
   - Pre-filtered pool before sentinel panel construction: $94 - 10 = 84$.
   - Exclusion of unexposed strict filter failure `fc22fd45...` ($C_{\text{strict}} = 14 < 15$): $84 - 1 = 83$ candidates in [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) (`pool_size: 83`).
   - The Sentinel Panel drew $5$ unexposed speakers ($|E_S| = 5$), leaving $83 - 5 = 78$ untouched, strictly eligible speakers.
   - **The Error:** An exploratory uncommitted draft inadvertently subtracted the $10$ replication speakers a *second time* from the post-filtered pool:
     $$83 - 10 = \mathbf{73}$$
2. **Epistemic Classification:**
   The number $73$ was neither a clip count nor an alternative stage of curation; it was an arithmetic artifact of subtracting the $10$ replication speakers twice in an exploratory draft.
3. **Formal Resolution:**
   - The verified candidate capacity is strictly $|I_{\text{available}}| = \mathbf{78}$ untouched, unexposed strictly eligible speakers.
   - The misleading label `"73 raw"` has been removed from all active summary tables and report templates.
   - This record documents the discrepancy and permanently resolves the historical question without modifying frozen archival records.

---

### 3.2 Evaluation of Planning Target Capacities:
Using the strictly audited bottleneck capacity of **$78$ untouched speakers**:

1. **Target 1: $N = 180$ ($30$ speakers/stratum — Supervisor Planning Target):**
   - Requirement: $30$ speakers per group
   - Irish English Reserve Headroom: $78 - 30 = \mathbf{48\text{ reserve speakers}}$
   - Utilization Rate: $30 / 78 = 38.5\%$
   - **Verdict: STRONGLY FEASIBLE.**
2. **Target 2: $N = 240$ ($40$ speakers/stratum — Intermediate Candidate):**
   - Requirement: $40$ speakers per group
   - Irish English Reserve Headroom: $78 - 40 = \mathbf{38\text{ reserve speakers}}$
   - Utilization Rate: $40 / 78 = 51.3\%$
   - **Verdict: STRONGLY FEASIBLE.**
3. **Target 3: $N = 300$ ($50$ speakers/stratum — Reconciled Candidate):**
   - Requirement: $50$ speakers per group
   - Irish English Reserve Headroom: $78 - 50 = \mathbf{28\text{ reserve speakers}}$
   - Utilization Rate: $50 / 78 = 64.1\%$
   - **Verdict: FEASIBLE.**
4. **Target 4: $N = 360$ ($60$ speakers/stratum — Recommended Dual-Scenario High-Power Target):**
   - Requirement: $60$ speakers per group
   - Irish English Reserve Headroom: $78 - 60 = \mathbf{18\text{ reserve speakers}}$
   - Utilization Rate: $60 / 78 = 76.9\%$
   - **Verdict: FEASIBLE.**
5. **Target 5: $N = 420$ ($70$ speakers/stratum — High-Capacity Intermediate):**
   - Requirement: $70$ speakers per group
   - Irish English Reserve Headroom: $78 - 70 = \mathbf{8\text{ reserve speakers}}$
   - Utilization Rate: $70 / 78 = 89.7\%$
   - **Verdict: FEASIBLE.**
6. **Target 6: $N = 450$ ($75$ speakers/stratum — High-Capacity with Reserve):**
   - Requirement: $75$ speakers per group
   - Irish English Reserve Headroom: $78 - 75 = \mathbf{3\text{ reserve speakers}}$
   - Utilization Rate: $75 / 78 = 96.2\%$
   - **Verdict: FEASIBLE (Maintains 3 untouched Irish speakers in reserve).**
7. **Target 7: $N = 468$ ($78$ speakers/stratum — Maximum Balanced Cohort Capacity):**
   - Requirement: $78$ speakers per group
   - Irish English Reserve Headroom: $78 - 78 = \mathbf{0\text{ reserve speakers}}$
   - Utilization Rate: $78 / 78 = 100.0\%$
   - **Verdict: FEASIBLE (Achieves $\ge 85\%$ joint power under Adjusted UCB97.5; exhausts unexposed Irish pool).**
   - Theoretical Maximum:
     $$N_{\text{max}} = 6 \times 78 = \mathbf{468\text{ speakers}} \quad (7,020\text{ clips})$$
     Any cohort exceeding $468$ total speakers ($>78$/group) would exhaust Irish English and violate balanced stratum representation.
8. **Target 8: $N = 540$ ($90$ speakers/stratum — Candidate Pool Expansion Target):**
   - Requirement: $90$ speakers per group across 6 strata ($540$ speakers total).
   - Target with 15 Reserve Headroom: $90 + 15 = \mathbf{105\text{ eligible unexposed Irish speakers}}$.
   - Verified Available in Common Voice 27.0: $\mathbf{78\text{ unexposed speakers}}$.
   - Capacity Headroom Deficit:
     $$105 - 78 = \mathbf{27\text{ additional eligible unexposed speakers required}}.$$
     (Even with zero reserve, the deficit is $90 - 78 = 12$ speakers).
   - Utilization of Existing Inventory: $90 / 78 = 115.4\%$ (Physically impossible from CV 27.0 alone).
   - **Feasibility Verdict: INFEASIBLE from Common Voice 27.0 alone.**
   - **Expansion Requirement:** Re-querying or re-filtering the existing Common Voice 27.0 inventory cannot produce these $27$ speakers because the entire verified release has already been exhausted under the frozen criteria. Option A expansion requires acquiring a genuinely new data source (e.g., Common Voice v28.0+ or public speech corpora such as IViE / LibriTTS-R) with cross-corpus speaker deduplication and acoustic harmonization.

---

### 3.3 Six-Stratum Multi-Corpus Active Feasibility Ledger ($N=540$)

The candidate Strategy A design ($N=540$) proposes an active allocation of $90$ evaluable speakers per stratum across all six accent groups ($540$ active participants total). To prevent accent–corpus confounding, external speech data must be introduced in an equal, fixed ratio $\theta = 15/90 = 16.7\%$ across **all six strata** ($75$ Common Voice + $15$ external speakers per stratum).

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              ACTIVE EVALUATION SAMPLE LEDGER (EXCLUDING RESERVES)                      │
│ The active study sample size is strictly N_active = 540 speakers (450 Common Voice + 90 External).    │
│ Reserve participants are designated strictly for replacement of attrition/corruption and are NOT      │
│ counted as active evaluable participants in statistical power or disparity estimands.                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 1. Complete Six-Stratum Active Allocation Ledger:

| Accent Stratum | Target Active ($n_{\text{eval}}$) | CV 27.0 Available (Unexposed Strictly Eligible) | CV Active Allocation | External Available in Repo | External Active Allocation | Active Corpus Proportions (CV / Ext) | Active External Shortfall | Eligibility & Exposure Verification Evidence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Australian English** | $90$ | $383$ | $75$ | $0$ | $15$ | $83.3\% / 16.7\%$ | **$15$** | CV: $C_{\text{strict}} \ge 15$ ($383$ available); external: unacquired (`[UNVERIFIED]`) |
| **Canadian English** | $90$ | $496$ | $75$ | $0$ | $15$ | $83.3\% / 16.7\%$ | **$15$** | CV: $C_{\text{strict}} \ge 15$ ($496$ available); external: unacquired (`[UNVERIFIED]`) |
| **England English** | $90$ | $1,198$ | $75$ | $0$ | $15$ | $83.3\% / 16.7\%$ | **$15$** | CV: $C_{\text{strict}} \ge 15$ ($1,198$ available); external: unacquired (`[UNVERIFIED]`) |
| **Irish English** | $90$ | $78$ | $75$ | $0$ | $15$ | $83.3\% / 16.7\%$ | **$15$** | CV: $C_{\text{strict}} \ge 15$ ($78$ available); external: unacquired (`[UNVERIFIED]`) |
| **South Asian English** | $90$ | $731$ | $75$ | $0$ | $15$ | $83.3\% / 16.7\%$ | **$15$** | CV: $C_{\text{strict}} \ge 15$ ($731$ available); external: unacquired (`[UNVERIFIED]`) |
| **US English** | $90$ | $3,869$ | $75$ | $0$ | $15$ | $83.3\% / 16.7\%$ | **$15$** | CV: $C_{\text{strict}} \ge 15$ ($3,869$ available); external: unacquired (`[UNVERIFIED]`) |
| **Active Study Totals** | **$540$** | **$6,755$** | **$450$** | **$0$** | **$90$** | **$83.3\% / 16.7\%$** | **$90$** | **$90$ active external speakers required across all 6 strata** |

#### 2. Key Multi-Corpus Feasibility Findings:
1. **$15$ External Speakers per Stratum Means $90$ Active External Speakers in Total:**
   $$N_{\text{external, active}} = 15 \times 6 = \mathbf{90 \text{ active external speakers}}$$
   The study requires $90$ active external speakers across the six accent strata, not $15$ external speakers overall.
2. **Tripartite Scoping of External Inventory Evidence:**
   The finding that external data cannot currently support confirmatory execution rests on three distinct, non-interchangeable evidentiary dimensions:
   - **Manifest Finding:** No external participants are registered in the confirmatory evaluation manifest. The confirmatory manifest (`datasets/splits/stage6m_confirmatory_eval.csv`) has not yet been generated or locked (`Cohort 2 = PROPOSED — NOT YET CREATED OR VERIFIED`).
   - **Repository Inventory Finding:** In the audited candidate pool inventory ([`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv), $6,905$ speakers), all $6,905$ speaker records originate $100\%$ from Mozilla Common Voice 27.0 ([`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv)). A full recursive scan of `datasets/` and workspace directories confirms that no non-Common Voice speech corpora (e.g., IViE, LibriTTS-R, or other multi-corpus evaluation datasets) are currently ingested, preprocessed, or validated for evaluation in the repository.
   - **Acquisition Finding:** The remaining external-speaker requirement ($102$ speakers under Policy A: $90$ active $+ 12$ Irish reserve; $162$ speakers under Policy B: $90$ active $+ 72$ reserve across all six strata) has not been fulfilled. All external candidates must be newly sourced, downloaded, audited for strict clip quality ($C_{\text{strict}} \ge 15$), and checked for cross-corpus speaker disjointness. Feasibility cannot be asserted based solely on the Common Voice Irish-speaker ledger.
3. **Accent–Corpus Confounding Analysis:**
   Even if macro-proportions are balanced ($75$ CV + $15$ External per group), multi-corpus sampling introduces severe risks of micro-level confounding:
   - **Speech Task Differences:** Common Voice consists of crowdsourced prompt-reading of disconnected sentences; external corpora such as LibriTTS-R comprise audiobook narration, while IViE comprises conversational and interview dialogues.
   - **Acoustic & Channel Disparities:** Microphones, room acoustics, signal-to-noise ratio (SNR), and background noise distributions differ systematically across corpora.
   - **Transcript Formatting:** Differences in casing, punctuation, and disfluency conventions between corpora could confound WER measurements unless strictly normalized.
   - **Conclusion:** Introducing external speech data does not automatically eliminate confounding; it requires explicit acoustic and phonetic covariate harmonization.

---

### 3.4 Reserve-Policy Definition & Scenario Ledger (Status: UNRESOLVED)

The reserve policy has **not been preregistered** in any existing protocol document (ADR-005, v1.1.0, or v1.2.0-proposal). It is formally classified as **`[UNRESOLVED]`**, requiring explicit supervisor determination before any multi-corpus candidate pool can be authorized.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 RESERVE POLICY STATUS: [UNRESOLVED]                                    │
│ Neither Policy A nor Policy B has been approved. The scenario tables below present the exact           │
│ arithmetic requirements under each candidate policy without pre-empting supervisory decision.          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Scenario 1: Policy Option A (Bottleneck-Focused Irish Reserve Only)
- **Concept:** Only the bottleneck Irish stratum maintains a pre-designated external reserve buffer ($15$ reserve speakers). The other five strata have large Common Voice surpluses ($>300$ unexposed speakers) from which replacements can be drawn directly if attrition occurs.
- **Allocation Rules:**
  - Irish English: $75$ CV active $+ 15$ Ext active $+ 3$ CV reserve $+ 12$ Ext reserve $= 105$ speakers ($78$ CV $+ 27$ Ext).
  - Other 5 Strata: $75$ CV active $+ 15$ Ext active $+ 0$ external reserve $= 90$ speakers each.

| Accent Stratum | Active Common Voice | Active External | Reserve Common Voice | Reserve External | Total Common Voice Ingested | Total External Ingested | Total Stratum Inventory | External Acquisition Shortfall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | $75$ | $15$ | $0$ | $0$ | $75$ | $15$ | $90$ | **$15$** |
| **Canadian English** | $75$ | $15$ | $0$ | $0$ | $75$ | $15$ | $90$ | **$15$** |
| **England English** | $75$ | $15$ | $0$ | $0$ | $75$ | $15$ | $90$ | **$15$** |
| **Irish English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **South Asian English** | $75$ | $15$ | $0$ | $0$ | $75$ | $15$ | $90$ | **$15$** |
| **US English** | $75$ | $15$ | $0$ | $0$ | $75$ | $15$ | $90$ | **$15$** |
| **Policy A Totals** | **$450$** | **$90$** | **$3$** | **$12$** | **$453$** | **$102$** | **$555$** | **$102$ unacquired external speakers** |

#### Scenario 2: Policy Option B (Stratum-Balanced Reserve in Every Group)
- **Concept:** Every stratum maintains identical reserve buffers ($3$ CV $+ 12$ External reserve $= 15$ reserve per group) to ensure uniform source mixture and identical attrition protocols across all six accent groups.
- **Allocation Rules:**
  - Every Stratum: $75$ CV active $+ 15$ Ext active $+ 3$ CV reserve $+ 12$ Ext reserve $= 105$ speakers ($78$ CV $+ 27$ Ext).

| Accent Stratum | Active Common Voice | Active External | Reserve Common Voice | Reserve External | Total Common Voice Ingested | Total External Ingested | Total Stratum Inventory | External Acquisition Shortfall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **Canadian English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **England English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **Irish English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **South Asian English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **US English** | $75$ | $15$ | $3$ | $12$ | $78$ | $27$ | $105$ | **$27$** |
| **Policy B Totals** | **$450$** | **$90$** | **$18$** | **$72$** | **$468$** | **$162$** | **$630$** | **$162$ unacquired external speakers** |

#### Crucial Feasibility Distinctions for Policy B:
1. **Common Voice Inventory Capacity is Feasible with Zero Headroom:**  
   Policy B requires $78$ Common Voice speakers per stratum ($75$ active $+ 3$ reserve), totaling $468$ Common Voice speakers across all six strata ($450$ active $+ 18$ reserve). Because the unexposed strictly eligible Irish pool contains exactly $78$ speakers, the Common Voice requirement is met with **zero reserve headroom** ($78 \ge 78$). The $18$ Common Voice reserve speakers are distributed uniformly across all six strata ($3$ per group), not concentrated in a single stratum. There is zero Common Voice deficit.
2. **External Acquisition Shortfall Remains an Absolute Blocker:**  
   Policy B requires $27$ external speakers per stratum ($15$ active $+ 12$ reserve), totaling $162$ external speakers across all six strata ($90$ active $+ 72$ reserve). Because zero external speakers currently exist in the repository, Policy B has an external acquisition shortfall of **$162$ unacquired external speakers**.

---

### 3.5 Disparity Estimand Notation & Qualified Allocation Statement (Workstream D & E)

#### 1. Formal Disparity Estimand Definitions:
Let $R_{m,g}$ denote the Word Error Rate (WER) for model condition $m \in \{\text{adapted}, \text{baseline}\}$ evaluated on accent group $g \in \mathcal{G}$ ($|\mathcal{G}| = 6$).

The inter-group disparity range for model condition $m$ is defined as:
$$D_m = \max_{g \in \mathcal{G}} R_{m,g} - \min_{g \in \mathcal{G}} R_{m,g}$$

The change in disparity induced by test-time adaptation is the difference in range statistics:
$$\Delta D = D_{\text{adapted}} - D_{\text{baseline}} = \left( \max_{g \in \mathcal{G}} R_{\text{adapted},g} - \min_{g \in \mathcal{G}} R_{\text{adapted},g} \right) - \left( \max_{g \in \mathcal{G}} R_{\text{baseline},g} - \min_{g \in \mathcal{G}} R_{\text{baseline},g} \right)$$
In the frozen protocol, $D_m$ represents a cross-sectional inequality level, while $\Delta D$ represents the primary confirmatory safety estimand (adaptation-induced disparity expansion or drift).

#### 2. Cancellation of Common Additive Corpus Effects in Range Estimators:
Consider an idealized case where corpus $k$ introduces a purely additive acoustic/channel shift $\gamma_k$ that is identical across all accent groups:
$$R^{(k)}_{m,g} = R_{m,g} + \gamma_k$$

Under this uniform additive shift, the corpus effect cancels identically from the disparity range:
$$\max_{g \in \mathcal{G}} R^{(k)}_{m,g} - \min_{g \in \mathcal{G}} R^{(k)}_{m,g} = \max_{g \in \mathcal{G}} (R_{m,g} + \gamma_k) - \min_{g \in \mathcal{G}} (R_{m,g} + \gamma_k) = \max_{g \in \mathcal{G}} R_{m,g} - \min_{g \in \mathcal{G}} R_{m,g} = D_m$$

Consequently, a nonzero corpus variance does **not** mathematically guarantee an inflation in the variance of the disparity estimator under all possible designs.

#### 3. Qualified Statement on Allocation Imbalance and Corpus Effects:
Differences in corpus composition across accent groups can leave group-specific residual shifts when corpus effects differ, potentially affecting disparity estimates and their uncertainty. The magnitude and direction of that effect depend on the allocation, corpus effects, and covariance structure.

Real-world speech corpora introduce complex, non-additive distortions that threaten statistical power:
1. **Corpus-by-Accent Interactions ($(\alpha\gamma)_{gk} \ne 0$):** Speech corpora recorded in different acoustic environments interact with accent characteristics (e.g., non-native phoneme substitutions may suffer higher degradation under low-SNR crowdsourced audio than native speech).
2. **Heteroscedastic Residual Variance ($\sigma^2_{\epsilon,k}$):** The clip-level error variance differs between studio-recorded speech, telephone speech, and browser-recorded crowdsourced speech.
3. **Correlation Shifts ($\rho_k$):** The paired correlation between adapted and baseline predictions may differ across recording channels.

#### 4. Disentangling Simulated Power from Executable Cohort Feasibility:
A crucial epistemic and methodological distinction must be maintained between hypothetical power under an idealized single-source Gaussian simulation and executable confirmatory research designs. Three distinct scenarios must be separated:

| Scenario Description | Cohort Size ($N$) | Stratum Allocation | Simulated Power Status | Audited Data Feasibility | Governance / Design Status |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Common Voice-Only Design** | $N = 468$ | $78$ CV/stratum ($0$ External) | Rule A PASS ($\widehat{P} = 85.82\% \ge 85\%$), **Rule B FAIL** ($L_{95\%} = 84.74\% < 85\%$) | **FEASIBLE** at stated capacity ($78 \le 78$ Irish CV) | Leaves **zero reserve headroom** for Irish English. Fallback design only. |
| **Hypothetical Single-Source Simulation** | $N = 540$ | $90$ CV/stratum ($0$ External) | **Rule A PASS** ($\widehat{P}_{\text{S2}} = 90.40\% \ge 85\%$), **Rule B PASS** ($L_{95\%} = 89.49\% > 85\%$) under single-source Gaussian DGP ($S_1\text{ Parity} = 99.95\%, S_2\text{ Drift} = 90.40\%$) | **NOT FEASIBLE** from current Irish CV pool ($12$-speaker deficit; $27$ with reserve) | **Hypothetical reference model only**; cannot be executed as a CV-only study. |
| **Proposed Multi-Corpus Study** | $N = 540$ | $75$ CV $+ 15$ Ext/stratum | **`UNRESOLVED`** pending design-specific power analysis | CV capacity **FEASIBLE** ($78 \ge 78$); External **SHORTFALL** ($102$ or $162$) | Mandatory hierarchical re-simulation with corpus variance priors required. |

**Required Methodological Distinction:**  
The $N=540$ single-source result passes Rule B under the simulated model, but the corresponding Common Voice-only participant allocation is infeasible using the current audited inventory. The proposed multi-corpus design has a separate, unresolved power status.

**Scientific Audit Invariant:** The existing $N=540$ simulation passes Rule B under its single-source Gaussian data-generating process ($\sigma^2_{\text{corpus}} = 0, \sigma^2_{\alpha\gamma} = 0$). Rule B status for the proposed multi-corpus study remains **`UNRESOLVED`** pending a design-specific power analysis. A design-specific power analysis incorporating empirical inter-corpus variance priors ($\sigma^2_{\text{corpus}} > 0$) and corpus-by-accent interaction parameters ($(\alpha\gamma)_{gk} \ne 0$) remains mandatory before confirmatory execution under Strategy A.

---

### 3.6 Canonical Source-Path Audit & Precise Version-Control Scope (Workstream D)

A comprehensive filesystem and repository history audit was conducted to verify artifact provenance:

#### 1. Current Working Tree & Active Path-Resolution Evidence:
- **Canonical Primary Artifact:** [`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv)
  - File Size: $614,927,262$ bytes ($1,929,854$ data rows).
  - SHA-256 Digest: `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a`.
  - Status: Exists on disk; actively read by [`scripts/phase3_external_eval_curation.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/phase3_external_eval_curation.py) and audited by [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py).
- **Configured Fallback Paths in Resolution Logic:**
  - `datasets/external/common_voice_27_intermediate/validated.tsv`: Unpack staging mirror with identical file size ($614,927,262$ bytes) and identical SHA-256 (`733c2fa7...`).
  - `datasets/external/common_voice_11/validated.tsv`: Legacy Common Voice 11.0 fallback.
  - HuggingFace streaming fallback (`cmu5jplf300nwmh07iqvk9leo`).
- **Path Actually Read During Documented Curation Run:**
  The canonical primary path [`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv) existed on disk and was selected on the initial candidate check in `load_metadata()`; configured fallback paths were not executed.
- **Absent Path:** `data/commonvoice/validated.tsv`
  - Status: **Absent from the current checkout** (`FileNotFoundError`). Zero occurrences across all active scripts, tests, manifests, and configurations.

#### 2. Precise Version Control Scope & Search Commands:
To substantiate historical provenance, an all-references history search was executed across the repository:
```powershell
git log --all --full-history -S"data/commonvoice/validated.tsv" -- .
git log --all --full-history -S"data/commonvoice" -- .
git log --all --grep="data/commonvoice"
```
**Empirical Search Result:** Exactly **$0$ commits found** across all three commands.

**Properly Scoped Epistemic Statement:**
No matching occurrence of `data/commonvoice/validated.tsv` was found in the reachable Git history searched. The path originated strictly as an informal shorthand label in earlier conversational audit review summaries. Frozen historical Stage 5 reports citing the intermediate unpacking directory remain untouched as immutable archival records. Active Stage 6M protocol documents and test suites specify `datasets/external/common_voice_27/validated.tsv` as the canonical source artifact.

---

### 3.7 Research-Validity Test Suite Execution & Qualified Warning Review

Execution of the full research-validity test directory ([`tests/research_validity/`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/)) confirms that all $110$ tests passed across all $12$ modules in $21.29\,\text{s}$ (exit code $0$). Complete log saved to [`reports/stage6m/research_validity_pytest_run.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/research_validity_pytest_run.log).

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

---

## 4. Status of Confirmatory Cohort & Disjointness Protections

### 4.1 Epistemic Status of Cohort 2:
The research supervisor rightly noted an inconsistency in earlier reporting: claiming both that Cohort 2 was uncreated and that it had mathematically verified zero speaker overlap.

To protect the scientific integrity of the confirmatory study, the formal declaration is updated:

> **Formal Protocol Declaration on Cohort 2 Disjointness:**  
> The preliminary data-feasibility audit indicates that the proposed cohort sizes ($N \in \{180, 240, 300, 360, 420, 450, 468\}$) may be achievable from the candidate Common Voice 27.0 dataset. The new confirmatory cohort (Cohort 2) has **not yet been selected or manifested**; its actual speaker-overlap checks remain strictly pending. No confirmatory independence claim will be made until the selected manifest has been generated, cryptographically locked, and audited.

### 4.2 Distinctions Maintained:
1. **Candidate-Pool Feasibility (`VERIFIED FROM ARTIFACT`):**  
   Common Voice 27.0 possesses $78$ unexposed Irish speakers and $>380$ unexposed speakers in all other strata, proving pool adequacy for balanced cohorts up to $N = 468$.
2. **Actual Selected Cohort Disjointness (`PROPOSED — PENDING MANIFEST CREATION`):**  
   Once the final sample size is approved by the supervisor, a deterministic curation script will sample candidate speakers from the unselected set (`selected == False`). Only when `stage6m_confirmatory_eval.csv` exists will the identity intersection test:
   $$\lvert S_{\text{confirmatory}} \cap S_{\text{stage5\_sentinel\_panel}} \rvert = 0$$
   $$\lvert S_{\text{confirmatory}} \cap S_{\text{stage5\_external\_eval}} \rvert = 0$$
   $$\lvert S_{\text{confirmatory}} \cap S_{\text{stage4\_characterization}} \rvert = 0$$
   be executed and verified against actual client hashes.
3. **Evaluation-Data Exposure History (`VERIFIED FROM ARTIFACT`):**  
   Cohort 1 ([`stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv), $N=60$) was utilized in Stage 5M exploration. It is preserved strictly as replication and replay data, with its prior exposure fully disclosed.
4. **Confirmatory Transcript Quarantine (`LOCKED`):**  
   Confirmatory reference transcripts must remain unaccessed and quarantined.

---

## 5. Reference Transcript Quarantining & Governance Protections

To preserve genuine blind confirmatory status and prevent result-driven optimization:
1. **Quarantine of Ground-Truth References:**  
   The reference transcripts $Y_t$ for Cohort 2 must remain in a quarantined research directory (`datasets/confirmatory_vault/quarantine/`) with read permissions restricted to the offline post-stream evaluator.
2. **Online Blindness Guarantee:**  
   The online adaptation loop (Arm 3) and operational safety gate operate exclusively on unannotated streaming audio $X_t$ and pre-stream Sentinel Panel data ($N=30$). It is cryptographically prohibited from accessing $Y_t$ during stream execution.
3. **Zero Pre-Execution Evaluation:**  
   No baseline evaluations, preliminary CTC decoding, or acoustic difficulty checks may be run on Cohort 2 prior to formal supervisor preregistration sign-off.
4. **Current Status Declaration:**  
   Until a cryptographically hashed manifest `stage6m_confirmatory_eval.lock.json` is signed by the supervisor, Cohort 2 is formally classified as:
   $$\boxed{\mathbf{PROPOSED\ —\ NOT\ YET\ CREATED\ OR\ VERIFIED}}$$

### Governance Lock Block

```
================================================================================
STAGE 6M PREREGISTRATION & GOVERNANCE LOCK
Status: HOLD — STRICTLY NOT AUTHORIZED
execution_authorized = false
Final Sample Size: UNFROZEN
Cohort 2 Status: PROPOSED — NOT YET CREATED OR VERIFIED
================================================================================
```
"""

if __name__ == "__main__":
    out = Path("reports/stage6m/stage6m_data_feasibility_audit.md")
    out.write_text(content, encoding="utf-8")
    print("Wrote stage6m_data_feasibility_audit.md successfully.")
