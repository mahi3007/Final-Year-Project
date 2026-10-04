# Stage 5 Data Feasibility & Speaker Allocation Audit

**Protocol Version:** `v1.0.0-canonical`  
**Evaluation Scope:** Mathematical Feasibility of Five-Way Speaker Separation in L2-ARCTIC  
**Date:** 2026-09-30  
**Artifact Dependencies:** `datasets/splits/`, `configs/stage4_thresholds.json`, `reports/stage4/stage5_data_allocation_plan.md`  
**Audit Status:** `FAIL — REMEDIATION REQUIRED`

---

## 1. Executive Audit Finding

The Stage 5 data allocation proposed in `reports/stage4/stage5_data_allocation_plan.md` contains a critical methodological violation:
$$\mathcal{S}_{\text{calibration}} \cap \mathcal{S}_{\text{evaluation}} = \{\text{HJK}, \text{HKK}, \text{MPXM}, \text{SKA}, \text{TNI}, \text{TNT}\} \quad (100\% \text{ speaker overlap})$$

The six speakers designated for the Stage 5 Final Holdout Evaluation partition ($\mathcal{S}_{\text{eval}}$) were previously used to:
1. Calibrate the empirical bootstrap standard deviations ($\sigma_{\Delta_R}, \sigma_{\Delta_D}, \sigma_{\max_g \Delta_g}$) that derived $\delta_G = 2.00\%$ and $\delta_D = 2.00\%$.
2. Run the window size granularity sweep ($K \in \{1, 4, 5, 10\}$) that established $K=4$ as the primary operating point.
3. Observe CTC blank-token collapse dynamics in the $K$-sweep provenance analysis.

Evaluating the final Stage 5 controller on these exact calibration speakers creates a circular evaluation dependency, violating the fundamental protocol invariant:
$$\boxed{\mathcal{S}_{\text{calibration}} \cap \mathcal{S}_{\text{evaluation}} = \emptyset}$$

---

## 2. Mathematical Proof of Infeasibility within L2-ARCTIC Alone

Let $\mathcal{C}$ denote the complete L2-ARCTIC corpus:
- **Total Speakers:** $|\mathcal{C}| = 24$ independent speakers.
- **Accent Groups ($G$):** Exactly 6 groups (`Arabic`, `Hindi`, `Korean`, `Mandarin`, `Spanish`, `Vietnamese`).
- **Group Capacity:** Exactly $n_g = 4$ independent speakers per group (2 Male, 2 Female).

Stage 5 controller validation requires five distinct partitions, each requiring representation from all 6 accent groups to evaluate subgroup regressions ($\max_g \Delta_g$) and disparity ($D = \max_g WER_g - \min_g WER_g$):
1. $\mathcal{S}_{\text{dev}}$: Exploratory development and baseline verification ($k \ge 1$ spk/group = 6 speakers)
2. $\mathcal{S}_{\text{cal}}$: Parameter freezing and threshold calibration ($k \ge 1$ spk/group = 6 speakers)
3. $\mathcal{S}_{\text{adapt}}$: Online prequential stream for unsupervised CTTA adaptation ($k \ge 1$ spk/group = 6 speakers)
4. $\mathcal{S}_{\text{sentinel}}$: Labeled safety validation panel queried at each window ($k \ge 1$ spk/group = 6 speakers)
5. $\mathcal{S}_{\text{eval}}$: Untouched holdout stream for final offline intervention evaluation ($k \ge 1$ spk/group = 6 speakers)

### Total Speaker Requirement:
$$N_{\text{required}} = |\mathcal{S}_{\text{dev}}| + |\mathcal{S}_{\text{cal}}| + |\mathcal{S}_{\text{adapt}}| + |\mathcal{S}_{\text{sentinel}}| + |\mathcal{S}_{\text{eval}}| = 6 + 6 + 6 + 6 + 6 = 30 \text{ speakers}$$

### The Pigeonhole Constraint:
$$N_{\text{available}} = 24 < 30 = N_{\text{required}}$$
$$\forall g \in G, \quad n_g = 4 < 5 \text{ partitions}$$

**Theorem:** A 5-way partition satisfying mutual pairwise disjointness and balanced 6-group representation is **MATHEMATICALLY IMPOSSIBLE** using the 24-speaker L2-ARCTIC corpus alone.

