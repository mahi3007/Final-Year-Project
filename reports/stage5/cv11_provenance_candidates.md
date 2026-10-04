# Stage 5 — Historical Common Voice 11.0 Provenance Investigation & Forensic Audit

**Date:** 2026-10-01  
**Project:** DSG-CTTA (Dynamic Spatial-Group Continual Test-Time Adaptation)  
**Document ID:** `reports/stage5/cv11_provenance_candidates.md`  
**Investigation Lead:** Research-Data Engineering / Forensic Audit  
**Status:** **STAGE 5 = BLOCKED** (No candidate achieves `AUTHENTICITY VERIFIED`)  

---

## 1. Executive Summary & Verdict

In accordance with strict experimental protocols, this investigation evaluated potential third-party, archival, and distribution mirrors of **Mozilla Common Voice 11.0 English** (`cv-corpus-11.0-2022-09-21`) to determine whether an authentic, canonical copy of the historical release can be retrieved to support the frozen Stage 5 external evaluation protocol.

### Forensic Verdict Summary

| Candidate ID | Source / Repository Identifier | Platform | Claimed Release | Authentic English Present? | Schema Match (Singular `accent`)? | Checksum Match? | Final Verdict |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **CAND-01** | `echodict/common_voice_11_0` | Hugging Face Dataset | CV 11.0 | ❌ No (Japanese Only) | N/A (Japanese only) | ❌ No | **SOURCE REJECTED** |
| **CAND-02** | `Krishna6889/common_voice_11_0-bucket` | Hugging Face Storage Bucket | CV 11.0 | ❌ No (Japanese Only clone) | N/A (Japanese only) | ❌ No | **SOURCE REJECTED** |
| **CAND-03** | `akahana/common-voice-11-eng-sample` | Hugging Face Dataset | CV 11.0 (Sample) | ⚠️ Partial (Train/Test only) | ❌ Failed (Uses `accents`) | ❌ No | **SOURCE REJECTED** |
| **CAND-04** | `mozilla-foundation/common_voice_11_0` | Hugging Face Official | CV 11.0 | ❌ Inaccessible (404 / 401) | N/A | N/A | **SOURCE REJECTED** (Decommissioned) |
| **CAND-05** | Community Preprocessed (`anforsm`, `sanchit-gandhi`, `daniel123321`) | Hugging Face | Various | ❌ No (Tokenized/Dummy/Empty) | ❌ No | ❌ No | **SOURCE REJECTED** |
| **CAND-06** | Mozilla Data Collective (MDC) API (`datacollective`) | Official Mozilla Portal | CV Catalog | ❌ No (Only v26.0 & v27.0) | N/A | N/A | **AUTHENTICITY INCONCLUSIVE** (Not Hosted) |

### Formal Pipeline State

$$
\boxed{\text{Stage 5 Pipeline Status: BLOCKED}}
$$

**Primary Blocker:** No authentic, complete copy of `cv-corpus-11.0-2022-09-21-en.tar.gz` is accessible through verified public, community, or official distribution endpoints. The frozen Stage 5 protocol remains intact. Audio materialization, ASR inference, and DSG controller execution remain strictly withheld.

---

## 2. Canonical Ground Truth Fingerprint for Common Voice 11.0 English

Through forensic extraction from official release metadata (`release_stats.py` embedded in historical release tooling), the exact cryptographic, demographic, and structural fingerprint of Mozilla's original Common Voice 11.0 English release was recovered:

* **Exact Canonical Release Identifier:** `cv-corpus-11.0-2022-09-21`
* **Official Release Date:** `2022-09-21`
* **Release Name:** `Common Voice Corpus 11.0`
* **Canonical Archive Filename:** `cv-corpus-11.0-2022-09-21-en.tar.gz`
* **Bundle URL Template:** `cv-corpus-11.0-2022-09-21/cv-corpus-11.0-2022-09-21-{locale}.tar.gz`
* **Canonical Archive Size:** `79,751,937,788` bytes (**74.27 GiB** / 79.75 GB)
* **Canonical Archive SHA-256 Checksum:**  
  `0efd86ca6b40641b55d1411b7d3b1f1ab8626de4b207504953706df201d198a5`
