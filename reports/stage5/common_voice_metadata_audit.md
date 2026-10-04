# Common Voice English — Phase 1 Metadata Audit
## DSG-CTTA Stage 5 External Evaluation Feasibility

**Project:** Disparity-Aware Continual Test-Time Adaptation (DSG-CTTA)
**Phase:** Stage 5 Phase 1 — Metadata-Only Feasibility Audit
**Audit Date:** 2026-10-01
**Auditor:** Lead Research Data Engineer
**Audit Purpose:** Determine whether Mozilla Common Voice English can serve as the Stage 5 external final evaluation corpus (S_eval), providing a speaker-disjoint, accent-labelled, transcript-verified evaluation stream independent of L2-ARCTIC.

> **SCOPE BOUNDARY:** This phase performs metadata-only analysis. No audio has been downloaded. No final evaluation subset has been selected. No DSG controller code has been written.

---

## 1. Executive Summary

Mozilla Common Voice English is a large-scale, crowdsourced, CC0-licensed English speech dataset with explicit accent metadata and verified transcripts. It is structurally suitable for the Stage 5 external evaluation role, subject to two material limitations:

1. **Accent label quality degraded post-early-2022.** Versions using the pre-2022 enumerated accent taxonomy (i.e., <= cv-corpus-11.0) have cleaner, more directly usable accent labels. Versions >= cv-corpus-12.0 use free-text self-description, requiring normalisation preprocessing before group assignment.

2. **Group definition mismatch with L2-ARCTIC.** L2-ARCTIC defines groups by speaker L1 background (Arabic, Hindi, Korean, Mandarin, Spanish, Vietnamese). Common Voice defines accent by self-report, not L1. The only group with substantial speaker-level overlap is indian (proxies Hindi/South Asian L1). Direct equivalence claims cannot be made.

**Feasibility verdict: SUITABLE WITH LIMITATIONS (Classification B).**

---

## 2. Phase 1A — Source Verification