---

## 3. Current Corpus Allocation Status

| Partition Name | Dataset File | Assigned Speaker IDs | Accent Balance | Primary Role |
| :--- | :--- | :--- | :---: | :--- |
| **Development** | `datasets/splits/development.csv` | `DTW`, `ERMS`, `LDC`, `NJS`, `PRK`, `YBAA` | 1/group (6 spk) | Baseline verification (Stage 1/2) |
| **Calibration** | `datasets/splits/calibration.csv` | `HJK`, `HKK`, `MPXM`, `SKA`, `TNI`, `TNT` | 1/group (6 spk) | Threshold & $K$ calibration (Stage 4) |
| **Stage 4 Characterization** | `datasets/splits/stage4_characterization.csv` | `ABA`, `ASI`, `BJM`, `BVT`, `BWC`, `EBVS`, `HCC`, `LXC`, `MBX`, `TLX`, `YDCK`, `ZHAA` | 2/group (12 spk) | Multi-order & stress audit (Stage 4) |

Notice that `Development` (6) + `Calibration` (6) + `Stage 4 Characterization` (12) = 24 speakers, completely exhausting the entire L2-ARCTIC corpus!

---

## 4. Remediation Options & Strategic Architecture

To enforce strict, uncompromised research validity, one of three architectural remediations must be executed:

### Strategy A: External Accented Corpus for Final Evaluation ($\mathcal{S}_{\text{eval}}$) — RECOMMENDED
- **Adaptation Stream ($\mathcal{S}_{\text{adapt}}$):** 6 L2-ARCTIC speakers (1/group, e.g. `ABA`, `BJM`, `EBVS`, `TLX`, `MBX`, `BVT`)
- **Sentinel Panel ($\mathcal{S}_{\text{sentinel}}$):** 6 L2-ARCTIC speakers (1/group, e.g. `ZHAA`, `ASI`, `HCC`, `BWC`, `YDCK`, `LXC`)
- **Final Evaluation ($\mathcal{S}_{\text{eval}}$):** Curate an external 6-group accented speech stream from **Mozilla Common Voice (en)** or **SpeechOcean762** matching the 6 accent demographics (`Arabic`, `Hindi`, `Korean`, `Mandarin`, `Spanish`, `Vietnamese`).
- **Scientific Merit:** Provides airtight speaker separation ($\mathcal{S}_{\text{cal}} \cap \mathcal{S}_{\text{eval}} = \emptyset$) AND evaluates whether the DSG controller generalizes across distinct recording environments and acoustic channels.

### Strategy B: External Accented Corpus for Sentinel Panel ($\mathcal{S}_{\text{sentinel}}$)
- Ingest an external frozen sentinel panel from Common Voice / Speech Commands / LibriSpeech accented subsets (6 speakers, 1/group).
- Allocate all 12 non-development/non-calibration L2-ARCTIC speakers to Adaptation (6) and Final Evaluation (6).
- **Scientific Merit:** Allows final evaluation to remain on pristine L2-ARCTIC audio while testing sentinel gating via an external benchmark panel.

### Strategy C: Cross-Validation Split Folding (Within L2-ARCTIC)
- If external datasets are disallowed, fold the evaluation into a 2-fold cross-characterization across the 12 non-dev/non-cal speakers:
  - Fold 1: Stream A adapts, Stream B acts as sentinel; offline test evaluates on held-out segments.
  - *Limitation:* Does not provide a 3rd distinct evaluation stream; requires utterance-level or session-level partitioning rather than clean speaker partitioning.

---

## 5. Formal Pre-Flight Verdict & Action Plan

$$\boxed{\textbf{PRE-FLIGHT STATUS: FAIL — STAGE 5 IMPLEMENTATION BLOCKED}}$$

1. **Blocking Condition:** Stage 5 controller coding cannot begin with the proposed recycling of calibration speakers into final evaluation.
2. **Immediate Remediation Required:**
   - Formal user agreement on whether Strategy A (External evaluation corpus) or Strategy B (External sentinel panel) will be ingested.
   - Preservation of existing L2-ARCTIC calibration splits without opportunistic reshuffling.
