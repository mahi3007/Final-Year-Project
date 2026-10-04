# Stage 5A Sentinel Panel Preflight Audit Report (Revised)

**Document Identifier:** `reports/stage5/stage5a_sentinel_preflight.md`  
**Date of Audit:** 2026-10-02  
**Project:** DSG-CTTA (Dynamic Spatial-Group Continual Test-Time Adaptation)  
**Stage:** Stage 5A — Disparity Safety Gate (DSG) Controller Implementation  
**Governing Standard:** ADR-005, Stage 5 Protocol Amendment, Master Task Specification  
**Preflight Outcome:** `PASS (OPTION 3 EXPANDED SENTINEL PANEL RATIFIED & LOCKED)`

---

## 1. Executive Summary & Resolution

In the initial Phase A preflight audit, the historical sentinel panel (`sentinel_candidates.csv`) was found to contain only $k_g = 1$ speaker per stratum (6 speakers total), causing paired speaker-cluster bootstrap at the stratum level to degenerate ($df = 0$, with groups omitted in $33.49\%$ of resamples). 

Following formal submission to the Principal Investigator, **RESOLUTION: OPTION 3 (Expand the Sentinel Panel)** was authorized:
- Do NOT switch to utterance-level bootstrap.
- Do NOT replace group-level UCB with point estimates.
- Expand the sentinel panel to the preferred target of **5 independent speakers per stratum (30 speakers total, 300 clips)**.
- Enforce strict mutual disjointness:
  $$\mathcal{S}_{\text{adapt}} \cap \mathcal{S}_{\text{cal}} \cap \mathcal{S}_{\text{sentinel}} \cap \mathcal{S}_{\text{eval}} = \emptyset$$
- Selection executed model-blind and deterministically from Mozilla Common Voice 27.0 (`validated.tsv`).

The revised sentinel panel has been curated, verified, and cryptographically locked at:
- **Canonical Split CSV:** `datasets/splits/stage5_sentinel_panel.csv`
- **Manifest:** `datasets/splits/stage5_sentinel_panel_manifest.json`
- **Cryptographic Lock:** `datasets/splits/stage5_sentinel_panel.lock.json`

With $k_g = 5$ independent clusters per stratum, group-level degrees of freedom are restored ($df = 4$ per stratum), between-speaker uncertainty is fully estimable, and the probability of an omitted group under stratified paired cluster bootstrap is **strictly 0.00%**. The sentinel preflight audit status is formally upgraded to **`PASS`**.

---

## 2. Expanded Sentinel Panel Composition

The canonical sentinel dataset is defined in `datasets/splits/stage5_sentinel_panel.csv`.

### 2.1 Demographic & Stratum Breakdown

| Demographic Stratum (`stage5_accent_group`) | Stratum Code | Eligible Speaker Pool | Sampled Speakers | Clips / Speaker | Total Clips | Total Reference Words |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | `australia` | 388 | 5 | 10 | 50 | 448 |
| **Canadian English** | `canada` | 501 | 5 | 10 | 50 | 436 |
| **England English** | `england` | 1,203 | 5 | 10 | 50 | 451 |
| **Irish English** | `ireland` | 83 | 5 | 10 | 50 | 429 |
| **South Asian English** | `south_asian` | 736 | 5 | 10 | 50 | 462 |
| **US English** | `us` | 3,874 | 5 | 10 | 50 | 455 |
| **TOTAL** | **6 Strata** | **6,785** | **30 Speakers** | **10 Clips** | **300 Clips** | **2,681 Words** |

- **Total Sentinel Speakers ($K$):** Exactly 30.
- **Speakers Per Accent Group ($k_g$):** Exactly 5 independent speakers per stratum.
- **Clips Per Speaker:** Exactly 10 validated clips.
- **Total Sentinel Audio Clips:** Exactly 300 clips.

---

### 2.2 Mutual Disjointness & Air-Gapping Matrix