* **Canonical Clip Counts:**
  * Total clips: `2,161,670`
  * `validated.tsv`: `1,618,225` clips *(in contrast to CV 27.0 which contains 1,929,854 validated clips)*
  * `train.tsv`: `948,736` clips
  * `test.tsv`: `16,354` clips
  * `dev.tsv`: `16,354` clips
  * `invalidated.tsv`: `252,599` clips
  * `other.tsv`: `290,846` clips
  * `reported.tsv`: `4,366` clips
* **Registered Speakers/Users:** `84,673` users
* **Audio Duration:** `3,097.91` total hours (`2,319.09` validated hours)
* **Metadata Schema (10 fields, strict singular `accent`):**  
  `client_id`, `path`, `sentence`, `up_votes`, `down_votes`, `age`, `gender`, `accent`, `locale`, `segment`

Any candidate source claiming to be Common Voice 11.0 English must match this fingerprint to be considered canonical.

---

## 3. Systematic Forensic Evaluation of Candidates

### Candidate 1: `echodict/common_voice_11_0`
* **Source URL:** `https://huggingface.co/datasets/echodict/common_voice_11_0`
* **Uploader / Organization:** `echodict`
* **Created Date:** 2026-04-16T07:07:13Z
* **Total Reported Size:** ~619 MB
* **Repository Architecture:**
  ```
  .gitattributes
  README.md
  common_voice_11_0.py
  count_n_shards.py
  languages.py
  n_shards.json
  release_stats.py
  transcript/
    ja/ (dev.tsv, invalidated.tsv, other.tsv, test.tsv, train.tsv)
  audio/
    ja/ (dev/, invalidated/, other/, test/, train/)
  ```
* **Forensic Findings:**
  1. The repository contains the official dataset card and `release_stats.py` script for Common Voice 11.0 across all languages.
  2. However, the data directories contain **exclusively Japanese (`ja`) data**.
  3. No English (`en`) directory exists under `transcript/` or `audio/`.
  4. Even within Japanese, `validated.tsv` is omitted (only split-specific TSVs are provided).
  5. The ~619 MB volume corresponds entirely to the Japanese audio shards and metadata.
* **Verdict:** **SOURCE REJECTED** (Zero English data present).

---

### Candidate 2: `Krishna6889/common_voice_11_0-bucket`
* **Source URL:** `https://huggingface.co/buckets/Krishna6889/common_voice_11_0-bucket`
* **Uploader / Organization:** `Krishna6889` (Krishna TG)
* **Created Date:** 2026-06-11T16:12:34Z
* **Total Storage Size:** `618,583,123` bytes (618.5 MB, 17 files)
* **Repository Architecture:**
  ```
  .gitattributes
  README.md
  common_voice_11_0.py
  count_n_shards.py
  languages.py
  n_shards.json
  release_stats.py
  transcript/
    ja/
  audio/
    ja/
  ```
* **Forensic Findings:**
  1. Storage metadata verification reveals identical byte sizes, file lists, and directory trees to `echodict/common_voice_11_0`.
  2. The bucket is a direct mirror/fork of `echodict/common_voice_11_0`.
  3. Contains exclusively Japanese (`ja`) audio and transcripts.
  4. Contains no English transcripts, no English audio, and no `cv-corpus-11.0-2022-09-21/en/` archive structure.
* **Verdict:** **SOURCE REJECTED** (Duplicate of Japanese-only mirror; no English assets).

---

### Candidate 3: `akahana/common-voice-11-eng-sample`
* **Source URL:** `https://huggingface.co/datasets/akahana/common-voice-11-eng-sample`
* **Uploader / Organization:** `akahana`
* **Total Storage Size:** ~39.4 GB across 28 files
* **Repository Architecture:**
  ```
  .gitattributes
  en_test_0.tar (722 MB)
  en_train_0.tar .. en_train_23.tar (~1.6 GB each)
  test.tsv (3.73 MB)
  train.tsv (243.13 MB)
  ```
