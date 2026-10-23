# Stage 6M Data Integrity & Exposure Audit: Speaker Disjointness & Manifest Provenance

**Protocol:** `v1.2.0-stage6m-proposal`  
**Governing Standard:** ADR-005  
**Document Status:** Formal Dataset Audit for Stakeholder Review  
**Governance State:** **HOLD — STRICTLY NOT AUTHORIZED**  
**Submission Date:** 2026-10-12  

---

## 1. Executive Summary & Exposure Classification

A critical methodological requirement for confirmatory speech research is distinguishing between **speaker-disjoint data** and **previously unexposed (virgin) evaluation data**. 

While this audit confirms that `stage5_external_eval.csv` has **zero speaker overlap** with the Sentinel Panel and earlier L2-ARCTIC development splits, archival evidence proves that this partition **was previously evaluated in historical Stage 5b and Stage 6**. Consequently, under strict scientific standards, `stage5_external_eval.csv` cannot be claimed as an untouched blind holdout; it is formally classified as a **Cross-Dataset Replication and Multi-Step Replay Benchmark**.

To resolve this issue decisively, Stage 6M adopts a formal **Two-Cohort Protocol Architecture**:
- **Cohort 1 (Replication & Multi-Step Replay Benchmark):** Evaluated on `stage5_external_eval.csv`. Replicates multi-step prequential adaptation, examines counterfactual states in the research vault, and evaluates whether the gate suppresses cumulative drift. Prior exposure in Stage 5b and historical Stage 6 is explicitly acknowledged. All findings are designated as **Replication & Replay claims**.
- **Cohort 2 (Primary Confirmatory Blind Benchmark):** A newly quarantined, unexposed partition (e.g. Common Voice 28.0+ English accent-balanced split, $N=60$ speakers) reserved for the **Primary Independent Confirmatory Claim**. Reference transcripts remain cryptographically locked and unopened until preregistered execution.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATASET INTEGRITY & EXPOSURE AUDIT                            │
├─────────────────────────┬──────────────────────┬──────────────────────┬─────────────────────┤
│ Dataset Partition       │ Speaker Disjointness │ Historical Exposure  │ Scientific Role     │
├─────────────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ COHORT 1:               │ |S_ext ∩ S_sent| = 0 │ Evaluated in Stage 5b│ CROSS-DATASET       │
│ stage5_external_eval.csv│ |S_ext ∩ S_dev| = 0  │ & Historical Stage 6 │ REPLICATION &       │
│ (N=60 speakers, 900 utt)│ Zero overlap proven  │                      │ REPLAY BENCHMARK    │
├─────────────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ Sentinel Panel:         │ |S_sent ∩ S_all| = 0 │ Sentinel runtime gate│ QUALIFIED SENTINEL  │
│ stage5_sentinel_panel.csv| Cryptographically lock│ for online decisions │ RUNTIME PANEL       │
│ (N=30 speakers, 300 utt)│ Zero overlap proven  │                      │                     │
├─────────────────────────┼──────────────────────┼──────────────────────┼─────────────────────┤
│ COHORT 2:               │ Required: New split  │ Zero prior exposure  │ PRIMARY CONFIRMATORY│
│ Virgin Confirmatory     │ |S_new ∩ S_all| = 0  │ Unopened blind split │ BLIND BENCHMARK     │
│ Holdout (e.g., CV 28.0+)│                      │ Transcripts locked   │                     │
└─────────────────────────┴──────────────────────┴──────────────────────┴─────────────────────┘
```

---

## 2. Actual Manifest Speaker Set-Intersection Audit

The speaker disjointness audit was conducted by extracting, normalizing, and comparing the literal set of unique `speaker_id` strings across all manifest files in `datasets/splits/`.

### 2.1 Speaker Normalization Rule
All speaker identifiers were normalized via:
$$\text{normalize}(s) = \operatorname{strip}(\operatorname{lower}(\operatorname{str}(s)))$$
to ensure casing discrepancies, leading/trailing whitespace, or platform-specific encoding do not mask identity overlap.

### 2.2 Pairwise Set Intersections ($|S_A \cap S_B|$)
Empirical verification of literal set intersections across all project manifests:

| Manifest A | Manifest B | $\lvert S_A \rvert$ | $\lvert S_B \rvert$ | Set Intersection $\lvert S_A \cap S_B \rvert$ | Overlap Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `stage5_external_eval.csv` | `stage5_sentinel_panel.csv` | 60 | 30 | **0** | **STRICTLY DISJOINT** |
| `stage5_external_eval.csv` | `stage4_characterization.csv` | 60 | 12 | **0** | **STRICTLY DISJOINT** |
| `stage5_external_eval.csv` | `calibration.csv` | 60 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_external_eval.csv` | `development.csv` | 60 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_external_eval.csv` | `final_test.csv` | 60 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_external_eval.csv` | `sentinel_candidates.csv` | 60 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_sentinel_panel.csv` | `stage4_characterization.csv` | 30 | 12 | **0** | **STRICTLY DISJOINT** |
| `stage5_sentinel_panel.csv` | `calibration.csv` | 30 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_sentinel_panel.csv` | `development.csv` | 30 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_sentinel_panel.csv` | `final_test.csv` | 30 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage5_sentinel_panel.csv` | `sentinel_candidates.csv` | 30 | 6 | **0** | **STRICTLY DISJOINT** |
| `stage4_characterization.csv` | `final_test.csv` | 12 | 6 | **6** (`aba`, `bjm`, `bvt`, `ebvs`, `mbx`, `tlx`) | **DOCUMENTED OVERLAP** |
| `stage4_characterization.csv` | `sentinel_candidates.csv` | 12 | 6 | **6** (`asi`, `bwc`, `hcc`, `lxc`, `ydck`, `zhaa`) | **DOCUMENTED OVERLAP** |

