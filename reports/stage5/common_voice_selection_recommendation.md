# Common Voice External Evaluation Design Recommendation
## DSG-CTTA Stage 5 Phase 1K/1L

**Date:** 2026-10-01
**Auditor:** Lead Research Data Engineer
**Purpose:** Propose the external evaluation design and issue the Phase 1 GO/NO-GO classification.

---

## 1. Phase 1I — Duplicate and Leakage Risk Assessment

### 1.1 Within-Common Voice Duplicate Risk

| Risk Type | Assessment | Mitigation |
|---|---|---|
| Duplicate recordings (same client_id, same path) | Very low: validated.tsv deduplicates by clip path | Verify during Phase 3 by checking client_id + path uniqueness |
| Duplicate prompts (same sentence, different speakers) | Expected and benign: same sentence read by multiple speakers | Does not affect speaker independence; filter at selection |
| Duplicate speaker entries across splits | LOW: validated.tsv covers all validated clips; splits are derived from it | Use validated.tsv as primary source; do not mix splits |
| Duplicated client_id across versions | POSSIBLE: client_id hash is version-specific; same physical person may have different hashes in v10 vs v11 | Fix to a single version (cv-corpus-11.0); do not mix versions |

### 1.2 Cross-Dataset Speaker Identity (Common Voice vs. L2-ARCTIC)

| Risk | Assessment |
|---|---|
| Common Voice and L2-ARCTIC share the same physical speakers | VERY UNLIKELY: L2-ARCTIC was recruited by university researchers; CV is crowdsourced platform registration |
| Cross-dataset speaker identity verifiable from metadata | NOT POSSIBLE: client_id is a hash with no linkage to external identities; L2-ARCTIC speaker IDs are not linked to CV |
| Cross-dataset sentence overlap | NONE expected: L2-ARCTIC uses CMU ARCTIC prompts; CV uses Mozilla sentence pool (different source) |

**Operational independence definition:**
"The Common Voice external evaluation speakers are operationally independent of L2-ARCTIC speakers.
Common Voice contributors registered independently on the Mozilla Common Voice platform.
L2-ARCTIC speakers were recruited and recorded in a separate research protocol. No shared
registration, identity, or audio exists. Cross-dataset speaker identity cannot be verified
or refuted from metadata alone; operational independence is the strongest achievable claim."

This wording must be used in the paper when describing cross-dataset independence.
Do NOT claim "zero cross-dataset speaker identity" without this qualification.

### 1.3 Cross-Dataset Audio Overlap

| Check | Result |
|---|---|
| L2-ARCTIC audio in Common Voice | NONE expected (different recording conditions, session, equipment) |
| Common Voice audio in L2-ARCTIC | NONE expected |
| Shared audio hashes | Cannot be verified without downloading both audio sets; document as unverified |

---

## 2. Phase 1K — Recommended External Evaluation Design

### 2.1 Design Proposal (NOT yet frozen; Phase 3 will freeze)

| Parameter | Proposed Value | Rationale |
|---|---|---|
| External Dataset | Mozilla Common Voice English | CC0, large scale, accent labels, transcript available |
| Release | cv-corpus-11.0-2022-09-21 | Enumerated accent taxonomy; pre-2022 controlled labels |
| Source URL | https://commonvoice.mozilla.org/en/datasets | Official distribution; via Mozilla Data Collective |
| License | CC0 1.0 | No restriction on research or publication |
| Selected Group Definition | Dataset-provided enumerated accent label (validated.tsv ccent field) | Explicit label; not geographic inference |
| Number of Groups | 6 | Consistent with L2-ARCTIC 6-group structure |
| Group Names | us, england, indian, australia, canada, ireland | Satisfy all 8 pre-declared selection criteria |
| Target Speakers/Group | 10 | Balances statistical power with pool availability across all 6 groups |
| Minimum Clips/Speaker | 15 | Ensures adequate WER per speaker at ~8-12 words/clip |
| Target Words/Group | ~1,200-1,800 | At 10 speakers x 15 clips x ~8-12 words/clip |
| Estimated Audio Duration | ~13 min/group; ~78 min total | At 5.3 sec/clip avg |
| Estimated Audio Size | ~80-100 MB | Laptop-feasible |
| Selection Rule | Random uniform sampling within group; seed-fixed for reproducibility | No WER/disparity-based selection |

