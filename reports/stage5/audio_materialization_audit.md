# Stage 5 Audio Materialization Audit Report
**Protocol Version:** v1.0-cv27-amended
**Dataset Release:** `cv-corpus-27.0-2026-09-11` (MDC ID: `cmu5jplf300nwmh07iqvk9leo`)
**Execution Timestamp:** 2026-10-02T14:42:03Z
**Status:** COMPLETE -- 100% VERIFIED -- ALL GATES PASSED

---

## 1. Executive Summary

| Metric | Target | Materialized / Verified | Status |
| :--- | :--- | :--- | :--- |
| **Total Audio Clips** | 900 | 900 | **MATCH (100%)** |
| **Total Speakers** | 60 | 60 | **MATCH (100%)** |
| **Accent Strata** | 6 | 6 | **MATCH (100%)** |
| **Clips Per Speaker** | Exactly 15 | Exactly 15 | **MATCH (100%)** |
| **Speakers Per Group** | Exactly 10 | Exactly 10 | **MATCH (100%)** |
| **Unique Audio Hashes** | 900 | 900 | **MATCH (0 collisions)** |
| **Missing / Corrupt Files** | 0 | 0 | **PASS** |
| **Total Audio Duration** | -- | 72.38 min (4343.05 s) | **NOMINAL** |
| **Mean Clip Duration** | -- | 4.83 s | **NOMINAL** |
| **Total Materialized Size** | -- | 31.33 MB | **OPTIMIZED** |

---

## 2. Source Resolution & Deterministic Mapping

Every materialized file corresponds strictly to one row in `datasets/splits/stage5_external_eval.csv`. Files saved under `datasets/external/common_voice_27/audio/` using `{recording_id}.mp3` naming.

- **Sample Rates Observed:** [32000, 48000] Hz
- **Channels Observed:** [1]
- **Min Clip Duration:** 1.13 s
- **Max Clip Duration:** 10.04 s

---

## 3. Stratum-Level Distribution

| Accent Stratum | Speakers | Clips | Total Duration | Mean Duration | Total Size |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 10 | 150 | 753.9 s (12.57 min) | 5.03 s | 5.62 MB |
| **Canadian English** | 10 | 150 | 726.7 s (12.11 min) | 4.84 s | 5.23 MB |
| **England English** | 10 | 150 | 706.5 s (11.77 min) | 4.71 s | 5.39 MB |
| **Irish English** | 10 | 150 | 632.1 s (10.54 min) | 4.21 s | 4.61 MB |
| **South Asian English** | 10 | 150 | 753.5 s (12.56 min) | 5.02 s | 5.08 MB |
| **US English** | 10 | 150 | 770.4 s (12.84 min) | 5.14 s | 5.40 MB |
| **TOTAL** | **60** | **900** | **4343.1 s (72.38 min)** | **4.83 s** | **31.33 MB** |

---

## 4. Cryptographic Provenance

- **Historical Pre-Materialization CSV Hash:** `5818255605c46db3832033bdd6c818d7606251a1c2d96d36a6383e9a30443351`
- **Finalized Post-Materialization CSV Hash:** `41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32`

---

## 5. Verdict

**STAGE 5 AUDIO MATERIALIZATION PASSED -- READY FOR STAGE 5A DSG CONTROLLER**