* **Forensic Inspection of TSV Schema:**
  Direct byte inspection of `test.tsv` yielded:
  ```
  client_id | path | sentence | up_votes | down_votes | age | gender | accents | locale | segment
  ```
* **Forensic Findings:**
  1. **Schema Non-Compliance:** The metadata uses the plural column name `accents` rather than the historical canonical singular `accent`.
  2. **Missing Canonical Core:** The repository completely lacks `validated.tsv`. It provides only an ad-hoc subset split (`train.tsv` and `test.tsv`).
  3. **Non-Canonical Packaging:** The audio files are packaged into 24 custom `.tar` training shards rather than Mozilla's canonical `cv-corpus-11.0-2022-09-21-en.tar.gz` directory hierarchy (`cv-corpus-11.0-2022-09-21/en/clips/`).
  4. **Arbitrary Subsampling:** The corpus is a personal sample curated for model fine-tuning, lacking provenance guarantees regarding speaker coverage or unbiased group distribution.
* **Verdict:** **SOURCE REJECTED** (Schema mismatch with plural `accents`, missing `validated.tsv`, non-canonical sharding).

---

### Candidate 4: Legacy Hugging Face Canonical Repo (`mozilla-foundation/common_voice_11_0`)
* **Source URL:** `https://huggingface.co/datasets/mozilla-foundation/common_voice_11_0`
* **Uploader / Organization:** `mozilla-foundation`
* **Current Access Status:** HTTP 404 (Not Found via web) / HTTP 401 (Unauthorized via API)
* **Forensic Findings:**
  1. Independent academic and industry community reporting confirms that in late 2025, Mozilla permanently decommissioned all legacy Common Voice datasets (`common_voice_1_0` through `common_voice_22_0`) from the Hugging Face Hub.
  2. The repositories were either deleted or restricted to internal administrative access as Mozilla moved dataset distribution exclusively to its proprietary platform, the **Mozilla Data Collective (MDC)**.
  3. No public API key or authentication token can retrieve files from `mozilla-foundation/common_voice_11_0`.
* **Verdict:** **SOURCE REJECTED** (Permanently unavailable / upstream deletion).

---

### Candidate 5: Other Hugging Face Community Repositories
A comprehensive catalog search of all 32 datasets on Hugging Face matching `common_voice_11` was executed:
1. `anforsm/common_voice_11_clean_tokenized`: Contains 4 preprocessed Parquet files with tokenized text; zero audio files.
2. `sanchit-gandhi/common_voice_11_0_dummy`: Unit-testing dummy fixture containing 2 Parquet files totaling 3.2 KB.
3. `daniel123321/common_voice_11`: Empty repository containing only `.gitattributes`.
4. Language-specific variants (`hi`, `ur`, `th`, `ar`, `kk`, `fr`, `es`, `fa`): Contain non-English speech only.
* **Verdict:** **SOURCE REJECTED** (No authentic English audio or validated metadata).

---

### Candidate 6: Official Mozilla Data Collective (MDC)
* **Distribution Portal:** `https://mozilladatacollective.com`
* **API Access Client:** `datacollective` Python SDK (authenticated with user key)
* **Forensic Findings:**
  1. Programmatic inventory via `list_datasets()` yielded 24 active datasets.
  2. Common Voice entries on MDC are restricted entirely to recent releases:
     - `Common Voice Scripted Speech 27.0` (all supported locales, including English `cmu5jplf300nwmh07iqvk9leo`)
     - `LRAC 2.0 Common Voice 26.0 Bundle`
  3. Historical snapshots (including CV 11.0 through CV 25.0) are **not hosted or distributed on MDC**.
  4. Mozilla maintains only current cumulative releases rather than archival point releases on its primary distribution CDN.
* **Verdict:** **AUTHENTICITY INCONCLUSIVE / UNAVAILABLE UPSTREAM** (MDC does not host historical releases).

---

