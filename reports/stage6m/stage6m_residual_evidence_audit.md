# Stage 6M v1.2.0 — Residual Evidence & Technical Integrity Audit

**Standard:** ADR-005  
**Protocol Version:** `v1.2.0-stage6m-proposal`  
**Document Identifier:** [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md)  
**Governance State:** `HOLD — STRICTLY NOT AUTHORIZED` (`execution_authorized = false`)  
**Audit Scope:** Residual Clip-Level Quality Accounting, Seed Lineage, Baseline Checksums, and Test Evidence Verification  
**Evaluation Target Corpus:** Mozilla Common Voice Scripted Speech 27.0 English (`cv-corpus-27.0-2026-09-11`)  

---

## 1. Executive Summary & Audit Matrix

Following the Independent Technical Audit, a targeted residual audit of primary local artifacts was conducted across the workspace. All technical issues have been investigated using direct disk, Git object store, and execution logs:

| Audit Domain | Focus Area | Audit Status | Primary Local Evidence |
| :--- | :--- | :---: | :--- |
| **Audit 1** | Irish Clip-Level Eligibility & Set Reconciliation | **PASS** | $16$ raw rows for `f3ea0447…` ($1$ baseline exclusion, $2$ strict exclusions); $15$ raw rows for `fc22fd45…` ($1$ strict exclusion). Deduplicated capacity is strictly $78$ speakers. |
| **Audit 2** | Seed Formula, Index Convention & Power Tempering | **PASS** | Script uses `np.random.seed(42 + cohort_n + sc_id * 1000)` ($\\text{seed} = 42 + N + 1000 \\cdot \\text{sc\\_id}$ with $1$-based $\\text{sc\\_id} \\in \\{1,2,3,4\\}$). Different seed initializations produce different pseudorandom sequences. Monte Carlo variation explicitly acknowledged alongside sample-size scaling. |
| **Audit 3** | Baseline Integrity, CRLF Normalization & Simulation Provenance | **PASS** (Tracked Text Parity) / **UNVERIFIED** (Untracked Historical Provenance) | Text content matches Git HEAD after CRLF normalization across all 6 tracked artifacts ($0$ standalone CR). For untracked `power_simulation_results.json`, current hash matches canonical documentation (`8fac4d32…`), but Git historical immutability is UNVERIFIED. |
| **Audit 4** | Full Research-Validity Test Suite Execution | **PASS** | [`test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) confirms **113 passed across 12 modules in 26.15s** (exit code $0$, $6$ counted pytest warnings, $2$ process stderr diagnostics). |
| **Audit 5** | Scientific & Governance Execution Lock | **PASS** | `execution_authorized = false`, `Cohort 2 = PROPOSED`, `Sample size = UNFROZEN`, `Reserve policy = UNRESOLVED`. Final verdict: **STRICT NO-GO**. |

```
═══════════════════════════════════════════════════════════════════════════════════════════════════
FINAL GOVERNANCE DECISION: HOLD — STRICTLY NOT AUTHORIZED
execution_authorized: false
Confirmatory Execution Verdict: STRICT NO-GO
Software and accounting invariants are verified; scientific hypotheses and multi-corpus
power models remain unpreregistered, unapproved, and blocked from execution.
═══════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 2. Audit 1 — Reconcile Irish Clip-Level Eligibility

### 2.1 The Two Disputed Irish Quality Exclusions
The frozen inventory [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) records exactly $94$ Irish English speakers satisfying baseline inventory qualification ($C_{\text{inventory}} \ge 15$). Under the strict quality predicate $V(r)$ ($\operatorname{locale} = \text{'en'}, \operatorname{up\_votes} \ge 2, \operatorname{down\_votes} < 2$), exactly **$2$ speakers** fail the strict threshold $C_{\text{strict}} \ge 15$.

A direct audit of all corresponding rows in [`datasets/external/common_voice_27/validated.tsv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/external/common_voice_27/validated.tsv) was performed:

#### 1. Speaker `f3ea04475e301f84785710b9…` (Cohort 1 Overlap Exclusion: $E_1 \cap Q$)
This speaker has **$16$ candidate rows in `validated.tsv`**.

| Clip # | Audio Path (`path`) | Transcript Word Count | Locale | Up-Votes | Down-Votes | Satisfies Baseline $B_0(r)$? | Satisfies Strict $V(r)$? | Strict Eligible? | Disqualification Reason / Notes |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `common_voice_en_30480269.mp3` | 10 | `en` | 2 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **2** | `common_voice_en_30480240.mp3` | 7 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **3** | `common_voice_en_30480248.mp3` | 13 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **4** | `common_voice_en_30480242.mp3` | 14 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **5** | `common_voice_en_30480274.mp3` | 7 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **6** | `common_voice_en_30480241.mp3` | 9 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **7** | `common_voice_en_30480278.mp3` | 9 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **8** | `common_voice_en_30480276.mp3` | 8 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **9** | `common_voice_en_30480275.mp3` | 12 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **10** | `common_voice_en_30480250.mp3` | 9 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **11** | `common_voice_en_30480271.mp3` | 8 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **12** | `common_voice_en_30480239.mp3` | 5 | `en` | 4 | **2** | **Yes** | **No** | **No** | **Strict Failure:** `down_votes >= 2` (2 down-votes) |
| **13** | `common_voice_en_30480238.mp3` | 13 | `en` | 4 | **2** | **Yes** | **No** | **No** | **Strict Failure:** `down_votes >= 2` (2 down-votes) |
| **14** | `common_voice_en_30480252.mp3` | 8 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **15** | `common_voice_en_30480272.mp3` | **1** | `en` | 4 | 0 | **No** | **Yes** | **No** | **Baseline Failure:** `words < 2` (`'Cllr.'`, single word) |
| **16** | `common_voice_en_30480251.mp3` | 12 | `en` | 6 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |

##### Reconciliation of Metrics for `f3ea0447…`:
1. **Raw Candidate Rows:** $16$ rows in `validated.tsv`.
2. **Baseline Inventory Filtering:** Row 15 (`'Cllr.'`) has only $1$ word, failing the baseline requirement $\operatorname{words}(\operatorname{sentence}(r)) \ge 2$. It is excluded during baseline inventory generation ($16 - 1 = \mathbf{15}$).
   $$C_{\text{inventory}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r)] = \mathbf{15}$$
   This qualifies the speaker for [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) ($C_{\text{inventory}} = 15$).
3. **Stage 5 Evaluation Inclusion:** When Stage 5 curated Cohort 1 ([`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv)), this speaker was drawn as one of the $10$ Irish speakers. Its $15$ baseline clips (`stage5ext_00796` through `stage5ext_00810`) were ingested.
4. **Strict Quality Filtering:** When the frozen strict quality predicate $V(r)$ (`down_votes < 2`) is evaluated across the $15$ baseline clips:
   - Row 12 (`common_voice_en_30480239.mp3` / `stage5ext_00808`): `down_votes = 2` (disqualified).
   - Row 13 (`common_voice_en_30480238.mp3` / `stage5ext_00803`): `down_votes = 2` (disqualified).
   - Surviving strict clips: $15 - 2 = \mathbf{13}$ clips.
   $$C_{\text{strict}}(s) = \sum_{r \in \mathcal{R}_s} \mathbf{1}[B_0(r) \land V(r)] = \mathbf{13}$$
