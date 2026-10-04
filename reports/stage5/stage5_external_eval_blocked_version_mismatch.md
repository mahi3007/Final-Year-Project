# Stage 5 External Evaluation — BLOCKED: Dataset Version Mismatch
## DSG-CTTA Stage 5 Protocol Enforcement Audit

**Audit Date:** 2026-10-01  
**Status:** **BLOCKED**  
**Auditor:** Lead Research Data Engineer  
**Stage:** Stage 5 — External Final Evaluation Curation  

---

## 1. Executive Summary & Verdict

The Stage 5 external evaluation pipeline is **HALTED and BLOCKED**.

The extracted archive metadata from the Mozilla Data Collective (MDC) has been forensically verified as belonging to **Common Voice Scripted Speech 27.0** (`cv-corpus-27.0-2026-09-11`), released September 2026. The frozen research protocol strictly requires **Common Voice 11.0** (`cv-corpus-11.0-2022-09-21`), released September 2022.

Consequently:
- The retrieved data is **Common Voice 27.0**, not Common Voice 11.0.
- The 900-clip split generated during Phase 3 is **NOT** the canonical Stage 5 external evaluation set.
- All CV27 artifacts have been quarantined and explicitly renamed as **non-canonical/intermediate artifacts**.
- **No audio has been materialized, and no ASR model, CTTA method, or DSG controller has been run.**
- No protocol amendment has been adopted automatically.

---

## 2. Forensic Dataset Verification

| Parameter | Protocol-Pinned Specification | Retrieved / Extracted File | Compliance Status |
|---|---|---|---|
| **Dataset Release** | `cv-corpus-11.0-2022-09-21` | `cv-corpus-27.0-2026-09-11` | **FAIL (Mismatch)** |
| **Release Date** | September 21, 2022 | September 11, 2026 | **FAIL (+4 years difference)** |
| **MDC Dataset ID** | Not applicable (pre-MDC) | `cmu5jplf300nwmh07iqvk9leo` | **Documented** |
| **Archive Internal Path** | `cv-corpus-11.0-2022-09-21/en/validated.tsv` | `cv-corpus-27.0-2026-09-11/en/validated.tsv` | **FAIL (Internal Path Mismatch)** |
| **Local File Path** | `datasets/external/common_voice_11/validated.tsv` | `datasets/external/common_voice_27_intermediate/validated.tsv` | **Quarantined** |
| **File Size (bytes)** | ~300 MB expected | `614,927,262` bytes (~586.44 MB) | **Mismatch** |
| **Row Count** | ~1,100,000 validated clips | `1,929,854` data rows | **Mismatch (+829k rows)** |
| **SHA-256 Checksum** | Known CV11 hash | `733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a` | **Documented** |

---

## 3. Schema & Accent Taxonomy Discrepancy

A deep forensic scan of the extracted `validated.tsv` confirms that CV27 uses a fundamentally altered schema and accent taxonomy compared to the frozen CV11 specification:

### 3.1 Column Schema Differences
- **CV11 Schema (10 columns):** `client_id`, `path`, `sentence`, `up_votes`, `down_votes`, `age`, `gender`, `accent`, `locale`, `segment`.
- **CV27 Schema (13 columns):** `client_id`, `path`, `sentence_id`, `sentence`, `sentence_domain`, `up_votes`, `down_votes`, `age`, `gender`, `accents`, `variant`, `locale`, `segment`.
  - The accent column is renamed from `accent` (singular) to `accents` (plural).
  - New columns introduced: `sentence_id`, `sentence_domain`, and `variant`.

### 3.2 Accent Taxonomy Incompatibility
The frozen protocol strictly relies on dataset-native accent labels rather than geographic inference. In CV27, the legacy enumerated accent codes have been entirely superseded by descriptive free-text labels:

