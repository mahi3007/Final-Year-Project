# Stage 5 Research Protocol Amendment: Migration to Common Voice 27.0

**Document Identifier:** `reports/stage5/protocol_amendment_cv27.md`  
**Date of Amendment:** 2026-10-01  
**Project:** DSG-CTTA (Dynamic Spatial-Group Continual Test-Time Adaptation)  
**Amendment Status:** **APPROVED & FROZEN**  
**Predecessor Pinned Protocol:** Stage 0 Protocol Freeze / Stage 5 Phase 1 (`cv-corpus-11.0-2022-09-21`)  
**Amended Protocol Target:** Mozilla Common Voice Scripted Speech 27.0 English (`cv-corpus-27.0-2026-09-11`)  
**Official Distributor:** Mozilla Data Collective (MDC Dataset ID: `cmu5jplf300nwmh07iqvk9leo`)  

---

## 1. Context and Objective Rationale for Protocol Amendment

### 1.1 Original Requirement
The original frozen research protocol for Stage 5 specified an external, out-of-distribution evaluation set constructed from **Mozilla Common Voice Corpus 11.0 English** (`cv-corpus-11.0-2022-09-21`), designed to evaluate model robustness and subgroup disparity under test-time adaptation across 6 speech varieties without overlapping calibration speakers.