5. **Resolution of Ambiguity:** The speaker fails strict eligibility because $C_{\text{strict}} = 13 < 15$. The confusion in previous drafts arose from listing $3$ disqualified clips ($1$ single-word clip $+ 2$ down-voted clips) alongside $C_{\text{inventory}} = 15$. The single-word clip was removed at the *baseline stage* ($16 \to 15$), and the two down-voted clips were removed at the *strict stage* ($15 \to 13$).

---

#### 2. Speaker `fc22fd45334612a489c45562…` (Unexposed Quality Exclusion: $Q \setminus (E_1 \cup E_S)$)
This speaker has **$15$ candidate rows in `validated.tsv`**.

| Clip # | Audio Path (`path`) | Transcript Word Count | Locale | Up-Votes | Down-Votes | Satisfies Baseline $B_0(r)$? | Satisfies Strict $V(r)$? | Strict Eligible? | Disqualification Reason / Notes |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `common_voice_en_619907.mp3` | 16 | `en` | 2 | 1 | **Yes** | **Yes** | **Yes** | Valid strict clip (`down_votes = 1 < 2`) |
| **2** | `common_voice_en_619900.mp3` | 16 | `en` | 3 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **3** | `common_voice_en_619902.mp3` | 12 | `en` | 3 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **4** | `common_voice_en_619903.mp3` | 8 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **5** | `common_voice_en_619904.mp3` | 9 | `en` | 3 | **2** | **Yes** | **No** | **No** | **Strict Failure:** `down_votes >= 2` (2 down-votes) |
| **6** | `common_voice_en_619905.mp3` | 16 | `en` | 5 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **7** | `common_voice_en_619909.mp3` | 7 | `en` | 3 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **8** | `common_voice_en_619906.mp3` | 8 | `en` | 2 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **9** | `common_voice_en_619898.mp3` | 9 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **10** | `common_voice_en_619908.mp3` | 5 | `en` | 5 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **11** | `common_voice_en_619897.mp3` | 14 | `en` | 4 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **12** | `common_voice_en_619901.mp3` | 6 | `en` | 2 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **13** | `common_voice_en_619899.mp3` | 13 | `en` | 5 | 1 | **Yes** | **Yes** | **Yes** | Valid strict clip (`down_votes = 1 < 2`) |
| **14** | `common_voice_en_619896.mp3` | 7 | `en` | 3 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |
| **15** | `common_voice_en_619895.mp3` | 7 | `en` | 7 | 0 | **Yes** | **Yes** | **Yes** | Valid strict clip |

##### Reconciliation of Metrics for `fc22fd45…`:
1. **Raw Candidate Rows:** Exactly $15$ rows in `validated.tsv`.
2. **Baseline Inventory Filtering:** All $15$ rows have word count between $5$ and $16$ ($\ge 2$ words) and satisfy $B_0(r)$.
   $$C_{\text{inventory}}(s) = \mathbf{15}$$