| Field | Value |
|---|---|
| Dataset Name | Mozilla Common Voice English |
| Recommended Release | cv-corpus-11.0-2022-09-21 (English, en) |
| Rationale | Last major release with enumerated accent taxonomy |
| Source URL | https://commonvoice.mozilla.org/en/datasets |
| Current Distribution | Mozilla Data Collective (https://datacollective.mozillafoundation.org/) |
| License | CC0 1.0 Public Domain Dedication |
| Task | Automatic Speech Recognition (ASR) |
| Language | English (en) |
| Audio Format | MP3, variable bitrate |
| Distribution Format | Compressed tar.gz (audio + metadata bundled) |
| Metadata-Only Download | NOT available standalone; TSV bundled with audio archive |

### License Verification

| Requirement | Status |
|---|---|
| Open license for research use | PASS: CC0 1.0 — unrestricted |
| Commercial restriction | PASS: None |
| Attribution requirement | PASS: None (CC0) |
| Speaker re-identification | CAUTION: Mozilla ToS discourages re-identification; aggregate analysis permitted |
| Suitability for external ASR evaluation | PASS |

---

## 3. Phase 1B — Metadata Schema Inventory

The validated.tsv file is the primary metadata manifest. Each row represents one validated audio clip.

| Field Name | Data Type | Meaning | Research Use | Risk/Limitation |
|---|---|---|---|---|
| client_id | string (SHA-256 hash) | Anonymised unique speaker identifier | Speaker-level grouping | Not a persistent real identity |
| path | string | Relative path to MP3 audio file | Audio retrieval | Requires full archive download |
| sentence | string | Orthographic transcript (exact read text) | WER evaluation reference | High quality; community-validated |
| up_votes | integer | Count confirming audio matches transcript | Quality gate | Minimum 2 required for validated.tsv inclusion |
| down_votes | integer | Count denying audio-transcript match | Quality gate | Majority down-votes -> invalidated.tsv |
| age | string (categorical) | Self-reported age bracket (teens/twenties/…) | Demographic stratification | Optional; ~40% missing |
| gender | string (categorical) | Self-reported gender | Demographic stratification | Optional; ~40% missing |
| accent | string (enumerated or free-text) | Self-reported accent/variety label | PRIMARY GROUP VARIABLE | ~50% missing; free-text post-2022 |
| locale | string | Language code (always 'en' for English) | Filtering | Not a speaker or accent proxy |
| segment | string | Optional subset/segment identifier | Subset identification | Often empty |

### Derived/Computed Fields (not in raw TSV)

| Derived Field | How to Compute | Purpose |
|---|---|---|
| clip_duration_sec | Compute from MP3 metadata or estimate from 5.3s average | Duration estimation |
| clips_per_speaker | GROUP BY client_id COUNT(path) | Speaker sampling fairness |
| validated_clips_per_accent | GROUP BY accent COUNT(path) on validated.tsv | Group size |
| unique_speakers_per_accent | GROUP BY accent COUNT(DISTINCT client_id) | Independent speaker count |

---

## 4. Phase 1C — Accent/Group Audit

### 4.1 Taxonomy Transition

**Before early 2022 (cv-corpus-11.0 and earlier):**
Accent field is drawn from a fixed enumerated taxonomy of ~16 predefined accent codes.
Missing entries are truly absent (NULL/empty), not mis-specified.

**After early 2022 (cv-corpus-12.0+):**
Free-text self-description produces synonymous entries, compound descriptors, and increased missingness.

**Recommendation: Use cv-corpus-11.0 for Stage 5 to obtain enumerated accent labels.**

### 4.2 Enumerated Accent Taxonomy (cv-corpus <= 11.0)

| # | Accent Code | Accent Label | Stage 5 Relevance |
|---|---|---|---|
| 1 | us | United States English | Native-English control |
| 2 | england | England English | Native-English control |
| 3 | indian | India and South Asia (India, Pakistan, Sri Lanka) | Partial proxy for Hindi/South Asian L1 |
| 4 | australia | Australian English | Native-English |
| 5 | canada | Canadian English | Native-English |
| 6 | ireland | Irish English | Native-English |
| 7 | scotland | Scottish English | Native-English |
| 8 | wales | Welsh English | Native-English; small pool |
| 9 | newzealand | New Zealand English | Native-English |
| 10 | philippines | Filipino English | L2-English; no L2-ARCTIC equivalent |
| 11 | hongkong | Hong Kong English | Cantonese-inflected; no L2-ARCTIC equivalent |
| 12 | malaysia | Malaysian English | L2-English; no L2-ARCTIC equivalent |
| 13 | singapore | Singaporean English | L2-English; no L2-ARCTIC equivalent |
| 14 | african | Southern African English | No L2-ARCTIC equivalent |
| 15 | southatlantic | South Atlantic | Very rare; <30 speakers |
| 16 | bermuda | West Indies and Bermuda | Rare; <50 speakers |

### 4.3 Estimated Speaker Counts (cv-corpus-11.0, English)

NOTE: Mozilla does not publish pre-computed per-accent speaker tables.
These estimates are derived from CommonAccent (Interspeech 2023), cvaccents analyses,
and Kaggle community analyses. Exact counts require processing validated.tsv.

| Accent Code | Est. Validated Clips | Est. Unique Speakers | Median Clips/Speaker |
|---|---|---|---|
| us | ~249,000 | ~12,000-15,000 | ~18 |
| england | ~75,000 | ~3,500-5,000 | ~18 |
| indian | ~79,000 | ~4,000-6,000 | ~16 |
| australia | ~33,000 | ~1,500-2,500 | ~16 |
| canada | ~20,000 | ~1,000-1,800 | ~15 |
| ireland | ~10,000 | ~500-900 | ~14 |
| scotland | ~7,000 | ~350-600 | ~14 |
| wales | ~3,000 | ~150-300 | ~14 |
| newzealand | ~5,000 | ~250-500 | ~14 |
| philippines | ~8,000 | ~400-700 | ~14 |
| hongkong | ~4,000 | ~200-400 | ~14 |
| malaysia | ~3,500 | ~150-300 | ~13 |
| singapore | ~3,000 | ~150-300 | ~13 |
| african | ~6,000 | ~300-600 | ~14 |
| southatlantic | <200 | <30 | ~8 |
| bermuda | <500 | <50 | ~10 |

### 4.4 Accent Field Missing Rate

| Dataset Version | Est. Missing Rate | Basis |
|---|---|---|
| cv-corpus <= 11.0 | ~45-55% of validated clips have NULL/empty accent | Community analyses; research papers |
| cv-corpus >= 12.0 | ~50-60% NULL + ~10-15% normalisation-required free-text | cvaccents analysis; EAAMO 2023 |

---

## 5. Phase 1D — Speaker Audit

### 5.1 Speaker Independence Principle

Unit of independence: client_id (one per registered contributor).

Key properties:
- client_id is a stable, hashed UUID per contributor within a release
- It does NOT change across clips by the same speaker within a version
- It is NOT a real identity; speaker re-identification is not possible from client_id alone
- One speaker may appear in multiple accent categories if they changed their self-report (uncommon)

### 5.2 Speaker Count Summary

| Metric | Estimate |
|---|---|
| Total unique speakers in English validated.tsv (v11.0) | ~80,000-100,000 |
| Speakers with at least one accent label | ~40,000-55,000 |
| Speakers in us accent | ~12,000-15,000 |
| Speakers in indian accent | ~4,000-6,000 |
| Speakers in england accent | ~3,500-5,000 |
| Speakers in ustralia accent | ~1,500-2,500 |

### 5.3 Clips Per Speaker Distribution

| Metric | Typical Value |
|---|---|
| Average clips per speaker (English) | ~15-20 |
| Median clips per speaker | ~10-15 |
| Average clip duration | ~5.3 seconds |
| Estimated words per clip | ~8-12 words |
| Estimated words per speaker (at median 12 clips) | ~100-140 words |

---

## 6. Phase 1E — Transcript Audit

| Property | Status |
|---|---|
| Transcript field name | sentence |
| Language | English (orthographic standard) |
| Source | Mozilla Common Voice sentence corpus (open, community-contributed) |
| Transcript type | Read speech (speaker reads a displayed sentence) |
| Missing transcript rate | ~0% in validated.tsv (sentence required for clip recording) |
| Duplicate transcript rate | Moderate (same sentence recorded by multiple speakers) |
| Validation mechanism | Community up-vote/down-vote |
| Average transcript length | ~8-12 words |
| Suitability for exact WER evaluation | SUITABLE |
| Non-English contamination | Very rare in English locale |
| Normalisation required | Standard text normalisation (lowercase, strip punctuation) |

---

## 7. Phase 1F — Group Balance Feasibility

### 7.1 Targets Evaluated

| Target Speakers/Group | Feasible Groups (est.) | Feasible on Laptop |
|---|---|---|
| 5 speakers/group | >=8 groups | YES |
| 10 speakers/group | >=6 groups | YES |
| 15 speakers/group | >=4 groups | YES |
| 20 speakers/group | >=4 groups | YES |

### 7.2 Recommended Target: 10 speakers/group, 6 groups

| Dimension | Assessment |
|---|---|
| Feasible groups | 6 (us, england, indian, australia, canada, ireland) |
| Est. clips (15 clips/speaker min) | >=900 total |
| Est. audio subset size | ~80-100 MB |
| WER computability | Sufficient |
| Bootstrap resample stability | Moderate-to-good at 10 speakers/group |
| Laptop feasibility | YES |

---

## 8. Key Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Accent label missing (~50% of clips) | High | Select only accent-labelled clips; pool remains large |
| Post-2022 free-text taxonomy | High | Use cv-corpus-11.0 (enumerated labels) |
| Accent label is self-reported, not L1-verified | Moderate | Document as stress/generalization test, not strict replication |
| No direct L1 equivalents for Arabic/Korean/Mandarin/Spanish/Vietnamese | High | See cross_dataset_group_definition.md |
| No metadata-only download available | Moderate | Download full archive (~22 GB); delete audio after TSV extraction |
| CC0 license | POSITIVE | No restriction on research or publication |

---

## 9. Phase 1 Conclusions

Mozilla Common Voice English (cv-corpus-11.0) provides:
- PASS: Explicit, enumerated accent labels (pre-2022 taxonomy)
- PASS: Large speaker pools (indian: ~4,000-6,000; england: ~3,500-5,000; australia: ~1,500-2,500)
- PASS: CC0 license (unrestricted research use)
- PASS: Community-validated transcripts suitable for WER evaluation
- PASS: Read-speech format compatible with L2-ARCTIC evaluation protocol
- PASS: Complete independence from L2-ARCTIC speakers (different dataset, different registration)
- CAUTION: No direct L1-equivalent groups for Arabic, Korean, Mandarin, Spanish, Vietnamese
- CAUTION: Accent label is self-report; not L1 verified
- CAUTION: Full archive download required (~22 GB for English v11.0)
- CAUTION: ~50% of clips have missing accent labels

**FINAL VERDICT: SUITABLE WITH LIMITATIONS (Classification B)**

The limitations are known, documentable, and do not invalidate the external evaluation role.
They require appropriate scoping in paper language (see cross_dataset_group_definition.md).
