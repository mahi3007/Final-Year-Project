# Stage 5 External Evaluation Set Curation Audit
## DSG-CTTA Phase 3

**Date:** 2026-10-01
**Protocol version:** v2.0.0-amended-cv27

---

## 1. Dataset Identity

| Field | Value |
|---|---|
| Dataset | Mozilla Common Voice English |
| Release | cv-corpus-27.0-2026-09-11 |
| License | CC0-1.0 |
| Language | en |
| Source | https://mozilladatacollective.com/datasets/cmu5jplf300nwmh07iqvk9leo |
| Metadata hash | b5520260d8ad3c8593174d8e1d2242b2ef86bd4ac2451221c7f3d49cf6af8fbf |

## 2. Release / License

CC0 1.0 Public Domain Dedication. No restrictions on research use or publication.

## 3. Accent Taxonomy

Group labels are **dataset-provided enumerated accent codes** from the cv-corpus-11.0
validated.tsv accent field. These are self-reported labels, NOT verified L1 identities.
They must not be equated with L2-ARCTIC L1-associated speaker groups.

## 4. Selection Criteria

Criteria applied (pre-declared in Phase 1):
1. `accent` field explicitly matches one of 6 target codes
2. `client_id` non-empty
3. `path` non-empty
4. `sentence` non-empty and >= 2 words
5. `path` deduplicated (no duplicate audio paths)
6. Speaker has >= 15 validated clips passing criteria 1-5

NOT used for selection:
- ASR WER or CER
- Disparity scores
- Acoustic difficulty
- Geographic metadata
- Age or gender (except optional balancing if pre-declared)

## 5. Speaker Selection Procedure

- Sorted eligible speaker IDs lexicographically
- Shuffled with `random.Random(seed=20261001)`
- Selected first 10 speakers per group

## 6. Clip Selection Procedure

- Sorted clips by path lexicographically
- Shuffled with `random.Random(seed=20261002)`
- Selected first 15 clips per speaker

## 7. Speaker Counts

| Group | Label | Total Spk | Eligible Spk | Target | Feasible | Selected |
|---|---|---|---|---|---|---|
| US English | United States English | 8,969 | 3,913 | 10 | YES | 10 |
| England English | England English | 2,695 | 1,223 | 10 | YES | 10 |
| South Asian English | India and South Asia (India, Pakistan, Sri Lanka) | 2,413 | 764 | 10 | YES | 10 |
| Australian English | Australian English | 800 | 400 | 10 | YES | 10 |
| Canadian English | Canadian English | 1,024 | 511 | 10 | YES | 10 |
| Irish English | Irish English | 218 | 94 | 10 | YES | 10 |
| **Total** | | | | 60 | | 60 |

## 8. Clip Counts

| Group | Speakers | Clips/Spk | Total Clips |
|---|---|---|---|
| US English | 10 | 15 | 150 |
| England English | 10 | 15 | 150 |
| South Asian English | 10 | 15 | 150 |
| Australian English | 10 | 15 | 150 |
| Canadian English | 10 | 15 | 150 |
| Irish English | 10 | 15 | 150 |
| **Total** | 60 | | 900 |

## 9. Transcript Quality

See `external_quality_report.md`.

## 10. Audio Integrity

Audio hashes: populated after Phase 3G materialization.
Status: PENDING until audio downloaded.

## 11. Duplicate Audit

Duplicate detection covers: recording path, audio hash, transcript+path pair.
See Phase 3L log output.

## 12. Cross-Source Independence

Operational source-level independence. Common Voice contributors registered independently on the Mozilla Common Voice platform. L2-ARCTIC speakers were recruited and recorded in a separate university research protocol. No shared registration, identity, or audio exists. Cross-dataset speaker identity cannot be formally verified or refuted from metadata alone.

Namespace note: Common Voice uses SHA-256 hashed client_id (anonymised UUID). L2-ARCTIC uses researcher-assigned speaker codes (e.g. HJK, TNI). These namespaces are disjoint by construction.

## 13. Reproducibility

Exact reproduction procedure:
1. Pin release: `cv-corpus-27.0-2026-09-11`
2. Verify metadata hash: `b5520260d8ad3c8593174d8e1d2242b2ef86bd4ac2451221c7f3d49cf6af8fbf`
3. Apply eligibility criteria (see Section 4)
4. Run speaker selection with `random.Random(20261001)`
5. Run clip selection with `random.Random(20261002)`
6. Verify CSV hash matches lock file

## 14. Limitations

1. Accent labels are self-reported; not verified L1 backgrounds.
2. Groups are not equivalent to L2-ARCTIC L1 groups.
3. ~50% of CV English clips have missing accent labels (eligible pool uses labelled clips only).
4. No direct L1 equivalents for Arabic, Korean, Mandarin, Spanish, Vietnamese.
5. Cross-dataset speaker identity cannot be formally verified.

## 15. Final Freeze Decision

The external evaluation set is FROZEN after Phase 3N.
See `datasets/splits/stage5_external_eval.lock.json` for immutability hash.

**Frozen evaluation set:** `datasets/splits/stage5_external_eval.csv`
**Evaluation role:** External out-of-distribution stress test.
**NOT permitted to use for:** DSG tuning, threshold selection, model selection.