3. **Strict Quality Filtering:** Row 5 has `down_votes = 2`, failing predicate $V(r)$. The remaining $14$ rows satisfy $V(r)$.
   $$C_{\text{strict}}(s) = 15 - 1 = \mathbf{14} < 15$$
4. **Exposure Status:** This speaker is unexposed ($\notin E_1$, $\notin E_S$). It represents a solitary unexposed quality exclusion ($Q \setminus (E_1 \cup E_S)$).

---

### 2.2 Recomputed Irish Exposure-Set Equations & Deduplication Proof

From primary records:
- **Baseline Irish Pool ($I_{\text{Irish}}$):** $|I_{\text{Irish}}| = \mathbf{94}$
- **Quality Exclusion Set ($Q_{\text{Irish}}$):** $|Q_{\text{Irish}}| = \mathbf{2}$ (`f3ea0447…` and `fc22fd45…`)
- **Strictly Eligible Irish Pool:** $|I_{\text{Irish}} \setminus Q_{\text{Irish}}| = 94 - 2 = \mathbf{92}$
- **Replication Cohort 1 Irish ($E_1$):** Exactly **$10$ speakers** ($1$ in $Q$, $9$ in $I \setminus Q$)
- **Sentinel Panel Irish ($E_S$):** Exactly **$5$ speakers** ($0$ in $Q$, all $5$ in $I \setminus Q$)
- **Sentinel Disjointness:** $|E_1 \cap E_S| = 0$
- **Total Exposed Irish Candidates:** $|(E_1 \cup E_S) \cap I_{\text{Irish}}| = 10 + 5 = \mathbf{15}$
- **Strictly Eligible Exposed Irish Candidates:** $|(E_1 \cup E_S) \cap (I_{\text{Irish}} \setminus Q)| = 9 + 5 = \mathbf{14}$

#### Derivation A (Strictly Eligible Pool Minus Strictly Eligible Exposed):
$$|I_{\text{available}}| = (|I_{\text{Irish}}| - |Q_{\text{Irish}}|) - |(E_1 \cup E_S) \cap (I_{\text{Irish}} \setminus Q)| = 92 - 14 = \mathbf{78}$$

#### Derivation B (Total Inventory Minus Deduplicated Exclusions):
$$\begin{aligned}
|I_{\text{excluded}}| &= |E_1 \cap I| + |E_S \cap I| + |Q \setminus (E_1 \cup E_S)| \\
&= 10 + 5 + 1 = \mathbf{16}
\end{aligned}$$
$$|I_{\text{available}}| = |I_{\text{Irish}}| - |I_{\text{excluded}}| = 94 - 16 = \mathbf{78}$$

Both derivations yield **$78$ available speakers**. The overlap speaker (`f3ea0447…`) is accounted for in $E_1$ ($10$ speakers) and is not double-subtracted.

---

## 3. Audit 2 — Verify Seed Formula, Scenario Indexing & Serialized Parameters

