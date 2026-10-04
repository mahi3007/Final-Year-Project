# Stage 4A: Data Scale & Statistical Power Feasibility Report (Revised — Option D Hybrid)

**Project Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition  
**Protocol Version:** `v1.0.0-canonical`  
**Phase:** Stage 4A (Data-Scale Inspection & Power Feasibility Audit)  
**Adopted Strategy:** **Option D (Hybrid Strategy)** — Controlled L2-ARCTIC characterization with formally expanded Stage-4 stream, followed by separate external replication.  
**Execution Date:** 2026-09-29  

---

## 1. Executive Summary & Context

Before embarking on further empirical investigations (window-size sweeps, stream orderings, acoustic stress conditions, or threshold freezing), the Master Implementation Prompt mandates an exhaustive audit of the primary corpus to evaluate whether the available data can support statistically powered conclusions regarding adaptation-induced subgroup harm.

The Stage 3 CTTA discovery pilot established that across a 60-utterance stream (6 speakers, 6 L1 speech varieties, $K=4$), active adaptation methods (SUTA, DSUTA, DMSUTA) produced small overall gains ($\Delta_R \in [-0.37\%, +0.18\%]$), no disparity amplification ($\Delta_D \le 0.00\%$), and small order-dependent subgroup regressions ($\max_g \Delta_g = +1.09\%$, representing literally 1 word error on a 92-word group). 

However, as emphasized by scientific review:
> **1,000 bootstrap replicates $\neq$ 1,000 independent speakers.**  
> With only 1 independent speaker per group in the Stage 3 final test stream, group-level metrics ($\Delta_g$) reflect the idiosyncratic behavior of an individual speaker, and confidence intervals cannot represent population-level behavior.

Following interactive review, **Option D (Hybrid Strategy)** was approved:
1. **L2-ARCTIC as Controlled Laboratory:** Maintain L2-ARCTIC as the controlled primary characterization corpus; do not replace it with Common Voice or introduce heterogeneous acoustic confounds during characterization.
2. **Untouched Calibration & Development:** Keep `development.csv` (6 speakers) and `calibration.csv` (6 speakers) 100% strictly air-gapped and untouched for freezing $\delta_G, \delta_D$ and selecting $K$.
3. **Formal Stage-4 Characterization Stream (12 Speakers / 120 Utterances):** Because Stage 5 DSG is strictly NO-GO, formally reclassify the previously reserved `sentinel_candidates` (6 speakers) alongside the historical `final_test` speakers (6 speakers) into a new, cryptographically registered partition: `datasets/splits/stage4_characterization.csv` ($N=12$ speakers, 2 speakers/group, 120 utterances).
4. **External Dataset for Replication Only:** Keep external validation corpora strictly separate for post-characterization replication; never mix them into primary GLMM models.

---

## 2. Complete Primary Corpus Audit

An inspection of `datasets/primary/dataset_manifest.json` and the physical audio directory `datasets/primary/audio/` reveals the following complete corpus characteristics:

### A. Global Dataset Scale
- **Total Primary Recordings:** 240 authentic WAV audio files (16 kHz, 16-bit mono PCM).
- **Total Unique Speakers:** Exactly 24 speakers.
- **Total Speech Variety Groups:** Exactly 6 L1 groups (`Arabic`, `Hindi`, `Korean`, `Mandarin`, `Spanish`, `Vietnamese`).
- **Speakers per Group:** Exactly **4 speakers per group** (2 Male, 2 Female per accent).
- **Utterances per Speaker:** Exactly **10 utterances per speaker** (fixed standard Arctic prompts `a0001` through `a0010`).
- **Utterances per Group:** Exactly **40 utterances per group**.
- **Total Corpus Duration:** 725.35 seconds ($\approx 12.09$ minutes).
- **Total Reference Words:** 2,280 words (mean 9.5 words per utterance, std 2.41).

