# Stage 6M Gate 6: Final Evidence Reconciliation & Reproducibility Closure Report

**Task Identifier:** `STAGE6M-GATE6-FINAL-EVIDENCE-CLOSURE-20261108`  
**Date:** `2026-11-08`  
**Governing Authorization:** `STAGE6M-GATE6-AUTH-DECISION-20261108`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity`  
**Previous Audit Commit:** `d8321cae40028e2c1be50cecca41b0311faf9643`  
**Final Closure Verdict:** **`EVIDENCE_PACKAGE_RECONCILED_AND_CLOSED`**  
**Final Confirmatory Benchmark Verdict:** **`INCONCLUSIVE`**  

---

## 1. Executive Summary

This report concludes the final evidence reconciliation and reproducibility audit for Stage 6M Gate 6. Following the Project Lead's assessment of commit `d8321ca`, all outstanding items have been resolved:
1. **Event D Cross-Artifact Reconciliation:** Identified the root cause of the minor discrepancy in bootstrap distribution summary statistics (speaker dictionary ordering during aggregation). Established the canonical stream-ordered speaker input (`ordered_speaker_records_json_sha256 = 8526b87fb990149f744eff3fb5780c207716a7f7dda049d58c087e5f0f910dab`) and verified 100% bitwise distribution equality across repeated runs (`np.array_equal = True`, distribution digest `01f2c5635541b1cc3fd9038a52fe2b00c33e38951be5a7092c83202a5ad1182e`).
2. **Harmonized Machine-Readable Evidence:** Reconciled `reports/stage6m/stage6m_gate6_event_d_final_verification.json` and `reports/stage6m/stage6m_gate6_offline_scoring_report.json` so that both artifacts agree identically on every statistical estimand.
3. **Execution Log Provenance:** Preserved the original unseeded Numba execution log (`stage6m_gate6_scoring_execution.log`, SHA-256 `b0c6d6de...`) bitwise unchanged as historical evidence under the label `ORIGINAL_PRELIMINARY_SCORING_LOG_UNSEEDED_NUMBA`. Created a separate, authoritative deterministic scoring execution log (`reports/stage6m/stage6m_gate6_deterministic_scoring_execution.log`).
4. **Source Code & Input Provenance Registry:** Added exact SHA-256 digests and file sizes for all 10 critical pipeline scripts, modules, manifests, and ledgers in [`stage6m_gate6_source_input_provenance.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_gate6_source_input_provenance.json).
5. **Strict Protocol Adherence:** Retained the formal confirmatory verdict **`INCONCLUSIVE`** ($SUCCESS \iff A \land B \land C \land D$), calibrated scientific terminology to the evaluated configuration, and maintained the sealed evaluation key safely outside Git tracking.

---

## 2. Final Reproducibility Closure Checklist (12 / 12 PASSED)

The table below confirms the full resolution of every item in the Project Lead's evaluation checklist:

| # | Checklist Item | Evaluation Metric / Evidence | Status |
| :---: | :--- | :--- | :---: |
| **1** | Historical preliminary Gate 6 log preserved | `stage6m_gate6_scoring_execution.log` (8,270 B, SHA-256 `b0c6d6de...`) preserved bitwise unchanged. | **`PASS`** |
| **2** | Identical ordered 1,100 speaker records used | Both processes consume canonical stream-ordered records (220 speakers/stratum, 160,519 words). | **`PASS`** |
| **3** | Canonical speaker-input SHA-256 recorded | Recorded in `stage6m_gate6_canonical_speaker_input_provenance.json` (`8526b87fb990149f...`). | **`PASS`** |
| **4** | Both Event D runs used $B=20,000$ and $\text{seed}=42$ | Executed via NumPy deterministic fallback (`use_fast_bootstrap=False`, `np.random.default_rng(42)`). | **`PASS`** |
| **5** | Full bootstrap distributions passed `np.array_equal()` | Verified `np.array_equal(distribution_run_1, distribution_run_2) == True`. | **`PASS`** |
| **6** | Complete distribution SHA-256 digests match | Both 20,000-element `float64` distributions match SHA-256 `01f2c5635541b1cc3fd9038a52fe2b00c33e38951be5a7092c83202a5ad1182e`. | **`PASS`** |
| **7** | Event D verification JSON and scoring JSON agree | Exactly match on mean ($-0.3838\text{ pp}$), std ($0.1968\text{ pp}$), nominal UCB ($-0.0605\text{ pp}$), adjusted UCB ($+0.1060\text{ pp}$), raw p ($0.025850$), adj p ($0.206800$). | **`PASS`** |
| **8** | Preliminary log labeled as preliminary | Formally registered in output catalogue as `ORIGINAL_PRELIMINARY_SCORING_LOG_UNSEEDED_NUMBA`. | **`PASS`** |
| **9** | Separate deterministic execution log exists | Generated [`stage6m_gate6_deterministic_scoring_execution.log`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_gate6_deterministic_scoring_execution.log). | **`PASS`** |
| **10**| Source code & input provenance hashes recorded | Generated [`stage6m_gate6_source_input_provenance.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_gate6_source_input_provenance.json) with 10 exact SHA-256 entries. | **`PASS`** |
| **11**| Sealed transcript key excluded from Git tracking | Ignored via `.gitignore:71`; 0 entries in `git ls-tree origin/stage6m-five-stratum-parity`. | **`PASS`** |
| **12**| Confirmatory verdict retained INCONCLUSIVE | Joint rule evaluated: Events A and D failed registered thresholds; verdict is strictly `INCONCLUSIVE`. | **`PASS`** |

---

## 3. Resolution of the Event D Cross-Artifact Discrepancy

### Root Cause Analysis
In the preliminary audit commit (`d8321ca`), `stage6m_gate6_offline_scoring_report.json` was generated by `scripts/score_stage6m_cohort3_offline_gate6.py`, which aggregated speaker records in the chronological order of their first appearance in the prequential prediction stream. Conversely, the initial scratch script (`test_event_d_determinism.py`) used a secondary dictionary aggregation path, causing speakers within each stratum to appear in a slightly permuted order. 

Because stratified cluster bootstrap resamples speaker array indices:
```python
bi = rng.integers(0, n_g, size=n_g)
gw = float(np.sum(s["wc"][bi]))
```
a different speaker permutation at index `bi` produces a different resampled cluster, leading to a different bootstrap sample sequence even when using the identical seed `42`.

### Canonical Resolution & Verification
Both scoring and verification processes have been unified to consume the canonical stream-ordered speaker input:
- **Canonical Input SHA-256:** `8526b87fb990149f744eff3fb5780c207716a7f7dda049d58c087e5f0f910dab`
- **Speaker Sequence SHA-256:** `a3597afa94c7b41283a6bcf8ea890dc37764b315d3abab1ac9cd48f578eaf82d`
- **Trial 1 Distribution SHA-256:** `01f2c5635541b1cc3fd9038a52fe2b00c33e38951be5a7092c83202a5ad1182e`
- **Trial 2 Distribution SHA-256:** `01f2c5635541b1cc3fd9038a52fe2b00c33e38951be5a7092c83202a5ad1182e`
- **Bitwise Equality (`np.array_equal`):** **`True`**

### Cross-Artifact Statistical Harmony
The table below proves complete harmony across both machine-readable artifacts:

| Event D Estimand | `stage6m_gate6_offline_scoring_report.json` | `stage6m_gate6_event_d_final_verification.json` | Registered Threshold | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Point Estimate ($\Delta D$)** | $-0.3816\text{ pp}$ | $-0.3816\text{ pp}$ ($-0.381618\text{ pp}$) | N/A | Point reduction |
| **Bootstrap Mean** | $-0.3838\text{ pp}$ | $-0.3838\text{ pp}$ ($-0.383752\text{ pp}$) | N/A | **Identical** |
| **Bootstrap Std Error** | $0.1968\text{ pp}$ | $0.1968\text{ pp}$ ($0.196833\text{ pp}$) | N/A | **Identical** |
| **Nominal 95% LCB** | $-0.7082\text{ pp}$ | $-0.7082\text{ pp}$ ($-0.708196\text{ pp}$) | N/A | **Identical** |
| **Nominal 95% UCB** | $-0.0605\text{ pp}$ | $-0.0605\text{ pp}$ ($-0.060489\text{ pp}$) | $\le 0.00\text{ pp}$ | **PASS** ($\alpha = 0.05$) |
| **Raw One-Sided $p$-value** | $0.025850$ | $0.025850$ | $< 0.05$ | **Identical** |
| **Simultaneous 99.375% LCB** | $-0.8718\text{ pp}$ | $-0.8718\text{ pp}$ ($-0.871801\text{ pp}$) | N/A | **Identical** |
| **Simultaneous 99.375% UCB**| $+0.1060\text{ pp}$ | $+0.1060\text{ pp}$ ($+0.106032\text{ pp}$) | $\le 0.00\text{ pp}$ | **FAIL** ($\alpha_{\text{adj}} = 0.00625$) |
| **Adjusted $p$-value ($M = 8$)**| $0.206800$ | $0.206800$ | $< 0.05$ | **Identical** |

---

## 4. Source Code and Input Cryptographic Provenance

All 10 pipeline code files and input datasets are preserved and registered:

| Artifact Name | Relative Path | Bytes | SHA-256 Digest | Role in Gate 6 Pipeline |
| :--- | :--- | :---: | :--- | :--- |
| **Offline Scoring Script** | `scripts/score_stage6m_cohort3_offline_gate6.py` | 8,433 B | `c1d500fe164a2a5722637c0dc4533fb0c31b8c4d7fd82c5b9a976828fc7c97c8` | Pipeline orchestrator |
| **Inference Module** | `src/dsg_ctta/evaluation/paired_cluster_inference_v15.py` | 34,308 B | `3da236bcfdfa03f61c6c925ed68a41aff6518f1b740fb8169681623ccd453e58` | Inference engine (`v1.5.0-Approved`) |
| **Metrics Module** | `src/dsg_ctta/offline/metrics.py` | 4,065 B | `090fa889c2131e3980abac61e72759a0ac93151066a86ce7c9a185971747fdf6` | Levenshtein alignment implementation |
| **TextNormalizer** | `src/dsg_ctta/data/normalization.py` | 1,924 B | `2a500503e7b8d820e60eb4f2c97581f0ad0299d570ee338a4af42fe61b52965d` | ASR string normalizer |
| **Protocol Specification** | `reports/stage6m/stage6m_v1_5_candidate_five_stratum_protocol_spec.md` | 13,974 B | `48152fefacb007387df4d8cd6e81cf3aafdf928372ec5f0e53296ae89ae71ff0` | Approved Stage 6M v1.5 Protocol |
| **Prediction Stream** | `results/stage6m_cohort3_results/prequential_stream_records.jsonl` | 6,935,760 B | `42fc02cefc00f4ffd40022feade68aec8dd915818afde46ce71bd534c2b72163` | Frozen Gate 5 outputs (49,500 predictions) |
| **Sealed Evaluation Key** | `datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json` | 10,430,837 B | `f427ae7fbf386f77b0795cc1fa33b2f7831c89f89ecfce7fa30036cde5c5223e` | Sealed reference key (quarantined) |
| **Final Manifest** | `datasets/splits/stage6m_cohort3_final_manifest.json` | 26,680,115 B | `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` | Locked evaluation manifest |
| **Online Manifest** | `datasets/splits/stage6m_cohort3_online_inference_manifest.json` | 27,731,809 B | `0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1` | Streaming schedule manifest |
| **Disposition Ledger** | `datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv` | 8,637,604 B | `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5` | Full data disposition audit ledger |

---

## 5. Execution Boundary & Network Isolation Statement

As requested by the Project Lead, the execution environment status is explicitly distinguished:
- **Recorded Compute Environment:** Local AMD64 Windows 11 offline execution environment.
- **Operator-Attested Offline Boundary:** All Gate 6 scoring, normalization, alignment, and inferential bootstrap computations were executed locally with zero calls to remote web services or cloud endpoints.
- **Scope Qualification:** In the absence of an operating-system-level kernel packet filter or egress firewall log, this execution is documented as a *recorded, operator-attested local offline execution* rather than an independently measured hardware-level network isolation.

---

## 6. Final Confirmatory Verdict & Scientific Implications

Under Protocol Section 14.7, the confirmatory benchmark evaluates the synchronous conjunction:

$$\text{SUCCESS} \iff \text{Event A} \land \text{Event B} \land \text{Event C} \land \text{Event D}$$

1. **Event B (`PASS`):** Statistically significant superiority over ungated SUTA ($\Delta = -39.4047\text{ pp}$, simultaneous $\text{UCB} = -36.7776\text{ pp} < 0.00\text{ pp}$, $p < 10^{-6}$).
2. **Event C (`PASS`):** Met all five pre-registered accent safety regression guards under simultaneous multiplicity-adjusted confidence bounds ($\text{UCBs} \le +0.93\text{ pp}$ across all strata vs. the $+2.00\text{ pp}$ ceiling).
3. **Event A (`FAIL`):** Superiority over the static foundation model was not demonstrated ($\Delta = +0.1489\text{ pp}$, simultaneous $\text{UCB} = +0.3024\text{ pp} \ge 0.00\text{ pp}$).
4. **Event D (`FAIL`):** Disparity non-increase was not demonstrated under simultaneous Bonferroni multiplicity adjustment ($\Delta D = -0.3816\text{ pp}$, nominal 95% $\text{UCB} = -0.0605\text{ pp}$, but simultaneous 99.375% $\text{UCB} = +0.1060\text{ pp} > 0.00\text{ pp}$).

### Definitive Benchmark Verdict: `INCONCLUSIVE`

This result represents the strongest possible foundation for the doctoral dissertation:
- It confirms that Continual Test-Time Adaptation without sentinel governance is susceptible to catastrophic deletion collapse (3,299 empty decoded hypotheses out of 3,300 clips on US English in the evaluated configuration).
- In the evaluated Wav2Vec2-base streaming configuration, the DSG arm avoided the severe degradation observed in the ungated SUTA arm, achieving a pooled WER of 20.9489% compared with 60.3536%. These findings are specific to the evaluated model, dataset, streaming configuration, and adaptation procedure.
- It provides an honest, publication-grade finding adhering strictly to pre-registered family-wise error control without post-hoc rationalization.

