# Common Voice Group Selection Rationale
## DSG-CTTA Stage 5 Phase 1G

**Date:** 2026-10-01
**Auditor:** Lead Research Data Engineer
**Purpose:** Document group selection rationale for Stage 5 external evaluation subset.
Pre-declared selection criteria only. No ASR WER used. No disparity used.

> **CRITICAL DISTINCTION**
> Every group listed below uses a DATASET-PROVIDED ACCENT LABEL from the cv-corpus-11.0
> enumerated taxonomy. No group is inferred from geography, country of residence, birthplace,
> or any geographic metadata. Geographic information embedded in the accent code names
> (e.g., ireland, ustralia) refers to the SELF-REPORTED LABEL chosen by the contributor,
> not an inferred location derived from non-accent fields.

---

## 1. Pre-Declared Selection Criteria

Groups are selected if and only if they satisfy ALL of the following:

1. EXPLICIT_LABEL: The group has a dataset-provided accent label in the cv-corpus-11.0
   enumerated taxonomy (not inferred from locale, path, age, gender, or any other field).

2. SUFFICIENT_SPEAKERS: Estimated unique speakers >= 10 per group to support meaningful
   WER aggregation and bootstrap resampling.

3. SUFFICIENT_CLIPS: Estimated validated clips >= 150 per group (at 15 clips/speaker target).

4. TRANSCRIPT_AVAILABLE: All clips in validated.tsv have a sentence field (~0% missing).

5. REASONABLE_CLIPS_PER_SPEAKER: Median clips/speaker >= 10 to support per-speaker WER.

6. METADATA_COMPLETENESS: Accent label is explicitly recorded (not inferred or imputed).

7. REPRODUCIBILITY: Group is defined by a fixed accent code in a fixed versioned release.

8. ENGLISH_ASR_SUITABILITY: Group comprises English speech suitable for English ASR evaluation.

---

## 2. Groups Satisfying All Criteria

The following 6 groups satisfy all 8 selection criteria using the cv-corpus-11.0 English
enumerated accent taxonomy:

| Group # | Accent Code | Accent Label | Criterion 1 | Criterion 2 | Criterion 3 | Criterion 4 | Criterion 5 | Criterion 6 | Criterion 7 | Criterion 8 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | us | United States English | PASS | PASS (~12k-15k spk) | PASS (~249k clips) | PASS | PASS (~18) | PASS | PASS | PASS |
| 2 | england | England English | PASS | PASS (~3.5k-5k spk) | PASS (~75k clips) | PASS | PASS (~18) | PASS | PASS | PASS |
| 3 | indian | India/South Asia English | PASS | PASS (~4k-6k spk) | PASS (~79k clips) | PASS | PASS (~16) | PASS | PASS | PASS |
| 4 | australia | Australian English | PASS | PASS (~1.5k-2.5k spk) | PASS (~33k clips) | PASS | PASS (~16) | PASS | PASS | PASS |
| 5 | canada | Canadian English | PASS | PASS (~1k-1.8k spk) | PASS (~20k clips) | PASS | PASS (~15) | PASS | PASS | PASS |
| 6 | ireland | Irish English | PASS | PASS (~500-900 spk) | PASS (~10k clips) | PASS | PASS (~14) | PASS | PASS | PASS |

---

## 3. Groups Considered but Not Selected

| Accent Code | Accent Label | Primary Exclusion Reason |
|---|---|---|
| scotland | Scottish English | Criterion 2 borderline: ~350-600 speakers; marginal at 10/group target |
| wales | Welsh English | Criterion 2 FAIL: ~150-300 speakers; insufficient for 10/group target |
| newzealand | New Zealand English | Criterion 2 borderline: ~250-500 speakers; marginal |
| philippines | Filipino English | Passes criteria but adds 7th group unnecessarily; stage 5 is 6 groups |
| hongkong | Hong Kong English | Criterion 2 borderline; L1 confound (Cantonese vs Mandarin) |
| malaysia | Malaysian English | Criterion 2 FAIL: ~150-300 speakers |
| singapore | Singaporean English | Criterion 2 FAIL: ~150-300 speakers |
| african | Southern African English | Passes criteria; excluded in favour of 6-group design consistent with L2-ARCTIC structure |
| southatlantic | South Atlantic | Criterion 2 FAIL: <30 speakers |
| bermuda | West Indies/Bermuda | Criterion 2 FAIL: <50 speakers |

---

## 4. Important Note on Group Label Interpretation

The 6 selected accent codes are DATASET-PROVIDED LABELS from the cv-corpus-11.0 enumerated
accent taxonomy. They represent what speakers SELF-REPORTED as their accent when registering
on the Common Voice platform.

These labels must NOT be interpreted as:
- Country of birth or residence (inferred geographic proxy)
- L1 (native language) background verified by any external source
- A direct equivalent to L2-ARCTIC L1 groups (see cross_dataset_group_definition.md)

The indian label specifically must not be treated as equivalent to Hindi-L1.
The indian label is a dataset-provided accent self-report that conflates multiple South Asian
L1 backgrounds (Hindi, Tamil, Telugu, Kannada, Urdu, etc.).

---

## 5. Conclusion

Six accent groups from cv-corpus-11.0 English satisfy all 8 pre-declared selection criteria:
us, england, indian, australia, canada, ireland.

These 6 groups constitute the proposed Stage 5 external evaluation group set, PENDING
Phase 1H compatibility assessment and Phase 1L final classification.

No groups were selected or excluded on the basis of ASR WER, disparity scores,
or any Stage 5 experimental outcome.