### 1.2 Upstream Deprecation & Provenance Investigation Findings
In accordance with research-validity protocols, a forensic provenance investigation was executed on October 1, 2026 ([`reports/stage5/cv11_provenance_candidates.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/cv11_provenance_candidates.md)):
1. **Upstream Deprecation:** In late 2025, Mozilla decommissioned all historical Common Voice repositories on the Hugging Face Hub (`mozilla-foundation/common_voice_11_0` returns HTTP 404 / 401 Unauthorized) and transitioned dataset hosting exclusively to the **Mozilla Data Collective (MDC)**.
2. **Catalog Scope:** An authenticated programmatic audit of MDC using the `datacollective` SDK confirmed that Mozilla hosts only active, cumulative releases (releases 26.0 and 27.0). Historical snapshots (including CV 11.0) are not retrievable through Mozilla's distribution platform.
3. **Third-Party Mirrors Corrupted or Incomplete:**
   - Candidate mirrors on Hugging Face (`echodict/common_voice_11_0`, `Krishna6889/common_voice_11_0-bucket`) were found to contain exclusively Japanese (`ja`) audio and transcripts (~618.5 MB total), with zero English files.
   - Community samples (`akahana/common-voice-11-eng-sample`) contained schema divergences (plural `accents`), lacked `validated.tsv`, and provided only ad-hoc training shards.
   - No authentic copy matching the canonical SHA-256 (`0efd86ca6b40641b55d1411b7d3b1f1ab8626de4b207504953706df201d198a5`, 74.27 GiB) is publicly obtainable.

### 1.3 Alternative Corpus Rejection Rationale
Alternative multi-accent corpora were evaluated and systematically rejected:
- **VCTK (University of Edinburgh):** Highly unbalanced speaker distribution (e.g., only 3 Indian and 2 Australian speakers), failing the frozen requirement of 10 independent speakers per group.
- **VoxCeleb:** Created for speaker identification/verification from unconstrained YouTube media; lacks reference transcription alignment and structured accent categorization.
- **LibriCSS:** Multi-speaker conversational overlap benchmark; not designed for accent-disparity evaluation.
- **EdAcc:** Designed for conversational ASR with fluid linguistic backgrounds; lacks the required 10-speaker $\times$ 6-group balanced structure and contains unverified subjective speaker labels.

### 1.4 Selection of Official Common Voice 27.0
**Common Voice Scripted Speech 27.0 English** (`cv-corpus-27.0-2026-09-11`) is an officially verified, active ASR release distributed directly by Mozilla Data Collective under CC0-1.0. It provides:
- Official distribution provenance with verified cryptographic integrity.
- Sufficient demographic volume across all target evaluation strata (e.g., smallest target stratum, Irish English, possesses 94 eligible speakers with $\ge 15$ validated clips, exceeding the 10-speaker requirement by 9.4$\times$).
- Clean separation from prior experimental stages (Stage 0–4 calibration sets).

---

## 2. Dataset Identifier and Distribution Provenance

* **Dataset Title:** Common Voice Scripted Speech 27.0 - English
* **Canonical Release Identifier:** `cv-corpus-27.0-2026-09-11`
* **Release Date:** September 11, 2026
* **Distributor Platform:** Mozilla Data Collective (MDC)
* **Dataset Identifier (MDC ID):** `cmu5jplf300nwmh07iqvk9leo`
* **License:** Creative Commons CC0 1.0 Universal (Public Domain Dedication)
* **Raw Validated Metadata File:** `datasets/external/common_voice_27_intermediate/validated.tsv`
* **Raw Validated TSV File Size:** 614,929,488 bytes (586.44 MB, 1,929,854 records)
* **Raw Validated TSV SHA-256:**  
  `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a`

---

## 3. Metadata Schema Changes & Specification

Common Voice 27.0 introduces an updated 13-column schema compared to the legacy 10-column CV 11.0 format.

| Column Index | Field Name (CV 27.0) | Legacy Field (CV 11.0) | Description / Type | Role in Stage 5 Curation |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `client_id` | `client_id` | 128-char hex hashed speaker UUID | Primary speaker deduplication key |
| 2 | `path` | `path` | MP3 audio clip filename (e.g. `common_voice_en_...mp3`) | Audio reference key |
| 3 | `sentence_id` | *New* | 64-char hex hash of sentence prompt | Prompt integrity verification |
| 4 | `sentence` | `sentence` | Ground-truth reference transcript | Reference text for WER calculation |
| 5 | `sentence_domain` | *New* | Sentence topic category (e.g., news, general) | Unused for selection |
| 6 | `up_votes` | `up_votes` | Validation up-votes | Quality filter ($\ge 2$) |
| 7 | `down_votes` | `down_votes` | Validation down-votes | Quality filter ($< 2$) |
| 8 | `age` | `age` | Self-reported speaker age category | Retained for demographic provenance |
| 9 | `gender` | `gender` | Self-reported speaker gender | Retained for demographic provenance |
| 10 | `accents` | `accent` *(Singular)* | Self-reported descriptive speech variety string | Input to `frozen_grouping_rule` |
| 11 | `variant` | *New* | Regional linguistic variant description | Unused for primary strata |
| 12 | `locale` | `locale` | BCP-47 locale code (`en`) | Filter (strictly `en`) |
| 13 | `segment` | `segment` | Benchmark or subcorpus tag | Unused for selection |

---

## 4. Frozen Accent Normalization & Grouping Rules

### 4.1 Definitional Separation: From Metadata Codes to Pre-Specified Evaluation Strata
Rather than asserting that CV 27.0 contains identical categories to CV 11.0, this amendment formally defines a **new Stage-5 grouping variable**:

$$
\text{source\_accent\_raw} \xrightarrow{\quad\text{frozen\_grouping\_rule}\quad} \text{stage5\_accent\_group}
$$

The six groups represent the **pre-specified evaluation strata** retained from the original research design to measure cross-accent disparity and adaptation stability.

### 4.2 Exact Deterministic Grouping Map

| Raw Metadata Value (`source_accent_raw` in CV 27.0) | Frozen Grouping Rule Mapping | Pre-Specified Evaluation Stratum (`stage5_accent_group`) | Stratum Code (`stratum_code`) |
| :--- | :---: | :--- | :---: |
| `United States English` | $\to$ | **US English** | `us` |
| `England English` | $\to$ | **England English** | `england` |
| `India and South Asia (India, Pakistan, Sri Lanka)` | $\to$ | **South Asian English** | `south_asian` |
| `Australian English` | $\to$ | **Australian English** | `australia` |
| `Canadian English` | $\to$ | **Canadian English** | `canada` |
| `Irish English` | $\to$ | **Irish English** | `ireland` |

### 4.3 Strict Treatment of Ambiguous, Compound, and Non-Conforming Entries
1. **Compound / Piped Accents (`|`):** Any utterance containing pipe characters (e.g., `United States English|England English` or `Canadian English|United States English`) is **strictly excluded** from the six-group primary evaluation strata. No arbitrary or probabilistic assignment is permitted.
2. **Unrecognized / Empty Strings:** Utterances with empty, whitespace-only, or unrecognized accent strings are strictly excluded.
3. **Speaker Homogeneity Constraint:** A speaker is defined as eligible **if and only if 100% of their validated utterances** bear the exact identical normalized `stage5_accent_group`. Any speaker with conflicting accent declarations across clips is flagged as ambiguous and completely disqualified. Across all 1.93M rows, exactly 1 ambiguous speaker was identified and disqualified.
4. **Preservation of Raw Provenance:** The resulting evaluation manifest preserves `source_accent_raw` verbatim alongside `stage5_accent_group` and `stratum_code`.

---

## 5. Speaker and Clip Selection Algorithm

The evaluation set selection is performed using a purely deterministic, model-blind algorithm:

$$
\text{Selection Seed} = 20261001, \quad \text{Clip Seed Offset} = 1, \quad \text{Rule Version} = \texttt{v1.0-cv27-amended}
$$

### 5.1 Strict Blindness Guarantee
Under no circumstances are clips or speakers selected based on:
- Word Error Rate (WER) or Character Error Rate (CER)
- ASR model output, confidence scores, or loss
- Acoustic disparity metrics or signal-to-noise ratio
- Post-hoc performance filtering

Selection is strictly a function of metadata eligibility, cryptographic hashing, and seeded pseudo-random sampling.

### 5.2 Eligibility Criteria
An utterance is eligible for selection if:
1. `locale == "en"`
2. It belongs to `validated.tsv` (validated by community consensus).
3. `accents` unambiguously maps to one of the six `stage5_accent_group` targets without pipes (`|`).
4. The transcript contains at least 2 whitespace-separated words.
5. The speaker has at least 15 eligible clips.
6. The speaker has zero conflicting accent annotations across all their clips.

### 5.3 Deterministic Selection Procedure
For each of the 6 strata:
1. Identify all eligible speakers in the stratum.
2. Sort eligible speaker IDs lexicographically.
3. Seed random generator with $\text{seed} = 20261001 + \text{stratum\_index}$.
4. Deterministically select exactly **10 speakers**.
5. For each selected speaker:
   - Identify all eligible clips for that speaker.
   - Sort clip paths lexicographically.
   - Seed clip random generator with $\text{seed} = 20261001 + 1 + (\text{int}(\text{hash}(\text{speaker\_id})) \pmod{10^6})$.
   - Deterministically sample exactly **15 clips**.

Total evaluation holdout size:
$$
6 \text{ groups} \times 10 \text{ speakers/group} \times 15 \text{ clips/speaker} = 60 \text{ speakers}, \quad 900 \text{ evaluation clips}
$$

---

## 6. Predecessor Invariants and Quarantine Management

1. **Predecessor Integrity Preserved:** Stages 0 through 4 (protocol freeze, baseline evaluation, continual test-time adaptation, calibration set, and empirical regression findings) remain 100% frozen and unmodified.
2. **Intermediate Artifact Quarantine:** The previous unamended CV 27.0 selection is retained strictly as provenance evidence at:  
   [`datasets/splits/stage5_external_eval_cv27_intermediate.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval_cv27_intermediate.csv)
3. **Promotion to Canonical Status:** The regenerated, amended split is promoted to the canonical path:  
   [`datasets/splits/stage5_external_eval.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage5_external_eval.csv)  
   accompanied by its manifest (`stage5_external_eval_manifest.json`) and cryptographic lock (`stage5_external_eval.lock.json`).

---

## 7. Gatekeeper Validation & Acceptance Criteria

Stage 5 may proceed to audio materialization and controller evaluation if and only if:
1. [x] This protocol amendment document is authored and committed.
2. [ ] The deterministic selection script is executed under the amended specifications.
3. [ ] Canonical `datasets/splits/stage5_external_eval.csv` is populated with exactly 900 rows across 60 independent speakers.
4. [ ] SHA-256 cryptographic lock file is generated.
5. [ ] All 14 research-validity tests in `tests/research_validity/test_stage5_external_eval.py` execute and pass ($14 / 14$ PASS).
6. [ ] Speaker independence tests verify $S_{\text{eval}} \cap S_{\text{calibration}} = \emptyset$ and $S_{\text{eval}} \cap S_{\text{L2-ARCTIC}} = \emptyset$.
7. [ ] No ASR inference or model execution is performed prior to test suite pass.