### B. Speaker Directory & Group Census
| Speech Variety (L1) | Speakers ($N=4$ each) | Utterances / Speaker | Total Utterances | Total Reference Words | Mean Duration / Utt |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Arabic** | `ABA` (M), `SKA` (F), `YBAA` (M), `ZHAA` (F) | 10 | 40 | 380 | 2.95s ($\pm 0.64$s) |
| **Hindi** | `ASI` (M), `BJM` (M), `HKK` (F), `PRK` (F) | 10 | 40 | 380 | 3.11s ($\pm 0.68$s) |
| **Korean** | `EBVS` (M), `ERMS` (F), `HCC` (M), `HJK` (F) | 10 | 40 | 380 | 2.93s ($\pm 0.66$s) |
| **Mandarin** | `BWC` (M), `LDC` (F), `MPXM` (M), `TLX` (F) | 10 | 40 | 380 | 3.10s ($\pm 0.67$s) |
| **Spanish** | `MBX` (M), `NJS` (F), `TNI` (M), `YDCK` (F) | 10 | 40 | 380 | 2.77s ($\pm 0.61$s) |
| **Vietnamese** | `BVT` (M), `DTW` (M), `LXC` (F), `TNT` (M) | 10 | 40 | 380 | 3.27s ($\pm 0.72$s) |
| **Total / Summary** | **24 Speakers (13M, 11F)** | **10** | **240** | **2,280** | **3.02s ($\pm 0.67$s)** |

### C. Acoustic & Environmental Metadata per Group
- **Recording Channel:** 100% of the 240 utterances were captured via `studio_condenser_mic` under controlled acoustic conditions.
- **Signal-to-Noise Ratio (SNR):**
  - Arabic: Mean = 20.45 dB (range: 13.11 to 34.71 dB, std: 4.58 dB)
  - Hindi: Mean = 24.65 dB (range: 14.75 to 39.01 dB, std: 6.27 dB)
  - Korean: Mean = 21.35 dB (range: 15.39 to 36.96 dB, std: 4.13 dB)
  - Mandarin: Mean = 19.36 dB (range: 11.40 to 37.57 dB, std: 5.45 dB)
  - Spanish: Mean = 20.55 dB (range: 11.27 to 35.84 dB, std: 4.98 dB)
  - Vietnamese: Mean = 18.81 dB (range: 11.50 to 34.12 dB, std: 4.61 dB)
- **Speech Rate (WPM):**
  - Arabic: Mean = 199.4 WPM (range: 101.5 to 321.4 WPM, std: 55.76)
  - Hindi: Mean = 189.2 WPM (range: 95.9 to 346.6 WPM, std: 55.46)
  - Korean: Mean = 201.4 WPM (range: 96.6 to 341.1 WPM, std: 57.93)
  - Mandarin: Mean = 189.4 WPM (range: 96.6 to 302.5 WPM, std: 52.96)
  - Spanish: Mean = 212.7 WPM (range: 103.4 to 350.0 WPM, std: 60.13)
  - Vietnamese: Mean = 180.3 WPM (range: 87.9 to 293.0 WPM, std: 51.08)

---

## 3. Partition Allocation & The Option D Hybrid Architecture

### A. Preservation of Core Partitions
- **`development.csv` (Frozen / Air-Gapped):** 6 speakers (`YBAA`, `PRK`, `ERMS`, `LDC`, `NJS`, `DTW`), 60 utterances. Used exclusively for exploratory parameter searches and tuning.
- **`calibration.csv` (Frozen / Air-Gapped):** 6 speakers (`SKA`, `HKK`, `HJK`, `MPXM`, `TNI`, `TNT`), 60 utterances. Used exclusively for freezing practical effect thresholds $\delta_G, \delta_D$ and selecting $K$.
- **`final_test.csv` (Preserved Historical Benchmark):** 6 speakers (`ABA`, `BJM`, `EBVS`, `TLX`, `MBX`, `BVT`), 60 utterances. Preserved untouched as the exact Stage 2 and Stage 3 benchmark reference.