### 3.1 Code Inspection of `scripts/simulate_stage6m_power.py`
Inspection of [`scripts/simulate_stage6m_power.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/simulate_stage6m_power.py) lines 324–340 reveals the exact implementation:

```python
    joint_scenarios = [
        ("Scenario 1: Parity Preserved & Anticipated Benefit", -0.85, 0.00, 1, "Benign adaptation with zero disparity widening"),
        ("Scenario 2: Modest Disparity Drift & Anticipated Benefit", -0.85, 0.50, 2, "Benign adaptation with mild subgroup widening"),
        ("Scenario 3: Null Regime (Zero Benefit & Zero Disparity)", 0.00, 0.00, 3, "Null benchmark / static parity"),
        ("Scenario 4: Disparity Regression at Safety Boundary", -0.85, 1.40, 4, "Overall benefit with worst-group regression"),
    ]
...
        for name, true_delta, true_disp, sc_id, desc in joint_scenarios:
            np.random.seed(seed_discovery + cohort_n + sc_id * 1000)
```
Where line 52 defines `seed_discovery = 42`.

#### Mathematical Formulation & Index Convention:
1. **1-Based Code Formulation:**
   $$\\text{seed} = \\text{seed\\_discovery} + \\text{cohort\\_n} + 1000 \\cdot \\text{sc\\_id} = 42 + N + 1000 \\cdot \\text{sc\\_id}$$
   where $\text{sc\_id} \in \{1, 2, 3, 4\}$ is a **1-based scenario identifier**.
2. **Equivalent 0-Based Index Formulation:**
   If $\text{scenario\_idx} = \text{sc\_id} - 1 \in \{0, 1, 2, 3\}$:
   $$\\text{seed} = 1000 \\cdot \\text{scenario\\_idx} + 1042 + N$$

### 3.2 Verification of Serialized Seeds in `power_simulation_results.json`

| Cohort Size ($N$) | Scenario 1 Identifier (`sc_id=1`) | Scenario 1 Serialized Seed | Scenario 2 Identifier (`sc_id=2`) | Scenario 2 Serialized Seed | Serialized Status in JSON |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$N = 420$** | $1$ | $42 + 420 + 1000 = \mathbf{1462}$ | $2$ | $42 + 420 + 2000 = \mathbf{2462}$ | **VERIFIED** |
| **$N = 450$** | $1$ | $42 + 450 + 1000 = \mathbf{1492}$ | $2$ | $42 + 450 + 2000 = \mathbf{2492}$ | **VERIFIED** |
| **$N = 468$** | $1$ | $42 + 468 + 1000 = \mathbf{1510}$ | $2$ | $42 + 468 + 2000 = \mathbf{2510}$ | **VERIFIED** |
| **$N = 540$** | $1$ | $42 + 540 + 1000 = \mathbf{1582}$ | $2$ | $42 + 540 + 2000 = \mathbf{2582}$ | **VERIFIED** |

### 3.3 Verification of Serialized Scenario 2 Parameters ($N=468$ vs $N=540$)

| Simulation Parameter | $N = 468$ (`cohort_468`) | $N = 540$ (`cohort_540`) | Concordance Evaluation |
| :--- | :---: | :---: | :---: |
| **True WER Effect ($\Delta_R$)** | $-0.85\text{ pp}$ | $-0.85\text{ pp}$ | Identical |
| **True Disparity Shift ($\Delta D$)** | $+0.50\text{ pp}$ | $+0.50\text{ pp}$ | **Identical** |
| **Monte Carlo Trials ($S$)** | $4,000$ | $4,000$ | Identical |
| **Inner Bootstrap Resamples ($B$)** | $1,000$ | $1,000$ | Identical |
| **Random Seed ($S_1 / S_2$)** | $1510 / 2510$ | $1582 / 2582$ | Differ by cohort offset |
| **Joint Successes ($S_2$) / $4,000$** | **$3,433$** | **$3,616$** | Serialized count |
| **Estimated Joint Power ($\widehat{P}_{\text{S2}}$)** | **$85.825\%$** (half-up: **$85.83\%$**) | **$90.40\%$** | Serialized estimate |
| **95% Monte Carlo Confidence Interval** | **$[84.74\%, 86.91\%]$** | **$[89.49\%, 91.31\%]$** | Serialized bounds |
| **Rule A ($\widehat{P} \ge 85.00\%$)** | **PASS** ($85.83\% \ge 85.00\%$) | **PASS** ($90.40\% \ge 85.00\%$) | Both Pass |
| **Rule B ($L_{95\%} > 85.00\%$)** | **FAIL** ($84.74\% < 85.00\%$) | **PASS** ($89.49\% > 85.00\%$) | Separates at $N=540$ |

#### Statistical Tempering: Monte Carlo Variation vs. Sample-Size Effect
Because the random seed formula incorporates `+ cohort_n`, the simulations for $N=468$ (seed $2510$) and $N=540$ (seed $2582$) instantiate **independent pseudorandom streams**. 

> [!IMPORTANT]
> **Qualified Statistical Finding on Sample-Size Scaling:**  
> The simulations use identical specified data-generating process parameters ($\Delta_R = -0.85\text{ pp}, \Delta D = +0.50\text{ pp}, \sigma_{\text{spk}} = 3.80\text{ pp}, \rho = 0.88$). The observed power difference ($85.825\%$ at $N=468$ vs. $90.40\%$ at $N=540$) is consistent with sample-size scaling. However, because independent random seeds were used, the observed difference reflects **both sample-size scaling and Monte Carlo realization variation**. It must not be characterized as an exclusively isolated or "pure" sample-size effect.

---

## 4. Audit 3 — Verify Current Frozen-Artifact Baselines, Git Integrity & Simulation Provenance

Direct cryptographic hashing, Git object tree inspection, and line-ending normalization audits were performed across all baseline artifacts.

### 4.1 Tracked Artifacts: Raw Bytes vs. Normalized Content Comparison
On Windows platforms where Git is configured with `core.autocrlf = true`, working-tree checkouts convert LF line endings (`\n`) to CRLF line endings (`\r\n`). Consequently, working-tree files have a larger byte size ($+1\text{ byte}$ per line) and a different raw SHA-256 digest from the repository's internal Git blob.

To rigorously verify data integrity, every tracked baseline artifact was inspected for:
1. Physical disk size and physical SHA-256 digest.
2. CRLF count and absence of corrupting standalone CR characters (`\r` without `\n`).
3. Normalized disk size and normalized SHA-256 digest (computed by stripping `\r`).
4. Git commit blob retrieved directly via `git show HEAD:<path>`.
5. Git object SHA-1 identifier retrieved via `git rev-parse HEAD:<path>`.
6. Exact identity check between normalized disk byte streams and raw Git blob byte streams (`norm_disk == git_blob`).

| Tracked Artifact Path | Physical Disk Size / SHA-256 | CRLF Count / Standalone CR | Normalized Disk Size / SHA-256 | Git HEAD Blob Size / SHA-256 | Git Object ID (SHA-1) | Final Parity Finding |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | $557,100\text{ B}$<br>`e964799b50a84fa5...` | $6,906$<br>$0$ | $550,194\text{ B}$<br>`96534400161e9d7a...` | $550,194\text{ B}$<br>`96534400161e9d7a...` | `e327b481eea1...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) | $451,539\text{ B}$<br>`41cec79d913a96aa...` | $901$<br>$0$ | $450,638\text{ B}$<br>`56cb4f9fc7ab7b8b...` | $450,638\text{ B}$<br>`56cb4f9fc7ab7b8b...` | `d3e20c88ac91...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) | $92,340\text{ B}$<br>`665009a00660f7e9...` | $301$<br>$0$ | $92,039\text{ B}$<br>`612b7045e3e68326...` | $92,039\text{ B}$<br>`612b7045e3e68326...` | `e9eea418fa14...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) | $5,344\text{ B}$<br>`4622b215b18c6b4d...` | $77$<br>$0$ | $5,267\text{ B}$<br>`63a189fdefdb2595...` | $5,267\text{ B}$<br>`63a189fdefdb2595...` | `f49bec277f9b...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) | $39,689\text{ B}$<br>`c2a746db83e02e81...` | $121$<br>$0$ | $39,568\text{ B}$<br>`652e0fadc045dea8...` | $39,568\text{ B}$<br>`652e0fadc045dea8...` | `113685050722...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv) | $19,210\text{ B}$<br>`7c1659433b2b3539...` | $61$<br>$0$ | $19,149\text{ B}$<br>`8a3a7b0fff1fc013...` | $19,149\text{ B}$<br>`8a3a7b0fff1fc013...` | `f858ba45a7a6...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |

*Note:* In every tracked file, the byte size difference ($\text{Disk Size} - \text{Git Blob Size}$) equals the exact CRLF count, standalone CR count is strictly $0$, and `norm_disk == git_blob` evaluates to `True`.

### 4.2 Untracked Artifact Provenance: `power_simulation_results.json`
The canonical power simulation output artifact [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) was audited separately:
- **Physical Disk State:** Exact size **$253,229\text{ bytes}$**, SHA-256 **`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`**.
- **Tracking Status in Version Control:** The file is **untracked** in Git (`git status` reports untracked).
- **Search of Git Commit History:**
  - `git log -S 8fac4d32` yields zero commits containing this hash in Git commit diffs.
  - `git grep 8fac4d32 HEAD` confirms no tracked file in historical Git commits records this digest.
- **Working Tree Documentation Records:** The canonical digest `8fac4d32…` is recorded across active Stage 6M proposal artifacts ([`reports/stage6m/stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`reports/stage6m/stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md)).
- **Epistemic Classification & Provenance Qualification:**
  The current simulation JSON has the reported SHA-256 digest (`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`) and size ($253,229\text{ bytes}$), matching the previously recorded canonical digest. Its reported contents are consistent with the proposal tables. Because the JSON is untracked and no independent version-controlled historical digest record was located, its historical immutability and execution provenance remain **UNVERIFIED**. The file was **not** regenerated or re-run to settle this question.

### 4.3 Epistemic Distinction Between Four Integrity Claims
In accordance with the audit directive, four distinct claims are strictly separated:
1. **Raw Byte Equality:** **False** between disk and Git HEAD. Working-tree files on Windows differ in raw byte size and SHA-256 digest from Git repository blobs due to CRLF line endings.
2. **Text Equality After Newline Normalization:** **Established (True)** for all 6 tracked artifacts. Stripping `\r` produces a byte stream that is identical to the Git blob in length, byte sequence, and SHA-256 digest.
3. **Audited Baseline Working-Tree Status:** The six audited baseline paths have no reported working-tree modifications. The repository's overall working-tree status is a separate matter and may include changes to audit reports, the changelog, and newly created evidence files.
4. **Historical Non-Modification Qualification:**
   No intermediate committed changes were found in the inspected Git history. The current working-tree content matches the corresponding Git blob after line-ending normalization. These checks do not establish that no temporary, uncommitted edits occurred and were subsequently reverted. (For the untracked simulation JSON, historical immutability and execution provenance are UNVERIFIED because it lacks version-controlled lineage).

---

## 5. Audit 4 — Test Execution Evidence Verification

### 5.1 Verification of `test_execution_research_validity_v1_2_0.log`
Inspection of the execution log [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) confirms:
- **Command Invoked:** `python -m pytest tests/research_validity/ -v`
- **Collected & Passed Items:** **Exactly 113 tests**
- **Test Modules (12 Modules Total):**
  1. `test_historical_immutability.py` (7 tests)
  2. `test_label_isolation.py` (1 test)
  3. `test_model_role_registry.py` (11 tests)
  4. `test_prequential_stream.py` (5 tests)
  5. `test_seed_reproducibility.py` (1 test)
  6. `test_sentinel_contamination.py` (2 tests)
  7. `test_speaker_leakage.py` (2 tests)
  8. `test_stage3m_stream_audit.py` (39 tests)
  9. `test_stage4_invariants.py` (6 tests)
  10. `test_stage5_external_eval.py` (16 tests)
  11. `test_stage5m_online_control.py` (3 tests)
  12. `test_stage6m_protocol_proposal.py` (20 tests)
- **Reported Pytest Duration:** **$26.15\text{ seconds}$** (outer subprocess wall-clock: $30.34\text{ seconds}$)
- **Exit Status:** **0 (PASS)**
- **Log SHA-256 Digest:** `2651a05b864e49b7f19e9b6af6fc50f0fe8eb28f547d248b2522a226758391fa` ($16,494\text{ bytes}$)

### 5.2 Forensic Classification of Pytest Warnings vs. Process Stderr Diagnostics
Inspection of lines 124–154 of the log reveals an exact boundary between counted pytest warnings and process-level stderr diagnostics:

#### Category A: Pytest Warnings (Counted in Pytest Summary: Exactly 6 Warnings)
These warnings were intercepted by pytest's warning capture mechanism and appear in the `=== warnings summary ===`:
1. `torchvision/transforms/_functional_pil.py:245`: `DeprecationWarning: BILINEAR is deprecated and will be removed in Pillow 10 (2023-07-01). Use Resampling.BILINEAR instead.`
2. `torchvision/transforms/_functional_pil.py:291`: `DeprecationWarning: NEAREST is deprecated and will be removed in Pillow 10 (2023-07-01). Use Resampling.NEAREST or Dither.NONE instead.`
3. `torchvision/transforms/_functional_pil.py:307`: `DeprecationWarning: NEAREST is deprecated and will be removed in Pillow 10 (2023-07-01). Use Resampling.NEAREST or Dither.NONE instead.`
4. `torchvision/transforms/_functional_pil.py:324`: `DeprecationWarning: BICUBIC is deprecated and will be removed in Pillow 10 (2023-07-01). Use Resampling.BICUBIC instead.`
5. `<frozen importlib._bootstrap>:241`: `DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute`
6. `<frozen importlib._bootstrap>:241`: `DeprecationWarning: builtin type SwigPyObject has no __module__ attribute`

#### Category B: Process Stderr Diagnostics (Not Counted in Pytest 6 Warnings Summary)
These diagnostics were emitted directly to process standard error during interpreter startup and C-extension module loading before or outside pytest's warning capture filter (recorded under `=== STDERR ===` in the execution log):
1. `requests/__init__.py:113`: `RequestsDependencyWarning: urllib3 (1.26.12) or chardet (7.4.3)/charset_normalizer (2.1.1) doesn't match a supported version!`
2. `sys:1`: `DeprecationWarning: builtin type swigvarlink has no __module__ attribute`