| Candidate Accent String | Occurrences in CV27 `validated.tsv` | Status in CV27 Taxonomy |
|---|---|---|
| `'us'` | **0** | Missing (replaced by `'United States English'`: 460,977) |
| `'england'` | **0** | Missing (replaced by `'England English'`: 163,648) |
| `'indian'` | **4** | Deprecated (replaced by `'India and South Asia (India, Pakistan, Sri Lanka)'`: 113,063) |
| `'australia'` | **0** | Missing (replaced by `'Australian English'`: 56,516) |
| `'canada'` | **0** | Missing (replaced by `'Canadian English'`: 78,271) |
| `'ireland'` | **0** | Missing (replaced by `'Irish English'`: 9,617) |

Furthermore, CV27 contains **868 distinct accent strings** and **81,035 compound/piped entries** (e.g. `'United States English|England English'`), reflecting the unconstrained self-description taxonomy introduced after CV12.

Mapping these descriptive strings back to the CV11 codes represents an ad-hoc normalization layer that was **not** part of the frozen CV11 protocol.

---

## 4. Mozilla Data Collective API Availability Audit

Using the authenticated MDC API integration (`datacollective` v0.6.3), we executed systematic queries to locate any archived English Common Voice 11.0 release:

### Queries Tested:
1. `query="cv-corpus-11"` $\rightarrow$ 0 results
2. `query="cv-corpus-11.0"` $\rightarrow$ 0 results
3. `query="2022-09-21"` $\rightarrow$ 0 Common Voice results
4. `query="Common Voice Scripted Speech 11"` $\rightarrow$ 0 results
5. Full catalog scan of Organization `Common Voice` for English ASR:
   - Total English ASR datasets published: **4**
     1. `cmu5jplf300nwmh07iqvk9leo`: *Common Voice Scripted Speech 27.0 - English* (88.43 GB)
     2. `cmu5nqn1h00vwmi07b4dbk085`: *Common Voice Spontaneous Speech 5.0 - English* (519.1 MB)
     3. `cmrt70sar001umm07jwxzhw89`: *Common Voice Scripted Speech 26.0 - South Asian English* (3.9 GB)
     4. `cmrt717ci0017mm075ewqaw6v`: *Common Voice Scripted Speech 26.0 - Scottish English* (770.7 MB)

**Conclusion:** Common Voice 11.0 (`cv-corpus-11.0-2022-09-21`) is **NOT** hosted or accessible via the Mozilla Data Collective platform or its authenticated API.

---

## 5. Actions Executed to Preserve Integrity

1. **Pipeline Halted:** Audio materialization, ASR inference, SUTA/DSUTA/DMSUTA adaptation, and DSG controller execution remain strictly uninitiated.
2. **Artifact Quarantine:** The CV27-derived artifacts have been renamed to prevent any accidental use as canonical splits:
   - `datasets/splits/stage5_external_eval_cv27_intermediate.csv`
   - `datasets/splits/stage5_external_eval_manifest_cv27_intermediate.json`
   - `datasets/splits/stage5_external_eval_cv27_intermediate.lock.json`
   - `datasets/external/common_voice_27_intermediate/validated.tsv`
3. **No Phantom Files:** The canonical target file `datasets/splits/stage5_external_eval.csv` has been removed so that downstream pipeline stages fail-closed if invoked.
4. **Git Isolation:** `.gitignore` updated to prevent accidental commitment of credentials, environment variables, or large intermediate files.

---

## 6. Current Blocking Status

$$
\boxed{\text{Stage 5 Status: BLOCKED}}
$$

**Reason:**  
$$\text{Retrieved Dataset Version } (\text{CV 27.0}, 2026\text{-}09\text{-}11) \ne \text{ Protocol-Pinned Version } (\text{CV 11.0}, 2022\text{-}09\text{-}21)$$

The pipeline will remain blocked until a formal decision is reached between:
- **Path A:** Securing an authentic historical archive of `cv-corpus-11.0-2022-09-21`.
- **Path B:** Authorizing a formal protocol amendment documenting the transition to Common Voice 27.0, including its schema, taxonomy normalization rules, and demographic differences.