| Partition Audited | Path | Overlap with Sentinel Panel ($\mathcal{S}_{\text{sentinel}} \cap \mathcal{S}_{\text{partition}}$) | Status |
| :--- | :--- | :---: | :---: |
| **Calibration Set** | `datasets/splits/calibration.csv` | $\emptyset$ (0 / 30 speakers) | ✅ **PASS (Air-Gapped)** |
| **Development Set** | `datasets/splits/development.csv` | $\emptyset$ (0 / 30 speakers) | ✅ **PASS (Air-Gapped)** |
| **Historical Test Set** | `datasets/splits/final_test.csv` | $\emptyset$ (0 / 30 speakers) | ✅ **PASS (Air-Gapped)** |
| **Stage 5 External Eval** | `datasets/splits/stage5_external_eval.csv` | $\emptyset$ (0 / 30 speakers) | ✅ **PASS (Air-Gapped)** |
| **Primary L2-ARCTIC** | `datasets/primary/audio/` | $\emptyset$ (0 / 24 speakers) | ✅ **PASS (Air-Gapped)** |

**Air-Gapping Invariant:**
$$\mathcal{S}_{\text{sentinel}} \cap \mathcal{S}_{\text{eval}} = \emptyset, \quad \mathcal{S}_{\text{sentinel}} \cap \mathcal{S}_{\text{cal}} = \emptyset, \quad \mathcal{S}_{\text{sentinel}} \cap \mathcal{S}_{\text{adapt}} = \emptyset$$
Zero leakage across all partitions.

---

## 3. Mathematical Verification of Group-Level Paired Speaker-Cluster Bootstrap

### 3.1 Stratified Cluster Resampling
To enforce the protocol invariant ("*Require zero omitted groups across bootstrap replicates*"):
- For each bootstrap replicate $b \in \{1, \dots, B\}$ ($B=1,000$):
  - For each stratum $g \in \{1, \dots, 6\}$:
    - Sample $k_g = 5$ speaker clusters **with replacement** from stratum $g$'s 5 sentinel speakers $\mathcal{S}_g = \{s_{g,1}, \dots, s_{g,5}\}$.
- **Omitted Group Probability:**
  $$P(\text{Stratum } g \text{ omitted}) \equiv 0.0000 \quad \text{for all } g \in G$$
  Across all $B=1,000$ replicates, zero empty groups can occur.

### 3.2 Degrees of Freedom & Estimability
- Within each stratum $g$, resampling among $k_g = 5$ independent speakers provides $5^5 = 3,125$ distinct cluster configurations per group.
- Between-speaker variance $\sigma^2_{\text{speaker}|g}$ is non-degenerate ($df = 4$).
- The empirical 95th percentile Upper Confidence Bound:
  $$\text{UCB}_{95}\left(\max_g \Delta_g\right)$$
  captures both within-group between-speaker variance and simultaneous worst-case group selection across all 6 strata.

---

## 4. Preflight Determination: PASS

| Item | Requirement | Observed / Verified | Status |
| :--- | :--- | :---: | :---: |
| **Sentinel Speakers** | $\ge 18$ ($k_g \ge 3$), preferred 30 ($k_g \ge 5$) | Exactly 30 speakers ($k_g = 5$) | ✅ **PASS** |
| **Stratum Representation** | All 6 Stage-5 evaluation strata represented | Exactly 6 strata, 5 spks/stratum | ✅ **PASS** |
| **Speaker Independence** | 0 overlap with cal, dev, adapt, and ext eval | 0 overlapping speakers (100% disjoint) | ✅ **PASS** |
| **Model Blindness** | No selection based on WER/CER/disparity | Deterministic seeded selection | ✅ **PASS** |
| **Group-Level Estimability** | Non-degenerate cluster bootstrap ($df > 0$) | $df = 4$ per group, 0 omitted groups | ✅ **PASS** |
| **Reproducibility** | Manifest & Cryptographic Lock generated | Manifest & Lock committed | ✅ **PASS** |

### Preflight Audit Verdict: **`PASS`**

Stage 5A is formally **UNBLOCKED** to proceed with:
- **Phase B:** Frozen Config (`configs/stage5_gate_config.json`)
- **Phase C:** Controller Architecture (`src/dsg_ctta/controller/`)
- **Phase D:** Paired Speaker-Cluster Bootstrap
- **Phase E–J:** Fail-closed semantics, unit/synthetic tests, replay, and final readiness guard.