**Summary of Provenance:** All eight messages are attributed to third-party dependencies or runtime diagnostics. No project-code origin was identified in the inspected log.


### 5.3 Methodological Boundary: Test Pass vs. Scientific Validity
Passing all 113 unit and research-validity tests verifies:
1. Software contracts, set arithmetic, data disjointness invariants, and configuration parsing function as coded.
2. Historical manifests remain immutable and uncorrupted.
3. Power simulation output tables synchronize with the serialized JSON.

> [!CRITICAL]
> **Scientific Validity Boundary:**  
> Test suite passage does **NOT** validate the scientific hypotheses of Stage 6M, does **NOT** validate the single-source Gaussian data-generating model for multi-corpus extrapolation, and does **NOT** constitute authorization for confirmatory execution.

---

## 6. Audit 5 — Preservation of All GO/NO-GO Prerequisites

Confirmatory execution remains strictly prohibited by the five unfulfilled prerequisites:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CONFIRMATORY EXECUTION GATE: [LOCKED]                                     │
├────────────────────────────────────────┬───────────────────┬───────────────────────────────────────────┤
│ Prerequisite Dimension                 │ Status            │ Epistemic / Governance Requirement        │
├────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────┤
│ 1. Formal Supervisor Preregistration   │ UNAPPROVED        │ Written sign-off on protocol ADR-005      │
├────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────┤
│ 2. Final Sample Size Selection         │ UNFROZEN          │ Formal decision on N=468 vs N=540         │
├────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────┤
│ 3. Reserve-Policy Preregistration      │ UNRESOLVED        │ Selection of Policy A vs Policy B         │
├────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────┤
│ 4. External Speech Corpus Acquisition  │ BLOCKED           │ Physical acquisition of 102/162 speakers  │
├────────────────────────────────────────┼───────────────────┼───────────────────────────────────────────┤
│ 5. Multi-Corpus Hierarchical Power     │ REQUIRED          │ Power validation incorporating sigma_corp │
└────────────────────────────────────────┴───────────────────┴───────────────────────────────────────────┘
```

**Confirmatory Verdict:** **STRICT NO-GO**.

---

## 7. Deliverable File Inventory

### 1. New Evidence Artifacts Created:
- [`reports/stage6m/stage6m_residual_evidence_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_residual_evidence_audit.md): This report (comprehensive residual audit artifact).
- [`reports/stage6m/git_normalization_verification_v1_2_0.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/git_normalization_verification_v1_2_0.txt): Complete machine-readable normalization verification log with full SHA-256 digests and Git blob IDs (SHA-256 `fa898d76e808...`, size $6,134\text{ bytes}$).
- [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log): Full terminal output for 113 tests in 26.15s (SHA-256 `2651a05b…`).
- [`scratch/audit_irish_clips.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scratch/audit_irish_clips.py): Clip-level audit script for Irish speakers in `validated.tsv`.
- [`scratch/audit_baselines_git.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scratch/audit_baselines_git.py): Git object hash and CRLF line-ending verification script.
- [`scratch/run_full_research_validity_suite.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scratch/run_full_research_validity_suite.py): Subprocess test runner capturing stdout, stderr, and timings.