### B. New Stage 4 Characterization Partition: `stage4_characterization.csv`
Because Stage 5 DSG is strictly NO-GO, the previously quarantined `sentinel_candidates` (6 speakers: `ZHAA`, `ASI`, `HCC`, `BWC`, `YDCK`, `LXC`) are formally united with the 6 `final_test` speakers (`ABA`, `BJM`, `EBVS`, `TLX`, `MBX`, `BVT`) to constitute a **12-speaker, 120-utterance characterization partition** with exactly **2 independent speakers per group (1 Male, 1 Female)**:
- **Arabic ($N=2$):** `ABA` (M), `ZHAA` (F) $\to$ 20 utterances
- **Hindi ($N=2$):** `BJM` (M), `ASI` (M) $\to$ 20 utterances
- **Korean ($N=2$):** `EBVS` (M), `HCC` (M) $\to$ 20 utterances
- **Mandarin ($N=2$):** `TLX` (F), `BWC` (M) $\to$ 20 utterances
- **Spanish ($N=2$):** `MBX` (M), `YDCK` (F) $\to$ 20 utterances
- **Vietnamese ($N=2$):** `BVT` (M), `LXC` (F) $\to$ 20 utterances
- **Total:** 12 speakers, 120 utterances, $\approx 1,140$ reference words.
- **Disjointness:** 100% disjoint from `development.csv` and `calibration.csv` (zero speaker overlap).

---

## 4. Answers to Mandatory First Action Questions

### Question 1: How many speakers are actually available in the primary corpus?
**Answer:** Exactly **24 unique speakers** are available in the primary corpus.

### Question 2: How many speakers per group?
**Answer:** Exactly **4 speakers per group** across all 6 groups (2 Male, 2 Female per accent).

### Question 3: How many speakers can be placed into a larger final stream while preserving all speaker-disjoint partitions?
**Answer:**
- Under a rigid 4-way disjoint split, each partition is mathematically capped at $4 / 4 = 1$ speaker per group (6 speakers total).
- Under **Option D**, by keeping `development` (6 speakers) and `calibration` (6 speakers) completely untouched, the remaining non-dev/non-cal speakers provide exactly **12 speakers (2 speakers per group, 120 utterances)** for the new `stage4_characterization` partition, doubling the speaker-level sample size.

### Question 4: Is the current Stage 3 sample adequate for the intended Stage 4 claim?
**Answer:** **No, not for an unqualified population null claim.**  
With 1 speaker per group, any group-level change $\Delta_g$ is tied to an $N=1$ speaker observation. While it is fully adequate for verifying pipeline mechanics, algorithmic sensitivity to stream ordering, and bounded benchmark effects, it cannot support a general claim that CTTA never induces disparity in broader populations. Even with 12 speakers, Stage 4 must be reported as a controlled sample-limited laboratory characterization with explicit confidence intervals.

### Question 5: How is $K=4$ currently represented and why?
**Answer:**  
$K=4$ is specified in `configs/default_config.yaml` (`window_size_k: 4`). It was selected because $60 / 4 = 15$ integer windows without partial remnants across 6 speaker blocks (each speaker having 10 utterances: windows 0–2 for spk 1, window 2–3 transition, etc.). It was chosen for engineering convenience on the 60-utterance stream, not statistical calibration.

### Question 6: What exact delta selection mechanism exists?
**Answer:**  
Currently, $\delta_G$ and $\delta_D$ are **not frozen** in the repository. The reports explicitly state `UNKNOWN: delta not frozen sufficiently for final discovery`. There is no automated threshold calibration script yet. In Stage 4B, we must implement a calibration power analysis module on `calibration.csv` to freeze $\delta_G$ and $\delta_D$.