### 2.2 Selection Rules (Pre-Declared)

Group inclusion criteria (applied in Phase 3):
1. ccent field matches one of the 6 selected codes in validated.tsv
2. Speaker has >= 15 validated clips in the group
3. Speaker has not been assigned to any other group (no cross-group contamination)
4. Random sample of 10 speakers per group; seed documented
5. Random sample of 15 clips per speaker; seed documented

Exclusion criteria:
- Any clip with down_votes >= up_votes (already excluded in validated.tsv)
- Any clip with sentence length < 4 words
- Any speaker appearing in multiple accent groups (exclude from both; rare)

### 2.3 What This Design Does NOT Do

- Does NOT tune DSG on Common Voice
- Does NOT select groups based on WER or disparity
- Does NOT claim L1 equivalence with L2-ARCTIC groups
- Does NOT create the final evaluation subset yet (Phase 3)
- Does NOT modify the L2-ARCTIC primary evaluation protocol

---

## 3. Phase 1L — GO / NO-GO Classification

### Classification: B — SUITABLE WITH LIMITATIONS

**Evidence summary:**

| Criterion | Assessment |
|---|---|
| Explicit accent labels available | YES (enumerated taxonomy in cv-corpus-11.0) |
| Sufficient speakers per proposed group | YES (all 6 groups have >> 10 speakers) |
| Transcript available and WER-suitable | YES (validated.tsv; community-validated) |
| CC0 license | YES (unrestricted) |
| Independent of L2-ARCTIC | YES (operationally independent) |
| Feasible on laptop | YES (~80-100 MB subset) |
| Group definitions equivalent to L2-ARCTIC | NO (self-report vs. verified L1) |
| Missing accent label rate | HIGH (~50% of clips lack label; sufficient labelled clips remain) |
| Direct L1 equivalents for all 6 L2-ARCTIC groups | NO (Arabic/Korean/Mandarin/Spanish/Vietnamese have no CV equivalent) |
| Post-2022 accent taxonomy concern | MITIGATED by fixing to cv-corpus-11.0 |

### Limitations That Must Be Documented in Paper

1. SELF-REPORT ACCENT: CV accent labels are self-reported; not verified against L1 or any external criterion.

2. GROUP DEFINITION MISMATCH: CV groups are not equivalent to L2-ARCTIC L1 groups.
   The evaluation serves as out-of-distribution stress testing, not replication.

3. NATIVE/NON-NATIVE DIFFERENCE: Most CV groups (us, england, australia, canada, ireland)
   are predominantly native-English speakers. L2-ARCTIC groups are exclusively non-native.
   This is a fundamental population difference.

4. MISSING LABELS: ~50% of CV English clips lack an accent label; only labelled clips
   are eligible for Stage 5 external evaluation.

5. CROSS-DATASET IDENTITY: Cross-dataset speaker identity cannot be formally ruled out
   from metadata alone; operational independence is the strongest achievable claim.

### GO Decision

**PHASE 1: GO — Common Voice English is suitable as the Stage 5 external evaluation corpus,**
**subject to the above limitations and appropriate paper language.**

Next step: Phase 3 — Download cv-corpus-11.0 English archive, extract validated.tsv,
generate speaker-disjoint accent-labelled evaluation manifest, and produce:
datasets/splits/stage5_external_eval.csv

Do NOT proceed to Phase 3 until this Phase 1 report has been reviewed and the proposed
design (Section 2.2) has been approved.

---

## 4. Summary Table

| Item | Value |
|---|---|
| Dataset | Mozilla Common Voice English |
| Version | cv-corpus-11.0-2022-09-21 |
| License | CC0 1.0 |
| Groups | us, england, indian, australia, canada, ireland |
| Speakers/group | 10 (proposed) |
| Clips/speaker | >=15 (proposed) |
| Total clips (est.) | ~900 |
| Total audio (est.) | ~80-100 MB |
| Group definition | Dataset-provided enumerated accent label |
| Evaluation role | External stress test / out-of-distribution validation |
| Equivalence to L2-ARCTIC | NOT equivalent; separate evaluation |
| Classification | B — SUITABLE WITH LIMITATIONS |
| Phase 1 decision | GO (proceed to Phase 3 after review) |