- **Empirical Proof:** $|S_{\text{external}} \cap S_{\text{sentinel}}| = 0$ is mathematically verified on literal speaker strings.
- **Stage 4 Construction Confirmed:** The 12 speakers in `stage4_characterization.csv` consist exactly of the 6 `final_test` speakers plus the 6 `sentinel_candidates` speakers from L2-ARCTIC.
- **Status:** `VERIFIED FROM ARTIFACT`.

---

## 3. Provenance & Historical Exposure History of `stage5_external_eval.csv`

Archival inspection traces the complete lifecycle of `stage5_external_eval.csv`:

1. **Creation (Phase 3 Curation):** Materialized via `scripts/phase3_external_eval_curation.py` from Mozilla Common Voice 27.0 English corpus, generating 900 clips across 60 speakers (10 speakers per accent stratum, 15 clips per speaker).
2. **Prior Experimental Runs:**
   - Evaluated in `scripts/run_stage5b_external_eval.py` (preflight streaming validation).
   - Evaluated in historical Stage 6 (`scripts/stage6/02_run_model.py`), generating `reports/stage6/eight_model_benchmark.csv`.
3. **Implications for Stage 6M:**
   Because baseline error rates, SUTA adaptation outcomes, and DSG acceptance rates were logged on this exact dataset in historical Stage 6, it cannot be represented as an unexposed, virgin confirmatory holdout.
   - **Formally Reclassified:** `stage5_external_eval.csv` is designated as the **Cross-Dataset Replication & Multi-Step Replay Benchmark**.
   - **Untouched Holdout Requirement:** If stakeholders require an unexposed blind confirmatory test, an untouched partition (e.g., from Common Voice 28.0 or LibriCSS) must be curated and quarantined before testing.
- **Status:** `VERIFIED FROM ARTIFACT`.

---

## 4. Accent Categorization & Demographic Provenance

The 6 accent groups in `stage5_external_eval.csv` are derived from self-reported demographic metadata in Mozilla Common Voice 27.0:
1. `US English` ($N=10$ speakers, 150 clips)
2. `England English` ($N=10$ speakers, 150 clips)
3. `South Asian English` ($N=10$ speakers, 150 clips)
4. `Australian English` ($N=10$ speakers, 150 clips)
5. `Canadian English` ($N=10$ speakers, 150 clips)
6. `Irish English` ($N=10$ speakers, 150 clips)

### Methodological Limitations of Group Categories
- **Self-Reported Origin:** Accent labels reflect self-reported regional and L1 associations, not standardized phonetic or sociolinguistic measurements.
- **Broad Macro-Categories:** Labels such as "South Asian English" encompass diverse linguistic backgrounds (e.g., Hindi, Tamil, Bengali L1 influences).
- **Research Scope:** These groups provide operational strata for evaluating subgroup regression and disparity metrics ($\Delta D$), but do not represent biologically or phonetically isolated causal categories.
- **Status:** `PROPOSED & DOCUMENTED`.

---

## 5. Audit Trail & Claim Status

| Claim / Component | Description | Status | Evidence Reference |
| :--- | :--- | :---: | :--- |
| **$\lvert S_{\text{ext}} \cap S_{\text{sent}} \rvert = 0$** | Exact speaker set intersection is empty | `VERIFIED FROM ARTIFACT` | Section 2.2 intersection table |
| **$\lvert S_{\text{ext}} \cap S_{\text{L2-ARCTIC}} \rvert = 0$** | Zero overlap with all L2-ARCTIC splits | `VERIFIED FROM ARTIFACT` | Section 2.2 intersection table |
| **Historical Exposure** | Evaluated in Stage 5b and historical Stage 6 | `VERIFIED FROM ARTIFACT` | `reports/stage6/eight_model_benchmark.csv` |
| **Replication Classification** | Reclassified from virgin holdout to replication split | `PROPOSED & FORMALIZED` | Section 3 |
| **Demographic Limitations** | Self-reported regional categories, not phonetic isolates | `PROPOSED & DOCUMENTED` | Section 4 |