### 2. Reports Updated:
- [`reports/stage6m/stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md): Appended Correction 18 documenting residual evidence audit completion.
- [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md): Synchronized cryptographic tables with exact physical byte counts and test suite provenance.

### 3. Preserved Baseline Files Status:
The six audited baseline paths have no reported working-tree modifications, and their normalized contents match the corresponding Git blobs. This does not establish that no temporary, uncommitted edits occurred and were subsequently reverted.
- [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) (SHA-256 `8fac4d32…`, size $253,229\text{ B}$; execution provenance and historical immutability remain UNVERIFIED).
- [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) (Physical disk size $557,100\text{ B}$, SHA-256 `e964799b…`; normalized LF size $550,194\text{ B}$, SHA-256 `96534400…`).
- [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) (Physical disk size $451,539\text{ B}$, SHA-256 `41cec79d…`; normalized LF size $450,638\text{ B}$, SHA-256 `56cb4f9f…`).
- [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) (Physical disk size $92,340\text{ B}$, SHA-256 `665009a0…`; normalized LF size $92,039\text{ B}$, SHA-256 `612b7045…`).
- [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) (Physical disk size $5,344\text{ B}$, SHA-256 `4622b215…`; normalized LF size $5,267\text{ B}$, SHA-256 `63a189fd…`).
- [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) and [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv).
- [`tests/research_validity/test_stage6m_protocol_proposal.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/tests/research_validity/test_stage6m_protocol_proposal.py) (SHA-256 `dddaf866…`).
- All audio files and raw recording directories.