## 4. Synthesis of Findings & Technical Reality

```
                   Historical CV 11.0 Archive
              (cv-corpus-11.0-2022-09-21-en.tar.gz)
                     [74.27 GiB, SHA-256: 0efd...]
                                   |
         +-------------------------+-------------------------+
         |                                                   |
   Hugging Face                                     Mozilla Official
         |                                                   |
  +------+------+                                     +------+------+
  |             |                                     |             |
echodict    akahana                             Hugging Face       MDC
(Japanese   (Sample only,                       (Deleted /        (Only v26-27
 only)       plural `accents`)                   404 error)        hosted)
  |             |                                     |             |
[REJECTED]  [REJECTED]                            [DECOMMISSIONED] [UNAVAILABLE]
```

1. **Upstream Deprecation is Complete:** The historical `cv-corpus-11.0-2022-09-21` English archive is no longer distributed by Mozilla or maintained on reputable scientific data hubs.
2. **Third-Party Mirrors are Incomplete or Corrupted:** Surviving third-party mirrors on Hugging Face are either language-specific subsets (Japanese only), non-canonical samples with altered schemas (`accents` plural), or text-only tokenized derivatives.
3. **No Authentic CV 11.0 English Asset Exists:** There is currently no verifiable, authentic, checksum-valid copy of Common Voice 11.0 English available for download.

---

## 5. Strict Protocol Enforcement & Scientific Next Steps

### Protocol Compliance Guard
* **No Silent Substitution:** Under no circumstances will Common Voice 27.0 be disguised as Common Voice 11.0.
* **Quarantined Status Maintained:** All CV 27.0 artifacts remain strictly quarantined under `datasets/splits/stage5_external_eval_cv27_intermediate.csv` and `datasets/external/common_voice_27_intermediate/`.
* **Zero Model Inference:** Model weights, ASR decoders, CTTA adaptation loops, and DSG controllers remain completely untouched.

### Decision Fork for Research Leads

Because Path A (obtaining genuine historical CV 11.0) has reached a definitive negative forensic conclusion across all known channels, the project faces a structured scientific decision:

1. **Option 1 (User / Institution-Provided Archive):**  
   If the user or their research institution possesses a private, locally stored copy of the original `cv-corpus-11.0-2022-09-21-en.tar.gz` (verifiable against SHA-256 `0efd86ca6b40641b55d1411b7d3b1f1ab8626de4b207504953706df201d198a5`), it can be placed into `datasets/external/common_voice_11/` for canonical processing.

2. **Option 2 (Formal Protocol Amendment to CV 27.0):**  
   Formally amend the Stage 5 experimental protocol to adopt Common Voice 27.0 (`cv-corpus-27.0-2026-09-11`) as the external evaluation corpus. This amendment would formally codify:
   - Upstream unavailability of CV 11.0 as the objective rationale.
   - Schema differences (10 columns $\rightarrow$ 13 columns; `accent` $\rightarrow$ `accents`).
   - Native accent taxonomy mapping specification (e.g., mapping `United States English` to `us`, `England English` to `england`, etc.).
   - Demographic composition differences (1.93M validated utterances vs 1.62M in CV 11).
   - Re-running deterministic selection under the amended protocol.

3. **Option 3 (Alternative Established Benchmark):**  
   Select a different publicly archived, checksum-verifiable multi-accent English evaluation benchmark (e.g., LibriCSS, VoxCeleb, or clean subsets of TED-LIUM / VCTK) through a formal protocol revision.

---

## 6. Current Pipeline Gate State

$$
\boxed{\text{Stage 5 State: BLOCKED}}
$$

* **Controller Implementation:** Withheld.  
* **ASR Inference:** Withheld.  
* **Audio Materialization:** Withheld.  
* **Canonical Evaluation Split:** None (Canonical `datasets/splits/stage5_external_eval.csv` is intentionally absent).  
* **Pending Action:** Awaiting user directive on whether to provide a private CV 11.0 archive (Option 1) or draft a formal Stage 5 Protocol Amendment (Option 2).