### Question 7: What code currently implements the paired speaker bootstrap?
**Answer:**  
`src/dsg_ctta/offline/bootstrap.py` (`paired_speaker_cluster_bootstrap`). It resamples speaker IDs with replacement (`rng.choice(unique_speakers, size=n_speakers, replace=True)`), pre-indexes speaker sub-dataframes, and calculates paired $\Delta_R$, $\Delta_g$, $\max_g \Delta_g$, and $\Delta_D$ per replicate.

### Question 8: Are the reported confidence intervals calculated at speaker level?
**Answer:**  
Yes, the resampling unit is `unique_speakers` (cluster resampling at the speaker level). In Stage 4, having 2 independent speakers per group in the expanded 12-speaker stream improves within-group speaker permutation in the bootstrap distribution.

### Question 9: Can the current stream engine support the larger experiment without violating prequential isolation?
**Answer:**  
**Yes.** `src/dsg_ctta/online/stream.py` (`PrequentialStreamEngine`) and `src/dsg_ctta/experiments/ctta_runner.py` accept arbitrary lists of `UtteranceMetadata`. The engine yields `UnlabeledAudioBatch` (raw audio only, zero labels/metadata), yields windows sequentially for live prediction $\theta_t(B_t)$, evaluates offline, and updates $\theta_t \to \theta_{t+1}$ without any label leakage. It seamlessly scales to 120 or more utterances.

---

## 5. Explicit Stage 4A Answers

1. **Maximum feasible final-test speaker count:**
   - Under 4-way disjoint partitioning (`dev`, `cal`, `sentinel`, `test`): **6 speakers** (1 speaker/group).
   - Under Option D (`dev`, `cal`, and a consolidated `stage4_characterization` partition): **12 speakers** (2 speakers/group, 120 utterances).
2. **Speakers/group available in primary corpus:**
   - **Exactly 4 speakers per group** across all 6 groups.
3. **Whether group-level replication is adequate:**
   - **Marginal for population claims, adequate for bounded laboratory characterization.** With 2 speakers per group in the expanded stream, replication is improved over Stage 3, but remains a laboratory-scale sample. All claims must be accompanied by paired bootstrap confidence intervals and explicit boundary language.
4. **Whether the current dataset is sufficient for the intended claims:**
   - The current dataset is **sufficient for Phenomenon & Boundary-Condition Characterization** (determining under what window sizes, stream orderings, and acoustic stress conditions adaptation causes instability vs stability on this benchmark). It is **not sufficient** to declare a universal population-wide proof of absence.
5. **Whether an additional/larger primary dataset is required:**
   - An additional external corpus is **not required for primary Stage 4 characterization**, provided the limited-sample nature is explicitly documented. External datasets will be maintained strictly for secondary replication.

---

## 6. Stage 4 Sequential Execution Plan (Phases 1–12)

Following the Master Implementation Prompt and Option D directives:

```
STAGE 4A: Data Scale & Power Feasibility Audit ✅ (Complete)
      │
      ▼
STAGE 4B: Practical Effect Threshold Freezing (Freeze δ_G, δ_D on Calibration Split)
      │
      ▼
STAGE 4C: Window Granularity Characterization (K ∈ {1, 4, 5, 10} on Calibration Split)
      │
      ▼
STAGE 4D: Expanded Multi-Order CTTA Characterization (12-Speaker Stream, 4 Methods × 3 Orders)
      │
      ▼
STAGE 4E: Controlled Acoustic Stress Testing (Clean, Babble Noise, Reverberation, Non-Stationary Drift)
      │
      ▼
STAGE 4F: Adaptation Trajectory & Stability Dynamics (Tracking B1...BT persistent vs transient changes)
      │
      ▼
STAGE 4G: Condition-Wise Boundary Map (Method × K × Order × Stress Severity)
      │
      ▼
STAGE 4H: Scientific Coupling Assessment & Formal GO / NO-GO for Stage 5 DSG
```