---

## 8. Supplemental Addendum: Final Integrity Wording, Simulation Provenance & Warning Diagnostics Correction

This supplemental addendum directly addresses the five specific tasks mandated by the supervisor's technical review:

### 8.1 Task 1 — Rectification of Git-Integrity Terminology & Normalization Proof
The previous draft erroneously used the phrase "byte-for-byte match with Git HEAD" to describe working-tree files whose physical byte count exceeded the repository blob size due to CRLF line endings on Windows (`core.autocrlf = true`). 

To eliminate any ambiguity, every tracked baseline artifact was re-evaluated by comparing raw disk bytes, normalized disk bytes (stripping `\r`), and raw Git commit blobs retrieved directly via `git show HEAD:<path>`:

```
Command executed:
python -c "
import subprocess, hashlib
git_blob = subprocess.check_output(['git', 'show', f'HEAD:{path}'])
norm_disk = open(path, 'rb').read().replace(b'\r\n', b'\n')
assert norm_disk == git_blob
"
```

#### Complete Tracked Baseline Audit Table:
| Baseline Artifact Path | Raw Working-Tree Size | Raw Working-Tree SHA-256 | CRLF Count | Standalone CR (`\r` without `\n`) | Normalized Size (LF) | Normalized SHA-256 Digest | Git Commit Blob Size | Git Commit Blob SHA-256 | Git Object ID (SHA-1) | Final Parity Finding |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- | :---: | :--- | :--- | :--- |
| [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv) | $557,100\text{ B}$ | `e964799b50a8...` | $6,906$ | $0$ | $550,194\text{ B}$ | `96534400161e...` | $550,194\text{ B}$ | `96534400161e...` | `e327b481eea1...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv) | $451,539\text{ B}$ | `41cec79d913a...` | $901$ | $0$ | $450,638\text{ B}$ | `56cb4f9fc7ab...` | $450,638\text{ B}$ | `56cb4f9fc7ab...` | `d3e20c88ac91...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_sentinel_panel.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel.csv) | $92,340\text{ B}$ | `665009a00660...` | $301$ | $0$ | $92,039\text{ B}$ | `612b7045e3e6...` | $92,039\text{ B}$ | `612b7045e3e6...` | `e9eea418fa14...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage5_sentinel_panel_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_sentinel_panel_manifest.json) | $5,344\text{ B}$ | `4622b215b18c...` | $77$ | $0$ | $5,267\text{ B}$ | `63a189fdefdb...` | $5,267\text{ B}$ | `63a189fdefdb...` | `f49bec277f9b...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/stage4_characterization.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage4_characterization.csv) | $39,689\text{ B}$ | `c2a746db83e0...` | $121$ | $0$ | $39,568\text{ B}$ | `652e0fadc045...` | $39,568\text{ B}$ | `652e0fadc045...` | `113685050722...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |
| [`datasets/splits/calibration.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/calibration.csv) | $19,210\text{ B}$ | `7c1659433b2b...` | $61$ | $0$ | $19,149\text{ B}$ | `8a3a7b0fff1f...` | $19,149\text{ B}$ | `8a3a7b0fff1f...` | `f858ba45a7a6...` | **Text content matches the Git version after line-ending normalization; raw byte representations differ because of newline conversion.** |

#### Strict Epistemic Boundaries:
1. **Raw Byte Equality:** **False**. The physical working-tree files and Git commit blobs differ in raw byte size and SHA-256 digest because of CRLF translation.
2. **Normalized Text Equality:** **Established (True)**. In all 6 files, the difference between physical size and blob size matches the CRLF count exactly, standalone CR count is strictly zero, and normalized disk bytes equal Git blob bytes 100%.
3. **Audited Baseline Working-Tree Status:** The six audited baseline paths have no reported working-tree modifications. The repository's overall working-tree status is a separate matter and may include changes to audit reports, the changelog, and newly created evidence files.
4. **Historical Non-Modification Qualification:** No intermediate committed changes were found in the inspected Git history. The current working-tree content matches the corresponding Git blob after line-ending normalization. These checks do not establish that no temporary, uncommitted edits occurred and were subsequently reverted.

---

### 8.2 Task 2 — Untracked Simulation JSON Provenance Qualification
The canonical power simulation results file [`reports/stage6m/power_simulation_results.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/power_simulation_results.json) was audited for provenance:
- **Physical Verification:** Exact byte size $253,229\text{ bytes}$, SHA-256 `8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`.
- **Git Tracking Status:** The file is **untracked** in Git (`git status` reports untracked).
- **Git History Search:** `git log -S 8fac4d32` yields zero commits. `git grep 8fac4d32 HEAD` confirms no tracked file in historical Git commits contains this digest.
- **Working Tree Documentation:** The canonical digest `8fac4d32…` was first established and documented during Stage 6M v1.2.0 proposal drafting across [`stage6m_protocol_proposal.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_protocol_proposal.md), [`stage6m_power_analysis.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_power_analysis.md), [`stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md), and [`stage6m_v1_2_0_changelog.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_v1_2_0_changelog.md).
- **Epistemic Classification & Provenance Qualification:**
  The current simulation JSON has the reported SHA-256 digest (`8fac4d32d5f86ba12aa43228f3ad0c4e2c700c7182781518379439962cbe20ad`) and size ($253,229\text{ bytes}$), matching the previously recorded canonical digest. Its reported contents are consistent with the proposal tables. Because the JSON is untracked and no independent version-controlled historical digest record was located, its historical immutability and execution provenance remain **UNVERIFIED**.
- **Protocol Governance Action:** The simulation JSON was **NOT regenerated, re-run, or modified**. Its execution provenance and historical immutability remain formally recorded as **UNVERIFIED**, while its current physical integrity is preserved.

---

### 8.3 Task 3 — Forensic Warning and Diagnostics Classification
Inspection of [`reports/stage6m/test_execution_research_validity_v1_2_0.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/test_execution_research_validity_v1_2_0.log) lines 124–154 reveals the exact provenance of all diagnostics:

1. **Counted Pytest Warnings (Category A — Exactly 6 Warnings in Pytest Summary):**
   - 4 deprecation warnings in `torchvision/transforms/_functional_pil.py:245, 291, 307, 324` (`BILINEAR/NEAREST/BICUBIC deprecated in Pillow 10`).
   - 2 deprecation warnings in `<frozen importlib._bootstrap>:241` (`builtin type SwigPyPacked / SwigPyObject has no __module__ attribute`).
2. **Process Stderr Diagnostics (Category B — Not Counted in Pytest 6 Warnings Summary):**
   - 1 `RequestsDependencyWarning` in `requests/__init__.py:113` (`urllib3 (1.26.12) or chardet (7.4.3)/charset_normalizer (2.1.1) doesn't match a supported version!`).
   - 1 interpreter startup `DeprecationWarning` in `sys:1` (`builtin type swigvarlink has no __module__ attribute`).
3. **Provenance Finding:** All eight messages are attributed to third-party dependencies or runtime diagnostics. No project-code origin was identified in the inspected log.

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
    $$|I_{\text{available}}| = 92 - 14 = \mathbf{78}$$
    $$|I_{\text{available}}| = 94 - (10 + 5 + 1) = \mathbf{78}$$
- **Clip-Level Quality Progression:**
  - Speaker `f3ea0447…`: $16\text{ raw rows} - 1\text{ baseline exclusion (`'Cllr.'`)} = 15\text{ baseline clips}$; $15 - 2\text{ strict exclusions (`down_votes = 2`)} = 13\text{ strict clips} < 15$. (Exclusion is baseline $+1$, strict $+2$; single-word clip excluded before baseline inventory).
  - Speaker `fc22fd45…`: $15\text{ raw rows} - 0\text{ baseline exclusions} = 15\text{ baseline clips}$; $15 - 1\text{ strict exclusion (`down_votes = 2`)} = 14\text{ strict clips} < 15$.
- **Simulation Seed Formula & Power Qualification:**
  - Formula from `scripts/simulate_stage6m_power.py` line 340: $\\text{seed} = 42 + N + 1000 \\cdot \\text{sc\\_id}$ with 1-based $\\text{sc\\_id} \\in \\{1, 2, 3, 4\\}$.
  - Seeds: $N=420 \to 1462 / 2462$; $N=450 \to 1492 / 2492$; $N=468 \to 1510 / 2510$; $N=540 \to 1582 / 2582$.
  - Power difference qualification: The simulations use different seed initializations and therefore different pseudorandom sequences. The observed power difference ($85.83\%$ at $N=468$ vs. $90.40\%$ at $N=540$) reflects **both sample-size effects and Monte Carlo realization variation** (not an exclusively isolated "pure sample-size effect").
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
